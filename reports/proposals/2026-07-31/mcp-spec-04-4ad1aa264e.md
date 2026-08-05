# Proposal 4ad1aa264e

- Target: `mcp-spec`
- File: `docs/community/interest-groups/auth.mdx`

## Why

The documented URL redirects. Pointing it at the resolved location removes a hop and survives the redirect being retired.

## How this was verified

Requested https://www.rfc-editor.org/rfc/rfc7591, followed redirects to https://www.rfc-editor.org/info/rfc7591/ (HTTP 200). Classified as a genuine move: same host, resource preserved, canonical form of the same page.

## Patch

```diff
--- a/docs/community/interest-groups/auth.mdx
+++ b/docs/community/interest-groups/auth.mdx
@@ -15,7 +15,7 @@
 
 ### In Scope
 
-- **Deployment experience reports**: how implementers have integrated the current authorization spec (OAuth 2.1, [RFC 9728](https://www.rfc-editor.org/rfc/rfc9728) Protected Resource Metadata, [RFC 7591](https://www.rfc-editor.org/rfc/rfc7591) Dynamic Client Registration, Client ID Metadata Documents) with real authorization servers, and where it falls short
+- **Deployment experience reports**: how implementers have integrated the current authorization spec (OAuth 2.1, [RFC 9728](https://www.rfc-editor.org/rfc/rfc9728) Protected Resource Metadata, [RFC 7591](https://www.rfc-editor.org/info/rfc7591/) Dynamic Client Registration, Client ID Metadata Documents) with real authorization servers, and where it falls short
 - **Enterprise identity integration**: requirements and friction points when connecting MCP servers to enterprise IdPs (Okta, Entra ID, Ping, Keycloak, etc.), including SSO, tenant isolation, and admin consent flows
 - **Delegated and agentic access**: use cases for on-behalf-of token exchange, downstream resource access, audience restriction, and consent when an MCP client acts through chains of agents or tools
 - **Scope and permission granularity**: whether and how MCP servers should advertise fine-grained scopes (per-tool, per-resource) and how clients should request and present them
```

Apply with `git apply` from the target repository root. This patch was drafted automatically and has not been opened anywhere. Read it before you send it.
