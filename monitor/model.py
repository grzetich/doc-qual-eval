"""Findings, proposals, and the tier system that decides which is which.

The tier is the most important idea in this codebase. A finding is something
the pipeline noticed. A proposal is a patch it is willing to put in front of a
human. Those are different bars, and the gap between them is deliberate.

A tool that drafts a fix for everything it finds produces confident, plausible,
unverifiable patches. Maintainers have learned to distrust exactly that. So a
finding is only promoted to a proposal when the fix can be checked against
something real: a redirect that was followed, a string that was already present
elsewhere in the same file, a linter rule that supplied its own replacement.

Everything else is reported and left alone, with the reason stated.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class Tier(str, Enum):
    """How much the pipeline is willing to do about a finding."""

    #: The fix is derived from evidence, not invented. Draft a diff.
    DRAFTABLE = "draftable"

    #: Real finding, but any fix would be a guess about the correct value.
    #: Report the location and let a human decide.
    REVIEW_ONLY = "review_only"

    #: Fixing this requires knowing how the API actually behaves. Writing a
    #: plausible answer here is worse than leaving the gap, because a wrong
    #: example gets copied into someone's code.
    REFUSED = "refused"


#: Why the pipeline declines to draft for particular finding kinds. Stated in
#: the report so the refusal reads as a decision rather than a gap in coverage.
REFUSAL_REASONS = {
    "missing_example": (
        "Writing an example requires knowing what the endpoint actually "
        "returns. An invented example is worse than a missing one because it "
        "gets copied."
    ),
    "missing_error_docs": (
        "Error conditions cannot be inferred from a schema. Documenting a "
        "status code the API does not return is a defect, not a fix."
    ),
    "parameter_naming": (
        "Renaming a parameter is a breaking change to the API, not an edit to "
        "the documentation."
    ),
    "schema_complexity": (
        "Restructuring a schema is a design decision owned by the maintainers."
    ),
    "auth_clarity": (
        "Auth behaviour cannot be verified from the document alone."
    ),
    "dead_link": (
        "The link is gone and the correct replacement is unknowable from here. "
        "Reported with its location so a maintainer can retarget it."
    ),
}


@dataclass
class Finding:
    """Something a gate noticed."""

    target: str
    gate: str
    kind: str
    message: str
    tier: Tier
    path: str | None = None          # repo-relative file path
    line: int | None = None
    evidence: dict[str, Any] = field(default_factory=dict)

    @property
    def id(self) -> str:
        raw = f"{self.target}|{self.gate}|{self.kind}|{self.path}|{self.line}|{self.message}"
        return hashlib.sha1(raw.encode()).hexdigest()[:10]

    @property
    def refusal_reason(self) -> str | None:
        if self.tier is not Tier.REFUSED:
            return None
        return REFUSAL_REASONS.get(self.kind, "No verifiable fix available.")

    def to_dict(self) -> dict:
        out = asdict(self)
        out["tier"] = self.tier.value
        out["id"] = self.id
        if self.tier is Tier.REFUSED:
            out["refusal_reason"] = self.refusal_reason
        return out


@dataclass
class Proposal:
    """A reviewable patch. Never opened automatically."""

    finding_id: str
    target: str
    path: str
    diff: str
    rationale: str
    #: What was actually checked to justify this edit. If this is empty the
    #: proposal should not exist.
    verification: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GateResult:
    """Outcome of running one gate against one target.

    status distinguishes a gate that ran from a gate that could not. `error`
    means this pipeline failed, not that the documentation did. Conflating the
    two lets an expired token or a slow runner masquerade as a docs defect.
    """

    gate: str
    status: str  # ok | error | skipped
    summary: str
    findings: list[Finding] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "gate": self.gate,
            "status": self.status,
            "summary": self.summary,
            "findings": [f.to_dict() for f in self.findings],
        }
