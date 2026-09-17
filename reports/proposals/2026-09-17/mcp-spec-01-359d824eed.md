# Proposal 359d824eed

- Target: `mcp-spec`
- File: `README.md`

## Why

The documented URL redirects. Pointing it at the resolved location removes a hop and survives the redirect being retired.

## How this was verified

Requested https://modelcontextprotocol.io, followed redirects to https://modelcontextprotocol.io/docs/2026-07-28/getting-started/intro (HTTP 200). Classified as a genuine move: same host, resource preserved, canonical form of the same page.

## Patch

```diff
--- a/README.md
+++ b/README.md
@@ -1,6 +1,6 @@
 # Model Context Protocol (MCP)
 
-_Just heard of MCP and not sure where to start? Check out our [documentation website](https://modelcontextprotocol.io)._
+_Just heard of MCP and not sure where to start? Check out our [documentation website](https://modelcontextprotocol.io/docs/2026-07-28/getting-started/intro)._
 
 This repo contains the:
```

Apply with `git apply` from the target repository root. This patch was drafted automatically and has not been opened anywhere. Read it before you send it.
