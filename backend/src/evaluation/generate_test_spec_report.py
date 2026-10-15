"""
Generate Presentation Deliverables & Key Metrics for TEST_SPEC.md:

1. Metric 1: Sifting & Key Sufficiency Table and Plot (Success rate vs delta in {0, 0.5, 1.0, 1.5, 2.0})
2. Metric 2: QBER Distribution Histogram & Bar Chart (Ideal, Noisy IBM, Eavesdropped vs 11% threshold)
3. Metric 3: Estimation Error Curve (|QBER_sample - QBER_key| vs qubit count 40 to 240)
4. Metric 4: Ballot Decryption Accuracy Table & Chart (Noisy QKD without vs with Error Correction)

Saves plots to:
- backend/src/evaluation/plots/
- report/
- report/figures/
"""

import os
import sys
import json
import shutil
import random
from typing import Dict, List, Any

# Ensure backend/src is in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from evaluation.test_spec import (
    run_bb84_trial,
    text_to_binary,
    binary_to_text,
    otp_encrypt,
    otp_decrypt
)

PLOTS_DIR = os.path.join(CURRENT_DIR, "plots")
REPORT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", "report"))
REPORT_FIG_DIR = os.path.join(REPORT_DIR, "figures")

os.makedirs(PLOTS_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(REPORT_FIG_DIR, exist_ok=True)


def save_plot_to_destinations(fig, filename: str):
    """Save plot to evaluation/plots, report/, and report/figures/."""
    p1 = os.path.join(PLOTS_DIR, filename)
    p2 = os.path.join(REPORT_DIR, filename)
    p3 = os.path.join(REPORT_FIG_DIR, filename)

    fig.savefig(p1, dpi=300, bbox_inches='tight')
    fig.savefig(p2, dpi=300, bbox_inches='tight')
    fig.savefig(p3, dpi=300, bbox_inches='tight')
    print(f"Saved plot: {filename} -> {PLOTS_DIR}, {REPORT_DIR}")


# ==============================================================================
# Deliverable 1: Sifting & Key Sufficiency Table and Plot
# ==============================================================================

def run_metric1_sifting_key_sufficiency(trials: int = 100) -> Dict[str, Any]:
    print("\n" + "="*80)
    print("DELIVERABLE 1: Sifting & Key Sufficiency (Target Key Length n = 24 bits)")
    print("="*80)

    n = 24
    deltas = [0.0, 0.5, 1.0, 1.5, 2.0]
    results_table = []

    for delta in deltas:
        multiplier = 4.0 + delta
        total_qubits = int(multiplier * n)

        trial_results = [
            run_bb84_trial(total_qubits=total_qubits, target_key_length=n, has_eavesdropping=False, channel_noise=0.0)
            for _ in range(trials)
        ]

        success_count = sum(1 for r in trial_results if r["final_key_len"] >= n)
        success_rate = (success_count / trials) * 100.0
        mean_sifted = float(np.mean([r["sifted_len"] for r in trial_results]))
        mean_final_key = float(np.mean([r["final_key_len"] for r in trial_results if r["final_key_len"] > 0])) if success_count > 0 else 0.0

        results_table.append({
            "delta": delta,
            "multiplier": multiplier,
            "total_qubits": total_qubits,
            "mean_sifted": round(mean_sifted, 1),
            "expected_sifted": round(total_qubits * 0.5, 1),
            "success_rate": round(success_rate, 1),
            "mean_final_key": round(mean_final_key, 1)
        })

    # Print ASCII Table
    print(f"{'Safety Margin (delta)':<22} | {'Multiplier':<12} | {'Total Qubits':<14} | {'Mean Sifted':<14} | {'Success Rate (%)':<18} | {'Status'}")
    print("-" * 95)
    for row in results_table:
        status = "PASSED (>=99%)" if row["success_rate"] >= 99.0 else ("PASSED (>=90%)" if row["success_rate"] >= 90.0 else f"Shortfall ({100-row['success_rate']:.1f}%)")
        print(f"delta = {row['delta']:<14.1f} | {row['multiplier']:<12.1f}x | {row['total_qubits']:<14} | {row['mean_sifted']:<14.1f} | {row['success_rate']:<18.1f} | {status}")

    # Generate Figure
    fig, ax = plt.subplots(figsize=(8, 5))
    x_vals = [r["delta"] for r in results_table]
    y_vals = [r["success_rate"] for r in results_table]

    bars = ax.bar(x_vals, y_vals, width=0.3, color='#1f77b4', edgecolor='black', alpha=0.85, label='Measured Success Rate')
    ax.plot(x_vals, y_vals, color='#d62728', marker='o', linewidth=2, label='Success Rate Curve')

    # Add threshold lines
    ax.axhline(90.0, color='orange', linestyle='--', linewidth=1.5, label='90% Reliability Goal (delta=1.0)')
    ax.axhline(99.0, color='green', linestyle='--', linewidth=1.5, label='99% Target Reliability (delta=2.0)')

    for bar, y in zip(bars, y_vals):
        ax.text(bar.get_x() + bar.get_width() / 2, y + 1.5, f"{y:.1f}%", ha='center', va='bottom', fontweight='bold', fontsize=10)

    ax.set_title("QKD Key Sufficiency vs. Safety Margin $\delta$ ($n = 24$ bits, 100 Trials)", fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel("Safety Margin $\delta$ in $N = (4 + \delta) \cdot n$", fontsize=11)
    ax.set_ylabel("First-Pass Key Generation Success Rate (%)", fontsize=11)
    ax.set_ylim(0, 110)
    ax.set_xticks(x_vals)
    ax.set_xticklabels([f"$\delta = {d:.1f}$\n({4+d:.1f}x, {int((4+d)*24)}Q)" for d in x_vals])
    ax.grid(axis='y', linestyle=':', alpha=0.6)
    ax.legend(loc='lower right', framealpha=0.9)

    save_plot_to_destinations(fig, "test_spec_metric1_sifting_key_sufficiency.png")
    plt.close(fig)

    return {"sifting_key_sufficiency": results_table}


# ==============================================================================
# Deliverable 2: QBER Distribution Histogram & Bar Chart
# ==============================================================================

def run_metric2_qber_distribution_threshold(trials: int = 100) -> Dict[str, Any]:
    print("\n" + "="*80)
    print("DELIVERABLE 2: QBER Distribution & Eavesdropping Threshold (11%)")
    print("="*80)

    total_qubits = 160
    n = 24
    threshold = 11.0

    # 1. Ideal Channel (No Eve)
    ideal_results = [
        run_bb84_trial(total_qubits=total_qubits, target_key_length=n, has_eavesdropping=False, channel_noise=0.0)
        for _ in range(trials)
    ]
    ideal_qbers = [r["sample_qber"] for r in ideal_results if not r["shortfall"]]

    # 2. Noisy Quantum Channel (No Eve, 2.5% noise)
    noisy_results = [
        run_bb84_trial(total_qubits=total_qubits, target_key_length=n, has_eavesdropping=False, channel_noise=0.025)
        for _ in range(trials)
    ]
    noisy_qbers = [r["sample_qber"] for r in noisy_results if not r["shortfall"]]

    # 3. Active Eve (Ideal Channel)
    eve_ideal_results = [
        run_bb84_trial(total_qubits=total_qubits, target_key_length=n, has_eavesdropping=True, channel_noise=0.0)
        for _ in range(trials)
    ]
    eve_ideal_qbers = [r["sample_qber"] for r in eve_ideal_results if not r["shortfall"]]

    # 4. Active Eve (Noisy Quantum Channel, 2.5% noise)
    eve_noisy_results = [
        run_bb84_trial(total_qubits=total_qubits, target_key_length=n, has_eavesdropping=True, channel_noise=0.025)
        for _ in range(trials)
    ]
    eve_noisy_qbers = [r["sample_qber"] for r in eve_noisy_results if not r["shortfall"]]

    metrics = [
        {"scenario": "Ideal Channel (No Eve)", "mean_qber": round(float(np.mean(ideal_qbers)), 2), "std_qber": round(float(np.std(ideal_qbers)), 2), "accepted_pct": 100.0, "expected": "0.0%"},
        {"scenario": "IBM Noisy Channel (No Eve)", "mean_qber": round(float(np.mean(noisy_qbers)), 2), "std_qber": round(float(np.std(noisy_qbers)), 2), "accepted_pct": round(sum(1 for q in noisy_qbers if q < threshold)/len(noisy_qbers)*100, 1), "expected": "1.0% - 5.0%"},
        {"scenario": "Active Eve (Ideal Channel)", "mean_qber": round(float(np.mean(eve_ideal_qbers)), 2), "std_qber": round(float(np.std(eve_ideal_qbers)), 2), "accepted_pct": round(sum(1 for q in eve_ideal_qbers if q < threshold)/len(eve_ideal_qbers)*100, 1), "expected": "~25.0%"},
        {"scenario": "Active Eve (Noisy Channel)", "mean_qber": round(float(np.mean(eve_noisy_qbers)), 2), "std_qber": round(float(np.std(eve_noisy_qbers)), 2), "accepted_pct": round(sum(1 for q in eve_noisy_qbers if q < threshold)/len(eve_noisy_qbers)*100, 1), "expected": "25.0% - 28.0%"}
    ]

    print(f"{'Scenario':<30} | {'Expected QBER':<15} | {'Mean QBER (%)':<15} | {'Std Dev (%)':<12} | {'Key Accepted (%)'}")
    print("-" * 90)
    for m in metrics:
        print(f"{m['scenario']:<30} | {m['expected']:<15} | {m['mean_qber']:<15.2f} | {m['std_qber']:<12.2f} | {m['accepted_pct']:.1f}%")

    # Generate Visualization (Histogram & Comparison Chart)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    # Subplot 1: Distribution Histograms
    bins = np.linspace(0, 40, 25)
    ax1.hist(ideal_qbers, bins=bins, alpha=0.7, color='green', label=f'Ideal Channel (Avg: {np.mean(ideal_qbers):.1f}%)')
    ax1.hist(noisy_qbers, bins=bins, alpha=0.7, color='blue', label=f'Noisy Channel (Avg: {np.mean(noisy_qbers):.1f}%)')
    ax1.hist(eve_noisy_qbers, bins=bins, alpha=0.7, color='red', label=f'Active Eve (Avg: {np.mean(eve_noisy_qbers):.1f}%)')
    ax1.axvline(threshold, color='darkred', linestyle='--', linewidth=2.5, label=f'Threshold ({threshold:.0f}%)')
    ax1.set_title("QBER Distribution & Threshold Separation", fontsize=12, fontweight='bold')
    ax1.set_xlabel("Sample QBER (%)", fontsize=11)
    ax1.set_ylabel("Frequency (Counts)", fontsize=11)
    ax1.legend(loc='upper right', framealpha=0.9)
    ax1.grid(axis='y', linestyle=':', alpha=0.6)

    # Subplot 2: Bar Comparison
    scenarios = ["Ideal", "Noisy\n(IBM)", "Active Eve\n(Ideal)", "Active Eve\n(Noisy)"]
    means = [m["mean_qber"] for m in metrics]
    stds = [m["std_qber"] for m in metrics]
    colors = ['#2ca02c', '#1f77b4', '#ff7f0e', '#d62728']

    bars = ax2.bar(scenarios, means, yerr=stds, capsize=6, color=colors, edgecolor='black', alpha=0.85)
    ax2.axhline(threshold, color='darkred', linestyle='--', linewidth=2, label=f'Threshold = {threshold:.0f}%')
    ax2.set_title("Mean QBER vs. 11% Eavesdropping Threshold", fontsize=12, fontweight='bold')
    ax2.set_ylabel("Quantum Bit Error Rate (QBER %)", fontsize=11)
    ax2.set_ylim(0, 35)

    for bar, val in zip(bars, means):
        ax2.text(bar.get_x() + bar.get_width()/2, val + 2.0, f"{val:.1f}%", ha='center', va='bottom', fontweight='bold')

    ax2.axhspan(0, 11, facecolor='green', alpha=0.1, label='Safe Zone (Key Accepted)')
    ax2.axhspan(11, 35, facecolor='red', alpha=0.1, label='Compromised Zone (Aborted)')
    ax2.legend(loc='upper left', framealpha=0.9)
    ax2.grid(axis='y', linestyle=':', alpha=0.6)

    plt.tight_layout()
    save_plot_to_destinations(fig, "test_spec_metric2_qber_distribution_threshold.png")
    plt.close(fig)

    return {"qber_distribution": metrics}


# ==============================================================================
# Deliverable 3: Estimation Error Curve (|QBER_sample - QBER_key|)
# ==============================================================================

def run_metric3_qber_estimation_error_curve(trials: int = 100) -> Dict[str, Any]:
    print("\n" + "="*80)
    print("DELIVERABLE 3: Sample QBER vs. Actual Key QBER Estimation Accuracy")
    print("="*80)

    qubit_configs = [
        {"qubits": 40, "sample_key": 10, "spec_bound": 8.0},
        {"qubits": 80, "sample_key": 20, "spec_bound": 6.0},
        {"qubits": 120, "sample_key": 30, "spec_bound": 4.5},
        {"qubits": 160, "sample_key": 40, "spec_bound": 3.5},
        {"qubits": 200, "sample_key": 50, "spec_bound": 3.0},
        {"qubits": 240, "sample_key": 60, "spec_bound": 2.5}
    ]

    metrics_table = []

    for cfg in qubit_configs:
        q = cfg["qubits"]
        target = cfg["sample_key"]

        # 1. Noisy Channel (~3% noise)
        deltas_noise = []
        for _ in range(trials):
            res = run_bb84_trial(total_qubits=q, target_key_length=target, has_eavesdropping=False, channel_noise=0.03, error_correction_enabled=False)
            if not res["shortfall"] and res["sample_size"] > 0:
                deltas_noise.append(abs(res["sample_qber"] - res["key_qber"]))
        mean_delta_noise = float(np.mean(deltas_noise))

        # 2. Active Eve Channel (~25% error)
        deltas_eve = []
        for _ in range(trials):
            res = run_bb84_trial(total_qubits=q, target_key_length=target, has_eavesdropping=True, channel_noise=0.0, error_correction_enabled=False)
            if not res["shortfall"] and res["sample_size"] > 0:
                deltas_eve.append(abs(res["sample_qber"] - res["key_qber"]))
        mean_delta_eve = float(np.mean(deltas_eve))

        metrics_table.append({
            "total_qubits": q,
            "sample_key_bits": target,
            "spec_bound": cfg["spec_bound"],
            "mean_delta_noisy": round(mean_delta_noise, 2),
            "mean_delta_eve": round(mean_delta_eve, 2)
        })

    # Print Table
    print(f"{'Total Qubits':<14} | {'Sample/Key Bits':<16} | {'Spec Bound (%)':<16} | {'Noisy Delta QBER (%)':<22} | {'Eve Delta QBER (%)'}")
    print("-" * 88)
    for row in metrics_table:
        status = "PASSED" if row["mean_delta_noisy"] <= row["spec_bound"] else "FAILED"
        print(f"{row['total_qubits']:<14} | ~{row['sample_key_bits']:<15} | <= {row['spec_bound']:<13.1f} | {row['mean_delta_noisy']:<22.2f} | {row['mean_delta_eve']:.2f}% ({status})")

    # Generate Figure
    fig, ax = plt.subplots(figsize=(8.5, 5))
    x_qubits = [m["total_qubits"] for m in metrics_table]
    y_noisy = [m["mean_delta_noisy"] for m in metrics_table]
    y_eve = [m["mean_delta_eve"] for m in metrics_table]
    y_bound = [m["spec_bound"] for m in metrics_table]

    ax.plot(x_qubits, y_noisy, marker='o', linewidth=2.5, color='#1f77b4', label=r'Noisy Channel ($\approx 3\%$ QBER)')
    ax.plot(x_qubits, y_eve, marker='s', linewidth=2, linestyle='--', color='#d62728', label=r'Active Eve ($\approx 25\%$ QBER)')
    ax.plot(x_qubits, y_bound, marker='^', linewidth=1.5, linestyle=':', color='black', label=r'TEST_SPEC Upper Bound ($\leq$)')

    for x, y in zip(x_qubits, y_noisy):
        ax.annotate(f"{y:.2f}%", (x, y), textcoords="offset points", xytext=(0, 8), ha='center', fontweight='bold', color='#1f77b4')

    ax.set_title(r"Estimation Error Convergence: $\Delta\mathrm{QBER} = |\mathrm{QBER}_{\mathrm{sample}} - \mathrm{QBER}_{\mathrm{key}}|$", fontsize=12, fontweight='bold', pad=12)
    ax.set_xlabel("Total Qubits Sent ($N$)", fontsize=11)
    ax.set_ylabel(r"Mean Absolute Estimation Error $\Delta\mathrm{QBER}$ (%)", fontsize=11)
    ax.set_xticks(x_qubits)
    ax.set_xticklabels([f"{q}\n(~{int(q*0.25)} bits)" for q in x_qubits])
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', framealpha=0.95)

    save_plot_to_destinations(fig, "test_spec_metric3_qber_estimation_error_curve.png")
    plt.close(fig)

    return {"qber_estimation_error": metrics_table}


# ==============================================================================
# Deliverable 4: Ballot Decryption Accuracy Table & Chart
# ==============================================================================

def run_metric4_ballot_decryption_accuracy(trials: int = 100) -> Dict[str, Any]:
    print("\n" + "="*80)
    print("DELIVERABLE 4: Ballot Decryption Accuracy (OTP Reversibility & Error Correction)")
    print("="*80)

    ballot_plaintext = "VT3"
    ballot_binary = text_to_binary(ballot_plaintext)  # 24 bits
    n = 24
    total_qubits = 144

    scenarios = [
        {"name": "Ideal Channel (No Noise)", "use_quantum": False, "noise": 0.0, "error_correction": False},
        {"name": "Noisy Channel (Uncorrected)", "use_quantum": True, "noise": 0.03, "error_correction": False},
        {"name": "Noisy Channel (With Error Correction)", "use_quantum": True, "noise": 0.03, "error_correction": True}
    ]

    results_table = []

    for sc in scenarios:
        correct_ballots = 0
        total_bit_errors = 0
        valid_sessions = 0

        for _ in range(trials):
            res = run_bb84_trial(
                total_qubits=total_qubits,
                target_key_length=n,
                has_eavesdropping=False,
                channel_noise=sc["noise"],
                error_correction_enabled=sc["error_correction"]
            )
            if res["status"] == "KEY_GENERATED" and len(res["alice_key"]) >= n:
                valid_sessions += 1
                k_alice = res["alice_key"][:n]
                k_bob = res["bob_key"][:n]

                cipher = otp_encrypt(ballot_binary, k_alice)
                decrypted_bin = otp_decrypt(cipher, k_bob)
                decrypted_text = binary_to_text(decrypted_bin)

                bit_errs = sum(1 for a, b in zip(ballot_binary, decrypted_bin) if a != b)
                total_bit_errors += bit_errs

                if decrypted_text == ballot_plaintext:
                    correct_ballots += 1

        accuracy = (correct_ballots / valid_sessions) * 100.0 if valid_sessions > 0 else 0.0
        ber = (total_bit_errors / (valid_sessions * n)) * 100.0 if valid_sessions > 0 else 0.0

        results_table.append({
            "scenario": sc["name"],
            "error_correction": sc["error_correction"],
            "accuracy_pct": round(accuracy, 1),
            "bit_error_rate": round(ber, 2),
            "valid_sessions": valid_sessions,
            "pass_criteria": "100%" if sc["error_correction"] or sc["noise"] == 0.0 else "Corrupted (>0% error)"
        })

    # Print Table
    print(f"{'Scenario':<42} | {'Error Correction':<18} | {'Ballot Accuracy (%)':<22} | {'Bit Error Rate (BER %)'}")
    print("-" * 96)
    for row in results_table:
        print(f"{row['scenario']:<42} | {str(row['error_correction']):<18} | {row['accuracy_pct']:<22.1f} | {row['bit_error_rate']:.2f}%")

    # Generate Visualization
    fig, ax = plt.subplots(figsize=(8.5, 5))
    names = ["Ideal Channel\n(Zero Noise)", "Noisy Channel\n(Without Reconciliation)", "Noisy Channel\n(With Error Correction)"]
    accuracies = [r["accuracy_pct"] for r in results_table]
    colors = ['#2ca02c', '#d62728', '#1f77b4']

    bars = ax.bar(names, accuracies, color=colors, edgecolor='black', width=0.45, alpha=0.88)
    ax.axhline(100.0, color='green', linestyle='--', linewidth=1.5, label='100% Target Correctness')

    for bar, val in zip(bars, accuracies):
        ax.text(bar.get_x() + bar.get_width()/2, val + 2.0, f"{val:.1f}%", ha='center', va='bottom', fontweight='bold', fontsize=11)

    ax.set_title("Ballot Recovery Rate: One-Time Pad Decryption Accuracy ($M = M'$)", fontsize=12, fontweight='bold', pad=12)
    ax.set_ylabel("Ballot Decryption Accuracy (%)", fontsize=11)
    ax.set_ylim(0, 115)
    ax.grid(axis='y', linestyle=':', alpha=0.6)
    ax.legend(loc='lower left', framealpha=0.9)

    save_plot_to_destinations(fig, "test_spec_metric4_ballot_decryption_accuracy.png")
    plt.close(fig)

    return {"ballot_decryption_accuracy": results_table}


# ==============================================================================
# Main Runner & JSON Summary
# ==============================================================================

def main():
    random.seed(42)
    np.random.seed(42)

    print("\n" + "="*80)
    print("RUNNING TEST_SPEC DELIVERABLES & GENERATING PRESENTATION METRICS")
    print("="*80)

    summary = {}
    summary |= run_metric1_sifting_key_sufficiency(trials=100)
    summary |= run_metric2_qber_distribution_threshold(trials=100)
    summary |= run_metric3_qber_estimation_error_curve(trials=100)
    summary |= run_metric4_ballot_decryption_accuracy(trials=100)

    json_path = os.path.join(CURRENT_DIR, "test_spec_summary.json")
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n[OK] Deliverables generation complete! Summary exported to: {json_path}")
    print(f"[OK] Plots saved to:\n  - {PLOTS_DIR}\n  - {REPORT_DIR}\n  - {REPORT_FIG_DIR}\n")


if __name__ == "__main__":
    main()
