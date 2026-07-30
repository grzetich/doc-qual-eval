"""Detection gates. These find things. They never fix anything.

Every gate returns a GateResult and catches its own exceptions. One broken
gate must not cost you the rest of the run.
"""

from __future__ import annotations

import concurrent.futures
import json
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from . import redirects
from .model import Finding, GateResult, Tier

USER_AGENT = "docs-quality-monitor (+https://github.com/grzetich/docs-quality-monitor)"

# Markdown inline links and bare URLs. Reference-style definitions too.
MD_LINK = re.compile(r"\[[^\]]*\]\(\s*(<?)(https?://[^\s)>]+)\1[^)]*\)")
MD_REFDEF = re.compile(r"^\s*\[[^\]]+\]:\s*(https?://\S+)", re.MULTILINE)
BARE_URL = re.compile(r"(?<![(<\"'])\bhttps?://[^\s\"'<>)\]},;`]+")
TRAILING = "`.,:;!?*_)]}'\""

# Namespace identifiers that are expected to 404 and are not links a reader
# would ever follow.
NAMESPACE_HOSTS = ("schema.org", "json-schema.org", "spdx.org", "www.w3.org",
                   "example.com", "example.org", "localhost")


# ---------------------------------------------------------------------------
# links
# ---------------------------------------------------------------------------

def _extract_links(text: str) -> list[tuple[int, str]]:
    """Return (line_number, url) pairs, deduplicated per file."""
    found: list[tuple[int, str]] = []
    seen: set[str] = set()
    for lineno, line in enumerate(text.splitlines(), start=1):
        urls = [m.group(2) for m in MD_LINK.finditer(line)]
        urls += [m.group(1) for m in MD_REFDEF.finditer(line)]
        if not urls:
            urls = [m.group(0) for m in BARE_URL.finditer(line)]
        for url in urls:
            url = url.rstrip(TRAILING)
            if any(host in url for host in NAMESPACE_HOSTS):
                continue
            if url in seen:
                continue
            seen.add(url)
            found.append((lineno, url))
    return found


def _probe(url: str, timeout: int) -> dict:
    """Resolve a URL. Reports redirects because those are the fixable case."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            final = resp.geturl()
            return {"url": url, "status": resp.status, "final": final,
                    "redirected": final.rstrip("/") != url.rstrip("/")}
    except urllib.error.HTTPError as exc:
        return {"url": url, "status": exc.code, "final": None, "redirected": False}
    except Exception as exc:
        return {"url": url, "status": str(exc)[:80], "final": None, "redirected": False}


def gate_links(target: str, files: list[tuple[str, Path]], cap: int,
               timeout: int) -> GateResult:
    """Check links in documentation files.

    Only 404 and 410 are treated as findings. Timeouts, TLS failures, 403s and
    429s are counted as inconclusive and reported separately, because those
    describe the runner's network or a bot rule rather than the documentation.
    On a restricted network every request returns 403, and a gate that counted
    those as dead would condemn every project it looked at.
    """
    try:
        jobs: list[tuple[str, int, str]] = []
        seen: set[str] = set()
        for rel, path in files:
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for lineno, url in _extract_links(text):
                if url in seen:
                    continue
                seen.add(url)
                jobs.append((rel, lineno, url))
                if len(jobs) >= cap:
                    break
            if len(jobs) >= cap:
                break

        if not jobs:
            return GateResult("links", "skipped", "no external links found")

        findings: list[Finding] = []
        inconclusive = 0
        gated = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            futures = {pool.submit(_probe, url, timeout): (rel, lineno, url)
                       for rel, lineno, url in jobs}
            for fut in concurrent.futures.as_completed(futures):
                rel, lineno, url = futures[fut]
                res = fut.result()
                status = res["status"]
                if status in (404, 410):
                    findings.append(Finding(
                        target=target, gate="links", kind="dead_link",
                        message=f"{url} returns {status}",
                        tier=Tier.REVIEW_ONLY, path=rel, line=lineno,
                        evidence={"url": url, "status": status},
                    ))
                elif res["redirected"] and isinstance(status, int) and status < 400:
                    verdict, reason = redirects.classify(url, res["final"])
                    if verdict == redirects.GATE:
                        # An auth or consent wall says nothing about the docs.
                        gated += 1
                        continue
                    findings.append(Finding(
                        target=target, gate="links", kind="redirected_link",
                        message=f"{url} redirects to {res['final']} ({reason})",
                        tier=(Tier.DRAFTABLE if verdict == redirects.SAFE
                              else Tier.REVIEW_ONLY),
                        path=rel, line=lineno,
                        evidence={"url": url, "final": res["final"],
                                  "status": status, "verdict": verdict,
                                  "reason": reason},
                    ))
                elif not isinstance(status, int) or status >= 400:
                    inconclusive += 1

        return GateResult(
            "links", "ok",
            f"{len(jobs)} links checked, {len(findings)} findings, "
            f"{inconclusive} inconclusive, {gated} auth or consent redirects ignored",
            findings,
        )
    except Exception as exc:  # a gate must never take down the run
        return GateResult("links", "error", f"{type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# prose (Vale)
# ---------------------------------------------------------------------------

def find_project_style(repo_root: Path) -> Path | None:
    """Return the project's own Vale config, if it has one.

    This matters more than it looks. A style rule is an opinion, and a project
    that has not adopted one has not agreed to it. Enforcing an outside
    styleguide against someone else's repository produces exactly the pull
    request maintainers have learned to close unread.

    When a project ships its own config, the situation inverts: the rules are
    theirs, they already agreed, and a patch that brings the prose back in line
    is doing work they signed up for.
    """
    for name in (".vale.ini", "vale.ini", ".vale.yml", ".vale.yaml"):
        candidate = repo_root / name
        if candidate.exists():
            return candidate
    return None


def gate_prose(target: str, files: list[tuple[str, Path]], repo_root: Path,
               config_path: Path | None, timeout: int,
               project_owns_style: bool = False) -> GateResult:
    """Run Vale over markdown.

    Vale is only useful here because these targets include prose. When every
    target was an OpenAPI specification this gate had nothing to say, which is
    why it did not exist until now.

    Only rules that supply an explicit replacement are promoted to draftable.
    A rule that says a sentence is too long has identified something real and
    has not told us what to write instead.
    """
    if shutil.which("vale") is None:
        return GateResult("prose", "skipped", "vale not on PATH")
    if not files:
        return GateResult("prose", "skipped", "no prose files")
    if not project_owns_style:
        # Running an outside styleguide here produced hundreds of findings on
        # the first attempt, none of which the project had agreed to, and they
        # buried the handful of real ones. Detection without a shared standard
        # is not neutral observation, it is an opinion at volume.
        return GateResult(
            "prose", "skipped",
            "project ships no style configuration, so there is no agreed "
            "standard to enforce",
        )
    if config_path is None:
        return GateResult("prose", "skipped", "no style configuration available")

    cmd = ["vale", "--no-exit", "--output=JSON", f"--config={config_path}"]
    cmd += [str(p) for _, p in files]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return GateResult("prose", "error", f"vale exceeded {timeout}s")

    if not proc.stdout.strip():
        return GateResult("prose", "skipped",
                          f"vale produced no output (exit {proc.returncode})")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return GateResult("prose", "error", "vale output was not valid JSON")

    findings: list[Finding] = []
    for abs_path, alerts in payload.items():
        try:
            rel = str(Path(abs_path).resolve().relative_to(repo_root.resolve()))
        except ValueError:
            rel = abs_path
        for alert in alerts:
            action = alert.get("Action") or {}
            params = action.get("Params") or []
            # Vale supplies a replacement only for substitution-style rules.
            replacement = params[0] if action.get("Name") == "replace" and params else None
            # A replacement is only patchable when the project adopted the
            # rule. Otherwise this is an outsider's preference and belongs in
            # the review pile at most.
            draftable = bool(replacement) and project_owns_style
            findings.append(Finding(
                target=target, gate="prose",
                kind="style_replace" if draftable else "style_note",
                message=f"{alert.get('Check')}: {alert.get('Message')}",
                tier=Tier.DRAFTABLE if draftable else Tier.REVIEW_ONLY,
                path=rel, line=alert.get("Line"),
                evidence={"match": alert.get("Match"),
                          "replacement": replacement,
                          "span": alert.get("Span"),
                          "check": alert.get("Check")},
            ))
    scope = ("project's own style rules" if project_owns_style
             else "external styleguide, detection only")
    return GateResult("prose", "ok",
                      f"{len(findings)} style findings across {len(payload)} "
                      f"files ({scope})", findings)


# ---------------------------------------------------------------------------
# JSON Schema validity
# ---------------------------------------------------------------------------

def gate_jsonschema(target: str, rel: str, path: Path) -> GateResult:
    """Validate a JSON Schema document against its declared meta-schema.

    MCP publishes JSON Schema, not OpenAPI. Running the OpenAPI validator over
    it would report a missing `openapi` field as a defect, which is a category
    error dressed up as a finding.
    """
    try:
        doc = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        return GateResult("jsonschema", "ok", "document does not parse", [
            Finding(target=target, gate="jsonschema", kind="unparseable",
                    message=f"does not parse: {exc}", tier=Tier.REVIEW_ONLY, path=rel)
        ])

    declared = doc.get("$schema")
    if not declared:
        return GateResult("jsonschema", "ok", "no $schema declared", [
            Finding(target=target, gate="jsonschema", kind="no_schema_decl",
                    message="document declares no $schema",
                    tier=Tier.REVIEW_ONLY, path=rel)
        ])

    try:
        import jsonschema
        validator_cls = jsonschema.validators.validator_for(doc)
        validator_cls.check_schema(doc)
    except ImportError:
        return GateResult("jsonschema", "skipped", "jsonschema not installed")
    except Exception as exc:
        return GateResult("jsonschema", "ok", "schema is invalid", [
            Finding(target=target, gate="jsonschema", kind="invalid_schema",
                    message=str(exc).splitlines()[0][:200],
                    tier=Tier.REVIEW_ONLY, path=rel)
        ])

    defs = len(doc.get("$defs") or doc.get("definitions") or {})
    return GateResult("jsonschema", "ok",
                      f"valid against {declared}, {defs} definitions")


# ---------------------------------------------------------------------------
# artie (OpenAPI AI-readiness), benchmark targets only
# ---------------------------------------------------------------------------

#: artie check names whose gaps cannot be safely drafted, mapped to the kind
#: recorded so the report can explain the refusal.
UNSAFE_CHECKS = {
    "Example Coverage": "missing_example",
    "Error Documentation": "missing_error_docs",
    "Parameter Naming": "parameter_naming",
    "Schema Complexity": "schema_complexity",
    "Auth Clarity": "auth_clarity",
}


def gate_artie(target: str, path: Path, threshold: float, timeout: int,
               generation: bool) -> GateResult:
    """Score an OpenAPI document for AI-readiness.

    Detection only. Every low-scoring check here needs knowledge of how the API
    actually behaves, which is exactly the knowledge this pipeline does not
    have, so findings are recorded as refused rather than drafted.
    """
    if shutil.which("artie") is None:
        return GateResult("artie", "skipped", "artie not on PATH")

    cmd = ["artie", "check", str(path), "--output", "json"]
    if not generation:
        cmd.append("--no-generation")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return GateResult("artie", "error", f"artie exceeded {timeout}s")

    if not proc.stdout.strip():
        return GateResult("artie", "error",
                          f"no output (exit {proc.returncode})")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return GateResult("artie", "error", "output was not valid JSON")

    checks = payload.get("checks")
    if not isinstance(checks, list):
        return GateResult("artie", "error", "unexpected output shape")

    scores, findings, skipped = [], [], []
    for check in checks:
        if not isinstance(check, dict):
            continue
        name = check.get("name", "unnamed")
        score = check.get("score")
        # A check that could not run carries score null. Averaging those in as
        # zero would turn a missing measurement into a bad grade.
        if not check.get("evaluable") or not isinstance(score, (int, float)):
            skipped.append(name)
            continue
        scores.append(float(score))
        if float(score) < threshold:
            findings.append(Finding(
                target=target, gate="artie",
                kind=UNSAFE_CHECKS.get(name, "low_score"),
                message=f"{name} scored {score:g}/10",
                tier=Tier.REFUSED if name in UNSAFE_CHECKS else Tier.REVIEW_ONLY,
                evidence={"check": name, "score": score,
                          "findings": check.get("findings", [])[:5]},
            ))

    if not scores:
        return GateResult("artie", "error", "no evaluable checks")
    mean = sum(scores) / len(scores)
    summary = f"mean {mean:.1f}/10 across {len(scores)} checks"
    if skipped:
        summary += f"; not evaluable: {', '.join(skipped)}"
    return GateResult("artie", "ok", summary, findings)
