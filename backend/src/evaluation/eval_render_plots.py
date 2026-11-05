"""
Master Plot & Analysis Orchestrator for QKD Voting System
Renders all 3 canonical publication figures directly from 'data/benchmark_results.json'
Execution time: <1 second (Zero simulation re-runs!)

Figures Generated:
1. report/figures/exp1_confusion_matrix_ibm.png (Experiment 1)
2. report/figures/exp2_qber_estimation_bias.png (Experiment 2)
3. report/figures/exp3_privacy_amplification.png (Experiment 3)
"""

import os
import sys
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CURRENT_DIR, "data")
BENCHMARK_RESULTS_PATH = os.path.join(DATA_DIR, "benchmark_results.json")

from eval_exp1_confusion_matrix import analyze_and_plot_exp1
from eval_exp2_qber_bias import analyze_and_plot_exp2
from eval_exp3_privacy_amplification import analyze_and_plot_exp3


def render_all_plots(force_retest: bool = False):
    if not os.path.exists(BENCHMARK_RESULTS_PATH) or force_retest:
        print("[DATA NOT FOUND or RETEST REQUESTED] Running eval_run_all.py...")
        from eval_run_all import run_all_benchmarks
        data = run_all_benchmarks(trials=100, force_retest=force_retest)
    else:
        with open(BENCHMARK_RESULTS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

    print("\n" + "=" * 80)
    print("ORCHESTRATING ALL CANONICAL REPORT ANALYSES & FIGURES (Execution time < 1s)")
    print("=" * 80)

    # 1. Experiment 1: IBM Kingston Hardware Confusion Matrix
    analyze_and_plot_exp1(data)

    # 2. Experiment 2: QBER Estimation Bias Convergence
    analyze_and_plot_exp2(data)

    # 3. Experiment 3: Privacy Amplification Eve Knowledge Elimination
    analyze_and_plot_exp3(data)

    print("\n" + "=" * 80)
    print("[ALL DONE] All 3 publication-grade figures successfully generated and saved to report/figures/")
    print("=" * 80)


if __name__ == "__main__":
    force = "--retest" in sys.argv or "--force" in sys.argv
    render_all_plots(force_retest=force)
