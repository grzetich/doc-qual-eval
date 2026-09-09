# Proposal 41c25f8393

- Target: `mcp-python-sdk`
- File: `docs/get-started/installation.md`

## Why

The documented URL redirects. Pointing it at the resolved location removes a hop and survives the redirect being retired.

## How this was verified

Requested https://opentelemetry-python.readthedocs.io/, followed redirects to https://opentelemetry-python.readthedocs.io/en/latest/ (HTTP 200). Classified as a genuine move: same host, resource preserved, canonical form of the same page.

## Patch

```diff
--- a/docs/get-started/installation.md
+++ b/docs/get-started/installation.md
@@ -32,7 +32,7 @@
 * [`starlette`](https://www.starlette.io/), [`uvicorn`](https://www.uvicorn.org/), [`sse-starlette`](https://pypi.org/project/sse-starlette/), and [`python-multipart`](https://pypi.org/project/python-multipart/): the HTTP *server* transports.
 * [`jsonschema`](https://pypi.org/project/jsonschema/): validates a tool's structured output against its declared output schema.
 * [`pyjwt[crypto]`](https://pyjwt.readthedocs.io/): OAuth token handling for authorization.
-* [`opentelemetry-api`](https://opentelemetry-python.readthedocs.io/): just the lightweight API, so the SDK's tracing middleware costs nothing unless you install an OpenTelemetry SDK and exporter yourself.
+* [`opentelemetry-api`](https://opentelemetry-python.readthedocs.io/en/latest/): just the lightweight API, so the SDK's tracing middleware costs nothing unless you install an OpenTelemetry SDK and exporter yourself.
 * [`typing-extensions`](https://typing-extensions.readthedocs.io/) and [`typing-inspection`](https://pypi.org/project/typing-inspection/): modern typing features on Python 3.10.
 * [`pywin32`](https://pypi.org/project/pywin32/): Windows only, used for `stdio` subprocess management.
```

Apply with `git apply` from the target repository root. This patch was drafted automatically and has not been opened anywhere. Read it before you send it.
