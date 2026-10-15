# Privacy amplification plan

This program implements privacy amplification for the BB84 quantum voting simulator.
Voters and election auditors gain information-theoretic security against eavesdropping.
The rule enforced is that Eve mutual information on the final key is under 2^-16.
The program ships across PR-01, PR-02, PR-03, and PR-04 in order.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `pstack/skills/poteto-mode/playbooks/autopilot-stack.md`. The operator reviews the linear stack and merges each PR bottom-up. PR-04 is the operator item that stops at merge-ready for visual review.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on the operator explicit go.
- [ ] Read these from trunk at program start. Re-read them at every tick.
  - [ ] `git show origin/main:pstack/skills/poteto-mode/playbooks/autopilot-stack.md`
  - [ ] `git show origin/main:pstack/skills/swarm/SKILL.md`
  - [ ] `git show origin/main:pstack/skills/control-ui/SKILL.md`
  - [ ] `git show origin/main:pstack/skills/poteto-mode/playbooks/opening-a-pr.md`
  - [ ] `git show origin/main:pstack/skills/technical-writing/SKILL.md`
- [ ] On the operator go, arm the audit tick as `/loop 1h` with the tick prompt below. Never leave the cadence to memory.
- [ ] Use this tick prompt, verbatim. "Re-read the execution playbook from trunk. Audit the operation against it and fix drift in this tick. Probe every active lane and judge progress by side effects only. Stand down a stuck lane and dispatch its replacement now. Then post a short status message to the operator in chat only when the audit found a tracked change that no earlier status message reported, such as a PR opened, a code-ready head, a round launched or closed, a verdict, a merge, a stuck agent and the action taken, a blocker added or cleared, or a decision only the operator can make. Name every such change and nothing else. Do not repeat a table, the merged list, or an unchanged blocker. If the audit found none, end the turn with no reply text. Either way, log this tick row in your decision trail. The row names the items reported, or none."
- [ ] On the operator hold or stand-down, send every owner a zero-writes order at once.

### Spawn owners

- [ ] Spawn one owner per PR with the full lifecycle the execution playbook names.
- [ ] Follow this dependency graph. Start dependent work only after its parent merges, or base it on the parent branch when the execution playbook stacks.
  - [ ] PR-01 is independent and first. PR-01 branches from `main`.
  - [ ] PR-02 after PR-01.
  - [ ] PR-03 after PR-02.
  - [ ] PR-04 after PR-03.
- [ ] Hold the file boundaries. PR-01 touches only `backend/src/modules/privacy_amplification.py` and `backend/src/evaluation/test_privacy_amplification.py`.
- [ ] Hold the file boundaries. PR-02 touches only `backend/src/modules/models.py`, `backend/src/modules/service.py`, and `backend/src/modules/router.py`.
- [ ] Hold the file boundaries. PR-03 touches only `backend/src/evaluation/test_spec.py` and `backend/src/evaluation/generate_test_spec_report.py`.
- [ ] Hold the file boundaries. PR-04 touches only `Front_end/src/types/qkd.ts`, `Front_end/src/services/`, and `Front_end/src/pages/`.
- [ ] Hold the review gate. PR-04 changes an interaction. It waits for the operator review in chat with screenshots and a video before merge.

### PR mechanics, for every PR

- [ ] Resolve the forge once. Default to `gh`; if `command -v origin` succeeds and Origin can resolve the repository, use `origin pr` for every PR operation. Record any fallback to `gh`. Never require `gt`.
- [ ] Open the PR ready, never draft, per **Opening a PR**. Use the run built-in PR tool when it has one, else `origin pr create --status open --base <base-branch>` or `gh pr create --base <base-branch>` according to the resolved forge. A stack child targets its parent branch.
- [ ] Run the repo lint and typecheck once before the PR-facing push. Push with hooks on.
- [ ] Run `/deslop` before each commit and `/no-comments` before review.
- [ ] Triage every Bugbot and security-reviewer comment per `../references/bugbot-triage.md`.
- [ ] Rebase onto current trunk before the code-ready report and babysit. Keep that merge base in fix rounds. Rebase again only at merge prep, on a `git merge-tree` conflict with trunk, or on a CI failure that comes from a change on trunk.

### Verdict and merge, for every PR

- [ ] At the code-ready head SHA and at each later push that changes the patch, run the swarm per `pstack/skills/swarm/SKILL.md`. One gates lane. The ten live lanes from the PR **Verify, live** block. The perf lane from its **Verify, perf** block. Two or more audit lanes, each with its own focus, that read the diff and the receipts and distrust the PR body. The root audits the receipts in the merge-ready report before the verdict.
- [ ] Clean only when every lane is `PASS`. Findings go back to the owner, including a defect that a lane filed as a note. A new head gets a fresh swarm and a fresh verdict, except for results that stay valid under the patch-id rule in `playbooks/shipping.md`.
- [ ] Append the verified PR to the linear base-branch stack per `playbooks/autopilot-stack.md`. The operator lands each PR bottom-up.

### Boot recipe, for every live lane

Each live lane runs on its own cloud VM at the PR head. Drive through `control-ui` or `control-cli` from `cursor-team-kit`.

- [ ] `git fetch origin <head-branch> && git checkout <head SHA>`.
- [ ] Start the FastAPI backend on port 8000 and the Vite frontend on port 5173. Wait for `http://localhost:8000/docs` to return HTTP 200.
- [ ] Deliver input only through the control skill commands. Read logs from `backend.log` and inspect HTTP payloads.
- [ ] Save every screenshot to `/tmp/swarm-<pr-id>/worker-<n>/<slug>.png` and return the paths with the report.

## Build Toeplitz universal hash family and entropy bounds (PR-01)

**Depends on.** None.

**Files.**

- [ ] Create `backend/src/modules/privacy_amplification.py`.
- [ ] Create `backend/src/evaluation/test_privacy_amplification.py`.

**Build.**

- [ ] Implement `toeplitz_hash` in `backend/src/modules/privacy_amplification.py` using GF(2) matrix-vector multiplication.
- [ ] Implement `estimate_eve_information` in `backend/src/modules/privacy_amplification.py` calculating Renyi entropy bound from QBER.
- [ ] Implement `calculate_amplified_key_length` in `backend/src/modules/privacy_amplification.py` deriving output length for security parameter `s = 16`.
- [ ] Implement `generate_toeplitz_seed` in `backend/src/modules/privacy_amplification.py` producing random bits of length `n + m - 1`.

**You see.**

- [ ] Running `python backend/src/evaluation/test_privacy_amplification.py` outputs `[PRIVACY-AMP] All 8 tests passed.`

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `backend/src/evaluation/test_privacy_amplification.py` gains unit tests for Toeplitz hash correctness, seed bounds, and Eve entropy elimination. Run `python backend/src/evaluation/test_privacy_amplification.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `grok-4.7-xhigh-fast` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run test suite at trunk and head. If trunk lacks the feature, record that and gate standalone matrix compression. Save `live-pr01-lane1-regression.png`. Pass when exit code is 0.
- [ ] Lane 2. Single bit flip in input key flips approximately half of output bits. Save `live-pr01-lane2-avalanche.png`. Pass when difference ratio is between 0.40 and 0.60.
- [ ] Lane 3. Seed length validation rejects seeds shorter than required formula. Save `live-pr01-lane3-seed-short.png`. Pass when ValueError is raised.
- [ ] Lane 4. Alice and Bob compute identical amplified keys from identical reconciled keys and seed. Save `live-pr01-lane4-alice-bob-match.png`. Pass when Alice key matches Bob key.
- [ ] Lane 5. Zero QBER compresses key by security parameter length. Save `live-pr01-lane5-zero-qber.png`. Pass when output length equals input length minus 16.
- [ ] Lane 6. Sample QBER of 0.10 compresses key by more than 30 percent. Save `live-pr01-lane6-high-qber.png`. Pass when output length is under 0.70 times input length.
- [ ] Lane 7. QBER exceeding error threshold returns zero length key. Save `live-pr01-lane7-abort-bound.png`. Pass when output length is 0.
- [ ] Lane 8. Monobit statistical check on 1000 generated hashes verifies bit balance. Save `live-pr01-lane8-monobit.png`. Pass when fraction of ones is between 0.48 and 0.52.
- [ ] Lane 9. Requesting output length larger than input length is rejected. Save `live-pr01-lane9-expansion-reject.png`. Pass when ValueError is raised.
- [ ] Lane 10. Matrix operations on 2048 bit keys run without memory exhaustion. Save `live-pr01-lane10-large-key.png`. Pass when execution finishes without error.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Execution latency for 128 bit key compression to 64 bit key on CPU across 1000 iterations.
- [ ] Probe. `python -c "import time, modules.privacy_amplification as pa; t0=time.perf_counter(); [pa.toeplitz_hash('1'*128, '1'*191, 64) for _ in range(1000)]; print('Total ms', (time.perf_counter()-t0)*1000)"`.
- [ ] Baseline. Record standalone loop baseline of 45.0 ms.
- [ ] Rule. Head execution time for 1000 iterations must remain under 80.0 ms.

**Review gate.** None. PR-01 is not review-gated.

**Merge.**

- [ ] Root clean verdict at the exact head SHA.
- [ ] Bugbot triage done.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] Root appends PR to the base-branch stack for operator landing.

## Integrate privacy amplification into backend service and schema (PR-02)

**Depends on.** PR-01.

**Files.**

- [ ] Edit `backend/src/modules/models.py`.
- [ ] Edit `backend/src/modules/service.py`.
- [ ] Edit `backend/src/modules/router.py`.

**Build.**

- [ ] Add `privacy_amplification_enabled` field to `GenerateKeyInput` in `backend/src/modules/models.py`.
- [ ] Add `pa_seed`, `eve_info_bound`, and `pa_compression_ratio` to `GenerateKeyRespond` and `VotingSession` in `backend/src/modules/models.py`.
- [ ] Update `create_qkd_key` in `backend/src/modules/service.py` to compress reconciled keys with `toeplitz_hash`.
- [ ] Update `calculate_key_length` in `backend/src/modules/service.py` to account for privacy amplification compression overhead.

**You see.**

- [ ] Calling `POST /vote/generate-key` returns JSON containing `paSeed`, `eveInfoBound`, and `paCompressionRatio`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `backend/src/evaluation/test_simulation.py` gains tests for `create_qkd_key` with privacy amplification active and inactive. Run `python backend/src/evaluation/test_simulation.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `grok-4.7-xhigh-fast` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run key generation with PA disabled at trunk and head. If trunk lacks the feature, record that and gate key generation. Save `live-pr02-lane1-regression.png`. Pass when response status is 200.
- [ ] Lane 2. Key generation with PA enabled returns non-empty seed string. Save `live-pr02-lane2-pa-enabled.png`. Pass when seed length is greater than 30.
- [ ] Lane 3. Stored voting session in database contains compression ratio field. Save `live-pr02-lane3-db-record.png`. Pass when record contains pa_compression_ratio.
- [ ] Lane 4. Aborted session sets generated key to empty string and Eve bound to 0.0. Save `live-pr02-lane4-aborted-session.png`. Pass when keyGenerated is empty.
- [ ] Lane 5. Ballot cast with amplified key decrypts accurately on server. Save `live-pr02-lane5-ballot-decrypt.png`. Pass when decrypted vote matches ballot.
- [ ] Lane 6. Disabling PA returns raw reconciled secret key without hash compression. Save `live-pr02-lane6-pa-disabled.png`. Pass when keyGenerated matches raw key.
- [ ] Lane 7. Quantum audit log endpoint includes PA telemetry fields. Save `live-pr02-lane7-audit-log.png`. Pass when log items include pa_seed.
- [ ] Lane 8. Requested target key length of 24 bits produces amplified key of exactly 24 bits. Save `live-pr02-lane8-exact-length.png`. Pass when length of keyGenerated is 24.
- [ ] Lane 9. Hardware simulation with realistic noise applies PA without error. Save `live-pr02-lane9-quantum-noise.png`. Pass when session status is KEY_GENERATED.
- [ ] Lane 10. Successive key generation calls produce unique random seeds. Save `live-pr02-lane10-unique-seeds.png`. Pass when seed strings differ.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. HTTP latency for `POST /vote/generate-key` with 40 qubits and privacy amplification enabled.
- [ ] Probe. `python -c "import requests, time; t0=time.perf_counter(); r=requests.post('http://localhost:8000/vote/generate-key', json={'voterId':'v1','electionCode':'TEST','qubitPerSession':40,'targetKeyLength':24,'privacyAmplificationEnabled':True}); print(r.status_code, (time.perf_counter()-t0)*1000)"`.
- [ ] Baseline. Record trunk endpoint latency baseline of 185.0 ms.
- [ ] Rule. Head endpoint latency must remain under 230.0 ms.

**Review gate.** None. PR-02 is not review-gated.

**Merge.**

- [ ] Root clean verdict at the exact head SHA.
- [ ] Bugbot triage done.
- [ ] Rebased onto parent branch with patch-id unchanged.
- [ ] Root appends PR to the base-branch stack for operator landing.

## Expand test specification with privacy amplification and randomness suites (PR-03)

**Depends on.** PR-02.

**Files.**

- [ ] Edit `backend/src/evaluation/test_spec.py`.
- [ ] Edit `backend/src/evaluation/generate_test_spec_report.py`.

**Build.**

- [ ] Add Test Suite 5 `test_ts5_privacy_amplification_entropy_reduction` to `backend/src/evaluation/test_spec.py`.
- [ ] Add Test Suite 5 `test_ts5_toeplitz_uniformity` to `backend/src/evaluation/test_spec.py`.
- [ ] Add figure generator for `report_fig7_privacy_amplification_compression.png` in `backend/src/evaluation/generate_test_spec_report.py`.
- [ ] Add figure generator for `report_fig8_eve_mutual_information.png` in `backend/src/evaluation/generate_test_spec_report.py`.

**You see.**

- [ ] Running `python backend/src/evaluation/test_spec.py` logs `[TEST-SPEC] Suite 5 passed: 100 trials, 0 security failures.`

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `backend/src/evaluation/test_spec.py` gains Test Suite 5. Run `python backend/src/evaluation/test_spec.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `grok-4.7-xhigh-fast` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run Test Suites 1 through 4 at trunk and head. If trunk lacks the feature, record that and gate test execution. Save `live-pr03-lane1-regression.png`. Pass when all existing 17 test cases pass.
- [ ] Lane 2. Test Suite 5 TC01 verifies key uniformity across 500 amplified keys. Save `live-pr03-lane2-tc01-uniformity.png`. Pass when p-value of runs test exceeds 0.01.
- [ ] Lane 3. Test Suite 5 TC02 verifies Eve mutual information bound drops below 0.0001 bits. Save `live-pr03-lane3-tc02-eve-bound.png`. Pass when maximum Eve bound is under 2^-16.
- [ ] Lane 4. Test Suite 5 TC03 verifies that key shortfall rate with delta = 2.0 is under 1 percent. Save `live-pr03-lane4-tc03-delta-margin.png`. Pass when success rate is at least 99 percent.
- [ ] Lane 5. Report generator creates figure for privacy amplification compression. Save `live-pr03-lane5-fig7.png`. Pass when file exists and size is over 50 KB.
- [ ] Lane 6. Report generator creates figure for Eve mutual information reduction. Save `live-pr03-lane6-fig8.png`. Pass when file exists and size is over 50 KB.
- [ ] Lane 7. Intercept-resend trial confirms Eve guesses amplified bits at 50 percent rate. Save `live-pr03-lane7-eve-guess.png`. Pass when Eve guess accuracy is between 48 and 52 percent.
- [ ] Lane 8. Multi-session concatenation handles amplified key chunks correctly. Save `live-pr03-lane8-multi-session.png`. Pass when concatenated key reaches target key length.
- [ ] Lane 9. Zero-noise trial verifies that PA preserves identical keys between Alice and Bob. Save `live-pr03-lane9-zero-noise.png`. Pass when Alice key matches Bob key across all trials.
- [ ] Lane 10. Automated report execution script completes with exit code 0. Save `live-pr03-lane10-report-run.png`. Pass when script exits with code 0.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Total execution runtime of test specification suite.
- [ ] Probe. `python -c "import time, subprocess; t0=time.perf_counter(); subprocess.run(['python', 'backend/src/evaluation/test_spec.py'], check=True); print('Seconds', time.perf_counter()-t0)"`.
- [ ] Baseline. Record trunk test execution time of 14.2 seconds.
- [ ] Rule. Head test execution time must remain under 22.0 seconds.

**Review gate.** None. PR-03 is not review-gated.

**Merge.**

- [ ] Root clean verdict at the exact head SHA.
- [ ] Bugbot triage done.
- [ ] Rebased onto parent branch with patch-id unchanged.
- [ ] Root appends PR to the base-branch stack for operator landing.

## Expose privacy amplification controls and stage visualization in user interface (PR-04)

**Depends on.** PR-03.

**Files.**

- [ ] Edit `Front_end/src/types/qkd.ts`.
- [ ] Edit `Front_end/src/services/real-api.ts`.
- [ ] Edit `Front_end/src/services/mock-api.ts`.
- [ ] Edit `Front_end/src/pages/ConfigurePage.tsx`.
- [ ] Edit `Front_end/src/pages/KeyGenerationPage.tsx`.
- [ ] Edit `Front_end/src/pages/KeyGenerationPage.module.css`.

**Build.**

- [ ] Add `privacyAmplificationEnabled`, `paSeed`, and `paCompressionRatio` to `Front_end/src/types/qkd.ts`.
- [ ] Add toggle switch for Privacy Amplification in `Front_end/src/pages/ConfigurePage.tsx`.
- [ ] Update qubit sizing recommendation text in `Front_end/src/pages/ConfigurePage.tsx`.
- [ ] Add Stage 4 card for Privacy Amplification in `Front_end/src/pages/KeyGenerationPage.tsx`.
- [ ] Add matrix seed display and compression badge styles in `Front_end/src/pages/KeyGenerationPage.module.css`.
- [ ] Update `Front_end/src/services/mock-api.ts` to compute simulated Toeplitz hash for offline demo.

**You see.**

- [ ] Key Generation page displays Stage 4 Privacy Amplification card with Toeplitz matrix seed and compression statistics.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Frontend unit test suite validates configuration toggle and stage card rendering. Run `npm test -- --watchAll=false` in `Front_end`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `grok-4.7-xhigh-fast` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run voting flow end to end at trunk and head with default settings. If trunk lacks the feature, record that and gate voting flow. Save `live-pr04-lane1-regression.png`. Pass when confirmation screen is reached.
- [ ] Lane 2. Toggle Privacy Amplification switch in Configure page. Save `live-pr04-lane2-config-toggle.png`. Pass when switch toggles to off state.
- [ ] Lane 3. Sizing recommendation card updates minimum qubit count when PA is active. Save `live-pr04-lane3-sizing-warning.png`. Pass when recommendation displays minimum 96 qubits for 24-bit key.
- [ ] Lane 4. Key generation page renders Stage 4 card after reconciliation completes. Save `live-pr04-lane4-stage4-card.png`. Pass when stage card element is visible.
- [ ] Lane 5. Toeplitz seed string renders in monospace element with copy button. Save `live-pr04-lane5-seed-display.png`. Pass when seed container is visible.
- [ ] Lane 6. Compression ratio badge displays percentage reduction value. Save `live-pr04-lane6-ratio-badge.png`. Pass when badge text contains percentage symbol.
- [ ] Lane 7. Eve information bound card displays numerical upper bound. Save `live-pr04-lane7-eve-bound-card.png`. Pass when bound metric element is visible.
- [ ] Lane 8. Mock mode runs simulated privacy amplification without backend connection. Save `live-pr04-lane8-mock-mode.png`. Pass when mock key generation finishes successfully.
- [ ] Lane 9. Mobile viewport 375px renders Stage 4 card without horizontal scrolling. Save `live-pr04-lane9-mobile-layout.png`. Pass when scrollWidth equals clientWidth.
- [ ] Lane 10. Proceeding to Cast Vote page uses amplified key for OTP encryption. Save `live-pr04-lane10-otp-cast.png`. Pass when Cast Vote page loads with amplified key.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Frontend production bundle size of compiled assets.
- [ ] Probe. Run `npm run build` in `Front_end` and check output bundle size.
- [ ] Baseline. Record trunk production bundle size of 285400 bytes.
- [ ] Rule. Head production bundle size must remain under 310000 bytes.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane 10 screenshot files into `docs/media/pr-04-review-screen.png`.
- [ ] Record a 30 to 60 second video of the UI interaction on a lane VM. Save it as `docs/media/pr-04-review.mp4`.
- [ ] Post the screenshots and the video in chat. Stop at merge-ready. Wait for the operator to review.

**Merge.**

- [ ] Root clean verdict at the exact head SHA.
- [ ] Bugbot triage done.
- [ ] Rebased onto parent branch with patch-id unchanged.
- [ ] Root appends PR to the base-branch stack for operator landing.

## Close the program

- [ ] Every box above is checked with its evidence.
- [ ] Reply to the operator with the report the execution playbook names.

## Appendix A. Prototype evidence

Toeplitz universal hashing was prototyped in Python using NumPy bitwise operations.
The prototype confirmed that a random public seed of length `n + m - 1` defines an `m x n` Toeplitz matrix over GF(2).
Input raw key of 24 bits was compressed to 16 bits with seed length 39 bits.
Execution time for 1000 compressions was 42 ms on standard CPU.
Avalanche effect confirmed that single bit flips in the input key change approximately 50 percent of output bits.
Eve mutual information bound confirmed exponential decay with security parameter `s`.

## Appendix B. Alternatives rejected

Standard cryptographic hash functions such as SHA-256 and Blake3 were rejected.
They offer computational security rather than information-theoretic security.
BB84 QKD requires information-theoretic security via 2-universal hash families.
Linear Feedback Shift Register hashing was rejected because Toeplitz matrix formulation is more transparent for educational presentation.
Pre-shared hash seeds were rejected because BB84 public channel model requires public seed transmission after reconciliation.

## Appendix C. Risks

High channel error or active eavesdropping reduces available raw bits below target key length after compression.
PR-02 mitigates this risk through multi-session concatenation and $(4 + \delta)$ transmission sizing checks.
Seed length validation errors could abort session if input length is miscalculated.
PR-01 guards against this with strict boundary assertion.
Displaying large matrix visualizations could clutter the user interface.
PR-04 mitigates this with condensed matrix previews and expandable inspection cards.

## Appendix D. Links and reading list

Read `CONTEXT.md` for project terminology and actor definitions.
Read `TODO.md` Phase 5 for roadmap alignment.
Read `TEST_SPEC.md` for test suite specifications.
Read Bennett, Brassard, Crepeau, and Maurer (1995), Generalized Privacy Amplification.
Read Renner (2005), Security of Quantum Key Distribution.
Apply `pstack/skills/technical-writing/SKILL.md` and `pstack/skills/unslop/SKILL.md` before edits.
