# Quantum resistance across the Xian stack

Status: account custody implemented and locally tested; enrollment closed.
This is a cross-repository dependency plan, not a claim that the network is
quantum-resistant or authorization to launch it. Final genesis remains deferred.

## What the master backup changes

[Single-master custody](ACCOUNT_MASTER_BACKUP.md) gives the user one current
backup per account and chain. Fresh 256-bit random material derives separate
active and recovery Ed25519/ML-DSA-65 credentials. Both signature algorithms are
required by the existing registry protocol. The account identifier and currency
balance key stay unchanged. The offline master is not stored in the daily vault.
Rotation/recovery requires a fresh, verified replacement backup; retain the old
one until the new authority commits.

This improves custody without changing consensus signatures, shielded proofs or
transport encryption. A longer Ed25519 private key alone cannot provide this
upgrade. ML-DSA is a standardized post-quantum signature scheme, with security
based on current assumptions rather than a guarantee against all future attacks.
See [NIST FIPS 204](https://csrc.nist.gov/pubs/fips/204/final) and its current
errata. Seed-based key storage is addressed in the
[NIST PQC FAQ](https://csrc.nist.gov/Projects/Post-Quantum-Cryptography/faqs).

## Required work, in priority order

| Boundary | Current source evidence | Required work and acceptance evidence |
| --- | --- | --- |
| Validator consensus | `xian-abci/src/xian/genesis_builder.py` configures `pub_key_types: [ed25519]`; `node_setup.py` creates Ed25519 validator and node keys. | Design an explicit consensus upgrade with a reviewed hybrid signature scheme. Change validator key encoding, genesis, votes/proposals/commits, evidence, remote signing and light-client verification together. Reject downgrade paths. Benchmark quorum latency, signature bandwidth, block limits and adversarial verification on the exact release binary and distributed hosts. An ABCI transaction change alone cannot secure CometBFT consensus. |
| Imported accounts and privileged authorities | The registry supports hybrid accounts, while imported unenrolled addresses retain Ed25519 access. The migration deliberately preserves those identities and balances. | Establish an owner-approved migration policy, including dormant holders, before any legacy cutoff. Do not silently freeze or confiscate funds. Enroll governance, operators and selected contract owners; audit every contract/admin path so legacy key verification cannot bypass registry authority. Test old-key rejection, recovery, nonce handling and authorization after crashes. |
| Shielded proof soundness | `xian-contracting/packages/xian-zk/src/core.rs` uses Groth16 over BN254; shielded note circuits use the same proof family. | Replace or exclude these proof paths from a post-quantum launch scope. Research a reviewed post-quantum proof system and design new circuits, verification, parameters, metering, note migration and custody recovery. This is a separate protocol project: forged proofs could threaten asset integrity even with strong account signatures. |
| Encrypted data and network channels | `xian-contracting/packages/xian-zk/python/xian_zk/shielded_notes.py` uses Curve25519/NaCl boxes; `xian-py/src/xian_py/crypto.py` exposes related encryption helpers. | Introduce versioned, authenticated hybrid key establishment with a reviewed post-quantum KEM, including recipient discovery and recovery. Audit P2P, RPC/TLS and relayer channels too. Existing recorded ciphertext cannot be made confidential retroactively. ML-DSA signatures do not encrypt data. |
| Bootstrap and off-chain authority | Node setup, signed manifests, genesis distribution, state-sync trust, wallet login and operator tooling span several repositories. | Inventory all trust roots and verification paths, including release signing, snapshots/checkpoints, hardware signers and light clients. Upgrade applicable signatures and transport; bind chain, purpose, expiry and replay protection. Generic legacy message verification must not authenticate an enrolled hybrid account. Verify restore/bootstrap against malicious and stale inputs. |
| External bridges | `xian-bridge` connects to Solana as well as Xian. | Upgrade the Xian-side signer and operational custody, but explicitly account for the external chain's consensus and authorization. A Xian-only upgrade cannot make bridged assets independent of their source chain's security. |

For encryption, [NIST FIPS 203](https://csrc.nist.gov/pubs/fips/203/final)
standardizes ML-KEM; it is a key-establishment component, not a complete messaging
or transport protocol. Select the hybrid construction and security parameters
through review. Similarly, hash-based transparent proof systems are candidates
for research, not a drop-in replacement for the existing shielded circuits.

## Enrollment and launch gates

Keep enrollment disabled while the remaining account release gates are open:

- Independent review of the hybrid protocol, seed derivation, parsers, backup
  lifecycle, wallet storage and every privileged authorization path.
- Reproduce load/restart/recovery tests with the exact release-pinned CometBFT,
  paid fees, production limits and distributed deployment. Current single-host
  free-metered rehearsals establish correctness under tested conditions, not
  production capacity or network DoS resistance.
- Test packaged browser/mobile releases on supported real devices, secure
  storage, app termination, backup download/import and interrupted submission.
- Rehearse the eventual chosen snapshot and selected contract balances against
  the final launch bundle, with independent conservation/access checks. The
  importer can be tested now without creating final genesis.

Account enrollment and whole-chain post-quantum readiness are separate decisions.
Do not label the whole chain quantum-resistant while consensus or an enabled
asset-authorizing proof path remains vulnerable to quantum attacks. Define the
target security level, benchmark all parameters, and retain cryptographic
agility without allowing an attacker to select a weaker mode.

Recommended next engineering project: the consensus signature specification and
an isolated multi-validator prototype, alongside the decision whether shielded
features belong in the initial post-quantum network scope.
