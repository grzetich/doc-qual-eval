# Proposal 78f0094b36

- Target: `mcp-python-sdk`
- File: `docs/advanced/skills.md`

## Why

The documented URL redirects. Pointing it at the resolved location removes a hop and survives the redirect being retired.

## How this was verified

Requested https://agentskills.io/, followed redirects to https://agentskills.io/home (HTTP 200). Classified as a genuine move: same host, resource preserved, canonical form of the same page.

## Patch

```diff
--- a/docs/advanced/skills.md
+++ b/docs/advanced/skills.md
@@ -1,7 +1,7 @@
 # Skills
 
 [SEP-2640](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2640) defines a
-convention for serving [Agent Skills](https://agentskills.io/) over MCP. A skill is just a
+convention for serving [Agent Skills](https://agentskills.io/home) over MCP. A skill is just a
 directory of files — at minimum a `SKILL.md` with YAML frontmatter — that you expose as ordinary
 MCP resources, conventionally under a `skill://` URI.
```

Apply with `git apply` from the target repository root. This patch was drafted automatically and has not been opened anywhere. Read it before you send it.
