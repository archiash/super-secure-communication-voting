"""
Benchmark and Evaluation Suite: 3 Separate Visualizations according to the Test Rubric (1, 2, 4).
Condition: Secret Key = n bits, Check Bits = n bits (Total sifted = 2n bits).
Each test configuration runs exactly 100x repetitions.

3 Standalone Pictures:
1. test_rubric_1_key_length_sufficiency.png
2. test_rubric_2_eavesdropping_threshold.png
3. test_rubric_4_qber_sample_vs_key_difference.png
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

def run_bb84_simulation(
    raw_qubits: int,
    n: int,
    has_eavesdropping: bool = False,
    channel_noise: float = 0.0,
    eve_intercept_rate: float = 1.0
) -> Dict[str, Any]:
    """
    BB84 Quantum Key Distribution Simulation:
    - Alice prepares qubits in random bit and basis
    - Eve optionally intercepts (intercept-resend)
    - Bob measures in random basis
    - Basis sifting
    - Splits sifted bits into n check bits and n key bits (if >= 2n)
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

    actual_n = min(n, sifted_len // 2)
    all_indices = list(range(sifted_len))
    random.shuffle(all_indices)

    check_idx = all_indices[:actual_n]
    key_idx = all_indices[actual_n: 2 * actual_n]

    # Sample QBER on n check bits
    check_errors = sum(1 for i in check_idx if sifted_alice[i] != sifted_bob[i])
    sample_qber = (check_errors / actual_n) * 100.0 if actual_n > 0 else 0.0

    # Secret Key QBER on n secret key bits
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


def save_plot_to_destinations(fig, filename: str, output_dirs: List[str]):
    for d in output_dirs:
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, filename)
        fig.savefig(path, dpi=300, bbox_inches='tight')
    print(f"Saved plot: {filename} to all destinations.")


# ==============================================================================
# TEST 1: Key Transmission Length Optimization (100x runs)
# ==============================================================================
def run_test_1(output_dirs: List[str], trials: int = 100) -> Dict[str, Any]:
    print("\n" + "="*80)
    print("RUBRIC TEST 1: Key Transmission Length Evaluation (100x runs per config)")
    print("Condition: Key = n bits, Check = n bits, Total Required Sifted = 2n bits")
    print("="*80)

    test_ns = [32, 64, 128, 256]
    multipliers = [3.0, 3.5, 4.0, 4.4, 4.8, 5.2]
    results = {}

    print(f"{'n (bits)':<10} | {'Total Req (2n)':<16} | {'Multiplier':<12} | {'Raw Bits':<10} | {'Success Rate (%)':<16} | {'Mean Usable Key':<16}")
    print("-" * 85)

    for n in test_ns:
        results[str(n)] = []
        for mult in multipliers:
            raw_sent = int(round(n * mult))
            success = 0
            final_keys = []

            for _ in range(trials):
                res = run_bb84_simulation(raw_sent, n, has_eavesdropping=False)
                if res["has_sufficient_bits"]:
                    success += 1
                final_keys.append(res["actual_key_bits"])

            sr = (success / trials) * 100.0
            mean_key = float(np.mean(final_keys))
            entry = {
                "multiplier": mult,
                "raw_sent": raw_sent,
                "success_rate": round(sr, 1),
                "mean_usable_key": round(mean_key, 1)
            }
            results[str(n)].append(entry)
            print(f"{n:<10} | {2*n:<16} | {mult:<12.1f} | {raw_sent:<10} | {sr:<16.1f} | {mean_key:<16.1f}")

    # Generate Picture 1
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

    for i, n in enumerate(test_ns):
        mults = [e["multiplier"] for e in results[str(n)]]
        srs = [e["success_rate"] for e in results[str(n)]]
        ax1.plot(mults, srs, marker='o', linewidth=2.2, color=colors[i], label=f"n = {n} bits (Req 2n = {2*n})")

    ax1.axhline(99.0, color='red', linestyle='--', linewidth=1.8, label='99% Target Reliability')
    ax1.axvline(4.8, color='gray', linestyle=':', linewidth=2.0, label='Optimal Multiplier (4.8x)')
    ax1.set_title("Success Rate of Obtaining Sifted Key >= 2n vs. Raw Multiplier\n(100x Trials per Configuration)", fontsize=11, fontweight='bold')
    ax1.set_xlabel("Transmission Multiplier (N_raw / n)", fontsize=11)
    ax1.set_ylabel("Success Rate P(Sifted >= 2n) (%)", fontsize=11)
    ax1.set_ylim(-5, 105)
    ax1.legend(loc='lower right')
    ax1.grid(True, linestyle='--', alpha=0.6)

    # Subplot 2: Usable Key vs Raw bits
    for i, n in enumerate(test_ns):
        raws = [e["raw_sent"] for e in results[str(n)]]
        keys = [e["mean_usable_key"] for e in results[str(n)]]
        ax2.plot(raws, keys, marker='s', linewidth=2.0, color=colors[i], label=f"n = {n} bits")
        ax2.axhline(n, color=colors[i], linestyle=':', alpha=0.7)

    ax2.set_title("Mean Usable Secret Key Obtained vs. Raw Qubits Transmitted\n(After Deducting n Check Bits)", fontsize=11, fontweight='bold')
    ax2.set_xlabel("Raw Qubits Transmitted (N_raw)", fontsize=11)
    ax2.set_ylabel("Usable Secret Key (bits)", fontsize=11)
    ax2.legend(loc='upper left')
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    save_plot_to_destinations(fig, "test_rubric_1_key_length_sufficiency.png", output_dirs)
    plt.close()

    return results


# ==============================================================================
# TEST 2: Eavesdropping vs No-Eavesdropping & Detection Threshold (100x runs)
# ==============================================================================
def run_test_2(output_dirs: List[str], trials: int = 100) -> Dict[str, Any]:
    print("\n" + "="*80)
    print("RUBRIC TEST 2: Eavesdropping Detection & Optimal Threshold (100x runs per config)")
    print("Condition: Key = 64 bits, Check = 64 bits, Total Sifted = 128 bits")
    print("="*80)

    n = 64
    raw_qubits = int(round(n * 4.8))

    clean_qbers = []
    eve50_qbers = []
    eve100_qbers = []

    for _ in range(trials):
        # 1. Clean transmission with 2% channel noise
        res_clean = run_bb84_simulation(raw_qubits, n, has_eavesdropping=False, channel_noise=0.02)
        clean_qbers.append(res_clean["sample_qber"])

        # 2. 50% partial intercept Eve
        res_eve50 = run_bb84_simulation(raw_qubits, n, has_eavesdropping=True, channel_noise=0.02, eve_intercept_rate=0.5)
        eve50_qbers.append(res_eve50["sample_qber"])

        # 3. 100% full intercept Eve
        res_eve100 = run_bb84_simulation(raw_qubits, n, has_eavesdropping=True, channel_noise=0.02, eve_intercept_rate=1.0)
        eve100_qbers.append(res_eve100["sample_qber"])

    print(f"Clean Channel (2% noise): Mean QBER = {np.mean(clean_qbers):.2f}% +/- {np.std(clean_qbers):.2f}%")
    print(f"Partial Eve (50% Intercept): Mean QBER = {np.mean(eve50_qbers):.2f}% +/- {np.std(eve50_qbers):.2f}%")
    print(f"Full Eve (100% Intercept): Mean QBER = {np.mean(eve100_qbers):.2f}% +/- {np.std(eve100_qbers):.2f}%")

    # Threshold sweep from 1% to 25%
    thresholds = [round(t, 1) for t in np.arange(1.0, 26.0, 1.0)]
    th_metrics = []

    print(f"\n{'Threshold (%)':<15} | {'False Alarm (FPR %)':<22} | {'Detection (TPR %)':<20} | {'F1-Score':<10}")
    print("-" * 75)

    for th in thresholds:
        fp = sum(1 for q in clean_qbers if q > th)
        fpr = (fp / trials) * 100.0

        tp = sum(1 for q in eve100_qbers if q > th)
        tpr = (tp / trials) * 100.0

        fn = trials - tp
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        th_metrics.append({
            "threshold": th,
            "fpr": round(fpr, 2),
            "tpr": round(tpr, 2),
            "f1": round(f1, 4)
        })

        if th in [5.0, 8.0, 10.0, 11.0, 12.0, 15.0, 20.0]:
            print(f"{th:<15.1f} | {fpr:<22.2f} | {tpr:<20.2f} | {f1:<10.4f}")

    # Generate Picture 2
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    bins = np.linspace(0, 35, 36)
    ax1.hist(clean_qbers, bins=bins, alpha=0.65, color='#2ca02c', label='Clean Channel (2% Noise)', density=True)
    ax1.hist(eve50_qbers, bins=bins, alpha=0.55, color='#ff7f0e', label='Partial Eve (50% Intercept)', density=True)
    ax1.hist(eve100_qbers, bins=bins, alpha=0.65, color='#d62728', label='Full Eve (100% Intercept)', density=True)
    ax1.axvline(11.0, color='darkred', linestyle='--', linewidth=2.5, label='BB84 Threshold (11.0%)')
    ax1.set_title("QBER Distribution: Legitimate vs. Eavesdropped Channel\n(100x Trials, n = 64 Check Bits)", fontsize=11, fontweight='bold')
    ax1.set_xlabel("Measured QBER (%)", fontsize=11)
    ax1.set_ylabel("Probability Density", fontsize=11)
    ax1.legend(loc='upper right')
    ax1.grid(True, linestyle='--', alpha=0.6)

    # Subplot 2: Detection performance vs Threshold
    th_x = [m["threshold"] for m in th_metrics]
    fpr_y = [m["fpr"] for m in th_metrics]
    tpr_y = [m["tpr"] for m in th_metrics]
    f1_y = [m["f1"] * 100.0 for m in th_metrics]

    ax2.plot(th_x, tpr_y, color='#2ca02c', linewidth=2.4, label='Detection Rate (TPR %)')
    ax2.plot(th_x, fpr_y, color='#d62728', linewidth=2.4, label='False Alarm Rate (FPR %)')
    ax2.plot(th_x, f1_y, color='#1f77b4', linestyle='-.', linewidth=2.2, label='F1-Score (%)')
    ax2.axvline(11.0, color='darkred', linestyle='--', linewidth=2.0, label='Optimal Threshold (11.0%)')
    ax2.set_title("Detection Performance Across QBER Thresholds\n(TPR vs. FPR Trade-off)", fontsize=11, fontweight='bold')
    ax2.set_xlabel("QBER Abort Threshold (%)", fontsize=11)
    ax2.set_ylabel("Rate (%)", fontsize=11)
    ax2.set_ylim(-5, 105)
    ax2.legend(loc='center right')
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    save_plot_to_destinations(fig, "test_rubric_2_eavesdropping_threshold.png", output_dirs)
    plt.close()

    return {
        "clean_mean": float(np.mean(clean_qbers)),
        "clean_std": float(np.std(clean_qbers)),
        "eve100_mean": float(np.mean(eve100_qbers)),
        "eve100_std": float(np.std(eve100_qbers)),
        "threshold_metrics": th_metrics
    }



# ==============================================================================
# TEST 4: Difference Between QBER of Key and QBER of Sample (100x runs)
# ==============================================================================
def run_test_4(output_dirs: List[str], trials: int = 100) -> Dict[str, Any]:
    print("\n" + "="*80)
    print("RUBRIC TEST 4: Difference Between Sample QBER (n) and Key QBER (n) (100x runs)")
    print("Condition: Sample = n bits, Key = n bits (Symmetric Equal Size)")
    print("="*80)

    test_ns = [16, 32, 64, 128, 256, 512]
    p = 0.25  # 100% intercept Eve
    results = {}

    print(f"{'n bits':<8} | {'Mean Diff (|Delta QBER| %)':<28} | {'RMSE (%)':<12} | {'Signed Mean (%)':<18} | {'Theoretical SE (%)':<20}")
    print("-" * 90)

    scatter_sample = []
    scatter_key = []

    for n in test_ns:
        diffs = []
        signed_diffs = []
        raw_qubits = int(round(n * 4.8))

        for _ in range(trials):
            res = run_bb84_simulation(raw_qubits, n, has_eavesdropping=True, eve_intercept_rate=1.0)
            diffs.append(res["qber_diff"])
            signed_diffs.append(res["signed_diff"])

            if n == 64:
                scatter_sample.append(res["sample_qber"])
                scatter_key.append(res["key_qber"])

        mean_diff = float(np.mean(diffs))
        rmse = float(np.sqrt(np.mean(np.array(diffs)**2)))
        signed_mean = float(np.mean(signed_diffs))
        theo_se = math.sqrt(2.0 * p * (1.0 - p) / n) * 100.0
        theo_mae = theo_se * math.sqrt(2.0 / math.pi)

        results[str(n)] = {
            "n": n,
            "mean_abs_diff": round(mean_diff, 2),
            "rmse": round(rmse, 2),
            "signed_mean": round(signed_mean, 2),
            "theo_se": round(theo_se, 2),
            "theo_mae": round(theo_mae, 2)
        }
        print(f"{n:<8} | {mean_diff:<28.2f} | {rmse:<12.2f} | {signed_mean:<18.2f} | {theo_se:<20.2f}")

    # Generate Picture 4
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    ns = [results[str(n)]["n"] for n in test_ns]
    emp_diffs = [results[str(n)]["mean_abs_diff"] for n in test_ns]
    emp_rmses = [results[str(n)]["rmse"] for n in test_ns]
    th_ses = [results[str(n)]["theo_se"] for n in test_ns]
    th_maes = [results[str(n)]["theo_mae"] for n in test_ns]

    ax1.plot(ns, emp_diffs, marker='o', color='#1f77b4', linewidth=2.4, label='Empirical Mean |QBER_check - QBER_key|')
    ax1.plot(ns, th_maes, linestyle='--', color='#d62728', linewidth=2.0, label='Theoretical MAE: sqrt(4p(1-p)/(pi*n))')
    ax1.plot(ns, emp_rmses, marker='s', color='#2ca02c', linewidth=2.0, label='Empirical RMSE')
    ax1.plot(ns, th_ses, linestyle=':', color='black', linewidth=1.8, label='Theoretical SE: sqrt(2p(1-p)/n)')
    ax1.set_title("Estimation Difference vs. Bit Size (n)\n(100x Trials per Size n)", fontsize=11, fontweight='bold')
    ax1.set_xlabel("Key and Check Bit Size (n)", fontsize=11)
    ax1.set_ylabel("Error (%)", fontsize=11)
    ax1.legend(loc='upper right')
    ax1.grid(True, linestyle='--', alpha=0.6)

    # Subplot 2: Scatter plot of sample QBER vs key QBER for n = 64
    ax2.scatter(scatter_sample, scatter_key, color='#17becf', alpha=0.75, edgecolors='none', s=45, label='100 Trials (n = 64 bits)')
    ax2.plot([5, 45], [5, 45], color='red', linestyle='--', linewidth=2.0, label='Identity Line (y = x, Unbiased)')
    ax2.set_title("Correlation: Check QBER vs. Secret Key QBER (n = 64)\n(Confirming Unbiased Estimation)", fontsize=11, fontweight='bold')
    ax2.set_xlabel("Sample Check QBER (%)", fontsize=11)
    ax2.set_ylabel("Secret Key QBER (%)", fontsize=11)
    ax2.legend(loc='upper left')
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    save_plot_to_destinations(fig, "test_rubric_4_qber_sample_vs_key_difference.png", output_dirs)
    plt.close()

    return results


# ==============================================================================
# MAIN RUNNER
# ==============================================================================
def main():
    set_seed(42)
    start_time = time.time()

    output_dirs = [
        os.path.join(CURRENT_DIR, "plots"),
        os.path.abspath(os.path.join(SRC_DIR, "..", "..", "report", "figures")),
        os.path.abspath(os.path.join(SRC_DIR, "..", "..", "report"))
    ]

    print("=" * 80)
    print("STARTING EVALUATION SUITE (RUBRICS 1, 2, 4 - 100x RUNS EACH)")
    print("=" * 80)

    res1 = run_test_1(output_dirs, trials=100)
    res2 = run_test_2(output_dirs, trials=100)
    res4 = run_test_4(output_dirs, trials=100)

    summary = {
        "test_rubric_1": res1,
        "test_rubric_2": res2,
        "test_rubric_4": res4,
        "total_time_seconds": round(time.time() - start_time, 2)
    }

    json_path = os.path.join(CURRENT_DIR, "rubric_evaluation_100x_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 80)
    print(f"EVALUATION COMPLETE in {time.time() - start_time:.2f} seconds!")
    print(f"Summary JSON: {json_path}")
    print("Generated 3 Pictures:")
    print(" 1. test_rubric_1_key_length_sufficiency.png")
    print(" 2. test_rubric_2_eavesdropping_threshold.png")
    print(" 4. test_rubric_4_qber_sample_vs_key_difference.png")
    print("=" * 80)


if __name__ == "__main__":
    main()
