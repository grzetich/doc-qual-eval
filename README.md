# docs-quality-monitor

Deterministic checks that tie an assertion in the documentation to an
assertion in the source.

Every claim this tool makes is settled against something outside the document:
a published JSON Schema, the symbol table of the SDK the docs describe, an HTTP
response. Nothing here asks a model whether the documentation looks good.

That constraint is the whole design. It decides which problems get reported,
which get a drafted patch, and which the tool refuses to touch.

The scoring checks come from
*[Tokens Not Jokin'](https://leanpub.com/tokensnotjokin)*, a controlled study of
over 21,000 integration tests measuring how documentation format affects
AI-generated code quality.

## Why deterministic

A pipeline that generates documentation faster than a human can review it has
moved the bottleneck rather than removed it. Producing words is cheap now.
Being accountable for whether the words are true has not moved at all.

So the useful question is not how much a tool can write. It is how much a tool
can settle without a human, and how honestly it reports the rest.

Three kinds of check, in descending order of how much they settle.

**Checked against a specification.** A generated tool declaration either
satisfies `$defs/Tool` in the published MCP schema or it does not. There is no
judgement in that answer.

**Checked against source.** An import either resolves against a symbol table
built by walking the cloned SDK or it does not. This catches the specific
failure of a model writing from training data instead of from the documentation
it was given.

**Checked against the network.** A URL either resolves, redirects, or is gone.
Weaker than the first two, because a 403 from a bot rule is indistinguishable
from a real failure, so those are reported as inconclusive rather than counted
against the docs.

Anything that cannot be settled by one of these is reported to a human with the
reason stated. It never becomes a patch.

## How it works

```
clone → check → classify → draft → queue → (human) → PR
```

Nothing is ever opened automatically. The output is patches with the evidence
attached, and a person decides which are worth a maintainer's time.

Three kinds of target. **Pages** are the documentation URLs a developer would
paste into a chat box, fetched the way an agent would fetch them.
**Contribution** targets are open source repositories where a pull request from
a stranger is normal, cloned and patched against real files at real line
numbers. **Benchmark** targets are commercial specifications, scored only so the
numbers have a reference point, never proposed against.

## The tier system

Every finding lands in one of three tiers. The boundaries are the point.

**Draftable.** The fix is a copy of something already confirmed, so a reviewer
verifies it in seconds. A redirect target came from following the redirect. A
style replacement came from the linter's own rule definition.

**Review only.** A real finding where the correct value is not derivable from
the document. A dead link is dead and the right replacement is unknowable from
here.

**Refused.** A real gap that would require knowing how the API behaves. Missing
examples, undocumented error conditions, auth behaviour. The tool states the
refusal and the reason rather than filling the gap. An invented example is
worse than a missing one, because a wrong example gets copied.

## The generation gate

The other checks ask whether the documentation is intact. This one asks whether
it works.

A model is given only the target repository's documentation and asked to write
a server implementing a named capability. What comes back is parsed, never
executed, and scored on things that can be settled:

- it parses
- it imports from the SDK
- **every imported symbol exists**, checked against the SDK's own source
- it declares the requested capability through the documented decorators
- **each declaration validates against the published schema**
- declarations carry descriptions

The two in bold are why this gate exists when code sample execution was
refused. Executing a sample against a commercial API gives an ambiguous failure
with at least four indistinguishable causes. MCP publishes a machine-checkable
schema and ships its own source, so a generated server can be judged against
both without running it.

A low score is a review-only finding. It says the documentation left something
out and names the capability, which points at a section. It never becomes a
patch, because writing the missing documentation requires knowing what the SDK
does.

### What this surfaced immediately

The SDK's current API is `MCPServer`. `FastMCP`, which earlier versions
documented and which a lot of published example code still uses, is gone from
`main`. A model leaning on training data instead of the provided documentation
writes `from mcp.server.fastmcp import FastMCP`, and the symbol check catches
it every time.

Whether the model used the documentation or its memory is the question the
research was built to answer. Here it falls out of the check for free.

## The page gate

Specifications are not what gets pasted into a chat box.

Locating Anthropic's OpenAPI document meant reading `.stats.yml` for a storage
bucket URL with a hash filename. Box's specification is roughly 441,000
estimated tokens. A developer working on cash balances copies the cash balance
page URL, because copying a URL is the muscle memory move.

So this gate fetches the page the way an agent would, with no browser and no
JavaScript, and reports what actually arrives. It needs no API key.

Fetching Stripe's cash balance reference returns about 100 words: a short
description, two links, one event name. No parameters, no authentication, no
code. The real content is one hop further on. A model handed that page knows
two endpoints exist and writes everything else from training data.

The checks: the page arrives as raw HTML, falls below a word floor, contains no
code block, reads as an index rather than a document, never mentions
authentication, or names endpoints without documenting parameters.

All review only. The fix is to write documentation.

**Scope limit worth stating.** This models one consumption path. Agents built on
headless browsers see the rendered page; agents doing a plain fetch see what
this sees. A finding here means the page is thin for plain-fetch clients, which
is narrower than saying the page is thin.

## Four things this got wrong first

These are in the README because a tool that claims to verify things is only
worth trusting if its own failures are visible.

**It scored non-evaluable checks as zero.** The scorer was written against a
guessed output schema. Checks that could not run return a null score, and
averaging those in as zero turns a missing measurement into a bad grade. Fixed
by reading the real output before writing the parser.

**It proposed replacing working links with login pages.** The first run drafted
three patches pointing GitHub issue links at `github.com/login?return_to=...`.
The server returned 200 there, so following the redirect and recording the
destination marked it verified. It was verified, and it was wrong. Redirects now
go through a classifier that separates a move from a gate. See
`monitor/redirects.py`.

**It generated 112 patches for one repository.** Vale was running Google's
styleguide against a project that never adopted it, and 106 were capitalization
preferences. The prose gate now runs only when the target ships its own Vale
configuration. If the rules are the project's own, a patch enforcing them is
doing work they signed up for. If not, this tool has no standing.

**It drafted twelve correct, worthless patches.** All in a `CHANGELOG.md` that a
generator produces, so every one would have been overwritten. Generated and
historical files are now excluded by pattern and by header scan.

Three of those are the same mistake: the pipeline turning its own limitation
into a finding about someone's documentation. That is why `fail` and `error` are
separate statuses everywhere in this codebase.

## Noise control

**Generated and historical files are skipped**, by pattern, by a per-target
`generated` list, and by scanning headers for generator markers. Changelogs are
excluded regardless of origin.

**Repeated findings collapse into a pattern.** Findings matching once numbers
are normalised away are grouped, and a group above the threshold drops to
review. Repetition changes the meaning: one instance is a mistake, twelve are a
convention, a generator, or platform behaviour.

**The proposal queue is capped** at twenty per target per run, with the number
held back stated rather than dropped. A queue nobody gets through is the same as
no queue.

## The number that matters

`reports/ledger.csv` tracks every proposal as proposed, opened, or merged, with
the status filled in by hand as patches progress.

Anything can generate patches. The merge ratio is the only honest measure of
whether they were worth a maintainer's attention.

## Using it on your own project

**Link and page checking: configuration only.** Add a target with a `repo`, a
`ref`, and `prose` globs.

The prose gate behaves better on your own repository than on anyone else's. It
only runs when the target ships its own Vale configuration, so this pipeline
never imposes an outside styleguide on a project that did not choose one. On
your own repository you write that configuration, which inverts the constraint.

**Generation on another protocol: configuration only.** Everything
protocol-specific lives in a profile in `targets.yml`:

```yaml
profiles:
  mcp-python:
    language: python
    import_namespace: mcp        # imports checked against the SDK symbol table
    declarations:
      - decorator: tool          # the decorator to look for
        capability: tools        # what to call it
        shape: schema_object     # how to build a declaration from the function
        schema_def: Tool         # the $defs entry to validate against
    tasks:
      tools: expose a tool that takes two named arguments and returns a value
```

Three shapes are available. `schema_object` builds an input schema from the
function signature, `uri_object` takes a URI from the decorator argument, and
`argument_list` produces a list of named arguments. Set `schema_def` wherever
your project publishes a schema, since that check settles the most. Without it,
declarations are still extracted and the summary says they went unvalidated.

Then point a target at the profile:

```yaml
    generation:
      profile: mcp-python
      schema: schema/2026-07-28.json
      docs: [README.md, "docs/**/*.md"]
```

**A different language: this needs code.** Extraction reads Python syntax trees.
A TypeScript SDK needs its own extractor, and the gate reports skipped rather
than guessing, because mis-parsing a language confidently is worse than
declining it.

## Running it

```bash
pip install -r requirements.txt
pip install "git+https://github.com/grzetich/artie-cli.git@main"
# optional, enables the prose gate on projects with their own config
# https://vale.sh/docs/install

python run_monitor.py                        # everything
python run_monitor.py --only mcp-python-sdk  # one target
python run_monitor.py --generation           # adds the generation gates
```

Requires `git`. The generation gates call the Anthropic API and need
`ANTHROPIC_API_KEY`; every other check is free. Set `MCPGEN_MODEL` to choose the
model, and verify the identifier against current documentation before a run that
matters, since a stale one fails with an unhelpful 404.

To be precise about what that key buys: the generation gate asks a model to
write code from the documentation, then scores what it wrote. It never executes
that code and never calls the API being documented. Scoring Stripe's
specification requires no Stripe credential and sends Stripe no request.

## Output

- `reports/latest.md` is the run at a glance
- `reports/proposals/<date>/` is one file per patch, with the rationale, the
  verification behind it, and a diff you can `git apply`
- `reports/ledger.csv` is the proposed, opened, merged trail
- `reports/raw/<date>.json` is everything

## What is deliberately not built

**Automatic pull requests.** Unreviewed machine-written pull requests are why
maintainers have started distrusting this category of tool.

**Code sample execution.** The gap is not language runtimes. Running a sample
means holding a credential for someone else's API, a sandbox account per vendor,
and side effects, since a sample that posts a charge either fails or creates
something. The disqualifying problem is interpretation: a failed execution has
at least four causes that look identical from outside. The documentation is
wrong, the credential expired, the API changed, or the snippet was a fragment
never meant to run standalone.

This is also why generated code is scored statically rather than run. Static
scoring cannot tell you the code works. It can tell you whether the docs gave
the model enough to write code that plausibly would.

**Proposals against commercial targets.** Stripe did not ask for a review.

## Adding a target

Add it to `targets.yml` and verify the URL returns 200 on the day you add it,
recording that date. Contribution targets need a repository where an outside
pull request is welcome. If you would not send a patch there yourself, it does
not belong in this file.
