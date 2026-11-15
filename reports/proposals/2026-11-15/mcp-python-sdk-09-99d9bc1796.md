# Proposal 99d9bc1796

- Target: `mcp-python-sdk`
- File: `docs/get-started/installation.md`

## Why

The documented URL redirects. Pointing it at the resolved location removes a hop and survives the redirect being retired.

## How this was verified

Requested https://rich.readthedocs.io/, followed redirects to https://rich.readthedocs.io/en/stable/ (HTTP 200). Classified as a genuine move: same host, resource preserved, canonical form of the same page.

## Patch

```diff
--- a/docs/get-started/installation.md
+++ b/docs/get-started/installation.md
@@ -39,4 +39,4 @@
 ## Optional extras
 
 * `mcp[cli]` adds [`typer`](https://typer.tiangolo.com/) and [`python-dotenv`](https://pypi.org/project/python-dotenv/) for the `mcp` command-line tool (`mcp dev`, `mcp run`, `mcp install`). You'll want this during development; you may not need it in a deployed server.
-* `mcp[rich]` adds [`rich`](https://rich.readthedocs.io/) for nicer server logs.
+* `mcp[rich]` adds [`rich`](https://rich.readthedocs.io/en/stable/) for nicer server logs.
```

Apply with `git apply` from the target repository root. This patch was drafted automatically and has not been opened anywhere. Read it before you send it.
