"""Writing the run out.

Three outputs, each for a different reader:

- `reports/latest.md` is the run at a glance
- `reports/proposals/<date>/` holds one file per patch, ready to review
- `reports/ledger.csv` tracks proposed, opened, merged over time

The ledger is the one that matters for judging this tool. Anything can
generate patches. The merge ratio is the only honest measure of whether they
were worth a maintainer's attention, and it is the number to quote.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from .model import Finding, Proposal, Tier


def _table(rows: list[list[str]], headers: list[str]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |",
           "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(c).replace("|", "\\|") for c in row) + " |")
    return out


def write(root: Path, run: dict, proposals: list[Proposal],
          findings: list[Finding]) -> None:
    reports = root / "reports"
    stamp = run["run_at"][:10]
    prop_dir = reports / "proposals" / stamp
    reports.mkdir(exist_ok=True)
    (reports / "raw").mkdir(exist_ok=True)
    prop_dir.mkdir(parents=True, exist_ok=True)

    with open(reports / "raw" / f"{stamp}.json", "w", encoding="utf-8") as fh:
        json.dump({**run, "proposals": [p.to_dict() for p in proposals]}, fh, indent=2)

    # one file per proposal, so review is a matter of reading and applying
    for index, proposal in enumerate(proposals, start=1):
        name = f"{proposal.target}-{index:02d}-{proposal.finding_id}.md"
        body = [
            f"# Proposal {proposal.finding_id}",
            "",
            f"- Target: `{proposal.target}`",
            f"- File: `{proposal.path}`",
            "",
            "## Why",
            "",
            proposal.rationale,
            "",
            "## How this was verified",
            "",
            proposal.verification,
            "",
            "## Patch",
            "",
            "```diff",
            proposal.diff.rstrip(),
            "```",
            "",
            "Apply with `git apply` from the target repository root. This patch "
            "was drafted automatically and has not been opened anywhere. Read it "
            "before you send it.",
        ]
        (prop_dir / name).write_text("\n".join(body) + "\n", encoding="utf-8")

    # ledger: one row per proposal, status filled in by hand as they progress
    ledger = reports / "ledger.csv"
    is_new = not ledger.exists()
    with open(ledger, "a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        if is_new:
            writer.writerow(["date", "proposal_id", "target", "path",
                             "status", "pr_url", "notes"])
        for proposal in proposals:
            writer.writerow([stamp, proposal.finding_id, proposal.target,
                             proposal.path, "proposed", "", ""])

    # summary
    refused = [f for f in findings if f.tier is Tier.REFUSED]
    review = [f for f in findings if f.tier is Tier.REVIEW_ONLY]

    lines = [
        "# Latest run",
        "",
        f"Run at {run['run_at']} UTC.",
        "",
        f"{len(proposals)} patches drafted, {len(review)} findings left for "
        f"review, {len(refused)} findings deliberately not patched.",
        "",
        "## Targets",
        "",
    ]
    lines += _table(
        [[t["name"], t["type"], t.get("revision", ""),
          ", ".join(f"{g['gate']}:{g['status']}" for g in t["gates"])]
         for t in run["targets"]],
        ["Target", "Type", "Revision", "Gates"],
    )

    if proposals:
        lines += ["", "## Drafted patches", "",
                  f"In `reports/proposals/{stamp}/`. Nothing has been opened.", ""]
        lines += _table(
            [[p.finding_id, p.target, p.path, p.verification[:80]] for p in proposals],
            ["ID", "Target", "File", "Verified by"],
        )

    if review:
        lines += ["", "## Findings needing a human", "",
                  "Real findings where the correct fix is not derivable from "
                  "the document.", ""]
        lines += _table(
            [[f.target, f.kind, f"{f.path or ''}:{f.line or ''}", f.message[:90]]
             for f in review[:40]],
            ["Target", "Kind", "Location", "Finding"],
        )
        if len(review) > 40:
            lines.append("")
            lines.append(f"{len(review) - 40} more in the raw report.")

    if refused:
        lines += ["", "## Deliberately not patched", "",
                  "These are real gaps. Filling them requires knowing how the "
                  "API behaves, and a plausible invented answer is worse than "
                  "the gap because it gets copied.", ""]
        seen: set[str] = set()
        rows = []
        for finding in refused:
            if finding.kind in seen:
                continue
            seen.add(finding.kind)
            rows.append([finding.target, finding.kind, finding.refusal_reason or ""])
        lines += _table(rows, ["Target", "Kind", "Why not"])

    lines += [
        "",
        "---",
        "",
        "`error` on a gate means this pipeline failed, not that the "
        "documentation did. Those are never reported as findings.",
    ]
    (reports / "latest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
