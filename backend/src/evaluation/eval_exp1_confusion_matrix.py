"""
Experiment 1: Confusion Matrix & Eavesdropping Detection on IBM Quantum Hardware
Analyzes results from IBM Kingston Heron QPU noise calibration (2.82% mean physical QBER)
Reads directly from 'data/benchmark_results.json' (Execution time: <0.5s)
Outputs publication-grade figure: 'report/figures/exp1_confusion_matrix_ibm.png'
"""

import os
import sys
import json
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


def analyze_and_plot_exp1(data=None):
    if data is None:
        data = load_benchmark_data()

    # Extract Experiment 1 IBM Hardware Confusion Matrix
    cm_ibm = data.get("exp1_confusion_matrix", {}).get("ibm_hardware", data.get("confusion_matrix_ibm", {}))
    meta = data.get("metadata", {})
    trials = meta.get("trials_per_test", 100)
    powers_of_2 = [int(k) for k in cm_ibm.keys()]
    powers_of_2.sort()

    print("\n" + "=" * 80)
    print("EXPERIMENT 1: CONFUSION MATRIX & DETECTION ANALYSIS (IBM KINGSTON HARDWARE)")
    print(f"Calibrated Hardware Noise: {meta.get('ibm_hardware_calibrated_noise', 0.0282)*100:.2f}% | Trials per class: {trials}")
    print("=" * 80)
    print(f"{'Key (n)':<9} {'Qubits':<8} {'TN':<5} {'FP':<5} {'FN':<5} {'TP':<5} {'Accuracy':<10} {'Recall':<10} {'Precision':<10}")
    print("-" * 80)

    for n in powers_of_2:
        res = cm_ibm[str(n)]
        tn, fp, fn, tp = res["TN"], res["FP"], res["FN"], res["TP"]
        acc = res.get("Accuracy", ((tn + tp) / (trials * 2)) * 100.0)
        rec = res.get("Recall", (tp / (tp + fn) * 100.0) if (tp + fn) > 0 else 0.0)
        prec = res.get("Precision", (tp / (tp + fp) * 100.0) if (tp + fp) > 0 else 0.0)
        q = res.get("qubits", 0)
        print(f"{n:<9} {q:<8} {tn:<5} {fp:<5} {fn:<5} {tp:<5} {acc:<9.1f}% {rec:<9.1f}% {prec:<9.1f}%")

    print("=" * 80)

    # --------------------------------------------------------------------------
    # Render Publication Figure: Multi-Panel Grid Across Powers of 2 on IBM Hardware
    # --------------------------------------------------------------------------
    fig, axes = plt.subplots(2, 3, figsize=(13.5, 7.8), facecolor='white')
    axes = axes.flatten()
    cell_colors = [['#eff6ff', '#fff1f2'], ['#fff1f2', '#eff6ff']]

    for idx, n in enumerate(powers_of_2):
        ax = axes[idx]
        res = cm_ibm[str(n)]
        matrix = [[res["TN"], res["FP"]], [res["FN"], res["TP"]]]
        acc = res.get("Accuracy", ((res["TN"] + res["TP"]) / (trials * 2)) * 100.0)
        rec = res.get("Recall", (res["TP"] / (res["TP"] + res["FN"]) * 100.0) if (res["TP"] + res["FN"]) > 0 else 0.0)

        for i in range(2):
            for j in range(2):
                val = matrix[i][j]
                pct = (val / trials) * 100.0
                rect = plt.Rectangle((j, 1 - i), 1, 1, facecolor=cell_colors[i][j], edgecolor='#cbd5e1', linewidth=1.1)
                ax.add_patch(rect)
                num_col = '#1e40af' if (i == j) else ('#b91c1c' if val > 0 else '#94a3b8')
                ax.text(j + 0.5, 1 - i + 0.58, f"{val}", ha='center', va='center', fontsize=19, fontweight='bold', color=num_col)
                ax.text(j + 0.5, 1 - i + 0.34, f"({pct:.1f}%)", ha='center', va='center', fontsize=9.2, color='#64748b')
                desc = "No Eve, No Alert" if (i==0 and j==0) else ("No Eve, Alert" if (i==0 and j==1) else ("Eve, No Alert" if (i==1 and j==0) else "Eve, Alert"))
                ax.text(j + 0.5, 1 - i + 0.17, desc, ha='center', va='center', fontsize=8.0, fontweight='bold', color='#475569')

        ax.set_xlim(0, 2); ax.set_ylim(0, 2)
        ax.set_xticks([0.5, 1.5]); ax.set_xticklabels(['No Alert', 'Alert'], fontsize=9.0, fontweight='bold')
        ax.xaxis.tick_top()
        ax.set_title(f"n = {n} bits (IBM Hardware) | Acc: {acc:.1f}% | Recall: {rec:.1f}%", pad=10, fontsize=10.0, fontweight='bold', color='#0f172a')
        if idx % 3 == 0:
            ax.set_yticks([0.5, 1.5]); ax.set_yticklabels(['Eve', 'No Eve'], fontsize=9.0, fontweight='bold')
        else:
            ax.set_yticks([])
        for spine in ax.spines.values(): spine.set_visible(False)
        ax.tick_params(top=False, bottom=False, left=False, right=False)

    plt.subplots_adjust(wspace=0.28, hspace=0.42)
    save_minimal(fig, "exp1_confusion_matrix_ibm.png")
    plt.close(fig)
    print("[EXP 1 COMPLETE] Analysis finished and figure generated successfully.")


if __name__ == "__main__":
    retest = "--retest" in sys.argv
    analyze_and_plot_exp1(load_benchmark_data(retest=retest))
