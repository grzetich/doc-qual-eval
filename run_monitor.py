#!/usr/bin/env python3
"""Detect problems in open source API documentation, then draft the fixes.

Two kinds of target:

- `contribution` targets are open source projects where a pull request is
  welcome. They are cloned, gated, and patches are drafted against real files.
- `benchmark` targets exist only to give the scores a reference point. They are
  fetched and scored, never proposed against, because nobody asked.

Nothing is ever opened automatically. The run produces a queue of patches for
a human to read, judge, and send by hand.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from monitor import dedupe, gates, generated, mcpgen, pages, propose, report, sources
from monitor.model import Finding, Tier
from monitor.profile import Profile

ROOT = Path(__file__).resolve().parent


def run_contribution(target: dict, settings: dict, profiles: dict,
                     workdir: Path, args) -> tuple[dict, list[Finding], list]:
    name = target["name"]
    dest = workdir / name
    ok, message = sources.clone(target["repo"], target.get("ref", "main"), dest)
    entry = {"name": name, "type": "contribution", "revision": "", "gates": []}

    if not ok:
        entry["gates"].append({"gate": "checkout", "status": "error",
                               "summary": message})
        return entry, [], []

    entry["revision"] = sources.head_sha(dest)
    entry["gates"].append({"gate": "checkout", "status": "ok",
                           "summary": f"{message} at {entry['revision']}"})

    prose_files = [(str(p.relative_to(dest)), p)
                   for p in sources.collect_files(dest, target.get("prose", []))]
    prose_files, dropped = generated.filter_files(
        prose_files, tuple(target.get("generated", [])))
    if dropped:
        sample = ", ".join(rel for rel, _ in dropped[:3])
        entry["gates"].append({
            "gate": "exclusions", "status": "ok",
            "summary": f"{len(dropped)} generated or historical files skipped "
                       f"({sample}{'...' if len(dropped) > 3 else ''})",
        })
    findings: list[Finding] = []

    link_result = gates.gate_links(
        name, prose_files, settings["max_links_per_target"],
        settings["link_timeout_seconds"],
    )
    entry["gates"].append(link_result.to_dict() | {"findings": []})
    findings += link_result.findings

    # Prefer the project's own style configuration. Falling back to ours is
    # detection only: see find_project_style for why.
    project_style = gates.find_project_style(dest)
    fallback = ROOT / ".vale.ini"
    prose_result = gates.gate_prose(
        name, prose_files, dest,
        project_style or (fallback if fallback.exists() else None),
        settings["gate_timeout_seconds"],
        project_owns_style=project_style is not None,
    )
    entry["gates"].append(prose_result.to_dict() | {"findings": []})
    findings += prose_result.findings

    for rel in target.get("json_schema", []):
        path = dest / rel
        if not path.exists():
            entry["gates"].append({"gate": "jsonschema", "status": "error",
                                   "summary": f"{rel} not found in checkout"})
            continue
        schema_result = gates.gate_jsonschema(name, rel, path)
        entry["gates"].append(schema_result.to_dict() | {"findings": []})
        findings += schema_result.findings

    generation = target.get("generation")
    if generation and args.generation:
        profile_name = generation.get("profile")
        profile_data = profiles.get(profile_name)
        if profile_data is None:
            entry["gates"].append({
                "gate": "generation", "status": "error",
                "summary": f"target names profile '{profile_name}', which is "
                           f"not defined in targets.yml",
            })
        else:
            schema_rel = generation.get("schema")
            result = mcpgen.gate_generation(
                target=name, repo_root=dest, sdk_root=dest,
                schema_path=dest / schema_rel if schema_rel else None,
                doc_paths=generation.get("docs", []),
                profile=Profile.from_dict({"name": profile_name, **profile_data}),
                threshold=args.threshold,
                model=generation.get("model", mcpgen.DEFAULT_MODEL),
            )
            entry["gates"].append(result.to_dict() | {"findings": []})
            findings += result.findings
    elif generation:
        entry["gates"].append({
            "gate": "generation", "status": "skipped",
            "summary": "pass --generation to run it; it calls a paid API",
        })

    findings, absorbed = dedupe.collapse(
        findings, settings.get("duplicate_threshold", 3))
    if absorbed:
        entry["gates"].append({
            "gate": "dedupe", "status": "ok",
            "summary": f"{absorbed} repeated findings collapsed into their "
                       f"patterns and demoted to review",
        })

    proposals, unproposed = propose.build(findings, dest)

    # A queue nobody can get through is the same as no queue. Cap it, and say
    # plainly how many were held back rather than quietly dropping them.
    cap = settings.get("max_proposals_per_target", 20)
    if len(proposals) > cap:
        held = len(proposals) - cap
        proposals = proposals[:cap]
        entry["gates"].append({
            "gate": "proposals", "status": "ok",
            "summary": f"{cap} patches queued, {held} held back to keep the "
                       f"queue reviewable",
        })
    # A draftable finding that produced no patch is not silently dropped.
    for finding in unproposed:
        finding.tier = Tier.REVIEW_ONLY
    return entry, findings, proposals


def run_pages(target: dict, settings: dict) -> tuple[dict, list[Finding]]:
    """Measure the pages a developer would actually paste into a chat box."""
    name = target["name"]
    entry = {"name": name, "type": "pages", "revision": "", "gates": []}
    result = pages.gate_page_fetch(
        name, target.get("pages", []),
        min_words=settings.get("page_min_words", 250),
        timeout=settings.get("fetch_timeout_seconds", 45),
    )
    entry["gates"].append(result.to_dict() | {"findings": []})
    return entry, result.findings


def run_benchmark(target: dict, settings: dict, workdir: Path,
                  args) -> tuple[dict, list[Finding]]:
    name = target["name"]
    entry = {"name": name, "type": "benchmark", "revision": "", "gates": []}
    dest = workdir / f"{name}{Path(target['spec']).suffix or '.yaml'}"

    ok, message = sources.fetch_url(
        target["spec"], dest, settings["fetch_timeout_seconds"],
        settings["min_spec_bytes"],
    )
    entry["gates"].append({"gate": "fetch",
                           "status": "ok" if ok else "error",
                           "summary": message})
    if not ok:
        return entry, []

    result = gates.gate_artie(name, dest, args.threshold,
                              settings["gate_timeout_seconds"], args.generation)
    entry["gates"].append(result.to_dict() | {"findings": []})
    return entry, result.findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generation", action="store_true",
                        help="enable artie's paid Generation Quality check")
    parser.add_argument("--threshold", type=float, default=7.0,
                        help="artie check score below which a finding is raised")
    parser.add_argument("--only", help="run a single target by name")
    args = parser.parse_args()

    config = sources.load_config(ROOT)
    settings = config["settings"]
    targets = config["targets"]
    profiles = config.get("profiles", {})
    if args.only:
        targets = [t for t in targets if t["name"] == args.only]
        if not targets:
            print(f"No target named {args.only}", file=sys.stderr)
            return 2

    all_findings: list[Finding] = []
    all_proposals: list = []
    entries: list[dict] = []

    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        for target in targets:
            print(f"  {target['name']} ...", flush=True)
            if target.get("kind") == "pages":
                entry, findings = run_pages(target, settings)
                proposals = []
            elif target.get("kind") == "benchmark":
                entry, findings = run_benchmark(target, settings, workdir, args)
                proposals = []
            else:
                entry, findings, proposals = run_contribution(
                    target, settings, profiles, workdir, args)
            entries.append(entry)
            all_findings += findings
            all_proposals += proposals

        run = {"run_at": report.now(), "threshold": args.threshold,
               "generation": args.generation, "targets": entries,
               "findings": [f.to_dict() for f in all_findings]}
        report.write(ROOT, run, all_proposals, all_findings)

    drafted = len(all_proposals)
    review = sum(1 for f in all_findings if f.tier is Tier.REVIEW_ONLY)
    refused = sum(1 for f in all_findings if f.tier is Tier.REFUSED)
    print(f"\n{drafted} patches drafted, {review} for review, "
          f"{refused} deliberately not patched")
    print("Nothing was opened. Review reports/proposals/ before sending anything.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
