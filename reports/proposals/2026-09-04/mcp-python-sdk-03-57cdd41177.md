# Proposal 57cdd41177

- Target: `mcp-python-sdk`
- File: `README.md`

## Why

The documented URL redirects. Pointing it at the resolved location removes a hop and survives the redirect being retired.

## How this was verified

Requested https://modelcontextprotocol.io, followed redirects to https://modelcontextprotocol.io/docs/2026-07-28/getting-started/intro (HTTP 200). Classified as a genuine move: same host, resource preserved, canonical form of the same page.

## Patch

```diff
--- a/README.md
+++ b/README.md
@@ -28,7 +28,7 @@
 
 ## What is MCP?
 
-The [Model Context Protocol](https://modelcontextprotocol.io) lets you build servers that expose data and functionality to LLM applications in a secure, standardized way. Think of it like a web API, but designed for LLM interactions. With this SDK you can:
+The [Model Context Protocol](https://modelcontextprotocol.io/docs/2026-07-28/getting-started/intro) lets you build servers that expose data and functionality to LLM applications in a secure, standardized way. Think of it like a web API, but designed for LLM interactions. With this SDK you can:
 
 - **Build MCP servers** that expose tools, resources, and prompts to any MCP host
 - **Build MCP clients** that connect to any MCP server
```

Apply with `git apply` from the target repository root. This patch was drafted automatically and has not been opened anywhere. Read it before you send it.
