# Proposal 2c67387f85

- Target: `mcp-python-sdk`
- File: `docs/handlers/sampling-and-roots.md`

## Why

The documented URL redirects. Pointing it at the resolved location removes a hop and survives the redirect being retired.

## How this was verified

Requested https://github.com/modelcontextprotocol/modelcontextprotocol/issues/2577, followed redirects to https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2577 (HTTP 200). Classified as a genuine move: same host, resource preserved, canonical form of the same page.

## Patch

```diff
--- a/docs/handlers/sampling-and-roots.md
+++ b/docs/handlers/sampling-and-roots.md
@@ -5,7 +5,7 @@
 Both still work, on every protocol version the SDK speaks. But read the warning before you design around them:
 
 !!! warning "Deprecated by the 2026-07-28 specification"
-    Sampling and roots are deprecated as of `2026-07-28` ([SEP-2577](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/2577)). They remain fully functional and stay in the specification for at least twelve months before becoming eligible for removal, but new implementations should not build on them. The suggested migrations: integrate directly with your LLM provider's API instead of sampling, and pass directories via tool parameters, resource URIs, or server configuration instead of roots. The SDK-wide list is in **[Deprecated features](../deprecated.md)**.
+    Sampling and roots are deprecated as of `2026-07-28` ([SEP-2577](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2577)). They remain fully functional and stay in the specification for at least twelve months before becoming eligible for removal, but new implementations should not build on them. The suggested migrations: integrate directly with your LLM provider's API instead of sampling, and pass directories via tool parameters, resource URIs, or server configuration instead of roots. The SDK-wide list is in **[Deprecated features](../deprecated.md)**.
 
 ## Sampling: borrow the client's model
```

Apply with `git apply` from the target repository root. This patch was drafted automatically and has not been opened anywhere. Read it before you send it.
