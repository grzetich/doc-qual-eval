# Proposal 9400e69adf

- Target: `mcp-spec`
- File: `docs/community/interest-groups/agents.mdx`

## Why

The documented URL redirects. Pointing it at the resolved location removes a hop and survives the redirect being retired.

## How this was verified

Requested https://github.com/modelcontextprotocol/agents-wg, followed redirects to https://github.com/modelcontextprotocol/agents-ig (HTTP 200). Classified as a genuine move: same host, resource preserved, canonical form of the same page.

## Patch

```diff
--- a/docs/community/interest-groups/agents.mdx
+++ b/docs/community/interest-groups/agents.mdx
@@ -82,7 +82,7 @@
 ## Resources
 
 - Group repository:
-  [modelcontextprotocol/agents-wg](https://github.com/modelcontextprotocol/agents-wg)
+  [modelcontextprotocol/agents-wg](https://github.com/modelcontextprotocol/agents-ig)
 
 ## Discussion Topics
```

Apply with `git apply` from the target repository root. This patch was drafted automatically and has not been opened anywhere. Read it before you send it.
