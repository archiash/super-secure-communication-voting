"""
Evaluation and Simulation Benchmark Suite for Quantum Key Distribution (BB84)
and Secure Communication / Voting System.

Covers:
1. Raw transmission key size vs desired final key length
2. Key generation with vs without eavesdropping & optimal threshold determination
3. Encryption / Decryption verification (One-Time Pad XOR) and error impact
4. Difference between Sample/Check QBER and Final Secret Key QBER
"""

import os
import sys
import math
import json
import random
import time
from typing import Dict, List, Tuple, Any

# Ensure backend/src is on Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from modules import qkd


def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)


# ==============================================================================
# Helper Functions
# ==============================================================================

def run_bb84_with_sampling(
    raw_qubits: int,
    sample_ratio: float = 0.25,
    has_eavesdropping: bool = False,
    channel_noise: float = 0.0,
    eve_intercept_rate: float = 1.0
) -> Dict[str, Any]:
    """
    Run BB84 simulation, sift matching bases, and split sifted bits into:
    - Sample/check bits (for eavesdropping detection)
    - Secret key bits (for encryption)
    """
    # 1. Alice generates random bits and random bases
    alice_bits = [random.choice(['0', '1']) for _ in range(raw_qubits)]
    alice_bases = [random.choice(['0', '1']) for _ in range(raw_qubits)]
    bob_bases = [random.choice(['0', '1']) for _ in range(raw_qubits)]

    bob_read = []

    for i in range(raw_qubits):
        bit = alice_bits[i]
        a_base = alice_bases[i]
        b_base = bob_bases[i]

        # Eavesdropping simulation
        if has_eavesdropping and (random.random() < eve_intercept_rate):
            # Eve chooses random basis
            eve_base = random.choice(['0', '1'])
            if eve_base == a_base:
                eve_bit = bit
            else:
                eve_bit = random.choice(['0', '1'])
            # Eve resends in her basis
            sent_bit = eve_bit
            sent_base = eve_base
        else:
            sent_bit = bit
            sent_base = a_base

        # Bob measures
        if b_base == sent_base:
            measured_bit = sent_bit
        else:
            measured_bit = random.choice(['0', '1'])

        # Channel noise (depolarizing/bit flip)
        if channel_noise > 0.0 and random.random() < channel_noise:
            measured_bit = '1' if measured_bit == '0' else '0'

        bob_read.append(measured_bit)

    # 2. Sifting: keep bits where Alice and Bob bases matched
    sifted_alice = []
    sifted_bob = []
    sifted_indices = []

    for i in range(raw_qubits):
        if alice_bases[i] == bob_bases[i]:
            sifted_alice.append(alice_bits[i])
            sifted_bob.append(bob_read[i])
            sifted_indices.append(i)

    sifted_len = len(sifted_alice)

    if sifted_len == 0:
        return {
            "raw_qubits": raw_qubits,
            "sifted_len": 0,
            "sample_len": 0,
            "key_len": 0,
            "total_qber": 0.0,
            "sample_qber": 0.0,
            "key_qber": 0.0,
            "qber_diff": 0.0,
            "signed_diff": 0.0,
            "alice_key": "",
            "bob_key": ""
        }

    # 3. Overall Sifted QBER
    total_errors = sum(1 for a, b in zip(sifted_alice, sifted_bob) if a != b)
    total_qber = total_errors / sifted_len

    # 4. Partition into Sample Bits vs Final Key Bits
    sample_len = int(round(sifted_len * sample_ratio))
    # Ensure sample doesn't exceed sifted_len and leaves at least 1 key bit if possible
    if sample_len >= sifted_len and sifted_len > 1:
        sample_len = sifted_len - 1

    all_indices = list(range(sifted_len))
    random.shuffle(all_indices)
    sample_idx = set(all_indices[:sample_len])
    key_idx = [i for i in range(sifted_len) if i not in sample_idx]

    # Sample QBER
    if sample_len > 0:
        sample_errors = sum(1 for i in sample_idx if sifted_alice[i] != sifted_bob[i])
        sample_qber = sample_errors / sample_len
    else:
        sample_qber = total_qber

    # Key QBER
    key_len = len(key_idx)
    if key_len > 0:
        key_errors = sum(1 for i in key_idx if sifted_alice[i] != sifted_bob[i])
        key_qber = key_errors / key_len
        alice_key = "".join(sifted_alice[i] for i in key_idx)
        bob_key = "".join(sifted_bob[i] for i in key_idx)
    else:
        key_qber = total_qber
        alice_key = "".join(sifted_alice)
        bob_key = "".join(sifted_bob)

    return {
        "raw_qubits": raw_qubits,
        "sifted_len": sifted_len,
        "sample_len": sample_len,
        "key_len": key_len,
        "total_qber": total_qber * 100.0,
        "sample_qber": sample_qber * 100.0,
        "key_qber": key_qber * 100.0,
        "qber_diff": abs(sample_qber - key_qber) * 100.0,
        "signed_diff": (sample_qber - key_qber) * 100.0,
        "alice_key": alice_key,
        "bob_key": bob_key
    }


# ==============================================================================
# Experiment 1: Key Length Optimization & Reliability
# ==============================================================================

def evaluate_key_length_requirements(
    target_key_lengths: List[int] = [32, 64, 128, 256],
    multipliers: List[float] = [1.0, 1.5, 2.0, 2.2, 2.5, 3.0, 3.5, 4.0],
    sample_ratios: List[float] = [0.0, 0.25, 0.33],
    trials: int = 150
) -> Dict[str, Any]:
    """
    Test various raw qubit transmission lengths for target secret key sizes
    to find the required transmission size for sufficient key yield.
    """
    print("\n" + "="*80)
    print("EXPERIMENT 1: Key Transmission Length vs. Target Secret Key Length")
    print("="*80)

    results = {}

    for sample_ratio in sample_ratios:
        ratio_label = f"sample_{int(sample_ratio*100)}pct"
        results[ratio_label] = {}

        print(f"\n--- Evaluation with Sample Check Ratio: {sample_ratio*100:.0f}% ---")
        print(f"{'Target':<8} | {'Mult':<6} | {'Raw Bits':<10} | {'Mean Sifted':<12} | {'Mean Final':<12} | {'Success Rate (%)':<18}")
        print("-" * 75)

        for target in target_key_lengths:
            results[ratio_label][str(target)] = []

            for mult in multipliers:
                raw_qubits = int(round(target * mult))
                success_count = 0
                sifted_lens = []
                final_lens = []

                for _ in range(trials):
                    res = run_bb84_with_sampling(
                        raw_qubits=raw_qubits,
                        sample_ratio=sample_ratio,
                        has_eavesdropping=False
                    )
                    effective_key_len = res["key_len"] if sample_ratio > 0 else res["sifted_len"]
                    sifted_lens.append(res["sifted_len"])
                    final_lens.append(effective_key_len)

                    if effective_key_len >= target:
                        success_count += 1

                success_rate = (success_count / trials) * 100.0
                mean_sifted = float(np.mean(sifted_lens))
                mean_final = float(np.mean(final_lens))
                std_final = float(np.std(final_lens))

                entry = {
                    "multiplier": mult,
                    "raw_qubits": raw_qubits,
                    "mean_sifted": round(mean_sifted, 2),
                    "mean_final": round(mean_final, 2),
                    "std_final": round(std_final, 2),
                    "success_rate": round(success_rate, 2)
                }
                results[ratio_label][str(target)].append(entry)

                print(f"{target:<8} | {mult:<6.1f} | {raw_qubits:<10} | {mean_sifted:<12.1f} | {mean_final:<12.1f} | {success_rate:<18.1f}")

    return results


# ==============================================================================
# Experiment 2: Eavesdropping Detection & Optimal Threshold
# ==============================================================================

def evaluate_eavesdropping_and_threshold(
    key_size: int = 128,
    trials: int = 200,
    noise_levels: List[float] = [0.0, 0.02, 0.04],
    eve_intercept_rates: List[float] = [0.25, 0.50, 0.75, 1.0]
) -> Dict[str, Any]:
    """
    Simulate BB84 with and without eavesdropping under different channel conditions.
    Determine optimal QBER threshold to separate legitimate vs eavesdropped channels.
    """
    print("\n" + "="*80)
    print("EXPERIMENT 2: Eavesdropping Detection and Optimal QBER Threshold")
    print("="*80)

    # 1. Clean / Legitimate transmissions (No Eve) across noise levels
    clean_data = {}
    for noise in noise_levels:
        qbers = []
        for _ in range(trials):
            res = run_bb84_with_sampling(
                raw_qubits=key_size * 2,
                sample_ratio=0.30,
                has_eavesdropping=False,
                channel_noise=noise
            )
            qbers.append(res["sample_qber"])
        clean_data[f"noise_{int(noise*100)}pct"] = {
            "mean": float(np.mean(qbers)),
            "std": float(np.std(qbers)),
            "min": float(np.min(qbers)),
            "max": float(np.max(qbers)),
            "p95": float(np.percentile(qbers, 95)),
            "raw_qbers": qbers
        }

    # 2. Eavesdropped transmissions (Eve Present) across intercept rates
    eve_data = {}
    for eve_rate in eve_intercept_rates:
        qbers = []
        for _ in range(trials):
            res = run_bb84_with_sampling(
                raw_qubits=key_size * 2,
                sample_ratio=0.30,
                has_eavesdropping=True,
                channel_noise=0.02,  # realistic 2% baseline optical noise
                eve_intercept_rate=eve_rate
            )
            qbers.append(res["sample_qber"])
        eve_data[f"eve_{int(eve_rate*100)}pct"] = {
            "mean": float(np.mean(qbers)),
            "std": float(np.std(qbers)),
            "min": float(np.min(qbers)),
            "max": float(np.max(qbers)),
            "p5": float(np.percentile(qbers, 5)),
            "raw_qbers": qbers
        }

    # 3. Threshold Analysis: Sweeping thresholds from 1% to 25%
    thresholds = [round(t, 1) for t in np.arange(1.0, 26.0, 1.0)]
    threshold_metrics = []

    # Use 2% noise legitimate channel vs 100% full Eve
    legit_qbers = clean_data["noise_2pct"]["raw_qbers"]
    intercepted_qbers = eve_data["eve_100pct"]["raw_qbers"]

    print(f"\n--- Threshold Performance Sweep (2% Channel Noise vs 100% Intercept Eve) ---")
    print(f"{'Threshold (%)':<15} | {'False Alarm (FPR %)':<22} | {'Detection (TPR %)':<20} | {'F1-Score':<10}")
    print("-" * 75)

    best_threshold = 11.0
    best_f1 = -1.0

    for th in thresholds:
        # False Positive: Clean session falsely aborted (QBER > th)
        fp = sum(1 for q in legit_qbers if q > th)
        fpr = (fp / len(legit_qbers)) * 100.0

        # True Positive: Eve session correctly detected/aborted (QBER > th)
        tp = sum(1 for q in intercepted_qbers if q > th)
        tpr = (tp / len(intercepted_qbers)) * 100.0

        # False Negative: Eve session missed
        fn = len(intercepted_qbers) - tp

        # Precision & Recall & F1
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        threshold_metrics.append({
            "threshold": th,
            "fpr": round(fpr, 2),
            "tpr": round(tpr, 2),
            "precision": round(precision * 100, 2),
            "recall": round(recall * 100, 2),
            "f1": round(f1, 4)
        })

        if f1 > best_f1:
            best_f1 = f1
            best_threshold = th

        if th in [5.0, 8.0, 10.0, 11.0, 12.0, 15.0, 20.0]:
            print(f"{th:<15.1f} | {fpr:<22.2f} | {tpr:<20.2f} | {f1:<10.4f}")

    print(f"\nOptimal Empirical Threshold: {best_threshold}% (F1-score: {best_f1:.4f})")
    print(f"Standard BB84 Theoretical Security Limit: 11.0% (Shor-Preskill / Mutual Information Limit)")

    return {
        "clean_summary": {k: {m: v[m] for m in ["mean", "std", "min", "max", "p95"]} for k, v in clean_data.items()},
        "eve_summary": {k: {m: v[m] for m in ["mean", "std", "min", "max", "p5"]} for k, v in eve_data.items()},
        "threshold_metrics": threshold_metrics,
        "best_threshold": best_threshold,
        "best_f1": best_f1,
        "clean_raw_qbers": {k: v["raw_qbers"] for k, v in clean_data.items()},
        "eve_raw_qbers": {k: v["raw_qbers"] for k, v in eve_data.items()}
    }


# ==============================================================================
# Experiment 3: Encryption / Decryption Correctness and QBER Impact
# ==============================================================================

def otp_encrypt(plaintext_bin: str, key_bin: str) -> str:
    """XOR Encryption for binary strings"""
    if len(plaintext_bin) != len(key_bin):
        raise ValueError(f"Length mismatch: plaintext ({len(plaintext_bin)}) vs key ({len(key_bin)})")
    return "".join(str(int(p) ^ int(k)) for p, k in zip(plaintext_bin, key_bin))

def otp_decrypt(ciphertext_bin: str, key_bin: str) -> str:
    """XOR Decryption (identical to encryption)"""
    return otp_encrypt(ciphertext_bin, key_bin)

def text_to_binary(text: str) -> str:
    return "".join(format(ord(c), '08b') for c in text)

def binary_to_text(binary: str) -> str:
    chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
    return "".join(chr(int(b, 2)) for b in chars)

def evaluate_encryption_decryption(trials: int = 500) -> Dict[str, Any]:
    """
    Test OTP / XOR encryption and decryption for:
    1. Functional correctness (100% reversibility)
    2. Edge cases (all 0s, all 1s, alternating patterns, text ballots)
    3. Error propagation: Impact of uncorrected quantum key errors on ballot integrity
    """
    print("\n" + "="*80)
    print("EXPERIMENT 3: Encryption and Decryption Verification (OTP / XOR)")
    print("="*80)

    # 1. Functional correctness test
    test_cases = [
        # Candidate voting indexes (e.g., 2-bit or 4-bit candidate numbers)
        ("Candidate 0", "00"),
        ("Candidate 1", "01"),
        ("Candidate 2", "10"),
        ("Candidate 3", "11"),
        # Edge cases
        ("All Zeros", "00000000"),
        ("All Ones", "11111111"),
        ("Alternating", "10101010"),
        # Full ballot text strings
        ("Ballot 'YES'", text_to_binary("YES")),
        ("Ballot 'NO'", text_to_binary("NO")),
        ("Candidate Name", text_to_binary("Alice_Smith"))
    ]

    all_passed = True
    print("\n--- Deterministic Ballot Test Cases ---")
    print(f"{'Test Case':<20} | {'Bits':<6} | {'Ciphertext Sample':<20} | {'Status':<10}")
    print("-" * 65)

    for name, plain_bin in test_cases:
        key_bin = "".join(random.choice(['0', '1']) for _ in range(len(plain_bin)))
        cipher = otp_encrypt(plain_bin, key_bin)
        decrypted = otp_decrypt(cipher, key_bin)

        is_match = (decrypted == plain_bin)
        if not is_match:
            all_passed = False
        sample = cipher[:16] + ("..." if len(cipher) > 16 else "")
        print(f"{name:<20} | {len(plain_bin):<6} | {sample:<20} | {'PASSED' if is_match else 'FAILED'}")

    # 2. Randomized stress testing
    random_tests_passed = 0
    for _ in range(trials):
        length = random.randint(8, 256)
        plain = "".join(random.choice(['0', '1']) for _ in range(length))
        key = "".join(random.choice(['0', '1']) for _ in range(length))
        cipher = otp_encrypt(plain, key)
        decrypted = otp_decrypt(cipher, key)
        if decrypted == plain:
            random_tests_passed += 1

    random_success_rate = (random_tests_passed / trials) * 100.0
    print(f"\nRandomized stress test ({trials} trials): {random_tests_passed}/{trials} passed ({random_success_rate:.2f}%)")

    # 3. Quantum Key Error (QBER) impact on ballot corruption
    error_rates = [0.0, 0.01, 0.05, 0.11, 0.25]
    qber_impact = []

    print("\n--- Impact of Quantum Key Errors (QBER) on Decrypted Ballot Integrity ---")
    print(f"{'Key QBER (%)':<15} | {'Ballot Bit Error Rate (BER %)':<32} | {'Vote Corruption Rate (%)':<25}")
    print("-" * 75)

    ballot_len = 16  # 16-bit ballot payload
    test_runs = 1000

    for err in error_rates:
        corrupted_ballots = 0
        total_bit_errors = 0

        for _ in range(test_runs):
            plain = "".join(random.choice(['0', '1']) for _ in range(ballot_len))
            alice_key = "".join(random.choice(['0', '1']) for _ in range(ballot_len))
            cipher = otp_encrypt(plain, alice_key)

            # Bob receives key with QBER errors
            bob_key_chars = []
            for k in alice_key:
                if random.random() < err:
                    bob_key_chars.append('1' if k == '0' else '0')
                else:
                    bob_key_chars.append(k)
            bob_key = "".join(bob_key_chars)

            decrypted = otp_decrypt(cipher, bob_key)

            bit_errs = sum(1 for p, d in zip(plain, decrypted) if p != d)
            total_bit_errors += bit_errs
            if decrypted != plain:
                corrupted_ballots += 1

        ber = (total_bit_errors / (test_runs * ballot_len)) * 100.0
        corruption_rate = (corrupted_ballots / test_runs) * 100.0

        qber_impact.append({
            "key_qber": err * 100.0,
            "ballot_ber": round(ber, 2),
            "ballot_corruption_rate": round(corruption_rate, 2)
        })

        print(f"{err*100.0:<15.1f} | {ber:<32.2f} | {corruption_rate:<25.2f}")

    return {
        "all_deterministic_passed": all_passed,
        "random_stress_success_rate": random_success_rate,
        "qber_impact": qber_impact
    }


# ==============================================================================
# Experiment 4: Difference between QBER of Sample vs QBER of Final Key
# ==============================================================================

def evaluate_qber_sample_vs_key(
    key_sizes: List[int] = [64, 128, 256, 512],
    sample_ratios: List[float] = [0.10, 0.20, 0.33, 0.50],
    trials: int = 300,
    has_eavesdropping: bool = True
) -> Dict[str, Any]:
    """
    Measure difference between QBER calculated from sample/check bits
    and QBER of remaining secret key bits:
    Delta_QBER = |QBER_sample - QBER_key|
    and evaluate statistical consistency across sizes and sample proportions.
    """
    print("\n" + "="*80)
    print("EXPERIMENT 4: Difference Between Sample QBER and Secret Key QBER")
    print(f"Condition: {'With Eavesdropping (Eve 100%)' if has_eavesdropping else 'Clean Channel + 3% Noise'}")
    print("="*80)

    results = {}
    channel_noise = 0.0 if has_eavesdropping else 0.03

    print(f"{'Sifted Key':<12} | {'Sample %':<10} | {'Mean Diff (|Delta_QBER| %)':<26} | {'RMSE (%)':<12} | {'Signed Mean (%)':<18} | {'Correlation r':<14}")
    print("-" * 95)

    for key_size in key_sizes:
        results[str(key_size)] = {}

        for ratio in sample_ratios:
            diffs = []
            signed_diffs = []
            sample_qbers = []
            key_qbers = []

            for _ in range(trials):
                # Raw transmission = key_size * 2 to get ~key_size sifted bits
                res = run_bb84_with_sampling(
                    raw_qubits=key_size * 2,
                    sample_ratio=ratio,
                    has_eavesdropping=has_eavesdropping,
                    channel_noise=channel_noise
                )

                if res["sifted_len"] > 2:
                    diffs.append(res["qber_diff"])
                    signed_diffs.append(res["signed_diff"])
                    sample_qbers.append(res["sample_qber"])
                    key_qbers.append(res["key_qber"])

            mean_abs_diff = float(np.mean(diffs))
            rmse = float(np.sqrt(np.mean(np.array(diffs)**2)))
            signed_mean = float(np.mean(signed_diffs))
            corr = float(np.corrcoef(sample_qbers, key_qbers)[0, 1]) if len(sample_qbers) > 1 else 0.0

            entry = {
                "sample_ratio": ratio,
                "mean_abs_diff": round(mean_abs_diff, 2),
                "rmse": round(rmse, 2),
                "signed_mean": round(signed_mean, 2),
                "std_diff": round(float(np.std(diffs)), 2),
                "correlation": round(corr, 4),
                "sample_qbers": sample_qbers[:50],  # store subset for JSON
                "key_qbers": key_qbers[:50]
            }
            results[str(key_size)][f"sample_{int(ratio*100)}pct"] = entry

            print(f"{key_size:<12} | {ratio*100:<10.0f} | {mean_abs_diff:<25.2f} | {rmse:<12.2f} | {signed_mean:<18.2f} | {corr:<14.4f}")

    return results


# ==============================================================================
# Visualization Generation
# ==============================================================================

def generate_plots(exp1_res, exp2_res, exp3_res, exp4_res, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

    # -------------------------------------------------------------------------
    # Plot 1: Key Length Reliability and Success Rate
    # -------------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    target_64 = exp1_res["sample_25pct"]["64"]
    target_128 = exp1_res["sample_25pct"]["128"]
    target_256 = exp1_res["sample_25pct"]["256"]

    mults = [e["multiplier"] for e in target_64]
    sr_64 = [e["success_rate"] for e in target_64]
    sr_128 = [e["success_rate"] for e in target_128]
    sr_256 = [e["success_rate"] for e in target_256]

    ax1.plot(mults, sr_64, marker='o', linewidth=2.2, label='Target = 64 bits')
    ax1.plot(mults, sr_128, marker='s', linewidth=2.2, label='Target = 128 bits')
    ax1.plot(mults, sr_256, marker='^', linewidth=2.2, label='Target = 256 bits')
    ax1.axhline(99.0, color='red', linestyle='--', label='99% Target Reliability')
    ax1.axvline(3.0, color='gray', linestyle=':', label='Recommended 3.0x Multiplier')
    ax1.set_title("Key Yield Reliability vs. Transmission Multiplier\n(with 25% Check Bits)", fontsize=12, fontweight='bold')
    ax1.set_xlabel("Transmission Multiplier (N_raw / L_target)", fontsize=11)
    ax1.set_ylabel("Success Rate P(L_final >= L_target) (%)", fontsize=11)
    ax1.set_ylim(-5, 105)
    ax1.legend(loc='lower right')
    ax1.grid(True, linestyle='--', alpha=0.6)

    # Final Key Length vs Raw Transmission
    final_64 = [e["mean_final"] for e in target_64]
    final_128 = [e["mean_final"] for e in target_128]
    final_256 = [e["mean_final"] for e in target_256]

    ax2.plot(mults, final_64, marker='o', linewidth=2.2, label='Target = 64')
    ax2.plot(mults, final_128, marker='s', linewidth=2.2, label='Target = 128')
    ax2.plot(mults, final_256, marker='^', linewidth=2.2, label='Target = 256')
    ax2.set_title("Mean Usable Secret Key Length vs. Multiplier\n(Post-Sifting & Sampling)", fontsize=12, fontweight='bold')
    ax2.set_xlabel("Transmission Multiplier (N_raw / L_target)", fontsize=11)
    ax2.set_ylabel("Mean Usable Secret Key (bits)", fontsize=11)
    ax2.legend(loc='upper left')
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plot1_path = os.path.join(output_dir, "eval_plot1_key_length_reliability.png")
    plt.savefig(plot1_path, dpi=300)
    plt.close()
    print(f"Saved: {plot1_path}")

    # -------------------------------------------------------------------------
    # Plot 2: Eavesdropping Detection & ROC / Threshold Curve
    # -------------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    clean_0 = exp2_res["clean_raw_qbers"]["noise_0pct"]
    clean_2 = exp2_res["clean_raw_qbers"]["noise_2pct"]
    eve_100 = exp2_res["eve_raw_qbers"]["eve_100pct"]
    eve_50 = exp2_res["eve_raw_qbers"]["eve_50pct"]

    # Histogram / KDE
    bins = np.linspace(0, 35, 36)
    ax1.hist(clean_2, bins=bins, alpha=0.6, label='Legitimate (2% Noise)', color='green', density=True)
    ax1.hist(eve_50, bins=bins, alpha=0.5, label='Partial Eve (50% Intercept)', color='orange', density=True)
    ax1.hist(eve_100, bins=bins, alpha=0.6, label='Full Eve (100% Intercept)', color='red', density=True)
    ax1.axvline(11.0, color='darkred', linestyle='--', linewidth=2.5, label='Optimal Threshold (11%)')
    ax1.set_title("QBER Distribution Under Eavesdropping vs. Clean Channel", fontsize=12, fontweight='bold')
    ax1.set_xlabel("Measured QBER (%)", fontsize=11)
    ax1.set_ylabel("Probability Density", fontsize=11)
    ax1.legend(loc='upper right')
    ax1.grid(True, linestyle='--', alpha=0.6)

    # ROC / Performance curve vs Threshold
    th_metrics = exp2_res["threshold_metrics"]
    thresholds = [m["threshold"] for m in th_metrics]
    fprs = [m["fpr"] for m in th_metrics]
    tprs = [m["tpr"] for m in th_metrics]
    f1s = [m["f1"] for m in th_metrics]

    ax2.plot(thresholds, tprs, color='green', linewidth=2.2, label='Detection Rate (TPR %)')
    ax2.plot(thresholds, fprs, color='red', linewidth=2.2, label='False Alarm Rate (FPR %)')
    ax2.plot(thresholds, [f*100 for f in f1s], color='blue', linestyle='-.', linewidth=2.2, label='F1 Score (%)')
    ax2.axvline(11.0, color='darkred', linestyle='--', linewidth=2.0, label='BB84 Threshold = 11%')
    ax2.set_title("Detection Performance Across QBER Thresholds", fontsize=12, fontweight='bold')
    ax2.set_xlabel("QBER Abort Threshold (%)", fontsize=11)
    ax2.set_ylabel("Rate (%)", fontsize=11)
    ax2.set_ylim(-5, 105)
    ax2.legend(loc='center right')
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plot2_path = os.path.join(output_dir, "eval_plot2_eavesdropping_threshold.png")
    plt.savefig(plot2_path, dpi=300)
    plt.close()
    print(f"Saved: {plot2_path}")

    # -------------------------------------------------------------------------
    # Plot 3: Encryption Verification & Ballot Corruption vs QBER
    # -------------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    qber_impact = exp3_res["qber_impact"]
    qbers = [item["key_qber"] for item in qber_impact]
    bers = [item["ballot_ber"] for item in qber_impact]
    corruptions = [item["ballot_corruption_rate"] for item in qber_impact]

    ax1.plot(qbers, bers, marker='o', color='purple', linewidth=2.5, label='Ballot Bit Error Rate (BER)')
    ax1.plot(qbers, qbers, linestyle='--', color='gray', label='Ideal 1:1 Parity Line')
    ax1.set_title("Decrypted Ballot Bit Error Rate vs. Key QBER", fontsize=12, fontweight='bold')
    ax1.set_xlabel("Key QBER (%)", fontsize=11)
    ax1.set_ylabel("Decrypted Ballot Bit Error Rate (%)", fontsize=11)
    ax1.legend(loc='upper left')
    ax1.grid(True, linestyle='--', alpha=0.6)

    ax2.plot(qbers, corruptions, marker='s', color='crimson', linewidth=2.5, label='16-bit Ballot Corruption Rate')
    ax2.axvline(11.0, color='darkred', linestyle='--', label='11% Abort Threshold')
    ax2.set_title("Vote Invalidation Probability vs. Unchecked QBER", fontsize=12, fontweight='bold')
    ax2.set_xlabel("Key QBER (%)", fontsize=11)
    ax2.set_ylabel("Corrupted Ballot Probability (%)", fontsize=11)
    ax2.set_ylim(-5, 105)
    ax2.legend(loc='center right')
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plot3_path = os.path.join(output_dir, "eval_plot3_encryption_qber_impact.png")
    plt.savefig(plot3_path, dpi=300)
    plt.close()
    print(f"Saved: {plot3_path}")

    # -------------------------------------------------------------------------
    # Plot 4: Sample QBER vs Key QBER Difference
    # -------------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    # Error vs Sample Ratio for different Key Sizes
    ratios = [10, 20, 33, 50]
    for k_size in [64, 128, 256, 512]:
        mae_vals = [exp4_res[str(k_size)][f"sample_{r}pct"]["mean_abs_diff"] for r in ratios]
        ax1.plot(ratios, mae_vals, marker='o', linewidth=2.0, label=f"Sifted Key = {k_size} bits")

    ax1.set_title("Mean Estimation Error (|Delta QBER|) vs. Check Sample Ratio", fontsize=12, fontweight='bold')
    ax1.set_xlabel("Sample Check Ratio (%)", fontsize=11)
    ax1.set_ylabel("Mean |QBER_sample - QBER_key| (%)", fontsize=11)
    ax1.legend(loc='upper right')
    ax1.grid(True, linestyle='--', alpha=0.6)

    # Scatter of Sample QBER vs Key QBER for 256 bits, 33% sample
    sample_qbers = exp4_res["256"]["sample_33pct"]["sample_qbers"]
    key_qbers = exp4_res["256"]["sample_33pct"]["key_qbers"]

    ax2.scatter(sample_qbers, key_qbers, color='teal', alpha=0.7, edgecolors='none', label='Trials (256 bits, 33% sample)')
    ax2.plot([15, 35], [15, 35], color='red', linestyle='--', label='Unbiased Estimator (y = x)')
    ax2.set_title("Correlation: Check Sample QBER vs. Secret Key QBER", fontsize=12, fontweight='bold')
    ax2.set_xlabel("Sample QBER (%)", fontsize=11)
    ax2.set_ylabel("Secret Key QBER (%)", fontsize=11)
    ax2.legend(loc='upper left')
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plot4_path = os.path.join(output_dir, "eval_plot4_sample_vs_key_qber.png")
    plt.savefig(plot4_path, dpi=300)
    plt.close()
    print(f"Saved: {plot4_path}")


# ==============================================================================
# Main Runner
# ==============================================================================

def main():
    set_seed(42)
    start_time = time.time()

    print("=" * 80)
    print("STARTING QKD & VOTING SIMULATION EVALUATION SUITE")
    print("=" * 80)

    # 1. Key length requirements
    exp1_res = evaluate_key_length_requirements(
        target_key_lengths=[32, 64, 128, 256],
        multipliers=[1.0, 1.5, 2.0, 2.2, 2.5, 3.0, 3.5, 4.0],
        sample_ratios=[0.0, 0.25, 0.33],
        trials=150
    )

    # 2. Eavesdropping and threshold
    exp2_res = evaluate_eavesdropping_and_threshold(
        key_size=128,
        trials=200,
        noise_levels=[0.0, 0.02, 0.04],
        eve_intercept_rates=[0.25, 0.50, 0.75, 1.0]
    )

    # 3. Encryption / Decryption verification
    exp3_res = evaluate_encryption_decryption(trials=500)

    # 4. Difference between sample QBER and key QBER
    exp4_res = evaluate_qber_sample_vs_key(
        key_sizes=[64, 128, 256, 512],
        sample_ratios=[0.10, 0.20, 0.33, 0.50],
        trials=250,
        has_eavesdropping=True
    )

    # Output directories
    eval_plots_dir = os.path.join(CURRENT_DIR, "plots")
    report_figures_dir = os.path.abspath(os.path.join(SRC_DIR, "..", "..", "report", "figures"))

    # Generate plots in both eval directory and report figures
    generate_plots(exp1_res, exp2_res, exp3_res, exp4_res, eval_plots_dir)
    generate_plots(exp1_res, exp2_res, exp3_res, exp4_res, report_figures_dir)

    # Save complete JSON summary
    summary = {
        "execution_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_seconds": round(time.time() - start_time, 2),
        "experiment_1_key_lengths": exp1_res,
        "experiment_2_eavesdropping_and_threshold": {
            "clean_summary": exp2_res["clean_summary"],
            "eve_summary": exp2_res["eve_summary"],
            "threshold_metrics": exp2_res["threshold_metrics"],
            "best_threshold": exp2_res["best_threshold"],
            "best_f1": exp2_res["best_f1"]
        },
        "experiment_3_encryption_decryption": exp3_res,
        "experiment_4_sample_vs_key_qber": {
            k: {
                rk: {
                    m: rv[m] for m in ["sample_ratio", "mean_abs_diff", "rmse", "signed_mean", "std_diff", "correlation"]
                } for rk, rv in v.items()
            } for k, v in exp4_res.items()
        }
    }

    json_path = os.path.join(CURRENT_DIR, "evaluation_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print(f"EVALUATION COMPLETE in {time.time() - start_time:.2f} seconds!")
    print(f"Summary JSON saved to: {json_path}")
    print(f"Plots saved to: {eval_plots_dir} and {report_figures_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
