# Kogen conformance suite v1.3-draft

> **Archived.** This suite checked the Rust, Go and TypeScript builds of Kogen against [kogen-spec](https://github.com/KogenAI/kogen-spec) in October 2026. Rust was chosen, and the suite now lives with the Rust implementation. More at [kogen.dev](https://kogen.dev).
>
> The comparison: [kogen-spec](https://github.com/KogenAI/kogen-spec) · [kogen-conformance](https://github.com/KogenAI/kogen-conformance) · [kogen-rs](https://github.com/KogenAI/kogen-rs) · [kogen-go](https://github.com/KogenAI/kogen-go) · [kogen-ts](https://github.com/KogenAI/kogen-ts)

Kogen is a command-line coding system that shapes requests into reviewed Intents and acceptance tests, builds changes in isolated workspaces, and lands verified changes. This suite checks its CLI behavior, persistent formats and Git state, provider protocol, recovery, and process custody.

The default profile composition targets the experimental Kogen **v1.3-draft** specification at [kogen-spec commit `2e6667eae0d626a5b894588aa465bab35b999928`](https://github.com/KogenAI/kogen-spec/commit/2e6667eae0d626a5b894588aa465bab35b999928). Passing this suite is not a frozen v1.3 release certification. It combines the historical v1.1 corpus with the v1.2 and v1.3 profile overlays. See the [v1.3 report](REPORT-v1.3.md), [case-to-clause expectations](expectations/v1.3.json), and [observation boundaries](data/v1.3/RECEIPTS.md). Implementation cases drive a `kogen` executable through its command line and check exit codes, stdout and stderr, files, Git refs, the run journal and fake-provider requests. Offline measurement cases use synthetic fixtures. The suite is language-neutral and can compare implementations on equal terms.

The publication report distinguishes the earlier Rust captures from the fresh gate against the current spec root. The CLI case corpus still measures the rules its assertions name; the vendored Quint contracts cover additional state transitions. Passing this experimental suite is not a frozen v1.3 release certification.

- **Runner:** Python 3 standard library only (3.9+), plus `git`, `sh` and `make`. Nothing is installed.
- **Cases:** The historical v1.1 profile has 244 cases. The v1.2 overlay adds 137 cases and supersedes 139 earlier assertions; v1.3 adds 49 cases and supersedes 13 more. The v1.3 effective suite has 278 cases and 619 instances.
- **Fake provider:** `kogen_conformance/fake_server.py`, which implements spec §4.8: scripted Responses SSE plus fake OAuth.
- **Normative data:** the original v1.1 data corpus remains frozen. The current overlay uses `data/v1.2/help/`, whose two queue pages now carry the v1.3 priority wording. Golden pages and other normative inputs come from these files, never from an implementation. The v1.3 loader applies [versioned projections](kogen_conformance/v13.py) to inherited schema, role-marker, landing-line, exact-base and recovery fixture assumptions; historical profile selections retain their original contracts.

## Contents
- [Running it](#running-it)
- [Profiles](#profiles)
- [How an implementer uses it](#how-an-implementer-uses-it)
- [Results](#results)
- [How a case is built](#how-a-case-is-built)
- [The fake provider](#the-fake-provider)
- [Readings settled in v1.1](#readings-settled-in-v11)
- [Historical implementation observations](#historical-implementation-observations)
- [Versioned v1.2 delta](#versioned-v12-delta)
- [Versioned v1.3 delta](#versioned-v13-delta)
- [Why a custom runner rather than pytest](#why-a-custom-runner-rather-than-pytest)
- [Freeze rule](#freeze-rule)

## Running it
```sh
bin/kogen-conformance run --kogen /path/to/kogen                      # every profile
# Historical v1.1 assertions only; the v1.2/v1.3 overlays are not selected.
bin/kogen-conformance run --kogen /path/to/kogen --profile cli,format
bin/kogen-conformance run --kogen /path/to/kogen --case 'build-0*,ladder-12' -v
bin/kogen-conformance list --profile build                            # ids, titles, unimplemented markers
bin/kogen-conformance summary results.jsonl --expectations reference/elixir-97ef563d.json
bin/kogen-conformance fake --script steps.jsonl --port 8765           # the fake provider on its own
```

| Option | Meaning |
|---|---|
| `--kogen PATH` | The implementation's executable (a wrapper script is fine) |
| `--profile a,b` / `--case glob,…` | Select profiles or case ids |
| `--jobs N` | Parallel cases (default: half the CPUs). Cases marked `serial` run afterwards, one at a time. |
| `--workdir DIR` | Where case directories go (default: a new temp dir). Passing cases are deleted unless `--keep` is given. |
| `--out FILE` | JSON Lines results (default `<workdir>/results.jsonl`) |
| `--time-scale X` | `KOGEN_TIME_SCALE` (default 0.01) |
| `--skip-needs login,elixir` | Skip cases that need these. Since v1.1 the runner sets `KOGEN_CREDENTIAL_STORE=file`, so `login` cases never touch a keychain in an implementation that has the seam. |
| `--env NAME=VALUE` | Extra environment for the implementation, such as a runtime path |
| `--expectations FILE` | Known-failure classification, joined into the summary |
| `-v` | Print failure details as cases finish |

The exit status is 0 only when no case failed or errored.

## Profiles
The table below gives the historical v1.1 base-profile counts.

| Profile | §C.4 | Implemented | Unimplemented | Needs |
|---|---:|---:|---:|---|
| `cli` | 30 | 30 | 0 | — (fake for 25, 27, 29, 30) |
| `state` | 30 | 30 | 0 | git, kt (fake for 11, 12, 15, 18, 23, 26, 27) |
| `approval` | 24 | 24 | 0 | git, kt |
| `shape` | 26 | 26 | 0 | fake, kt |
| `build` | 44 | 44 | 0 | fake, kt |
| `ladder` | 36 | 36 | 0 | fake, kt |
| `provider` | 26 | 26 | 0 | fake; login cases need the OAuth flow on port 1455 |
| `custody` | 10 | 10 | 0 | kt, fake |
| `format` | 12 | 12 | 0 | — (fake for 7, 10, 12; login for 11) |
| `exunit` | 6 | 6 | 0 | Elixir on PATH |
| **Total** | **244** | **244** | **0** | |

The 244-case v1.1 profile remains selectable. To run the v1.2 overlay, include `v1.2` with the profiles you want, for example:

```sh
bin/kogen-conformance run --kogen /path/to/kogen --profile cli,state,approval,shape,build,ladder,provider,custody,format,v1.2
```

The overlay omits the 139 listed v1.1 case IDs and runs their replacements from `cases/v1.2/`; all other selected cases stay in the run. Selecting only historical profiles such as `--profile cli,state` runs their v1.1 assertions. The `v1.2` profile contains 137 cases: 6 delta cases and 131 replacements.

Each unimplemented case is still present as a file with `"status": "unimplemented"` and a `reason`; `list` shows them.

Conformance on a host (§C.1) means every case in `cli state approval shape build ladder provider custody format` passes, with no unmatched fake-provider request. `format` is reported separately so that behaviour work is weighted on its own. `exunit` is required only for the Elixir tier.

## How an implementer uses it
1. **Build the seams first** (spec §4.1, §5.3).
   - `KOGEN_PROVIDER_URL` replaces the responses URL in both owned and injected mode.
   - `KOGEN_AUTH_URL` replaces `https://auth.openai.com` for discovery, authorize, token, JWKS and revoke. The issuer check still expects `https://auth.openai.com`; the fake's discovery document returns that issuer.
   - `KOGEN_TIME_SCALE` multiplies every `scaled: true` constant.
   - `KOGEN_SANDBOX=unavailable`.
   - The `command` acceptance adapter (§2.4.3). Without it, no `kt` case can start.
2. **Put the marker sentences verbatim in the system prompts** (§4.8.2). The fake identifies roles by them alone.
3. **Run `cli` and `format`.** They need no live provider; some cases exercise the local fake-provider and OAuth seams.
4. **Run `state` and `approval`.** They need git and the `kt` fixture.
5. **Run `build`, `ladder`, `shape` and `provider`.** They need the fake provider.
6. **Run `custody`.** It needs real process groups and signals.
7. **Read failures with `-v`**, or from `results.jsonl`. Each failure names the step, the assertion and what was observed. A failing case keeps its directory (`workdirs` in the JSONL), with HOME, the origin, the checkout and the state root, so you can rerun `kogen` there by hand.
8. **Do not edit cases.** If a case looks wrong, the fix starts in the spec (§C.2). Historical v1.1 profile cases remain in `cases/`; v1.2 and v1.3 corrections live in their versioned directories.

### What the runner gives every case (§C.3)
| Item | Value |
|---|---|
| Directories | `HOME=<case>/home`, `TMPDIR=<case>/tmp`, a bare origin `<case>/origin.git` and a clone `<case>/checkout`. Some cases use the topologies `single` (the checkout is the origin) or `nonbare`. All paths are canonical (symlinks resolved). |
| `PATH` | `<case>/stubs:` followed by the runner's `PATH` |
| Stubs | `mise` (`env --json` prints `{}`; `exec --` passes the command through); `open` and `xdg-open`, which follow the authorize URL to the loopback from a detached session; argv-size loggers for `sh` and `git` in custody-8 |
| Git | `GIT_CONFIG_GLOBAL=<case>/gitconfig` with identity `Kogen Test <test@kogen.invalid>`, no signing and `init.defaultBranch=main`; `GIT_CONFIG_NOSYSTEM=1` |
| Seams | `KOGEN_PROVIDER_URL=http://127.0.0.1:<port>/v1/responses`, `KOGEN_AUTH_URL=http://127.0.0.1:<port>` and `KOGEN_TIME_SCALE=0.01`. `KOGEN_SANDBOX=unavailable` only where a case asks for it. |
| Credentials | Injected mode by default: `KOGEN_AUTH_PATH=<case>/auth.json`, a JWT with `exp` one day ahead and account `acct_kogen_test`. Owned-mode cases log in through the fake OAuth flow. |
| Other variables | `LANG` (`en_US.UTF-8` on macOS, `C.UTF-8` elsewhere), `TZ=UTC`, `USER`, `LOGNAME`, `SHELL=/bin/sh`. Nothing else from the runner's environment is passed. |
| Fixtures | `kt` (Appendix A; `fixtures/kt` plus `fixtures/kt.project.json`, emitted as strict YAML), `exunit-hello`, `empty`, `none` (no repository) |

Every case asserts the §1.1 stderr rule unless it says otherwise: stderr may hold only shaper progress, the deprecated-`account:` line, `land: warning:` lines and the sandbox warning. stdout must be UTF-8, end with `\n` and contain no `\r` or trailing spaces. Exact wording of shaper progress is checked only in `format`.

## Results
`results.jsonl` holds a `meta` line (suite version, kogen path, platform, git version, time scale) followed by one line per case:
```json
{"id":"build-02","profile":"build","title":"R1 happy path…","spec":["§3.4","§2.5.4"],"file":"cases/build/build-02-….json",
 "status":"pass|fail|error|skip|unimplemented","instances":{"total":1,"passed":1,"skipped":0,"errors":0},
 "failures":[{"instance":"2:failed","messages":["step 4 (run kogen intent remove greet): …"]}],
 "hints":["no provider request reached the fake server (KOGEN_PROVIDER_URL seam missing?)"],
 "duration_ms":2310,"workdirs":["<workdir>/build-02"],"reason":"(skip/unimplemented only)"}
```
- **Statuses.**
  - `fail` means the implementation broke an assertion.
  - `error` means the harness could not run the case, for example a placeholder that could not be resolved because a run never happened.
  - `skip` means the case needs something that was skipped or is missing (`--skip-needs`, Elixir, a platform).
- **Summary.** The run ends with a per-profile table (cases, implemented, pass, fail, error, skip, unimplemented, instances).
- **Classification.** With `--expectations`, failing cases are grouped by their classification (`R-gap`, `ref-bug`, `spec`), which turns a run into a gap report.
- **No retries.** A failing case is never retried (§C.1).

## How a case is built
A case is one JSON file:
```json
{
 "id": "build-02", "profile": "build", "title": "…", "spec": ["§3.4"],
 "fixture": "kt",
 "project": {"build": {"ladder": {"max_rungs": 1}}},
 "fake": true,
 "script": [{"include": "r1_happy"}],
 "steps": [
  {"intent": "greet"},
  {"approve": "greet"},
  {"run": ["kogen", "queue", "start"], "expect": {"exit": 0, "stdout_lines": ["building greet", "~landed greet [0-9a-f]{8} \\(Build [0-9a-f]{8}\\)", "queue: done; 1 Build(s), 1 landed, 0 not"]}},
  {"assert": {"events": {"slug": "greet", "subsequence": ["started", "plan", "rung_started", "verification", "commit_result", "landing_prepared", {"event": "finished", "status": "landed"}]},
              "refs": {"refs/kogen/claim": false}}}
 ]
}
```

**Top-level keys.**
- `fixture` and `topology` select the world.
- `project` is deep-merged into the kt `project.yaml`; `project_yaml` replaces it verbatim.
- `fixture_files` adds files to the fixture.
- `env`, `auth` (`injected`, `owned` or `none`), `sandbox_unavailable`, `time_scale`, `fake`, `script`, `allow_remaining`, `allow_unmatched`, `needs`, `serial`, `notes`.
- `rows`, `rows_from` and `rows_zip` expand a case into instances. `{row.x}` substitutes a value and `{*row.x}` splices a list. The v1.2 help corpus uses the `help_pages_v1_2` generator and `data/v1.2/help/`.

**Steps.** The first key names the step:
- **Files and git:** `write` (text, `b64`, template `from`, `crlf`, `mode`, `in`), `remove`, `symlink`, `intent` (installs `cases/_templates/intents/<t>/`, optionally with replacements, and commits it), `commit`, `push`, `origin_commit` (moves the origin's base), `git`, `sh`.
- **The implementation:** `run`, which takes `stdin`, `env`, `cwd`, `background`, `signal: {sig, when}`, `timeout` and `capture`. `approve` is a shorthand for approving with the computed hash.
- **Processes:** `wait`, `signal`, `wait_until` (a file, stdout, a journal event, a fake request count, or an exit), `sleep`.
- **State:** `synthetic_run` writes a §2.8 run dir for status derivation cases. `snapshot` records the checkout state, `capture` records a value into a variable, and `fake` replaces or appends script steps or changes the OAuth configuration.
- **Checks:** `assert`, `eventually` (an `assert` retried until a deadline) and `skip_if`.

**Expectations (`run.expect`).**
- `exit`.
- `stdout` exact; it may be built from parts such as `{"data": "help/kogen.txt"}` or `{"lines": […]}`.
- `stdout_regex`, `stdout_lines` (exact lines, or `~regex` lines), `stdout_starts_lines`, `stdout_contains`, `stdout_json` / `stdout_jsonl` (matchers), `watch_frames`.
- `stderr` exact, `stderr_lines`, `stderr_contains`, `stderr_any`.
- `max_wall_ms`.

**Assertions.**
- `files`: exists, text, regex, contains, json, jsonl, mode, `is_symlink`, entries, `same_as`.
- `glob_count`.
- `refs` / `ref_count`: in the origin by default.
- `git`: a command whose output is checked as text or JSON.
- `events`: on a slug's latest run, with `subsequence`, `contains`, `each`, `absent`, `count`, `first`, `last` and `sequence_equal`.
- `run_json`, `runs_count`.
- `fake_requests`: select by role, turn, step or nth, then a body/header matcher, `input_contains`, `input_regex` or `first_user_text`.
- `fake_request_sequences`: relational checks over ordered fake requests, including raw body bytes, append-only input, cache/session headers and journal identities.
- `fake_request_count`, `fake_remaining`, `fake_oauth`, `fake_oauth_count`.
- `checkout_clean`, `checkout_unchanged`, `argv_max`, `vars`.

**Matchers** are JSON:
- An object matches as a subset; `"$exact": true` forbids extra keys.
- `"~regex"` must match fully.
- Type tokens: `$str`, `$int`, `$bool`, `$null`, `$sha`, `$hex8`, `$hex32`, `$hex64`, `$any`, `$absent`, …
- Combinators: `{"$any_of": […]}`, `{"$contains": […]}`, `{"$subsequence": […]}`, `{"$not": m}`, `{"$ge": n}`, …

**Placeholders.** The runner computes these from the spec's formulas, never from the implementation's output:
- Paths: `{checkout}`, `{origin}`, `{home}`, `{case}`, `{tmp}`.
- `{state_root}`: `~/.kogen/workspaces/<basename≤40>-<sha256(path)[:10]>`.
- Approval hashes `{hash6:slug}`, `{hash8:slug}`, `{hash64:slug}`: SHA-256 of `intent.md` ‖ NUL ‖ the test.
- `{intent_sha:slug}`, `{base_sha}`, `{approval_commit:slug}`, `{approval8:slug}`.
- `{run_id:slug}`, `{id8:slug}`, `{run_dir:slug}`: the latest run, by `started_ms`.
- `{sha256_file:path}`, `{sha256_origin:path}`, `{absent_sha}`, `{var:name}`.

## The fake provider
The fake implements spec §4.8:
- **Endpoints:** `POST …/responses`; inspection at `GET /_fake/requests`, `GET /_fake/remaining`, `POST /_fake/reset`, `POST /_fake/script` and `GET /_fake/oauth`; OAuth at `/.well-known/openid-configuration`, `/api/accounts/authorize` (302 to the callback with the same `state`), `/api/accounts/oauth/token` (verifies PKCE S256), `/jwks` (a 2048-bit RSA key generated per run, signing RS256 id_tokens) and `/revoke`.
- **Roles** come from the §4.8.2 marker sentences.
- **`turn`** is 1 for a fresh conversation (exactly one user message, not counting `additional_tools`) and adds 1 for each later request of the same role whose input extends the previous one.

A script step looks like this:
```json
{"id": "edit",
 "expect": {"role": "builder", "model": "gpt-6-luna", "effort": "max", "tools": ["shell"], "turn": 1,
            "input_contains": ["## Request"], "last_output_contains": "exit 0", "last_user_contains": "…", "fresh": true, "after": ["plan"]},
 "reply": {"calls": [{"name": "shell", "arguments": {"cmd": "printf 'Hello, World!\\n' > lib/greet.txt"}}]},
 "first_byte_ms": 0, "chunk_gap_ms": 0, "drop_after_events": null, "pad_events": 0, "repeat": 1, "side_effect_sh": "…", "side_effect_keepalive": false, "usage": {…}}
```
- **Replies:** `text` (builder progress in v1.2/v1.3; completion requires a `finish` call alone with `{}`; historical v1.1 cases may use text as a done claim), `calls` (call ids `call_<step>_<i>`, arguments serialised as a JSON string), `items`, `sse` (raw frames, `{"raw": …}` or `{"raw_b64": …}`), and `http` (`{status, body, headers}`).
- **Delays** are given in unscaled milliseconds and multiplied by `KOGEN_TIME_SCALE` (for example, 1,000 ms at 0.01 becomes 10 ms).
- **`side_effect_sh`** runs before the reply. It sees `ORIGIN`, `CHECKOUT`, `CASE_DIR` and `STATE_ROOT`.
- **`side_effect_keepalive`** opts into SSE comment bytes while that side effect runs. The actual response still follows completion; provider first-byte, idle and total deadlines remain active.
- **v1.3 request matching:** `tools` checks all seven shared schemas; `callable_tools` separately checks exact role permissions (`allowed_tools` or `none`). `system_prompt_contains` checks system/developer instructions across both codecs. Fresh-turn detection skips leading instruction/schema items but later turns must preserve the complete prior input.
- **A successful reply** streams one `response.output_item.done` per item, then `response.completed` (`resp_<n>`, empty `output`, usage). The default usage is input 120, cached 20, output 30, reasoning 10. A scripted `usage: null` omits the usage object; `usage: {}` sends it without counts.
- **Unmatched requests** get HTTP 400 `scripted_mismatch`. A case fails on any unmatched request and, unless it says otherwise, on any unserved step.

## Readings settled in v1.1

The v1.1 suite recorded 30 decisions for points the spec left silent or ambiguous. Product and developer-experience behavior follows the latest recorded product decision; success, speed and cost follow the latest measurement. When neither determines a result, exact strings follow the reference behavior. These rules make each interpretation reproducible and are reflected in the spec and applicable cases.

| # | Point | Settled as | Source | Cases |
|---|---|---|---|---|
| 1 | Credential store isolation | Test seam `KOGEN_CREDENTIAL_STORE=file`: logins are mode 0600 files under `~/.kogen/credentials/`. The runner sets this seam so login cases never access the host keychain. This isolates test credentials from host credentials. | Spec §§4.1, 4.6 | runner, all login cases |
| 2 | Build auditor marker | The test-auditor marker `You are Kogen's acceptance test auditor.` | Reference 80a4dd97 (`Kogen.Runner.Auditor` uses it at build time) | unchanged |
| 3 | Requirement-auditor reply | `{"rows":[{"constraint","maps_to"}]}`, the shape of `ledger.json` | Spec-internal consistency (§2.4.5) | unchanged |
| 4 | Witness adjudication | Tool-less request with the test-auditor marker; `{"items":[{"id","verdict":"TEST-WRONG\|WITNESS-WRONG\|UNDECIDED","citation","reason"}]}` | Consistency with §3.8.2; witness stays pending measurement | unchanged |
| 5 | Fallback shaper marker | The shaper marker; told apart by model and fresh conversation | §3.2.1 | unchanged |
| 6 | `kogen help <words> --help` | `--help` right after `help` is the flag; after a word it is a word (`kogen help: no command 'intent --help'`) | Reference | none added |
| 7 | Queued and Drafts rows | `  <slug>`, no detail | Reference | cli-25 |
| 8 | Stopped-drain counts and article | `<N>` counts the stopped Build; `hit an environment error` | Reference counts; English | build-39/40/41, exunit-02, state-10, provider-19 |
| 9 | `(Build <id8>)` on B0 refusals | Absent: no run exists before B1 | §3.4 | build-41, state-10 (provider-19 keeps it: its run exists) |
| 10 | Skipped-only drain | `queue: nothing to build` | §1.7.4 (nothing was built) | build-42 |
| 11 | `remove_requires_force` lines | `Intent still has a failed Build approval; pass --force to discard the approval and remove its files` (parked, approval ref alike) | Reference | approval-23 |
| 12 | Path forms | `request_unavailable` absolute; `acceptance_check_path_conflict` checkout-relative; `--json` paths absolute | Reference | shape-05, approval-19 |
| 13 | Shaping first message | Gate paths in byte order; request verbatim, then `\n\n` | Reference | unchanged |
| 14 | Missing formatter | Progress line `shaper pass=<n> role=<role> warning formatter_unavailable` (already allowed by §1.1) | §3.2.6 vocabulary | shape-18 |
| 15 | CheckSpec index and line | 1-based `<list>[<i>]`; schema issues have no `line` | Reference | state-02 |
| 16 | YAML sibling messages | Block scalar → "anchors, aliases, tags, and block scalars"; anchor/alias/tag → "anchors, aliases, and tags"; `<v>` the scalar as written, `<text>` the rest of the line | Reference | unchanged (wording is SHOULD) |
| 17 | Intent parse lines | Missing closing `---`: line after the last line; missing key and non-map frontmatter: line 2 | Reference | state-04 |
| 18 | `unsupported_verify_kind` | First word `example` or `check`; any other word is `invalid_verify` | Reference parser | none added |
| 19 | Base-red rows and `symbol` | `symbol` is parsed only for test findings; the row keeps the rest (`greet.txt: TODO found`) | §2.4.4 statement | approval-08 |
| 20 | `acceptance_paths` | Source paths | Reference | state-09 |
| 21 | Empty `chatgpt:` map | `chatgpt: {}` | Strict YAML rule | unchanged |
| 22 | Rung wall in the journal | `rung_started.wall_ms`, unscaled | §2.8 table | unchanged |
| 23 | `model_stage` granularity | One per model request; stages `shape`, `ledger`, `shape_audit`, `plan`, `develop`, `audit` | Reference output records each request | unchanged |
| 24 | Report budget figures | `budget_ms` configured (unscaled); `used_ms`, `paused_ms` measured | §4.1 journal rule | unchanged |
| 25 | `--by` without a git identity | Refused: `intent/approval_identity_unavailable` (exit 2); `--by` records the delegate, while the approval commit uses the caller's Git identity. This keeps approval metadata separate from commit authorship. | Historical ruling (2026-10-05); approver selection in Spec §1.7.2 | none added |
| 26 | Shaping recounts | Ledger and audit run in every pass reaching step 7; `candidate/coverage_gap`; an uncited non-valid verdict is a warning, never a repair | §3.8.2 | unchanged |
| 27 | Dropped stream | `transport` | Reference | provider-17 |
| 28 | Turn budget note | Turn 49 (after 48 turns), N = 12 | Reference | unchanged (already turn 49) |
| 29 | Undetected checkout writes | Confining host: the write fails and the Build lands (exit 0); 70 only when unconfined and detected | §5.3 | custody-06 |
| 30 | Integration repairs | Bounded by the landing allowance alone; a moved base parks only when rebase or re-gate is impossible after repairs | §3.9.2 | build-25/26, ladder-19 already match |

### Other v1.1 changes
- **Provider resilience (decision 2026-10-05):** after **2** consecutive overload responses (overloads only), switch to `gpt-6.1-sol/medium`; allow **4** attempts per request and **2** stage retries, with jittered backoff from half to the full ceiling and the actual delay recorded in `delay_ms`, then stop as `provider/<class>`. The 30-minute outage window does not apply. This bounds retries while retaining a defined fallback path. Cases provider-08/09/12/13/14/15/16/17, ladder-22, ladder-36; `data/constants.json`.
- **Shaper default (decision 2026-10-05):** use `gpt-6.1-sol/high` when no shaper role is configured. An explicit role default keeps shaping independent of the builder model. Cases shape-01/06/12/13/23.
- **provider-21** accepts an upper-case host UUID (the spec does not pin case).

## Historical implementation observations

Earlier implementation captures and their classifications are retained under `reference/` as historical evidence. They are not current v1.3 conformance claims. Environment-specific executable and work-directory values in captured output use portable placeholders.

## Why a custom runner rather than pytest
§C.3 recommends Python 3 with the standard library only, and this suite follows that:
- **Nothing to install.** An implementer on a macOS or Linux host runs `bin/kogen-conformance` with no virtualenv, pip or version pinning, and the oracle cannot drift through a dependency upgrade. pytest and PyYAML are not required.
- **Cases are data, not code.** The freeze rule is about case files. JSON files with a closed step and assertion vocabulary can be reviewed, diffed and frozen without reading Python. They also cannot hide implementation-specific logic in test code.
- **Results are first-class.** The runner writes the JSON Lines and summary formats this README specifies, joins known-failure classifications, keeps failing worlds, never retries, and runs `serial` cases (the fixed 1455 loopback) apart. Expressing all that through pytest plugins would add more machinery than it removes.
- **JSON rather than YAML.** The standard library has no YAML parser, and a strict YAML subset is one of the things under test. The suite emits `project.yaml` through its own small emitter for the §2.6 subset and never parses YAML.

## Versioned v1.2 delta

The v1.2 profile overlays the v1.1 assertions it supersedes. Its cases live in `cases/v1.2/`, and its help goldens live in `data/v1.2/help/`. The profile is language-neutral and invokes only the `kogen` executable. Run it with:

```sh
bin/kogen-conformance run --kogen /path/to/kogen --profile v1.2 -v
```

The fake provider records exact request-body bytes as `body_raw_b64`, so the suite can prove the byte-prefix rule from §4.9.2. The `fake_request_sequences` assertion checks request-to-request identity and journal relations. Scripted missing usage exercises §4.9.5.

| Case | Required observation |
|---|---|
| `v1.2-01-fixed-cli-help-and-grok` | Exact v1.2 help pages/routes; `grok` is accepted by existing provider commands. |
| `v1.2-02-approval-hash-intent-and-test-bytes` | Hash equals exact Intent bytes, NUL, and exact UTF-8 acceptance-source bytes; the approval commit preserves the bytes. |
| `v1.2-03-consecutive-request-byte-prefix` | Turn 2's request input keeps turn 1 as an unchanged prefix. |
| `v1.2-04-cache-key-session-headers` | Build cache key, session header, thread identity and request journal agree. |
| `v1.2-05-missing-usage` | Missing usage counts remain null; unmeasured input does not produce a `cache_hit_rate`. |
| `v1.2-06-crash-after-base-cas` | Recovery after a process exits just after base CAS reports landed, releases its claim and removes the incoming ref. |

These cases cover the fixed help corpus, approval hash bytes, provider input prefixes, cache/session identity, missing-usage semantics and recovery after base CAS.

A rewrite must pass the v1.2 profile in addition to the guaranteed v1.1 slices before claiming v1.2 conformance. The profile does not itself establish the separate live-cache hit-rate target.

## Freeze rule
- Historical v1.1 and v1.2 profiles remain available; the v1.2 and v1.3 profile files identify superseded assertions and their replacements.
- Fixture names use neutral sample data. These editorial substitutions preserve the asserted behavior and do not change case IDs.
- A case found to be ambiguous is fixed in the spec first. The readings section above records the suite's interpretations.

## Versioned v1.3 delta

`VERSION` is 1.3. The default selection applies `profiles/v1.2.json` and
`profiles/v1.3.json`, retaining 229 inherited cases and running 49 v1.3 cases.
Thirteen old active assertions are superseded: the seven demotion cases, the
literal HTTP-body-prefix case, the two old Shape pass/fallback cases, the run
schema, the default report policy and the old valid-config role list. Case IDs
and assertion structures remain stable across the overlays.

```sh
# The whole effective suite, including inherited v1.2 cases:
bin/kogen-conformance run --kogen /path/to/kogen --expectations expectations/v1.3.json
# Only the new/replacement cases:
bin/kogen-conformance run --kogen /path/to/kogen --profile v1.3 --case 'v1.3-*'
# Every new case's passing control and deliberately wrong fake:
python3 -m unittest discover -s tests -v
# Scan the current tree for disclosure patterns; Git history and refs are not scanned:
tools/public_scan.sh
# Regenerate migrated Quint hand goldens:
KOGEN_SPEC=/path/to/kogen-spec quint/v1.3/run.sh
```

Selecting v1.3 activates v1.2 supersessions. Explicit selections of historical
case ids follow the replacement chain. Selecting historical profiles without
v1.2/v1.3 runs their v1.1 assertions. Expectations map **every** case to its
recorded spec clauses and identify active and superseded cases.

Cache cases 25–30 are marked `measurement-boundary`; their passes validate offline
accounting and synthetic request counts. They confer no live release qualification
and no CLI implementation pass. Real git/filesystem recovery fixtures and captured
provider requests stay separate from the Quint model results. Receipt/codec
projection conventions and fault-injection requirements are documented in
[data/v1.3/RECEIPTS.md](data/v1.3/RECEIPTS.md).

## License

This repository is licensed under [Apache-2.0](LICENSE). The license covers the
runner, cases and fixtures, and the copied and adapted specification and Quint
material included here.
