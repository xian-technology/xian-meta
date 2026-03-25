# Core Repo Cleanup Plan

## Goal

Keep the core Xian repos professionally usable as standalone building blocks,
even when an operator or product team ignores the higher-level packs,
templates, and reference flows.

The target is:

- clean repo boundaries
- minimal but complete human-facing entry docs
- no misleading history-oriented README language
- examples and reference assets that help without muddying package ownership
- cross-repo dependencies that follow the intended architecture

## Current Assessment

The stack is already stronger at the architecture level than it looks from the
top-level docs.

Good:

- `xian-contracting`, `xian-abci`, `xian-cli`, `xian-stack`, `xian-configs`,
  `xian-deploy`, and `xian-py` each have a recognizable primary ownership
  boundary.
- Python package boundaries are mostly clean. For example, `xian-py/examples/`
  are outside `src/`, so they are not shipped inside the published wheel.
- The packs, templates, monitoring presets, and reference apps validate the
  product story without being required for the core node/runtime path.

Not good enough yet:

- root `README.md` files are too contract-heavy and too often written in a
  “what changed recently” style instead of a “what this repo is, how to use it,
  and what principles it follows” style
- `xian-meta` conventions overfit structure and AI traversal, and under-specify
  human-first usage guidance
- some reference-app material has grown inside core repos to the point where it
  can blur the repo identity even if it does not affect packaging
- there is at least one real layering smell:
  `xian-abci` currently imports wallet and decompiler helpers from `xian-py`

## Decision

Do not throw away the recent work.

The core direction is correct. The cleanup should be:

- subtractive in docs
- selective in repo reshaping
- strict on dependency direction

The point is not to remove useful assets. The point is to make the ownership
and entry surface much cleaner.

## Principles

### 1. Human-First README, AI-First AGENTS

`README.md` should be optimized for a human engineer evaluating or using the
repo professionally.

`AGENTS.md` should keep the AI/operator workflow details.

The root README should not read like a migration guide, a changelog, or an
internal contract note.

### 2. Current State Only

Root READMEs should describe the current repo, not the path taken to get there.

Avoid phrases like:

- “now exposes”
- “old”
- “new”
- “still”
- “no longer”

unless the historical comparison is essential for safe use.

### 3. Minimal Surface, Deep Docs Behind It

The root README should stay short and answer:

1. what this repo is for
2. how to use it first
3. what the main principles or constraints are
4. where to go deeper

Detailed contracts, migration notes, and backlog items belong deeper in `docs/`.

### 4. Repo Identity Matters More Than Example Volume

Examples are valuable, but they should not make the repo feel like it owns more
than it actually owns.

Minimal examples that explain usage belong in the repo.
Larger reference-app material should move out once it starts dominating the
reader’s first impression.

### 5. Dependency Direction Must Match Product Architecture

The professional-use test is not just “does it work?”
It is also “does the layering still make sense six months from now?”

`xian-abci` depending on `xian-py` is a smell because the node runtime should
not depend on the external application SDK.

## Concrete Problems To Fix

### Problem A: Root READMEs Are Too Dense And Too Change-Oriented

Examples:

- `xian-py/README.md` is useful, but too long and too much of it reads like
  release notes
- `xian-cli/README.md` is overloaded with lifecycle contract details that
  belong in deeper docs
- `xian-stack/README.md` mixes product identity, backend contract, and many
  detailed command surfaces into one long top page

Desired outcome:

- shorter root READMEs
- one short quick-start or “first use” section
- one principles/constraints section where needed
- move the rest to targeted docs pages

### Problem B: `xian-meta` Needs A Human-First Revision

Current conventions successfully standardized structure, but they push every
repo toward the same contract-heavy README shape.

Desired outcome:

- keep stable file locations
- revise the README template to require:
  - summary
  - quick start
  - key principles or constraints
  - validation
  - deeper docs
- stop requiring “Scope / Key Directories / Validation / Related Docs” to be
  the only top-level shape

### Problem C: Reference Material Placement Needs A Clear Rule

Current state:

- canonical chain assets and pack manifests fit well in `xian-configs`
- minimal SDK usage examples fit in `xian-py`
- the deeper reference apps in `xian-py/examples/` are valuable, but they are
  close to the threshold where they deserve a separate home

Desired outcome:

- keep minimal examples in core repos
- define a threshold for moving full reference applications into a dedicated
  repo such as `xian-reference-apps` or `xian-solutions`

### Problem D: Cross-Repo Dependency Inversion

Current state:

- `xian-abci` imports:
  - `Wallet` from `xian-py`
  - `ContractDecompiler` from `xian-py`

Desired outcome:

- remove the `xian-abci -> xian-py` dependency
- place shared helpers in the correct neutral home

Likely direction:

- move contract-source/decompiler helpers closer to `xian-contracting` or into a
  small neutral helper package
- move key/account helpers into a neutral shared package or a focused account
  helper module owned outside the SDK

## Recommended Staged Path

### Stage 1: Reset The Shared Convention

Owner:
- `xian-meta`

Tasks:

- rewrite `REPO_CONVENTIONS.md` to be human-first
- replace the current root README template with a shorter one
- make the README standard describe current-state-only wording
- explicitly split:
  - `README.md`: human entrypoint
  - `AGENTS.md`: AI/operator workflow entrypoint

Output:

- updated shared convention
- updated README template

### Stage 2: Rewrite Root READMEs Across Core Repos

Owners:
- `xian-abci`
- `xian-contracting`
- `xian-py`
- `xian-cli`
- `xian-stack`
- `xian-configs`
- `xian-deploy`
- `xian-meta`

Tasks:

- rewrite each root README against the revised template
- remove historical/change-log wording
- add one short quick-start or first-use example per repo
- move dense operational or lifecycle detail into deeper docs pages

Priority order:

1. `xian-py`
2. `xian-cli`
3. `xian-stack`
4. `xian-abci`
5. the remaining repos

### Stage 3: Fix The Real Layering Smell

Owners:
- `xian-abci`
- `xian-py`
- potentially `xian-contracting` or a new neutral helper package

Tasks:

- inventory exactly why `xian-abci` imports `Wallet` and `ContractDecompiler`
- move those responsibilities into the right neutral layer
- remove `xian-py` from `xian-abci` runtime dependencies if possible

This is the most important code-level cleanup in this plan.

### Stage 4: Define Reference-Material Placement Rules

Owners:
- `xian-meta`
- `xian-py`
- `xian-configs`
- `xian-docs-web`

Tasks:

- decide what stays in core repos:
  - minimal examples
  - canonical assets
  - essential integration samples
- decide what moves if it grows further:
  - deeper reference apps
  - multi-component solution demos

Recommended rule:

- `xian-configs`: canonical pack assets and contract manifests stay
- `xian-py`: minimal SDK and service examples stay
- large reference applications move to a dedicated repo when they start to
  outweigh the SDK itself

### Stage 5: Optional Extraction Repo

Only do this if Stage 4 shows the threshold has been crossed.

Potential repo:

- `xian-reference-apps`

Possible contents:

- the three deeper reference apps
- shared docker-compose for app-side services
- app-facing walkthroughs that are larger than SDK examples

This is optional, not mandatory.

## Recommended Immediate Next Actions

1. revise `xian-meta` conventions and README template
2. rewrite `xian-py/README.md` as the pilot human-first README
3. rewrite `xian-cli/README.md` and `xian-stack/README.md`
4. plan the `xian-abci -> xian-py` dependency removal before adding more
   features

## Non-Goals

This cleanup is not about:

- removing useful examples just to look minimal
- hiding important docs from AI tools
- flattening the stack into fewer repos
- undoing packs, templates, or reference apps

It is about keeping the professional core understandable and correctly layered.
