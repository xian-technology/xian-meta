# PyPI Release Rollout

This note is the canonical maintainer checklist for turning the existing GitHub
release workflows into real PyPI publication across the Xian Python packages.

## Current State

The GitHub side is already mostly set up:

- `xian-abci`, `xian-cli`, `xian-py`, and `xian-tech-linter` already publish through
  GitHub Actions release workflows using PyPI Trusted Publishing
  (`pypa/gh-action-pypi-publish` with `id-token: write`).
- `xian-contracting` already has a multi-package release workflow for:
  - `xian-tech-accounts`
  - `xian-tech-contracting`
  - `xian-tech-runtime-types`
  - `xian-tech-native-tracer`
  - `xian-tech-zk`

That means the missing work is primarily on the PyPI side:

- create the PyPI projects if they do not exist yet
- register the matching GitHub workflows as trusted publishers
- then release by tag

## Do Not Share Tokens In Chat

Do not pass a PyPI API token through chat to an agent.

Use PyPI Trusted Publishing instead. It is cleaner, safer, and already matches
the workflows in the repos. The only secretless requirement is that the PyPI
project must trust the exact GitHub repository/workflow/environment that will
publish it.

Official references:

- <https://docs.pypi.org/trusted-publishers/adding-a-publisher/>
- <https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/>
- <https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/>

## Package Inventory

### Single-package repos

| PyPI project | GitHub repo | Workflow | Environment | Tag shape |
| --- | --- | --- | --- | --- |
| `xian-tech-abci` | `xian-technology/xian-abci` | `.github/workflows/release.yml` | `pypi` | `v*` |
| `xian-tech-cli` | `xian-technology/xian-cli` | `.github/workflows/release.yml` | `pypi` | `v*` |
| `xian-tech-py` | `xian-technology/xian-py` | `.github/workflows/release.yml` | `pypi` | `v*` |
| `xian-tech-linter` | `xian-technology/xian-linter` | `.github/workflows/release.yml` | `pypi` | `v*` |

### Multi-package repo

`xian-contracting` publishes multiple projects from one workflow:

| PyPI project | GitHub repo | Workflow | Environment | Tag shape |
| --- | --- | --- | --- | --- |
| `xian-tech-accounts` | `xian-technology/xian-contracting` | `.github/workflows/release.yml` | `pypi-xian-accounts` | `accounts-v*` |
| `xian-tech-contracting` | `xian-technology/xian-contracting` | `.github/workflows/release.yml` | `pypi-xian-contracting` | `contracting-v*` |
| `xian-tech-runtime-types` | `xian-technology/xian-contracting` | `.github/workflows/release.yml` | `pypi-xian-runtime-types` | `runtime-types-v*` |
| `xian-tech-native-tracer` | `xian-technology/xian-contracting` | `.github/workflows/release.yml` | `pypi-xian-native-tracer` | `native-tracer-v*` |
| `xian-tech-zk` | `xian-technology/xian-contracting` | `.github/workflows/release.yml` | `pypi-xian-zk` | `zk-v*` |

## Recommended Release Order

Release bottom-up so dependency constraints stay satisfiable.

1. `xian-tech-runtime-types`
2. `xian-tech-accounts`
3. `xian-tech-native-tracer`
4. `xian-tech-zk`
5. `xian-tech-contracting`
6. `xian-tech-py`
7. `xian-tech-abci`
8. `xian-tech-cli`
9. `xian-tech-linter`

Notes:

- `xian-tech-py` depends on `xian-tech-accounts` and `xian-tech-runtime-types`.
- `xian-tech-abci` depends on `xian-tech-contracting`, `xian-tech-accounts`, and
  `xian-tech-runtime-types`.
- `xian-tech-cli` depends on `xian-tech-abci`.
- `xian-tech-linter` depends on `xian-tech-contracting`.

## Current Version Baseline

As of March 29, 2026, the local package versions are:

| Project | Local version |
| --- | --- |
| `xian-tech-runtime-types` | `0.1.0` |
| `xian-tech-accounts` | `0.1.0` |
| `xian-tech-native-tracer` | `0.1.1` |
| `xian-tech-zk` | `0.1.1` |
| `xian-tech-contracting` | `1.0.1` |
| `xian-tech-py` | `0.4.8` |
| `xian-tech-abci` | `0.8.4` |
| `xian-tech-cli` | `0.1.0` |
| `xian-tech-linter` | `0.3.1` |

The legacy project names currently return `404` from the public PyPI JSON API,
so there is no evidence of an already-published version collision on:

- `xian-tech-py`
- `xian-tech-contracting`
- `xian-tech-linter`
- `xian-tech-abci`
- `xian-tech-native-tracer`
- `xian-tech-zk`

That means the first release wave can use the current local versions without a
preemptive version bump.

## Current Publisher State

Already published:

- `xian-tech-runtime-types`
- `xian-tech-accounts`

Already staged in PyPI as pending trusted publishers:

- `xian-tech-cli`
- `xian-tech-py`
- `xian-tech-abci`

Still unresolved on the PyPI side:

- no additional project registrations are needed before the contracting release

Because PyPI only allows three pending publishers at once, keep working in
batches that free those slots before creating the next set.

## Exact First Release Wave

### Batch 1

Completed:

1. `xian-tech-runtime-types`
   - repo: `xian-contracting`
   - tag: `runtime-types-v0.1.0`
   - workflow environment: `pypi-xian-runtime-types`
2. `xian-tech-accounts`
   - repo: `xian-contracting`
   - tag: `accounts-v0.1.0`
   - workflow environment: `pypi-xian-accounts`

### Batch 2

The next two are ready once the repo-side rename is in place:

1. `xian-tech-native-tracer`
   - repo: `xian-contracting`
   - tag: `native-tracer-v0.1.1`
   - workflow environment: `pypi-xian-native-tracer`
2. `xian-tech-zk`
   - repo: `xian-contracting`
   - tag: `zk-v0.1.1`
   - workflow environment: `pypi-xian-zk`

The `0.1.0` native release attempts failed because PyPI rejected the raw
single-runner Linux wheels (`linux_x86_64`). The workflow now publishes source
distributions for the Rust-backed packages until a proper manylinux/macOS wheel
matrix is added.

Do not publish `xian-tech-cli` yet. Its publisher is registered, but it depends
on `xian-abci`, which should land later in the chain.

### Batch 3

After `xian-tech-native-tracer` and `xian-tech-zk` are live, resolve the core
runtime package name on PyPI and then publish:

1. `xian-tech-contracting`
   - repo: `xian-contracting`
   - tag: `contracting-v1.0.1`
   - workflow environment: `pypi-xian-contracting`

### Batch 4

After the contracting package is published, create the next publisher batch:

- `xian-tech-py`
- `xian-tech-abci`
- `xian-tech-linter`

Then publish:

1. `xian-tech-py`
   - repo: `xian-py`
   - tag: `v0.4.8`
   - workflow environment: `pypi`
2. `xian-tech-abci`
   - repo: `xian-abci`
   - tag: `v0.8.4`
   - workflow environment: `pypi`
3. `xian-tech-linter`
   - repo: `xian-linter`
   - tag: `v0.3.1`
   - workflow environment: `pypi`

### Batch 5

Once `xian-tech-abci` is live, publish the remaining already-registered CLI package:

1. `xian-tech-cli`
   - repo: `xian-cli`
   - tag: `v0.1.0`
   - workflow environment: `pypi`

## Release Commands

From a clean checkout, the first tag wave is:

```bash
cd /path/to/xian-contracting
git tag runtime-types-v0.1.0
git push origin runtime-types-v0.1.0

git tag accounts-v0.1.0
git push origin accounts-v0.1.0
```

Then wait for both release workflows to publish successfully before adding the
next trusted-publisher batch in PyPI.

## One-Time PyPI Setup

Do this once per package.

1. Log into the target PyPI account in the browser.
2. If the project already exists:
   - add a trusted publisher for the matching repo/workflow/environment
3. If the project does not exist yet:
   - create a pending publisher for the matching repo/workflow/environment
   - let the first tagged GitHub release create the project
4. Repeat for every package in the tables above.

The environment name matters. For `xian-contracting`, each package has its own
PyPI environment name in the workflow, and the PyPI trusted publisher entry
must match the package-specific environment.

## Release Execution

For each package release:

1. bump the package version in its `pyproject.toml` or dynamic version source
2. commit the version bump
3. create and push the matching release tag
4. let the release workflow build, publish to PyPI, and create the GitHub release
5. verify the project page on PyPI and the GitHub release artifacts

## Build Readiness

Local build checks already confirm that the current package layouts are
publishable:

- `xian-abci`
- `xian-cli`
- `xian-py`
- `xian-tech-linter`
- `xian-contracting`
- `xian-accounts`
- `xian-runtime-types`
- `xian-tech-native-tracer`
- `xian-tech-zk`

## Wheel Coverage

Pure Python packages already build normal `py3-none-any` wheels cleanly.

The Rust-backed packages:

- `xian-tech-native-tracer`
- `xian-tech-zk`

currently publish source distributions first. The earlier `0.1.0` attempts
showed that PyPI rejects the raw `linux_x86_64` wheels produced by the
single-runner workflow. Proper manylinux/macOS wheel coverage remains a
follow-up improvement.

Highest-value next step:

- extend `xian-contracting/.github/workflows/release.yml` to publish a wheel
  matrix for the native packages, starting with Linux wheels and then macOS
  coverage

## Practical Recommendation

Do not block PyPI rollout on perfect wheel coverage.

The right sequence is:

1. finish Trusted Publishing registration in PyPI
2. publish the current packages
3. improve native wheel coverage afterward

That gets the packages live without forcing local token handling or delaying on
CI matrix work.
