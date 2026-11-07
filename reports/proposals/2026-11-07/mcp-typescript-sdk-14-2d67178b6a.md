# Proposal 2d67178b6a

- Target: `mcp-typescript-sdk`
- File: `README.md`

## Why

The documented URL redirects. Pointing it at the resolved location removes a hop and survives the redirect being retired.

## How this was verified

Requested https://modelcontextprotocol.io/specification/latest, followed redirects to https://modelcontextprotocol.io/specification/2026-07-28 (HTTP 200). Classified as a genuine move: same host, resource preserved, canonical form of the same page.

## Patch

```diff
--- a/README.md
+++ b/README.md
@@ -148,7 +148,7 @@
 - [Troubleshooting](docs/troubleshooting.md) — common errors and their fixes
 - [API reference](https://ts.sdk.modelcontextprotocol.io/v2/api/)
 - [MCP documentation](https://modelcontextprotocol.io/docs)
-- [MCP specification](https://modelcontextprotocol.io/specification/latest)
+- [MCP specification](https://modelcontextprotocol.io/specification/2026-07-28)
 
 ### Building docs locally
```

Apply with `git apply` from the target repository root. This patch was drafted automatically and has not been opened anywhere. Read it before you send it.
