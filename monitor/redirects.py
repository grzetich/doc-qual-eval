"""Deciding which redirects are safe to patch.

This module exists because the first test run of this pipeline drafted three
patches that would have replaced working GitHub issue links with
`github.com/login?return_to=...`. The server really did return 200 at that
URL, so a naive "follow the redirect and record where you land" check reported
it as verified. It was verified. It was also wrong.

A redirect is only evidence that the documented URL should change when the
redirect represents a move. Most redirects on the open web represent something
else: an auth wall, a consent screen, a locale guess, a tracking bounce, or a
session. Following those and writing down the destination bakes this runner's
own unauthenticated, cookie-less, region-specific session into someone's
documentation.

So the test is not "did it redirect" but "does the destination still identify
the same resource".
"""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

#: Query parameters that carry the original destination. Their presence means
#: the server is holding the real URL hostage behind a gate, not moving it.
BOUNCE_PARAMS = {"return_to", "returnto", "redirect_uri", "redirect_to",
                 "redirect", "next", "continue", "dest", "destination",
                 "callback", "service", "target"}

#: Path fragments that indicate a gate rather than a destination.
GATE_SEGMENTS = ("/login", "/signin", "/sign-in", "/signup", "/sign-up",
                 "/auth", "/oauth", "/sso", "/session", "/account",
                 "/accounts", "/consent", "/cookie", "/privacy-gate",
                 "/challenge", "/captcha", "/verify", "/checkpoint")

SAFE = "safe"          # a real move, patchable
REVIEW = "review"      # plausibly a move, needs a person
GATE = "gate"          # an auth or consent wall, not a documentation problem


def classify(url: str, final: str) -> tuple[str, str]:
    """Return (verdict, reason) for a redirect from `url` to `final`."""
    if not final or final.rstrip("/") == url.rstrip("/"):
        return GATE, "no meaningful redirect"

    src, dst = urlparse(url), urlparse(final)

    query = {k.lower() for k in parse_qs(dst.query)}
    if query & BOUNCE_PARAMS:
        return GATE, (
            "destination carries a return parameter, so this is a gate "
            "holding the original URL rather than a move"
        )

    lowered = dst.path.lower()
    if any(seg in lowered for seg in GATE_SEGMENTS):
        return GATE, "destination looks like an auth or consent screen"

    if src.netloc.lower() != dst.netloc.lower():
        return REVIEW, (
            f"redirect crosses hosts, {src.netloc} to {dst.netloc}; a person "
            f"should confirm the new host is the intended home"
        )

    # Same host. A redirect to the site root or to a bare section index has
    # dropped the specific resource, which usually means the page is gone and
    # the server is being polite rather than helpful.
    if dst.path.strip("/") == "":
        return REVIEW, "redirects to the site root, so the page is likely gone"

    src_tail = src.path.rstrip("/").rsplit("/", 1)[-1].lower()
    dst_tail = dst.path.rstrip("/").rsplit("/", 1)[-1].lower()
    if src_tail and dst_tail and src_tail != dst_tail:
        if len(dst.path.strip("/").split("/")) < len(src.path.strip("/").split("/")):
            return REVIEW, (
                "destination is shallower than the source, so the specific "
                "page may have been folded into an index"
            )

    return SAFE, "same host, resource preserved, canonical form of the same page"
