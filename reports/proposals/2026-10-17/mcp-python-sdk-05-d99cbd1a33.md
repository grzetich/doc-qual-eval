# Proposal d99cbd1a33

- Target: `mcp-python-sdk`
- File: `docs/advanced/low-level-server.md`

## Why

The documented URL redirects. Pointing it at the resolved location removes a hop and survives the redirect being retired.

## How this was verified

Requested https://modelcontextprotocol.io/specification/latest/basic#json-schema-usage, followed redirects to https://modelcontextprotocol.io/specification/2026-07-28/basic (HTTP 200). Classified as a genuine move: same host, resource preserved, canonical form of the same page.

## Patch

```diff
--- a/docs/advanced/low-level-server.md
+++ b/docs/advanced/low-level-server.md
@@ -119,7 +119,7 @@
 
 ## The dialect is JSON Schema 2020-12
 
-`input_schema` and `output_schema` are JSON Schema, and the [MCP specification](https://modelcontextprotocol.io/specification/latest/basic#json-schema-usage) fixes the dialect: a schema with no `$schema` key is **JSON Schema 2020-12**. The schemas `MCPServer` generates rely on that default (Pydantic writes 2020-12 and omits the key), and a hand-written dict is held to it too, so the full 2020-12 vocabulary is available:
+`input_schema` and `output_schema` are JSON Schema, and the [MCP specification](https://modelcontextprotocol.io/specification/2026-07-28/basic) fixes the dialect: a schema with no `$schema` key is **JSON Schema 2020-12**. The schemas `MCPServer` generates rely on that default (Pydantic writes 2020-12 and omits the key), and a hand-written dict is held to it too, so the full 2020-12 vocabulary is available:
 
 ```python title="server.py" hl_lines="8 14-15"
 --8<-- "docs_src/lowlevel/tutorial007.py"
```

Apply with `git apply` from the target repository root. This patch was drafted automatically and has not been opened anywhere. Read it before you send it.
