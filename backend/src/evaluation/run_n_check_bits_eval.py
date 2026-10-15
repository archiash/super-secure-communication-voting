"""
Evaluation Suite specifically modeling FIXED 'n' check bits for eavesdropping verification.

Covers:
1. Transmission length requirement: N_raw needed for L_target when using n check bits
2. Eavesdropping detection sensitivity & false alarm rate as a function of n check bits
3. Encryption/decryption verification using remaining (L_sifted - n) secret key bits
4. Measurement of |QBER_sample - QBER_key| as a direct function of n check bits
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

def run_bb84_fixed_n_check(
    raw_qubits: int,
    n_check_bits: int,
    has_eavesdropping: bool = False,
    channel_noise: float = 0.0,
    eve_intercept_rate: float = 1.0
) -> Dict[str, Any]:
    """
    Run BB84 simulation, sift matching bases, and extract exactly n check bits
    for QBER verification, leaving the rest as secret key.
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

    # Total sifted QBER
    if sifted_len > 0:
        total_errors = sum(1 for a, b in zip(sifted_alice, sifted_bob) if a != b)
        total_qber = (total_errors / sifted_len) * 100.0
    else:
        total_qber = 0.0

    # Extract exactly n check bits
    actual_n = min(n_check_bits, sifted_len)
    all_indices = list(range(sifted_len))
    random.shuffle(all_indices)
    check_idx = set(all_indices[:actual_n])
    key_idx = [i for i in range(sifted_len) if i not in check_idx]

    # Sample QBER on n check bits
    if actual_n > 0:
        check_errors = sum(1 for i in check_idx if sifted_alice[i] != sifted_bob[i])
        sample_qber = (check_errors / actual_n) * 100.0
    else:
        sample_qber = total_qber

    # Secret Key QBER on remaining bits
    key_len = len(key_idx)
    if key_len > 0:
        key_errors = sum(1 for i in key_idx if sifted_alice[i] != sifted_bob[i])
        key_qber = (key_errors / key_len) * 100.0
        alice_key = "".join(sifted_alice[i] for i in key_idx)
        bob_key = "".join(sifted_bob[i] for i in key_idx)
    else:
        key_qber = total_qber
        alice_key = ""
        bob_key = ""

    return {
        "raw_qubits": raw_qubits,
        "sifted_len": sifted_len,
        "n_check_bits": actual_n,
        "key_len": key_len,
        "total_qber": total_qber,
        "sample_qber": sample_qber,
        "key_qber": key_qber,
        "qber_diff": abs(sample_qber - key_qber),
        "signed_diff": sample_qber - key_qber,
        "alice_key": alice_key,
        "bob_key": bob_key
    }


def evaluate_n_check_bits_suite():
    set_seed(42)
    start_time = time.time()

    print("=" * 80)
    print("EVALUATION SUITE: ASSUMING 'n' BITS FOR CHECK BITS")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # Part 1: Required Raw Transmission vs (L_target + n)
    # -------------------------------------------------------------------------
    print("\n--- PART 1: Raw Qubit Transmission Size vs. (L_target + n check bits) ---")
    print("Formula: N_raw >= 2*(L_target + n) + z * sqrt(L_target + n) for high reliability")
    print(f"{'Target (L)':<10} | {'Check (n)':<10} | {'Total Req':<10} | {'Raw Sent':<10} | {'Mean Final':<12} | {'Success Rate (%)':<16}")
    print("-" * 75)

    part1_results = []
    scenarios = [
        (64, 16),
        (64, 32),
        (64, 64),
        (128, 32),
        (128, 64),
        (256, 64),
        (256, 128)
    ]

    for l_target, n_check in scenarios:
        total_req = l_target + n_check
        # Multipliers on total required bits (2.0x is theoretical mean, 2.3x adds 99% safety margin)
        for mult in [2.0, 2.2, 2.4]:
            raw_qubits = int(math.ceil(total_req * mult))
            success = 0
            finals = []
            for _ in range(200):
                res = run_bb84_fixed_n_check(raw_qubits, n_check, has_eavesdropping=False)
                finals.append(res["key_len"])
                if res["key_len"] >= l_target:
                    success += 1

            sr = (success / 200.0) * 100.0
            mean_final = float(np.mean(finals))
            part1_results.append({
                "l_target": l_target,
                "n_check": n_check,
                "total_req": total_req,
                "multiplier": mult,
                "raw_qubits": raw_qubits,
                "mean_final": round(mean_final, 1),
                "success_rate": round(sr, 1)
            })
            if mult in [2.0, 2.4]:
                print(f"{l_target:<10} | {n_check:<10} | {total_req:<10} | {raw_qubits:<10} | {mean_final:<12.1f} | {sr:<16.1f}")

    # -------------------------------------------------------------------------
    # Part 2: Eavesdropping Detection Sensitivity vs n Check Bits
    # -------------------------------------------------------------------------
    print("\n--- PART 2: Eavesdropping Detection & False Alarm vs. n Check Bits ---")
    print("Testing n in {16, 32, 64, 128} bits with 11% QBER Abort Threshold")
    print(f"{'n Check Bits':<14} | {'Clean FPR (2% noise)':<22} | {'Eve TPR (100% Eve)':<20} | {'Eve TPR (50% Eve)':<20}")
    print("-" * 80)

    n_values = [16, 32, 64, 128]
    part2_results = {}

    for n in n_values:
        clean_qbers = []
        eve100_qbers = []
        eve50_qbers = []

        raw = (256 + n) * 2
        for _ in range(300):
            res_clean = run_bb84_fixed_n_check(raw, n, has_eavesdropping=False, channel_noise=0.02)
            clean_qbers.append(res_clean["sample_qber"])

            res_eve100 = run_bb84_fixed_n_check(raw, n, has_eavesdropping=True, eve_intercept_rate=1.0)
            eve100_qbers.append(res_eve100["sample_qber"])

            res_eve50 = run_bb84_fixed_n_check(raw, n, has_eavesdropping=True, eve_intercept_rate=0.5)
            eve50_qbers.append(res_eve50["sample_qber"])

        th = 11.0
        fpr = (sum(1 for q in clean_qbers if q > th) / len(clean_qbers)) * 100.0
        tpr100 = (sum(1 for q in eve100_qbers if q > th) / len(eve100_qbers)) * 100.0
        tpr50 = (sum(1 for q in eve50_qbers if q > th) / len(eve50_qbers)) * 100.0

        part2_results[str(n)] = {
            "n": n,
            "fpr": round(fpr, 2),
            "tpr100": round(tpr100, 2),
            "tpr50": round(tpr50, 2),
            "clean_mean": round(float(np.mean(clean_qbers)), 2),
            "clean_std": round(float(np.std(clean_qbers)), 2),
            "eve100_mean": round(float(np.mean(eve100_qbers)), 2),
            "eve100_std": round(float(np.std(eve100_qbers)), 2)
        }

        print(f"{n:<14} | {fpr:<22.2f} | {tpr100:<20.2f} | {tpr50:<20.2f}")

    # -------------------------------------------------------------------------
    # Part 3: Difference |QBER_sample - QBER_key| as function of n Check Bits
    # -------------------------------------------------------------------------
    print("\n--- PART 3: |QBER_sample - QBER_key| as a Function of n Check Bits ---")
    print(f"{'n Check Bits':<14} | {'Mean Diff (|Delta QBER| %)':<28} | {'RMSE (%)':<12} | {'Theoretical SE (%)':<20}")
    print("-" * 80)

    part3_results = {}
    check_ns = [16, 32, 64, 128, 256]

    for n in check_ns:
        diffs = []
        signed_diffs = []
        sample_qbers = []
        key_qbers = []

        raw = (256 + n) * 2
        for _ in range(400):
            res = run_bb84_fixed_n_check(raw, n, has_eavesdropping=True)
            diffs.append(res["qber_diff"])
            signed_diffs.append(res["signed_diff"])
            sample_qbers.append(res["sample_qber"])
            key_qbers.append(res["key_qber"])

        mean_diff = float(np.mean(diffs))
        rmse = float(np.sqrt(np.mean(np.array(diffs)**2)))
        signed_mean = float(np.mean(signed_diffs))
        # Theoretical SE for p = 0.25 (100% Eve): sqrt(0.25 * 0.75 / n) * 100
        theo_se = math.sqrt(0.25 * 0.75 / n) * 100.0

        part3_results[str(n)] = {
            "n": n,
            "mean_abs_diff": round(mean_diff, 2),
            "rmse": round(rmse, 2),
            "signed_mean": round(signed_mean, 2),
            "theo_se": round(theo_se, 2)
        }

        print(f"{n:<14} | {mean_diff:<28.2f} | {rmse:<12.2f} | {theo_se:<20.2f}")

    # -------------------------------------------------------------------------
    # Generate Dedicated Plots for n check bits
    # -------------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    # Subplot 1: Estimation Error vs n check bits
    ns = [p["n"] for p in part3_results.values()]
    maes = [p["mean_abs_diff"] for p in part3_results.values()]
    theos = [p["theo_se"] for p in part3_results.values()]

    ax1.plot(ns, maes, marker='o', color='royalblue', linewidth=2.4, label='Empirical Mean |QBER_sample - QBER_key|')
    ax1.plot(ns, theos, marker='s', linestyle='--', color='crimson', linewidth=2.0, label='Theoretical SE: sqrt(p(1-p)/n)')
    ax1.set_title("QBER Estimation Error vs. Number of Check Bits (n)\n(Eve 100% Intercept-Resend)", fontsize=12, fontweight='bold')
    ax1.set_xlabel("Number of Check Bits (n)", fontsize=11)
    ax1.set_ylabel("Error (%)", fontsize=11)
    ax1.legend(loc='upper right')
    ax1.grid(True, linestyle='--', alpha=0.6)

    # Subplot 2: Detection Rate (TPR) and False Alarm Rate (FPR) vs n check bits
    n_pts = [part2_results[str(n)]["n"] for n in n_values]
    tpr_100 = [part2_results[str(n)]["tpr100"] for n in n_values]
    tpr_50 = [part2_results[str(n)]["tpr50"] for n in n_values]
    fpr_vals = [part2_results[str(n)]["fpr"] for n in n_values]

    ax2.plot(n_pts, tpr_100, marker='^', color='green', linewidth=2.2, label='Detection: 100% Eve (Threshold = 11%)')
    ax2.plot(n_pts, tpr_50, marker='D', color='orange', linewidth=2.2, label='Detection: 50% Eve (Threshold = 11%)')
    ax2.plot(n_pts, fpr_vals, marker='x', color='red', linestyle='--', linewidth=2.0, label='False Alarm Rate (2% Noise)')
    ax2.axhline(99.0, color='gray', linestyle=':', label='99% Target Reliability')
    ax2.set_title("Eavesdropping Detection Sensitivity vs. n Check Bits", fontsize=12, fontweight='bold')
    ax2.set_xlabel("Number of Check Bits (n)", fontsize=11)
    ax2.set_ylabel("Rate (%)", fontsize=11)
    ax2.set_ylim(-5, 105)
    ax2.legend(loc='center right')
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plot_file = os.path.join(CURRENT_DIR, "plots", "eval_plot_n_check_bits.png")
    report_plot_file = os.path.abspath(os.path.join(SRC_DIR, "..", "..", "report", "figures", "eval_plot_n_check_bits.png"))
    report_root_plot_file = os.path.abspath(os.path.join(SRC_DIR, "..", "..", "report", "eval_plot_n_check_bits.png"))

    plt.savefig(plot_file, dpi=300)
    plt.savefig(report_plot_file, dpi=300)
    plt.savefig(report_root_plot_file, dpi=300)
    plt.close()

    print(f"\nSaved plots to: {plot_file}")

    # Output JSON summary
    summary = {
        "part1_transmission_requirements": part1_results,
        "part2_eavesdropping_vs_n": part2_results,
        "part3_diff_vs_n": part3_results
    }
    json_path = os.path.join(CURRENT_DIR, "n_check_bits_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved summary JSON to: {json_path}")
    print(f"Total time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    evaluate_n_check_bits_suite()
