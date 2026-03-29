# PyPI Release Rollout

This note is the canonical maintainer checklist for turning the existing GitHub
release workflows into real PyPI publication across the Xian Python packages.

## Current State

The GitHub side is already mostly set up:

- `xian-abci`, `xian-cli`, `xian-py`, and `xian-linter` already publish through
  GitHub Actions release workflows using PyPI Trusted Publishing
  (`pypa/gh-action-pypi-publish` with `id-token: write`).
- `xian-contracting` already has a multi-package release workflow for:
  - `xian-tech-accounts`
  - `xian-contracting`
  - `xian-tech-runtime-types`
  - `xian-native-tracer`
  - `xian-zk`

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
| `xian-abci` | `xian-technology/xian-abci` | `.github/workflows/release.yml` | `pypi` | `v*` |
| `xian-tech-cli` | `xian-technology/xian-cli` | `.github/workflows/release.yml` | `pypi` | `v*` |
| `xian-py` | `xian-technology/xian-py` | `.github/workflows/release.yml` | `pypi` | `v*` |
| `xian-linter` | `xian-technology/xian-linter` | `.github/workflows/release.yml` | `pypi` | `v*` |

### Multi-package repo

`xian-contracting` publishes multiple projects from one workflow:

| PyPI project | GitHub repo | Workflow | Environment | Tag shape |
| --- | --- | --- | --- | --- |
| `xian-tech-accounts` | `xian-technology/xian-contracting` | `.github/workflows/release.yml` | `pypi-xian-accounts` | `accounts-v*` |
| `xian-contracting` | `xian-technology/xian-contracting` | `.github/workflows/release.yml` | `pypi-xian-contracting` | `contracting-v*` |
| `xian-tech-runtime-types` | `xian-technology/xian-contracting` | `.github/workflows/release.yml` | `pypi-xian-runtime-types` | `runtime-types-v*` |
| `xian-native-tracer` | `xian-technology/xian-contracting` | `.github/workflows/release.yml` | `pypi-xian-native-tracer` | `native-tracer-v*` |
| `xian-zk` | `xian-technology/xian-contracting` | `.github/workflows/release.yml` | `pypi-xian-zk` | `zk-v*` |

## Recommended Release Order

Release bottom-up so dependency constraints stay satisfiable.

1. `xian-tech-runtime-types`
2. `xian-tech-accounts`
3. `xian-native-tracer`
4. `xian-zk`
5. `xian-contracting`
6. `xian-py`
7. `xian-abci`
8. `xian-tech-cli`
9. `xian-linter`

Notes:

- `xian-py` depends on `xian-tech-accounts` and `xian-tech-runtime-types`.
- `xian-abci` depends on `xian-contracting`, `xian-tech-accounts`, and
  `xian-tech-runtime-types`.
- `xian-tech-cli` depends on `xian-abci`.
- `xian-linter` depends on `xian-contracting`.

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
- `xian-linter`
- `xian-contracting`
- `xian-accounts`
- `xian-runtime-types`
- `xian-native-tracer`
- `xian-zk`

## Wheel Coverage

Pure Python packages already build normal `py3-none-any` wheels cleanly.

The Rust-backed packages:

- `xian-native-tracer`
- `xian-zk`

already build valid native wheels through `maturin`, but the current release
workflow still builds them on a single GitHub runner platform per release. That
is enough to start publishing, but broad platform wheel coverage should still be
treated as a follow-up improvement.

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
