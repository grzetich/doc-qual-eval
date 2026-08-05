"""Collapsing findings that are all the same finding.

The same Anthropic SDK run produced twelve separate findings for one pattern:
`/issues/1783` redirecting to `/pull/1783`, repeated down a changelog. Reported
individually they would have consumed most of the proposal cap and pushed
anything else out of the queue.

Repetition also changes what the finding means. One instance is a typo. Twelve
identical instances are a convention, a generator, or a platform behaviour, and
the right response is to tell someone about the pattern rather than to send
twelve patches. So a collapsed group is demoted to review: a person should
decide whether the pattern is even wrong before anybody patches it.
"""

from __future__ import annotations

import re
from collections import defaultdict

from .model import Finding, Tier

#: Numbers are the usual difference between otherwise identical findings, so
#: they are normalised away when deciding whether two findings are the same.
DIGITS = re.compile(r"\d+")


def _signature(finding: Finding) -> tuple:
    """A key that ignores incidental differences like issue numbers."""
    evidence = finding.evidence or {}
    url = DIGITS.sub("#", str(evidence.get("url", "")))
    final = DIGITS.sub("#", str(evidence.get("final", "")))
    if url or final:
        detail = (url, final)
    else:
        detail = (DIGITS.sub("#", finding.message),)
    return (finding.target, finding.gate, finding.kind, finding.path) + detail


def collapse(findings: list[Finding], threshold: int = 3
             ) -> tuple[list[Finding], int]:
    """Group repeated findings. Returns (findings, number absorbed)."""
    groups: dict[tuple, list[Finding]] = defaultdict(list)
    for finding in findings:
        groups[_signature(finding)].append(finding)

    out: list[Finding] = []
    absorbed = 0
    for group in groups.values():
        if len(group) < threshold:
            out.extend(group)
            continue

        first = group[0]
        lines = sorted(f.line for f in group if f.line)
        absorbed += len(group) - 1
        out.append(Finding(
            target=first.target,
            gate=first.gate,
            kind=first.kind,
            message=(f"{len(group)} occurrences of the same pattern in "
                     f"{first.path}: {first.message}"),
            # A repeated pattern is a convention until someone says otherwise.
            tier=Tier.REVIEW_ONLY,
            path=first.path,
            line=lines[0] if lines else None,
            evidence={**first.evidence,
                      "occurrences": len(group),
                      "lines": lines[:25],
                      "collapsed": True,
                      "note": "Repeated at this scale this is a convention, a "
                              "generator, or platform behaviour rather than a "
                              "mistake. Confirm the pattern is wrong before "
                              "patching any of it."},
        ))
    return out, absorbed
