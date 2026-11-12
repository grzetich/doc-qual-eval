# Proposal 2fa5d50fba

- Target: `mcp-typescript-sdk`
- File: `docs/advanced/opentelemetry.md`

## Why

The documented URL redirects. Pointing it at the resolved location removes a hop and survives the redirect being retired.

## How this was verified

Requested https://modelcontextprotocol.io/community/seps/414-request-meta, followed redirects to https://modelcontextprotocol.io/seps/414-request-meta (HTTP 200). Classified as a genuine move: same host, resource preserved, canonical form of the same page.

## Patch

```diff
--- a/docs/advanced/opentelemetry.md
+++ b/docs/advanced/opentelemetry.md
@@ -92,7 +92,7 @@
 :::
 
 ::: info
-Any SDK that follows [SEP-414](https://modelcontextprotocol.io/community/seps/414-request-meta) reads the same `traceparent`, `tracestate` and `baggage` keys, so a Python or C# peer joins the trace too.
+Any SDK that follows [SEP-414](https://modelcontextprotocol.io/seps/414-request-meta) reads the same `traceparent`, `tracestate` and `baggage` keys, so a Python or C# peer joins the trace too.
 :::
 
 ## Read the duration metrics
```

Apply with `git apply` from the target repository root. This patch was drafted automatically and has not been opened anywhere. Read it before you send it.
