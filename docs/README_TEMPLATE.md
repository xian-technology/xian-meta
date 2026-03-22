# Root README Template

Use this as the baseline for the main repo root `README.md` files.

~~~md
# <repo-name>

<one paragraph summary of what the repo is for>

## Scope

- what the repo owns
- what the repo intentionally does not own

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

After these shared sections, add repo-specific sections as needed. Keep the
top-level structure stable even when the repo needs extra detail.

For the docs-site repo, use `.meta/ARCHITECTURE.md` and `.meta/BACKLOG.md`.
If the root README participates in the published site build, reference those as
plain paths instead of markdown links so hidden files do not trigger dead-link
checks.
