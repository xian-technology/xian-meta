# Shared Package Extraction Plan

## Current Decision

For now, keep these shared packages inside the `xian-contracting` repo:

- `xian-runtime-types`
- `xian-accounts`
- `xian-contract-tools`

Do not extract them into standalone repos yet.

Reason:

- the package boundaries are now clean enough
- the current package set may still grow or adjust
- repo extraction would add admin overhead before the APIs and scope have fully
  settled

This is a deliberate deferral, not an implicit “never”.

## What Would Justify Extraction Later

Extract a shared package into its own repo only when all or most of these are
true:

1. the package has a narrow and stable purpose
2. multiple main repos depend on it directly
3. the package should have an independent release cadence
4. the package boundary is unlikely to churn significantly
5. repo-level ownership would be clearer than package-level ownership
6. the extra GitHub/PyPI/release overhead is worth the clarity gain

If those conditions are not met yet, keep the package where it is.

## Package-by-Package View

### `xian-runtime-types`

Strongest extraction candidate.

Why:

- it is narrow
- it is neutral
- it is already shared
- it represents foundational deterministic semantics

What could still justify waiting:

- additional deterministic types may still be added
- the boundary should settle before freezing repo ownership around it

### `xian-accounts`

Reasonable to keep inside `xian-contracting` for now.

Why:

- it is still new
- its future scope may expand with multi-account support
- it is not yet proven as a fully settled cross-stack foundation

Extraction becomes more attractive if it later becomes the clear shared home
for:

- Ed25519 account helpers
- secp256k1 / Ethereum-compatible account helpers
- account normalization
- signature-scheme-specific primitives

### `xian-contract-tools`

Keep it where it is unless it grows into a more substantial contract-tooling
surface.

Right now it is better understood as:

- a narrow companion package in the `xian-contracting` repo

than as:

- a standalone repo with its own longer-term identity

## Decision Process

When reconsidering extraction later, use this process:

1. confirm the package scope in writing
2. list all direct dependents across the main repos
3. identify whether the package needs independent versioning/releases
4. evaluate whether the package API has been stable for a meaningful period
5. decide whether extraction improves clarity more than it increases process
6. if still justified, create a concrete migration plan before moving code

Do not extract a package just because it is “shared”. Shared is not enough.

## Migration Conditions

Do not start extraction unless these conditions are met:

- the package tests are reliable and independent
- the package release workflow is already working cleanly
- consumers already import the package directly, not through legacy shims
- package-local docs clearly state what the package owns
- there is no unresolved scope ambiguity about what belongs in the package

## Migration Path When The Time Comes

### Step 1: Freeze Scope

- write the package scope explicitly
- reject unrelated additions during the extraction window

### Step 2: Create New Repo

- create a dedicated repo under `xian-technology`
- apply the `xian-meta` repo conventions immediately
- move only the package, tests, release workflow, and package-local docs

### Step 3: Preserve Packaging Identity

- keep the package name the same on PyPI
- keep import paths stable
- avoid unnecessary API changes during the repo move

### Step 4: Switch Dependents

- update `tool.uv.sources` paths in dependent repos
- rerun local validation for every dependent repo
- update release docs and trusted publisher entries

### Step 5: Remove Old In-Repo Package Copy

- only after all dependents validate cleanly
- keep the repo history and changelog clear about the move

## Recommendation

Current recommendation:

- keep `xian-runtime-types` in `xian-contracting` for now
- keep `xian-accounts` in `xian-contracting` for now
- revisit extraction only after the shared package APIs and scope have settled

If one package is extracted first later, it should probably be
`xian-runtime-types`.
