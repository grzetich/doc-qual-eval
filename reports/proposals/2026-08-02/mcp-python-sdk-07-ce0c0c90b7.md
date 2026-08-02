# Proposal ce0c0c90b7

- Target: `mcp-python-sdk`
- File: `README.md`

## Why

The documented URL redirects. Pointing it at the resolved location removes a hop and survives the redirect being retired.

## How this was verified

Requested https://modelcontextprotocol.io/specification/latest, followed redirects to https://modelcontextprotocol.io/specification/2026-07-28 (HTTP 200). Classified as a genuine move: same host, resource preserved, canonical form of the same page.

## Patch

```diff
--- a/README.md
+++ b/README.md
@@ -126,4 +126,4 @@
 [protocol-badge]: https://img.shields.io/badge/protocol-modelcontextprotocol.io-blue.svg
 [protocol-url]: https://modelcontextprotocol.io
 [spec-badge]: https://img.shields.io/badge/spec-spec.modelcontextprotocol.io-blue.svg
-[spec-url]: https://modelcontextprotocol.io/specification/latest
+[spec-url]: https://modelcontextprotocol.io/specification/2026-07-28
```

Apply with `git apply` from the target repository root. This patch was drafted automatically and has not been opened anywhere. Read it before you send it.
