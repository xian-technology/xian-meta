# Cross-repo consistency audit

Snapshot: 2026-09-11. This is a source-backed audit of shared contracts across
the sibling workspace, not an exhaustive security review or a release gate.
All five findings have now been fixed in the local working trees and verified.
Nothing has been committed or published. Subsequent deployment/testing was
limited to an isolated localnet; see the live follow-up below. The numbered findings below
preserve the original evidence; their descriptions of broken behavior and old
dependency ranges describe the pre-fix snapshot.

Five actionable inconsistencies were confirmed. The broader pattern was that
independently tested components lacked shared input/output fixtures at their
boundaries. The fixes establish that shared coverage.

## Resolution

| Finding | Implemented change |
| --- | --- |
| 1. JavaScript transaction bytes | Canonical JSON emits sorted key/value pairs directly; encoding, decoding, and copying preserve own `__proto__` properties. Shared golden fixtures pin payloads, signatures, and submitted bytes across both SDKs and both node validators. |
| 2. SDK requirements | All four consumers require `xian-tech-py>=0.5.0,<0.6`. Locks were refreshed where needed. Bridge CI enforces lock freshness; NFT and stable CI install and test the deploy group, including the shared CLI bundle validator. |
| 3. Nested runtime integers | Encoding recursively normalizes dictionaries and lists; conversion recursively restores nested runtime wrappers. Booleans and existing integer boundaries remain unchanged. A processor regression verifies native values reach VM execution. |
| 4. MCP message signing | Signing preserves the exact message, matching verification. Regression cases cover whitespace, newlines, and Unicode. |
| 5. Bundle enforcement | NFT and stable bootstrap validate bundles before connecting, consume manifest source paths/order/budgets, and retain verified source in the deployment plan. Explicit configuration overrides remain available. The shared CLI reader hashes and returns the same bytes, including original line endings. |

The wire format and fixture ownership are documented in
[TRANSACTION_ENCODING_CONTRACT.md](TRANSACTION_ENCODING_CONTRACT.md). Product,
SDK, runtime package, and public documentation describe the updated behavior.
Existing Graphify work and exempt checkouts were preserved.

## Post-fix verification

Local verification on 2026-09-11 used the installed sibling-source environments.
This first verification stage submitted no live transactions. Counts below
exclude reported subtests; subsequent live results are recorded separately.

| Surface | Result |
| --- | --- |
| Contracting/runtime full default suite | 821 passed; 46 optional-native tests deselected |
| Contracting optional-native suite | 46 passed, using the local VM extension |
| Python SDK full suite | 198 passed |
| ABCI full suite | 693 passed, 1 skipped; VM and native fastpath extensions installed |
| CLI full suite | 144 passed |
| Bridge full suite | 91 passed, 2 skipped |
| Stable-protocol full suite | 42 passed, including bootstrap and contract execution |
| NFT Python suite | 8 passed |
| Playground full suite | 33 passed; frontend production export also passed |
| MCP full suite | 91 passed; real stdio initialization and tool discovery also passed |
| JavaScript SDK validation | Types/build passed; 104 tests passed, 2 optional compiler-WASM tests skipped; 6 release tests passed |
| NFT frontend | Type checking/build passed; 38 tests passed |
| Browser wallet validation | Types/build passed; 89 tests and 6 release tests passed |
| Mobile wallet | Type checking passed; 79 tests passed |
| Stack DEX consumers | 12 bootstrap/backend tests passed |
| Meta Graphify helper | 8 tests passed |
| Public documentation | Production build passed |

Regression coverage includes exact signatures and submitted transaction bytes,
numeric-looking and Unicode keys, prototype-named data, nested wrapper conversion,
modified bundle rejection before client creation, missing roles, bundle order and
budget overrides, already-existing contracts, and using the source bytes that
were actually verified. Both the Python and native node validation paths accept
the shared golden transactions.

Additional checks passed: Ruff lint in all nine affected Python repos; formatting
of changed Python files; all four affected lock freshness checks; the three
modified CI workflows through actionlint; network manifests, allocation sync,
workspace conventions, and whitespace checks. Refreshed directed graphs were
used for a final impact review, with sibling source searches and downstream
wallet/DEX checks supplementing graph edges.

Registry-only dependency resolution passed for bridge, NFT, and stable-protocol.
Playground still requires its documented sibling-source setup because
`xian-tech-vm-core` is not published in the registry. That packaging limitation
predates these fixes; no package publication was attempted.

Full-repo formatter checks still identify pre-existing drift in untouched files
in MCP, playground, and stable-protocol; the same failures were confirmed against
their HEAD contents. These unrelated files were not reformatted. Environment-
dependent skips and optional compiler-WASM tests are not counted as passes.
At this first stage, live localnet deployment, PostgreSQL integration without a
configured test URL, and browser/mobile device sessions were not exercised. The checks above validate
the changed code and covered consumers, not every possible production flow.

## Live follow-up

A five-validator localnet subsequently passed 31 executed integrated phases,
818-block native replay, focused protocol safety, and live SDK/product/MCP
regressions. Optional PostgreSQL/browser and compiler-WASM checks also ran.
Live browser testing found and fixed indexed-event JSON decoding and UTC date
parsing defects in the JS SDK/NFT app. Updated suites pass: SDK 108 tests plus 6
release tests, NFT 41, browser wallet 89 plus 6, mobile wallet 79, governance UI 42.

The additional native-VM defect in function-local `ForeignHash` construction
was subsequently fixed. Dynamic foreign reads retain read-only enforcement and
metering; the shipped NFT checker, automatic discovery, profiles and activity
pass against the corrected localnet. See
[the foreign-storage validation](../../xian-stack/docs/FOREIGN_STORAGE_VALIDATION.md)
for the implementation, 891 runtime tests, native/product gates and both replays.
The [initial live report](../../xian-stack/docs/LOCALNET_CONSISTENCY_VALIDATION.md)
preserves the original failure evidence and broader test coverage.
The scope and numbered reproductions below describe the original audit stage.

## Scope and method

- Screened all 29 non-exempt repos from `workspace-repos.json` through graph
  navigation, dependency/configuration searches, and workspace checks.
- Deeper source review covered transaction encoding, signing, runtime values,
  SDK deployment compatibility, and product bootstrap paths, principally in
  `xian-js`, `xian-py`, `xian-contracting`, `xian-abci`, `xian-mcp-server`,
  `xian-bridge`, `xian-nft`, `xian-stable-protocol`, `xian-playground-web`,
  `xian-dex`, `xian-cli`, `xian-stack`, and `xian-configs`.
- Also screened wallet and application consumers for shared SDK usage and
  network configuration. This does not mean every application flow was tested.
- Excluded `.github` and `xian-intentkit` per the workspace manifest.
- Graph indexes were current and directed. Queries selected available graph
  vocabulary: transaction, signing, network, deploy, nonce, config, compiler,
  runtime, client, manifest. Graph gaps and truncated neighborhoods were
  followed by source searches; missing edges were not treated as evidence.
- Reproductions used synthetic signing keys, offline node validation, and mock
  deployment clients. No chain transactions were broadcast.
- Existing uncommitted Graphify work was preserved. Licensing was outside scope.

## 1. High: JavaScript canonical serialization changes valid transaction data

**Owners:** `xian-js`; protocol counterparts: `xian-abci`, `xian-py`, and the
native fastpath in `xian-contracting`. Consumers include wallets and web apps
using `@xian-tech/client`.

[`sortKeysDeep`](../../xian-js/packages/client/src/encoding.ts#L70) copies sorted
keys into an ordinary JavaScript object. [`encodeRuntime`](../../xian-js/packages/client/src/encoding.ts#L127)
then uses `JSON.stringify`. JavaScript enumerates integer-index keys numerically,
even after insertion in lexical order. The node requires canonical lexical order.

For `kwargs = {data: {"2": "two", "10": "ten"}}`:

| Producer | Encoded nested object |
| --- | --- |
| JavaScript SDK | `{"2":"two","10":"ten"}` |
| Python SDK / node | `{"10":"ten","2":"two"}` |

Using the actual SDK `buildTx` and `signTx`, both the native and Python node
validation paths reject the resulting submitted bytes with
`Transaction bytes are not canonical`. An otherwise identical transaction with
ordinary alphabetic keys passes both paths. These nested keys are valid protocol
inputs; the identifier restriction applies to top-level kwargs names.

There is a second failure in the same object-copying code: an own `__proto__`
key parsed from JSON is lost when assigned into `{}`. Input
`{"data":{"__proto__":"keep me","ok":true}}` becomes
`{"data":{"ok":true}}`. The altered transaction passes node validation,
so this is silent data loss rather than just rejection.

Sources: [SDK signing/broadcast](../../xian-js/packages/client/src/client.ts#L1078),
[node canonical-byte check](../../xian-abci/src/xian/utils/encoding.py#L72),
[native canonical writer](../../xian-contracting/packages/xian-fastpath-core/src/lib.rs#L376).

**Fix:** use a canonical JSON writer that emits sorted key/value pairs directly,
and preserve own keys safely throughout object copying and decoding. Changing
only the comparator or only using a null-prototype object will not fix numeric
key ordering. Add shared fixtures for numeric keys, `__proto__`, Unicode keys,
runtime wrappers, and exact signed/submitted bytes. Shared canonicalization
vectors are already listed in `xian-js/docs/BACKLOG.md`; these failures make that
work concrete and urgent. Keep the node's canonical validation strict.

## 2. Medium: Four apps still declare the pre-source-deployment Python SDK

**Owners:** `xian-bridge`, `xian-nft`, `xian-stable-protocol`,
`xian-playground-web`; shared API owner: `xian-py`.

| Consumer | Declared Python SDK requirement |
| --- | --- |
| [Bridge](../../xian-bridge/pyproject.toml#L45) | `>=0.4.15,<0.5` |
| [NFT deploy group](../../xian-nft/pyproject.toml#L15) | `>=0.4.11,<0.5` |
| [Stable-protocol deploy group](../../xian-stable-protocol/pyproject.toml#L15) | `>=0.4.11,<0.5` |
| [Playground](../../xian-playground-web/pyproject.toml#L12) | `>=0.4.8,<0.5.0` |

The current workspace SDK is **0.5.0**. Its
[`submit_contract`](../../xian-py/src/xian_py/xian_async.py#L1054) sends a `code`
source string. The current
[submission contract](../../xian-contracting/src/contracting/contracts/submission_source.s.py#L48)
requires that source parameter.

This is a behavior mismatch, not simply an old version number. Inspection of
the locally available `xian-py` tag `v0.4.19` shows `deploy_contract` compiling an
artifact and `submit_contract` sending `kwargs["deployment_artifacts"]`.
That version is permitted by every range above and cannot deploy through the
current source-only contract interface. Bridge also passes a source string
directly to `submit_contract`, whereas that tagged API requires an artifact dict.

Sibling `[tool.uv.sources]` overrides mask the declaration drift during local
development: NFT, stable-protocol, and playground lock checks pass with the local
0.5.0 source. An installation resolving the declared registry requirements instead
does not describe the API those codebases are tested against. No registry
installation was performed; the incompatibility is established from the allowed
tag's implementation and the current node interface.

Bridge has an additional reproducible lock drift:
`uv lock --check` resolves dependencies and exits 1 because its lockfile needs an
update. The lock still records `xian-tech-py` 0.4.20b1 and older accounts/runtime
package metadata. Its CI uses
[`uv sync --frozen`](../../xian-bridge/.github/workflows/validate.yml#L82), which
does not enforce lock freshness. This is not a claim that the entire CI run was
tested or necessarily fails.

**Fix:** align the four requirements with the supported 0.5 SDK, refresh the
affected lock metadata, and check lock freshness in bridge CI. Exercise both
sibling-source development and the intended distributable installation mode.
Keep deployments source-only; do not restore obsolete artifact submission to
accommodate stale consumers.

## 3. Medium: Python runtime encoding stops recursing into nested lists

**Owner:** `xian-contracting/packages/xian-runtime-types`; affected API:
`xian-py` transaction preparation; counterpart: `xian-js`.

[`encode_ints_in_dict`](../../xian-contracting/packages/xian-runtime-types/src/xian_runtime_types/encoding.py#L81)
wraps large integers in dictionaries and directly contained lists. A list item
that is itself a list falls through unchanged. `encode` also does not normalize
a top-level list.

The Python SDK uses this encoder in
[`normalize_transaction_payload`](../../xian-py/src/xian_py/transaction.py#L232).
With `n = 2**80`, actual `create_tx` results were:

| kwargs | Python SDK | JavaScript SDK + node |
| --- | --- | --- |
| `{"data": [n]}` | Encoded and accepted by node | Supported |
| `{"data": [[n]]}` | `TransactionError: Invalid payload provided` | Wrapped as `__big_int__`; accepted by both node validators |

The integer is supported; only its nesting changes whether Python can submit it.
Other runtime values handled by `JSONEncoder.default`, such as decimals, should
not be assumed to share this exact failure.

**Fix:** replace the partial traversal with one recursive value normalizer for
dicts, lists, and scalars. Preserve booleans and existing wrapper conventions.
Add shared vectors for top-level lists, nested lists, mixed containers, and
integer bounds, then validate the resulting wire data through both node paths.

## 4. Medium: MCP message signing fails its own whitespace round trip

**Owner:** `xian-mcp-server`; counterpart: `xian-py` wallet primitives.

[`sign_message`](../../xian-mcp-server/xian_server.py#L1368) signs
`message.strip()`, while
[`verify_signature`](../../xian-mcp-server/xian_server.py#L1392) verifies the
original `message`. `Wallet.sign_msg` itself preserves the supplied string.

Direct execution of both MCP tool functions using the synthetic private key
`"01" * 32` confirmed:

- Signing `" hello "` and verifying `" hello "` returns `False`.
- Verifying that signature against `"hello"` returns `True`.

**Fix:** preserve the exact message bytes when signing. Validate missing/empty
input separately. Add a round-trip test with spaces, newlines, and Unicode.
This is independent of the intentional distinction between raw transaction
signing primitives and the wallet's versioned signed-message envelope.

## 5. Medium: Product bootstrap paths do not enforce the same bundle contract

**Owners:** `xian-nft`, `xian-stable-protocol`; consistent counterpart:
DEX bootstrap through `xian-stack` and `xian-cli`.

The NFT README describes the hash-pinned bundle as the canonical deployer
interface. However, its
[`_contract_source`](../../xian-nft/scripts/bootstrap_nft.py#L47) and
[`_deploy_if_missing`](../../xian-nft/scripts/bootstrap_nft.py#L63) read and deploy
raw source files without loading the manifest. Stable-protocol's
[`_deploy_contract`](../../xian-stable-protocol/scripts/bootstrap_protocol.py#L326)
has the same source-loading pattern. Plans, order, and chi defaults are maintained
separately from their bundle files.

By comparison, DEX delegates to a stack bootstrap that calls
[`validate_contract_bundle`](../../xian-stack/scripts/localnet-dex-bootstrap.py#L289)
before using the bundle. The shared
[validator](../../xian-cli/src/xian_cli/contract_bundles.py#L97) checks source hashes.

Reproduction used a temporary copy of the NFT bundle and contracts, with one
comment appended to a source file. The shared validator rejected the SHA mismatch;
the NFT deployment helper passed the modified source to a mock SDK successfully.
No actual contract was deployed. All 11 checked-in source hashes across the three
bundles currently match; this finding concerns enforcement during bootstrap,
not an existing tampered bundle.

**Fix:** validate and consume the bundle in the same bootstrap invocation, using
it for source selection/order/defaults. Keep product-specific constructor and
configuration logic local. If raw-source development is intentionally supported,
make that an explicit mode with accurate documentation rather than an implicit
bypass of the documented bundle workflow.

## Recommended sequence

1. Fix JavaScript canonical serialization and establish shared wire fixtures.
2. Align Python SDK declarations and bridge lock freshness with source deployment.
3. Make runtime integer normalization fully recursive and reuse the wire fixtures.
4. Fix the MCP exact-message round trip.
5. Align product bootstrap bundle enforcement.

The first two are the most consequential cross-repo mismatches. There is no need
to homogenize unrelated frontend stacks or local implementation style to address
these issues. Repo-local implementation follow-ups belong with the owners above.

## Validation and limitations

- Workspace conventions: **pass** for the 29 non-exempt repos.
- Graph freshness/direction before review: **pass** for all 29.
- `uv lock --check --offline`: **16 of 17 pass**. Bridge needed uncached registry
  metadata; retrying its check with network access confirmed the stale lock.
- Network manifest validation via `xian-cli/.venv/bin/python
  xian-configs/scripts/validate-manifests.py`: **pass**, covering four network
  manifests, three templates, and four authored contract sets.
- Mainnet allocation synchronization check: **pass**.
- Bundle source hashes: **11 of 11 match**, across DEX, NFT, and stable-protocol.
- JS types/client build: **pass**; reproductions used the rebuilt SDK.
- Actual JS transaction construction/signing and both node static validators
  reproduced finding 1; Python transaction preparation reproduced finding 3.
- Actual MCP functions reproduced finding 4. An isolated modified bundle and
  mock deployment client reproduced finding 5.
- Did not run every repo's full test suite, start a localnet, perform custody
  flows, test live browsers/mobile devices, or audit every contract. Passing
  screening checks are not evidence that those untested surfaces are bug-free.

To inspect the old SDK interface without changing a checkout:

```bash
git -C xian-py show v0.4.19:src/xian_py/xian_async.py
```

Minimal encoding reproductions from the workspace root (Node with TypeScript
stripping support and the existing Python environment):

```bash
node --input-type=module - <<'JS'
import { canonicalizeRuntime } from './xian-js/packages/client/src/encoding.ts';
console.log(canonicalizeRuntime({kwargs: {data: {'2': 'two', '10': 'ten'}}}));
console.log(canonicalizeRuntime(JSON.parse('{"data":{"__proto__":"keep me","ok":true}}')));
JS

PYTHONPATH=xian-py/src xian-abci/.venv/bin/python - <<'PY'
from xian_py import Wallet
from xian_py.transaction import create_tx
from xian.utils.tx import canonical_json
print(canonical_json({'kwargs': {'data': {'2': 'two', '10': 'ten'}}}))
wallet = Wallet('01' * 32)  # Synthetic test key only.
for data in ([2**80], [[2**80]]):
    payload = dict(chain_id='xian-local-1', sender=wallet.public_key,
                   nonce=0, chi_supplied=100, contract='con_probe',
                   function='run', kwargs={'data': data})
    try:
        create_tx(payload, wallet)
        print('prepared')
    except Exception as error:
        print(type(error).__name__, str(error))
PY
```
