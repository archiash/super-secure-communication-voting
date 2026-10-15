"""
Generate the EXACT Single Line Chart and Table for:
Test Plan: Key Sizing & Safety Margin (delta) Optimization (n = 24 bits, 'VT3')

Using solely the codebase implementation:
- modules.service.calculate_key_length
- modules.qkd.simulate_bb84_protocal
- modules.qkd.filter_key_by_basis
- modules.qkd.QBER

Single Graph Setup:
- X-axis: delta (0, 0.25, 0.5, 0.8, 1.0)
- Y-axis: % Success Rate |K| >= 24 (0% to 100%)
- 3 Lines:
  1. Dashed Grey/Black: Theory (Theoretical Curve)
  2. Solid Blue: Local Simulator
  3. Solid Orange: IBM Quantum (Realistic 2.5% Hardware Noise)
"""

import os
import sys
import json
import random
from math import comb

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

from modules import qkd, service

PLOTS_DIR = os.path.join(CURRENT_DIR, "plots")
REPORT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", "report"))
REPORT_FIG_DIR = os.path.join(REPORT_DIR, "figures")
ARTIFACT_DIR = r"C:\Users\Archiash\.gemini\antigravity\brain\fe188d27-1463-46c3-aca9-529a07ed20b1"

for d in [PLOTS_DIR, REPORT_DIR, REPORT_FIG_DIR, ARTIFACT_DIR]:
    os.makedirs(d, exist_ok=True)


def evaluate_and_plot(trials: int = 200):
    random.seed(42)
    n = 24
    deltas = [0.0, 0.25, 0.5, 0.8, 1.0]
    
    theory_rates = []
    local_rates = []
    ibm_rates = []
    table_rows = []

    print("\nRunning Evaluation Using Codebase Implementation (modules.qkd & modules.service)...")
    for d in deltas:
        mult = 4.0 + d
        total_q = service.calculate_key_length(d, n)
        theoretical_mean_key = 0.25 * total_q

        # Exact Theoretical Probability: P(W >= 48) where W ~ Binomial(total_q, 0.5)
        prob_theory = sum(comb(total_q, k) * (0.5**total_q) for k in range(2 * n, total_q + 1)) * 100.0
        theory_rates.append(prob_theory)

        # 1. Local Simulator (use_ibm=False, channel_noise=0.0)
        local_success = 0
        for _ in range(trials):
            sim = qkd.simulate_bb84_protocal(
                key_size=total_q, 
                per_time_bits=total_q, 
                has_eavesdropping=False, 
                use_ibm=False, 
                channel_noise=0.0
            )
            s_alice = qkd.filter_key_by_basis(sim['server_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            s_bob = qkd.filter_key_by_basis(sim['client_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            w = len(s_alice)
            if w >= 2 * n:
                test_indices = random.sample(range(w), w - n)
                test_err = sum(1 for idx in test_indices if s_alice[idx] != s_bob[idx])
                qber = (test_err / (w - n)) * 100.0 if (w - n) > 0 else 0.0
                if qber <= 11.0:
                    local_success += 1

        loc_rate = (local_success / trials) * 100.0
        local_rates.append(loc_rate)

        # 2. IBM Quantum (use_ibm=True, channel_noise=0.025)
        ibm_success = 0
        for _ in range(trials):
            sim = qkd.simulate_bb84_protocal(
                key_size=total_q, 
                per_time_bits=total_q, 
                has_eavesdropping=False, 
                use_ibm=True, 
                channel_noise=0.025
            )
            s_alice = qkd.filter_key_by_basis(sim['server_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            s_bob = qkd.filter_key_by_basis(sim['client_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            w = len(s_alice)
            if w >= 2 * n:
                test_indices = random.sample(range(w), w - n)
                test_err = sum(1 for idx in test_indices if s_alice[idx] != s_bob[idx])
                qber = (test_err / (w - n)) * 100.0 if (w - n) > 0 else 0.0
                if qber <= 11.0:
                    ibm_success += 1

        ibm_rate = (ibm_success / trials) * 100.0
        ibm_rates.append(ibm_rate)

        table_rows.append({
            "delta": f"{d:.2f}",
            "multiplier": f"{mult:.2f}x",
            "qubits": total_q,
            "theory_mean_key": f"{theoretical_mean_key:.1f} bits",
            "theory_prob": f"~{prob_theory:.0f}%",
            "local_sim": f"{loc_rate:.1f}%",
            "ibm_quantum": f"{ibm_rate:.1f}%"
        })

    # Print Table
    print("\n" + "="*95)
    print("EVALUATION TABLE: Target n = 24 bits ('VT3')")
    print("="*95)
    print(f"{'delta':<8} | {'Multiplier':<12} | {'Qubits (N)':<12} | {'Theory Mean':<14} | {'Theory (>=24b)':<16} | {'Local Sim':<14} | {'IBM Quantum'}")
    print("-" * 95)
    for r in table_rows:
        print(f"{r['delta']:<8} | {r['multiplier']:<12} | {r['qubits']:<12} | {r['theory_mean_key']:<14} | {r['theory_prob']:<16} | {r['local_sim']:<14} | {r['ibm_quantum']}")

    # --------------------------------------------------------------------------
    # Single Clean Line Graph (Success Rate vs. delta)
    # --------------------------------------------------------------------------
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Segoe UI', 'DejaVu Sans', 'Arial'],
        'font.size': 11,
        'axes.edgecolor': '#475569',
        'axes.linewidth': 1.1,
        'axes.titlesize': 13,
        'axes.titleweight': 'bold',
        'axes.labelsize': 11,
        'axes.labelweight': 'bold',
        'xtick.labelsize': 10.5,
        'ytick.labelsize': 10.5,
        'grid.color': '#f1f5f9',
        'grid.linestyle': '-',
        'grid.linewidth': 1.0
    })

    fig, ax = plt.subplots(figsize=(7.6, 4.6), facecolor='white')

    # Line 1: Dashed Line (Theoretical Curve)
    ax.plot(deltas, theory_rates, color='#64748b', linestyle='--', linewidth=2.0, marker='s', markersize=6, label='Theory (Binomial)', zorder=2)

    # Line 2: Solid Blue Line (Local Simulator)
    ax.plot(deltas, local_rates, color='#2563eb', linestyle='-', linewidth=2.6, marker='o', markersize=7, label='Local Simulator', zorder=3)

    # Line 3: Solid Orange Line (IBM Quantum)
    ax.plot(deltas, ibm_rates, color='#ea580c', linestyle='-', linewidth=2.6, marker='^', markersize=7, label='IBM Quantum (Noise 2.5%)', zorder=4)

    # Annotate points with clean text
    for d, loc_val, ibm_val in zip(deltas, local_rates, ibm_rates):
        ax.text(d, loc_val + 2.8, f"{loc_val:.0f}%", ha='center', va='bottom', fontsize=9.5, fontweight='bold', color='#1d4ed8')
        ax.text(d, ibm_val - 4.5, f"{ibm_val:.0f}%", ha='center', va='top', fontsize=9.5, fontweight='bold', color='#c2410c')

    ax.axhline(90.0, color='#f59e0b', linestyle=':', linewidth=1.3, alpha=0.8, zorder=1)
    ax.text(0.01, 91.0, '90% Benchmark', fontsize=9.0, color='#b45309', fontweight='bold')

    ax.set_title("Key Generation Success Rate vs. Safety Margin δ (n = 24 bits)", pad=12)
    ax.set_xlabel(r"Safety Margin Parameter $\delta$   [$N = \lceil (4 + \delta) \times 24 \rceil$]", labelpad=8)
    ax.set_ylabel("Success Rate |K| >= 24 (%)", labelpad=8)
    ax.set_xticks(deltas)
    ax.set_xticklabels([f"δ = {d}\n({service.calculate_key_length(d, 24)}Q)" for d in deltas])
    ax.set_ylim(40, 108)
    ax.grid(True, zorder=0)
    ax.legend(loc='lower right', framealpha=0.95, fontsize=10)

    # Save to all target paths
    filenames = ["keysizing_single_comparison.png", "keysizing_fig1_safety_margin_delta.png"]
    for fn in filenames:
        paths = [
            os.path.join(PLOTS_DIR, fn),
            os.path.join(REPORT_DIR, fn),
            os.path.join(REPORT_FIG_DIR, fn),
            os.path.join(ARTIFACT_DIR, fn)
        ]
        for p in paths:
            fig.savefig(p, dpi=300, bbox_inches='tight', facecolor='white')

    plt.close(fig)
    print("\n[OK] Single graph generated cleanly at: keysizing_single_comparison.png")

    # Export json summary
    json_path = os.path.join(CURRENT_DIR, "single_keysizing_summary.json")
    with open(json_path, "w") as f:
        json.dump({"table": table_rows}, f, indent=2)

    return table_rows


if __name__ == "__main__":
    evaluate_and_plot(trials=200)
