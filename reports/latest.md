# Latest run

Run at 2026-08-01T12:06:20+00:00 UTC.

16 patches drafted, 12 findings left for review, 0 findings deliberately not patched.

## Targets

| Target | Type | Revision | Gates |
| --- | --- | --- | --- |
| mcp-spec | contribution | 7376311 | checkout:ok, links:ok, prose:skipped, jsonschema:ok |
| mcp-python-sdk | contribution | a4f4ccd | checkout:ok, links:ok, prose:skipped |
| mcp-typescript-sdk | contribution | cc4b416 | checkout:ok, links:ok, prose:skipped |
| stripe | benchmark |  | fetch:ok, artie:error |

## Drafted patches

In `reports/proposals/2026-08-01/`. Nothing has been opened.

| ID | Target | File | Verified by |
| --- | --- | --- | --- |
| 359d824eed | mcp-spec | README.md | Requested https://modelcontextprotocol.io, followed redirects to https://modelco |
| 87384173a1 | mcp-spec | docs/community/contributing.mdx | Requested https://nodejs.org/, followed redirects to https://nodejs.org/en (HTTP |
| f03e5080f2 | mcp-spec | docs/community/interest-groups/auth.mdx | Requested https://www.rfc-editor.org/rfc/rfc9728, followed redirects to https:// |
| 4ad1aa264e | mcp-spec | docs/community/interest-groups/auth.mdx | Requested https://www.rfc-editor.org/rfc/rfc7591, followed redirects to https:// |
| d65f6a95f4 | mcp-spec | docs/community/interest-groups/auth.mdx | Requested https://www.rfc-editor.org/rfc/rfc9396, followed redirects to https:// |
| 57cdd41177 | mcp-python-sdk | README.md | Requested https://modelcontextprotocol.io, followed redirects to https://modelco |
| ce0c0c90b7 | mcp-python-sdk | README.md | Requested https://modelcontextprotocol.io/specification/latest, followed redirec |
| d676ebedb3 | mcp-python-sdk | docs/get-started/installation.md | Requested https://anyio.readthedocs.io/, followed redirects to https://anyio.rea |
| 41c25f8393 | mcp-python-sdk | docs/get-started/installation.md | Requested https://opentelemetry-python.readthedocs.io/, followed redirects to ht |
| 99d9bc1796 | mcp-python-sdk | docs/get-started/installation.md | Requested https://rich.readthedocs.io/, followed redirects to https://rich.readt |
| b168171a30 | mcp-python-sdk | docs/get-started/installation.md | Requested https://typing-extensions.readthedocs.io/, followed redirects to https |
| f25a934431 | mcp-python-sdk | docs/servers/uri-templates.md | Requested https://modelcontextprotocol.io/specification/latest/server/resources, |
| 9bc777a632 | mcp-python-sdk | examples/stories/apps/README.md | Requested https://github.com/modelcontextprotocol/modelcontextprotocol/issues/21 |
| 2c67387f85 | mcp-python-sdk | docs/handlers/sampling-and-roots.md | Requested https://github.com/modelcontextprotocol/modelcontextprotocol/issues/25 |
| b48e0cff86 | mcp-typescript-sdk | README.md | Requested https://modelcontextprotocol.io/docs, followed redirects to https://mo |
| 3b892475dd | mcp-typescript-sdk | README.md | Requested https://modelcontextprotocol.io/specification/latest, followed redirec |

## Findings needing a human

Real findings where the correct fix is not derivable from the document.

| Target | Kind | Location | Finding |
| --- | --- | --- | --- |
| mcp-spec | redirected_link | docs/community/communication.mdx:12 | https://discord.gg/6CSzBmMkjX redirects to https://discord.com/invite/6CSzBmMkjX (redirect |
| mcp-spec | redirected_link | docs/community/contributing.mdx:319 | https://mintlify.com/ redirects to https://www.mintlify.com/ (redirect crosses hosts, mint |
| mcp-spec | dead_link | docs/community/contributing.mdx:98 | https://github.com/YOUR-USERNAME/modelcontextprotocol.git returns 404 |
| mcp-spec | redirected_link | docs/community/interest-groups/enterprise-managed-authorization.mdx:60 | https://discord.gg/xw55W9Sw5s redirects to https://discord.com/invite/xw55W9Sw5s (redirect |
| mcp-spec | redirected_link | docs/community/interest-groups/financial-services.mdx:101 | https://discord.gg/NzkBHsrGf redirects to https://discord.com/invite/NzkBHsrGf (redirect c |
| mcp-spec | redirected_link | docs/community/governance.mdx:10 | https://www.lfprojects.org/policies/ redirects to https://lfprojects.org/policies/ (redire |
| mcp-python-sdk | redirected_link | README.md:21 | https://discord.gg/6CSzBmMkjX redirects to https://discord.com/invite/6CSzBmMkjX (redirect |
| mcp-python-sdk | redirected_link | docs/get-started/installation.md:30 | https://docs.pydantic.dev/ redirects to https://pydantic.dev/docs/ (redirect crosses hosts |
| mcp-python-sdk | redirected_link | docs/run/opentelemetry.md:59 | https://logfire.pydantic.dev/ redirects to https://logfire-us.pydantic.dev/ (redirect cros |
| mcp-python-sdk | dead_link | examples/stories/apps/README.md:35 | https://modelcontextprotocol.io/specification/draft/extensions/apps returns 404 |
| mcp-python-sdk | dead_link | examples/stories/caching/README.md:15 | https://modelcontextprotocol.io/specification/draft/basic/utilities/caching returns 404 |
| mcp-python-sdk | dead_link | examples/stories/events/README.md:16 | https://modelcontextprotocol.io/specification/draft/extensions/events returns 404 |

---

`error` on a gate means this pipeline failed, not that the documentation did. Those are never reported as findings.
