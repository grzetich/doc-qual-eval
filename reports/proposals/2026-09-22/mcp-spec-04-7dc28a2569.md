# Proposal 7dc28a2569

- Target: `mcp-spec`
- File: `docs/community/interest-groups/primitive-grouping.mdx`

## Why

The documented URL redirects. Pointing it at the resolved location removes a hop and survives the redirect being retired.

## How this was verified

Requested https://github.com/modelcontextprotocol/experimental-ext-grouping, followed redirects to https://github.com/modelcontextprotocol/progressive-disclosure-wg (HTTP 200). Classified as a genuine move: same host, resource preserved, canonical form of the same page.

## Patch

```diff
--- a/docs/community/interest-groups/primitive-grouping.mdx
+++ b/docs/community/interest-groups/primitive-grouping.mdx
@@ -121,7 +121,7 @@
 
 ## Resources
 
-- [Experimental repo](https://github.com/modelcontextprotocol/experimental-ext-grouping) - incubation space for the Primitive Grouping Interest Group
+- [Experimental repo](https://github.com/modelcontextprotocol/progressive-disclosure-wg) - incubation space for the Primitive Grouping Interest Group
 
 ## Changelog
```

Apply with `git apply` from the target repository root. This patch was drafted automatically and has not been opened anywhere. Read it before you send it.
