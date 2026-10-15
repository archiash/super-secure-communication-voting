# Quantum-Secured Voting System — Development Roadmap & TODO

This document is the master specification and roadmap for building, refining, and aligning the **BB84 Quantum Key Distribution (QKD)** simulation with the educational voting system.

---

## 🔬 Core Physical & Cryptographic Principles

### 1. The Dual-Perspective Design
An educational simulation of quantum cryptography must distinguish between what is physically happening in the simulator vs. what the protocol participants can legitimately observe:

| Dimension | System Perspective (God View) | Real-Life Perspective (Alice & Bob) |
| :--- | :--- | :--- |
| **Visibility** | Omniscient simulation engine (impossible in real physics) | Alice and Bob over quantum & classical channels |
| **QBER Measurement** | Evaluates **100%** of all sifted bits ($N_{\text{sifted}}$) | Evaluates **only a random sample** of $k$ test bits |
| **Bit Sacrificing** | No bits discarded (purely for analytics & teaching) | **Sacrifices and discards** the $k$ test bits permanently |
| **Eve Telemetry** | Full inspection: Eve's bases, measured bits, disturb rate | **Zero direct visibility**: Eve inferred only if $\text{QBER} > 11\%$ |
| **Key Extraction** | Retains both parties' raw sifted bitstreams | Extracts unrevealed secret bits $\to$ One-Time Pad |
| **Purpose** | Visualizing quantum mechanics, debugging, grading | Information-theoretic security & vote encryption |

### 2. The $(4 + \delta) \cdot n$ Transmission Bound
To produce a secure final key of length $n$ bits (`target_key_length`), Alice must transmit $N$ photons where:
$$N \ge (4 + \delta) \cdot n$$
- **Factor of $2\times$**: Basis Sifting discards $\approx 50\%$ of qubits because Alice and Bob choose bases independently at random.
- **Factor of $2\times$ (plus $\delta$)**: Consumed by test-bit sacrificing ($k$ bits), Cascade error correction parity leakage, and privacy amplification compression.
- *Note:* Transmitting $n$ qubits cannot yield an $n$-bit final secret key.

### 3. Pydantic Architecture
All perspective data structures inherit from `CamelModel` (Pydantic V2) in `backend/src/core/schemas.py`:
- Automatic runtime type validation and error catching.
- Seamless conversion between Python `snake_case` and frontend TypeScript `camelCase`.
- Native FastAPI JSON serialization and Beanie/MongoDB document persistence.

---

## ✅ Completed Tasks

- [x] Basic BB84 quantum circuit implementation (Pauli-X, Hadamard, measurement) in `qkd.py`.
- [x] Intercept-resend attack simulation for Eve in `qkd.py`.
- [x] Execution backends: Qiskit Aer local simulation & IBM Quantum hardware.
- [x] Renamed `get_match_indexes` $\to$ `sift_bases(alice_basis, bob_basis)`.
- [x] Renamed `sifting` $\to$ `filter_key_by_basis(key, basis1, basis2)` and updated all callers in `service.py`.

---

## 📋 Actionable Tasks

### Phase 1: Dual-Perspective Data Models (`models.py` & `qkd.py`)
- [ ] **Define `SystemPerspective` (`CamelModel`)**:
  - `total_qubits_transmitted: int`
  - `alice_bits: str` (Alice's raw generated bitstring)
  - `alice_bases: str` (Alice's basis choices)
  - `bob_reads: str` (Bob's raw measured bitstring)
  - `bob_bases: str` (Bob's basis choices)
  - `matching_indices: list[int]` (All photon indices where bases matched)
  - `alice_sifted_key: str` (Alice's 100% sifted key)
  - `bob_sifted_key: str` (Bob's 100% sifted key)
  - `true_error_count: int` (Exact count of bit mismatches across all sifted bits)
  - `true_qber: float` (True physical QBER: `true_error_count / len(sifted_bits)`)
  - `eve_present: bool`
  - `eve_bases: Optional[str]`
  - `eve_reads: Optional[str]`
  - `eve_matched_bases_count: Optional[int]`
- [ ] **Define `RealLifePerspective` (`CamelModel`)**:
  - `public_matching_indices: list[int]` (Basis match positions announced on classical channel)
  - `total_sifted_bits: int`
  - `test_sample_indices: list[int]` (Randomly chosen sample indices sacrificed for QBER)
  - `test_sample_size: int` (Number of sacrificed test bits, $k$)
  - `test_errors_found: int` (Mismatches found in test sample)
  - `sample_qber: float` (Estimated error rate: `test_errors_found / test_sample_size`)
  - `error_threshold: float` (Security limit, e.g., 0.11 / 11%)
  - `passed_threshold: bool` (`sample_qber <= error_threshold`)
  - `status: str` (`KEY_GENERATED` or `ABORTED`)
  - `raw_secret_key_alice: str` (Sifted key with test bits permanently stripped out)
  - `raw_secret_key_bob: str` (Sifted key with test bits permanently stripped out)
  - `final_key: str` (Key truncated to `target_key_length`, empty string if aborted)
- [ ] **Define `BB84SimulationResult` (`CamelModel`)**:
  - Encapsulates `system: SystemPerspective` and `real_life: RealLifePerspective`.

---

### Phase 2: Core Protocol Enhancements (`qkd.py`)
- [ ] **Fix Qubit Transmission Sizing**:
  - Update `simulate_bb84_protocal` to accept `qubit_count` as the photon transmission count.
  - Sifted bits must be large enough to satisfy: $\text{sifted\_bits} \ge \text{target\_key\_length} + \text{test\_sample\_size}$.
- [ ] **Fix `random_binary` Length Bug**:
  - Slice generated bitstring to exact requested length (`[:number_of_bit]`).
- [ ] **Implement Random Test Bit Sampling & Key Sacrificing**:
  - Create `estimate_sample_qber_and_extract_key()`:
    - Randomly sample $k$ test positions using `secrets.SystemRandom().sample()`.
    - Compute `sample_qber = sample_errors / k`.
    - **Discard** the $k$ test bits from both keys.
    - Return remaining unrevealed secret key bits.
- [ ] **Implement Dual-Perspective Orchestrator**:
  - Package both `system` and `real_life` data models from each simulation run.
  - Attach Eve's intercept telemetry to `SystemPerspective`.

---

### Phase 3: Backend Integration & Security Hardening (`service.py` & `models.py`)
- [ ] **Update `create_qkd_key()` in `service.py`**:
  - Use the dual-perspective simulation output.
  - Return both perspectives in `GenerateKeyRespond` while preserving existing top-level fields for frontend compatibility.
  - If `passed_threshold == False`, set status to `ABORTED` and set `final_key = ""`.
- [ ] **Fix Models & Database Schemas in `models.py`**:
  - Fix typo: `elction_code` $\to$ `election_code` in `GenerateKeyRespond`.
  - Add missing `error_found: int` field in `GenerateKeyRespond`.
  - Update `VotingSession` MongoDB schema to persist `system` and `real_life` perspectives.
- [ ] **Security Gate in `cast_ballot()`**:
  - Reject vote submissions with HTTP 400 if `session.status == "ABORTED"`.

---

### Phase 4: Frontend Alignment & Dual-Perspective UI (`Front_end/`)
- [ ] **Update TypeScript Types (`types/qkd.ts`)**:
  - Add `SystemPerspectiveData` and `RealLifePerspectiveData` interfaces matching backend models.
  - Update `QKDResponse` to carry both perspectives.
- [ ] **Update API Client (`services/real-api.ts`)**:
  - Parse `system` and `real_life` data from backend responses without dropping `errorFound` or `testSample`.
- [ ] **Add Perspective Toggle in UI (`pages/KeyGenerationPage.tsx`)**:
  - Add an interactive switch between:
    - **🛰️ System Perspective (God View)**: Full table with Alice/Bob/Eve, photon polarizations, Eve's disturbance, and True QBER across 100% of bits.
    - **👤 Real-Life Perspective (Alice & Bob View)**: Shows only legitimate public channel info, clearly highlights sacrificed test bits, and displays the Sample QBER card.
- [ ] **Update Configuration Page (`pages/ConfigurePage.tsx`)**:
  - Add validation / warning helper: recommend $\text{Qubit Count} \ge 4 \times \text{Target Key Length} + \text{Test Bits}$.
  - Expose `testBitCount` configuration slider in the UI.

---

### Phase 5: Advanced Post-Processing & Realism (Future)
- [ ] **Cascade Error Correction Protocol**:
  - Implement iterative parity block checks to correct residual bit errors.
- [ ] **Privacy Amplification**:
  - Shrink the key using universal hashing / Toeplitz matrices to eliminate information leaked to Eve.
- [ ] **Channel Noise Simulation**:
  - Apply `qiskit_aer.noise.NoiseModel` (depolarizing channel) to simulate 1%–2% realistic fiber noise when Eve is disabled.
- [ ] **Implement Missing Backend Endpoints**:
  - Add `/vote/voting-audits/{election_code}` and `/vote/reset` in backend router so frontend doesn't fallback to mock.
