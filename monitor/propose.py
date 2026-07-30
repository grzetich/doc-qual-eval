"""Turning findings into reviewable patches.

The rule for this module: a proposal may only be built from evidence already
in hand. Nothing here asks a model what the fix should be. A redirect target
came from following the redirect. A style replacement came from the linter's
own rule. A copied description came from elsewhere in the same file.

That constraint is what keeps the output reviewable. A maintainer can check
any diff in this queue against the stated verification in a few seconds. The
moment a proposal requires them to trust the tool's judgement instead, it
belongs in the review-only list.

Nothing here opens a pull request. The queue is for a human to work through.
"""

from __future__ import annotations

import difflib
from pathlib import Path

from . import redirects
from .model import Finding, Proposal, Tier


def _unified(rel: str, before: str, after: str) -> str:
    diff = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=f"a/{rel}", tofile=f"b/{rel}", n=3,
    )
    return "".join(diff)


def _edit_line(path: Path, line_no: int, old: str, new: str) -> tuple[str, str] | None:
    """Replace `old` with `new` on one line. Returns (before, after) or None.

    Refuses when the target string is absent or appears more than once on the
    line. An ambiguous replacement is not a fix, it is a coin flip.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    lines = text.splitlines(keepends=True)
    if not (1 <= line_no <= len(lines)):
        return None
    line = lines[line_no - 1]
    if line.count(old) != 1:
        return None
    lines[line_no - 1] = line.replace(old, new)
    return text, "".join(lines)


def propose_link_redirect(finding: Finding, repo_root: Path) -> Proposal | None:
    """Point a link at wherever it already ends up.

    Verifiable: the replacement URL is the one the server returned after
    following the redirect, not a guess.
    """
    url = finding.evidence.get("url")
    final = finding.evidence.get("final")
    if not url or not final or url == final:
        return None
    # Re-check the classification here rather than trusting the gate. A patch
    # that rewrites a working link into a login URL is worse than no tool at
    # all, and this is the last place to catch it.
    verdict, reason = redirects.classify(url, final)
    if verdict != redirects.SAFE:
        return None

    path = repo_root / finding.path
    edited = _edit_line(path, finding.line, url, final)
    if edited is None:
        return None
    before, after = edited
    return Proposal(
        finding_id=finding.id,
        target=finding.target,
        path=finding.path,
        diff=_unified(finding.path, before, after),
        rationale=(
            f"The documented URL redirects. Pointing it at the resolved "
            f"location removes a hop and survives the redirect being retired."
        ),
        verification=(
            f"Requested {url}, followed redirects to {final} "
            f"(HTTP {finding.evidence.get('status')}). Classified as a genuine "
            f"move: {reason}."
        ),
    )


def propose_style_replacement(finding: Finding, repo_root: Path) -> Proposal | None:
    """Apply a linter substitution the rule itself supplied.

    Verifiable: the replacement text comes from the Vale rule, not from a
    model. Rules without an explicit replacement never reach this function.
    """
    match = finding.evidence.get("match")
    replacement = finding.evidence.get("replacement")
    if not match or not replacement or match == replacement:
        return None

    path = repo_root / finding.path
    edited = _edit_line(path, finding.line, match, replacement)
    if edited is None:
        return None
    before, after = edited
    return Proposal(
        finding_id=finding.id,
        target=finding.target,
        path=finding.path,
        diff=_unified(finding.path, before, after),
        rationale=f"Style rule {finding.evidence.get('check')} supplies this replacement.",
        verification=(
            f"Replacement text came from the rule definition, not from "
            f"generation. Single unambiguous occurrence on line {finding.line}."
        ),
    )


BUILDERS = {
    "redirected_link": propose_link_redirect,
    "style_replace": propose_style_replacement,
}


def build(findings: list[Finding], repo_root: Path) -> tuple[list[Proposal], list[Finding]]:
    """Draft patches for draftable findings.

    Returns the proposals and the findings that stayed unproposed. A draftable
    finding can still fail to produce a patch, usually because the line moved
    or the match was ambiguous. Those fall back to review rather than being
    forced into a guess.
    """
    proposals: list[Proposal] = []
    unproposed: list[Finding] = []
    for finding in findings:
        if finding.tier is not Tier.DRAFTABLE:
            continue
        builder = BUILDERS.get(finding.kind)
        proposal = builder(finding, repo_root) if builder else None
        if proposal is None:
            unproposed.append(finding)
        else:
            proposals.append(proposal)
    return proposals, unproposed
