# Historical initial v1.3 report (a402540b)

This capture predates reconciliation. Current results and rulings are in [REPORT-v1.3.md](../../../REPORT-v1.3.md).

# v1.3 conformance update

This report covers suite **v1.3**, targeting spec **v1.3-draft** at `e19dd1c21c19c5be1201c3b6a42c59c28b5c2887`. The implementation under test was built from Rust source revision `a402540b39cedc7f788472297add7ae2f8a6631a`.

The executable reported `kogen a402540b (2026-10-07)` and had SHA-256 `a88ce05acbd6e45493d03f041e97738a8a09dd547fa797d28491e2b59297f8dc`.

## Added, changed and removed

**39 added cases; 7 replacement cases; 13 old active assertions superseded; 229 unaffected active cases retained.** The effective suite has 275 cases / 616 instances. Case IDs and assertion structures are retained; the demo greeting uses a neutral sample name. [Expectations](../../../expectations/v1.3.json) map all 427 historical/current cases to their spec clauses, active status and replacement chains.

| Retired active assertion | Replacement |
|---|---|
| `v1.2-73-ladder-05` | `v1.3-01-observational-auditor` |
| `v1.2-74-ladder-06` | `v1.3-01-observational-auditor` |
| `v1.2-75-ladder-07` | `v1.3-01-observational-auditor` |
| `v1.2-76-ladder-08` | `v1.3-01-observational-auditor` |
| `v1.2-77-ladder-09` | `v1.3-01-observational-auditor` |
| `v1.2-78-ladder-10` | `v1.3-01-observational-auditor` |
| `v1.2-79-ladder-11` | `v1.3-01-observational-auditor` |
| `v1.2-03-consecutive-request-byte-prefix` | `v1.3-10-reusable-prefix` |
| `shape-12` | `v1.3-16-shape-passes-fallback` |
| `shape-13` | `v1.3-17-shape-six-passes` |
| `v1.2-130-state-11` | `v1.3-44-run-schema` |
| `v1.2-131-state-12` | `v1.3-45-report-default` |
| `state-03` | `v1.3-46-valid-config` |

The auditor is observational under both land policies, with calibrated demotion explicitly refused. Baseline fixtures bind setup_inputs-independent source trees and changed check/environment context. Recovery fixtures kill real owners and inspect real git trees, modes, links and deletion preservation, including create-only publication adoption, failure/retry and post-CAS work. Shape fixtures exercise both counters, guards, style repairs, combined audits, retries/continuations, last allowances, receipts, project/machine overrides and Grok fallback. Prefix fixtures cover two Shapes, two Builds and Shape-to-Build, accepting equivalent outer HTTP JSON serialization. Cache fixtures exercise feasible versus infeasible qualification and complete/partial telemetry.

## Case inventory and mutation results

**46/46 passing controls; 46/46 deliberately wrong fakes rejected; zero survivors.** The executable [fake](../../../tests/fakes/wrong_kogen.py) emits faulty observations at the same oracle boundary used by the cases. These are assertion-sensitivity checks, not a claim that the fake implements the full CLI. Real-git controls inspect contents/modes/symlinks through the production recovery oracle. The [mutation results](../../../reference/results/v1.3/mutations.json) name each fault and diagnostic.

| Case | Change | Contract | Rust result | Killed mutation |
|---|---|---|---|---|
| [v1.3-01-observational-auditor](../../../cases/v1.3/v1.3-01-observational-auditor.json) | replacement | A1 pass / required A2 fail never lands under either policy | fail | `demote` |
| [v1.3-02-malformed-audit](../../../cases/v1.3/v1.3-02-malformed-audit.json) | added | Unknown, duplicate and garbled audit replies warn and preserve gate | fail | `suppress-audit-warning` |
| [v1.3-03-audit-repair-verified](../../../cases/v1.3/v1.3-03-audit-repair-verified.json) | added | Only repaired bytes with a new green verification land | fail | `skip-verification` |
| [v1.3-04-demotion-refused](../../../cases/v1.3/v1.3-04-demotion-refused.json) | added | Experimental demotion true refuses load without calibration | fail | `accept-experimental` |
| [v1.3-05-observational-default](../../../cases/v1.3/v1.3-05-observational-default.json) | added | Explicit demotion false is accepted; default policy is green | fail | `reject-false` |
| [v1.3-06-baseline-source-tree](../../../cases/v1.3/v1.3-06-baseline-source-tree.json) | added | Source-only base change hits setup, misses baseline and replaces red rows | fail | `stale-baseline` |
| [v1.3-07-baseline-exact-base](../../../cases/v1.3/v1.3-07-baseline-exact-base.json) | added | Dirty and stale checkouts cannot stand in for the resolved base tree | fail | `dirty-base` |
| [v1.3-08-baseline-context](../../../cases/v1.3/v1.3-08-baseline-context.json) | added | Changed effective check deadlines invalidate the baseline | pass | `ignore-check-context` |
| [v1.3-09-baseline-regression](../../../cases/v1.3/v1.3-09-baseline-regression.json) | added | An old red row cannot excuse a defect reintroduced on the new green base | fail | `excuse-regression` |
| [v1.3-10-reusable-prefix](../../../cases/v1.3/v1.3-10-reusable-prefix.json) | replacement | Same-conversation provider-visible prefix and append-only input survive JSON serialization choices | fail | `rewrite-history` |
| [v1.3-11-cross-session-prefix](../../../cases/v1.3/v1.3-11-cross-session-prefix.json) | added | Two Shapes, two Builds and Shape-to-Build share static instructions/schemas with distinct threads | fail | `prefix-pollution` |
| [v1.3-12-shape-receipt](../../../cases/v1.3/v1.3-12-shape-receipt.json) | added | Successful Shape accounts shaper and separate auditors, tokens and all-in elapsed time | fail | `shape-counter` |
| [v1.3-13-shape-turn-fallback](../../../cases/v1.3/v1.3-13-shape-turn-fallback.json) | added | Primary turn 60 starts exactly one fresh fallback; unused primary pass slots are not counted | fail | `shape-counter` |
| [v1.3-14-shape-turn-exhausted](../../../cases/v1.3/v1.3-14-shape-turn-exhausted.json) | added | Two 60-turn conversations exhaust at 120 attempts and publish a failure receipt | fail | `shape-counter` |
| [v1.3-15-shape-last-turn](../../../cases/v1.3/v1.3-15-shape-last-turn.json) | added | A valid traversal on primary turn 60 succeeds without fallback | fail | `shape-counter` |
| [v1.3-16-shape-passes-fallback](../../../cases/v1.3/v1.3-16-shape-passes-fallback.json) | replacement | Three counted failures start fallback slots 4–6; override propagates to fresh conversation | fail | `shape-counter` |
| [v1.3-17-shape-six-passes](../../../cases/v1.3/v1.3-17-shape-six-passes.json) | replacement | Fallback third failed pass exits 1; receipt counts six actual validations | fail | `shape-counter` |
| [v1.3-18-shape-retry-usage](../../../cases/v1.3/v1.3-18-shape-retry-usage.json) | added | Failed retry is an attempt under one logical turn and remains unknown usage | fail | `shape-counter` |
| [v1.3-19-shape-provider-failure](../../../cases/v1.3/v1.3-19-shape-provider-failure.json) | added | Provider failure keeps exit 4 and publishes attempts without Shape fallback | fail | `shape-counter` |
| [v1.3-20-fallback-role-rejected](../../../cases/v1.3/v1.3-20-fallback-role-rejected.json) | added | fallback_shaper stays an internal alias, never a configurable role | fail | `accept-experimental` |
| [v1.3-21-cross-provider-role-rejected](../../../cases/v1.3/v1.3-21-cross-provider-role-rejected.json) | added | A selected Grok provider refuses a ChatGPT shaper override before credentials | fail | `accept-experimental` |
| [v1.3-22-recovery-first](../../../cases/v1.3/v1.3-22-recovery-first.json) | added | Killed before first snapshot preserves latest complete tree and survives repeat recovery | fail | `lose-latest` |
| [v1.3-23-recovery-later](../../../cases/v1.3/v1.3-23-recovery-later.json) | added | Killed after an earlier snapshot preserves latest complete tree and survives repeat recovery | fail | `lose-latest` |
| [v1.3-24-recovery-ref-failure](../../../cases/v1.3/v1.3-24-recovery-ref-failure.json) | added | Real git publication failure requires a lossless archive or retained workspace | fail | `lose-latest` |
| [v1.3-25-cache-production](../../../cases/v1.3/v1.3-25-cache-production.json) | added | cache production | pass (offline fixture) | `production-gate` |
| [v1.3-26-cache-blocks](../../../cases/v1.3/v1.3-26-cache-blocks.json) | added | cache blocks | pass (offline fixture) | `ignore-blocks` |
| [v1.3-27-cache-incomplete](../../../cases/v1.3/v1.3-27-cache-incomplete.json) | added | cache incomplete | pass (offline fixture) | `unknown-is-miss` |
| [v1.3-28-cache-feasible](../../../cases/v1.3/v1.3-28-cache-feasible.json) | added | cache feasible | pass (offline fixture) | `lower-threshold` |
| [v1.3-29-cache-infeasible](../../../cases/v1.3/v1.3-29-cache-infeasible.json) | added | cache infeasible | pass (offline fixture) | `accept-infeasible` |
| [v1.3-30-cache-miss-vs-incomplete](../../../cases/v1.3/v1.3-30-cache-miss-vs-incomplete.json) | added | cache miss vs incomplete | pass (offline fixture) | `incomplete-is-pass` |
| [v1.3-31-shape-style](../../../cases/v1.3/v1.3-31-shape-style.json) | added | Two free style repairs spend turns but leave the counted validation allowance intact | fail | `shape-counter` |
| [v1.3-32-shape-combined-repair](../../../cases/v1.3/v1.3-32-shape-combined-repair.json) | added | Coverage and audit feedback combine into one repair with separate auditor turns | fail | `shape-counter` |
| [v1.3-33-shape-stream-continuation](../../../cases/v1.3/v1.3-33-shape-stream-continuation.json) | added | Partial-stream continuation spends attempts within the same logical turn | fail | `shape-counter` |
| [v1.3-34-grok-fallback](../../../cases/v1.3/v1.3-34-grok-fallback.json) | added | Grok primary pass exhaustion starts fresh Grok with the same effective model/effort | fail | `cross-provider-fallback` |
| [v1.3-35-machine-fallback](../../../cases/v1.3/v1.3-35-machine-fallback.json) | added | Machine shaper effort override propagates to both fresh Shape conversations | fail | `shape-counter` |
| [v1.3-36-recovery-adopt-publication](../../../cases/v1.3/v1.3-36-recovery-adopt-publication.json) | added | Crash between durable publication and run-record publication adopts existing candidate exactly once | fail | `duplicate-publication` |
| [v1.3-37-recovery-create-only](../../../cases/v1.3/v1.3-37-recovery-create-only.json) | added | Later workspace state gets a separate snapshot without overwriting a published recovery candidate | fail | `overwrite-candidate` |
| [v1.3-38-recovery-post-cas](../../../cases/v1.3/v1.3-38-recovery-post-cas.json) | added | Post-CAS recovery remains landed while preserving later workspace edits as unverified | fail | `lose-latest` |
| [v1.3-39-recovery-live-owner](../../../cases/v1.3/v1.3-39-recovery-live-owner.json) | added | Recovery leaves a live owner and its sole workspace untouched | pass | `destroy-live` |
| [v1.3-40-audit-selector](../../../cases/v1.3/v1.3-40-audit-selector.json) | added | Audit advice preserves repair counts, ranking and winner across sequential and parallel rungs | fail | `rank-advice` |
| [v1.3-41-recovery-failure-retry](../../../cases/v1.3/v1.3-41-recovery-failure-retry.json) | added | Ref and archive failures retain the sole workspace; terminal cleanup retries after fault removal | fail | `lose-latest` |
| [v1.3-42-baseline-environment](../../../cases/v1.3/v1.3-42-baseline-environment.json) | added | Changed effective child environment misses baseline at the identical checked source tree | pass | `stale-environment` |
| [v1.3-43-shape-last-pass](../../../cases/v1.3/v1.3-43-shape-last-pass.json) | added | Valid completion on fallback pass 6 succeeds at the last counted allowance | fail | `shape-counter` |
| [v1.3-44-run-schema](../../../cases/v1.3/v1.3-44-run-schema.json) | replacement | Run schema adds durable recovery identity and pending cleanup; default started policy is green | fail | `old-run-schema` |
| [v1.3-45-report-default](../../../cases/v1.3/v1.3-45-report-default.json) | replacement | Report default land policy is green with empty advisory items | fail | `legacy-default-policy` |
| [v1.3-46-valid-config](../../../cases/v1.3/v1.3-46-valid-config.json) | replacement | Valid v1.3 configuration excludes internal/unknown roles and accepts observational auditing | fail | `valid-config-refused` |

## Rust results against v1.3

| Scope | Passed | Failed | Errors / skips |
|---|---:|---:|---:|
| v1.3 implementation cases | 3 | 37 | 0 / 0 |
| Offline synthetic cache accounting | 6 | 0 | 0 / 0 |
| Unchanged active cases | 194 | 35 | 0 / 0 |
| Effective suite total | 203 | 72 | 0 / 0 |

The three passing implementation cases are `v1.3-08-baseline-context`, `v1.3-39-recovery-live-owner` and `v1.3-42-baseline-environment`. Synthetic cache passes establish accounting only; they do not establish live cache reuse or implementation release qualification.

The 37 failing v1.3 cases in the inventory are expected implementation gaps:

- Auditor/default/config/schema: 01–05, 40, 44–46. Rust still demotes advice, exposes the advisory default, rejects auditor_demotion as unknown, and lacks the new recovery fields.
- Baseline: 06, 07, 09. A source-only change reuses red baseline rows; a dirty/stale checkout is checked; a reintroduced defect is excused and lands.
- Prefix: 10, 11. Role-specific schema subsets omit the shared complete schemas and generic content differs across Shape and Build. Literal outer HTTP JSON byte ordering is not tested.
- Shape/fallback: 12–21, 31–35, 43. Receipts are absent; primary turn exhaustion exits without fallback; combined audit feedback is absent; Grok pass 4 sends gpt-6.1-sol despite an explicitly effective Grok shaper.
- Recovery: 22–24, 36–38, 41. Latest work is not durably preserved/recorded before cleanup, including post-CAS work; publication adoption and pending cleanup retry are absent.

Full final observations: [kogen-rs-v1.3.jsonl](../../../reference/results/v1.3/kogen-rs-v1.3.jsonl). This aggregate selects the final active cases from the inherited run and the v1.3 delta runs; `source_results` identifies each source record. Captured result files are retained alongside it. Personal sample labels and machine-specific paths in the public copies are normalized; statuses, counts and observations are retained.

The inherited failures are observations from macOS, `--jobs 10`, `KOGEN_TIME_SCALE=0.01`, and a 180-second invocation timeout. They are separate from the v1.3 delta; several involve existing script/repair/budget/timing assertions and all six exunit cases fail. No v1.2 parity claim is made. They are classified as `inherited-failure`:

`build-41`, `exunit-01`, `exunit-02`, `exunit-03`, `exunit-04`, `exunit-05`, `exunit-06`, `v1.2-103-ladder-35`, `v1.2-124-build-31`, `v1.2-134-state-27`, `v1.2-39-build-04`, `v1.2-40-build-05`, `v1.2-41-build-06`, `v1.2-54-build-20`, `v1.2-58-build-24`, `v1.2-59-build-25`, `v1.2-61-build-27`, `v1.2-68-build-44`, `v1.2-70-ladder-02`, `v1.2-80-ladder-12`, `v1.2-81-ladder-13`, `v1.2-82-ladder-14`, `v1.2-83-ladder-15`, `v1.2-84-ladder-16`, `v1.2-86-ladder-18`, `v1.2-87-ladder-19`, `v1.2-88-ladder-20`, `v1.2-89-ladder-21`, `v1.2-91-ladder-23`, `v1.2-92-ladder-24`, `v1.2-94-ladder-26`, `v1.2-95-ladder-27`, `v1.2-96-ladder-28`, `v1.2-98-ladder-30`, `v1.2-99-ladder-31`.

## Quint migration

37/37 hand scenarios and the five embedded regressions pass against the pinned models. Approve events/observations now bind `[baseTree, cacheKey]`; gate/04-advisory is observational; recovery includes preservation-result/pending-cleanup transitions and terminal retry; session retains a versioned prefix map with optional shared affinity. Goldens were regenerated by Quint rather than an implementation. Elixir wire expectations were migrated and missing seams remain explicit.

The unchanged Rust `kogen-xspec` adapter fails 37/37 migrated hand traces: approve 0/18, gate 0/5, recovery 0/6, session 0/8. These are abstract adapter gaps, separate from CLI/filesystem evidence. [Quint details](../../../quint/v1.3/README.md) and `reference/results/v1.3/quint-*.txt` retain diagnostics.

The recorded executable/input digest is `951e5b82967e94f30311ac73b276955c4dfd7f20280051e28906f7aa41477e9b`; the file-by-file [manifest](../../../reference/results/v1.3/suite-inputs.json) identifies the corpus used for these observations. The captures predate the public editorial substitutions to the neutral greeting label and portable path tokens; those substitutions preserve the asserted behavior.

## Reproduction and limits

```sh
python3 -m unittest discover -s tests -v
tools/public_scan.sh
KOGEN_SPEC=/path/to/kogen-spec quint/v1.3/run.sh
bin/kogen-conformance run --kogen /path/to/kogen --expectations expectations/v1.3.json
bin/kogen-conformance run --kogen /path/to/kogen --profile v1.3 --case 'v1.3-*'
bin/kogen-conformance summary reference/results/v1.3/kogen-rs-v1.3.jsonl --expectations expectations/v1.3.json
```

The v1.3 receipt/codec/archive projections are documented in [RECEIPTS.md](../../../data/v1.3/RECEIPTS.md); prose does not freeze every receipt field spelling or archive format, so other representations need a lossless adapter projection. Fault tests use isolated HOME/TMPDIR/origins and an explicitly verified native write-failure shim. No live provider replay or demotion calibration was run, and the observed implementation does not meet v1.3 release conformance.
