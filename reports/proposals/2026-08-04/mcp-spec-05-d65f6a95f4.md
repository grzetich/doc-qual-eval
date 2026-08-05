# Proposal d65f6a95f4

- Target: `mcp-spec`
- File: `docs/community/interest-groups/auth.mdx`

## Why

The documented URL redirects. Pointing it at the resolved location removes a hop and survives the redirect being retired.

## How this was verified

Requested https://www.rfc-editor.org/rfc/rfc9396, followed redirects to https://www.rfc-editor.org/info/rfc9396/ (HTTP 200). Classified as a genuine move: same host, resource preserved, canonical form of the same page.

## Patch

```diff
--- a/docs/community/interest-groups/auth.mdx
+++ b/docs/community/interest-groups/auth.mdx
@@ -77,7 +77,7 @@
 | Mix-up Protection          | `#auth-wg-mixup-protection`    | Mitigating OAuth authorization-server mix-up and token-audience confusion attacks                                                                                                   | Completed | —       |
 | Profiles                   | `#auth-wg-profiles`            | Extension specifications for additional grant types and token-binding mechanisms (Client Credentials, Enterprise-Managed Authorization, DPoP, Workload Identity Federation)         | Completed | —       |
 | Tool Scopes                | `#auth-wg-tool-scopes`         | Per-tool OAuth scope advertisement, step-up authorization / scope challenge, and client-side scope accumulation — mechanics within the OAuth scope-string model                     | Active    | Pending |
-| Fine-Grained Authorization | `#auth-wg-fine-grained-authz`  | Authorization granularity beyond scope strings — Rich Authorization Requests ([RFC 9396](https://www.rfc-editor.org/rfc/rfc9396)), remediation hints, and multi-credential handling | Active    | Pending |
+| Fine-Grained Authorization | `#auth-wg-fine-grained-authz`  | Authorization granularity beyond scope strings — Rich Authorization Requests ([RFC 9396](https://www.rfc-editor.org/info/rfc9396/)), remediation hints, and multi-credential handling | Active    | Pending |
 | Improve DevX               | `#auth-wg-improve-devx`        | Best-practices guidance and tutorials for building secure MCP clients and servers, beyond the normative spec                                                                        | Completed | —       |
 
 ## Changelog
```

Apply with `git apply` from the target repository root. This patch was drafted automatically and has not been opened anywhere. Read it before you send it.
