"""
Evaluation Suite specifically modeling the 1:1 Symmetric Case:
- Key Length = n bits
- Check Bits = n bits
- Total Sifted Bits Required = 2n bits

Covers all 4 requirements under this exact condition:
1. Transmission length: N_raw needed to yield n secret bits + n check bits (2n total)
2. Eavesdropping detection & optimal threshold when using n check bits
3. Encryption/decryption of n-bit ballot with n-bit key
4. Difference between QBER_sample (n bits) and QBER_key (n bits)
"""

import os
import sys
import math
import json
import random
import time
from typing import Dict, List, Tuple, Any

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)

def run_bb84_equal_n(
    raw_qubits: int,
    n: int,
    has_eavesdropping: bool = False,
    channel_noise: float = 0.0,
    eve_intercept_rate: float = 1.0
) -> Dict[str, Any]:
    """
    Run BB84 simulation:
    Attempts to get at least 2n sifted bits, then splits exactly into:
    - n bits for check/sample
    - n bits for final secret key
    """
    alice_bits = [random.choice(['0', '1']) for _ in range(raw_qubits)]
    alice_bases = [random.choice(['0', '1']) for _ in range(raw_qubits)]
    bob_bases = [random.choice(['0', '1']) for _ in range(raw_qubits)]

    bob_read = []
    for i in range(raw_qubits):
        bit = alice_bits[i]
        a_base = alice_bases[i]
        b_base = bob_bases[i]

        if has_eavesdropping and (random.random() < eve_intercept_rate):
            eve_base = random.choice(['0', '1'])
            eve_bit = bit if eve_base == a_base else random.choice(['0', '1'])
            sent_bit = eve_bit
            sent_base = eve_base
        else:
            sent_bit = bit
            sent_base = a_base

        if b_base == sent_base:
            measured_bit = sent_bit
        else:
            measured_bit = random.choice(['0', '1'])

        if channel_noise > 0.0 and random.random() < channel_noise:
            measured_bit = '1' if measured_bit == '0' else '0'

        bob_read.append(measured_bit)

    # Sifting
    sifted_alice = []
    sifted_bob = []
    for i in range(raw_qubits):
        if alice_bases[i] == bob_bases[i]:
            sifted_alice.append(alice_bits[i])
            sifted_bob.append(bob_read[i])

    sifted_len = len(sifted_alice)
    has_sufficient_bits = (sifted_len >= 2 * n)

    if sifted_len < 2:
        return {
            "sifted_len": sifted_len,
            "has_sufficient_bits": False,
            "sample_qber": 0.0,
            "key_qber": 0.0,
            "qber_diff": 0.0,
            "signed_diff": 0.0,
            "alice_key": "",
            "bob_key": ""
        }

    # Split into n check bits and n key bits (if sifted_len >= 2n, take exactly n each; otherwise half-half)
    actual_n = min(n, sifted_len // 2)
    all_indices = list(range(sifted_len))
    random.shuffle(all_indices)

    check_idx = all_indices[:actual_n]
    key_idx = all_indices[actual_n: 2 * actual_n]

    # Sample QBER (on n check bits)
    check_errors = sum(1 for i in check_idx if sifted_alice[i] != sifted_bob[i])
    sample_qber = (check_errors / actual_n) * 100.0 if actual_n > 0 else 0.0

    # Key QBER (on n secret key bits)
    key_errors = sum(1 for i in key_idx if sifted_alice[i] != sifted_bob[i])
    key_qber = (key_errors / actual_n) * 100.0 if actual_n > 0 else 0.0

    alice_key = "".join(sifted_alice[i] for i in key_idx)
    bob_key = "".join(sifted_bob[i] for i in key_idx)

    return {
        "raw_qubits": raw_qubits,
        "sifted_len": sifted_len,
        "n_target": n,
        "actual_check_bits": actual_n,
        "actual_key_bits": len(key_idx),
        "has_sufficient_bits": has_sufficient_bits,
        "sample_qber": sample_qber,
        "key_qber": key_qber,
        "qber_diff": abs(sample_qber - key_qber),
        "signed_diff": sample_qber - key_qber,
        "alice_key": alice_key,
        "bob_key": bob_key
    }

def main():
    set_seed(42)
    start_time = time.time()

    print("=" * 80)
    print("EVALUATION: KEY = n BITS, CHECK BITS = n BITS (TOTAL SIFTED = 2n BITS)")
    print("=" * 80)

    test_ns = [32, 64, 128, 256]
    trials = 300

    # -------------------------------------------------------------------------
    # PART 1: Raw Qubit Multipliers for Equal n Key + n Check (2n total)
    # -------------------------------------------------------------------------
    print("\n--- PART 1: Raw Transmission Size (N_raw) vs. n Bits (Key=n, Check=n, Total=2n) ---")
    print("Multipliers tested as Ratio of n: 4.0x (mean expected), 4.4x, 4.8x, 5.0x")
    print(f"{'n bits':<8} | {'Total Req (2n)':<16} | {'Multiplier':<12} | {'Raw Sent':<10} | {'Success Rate (%)':<18}")
    print("-" * 75)

    part1_data = {}
    multipliers = [3.5, 4.0, 4.4, 4.8, 5.0]

    for n in test_ns:
        part1_data[str(n)] = []
        for mult in multipliers:
            raw_sent = int(round(n * mult))
            success = 0
            for _ in range(trials):
                res = run_bb84_equal_n(raw_sent, n, has_eavesdropping=False)
                if res["has_sufficient_bits"]:
                    success += 1
            sr = (success / trials) * 100.0
            part1_data[str(n)].append({
                "multiplier": mult,
                "raw_sent": raw_sent,
                "success_rate": round(sr, 1)
            })
            if mult in [4.0, 4.4, 4.8]:
                print(f"{n:<8} | {2*n:<16} | {mult:<12.1f} | {raw_sent:<10} | {sr:<18.1f}")

    # -------------------------------------------------------------------------
    # PART 2: Eavesdropping Detection Sensitivity using n Check Bits
    # -------------------------------------------------------------------------
    print("\n--- PART 2: Eavesdropping Detection & False Alarm (using n check bits) ---")
    print("Abort Threshold = 11.0% QBER")
    print(f"{'n bits':<8} | {'Clean FPR (2% noise)':<22} | {'Eve TPR (100% Eve)':<20} | {'Eve TPR (50% Eve)':<20}")
    print("-" * 75)

    part2_data = {}
    for n in test_ns:
        raw_qubits = int(round(n * 4.8))
        clean_qbers = []
        eve100_qbers = []
        eve50_qbers = []

        for _ in range(trials):
            res_c = run_bb84_equal_n(raw_qubits, n, has_eavesdropping=False, channel_noise=0.02)
            clean_qbers.append(res_c["sample_qber"])

            res_e100 = run_bb84_equal_n(raw_qubits, n, has_eavesdropping=True, eve_intercept_rate=1.0)
            eve100_qbers.append(res_e100["sample_qber"])

            res_e50 = run_bb84_equal_n(raw_qubits, n, has_eavesdropping=True, eve_intercept_rate=0.5)
            eve50_qbers.append(res_e50["sample_qber"])

        th = 11.0
        fpr = (sum(1 for q in clean_qbers if q > th) / trials) * 100.0
        tpr100 = (sum(1 for q in eve100_qbers if q > th) / trials) * 100.0
        tpr50 = (sum(1 for q in eve50_qbers if q > th) / trials) * 100.0

        part2_data[str(n)] = {
            "n": n,
            "fpr": round(fpr, 2),
            "tpr100": round(tpr100, 2),
            "tpr50": round(tpr50, 2)
        }
        print(f"{n:<8} | {fpr:<22.2f} | {tpr100:<20.2f} | {tpr50:<20.2f}")

    # -------------------------------------------------------------------------
    # PART 3: OTP Encryption & Decryption of n-bit Ballots with n-bit Secret Key
    # -------------------------------------------------------------------------
    print("\n--- PART 3: Encryption & Decryption Verification (n-bit Key, n-bit Ballot) ---")
    correct_count = 0
    total_crypto_tests = 1000

    for _ in range(total_crypto_tests):
        cur_n = random.choice(test_ns)
        # Plaintext ballot of n bits
        ballot = "".join(random.choice(['0', '1']) for _ in range(cur_n))
        res = run_bb84_equal_n(int(cur_n * 4.8), cur_n, has_eavesdropping=False)
        while not res["has_sufficient_bits"]:
            res = run_bb84_equal_n(int(cur_n * 4.8), cur_n, has_eavesdropping=False)
        key = res["alice_key"][:cur_n]

        # OTP XOR Encrypt & Decrypt
        cipher = "".join(str(int(b) ^ int(k)) for b, k in zip(ballot, key))
        decrypted = "".join(str(int(c) ^ int(k)) for c, k in zip(cipher, key))

        if decrypted == ballot:
            correct_count += 1

    crypto_acc = (correct_count / total_crypto_tests) * 100.0
    print(f"Verified {total_crypto_tests} random n-bit ballots: {correct_count}/{total_crypto_tests} Passed ({crypto_acc:.2f}%)")

    # -------------------------------------------------------------------------
    # PART 4: Difference |QBER_check(n) - QBER_key(n)| in Symmetrical Case
    # -------------------------------------------------------------------------
    print("\n--- PART 4: Difference Between QBER of Check (n bits) and Key (n bits) ---")
    print(f"{'n bits':<8} | {'Mean Diff (|Delta QBER| %)':<28} | {'RMSE (%)':<12} | {'Signed Mean (%)':<18} | {'Theory SE (sqrt(2p(1-p)/n) %)':<30}")
    print("-" * 105)

    part4_data = {}
    p = 0.25  # 100% intercept-resend error probability

    for n in [16, 32, 64, 128, 256, 512]:
        raw_qubits = int(round(n * 4.8))
        diffs = []
        signed_diffs = []

        for _ in range(500):
            res = run_bb84_equal_n(raw_qubits, n, has_eavesdropping=True, eve_intercept_rate=1.0)
            diffs.append(res["qber_diff"])
            signed_diffs.append(res["signed_diff"])

        mean_diff = float(np.mean(diffs))
        rmse = float(np.sqrt(np.mean(np.array(diffs)**2)))
        signed_mean = float(np.mean(signed_diffs))
        # Theoretical SE for difference of two independent n-sample estimators:
        # Var(sample - key) = Var(sample) + Var(key) = p(1-p)/n + p(1-p)/n = 2p(1-p)/n
        theo_se = math.sqrt(2.0 * p * (1.0 - p) / n) * 100.0
        # Expected absolute difference for normal approximation: sigma * sqrt(2/pi)
        theo_mae = theo_se * math.sqrt(2.0 / math.pi)

        part4_data[str(n)] = {
            "n": n,
            "mean_abs_diff": round(mean_diff, 2),
            "rmse": round(rmse, 2),
            "signed_mean": round(signed_mean, 2),
            "theo_se": round(theo_se, 2),
            "theo_mae": round(theo_mae, 2)
        }
        print(f"{n:<8} | {mean_diff:<28.2f} | {rmse:<12.2f} | {signed_mean:<18.2f} | {theo_se:<30.2f}")

    # -------------------------------------------------------------------------
    # Plots Generation
    # -------------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    # Plot 1: Key Success Rate vs Multiplier
    for n in test_ns:
        mults = [e["multiplier"] for e in part1_data[str(n)]]
        srs = [e["success_rate"] for e in part1_data[str(n)]]
        ax1.plot(mults, srs, marker='o', linewidth=2.2, label=f"n = {n} bits (2n = {2*n})")

    ax1.axhline(99.0, color='red', linestyle='--', label='99% Target Reliability')
    ax1.axvline(4.8, color='gray', linestyle=':', label='Recommended 4.8x Multiplier')
    ax1.set_title("Success Rate of Getting (n Key + n Check) Bits vs. Raw Multiplier", fontsize=12, fontweight='bold')
    ax1.set_xlabel("Transmission Multiplier (N_raw / n)", fontsize=11)
    ax1.set_ylabel("P(Sifted >= 2n) (%)", fontsize=11)
    ax1.set_ylim(-5, 105)
    ax1.legend(loc='lower right')
    ax1.grid(True, linestyle='--', alpha=0.6)

    # Plot 2: Error Difference |QBER_check - QBER_key| vs n
    eval_ns = [16, 32, 64, 128, 256, 512]
    emp_maes = [part4_data[str(n)]["mean_abs_diff"] for n in eval_ns]
    emp_rmses = [part4_data[str(n)]["rmse"] for n in eval_ns]
    th_ses = [part4_data[str(n)]["theo_se"] for n in eval_ns]
    th_maes = [part4_data[str(n)]["theo_mae"] for n in eval_ns]

    ax2.plot(eval_ns, emp_maes, marker='o', color='royalblue', linewidth=2.4, label='Empirical Mean |QBER_check - QBER_key|')
    ax2.plot(eval_ns, th_maes, linestyle='--', color='crimson', linewidth=2.0, label='Theoretical MAE: sqrt(4p(1-p)/(pi*n))')
    ax2.plot(eval_ns, emp_rmses, marker='s', color='darkgreen', linewidth=2.0, label='Empirical RMSE')
    ax2.plot(eval_ns, th_ses, linestyle=':', color='black', linewidth=1.8, label='Theoretical SE: sqrt(2p(1-p)/n)')

    ax2.set_title("Difference Between Check QBER and Key QBER vs. n\n(Both Sample & Secret Key Have Size n)", fontsize=12, fontweight='bold')
    ax2.set_xlabel("Key and Check Bit Size (n)", fontsize=11)
    ax2.set_ylabel("Error (%)", fontsize=11)
    ax2.legend(loc='upper right')
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()

    plot_paths = [
        os.path.join(CURRENT_DIR, "plots", "eval_plot_equal_n.png"),
        os.path.abspath(os.path.join(SRC_DIR, "..", "..", "report", "figures", "eval_plot_equal_n.png")),
        os.path.abspath(os.path.join(SRC_DIR, "..", "..", "report", "eval_plot_equal_n.png"))
    ]

    for p in plot_paths:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        plt.savefig(p, dpi=300)

    plt.close()

    summary_file = os.path.join(CURRENT_DIR, "equal_n_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump({
            "part1_multipliers": part1_data,
            "part2_eavesdropping": part2_data,
            "part3_crypto_accuracy": crypto_acc,
            "part4_diff_metrics": part4_data
        }, f, indent=2)

    print(f"\nSaved plots to: {plot_paths[0]}")
    print(f"Saved summary JSON to: {summary_file}")
    print(f"Execution completed in {time.time() - start_time:.2f} seconds!")

if __name__ == "__main__":
    main()
