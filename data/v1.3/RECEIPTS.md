# v1.3 observation boundaries

Normative source: [kogen-spec commit `2e6667eae0d626a5b894588aa465bab35b999928`](https://github.com/KogenAI/kogen-spec/commit/2e6667eae0d626a5b894588aa465bab35b999928),
version `v1.3-draft`. This observation-boundary projection originated in the earlier
`e19dd1c21c19c5be1201c3b6a42c59c28b5c2887` snapshot. Its provider and queue
cases were last reconciled against `501e3c3`. The current vendored gate contract
and refreshed help fixtures are checked separately; the fresh Rust gate and
remaining case-coverage limits are recorded in the v1.3 report.

## Shape receipt projection

§3.2.1 requires receipt semantics but does not freeze every JSON member spelling.
The suite uses the following neutral projection for `shape-accounting.json`:

```json
{
  "schema": 1,
  "profile": "shape-v1.3",
  "outcome": "success",
  "conversations": [
    {"conversation_id": "opaque", "model": "effective-model", "effort": "effective-effort",
     "logical_turns": 2, "validation_passes": 1, "style_repairs": 0}
  ],
  "roles": {},
  "http_attempts": 4,
  "validation_passes": 1,
  "finish_guards": 0,
  "repairs": {},
  "tokens": {"input": 400, "cached_input": 80, "output": 120, "reasoning": 40},
  "unknown_usage_attempts": 0,
  "elapsed_ms": 1500
}
```

`outcome` is `success` or `failure`. `roles` and `repairs` retain the per-role
logical-turn/attempt counters and repairs by kind; implementations can keep
additional detail. Token `input` excludes cached input, following §4.9.5.
Attempts with failed, partial or missing usage stay in the attempt total; known
counts are summed separately. Per-conversation counters reset at fallback; total
validation traversals count actual work, independently of slots 4–6. The fixture
provider publishes its served usage for the oracle to compare with the receipt.
The receipt must be inside the checkout's state root and retained on failure.

This projection is a suite adapter convention, not a claim that the prose fixes
all of these field names. A differently shaped implementation receipt needs a
lossless adapter projection before running these assertions; no missing field is
silently synthesized.

## Recovery and filesystem faults

§2.8 freezes `recovery` and `cleanup_pending`. Git recovery records are checked
against real origin objects: exact contents, deletions, untracked files, executable
mode, symlink target, tree identity, base and `unverified` classification. The
suite retains earlier refs and verifies publication adoption/counts and repeated
recovery. Fixtures kill an actual CLI owner, pause a real git CAS, and publish real
git objects before leaving a run record unpublished.

The archive branch accepts an adapter manifest at `<archive>.json` (or
`archive.manifest` in an object-valued archive identity), with a `files` map in the
same neutral text/mode form used in the cases and `sha256` binding the archive
bytes. The adapter exposes a tar archive (`archive.path` when object-valued).
The oracle reads archive members without extracting them and verifies actual
contents, modes, symlink targets and deletions as well as the digest. This is an adapter boundary:
production archives must be lossless and durable; an abstract Quint pass proves
neither property. Archive implementations need to expose this projection.

`tests/faults/preservation.c` denies archive creation/publication in disposable
run/recovery destinations while keeping run records and journals writable. A
PATH git shim independently denies recovery-ref publication. The runner compiles
the shim and verifies that an actual archive write gets EACCES before using it.
The loader is DYLD_INSERT_LIBRARIES on macOS or LD_PRELOAD on Linux. This optional
fault fixture needs a C compiler and a binary that permits loader interposition;
a failed injection is a harness error, never an implementation gap.

## Provider-visible prefix

The oracle compares decoded provider content and canonical complete tool schemas,
append-only history, settings and thread identities. It accepts whitespace,
escaping and outer JSON-member order differences. Static instructions are a
leading developer/system item, or the initial paragraph of a string-valued
`instructions` codec; role instructions and variable task data follow that
boundary. The boundary must contain meaningful generic instructions. Different
invocations have different threads; they can share evidenced safe affinity.
No exact cache/thread hash bytes or different-per-Build cache key is required.

## Measurement and fake checks

Cases 25–30 exercise the offline measurement boundary, not the Kogen CLI. Their
synthetic adapter declares its 1,024-token block/minimum, endpoint, tokenizer,
namespace/affinity, retention, appended budget and version identities. Missing
usage is incomplete; complete observed zero is a miss. The third-and-later warm
requests are rejected before measurement when E/T < .95 or appended budget is
exceeded. Feasible designated warm requests still require C/T >= .95.
`live_release_qualified` is always false for these fake fixtures.

`tests/fakes/wrong_kogen.py` is an executable observation-boundary fake. Every
new case has an independent passing observation fixture and a named mutation
that its production oracle rejects. Recovery controls use real git objects and
filesystem modes/symlinks. This establishes assertion sensitivity; it does not
claim that the fake implements all CLI orchestration. End-to-end implementation
results are recorded separately, and no fake/live replay equivalence is claimed.
