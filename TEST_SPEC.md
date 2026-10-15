# Test Specification: QKD-Secured Online Voting Simulator (BB84 + OTP)

**Project:** 261492 — Super-Secure Communication for Voting System Using Quantum Key Distribution  
**Module Under Test:** QKD Simulator Backend & End-to-End OTP Voting Pipeline  
**Target Endpoints:**
* `POST /vote/generate-key`
* `POST /vote/cast-ballot`
* `GET /vote/election-result`
* `GET /vote/quantum-audit-log`

---

## 1. Overview & Testing Objectives

This specification defines the test suites required to validate the **BB84 Quantum Key Distribution (QKD) Simulator** and **One-Time Pad (OTP)** encryption pipeline. The testing process evaluates four core engineering goals:

1. **Key Sizing & Sifting Efficiency ($\delta$ Safety Margin):** Determine the optimal number of transmitted qubits $(4 + \delta) \times n$ required to reliably generate a final secret key satisfying $|K_{\text{final}}| \ge |M|$.
2. **Eavesdropping Detection & QBER Threshold Calibration:** Verify that the Quantum Bit Error Rate (QBER) threshold (`thresholdPercent = 11%`) accurately separates normal quantum hardware noise from an active Intercept-and-Resend eavesdropper (Eve).
3. **Sample QBER vs. Actual Key QBER Estimation Accuracy:** Validate that the error rate computed from sacrificed sample bits (`testSample`) is an accurate statistical estimator of the hidden error rate in the final secret key (`keyGenerated`).
4. **End-to-End Ballot Correctness & Error Correction:** Confirm that OTP encryption/decryption ($C = M \oplus K$) combined with key reconciliation (`errorCorrectionEnabled`) achieves 100% ballot correctness and preserves uniform ciphertext randomness.

---

## 2. Test Environment & Configuration Schema

### 2.1 Request Payload Schema (`POST /vote/generate-key`)
```json
{
  "voterId": "string (nanoid)",
  "electionCode": "string (nanoid)",
  "isUsingQuantumComputer": true,
  "errorCorrectionEnabled": true,
  "enableEavesdropper": false,
  "qubitPerSession": 40,
  "targetKeyLength": 24
}
```

### 2.2 Response Payload Schema (`VotingSchema`)

```json
{
  "voterId": "string",
  "electionCode": "string",
  "sessionId": "string",
  "keyGenerated": "string (binary)",
  "aliceBit": "string (binary)",
  "aliceBasis": "string (binary/+x)",
  "bobRead": "string (binary)",
  "bobBasis": "string (binary/+x)",
  "testSample": 0,
  "errorFound": 0,
  "qberPercent": 0,
  "thresholdPercent": 11
}
```

---

## 3. Test Suites & Test Cases

### Test Suite 1: Key Sizing & Safety Margin ($\delta$) Optimization

**Objective:** Find the minimum safety margin $\delta$ in $N_{\text{qubits}} = (4 + \delta) \times n$ (or multi-session concatenation count $r$) so that the post-sifting, post-sampling key length satisfies $|K_{\text{final}}| \ge \text{targetKeyLength}$ ($n$).

* **Preconditions:** `enableEavesdropper = false`, `isUsingQuantumComputer = false` (Ideal channel).
* **Plaintext Reference:** `"VT3"` (3 ASCII characters = **24 bits** $\rightarrow n = 24$).
* **Number of Trials:** 100 iterations per test case.

| Test Case ID | `targetKeyLength` ($n$) | Multiplier $(4 + \delta)$ | Total Qubits Sent | Expected Sifted Bits (~50%) | Expected Final Key Bits (~25%) | Pass Criteria |
| --- | --- | --- | --- | --- | --- | --- |
| **TS1-TC01** | 8 bits | $4.0\times$ ($\delta = 0$) | 32 | ~16 bits | ~8 bits | Establish baseline first-pass success rate (~50%–60% due to binomial variance). |
| **TS1-TC02** | 24 bits (`"VT3"`) | $4.0\times$ ($\delta = 0$) | 96 | ~48 bits | ~24 bits | Observe frequency of key-shortfall events ($|K_{\text{final}}| < 24$). |
| **TS1-TC03** | 24 bits (`"VT3"`) | $5.0\times$ ($\delta = 1.0$) | 120 | ~60 bits | ~30 bits | $\ge 90\%$ of single-pass runs yield $|K_{\text{final}}| \ge 24$ bits. |
| **TS1-TC04** | 24 bits (`"VT3"`) | $6.0\times$ ($\delta = 2.0$) | 144 | ~72 bits | ~36 bits | $\ge 99\%$ of single-pass runs yield $|K_{\text{final}}| \ge 24$ bits. |
| **TS1-TC05** | 24 bits (`"VT3"`) | Multi-session (`qubitPerSession = 40`) | $40 \times r$ | ~20 bits / session | ~10 bits / session | System automatically concatenates $r \ge 3$ independent sessions until $|K_{\text{total}}| \ge 24$. |

---

### Test Suite 2: Eavesdropping Detection & QBER Threshold Calibration

**Objective:** Verify that `thresholdPercent = 11%` reliably distinguishes legitimate quantum channel noise from an active Eve performing an Intercept-and-Resend attack.

* **Preconditions:** `targetKeyLength = 24`, `qubitPerSession = 128` (or sufficient to yield $\ge 32$ `testSample` bits).
* **Number of Trials:** 100 iterations per test case.

| Test Case ID | Scenario | `isUsingQuantumComputer` | `enableEavesdropper` | Expected `qberPercent` | Expected System Behavior | Pass Criteria |
| --- | --- | --- | --- | --- | --- | --- |
| **TS2-TC01** | Ideal Channel (No Eve) | `false` | `false` | **0.0%** | Key Accepted (`qberPercent < 11%`) | 100% key acceptance; `errorFound == 0`. |
| **TS2-TC02** | Noisy Quantum Channel (No Eve) | `true` | `false` | **1.0% – 5.0%** | Key Accepted (`qberPercent < 11%`) | False Positive (False Alarm) rate $< 2\%$. |
| **TS2-TC03** | Active Eve (Ideal Channel) | `false` | `true` | **~25.0%** ($\pm 5\%$) | **Key Rejected / Aborted** (`qberPercent >= 11%`) | Detection rate $\ge 98\%$; session flagged as compromised. |
| **TS2-TC04** | Active Eve (Noisy Quantum Channel) | `true` | `true` | **~25.0% – 28.0%** | **Key Rejected / Aborted** (`qberPercent >= 11%`) | Detection rate $\ge 99\%$; no compromised key is passed to OTP. |

---

### Test Suite 3: Sample QBER vs. Actual Key QBER Accuracy

**Objective:** Evaluate how closely the public sample QBER ($\text{QBER}_{\text{sample}}$, computed over `testSample` bits) estimates the hidden QBER in the unrevealed secret key ($\text{QBER}_{\text{key}}$, computed inside the simulator by comparing Alice's and Bob's remaining sifted bits).

* **Formula:**

$$\Delta \text{QBER} = \left| \text{QBER}_{\text{sample}} - \text{QBER}_{\text{key}} \right|$$

* **Preconditions:** Run under both `enableEavesdropper = true` (~25% error rate) and noisy `isUsingQuantumComputer = true` (~3% error rate).

| Test Case ID | Total Qubits Sent | Expected Sifted Bits | `testSample` Ratio | Expected Mean $\Delta \text{QBER}$ | Pass Criteria |
| --- | --- | --- | --- | --- | --- |
| **TS3-TC01** | 40 | ~20 bits | 50% (~10 sample, ~10 key) | $\le 8.0\%$ | Demonstrates high variance at small sample sizes. |
| **TS3-TC02** | 120 | ~60 bits | 50% (~30 sample, ~30 key) | $\le 4.5\%$ | $\Delta \text{QBER}$ decreases as sample size grows. |
| **TS3-TC03** | 240 | ~120 bits | 50% (~60 sample, ~60 key) | $\le 2.5\%$ | Sample QBER converges to within $\pm 2.5\%$ of true key QBER. |

---

### Test Suite 4: End-to-End OTP Ballot Correctness & Error Correction

**Objective:** Validate that casting a ballot (`"VT1"`, `"VT2"`, `"VT3"`) using XOR One-Time Pad ($C = M \oplus K_{\text{Alice}}$, $M' = C \oplus K_{\text{Bob}}$) recovers the exact plaintext vote $M' = M$ 100% of the time when error correction is active, and satisfies Shannon's Perfect Secrecy requirements.

| Test Case ID | Scenario | Config | Input Vote ($M$) | Expected Output ($M'$) | Pass Criteria |
| --- | --- | --- | --- | --- | --- |
| **TS4-TC01** | Ideal OTP Encryption & Decryption | `isUsingQuantumComputer = false`, `errorCorrectionEnabled = false` | `"VT3"` (`01010110 01010100 00110011`) | `"VT3"` | 100% decryption accuracy across 100 cast ballots. |
| **TS4-TC02** | Noisy Channel **Without** Error Correction | `isUsingQuantumComputer = true`, `errorCorrectionEnabled = false` | `"VT3"` | Corrupted (e.g., `"VT2"` or `"VU3"`) when $\text{QBER}_{\text{key}} > 0\%$ | Demonstrates why raw noisy QKD keys corrupt OTP decryption without reconciliation. |
| **TS4-TC03** | Noisy Channel **With** Error Correction | `isUsingQuantumComputer = true`, `errorCorrectionEnabled = true` | `"VT3"` | `"VT3"` | **100% decryption accuracy**; all residual noise bit-flips in $K_{\text{Bob}}$ are corrected before XOR decryption. |
| **TS4-TC04** | Insufficient Key Length Guardrail | Force $|K_{\text{final}}| = 16\text{ bits} < |M| = 24\text{ bits}$ | `"VT3"` (24 bits) | `400 Bad Request` or Auto-Concatenate | System strictly prevents OTP encryption with a key shorter than the plaintext ($|K| < |M|$) or automatically requests additional QKD sessions. |
| **TS4-TC05** | Ciphertext Uniformity & Key Independence | Cast `"VT3"` 50 times across 50 sessions | `"VT3"` $\times 50$ | 50 distinct ciphertexts $C^{(1)} \dots C^{(50)}$ | Bit distribution across generated keys and ciphertexts is uniform (~50% `0`s, ~50% `1`s within $\pm 3\%$), with zero key reuse. |

---

## 4. Key Metrics & Deliverables for Presentation Report

When executing this test specification, record and plot the following 4 summary metrics for the presentation slides:

1. **Sifting & Key Sufficiency Table:** Success rate (%) of reaching 24-bit key length vs. safety margin $\delta \in \{0, 0.5, 1.0, 1.5, 2.0\}$.
2. **QBER Distribution Histogram / Bar Chart:** Average `qberPercent` across:
* Ideal Channel (`0%`)
* IBM Quantum / Noisy Channel (`~2–4%`)
* Eavesdropper Active (`~25%`), showing the `11%` threshold line clearly separating safe vs. attacked sessions.
3. **Estimation Error Curve ($\Delta \text{QBER}$):** Line plot showing $|\text{QBER}_{\text{sample}} - \text{QBER}_{\text{key}}|$ converging toward `0%` as `qubitPerSession` increases from `40` to `240`.
4. **Ballot Decryption Accuracy Table:** Comparison of Ballot Recovery Rate (%) under Noisy QKD with `errorCorrectionEnabled = false` vs. `errorCorrectionEnabled = true` (`100%`).
