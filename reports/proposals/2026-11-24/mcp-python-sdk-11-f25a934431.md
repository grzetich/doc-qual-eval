# Proposal f25a934431

- Target: `mcp-python-sdk`
- File: `docs/servers/uri-templates.md`

## Why

The documented URL redirects. Pointing it at the resolved location removes a hop and survives the redirect being retired.

## How this was verified

Requested https://modelcontextprotocol.io/specification/latest/server/resources, followed redirects to https://modelcontextprotocol.io/specification/2026-07-28/server/resources (HTTP 200). Classified as a genuine move: same host, resource preserved, canonical form of the same page.

## Patch

```diff
--- a/docs/servers/uri-templates.md
+++ b/docs/servers/uri-templates.md
@@ -13,7 +13,7 @@
 URIs, plus a security layer that rejects values that would resolve
 outside the directory you intend to serve. For the protocol-level
 details (message formats, lifecycle, pagination) see the
-[MCP resources specification](https://modelcontextprotocol.io/specification/latest/server/resources).
+[MCP resources specification](https://modelcontextprotocol.io/specification/2026-07-28/server/resources).
 
 ## The full operator set
```

Apply with `git apply` from the target repository root. This patch was drafted automatically and has not been opened anywhere. Read it before you send it.
