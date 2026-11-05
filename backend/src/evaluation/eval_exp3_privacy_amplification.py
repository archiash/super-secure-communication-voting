"""
Experiment 3: Privacy Amplification & Eve Knowledge Elimination Suite
Evaluates the stealth eavesdropping scenario (QBER <= 11% threshold)
Quantifies:
1. Number of bits Eve knows BEFORE Privacy Amplification (k_before)
2. Number of bits Eve knows AFTER Privacy Amplification (k_after via GF(2) rank analysis)
3. Percentage of sessions where Eve's knowledge FULLY disappears (k_after == 0)
Reads directly from 'data/benchmark_results.json' (Execution time: <0.5s)
Outputs publication-grade figure: 'report/figures/exp3_privacy_amplification.png'
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


def analyze_and_plot_exp3(data=None):
    if data is None:
        data = load_benchmark_data()

    # Extract Experiment 3 Results
    exp3_data = data.get("exp3_privacy_amplification", data.get("privacy_amplification_analysis", {}))
    pa_results = exp3_data.get("results", {})
    pa_keys = [int(k) for k in pa_results.keys()]
    pa_keys.sort()

    print("\n" + "=" * 80)
    print("EXPERIMENT 3: PRIVACY AMPLIFICATION & EVE KNOWLEDGE ELIMINATION")
    print("Evaluates 2-Universal Toeplitz Hashing against Stealth Eavesdropping (QBER = 8.0%)")
    print("=" * 80)
    print(f"{'Key (n)':<9} {'Sec Param (s)':<14} {'Raw Bits (N)':<14} {'Eve Before (b)':<16} {'Eve After (b)':<15} {'100% Eliminated':<16}")
    print("-" * 80)

    for n in pa_keys:
        for s in [8, 16, 32]:
            sub = pa_results[str(n)][str(s)]
            nb = sub["n_raw_input"]
            kb = sub["k_before_mean"]
            ka = sub["k_after_mean"]
            pct = sub["pct_fully_disappeared"]
            print(f"{n:<9} {s:<14} {nb:<14} {kb:<16.1f} {ka:<15.2f} {pct:<15.1f}%")

    print("=" * 80)

    # --------------------------------------------------------------------------
    # Render Publication Figure: Unified 2-Panel Summary
    # --------------------------------------------------------------------------
    before_s16 = [pa_results[str(k)]["16"]["k_before_mean"] for k in pa_keys]
    after_s8 = [pa_results[str(k)]["8"]["k_after_mean"] for k in pa_keys]
    after_s16 = [pa_results[str(k)]["16"]["k_after_mean"] for k in pa_keys]
    after_s32 = [pa_results[str(k)]["32"]["k_after_mean"] for k in pa_keys]

    pct_s8 = [pa_results[str(k)]["8"]["pct_fully_disappeared"] for k in pa_keys]
    pct_s16 = [pa_results[str(k)]["16"]["pct_fully_disappeared"] for k in pa_keys]
    pct_s32 = [pa_results[str(k)]["32"]["pct_fully_disappeared"] for k in pa_keys]

    x_pa = np.arange(len(pa_keys))
    w_pa = 0.20

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.2, 5.4), facecolor='white')

    # Panel A: Eve Known Bits Before vs. After
    ax1.bar(x_pa - 1.5 * w_pa, before_s16, w_pa, label='Before PA (Eve Raw Knowledge)', color='#e11d48', alpha=0.9, edgecolor='none')
    ax1.bar(x_pa - 0.5 * w_pa, [max(0.3, v) for v in after_s8], w_pa, label='After PA (s = 8b)', color='#f59e0b', alpha=0.9, edgecolor='none')
    ax1.bar(x_pa + 0.5 * w_pa, [max(0.3, v) for v in after_s16], w_pa, label='After PA (s = 16b)', color='#0284c7', alpha=0.9, edgecolor='none')
    ax1.bar(x_pa + 1.5 * w_pa, [max(0.3, v) for v in after_s32], w_pa, label='After PA (s = 32b)', color='#059669', alpha=0.9, edgecolor='none')

    for i in range(len(pa_keys)):
        ax1.text(x_pa[i] - 1.5 * w_pa, before_s16[i] + 0.8, f"{before_s16[i]:.1f}b", ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#9f1239')
        v8 = after_s8[i]; v16 = after_s16[i]; v32 = after_s32[i]
        txt8 = f"{v8:.2f}" if v8 > 0 else "0"
        txt16 = f"{v16:.2f}" if v16 > 0 else "0"
        txt32 = f"{v32:.2f}" if v32 > 0 else "0"
        ax1.text(x_pa[i] - 0.5 * w_pa, max(0.4, v8) + 0.5, txt8, ha='center', va='bottom', fontsize=7.8, fontweight='bold', color='#b45309', rotation=90)
        ax1.text(x_pa[i] + 0.5 * w_pa, max(0.4, v16) + 0.5, txt16, ha='center', va='bottom', fontsize=7.8, fontweight='bold', color='#0369a1', rotation=90)
        ax1.text(x_pa[i] + 1.5 * w_pa, max(0.4, v32) + 0.5, txt32, ha='center', va='bottom', fontsize=7.8, fontweight='bold', color='#047857', rotation=90)

    ax1.set_title("A. Eve Known Bits: Before vs. After Privacy Amplification", pad=14, fontsize=10.5, fontweight='bold', color='#0f172a')
    ax1.set_xlabel("Target Key Size n (bits)", fontsize=9.2, color='#475569')
    ax1.set_ylabel("Eve Known Bits (bits)", fontsize=9.2, color='#475569')
    ax1.set_xticks(x_pa)
    ax1.set_xticklabels([f"{k}b" for k in pa_keys], fontsize=8.8, color='#64748b')
    ax1.set_ylim(0, max(before_s16) * 1.18)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_color('#94a3b8')
    ax1.spines['bottom'].set_color('#94a3b8')
    ax1.grid(axis='y', linestyle='-', linewidth=0.7, color='#f1f5f9')
    ax1.legend(loc='upper left', frameon=False, fontsize=8.4)

    # Panel B: Full Elimination Rate (%)
    ax2.plot(x_pa, pct_s32, marker='s', markersize=6.5, color='#059669', linewidth=2.0, label=f's = 32 bits (Avg: {np.mean(pct_s32):.1f}% Erased)')
    ax2.plot(x_pa, pct_s16, marker='o', markersize=6.0, color='#0284c7', linewidth=1.8, label=f's = 16 bits (Avg: {np.mean(pct_s16):.1f}% Erased)')
    ax2.plot(x_pa, pct_s8, marker='^', markersize=6.0, color='#f59e0b', linewidth=1.6, linestyle='--', label=f's = 8 bits (Avg: {np.mean(pct_s8):.1f}% Erased)')

    for i in range(len(pa_keys)):
        ax2.text(x_pa[i], pct_s32[i] + 1.2, f"{pct_s32[i]:.0f}%", ha='center', va='bottom', fontsize=8.4, fontweight='bold', color='#047857')
        if pct_s16[i] < 100.0:
            ax2.text(x_pa[i] + 0.15, pct_s16[i] - 1.6, f"{pct_s16[i]:.0f}%", ha='left', va='top', fontsize=8.2, fontweight='bold', color='#0369a1')
        ax2.text(x_pa[i], pct_s8[i] - 1.5, f"{pct_s8[i]:.0f}%", ha='center', va='top', fontsize=8.2, fontweight='bold', color='#b45309')

    ax2.set_title("B. Probability of Complete Knowledge Elimination (k_after = 0)", pad=14, fontsize=10.5, fontweight='bold', color='#0f172a')
    ax2.set_xlabel("Target Key Size n (bits)", fontsize=9.2, color='#475569')
    ax2.set_ylabel("Full Elimination Percentage (%)", fontsize=9.2, color='#475569')
    ax2.set_xticks(x_pa)
    ax2.set_xticklabels([f"{k}b" for k in pa_keys], fontsize=8.8, color='#64748b')
    min_pa_pct = min(min(pct_s8), min(pct_s16), min(pct_s32))
    ax2.set_ylim(min(75, min_pa_pct - 5), 106)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_color('#94a3b8')
    ax2.spines['bottom'].set_color('#94a3b8')
    ax2.grid(axis='y', linestyle='-', linewidth=0.7, color='#f1f5f9')
    ax2.legend(loc='lower left', frameon=False, fontsize=8.4)

    plt.subplots_adjust(wspace=0.22)
    save_minimal(fig, "exp3_privacy_amplification.png")
    plt.close(fig)
    print("[EXP 3 COMPLETE] Analysis finished and figure generated successfully.")


if __name__ == "__main__":
    retest = "--retest" in sys.argv
    analyze_and_plot_exp3(load_benchmark_data(retest=retest))
