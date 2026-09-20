# Proposal b168171a30

- Target: `mcp-python-sdk`
- File: `docs/get-started/installation.md`

## Why

The documented URL redirects. Pointing it at the resolved location removes a hop and survives the redirect being retired.

## How this was verified

Requested https://typing-extensions.readthedocs.io/, followed redirects to https://typing-extensions.readthedocs.io/en/latest/ (HTTP 200). Classified as a genuine move: same host, resource preserved, canonical form of the same page.

## Patch

```diff
--- a/docs/get-started/installation.md
+++ b/docs/get-started/installation.md
@@ -33,7 +33,7 @@
 * [`jsonschema`](https://pypi.org/project/jsonschema/): validates a tool's structured output against its declared output schema.
 * [`pyjwt[crypto]`](https://pyjwt.readthedocs.io/): OAuth token handling for authorization.
 * [`opentelemetry-api`](https://opentelemetry-python.readthedocs.io/): just the lightweight API, so the SDK's tracing middleware costs nothing unless you install an OpenTelemetry SDK and exporter yourself.
-* [`typing-extensions`](https://typing-extensions.readthedocs.io/) and [`typing-inspection`](https://pypi.org/project/typing-inspection/): modern typing features on Python 3.10.
+* [`typing-extensions`](https://typing-extensions.readthedocs.io/en/latest/) and [`typing-inspection`](https://pypi.org/project/typing-inspection/): modern typing features on Python 3.10.
 * [`pywin32`](https://pypi.org/project/pywin32/): Windows only, used for `stdio` subprocess management.
 
 ## Optional extras
```

Apply with `git apply` from the target repository root. This patch was drafted automatically and has not been opened anywhere. Read it before you send it.
