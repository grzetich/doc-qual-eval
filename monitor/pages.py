"""Checking the artifact a developer actually hands to an AI tool.

The rest of this pipeline grades specifications, and specifications are not
what gets pasted into a chat box. Finding Anthropic's OpenAPI document meant
reading `.stats.yml` for a storage bucket URL with a hash filename. Box's
specification is roughly 441,000 estimated tokens. Nobody is pasting either.

What gets pasted is a page. A developer working on cash balances copies the
cash balance page URL, because copying a URL is the muscle memory move, and
asks a model to build the integration from that.

So the page is the unit worth measuring, and it has two properties the
specification does not. It is what actually reaches the model, and it belongs
to the documentation team rather than to engineering, which means a finding
about it is a finding somebody can act on.

The first check here needs no model and no API key: fetch the URL the way an
agent would and look at what arrives. That alone catches the case this module
was written for, a page that reads as thorough in a browser and arrives as a
short list of links to somewhere else.
"""

from __future__ import annotations

import re
import urllib.error
import urllib.request

from .model import Finding, GateResult, Tier

#: Sent by tools that fetch on a user's behalf. Some documentation sites
#: content-negotiate markdown for these, which is worth knowing about, so the
#: fetch is deliberately not disguised as a browser.
AGENT_UA = "docs-quality-monitor (+https://github.com/grzetich/docs-quality-monitor)"

CODE_FENCE = re.compile(r"```|<pre[\s>]|<code[\s>]")
MD_LINK = re.compile(r"\[[^\]]+\]\([^)]+\)")
HTML_LINK = re.compile(r"<a\s[^>]*href=", re.I)
HTTP_VERB = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\s+/", re.I)
PATH_LIKE = re.compile(r"/v\d+/[A-Za-z0-9_/{}:.\-]+")
AUTH_WORDS = ("api key", "api_key", "bearer", "authorization", "auth token",
              "secret key", "oauth", "authenticate")
PARAM_SIGNALS = ("parameter", "required", "optional", "arguments", "| type |",
                 "query string", "request body")


def fetch_page(url: str, timeout: int = 45) -> tuple[str | None, dict]:
    """Fetch a documentation URL the way an agent would.

    No browser, no JavaScript execution, no cookies. If a page only becomes
    useful after client-side rendering, an agent never sees the useful version,
    and the point of this gate is to observe that rather than work around it.
    """
    request = urllib.request.Request(url, headers={
        "User-Agent": AGENT_UA,
        # Ask for markdown first. Sites that offer it will say so, and sites
        # that do not simply return HTML.
        "Accept": "text/markdown, text/plain;q=0.9, text/html;q=0.8",
    })
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return raw, {
                "status": response.status,
                "content_type": response.headers.get("content-type", ""),
                "final_url": response.geturl(),
                "bytes": len(raw),
            }
    except urllib.error.HTTPError as exc:
        return None, {"status": exc.code, "error": f"HTTP {exc.code}"}
    except Exception as exc:
        return None, {"status": None, "error": str(exc)[:150]}


def analyse(text: str) -> dict:
    """Describe what arrived, without judging it yet."""
    words = len(text.split())
    links = len(MD_LINK.findall(text)) + len(HTML_LINK.findall(text))
    lowered = text.lower()
    return {
        "words": words,
        "code_blocks": len(CODE_FENCE.findall(text)),
        "links": links,
        # A page that is mostly links to other pages is an index. An agent
        # given an index has been given a table of contents and asked to cook.
        "link_density": round(links / max(words / 100, 1), 2),
        "http_verbs": len(HTTP_VERB.findall(text)),
        "endpoint_paths": sorted(set(PATH_LIKE.findall(text)))[:12],
        "mentions_auth": any(word in lowered for word in AUTH_WORDS),
        "documents_params": any(signal in lowered for signal in PARAM_SIGNALS),
        "looks_like_html": "<html" in lowered or "<!doctype html" in lowered,
    }


def judge(target: str, url: str, shape: dict, meta: dict,
          min_words: int) -> list[Finding]:
    """Turn measurements into findings.

    Everything here is review only. The fix is to write documentation, which
    requires knowing what the endpoint does, so nothing on this page is
    draftable by the rules the rest of this pipeline follows.
    """
    findings: list[Finding] = []

    def add(kind: str, message: str, **evidence) -> None:
        findings.append(Finding(
            target=target, gate="page_fetch", kind=kind, message=message,
            tier=Tier.REVIEW_ONLY, path=url,
            evidence={"url": url, **meta, **evidence},
        ))

    if shape["looks_like_html"]:
        add("page_arrives_as_html",
            "page arrives as raw HTML, so an agent parses markup and site "
            "furniture alongside the documentation",
            content_type=meta.get("content_type"))

    if shape["words"] < min_words:
        add("page_too_thin",
            f"page carries {shape['words']} words, below the {min_words} word "
            f"floor for supporting an integration task",
            words=shape["words"])

    if shape["code_blocks"] == 0:
        add("page_has_no_examples",
            "page contains no code block, so a model working from it writes "
            "the call signature from training data rather than from the docs",
            words=shape["words"])

    # The case this module exists for: short, link heavy, no code. Reads as a
    # complete page in a browser because the browser renders the links as
    # navigation. Arrives as a table of contents.
    if (shape["links"] >= 2 and shape["code_blocks"] == 0
            and shape["words"] < min_words * 2):
        add("page_is_an_index",
            f"page reads as an index rather than a document: {shape['links']} "
            f"links, no code, {shape['words']} words. The content an agent "
            f"needs is one hop further on",
            links=shape["links"], words=shape["words"],
            link_density=shape["link_density"])

    if not shape["mentions_auth"]:
        add("page_omits_auth",
            "page never mentions authentication, so generated code has to "
            "guess the scheme",
            )

    if not shape["documents_params"] and shape["http_verbs"]:
        add("page_omits_parameters",
            "page names endpoints but documents no parameters, so generated "
            "calls are assembled from assumption",
            endpoints=shape["endpoint_paths"])

    return findings


def gate_page_fetch(target: str, pages: list[dict], min_words: int = 250,
                    timeout: int = 45) -> GateResult:
    """Fetch each documented page and report what an agent would receive."""
    if not pages:
        return GateResult("page_fetch", "skipped", "no pages configured")

    findings: list[Finding] = []
    fetched, failed = 0, 0
    for page in pages:
        url = page.get("url")
        if not url:
            continue
        text, meta = fetch_page(url, timeout)
        if text is None:
            # The pipeline could not reach the page. That is this runner's
            # problem, not the documentation's, and it is never a finding.
            failed += 1
            continue
        fetched += 1
        shape = analyse(text)
        findings += judge(target, url, shape, meta,
                          page.get("min_words", min_words))

    if fetched == 0:
        return GateResult("page_fetch", "error",
                          f"no pages could be fetched ({failed} failures)")
    summary = f"{fetched} pages fetched, {len(findings)} findings"
    if failed:
        summary += f", {failed} unreachable and not counted against the docs"
    return GateResult("page_fetch", "ok", summary, findings)
