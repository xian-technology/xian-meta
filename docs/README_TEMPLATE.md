# Root README Template

Use this as the baseline for the main repo root `README.md` files.

The goal is a short human-first entrypoint, not a changelog or an internal
contract dump.

~~~md
# <repo-name>

<one paragraph summary of what the repo is for>

## Quick Start

~~~bash
<small first-use example>
~~~

## Principles

- what this repo is best used for
- what it intentionally does not own
- any constraints a professional user should know up front

## Key Directories

- `path/`: what lives here
- `path/`: what lives here

## Validation

~~~bash
<preferred local validation commands>
~~~

## Related Docs

- [AGENTS.md](../AGENTS.md) or [AGENTS.md](AGENTS.md)
- [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- [docs/BACKLOG.md](BACKLOG.md)
- other high-value notes when needed
~~~

`## Validation` and `## Related Docs` should stay stable. The other sections may
be renamed to fit the repo, for example `## Common Workflows` instead of
`## Quick Start` or `## Scope` instead of `## Principles`.

Write the README in current-state language. Avoid phrases like `now exposes`,
`old`, `new`, `still`, or `no longer` unless the historical comparison is
essential for correct usage.

For the docs-site repo, use `.meta/ARCHITECTURE.md` and `.meta/BACKLOG.md`.
If the root README participates in the published site build, reference those as
plain paths instead of markdown links so hidden files do not trigger dead-link
checks.
