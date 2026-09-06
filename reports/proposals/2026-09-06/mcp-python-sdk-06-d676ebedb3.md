# Proposal d676ebedb3

- Target: `mcp-python-sdk`
- File: `docs/get-started/installation.md`

## Why

The documented URL redirects. Pointing it at the resolved location removes a hop and survives the redirect being retired.

## How this was verified

Requested https://anyio.readthedocs.io/, followed redirects to https://anyio.readthedocs.io/en/stable/ (HTTP 200). Classified as a genuine move: same host, resource preserved, canonical form of the same page.

## Patch

```diff
--- a/docs/get-started/installation.md
+++ b/docs/get-started/installation.md
@@ -26,7 +26,7 @@
 You don't need to know any of this to use the SDK, but if you're wondering what each dependency is for:
 
 * `mcp-types`: every protocol type (requests, results, content blocks) as its own package, versioned in lockstep with the SDK. Code that depends on `mcp` imports it through the `mcp.types` alias (every `from mcp.types import ...` in these docs); import `mcp_types` directly only in a project that installs `mcp-types` without the SDK.
-* [`anyio`](https://anyio.readthedocs.io/): the async runtime. The whole SDK is written against anyio, so it runs on either `asyncio` or `trio`.
+* [`anyio`](https://anyio.readthedocs.io/en/stable/): the async runtime. The whole SDK is written against anyio, so it runs on either `asyncio` or `trio`.
 * [`pydantic`](https://docs.pydantic.dev/): what every `mcp.types` model is built on, plus all schema generation and validation.
 * [`httpx2`](https://pypi.org/project/httpx2/): the HTTP client behind the Streamable HTTP and SSE *client* transports, with server-sent events support built in.
 * [`starlette`](https://www.starlette.io/), [`uvicorn`](https://www.uvicorn.org/), [`sse-starlette`](https://pypi.org/project/sse-starlette/), and [`python-multipart`](https://pypi.org/project/python-multipart/): the HTTP *server* transports.
```

Apply with `git apply` from the target repository root. This patch was drafted automatically and has not been opened anywhere. Read it before you send it.
