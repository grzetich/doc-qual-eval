# docs-quality-monitor

Finds problems in open source API documentation, drafts the fix, and puts it in
a queue for a human to send.

It never opens a pull request. Not because opening one is technically hard, but
because unreviewed machine-generated pull requests are currently making
maintainers hostile to this entire category of tool. The output is a set of
patches with the reasoning attached, and a person decides which ones are worth
a maintainer's time.

The AI-readiness scoring uses [artie-cli](https://github.com/grzetich/artie-cli),
whose checks come from *[Tokens Not Jokin'](https://leanpub.com/tokensnotjokin)*,
a controlled study of over 21,000 integration tests measuring how documentation
format affects AI-generated code quality.

## How it works

```
clone → gate → classify → draft → queue → (human) → PR
```

Two kinds of target. **Contribution** targets are open source projects where a
pull request from a stranger is a normal contribution. They get cloned, gated,
and patched against real files at real line numbers. **Benchmark** targets are
commercial APIs, scored only so the numbers have a reference point. Nothing is
ever proposed against them, because nobody asked us to review their
documentation.

Current targets: the MCP specification, the MCP Python and TypeScript SDKs, and
Stripe as the benchmark.

## The tier system

Every finding lands in one of three tiers, and the boundaries are the point of
the project.

**Draftable.** The fix is derived from evidence already in hand, so a reviewer
can verify it in seconds. A redirect target came from following the redirect. A
style replacement came from the linter's own rule definition. Nothing here asks
a model what the fix should be.

**Review only.** A real finding where the correct value is not derivable from
the document. A dead link is genuinely dead and the right replacement is
unknowable from here, so the location is reported and a maintainer decides.

**Refused.** A real gap that would require knowing how the API actually
behaves. Missing examples, undocumented error conditions, auth behaviour. The
pipeline states the refusal and the reason rather than filling the gap. An
invented example is worse than a missing one, because a wrong example gets
copied into someone's code.

## Three things this got wrong first, and what changed

These are in the README because the corrections are the substance of the
project, and because a tool like this is only worth trusting if its failures
are visible.

**It proposed replacing working links with login pages.** The first run drafted
three patches pointing GitHub issue links at
`github.com/login?return_to=...`. The server really did return 200 there, so
"follow the redirect and record the destination" reported it as verified. It
was verified, and it was wrong. Redirects now go through a classifier that
separates a move from a gate: destinations carrying a return parameter, auth
and consent paths, cross-host hops, and redirects to a section index are all
withheld from drafting. See `monitor/redirects.py`.

**It generated 112 patches for one repository.** Vale was running Google's
styleguide against a project that never adopted it, and 106 of the patches were
capitalization preferences. A maintainer receiving that would close it unread,
correctly. The prose gate now runs only when the target ships its own Vale
configuration. If the rules are the project's own, a patch bringing prose back
in line is doing work they signed up for. If not, there is no agreed standard
and this pipeline has no standing to enforce one, so the gate reports skipped.

**It buried two real findings under 354 opinions.** Even demoted to
review-only, an outside styleguide at volume drowns the signal. Detection
without a shared standard is not neutral observation.

## Why the proposal queue is capped

Twenty patches per target per run. A queue nobody gets through is the same as
no queue, and the number held back is stated rather than quietly dropped.

## The number that matters

`reports/ledger.csv` tracks every proposal as proposed, opened, or merged. The
status column is filled in by hand as patches progress.

Anything can generate patches. The merge ratio is the only honest measure of
whether they were worth a maintainer's attention, and it is the number to
quote when describing this tool.

## Running it

```bash
pip install -r requirements.txt
pip install "git+https://github.com/grzetich/artie-cli.git@main"
# optional, enables the prose gate on projects with their own config
# https://vale.sh/docs/install

python run_monitor.py                        # everything
python run_monitor.py --only mcp-python-sdk  # one target
python run_monitor.py --generation           # adds artie's paid check
```

Requires `git`. The generation check calls the Anthropic API and needs
`ANTHROPIC_API_KEY`; every other gate is free.

To be precise about what that key buys: the generation check asks a model to
write code from the documentation, then scores what it wrote. It never executes
that code and never calls the API being documented. Scoring Stripe's
specification requires no Stripe credential and sends Stripe no request.

## Output

- `reports/latest.md` is the run at a glance
- `reports/proposals/<date>/` is one file per patch, with rationale, the
  verification behind it, and a diff you can `git apply`
- `reports/ledger.csv` is the proposed, opened, merged trail
- `reports/raw/<date>.json` is everything

## What is deliberately not built

**Automatic pull requests.** Covered above.

**Code sample execution.** The gap here is not language runtimes. Running a
sample means holding a credential for someone else's API, a sandbox account per
vendor, and side effects, since a sample that posts a charge either fails or
creates something. The disqualifying problem is interpretation: a failed
execution has at least four causes that look identical from outside. The
documentation is wrong, the credential expired, the API changed, or the snippet
was a fragment never meant to run standalone. A gate that cannot separate those
produces findings nobody can act on.

This is also why artie scores generated code statically rather than running it.
That is a tradeoff, not a shortcut. Static scoring cannot tell you the code
works. It can tell you whether the docs gave the model enough to write code that
plausibly would.

**Proposals against commercial targets.** Stripe did not ask for a review.

## Adding a target

Add it to `targets.yml` and verify the URL returns 200 on the day you add it,
recording that date. Contribution targets need a repository where an outside
pull request is welcome. If you would not send a patch there yourself, it does
not belong in this file.
