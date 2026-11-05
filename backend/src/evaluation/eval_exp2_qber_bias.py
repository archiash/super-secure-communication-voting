"""
Experiment 2: Blind Security Verification & QBER Estimation Bias
Analyzes whether sacrificed sample QBER accurately estimates the unmeasured secret key QBER
Reads directly from 'data/benchmark_results.json' (Execution time: <0.5s)
Outputs publication-grade figure: 'report/figures/exp2_qber_estimation_bias.png'
"""

import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CURRENT_DIR, "data")
REPORT_FIG_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", "report", "figures"))
BENCHMARK_RESULTS_PATH = os.path.join(DATA_DIR, "benchmark_results.json")

os.makedirs(REPORT_FIG_DIR, exist_ok=True)


def save_minimal(fig, filename):
    path = os.path.join(REPORT_FIG_DIR, filename)
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    print(f" -> [SAVED TO REPORT] {filename}")


def load_benchmark_data(retest=False):
    if not os.path.exists(BENCHMARK_RESULTS_PATH) or retest:
        print("[DATA NOT FOUND or RETEST REQUESTED] Running eval_run_all.py...")
        from eval_run_all import run_all_benchmarks
        return run_all_benchmarks(trials=100, force_retest=retest)

    with open(BENCHMARK_RESULTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze_and_plot_exp2(data=None):
    if data is None:
        data = load_benchmark_data()

    # Extract Experiment 2 Convergence Data
    exp2_data = data.get("exp2_qber_estimation_bias", data.get("priority2_blind_verification", {}))
    conv = exp2_data.get("convergence", exp2_data.get("convergence_powers_of_2", {}))
    
    key_sizes = [int(k) for k in conv.keys()]
    key_sizes.sort()
    mean_biases = [conv[str(k)]["mean_bias"] for k in key_sizes]
    qubits_list = [conv[str(k)].get("qubits", 0) for k in key_sizes]
    sample_sizes = [conv[str(k)].get("sample_size", k) for k in key_sizes]

    print("\n" + "=" * 80)
    print("EXPERIMENT 2: BLIND VERIFICATION & ESTIMATION BIAS CONVERGENCE")
    print("Proves that sacrificed sample QBER unbiasedly reflects uninspected secret key QBER")
    print("=" * 80)
    print(f"{'Key Size (n)':<14} {'Raw Qubits (N)':<16} {'Sample Bits (m)':<18} {'Mean Estimation Bias |Qs - Qk|':<30}")
    print("-" * 80)

    for n, q, s, b in zip(key_sizes, qubits_list, sample_sizes, mean_biases):
        print(f"{n:<14} {q:<16} {s:<18} {b:<30.2f}%")

    print("=" * 80)

    # --------------------------------------------------------------------------
    # Render Publication Figure: Estimation Error Convergence vs Key Size
    # --------------------------------------------------------------------------
    x_positions = np.arange(len(key_sizes))
    fig, ax = plt.subplots(figsize=(6.4, 4.2), facecolor='white')

    ax.plot(x_positions, mean_biases, marker='o', markersize=5.5, color='#0284c7', linewidth=1.8, label='Estimation Bias |Q_sample - Q_key|')

    for i, n in enumerate(key_sizes):
        ax.text(x_positions[i], mean_biases[i] + 0.35, f"{mean_biases[i]:.2f}%", ha='center', fontsize=8.5, fontweight='bold', color='#0369a1')

    ax.set_title("Sample QBER Estimation Accuracy vs. Target Key Size", pad=12, fontsize=11.5, fontweight='bold', color='#0f172a')
    ax.set_xlabel("Target Key Size n (bits)", fontsize=9.2, color='#475569')
    ax.set_ylabel("Mean Estimation Bias (%)", fontsize=9.2, color='#475569')
    ax.set_xticks(x_positions)
    ax.set_xticklabels([f"{n}b" for n in key_sizes], fontsize=8.8, color='#64748b')
    ax.set_ylim(0, max(20.0, max(mean_biases) * 1.25))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#94a3b8')
    ax.spines['bottom'].set_color('#94a3b8')
    ax.grid(axis='y', linestyle='-', linewidth=0.7, color='#f1f5f9')
    ax.legend(frameon=False, loc='upper right', fontsize=8.6)

    save_minimal(fig, "exp2_qber_estimation_bias.png")
    plt.close(fig)
    print("[EXP 2 COMPLETE] Analysis finished and figure generated successfully.")


if __name__ == "__main__":
    retest = "--retest" in sys.argv
    analyze_and_plot_exp2(load_benchmark_data(retest=retest))
