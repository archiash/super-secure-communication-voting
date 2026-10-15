"""
Evaluation & Visualization Suite for:
Key Sizing & Safety Margin (delta) Optimization

Requested Deltas: [0.0, 0.25, 0.5, 0.8, 1.0]
Focused, clutter-free, publication-ready figures for thesis report and slides.
"""

import os
import sys
import json
import random
from math import comb
from typing import Dict, List, Any

# Ensure backend/src is in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from evaluation.test_spec import run_bb84_trial
from modules import service

PLOTS_DIR = os.path.join(CURRENT_DIR, "plots")
REPORT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", "report"))
REPORT_FIG_DIR = os.path.join(REPORT_DIR, "figures")
ARTIFACT_DIR = r"C:\Users\Archiash\.gemini\antigravity\brain\fe188d27-1463-46c3-aca9-529a07ed20b1"

for d in [PLOTS_DIR, REPORT_DIR, REPORT_FIG_DIR, ARTIFACT_DIR]:
    os.makedirs(d, exist_ok=True)


def save_figure(fig, filename: str):
    """Save figure cleanly across report, plots, and artifact directories."""
    paths = [
        os.path.join(PLOTS_DIR, filename),
        os.path.join(REPORT_DIR, filename),
        os.path.join(REPORT_FIG_DIR, filename),
        os.path.join(ARTIFACT_DIR, filename)
    ]
    for p in paths:
        fig.savefig(p, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"[OK] Generated: {filename}")


plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Segoe UI', 'DejaVu Sans', 'Arial', 'Helvetica'],
    'font.size': 11,
    'axes.edgecolor': '#475569',
    'axes.linewidth': 1.0,
    'axes.titlesize': 13,
    'axes.titleweight': 'bold',
    'axes.labelsize': 11,
    'axes.labelweight': 'bold',
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'grid.color': '#f1f5f9',
    'grid.linestyle': '-',
    'grid.linewidth': 1.0
})


# ==============================================================================
# Variation 1: Safety Margin delta in [0, 0.25, 0.5, 0.8, 1.0] (Target n = 24)
# ==============================================================================

def run_variation1_safety_margin(trials: int = 100) -> Dict[str, Any]:
    print("\n" + "="*80)
    print("VARIATION 1: Safety Margin delta in [0.0, 0.25, 0.5, 0.8, 1.0] (Target n = 24)")
    print("="*80)

    n = 24
    deltas = [0.0, 0.25, 0.5, 0.8, 1.0]
    data = []

    for delta in deltas:
        mult = 4.0 + delta
        total_q = int(round(mult * n))

        results = [
            run_bb84_trial(total_qubits=total_q, target_key_length=n, has_eavesdropping=False, channel_noise=0.0)
            for _ in range(trials)
        ]

        success_count = sum(1 for r in results if r["final_key_len"] >= n)
        success_rate = (success_count / trials) * 100.0
        shortfall_rate = 100.0 - success_rate
        mean_sifted = float(np.mean([r["sifted_len"] for r in results]))

        data.append({
            "delta": delta,
            "multiplier": round(mult, 2),
            "total_qubits": total_q,
            "success_rate": round(success_rate, 1),
            "shortfall_rate": round(shortfall_rate, 1),
            "mean_sifted": round(mean_sifted, 1)
        })

    # Terminal output
    print(f"{'delta':<8} | {'Multiplier':<12} | {'Qubits (N)':<12} | {'Mean Sifted':<14} | {'Success Rate (%)':<18} | {'Verdict'}")
    print("-" * 88)
    for r in data:
        verdict = "Optimal (>=99%)" if r["success_rate"] >= 99 else ("Adequate (>=90%)" if r["success_rate"] >= 90 else "Deficient (<90%)")
        print(f"{r['delta']:<8.2f} | {r['multiplier']:<12.2f}x | {r['total_qubits']:<12} | {r['mean_sifted']:<14.1f} | {r['success_rate']:<18.1f} | {verdict}")

    # Figure 1: Clean, minimalist, high-impact bar chart
    fig, ax = plt.subplots(figsize=(7.2, 4.4), facecolor='white')
    x_labels = [f"δ = {d['delta']}\n({d['total_qubits']} Q)" for d in data]
    y_vals = [d["success_rate"] for d in data]
    colors = ['#ef4444', '#f59e0b', '#84cc16', '#10b981', '#059669']

    bars = ax.bar(x_labels, y_vals, color=colors, edgecolor='#334155', linewidth=1.1, width=0.55, zorder=3)
    ax.axhline(90.0, color='#f59e0b', linestyle='--', linewidth=1.5, label='90% Target Benchmark', zorder=2)
    ax.axhline(99.0, color='#059669', linestyle=':', linewidth=1.5, label='99% Production Target', zorder=2)

    for bar, val in zip(bars, y_vals):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 2.0, f"{val:.1f}%",
                ha='center', va='bottom', fontweight='bold', fontsize=11, color='#0f172a')

    ax.set_title("Key Generation Success Rate vs. Safety Margin δ", pad=12)
    ax.set_ylabel("First-Pass Success Rate |K| >= 24 (%)")
    ax.set_ylim(0, 115)
    ax.grid(axis='y', zorder=0)
    ax.legend(loc='lower right', framealpha=0.9, fontsize=9.5)

    save_figure(fig, "keysizing_fig1_safety_margin_delta.png")
    plt.close(fig)

    return {"variation1_safety_margin": data}


# ==============================================================================
# Variation 2: Law of Large Numbers (Variance Shrinkage across n)
# ==============================================================================

def run_variation2_key_lengths(trials: int = 100) -> Dict[str, Any]:
    print("\n" + "="*80)
    print("VARIATION 2: Law of Large Numbers (Target n in [8, 16, 24, 40])")
    print("="*80)

    key_lengths = [8, 16, 24, 40]
    data = []

    for n in key_lengths:
        n_qubits = 4 * n
        res = [
            run_bb84_trial(total_qubits=n_qubits, target_key_length=n, has_eavesdropping=False, channel_noise=0.0)
            for _ in range(trials)
        ]
        sifted_ratios = [r["sifted_len"] / n_qubits * 100.0 for r in res]
        success_rate = sum(1 for r in res if r["final_key_len"] >= n) / trials * 100.0

        std_theo = (np.sqrt(0.5 * 0.5 / n_qubits)) * 100.0
        std_meas = float(np.std(sifted_ratios))

        data.append({
            "target_key_length": n,
            "raw_qubits": n_qubits,
            "success_rate": round(success_rate, 1),
            "std_theoretical": round(std_theo, 2),
            "std_measured": round(std_meas, 2)
        })

    # Terminal output
    print(f"{'Target n (bits)':<16} | {'Qubits (4n)':<14} | {'Std Dev Meas (%)':<18} | {'Std Dev Theo (%)':<18} | {'Success Rate (%)'}")
    print("-" * 88)
    for r in data:
        print(f"{r['target_key_length']:<16} | {r['raw_qubits']:<14} | {r['std_measured']:<18.2f} | {r['std_theoretical']:<18.2f} | {r['success_rate']:.1f}%")

    # Figure 2: Clean single line chart for Law of Large Numbers
    fig, ax = plt.subplots(figsize=(6.8, 4.2), facecolor='white')
    x_n = [r["target_key_length"] for r in data]
    y_meas = [r["std_measured"] for r in data]
    y_theo = [r["std_theoretical"] for r in data]

    ax.plot(x_n, y_meas, marker='o', markersize=7, color='#2563eb', linewidth=2.2, label='Measured Std Dev (100 trials)', zorder=3)
    ax.plot(x_n, y_theo, marker='s', markersize=5, color='#dc2626', linestyle='--', linewidth=1.8, label='Theoretical σ', zorder=2)

    for i, (x, y) in enumerate(zip(x_n, y_meas)):
        offset_y = 0.45 if i < len(x_n) - 1 else -0.75
        va_val = 'bottom' if i < len(x_n) - 1 else 'top'
        ax.text(x, y + offset_y, f"{y:.1f}%", ha='center', va=va_val, fontsize=10, fontweight='bold', color='#1e40af')

    ax.set_title("Sifting Variance Contraction (Law of Large Numbers)", pad=12)
    ax.set_xlabel("Target Key Length n (bits)")
    ax.set_ylabel("Standard Deviation of Sifted Ratio (%)")
    ax.set_xticks(x_n)
    ax.set_xticklabels([f"n = {n}\n({4*n} Q)" for n in x_n])
    ax.set_ylim(1.8, 11)
    ax.grid(True, zorder=0)
    ax.legend(loc='upper right', framealpha=0.9, fontsize=9.5)

    save_figure(fig, "keysizing_fig2_law_of_large_numbers.png")
    plt.close(fig)

    return {"variation2_key_lengths": data}


# ==============================================================================
# Variation 3: Environment Comparison (Local 120Q vs IBM Single 40Q vs Multi-Session)
# ==============================================================================

def run_variation3_local_vs_ibm(trials: int = 100) -> Dict[str, Any]:
    print("\n" + "="*80)
    print("VARIATION 3: Environment Comparison (Local Simulator vs. IBM Quantum Constraints)")
    print("="*80)

    n = 24
    qubit_limit = 40

    # 1. Local Simulator: 120 Qubits (delta = 1.0)
    local_trials = [
        run_bb84_trial(total_qubits=120, target_key_length=n, has_eavesdropping=False, channel_noise=0.0)
        for _ in range(trials)
    ]
    local_success = sum(1 for r in local_trials if r["final_key_len"] >= n) / trials * 100.0

    # 2. IBM Single-Pass (40 Qubits limit)
    ibm_single_trials = [
        run_bb84_trial(total_qubits=qubit_limit, target_key_length=n, has_eavesdropping=False, channel_noise=0.03)
        for _ in range(trials)
    ]
    ibm_single_success = sum(1 for r in ibm_single_trials if r["final_key_len"] >= n) / trials * 100.0

    # 3. IBM Multi-Session Concatenation (40 Qubits x r)
    multi_sessions_counts = []
    multi_key_lens = []
    for _ in range(trials):
        res = service.simulate_multi_session_qkd(
            target_key_length=n,
            qubit_per_session=qubit_limit,
            has_eavesdropping=False,
            channel_noise=0.03,
            threshold_percent=11.0,
            use_qiskit=False
        )
        multi_sessions_counts.append(res["sessions_count"])
        multi_key_lens.append(len(res["final_alice_key"]))

    ibm_multi_success = sum(1 for k in multi_key_lens if k >= n) / trials * 100.0
    mean_sessions = float(np.mean(multi_sessions_counts))

    env_data = [
        {"name": "Local Simulator\n(Single-Pass, 120 Q)", "success": local_success, "sessions": 1.0},
        {"name": "IBM Quantum\n(Single-Pass, 40 Q Limit)", "success": ibm_single_success, "sessions": 1.0},
        {"name": f"IBM Quantum\n(Multi-Session, r = {mean_sessions:.1f})", "success": ibm_multi_success, "sessions": round(mean_sessions, 1)}
    ]

    print(f"{'Pipeline & Setup':<35} | {'Sessions':<10} | {'Success Rate (%)':<18}")
    print("-" * 70)
    for e in env_data:
        print(f"{e['name'].replace(chr(10), ' '):<35} | {e['sessions']:<10.1f} | {e['success']:<18.1f}%")

    # Figure 3: Clean, uncluttered comparison chart
    fig, ax = plt.subplots(figsize=(7.2, 4.4), facecolor='white')
    x_labels = [e["name"] for e in env_data]
    y_vals = [e["success"] for e in env_data]
    colors = ['#3b82f6', '#ef4444', '#10b981']

    bars = ax.bar(x_labels, y_vals, color=colors, edgecolor='#334155', linewidth=1.1, width=0.48, zorder=3)
    ax.axhline(100.0, color='#059669', linestyle='--', linewidth=1.5, label='100% Target', zorder=2)

    for bar, val in zip(bars, y_vals):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 2.5, f"{val:.1f}%",
                ha='center', va='bottom', fontweight='bold', fontsize=11, color='#0f172a')

    ax.set_title("Key Generation: Local Simulation vs. IBM Quantum Limits", pad=12)
    ax.set_ylabel("Success Rate |K| >= 24 (%)")
    ax.set_ylim(0, 115)
    ax.grid(axis='y', zorder=0)
    ax.legend(loc='lower left', framealpha=0.9, fontsize=9.5)

    save_figure(fig, "keysizing_fig3_local_vs_ibm_multisession.png")
    plt.close(fig)

    return {"variation3_local_vs_ibm": env_data}


# ==============================================================================
# Figure 4: Clean Binomial Probability S-Curve (delta from 0 to 1.0)
# ==============================================================================

def make_fig4_theoretical_proof():
    fig, ax = plt.subplots(figsize=(7.2, 4.4), facecolor='white')

    delta_range = np.linspace(0.0, 1.0, 25)
    n = 24

    p_success = []
    for d in delta_range:
        total_N = int(round((4.0 + d) * n))
        prob = sum(comb(total_N, k) * (0.5**total_N) for k in range(2 * n, total_N + 1)) * 100.0
        p_success.append(prob)

    ax.plot(delta_range, p_success, color='#2563eb', linewidth=2.5, label='Theoretical P(|K| >= 24)', zorder=3)

    # Highlight requested points: 0, 0.25, 0.5, 0.8, 1.0
    req_deltas = [0.0, 0.25, 0.5, 0.8, 1.0]
    offsets = {
        0.0: (-6.5, 'top'),
        0.25: (-6.0, 'top'),
        0.5: (-6.0, 'top'),
        0.8: (3.0, 'bottom'),
        1.0: (-6.0, 'top')
    }
    for d in req_deltas:
        total_N = int(round((4.0 + d) * n))
        prob = sum(comb(total_N, k) * (0.5**total_N) for k in range(2 * n, total_N + 1)) * 100.0
        ax.plot(d, prob, marker='o', markersize=7, color='#dc2626', zorder=4)
        dy, va_align = offsets[d]
        ax.text(d, prob + dy, f"{prob:.0f}%", ha='center', va=va_align, fontsize=10, fontweight='bold', color='#991b1b')

    ax.axhline(90.0, color='#f59e0b', linestyle='--', linewidth=1.4, label='90% Threshold', zorder=2)
    ax.axhline(99.0, color='#059669', linestyle=':', linewidth=1.4, label='99% Target', zorder=2)

    ax.set_title("Theoretical Key Sufficiency: P(W >= 48) vs. Safety Margin δ", pad=12)
    ax.set_xlabel("Safety Margin Parameter δ (where N = (4 + δ) × 24)")
    ax.set_ylabel("Probability of Full Key Yield (%)")
    ax.set_xlim(-0.03, 1.03)
    ax.set_ylim(40, 108)
    ax.grid(True, zorder=0)
    ax.legend(loc='lower right', framealpha=0.9, fontsize=9.5)

    save_figure(fig, "keysizing_fig4_binomial_shortfall_theory_vs_practice.png")
    plt.close(fig)


# ==============================================================================
# Main Runner & JSON Export
# ==============================================================================

def main():
    random.seed(42)
    np.random.seed(42)

    print("\n" + "="*80)
    print("RUNNING KEY SIZING OPTIMIZATION WITH DELTA: [0.0, 0.25, 0.5, 0.8, 1.0]")
    print("="*80)

    summary = {}
    summary |= run_variation1_safety_margin(trials=100)
    summary |= run_variation2_key_lengths(trials=100)
    summary |= run_variation3_local_vs_ibm(trials=100)
    make_fig4_theoretical_proof()

    json_path = os.path.join(CURRENT_DIR, "key_sizing_optimization_summary.json")
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n[OK] Evaluation complete! Summary exported to: {json_path}")


if __name__ == "__main__":
    main()
