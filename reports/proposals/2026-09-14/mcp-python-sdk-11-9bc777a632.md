# Proposal 9bc777a632

- Target: `mcp-python-sdk`
- File: `examples/stories/apps/README.md`

## Why

The documented URL redirects. Pointing it at the resolved location removes a hop and survives the redirect being retired.

## How this was verified

Requested https://github.com/modelcontextprotocol/modelcontextprotocol/issues/2133, followed redirects to https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2133 (HTTP 200). Classified as a genuine move: same host, resource preserved, canonical form of the same page.

## Patch

```diff
--- a/examples/stories/apps/README.md
+++ b/examples/stories/apps/README.md
@@ -33,7 +33,7 @@
 ## Spec
 
 [MCP Apps — extensions](https://modelcontextprotocol.io/specification/draft/extensions/apps)
-· [SEP-2133 — extensions capability](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/2133)
+· [SEP-2133 — extensions capability](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2133)
 
 ## See also
```

Apply with `git apply` from the target repository root. This patch was drafted automatically and has not been opened anywhere. Read it before you send it.
