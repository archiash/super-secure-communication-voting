"""
Generate the EXACT 2 Requested Graphs for the Test Plan:
Graph 1: Key Success Rate vs. delta in [0, 0.25, 0.5, 0.8, 1.0] for n = 24 bits ('VT3')
Graph 2: Optimal Safety Margin delta* with respect to Target Key Size n in [8, 16, 24, 32, 40] bits

Using purely the project codebase:
- modules.service.calculate_key_length
- modules.qkd.simulate_bb84_protocal
- modules.qkd.filter_key_by_basis
- modules.qkd.QBER
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


def save_fig(fig, filename):
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


# ==============================================================================
# GRAPH 1: Success Rate vs delta for 24 bits ("VT3")
# ==============================================================================
def make_graph1(trials: int = 100):
    random.seed(42)
    n = 24
    deltas = [0.0, 0.25, 0.5, 0.8, 1.0]

    theory_rates = []
    local_rates = []
    ibm_rates = []

    print("Running Graph 1: 24 bits ('VT3') with exactly 100 trials per case...")
    for d in deltas:
        total_q = service.calculate_key_length(d, n)
        # Theory P(W >= 48)
        p_th = sum(comb(total_q, k) * (0.5**total_q) for k in range(2 * n, total_q + 1)) * 100.0
        theory_rates.append(p_th)

        # Local Sim
        loc_succ = 0
        for _ in range(trials):
            sim = qkd.simulate_bb84_protocal(key_size=total_q, per_time_bits=total_q, has_eavesdropping=False, use_ibm=False, channel_noise=0.0)
            s_alice = qkd.filter_key_by_basis(sim['server_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            s_bob = qkd.filter_key_by_basis(sim['client_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            w = len(s_alice)
            if w >= 2 * n:
                test_idx = random.sample(range(w), w - n)
                err = sum(1 for idx in test_idx if s_alice[idx] != s_bob[idx])
                qber = (err / (w - n)) * 100.0 if (w - n) > 0 else 0.0
                if qber <= 11.0:
                    loc_succ += 1
        local_rates.append(loc_succ / trials * 100.0)

        # IBM Quantum
        ibm_succ = 0
        for _ in range(trials):
            sim = qkd.simulate_bb84_protocal(key_size=total_q, per_time_bits=total_q, has_eavesdropping=False, use_ibm=True, channel_noise=0.025)
            s_alice = qkd.filter_key_by_basis(sim['server_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            s_bob = qkd.filter_key_by_basis(sim['client_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            w = len(s_alice)
            if w >= 2 * n:
                test_idx = random.sample(range(w), w - n)
                err = sum(1 for idx in test_idx if s_alice[idx] != s_bob[idx])
                qber = (err / (w - n)) * 100.0 if (w - n) > 0 else 0.0
                if qber <= 11.0:
                    ibm_succ += 1
        ibm_rates.append(ibm_succ / trials * 100.0)

    fig, ax = plt.subplots(figsize=(7.5, 4.6), facecolor='white')
    ax.plot(deltas, theory_rates, color='#64748b', linestyle='--', linewidth=2.0, marker='s', markersize=6, label='Theory (Binomial)', zorder=2)
    ax.plot(deltas, local_rates, color='#2563eb', linestyle='-', linewidth=2.6, marker='o', markersize=7, label='Local Simulator', zorder=3)
    ax.plot(deltas, ibm_rates, color='#ea580c', linestyle='-', linewidth=2.6, marker='^', markersize=7, label='IBM Quantum (Noise 2.5%)', zorder=4)

    for d, loc_val, ibm_val in zip(deltas, local_rates, ibm_rates):
        ax.text(d, loc_val + 2.8, f"{loc_val:.0f}%", ha='center', va='bottom', fontsize=9.5, fontweight='bold', color='#1d4ed8')
        ax.text(d, ibm_val - 4.5, f"{ibm_val:.0f}%", ha='center', va='top', fontsize=9.5, fontweight='bold', color='#c2410c')

    ax.axhline(90.0, color='#f59e0b', linestyle=':', linewidth=1.3, alpha=0.8, zorder=1)
    ax.text(0.01, 91.0, '90% Benchmark', fontsize=9.0, color='#b45309', fontweight='bold')

    ax.set_title("Key Generation Success Rate vs. Safety Margin δ (n = 24 bits)\n[100 Trials per Test Case]", pad=12, fontsize=12)
    ax.set_xlabel(r"Safety Margin Parameter $\delta$   [$N = \lceil (4 + \delta) \times 24 \rceil$]", labelpad=8)
    ax.set_ylabel("Success Rate |K| >= 24 (%)", labelpad=8)
    ax.set_xticks(deltas)
    ax.set_xticklabels([f"δ = {d}\n({service.calculate_key_length(d, 24)}Q)" for d in deltas])
    ax.set_ylim(40, 108)
    ax.grid(True, zorder=0)
    ax.legend(loc='lower right', framealpha=0.95, fontsize=10)

    save_fig(fig, "keysizing_graph1_delta_24bits.png")
    save_fig(fig, "keysizing_single_comparison.png")
    plt.close(fig)


# ==============================================================================
# GRAPH 2: Optimal Safety Margin delta* vs. Key Size n in [8, 16, 24, 32, 40]
# ==============================================================================
def make_graph2(trials: int = 100):
    random.seed(42)
    key_sizes = [8, 16, 24, 32, 40]
    
    # Grid of candidate deltas to evaluate
    delta_search = [round(x, 2) for x in np.linspace(0.1, 1.8, 35)]

    # 1. Theoretical Optimal delta for 90% and 95%
    theo_opt_90 = []
    theo_opt_95 = []
    for n in key_sizes:
        # 90%
        d90 = next((d for d in delta_search if sum(comb(service.calculate_key_length(d, n), k) * (0.5**service.calculate_key_length(d, n)) for k in range(2*n, service.calculate_key_length(d, n)+1))*100.0 >= 90.0), 1.0)
        theo_opt_90.append(d90)
        # 95%
        d95 = next((d for d in delta_search if sum(comb(service.calculate_key_length(d, n), k) * (0.5**service.calculate_key_length(d, n)) for k in range(2*n, service.calculate_key_length(d, n)+1))*100.0 >= 95.0), 1.2)
        theo_opt_95.append(d95)

    # 2. Empirical Local Simulator: Find lowest delta achieving >=90%
    empirical_local_90 = []
    empirical_ibm_90 = []
    eval_delta_candidates = [0.2, 0.4, 0.6, 0.8, 1.0, 1.2]

    print("Running Graph 2: Optimal delta vs. Key Size n...")
    for n in key_sizes:
        # Local Sim Search
        best_loc = 1.0
        for d in eval_delta_candidates:
            total_q = service.calculate_key_length(d, n)
            succ = 0
            for _ in range(trials):
                sim = qkd.simulate_bb84_protocal(key_size=total_q, per_time_bits=total_q, has_eavesdropping=False, use_ibm=False, channel_noise=0.0)
                s_alice = qkd.filter_key_by_basis(sim['server_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
                s_bob = qkd.filter_key_by_basis(sim['client_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
                w = len(s_alice)
                if w >= 2 * n:
                    test_idx = random.sample(range(w), w - n)
                    err = sum(1 for idx in test_idx if s_alice[idx] != s_bob[idx])
                    qber = (err / (w - n)) * 100.0 if (w - n) > 0 else 0.0
                    if qber <= 11.0:
                        succ += 1
            if (succ / trials * 100.0) >= 90.0:
                best_loc = d
                break
        empirical_local_90.append(best_loc)

        # IBM Quantum Search
        best_ibm = 1.0
        for d in eval_delta_candidates:
            total_q = service.calculate_key_length(d, n)
            succ = 0
            for _ in range(trials):
                sim = qkd.simulate_bb84_protocal(key_size=total_q, per_time_bits=total_q, has_eavesdropping=False, use_ibm=True, channel_noise=0.025)
                s_alice = qkd.filter_key_by_basis(sim['server_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
                s_bob = qkd.filter_key_by_basis(sim['client_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
                w = len(s_alice)
                if w >= 2 * n:
                    test_idx = random.sample(range(w), w - n)
                    err = sum(1 for idx in test_idx if s_alice[idx] != s_bob[idx])
                    qber = (err / (w - n)) * 100.0 if (w - n) > 0 else 0.0
                    if qber <= 11.0:
                        succ += 1
            if (succ / trials * 100.0) >= 90.0:
                best_ibm = d
                break
        empirical_ibm_90.append(best_ibm)

    fig, ax = plt.subplots(figsize=(7.5, 4.6), facecolor='white')

    # Continuous smooth theoretical curve
    n_smooth = np.linspace(8, 40, 100)
    # Asymptotic formula delta*(n) ~ 2 * z_alpha / sqrt(n) where z_0.90 = 1.282
    delta_th_curve = (1.282**2 + np.sqrt(1.282**4 + 16 * n_smooth * (1.282**2))) / (2 * n_smooth)
    ax.plot(n_smooth, delta_th_curve, color='#64748b', linestyle='--', linewidth=2.0, label='Theory Curve (90% Reliability)', zorder=2)

    # Measured Points
    ax.plot(key_sizes, empirical_local_90, color='#2563eb', linestyle='-', linewidth=2.5, marker='o', markersize=7.5, label='Local Sim Optimal δ* (≥90%)', zorder=3)
    ax.plot(key_sizes, empirical_ibm_90, color='#ea580c', linestyle='-', linewidth=2.5, marker='^', markersize=7.5, label='IBM Quantum Optimal δ* (≥90%)', zorder=4)

    # Clean annotations on empirical points
    for n_val, d_loc in zip(key_sizes, empirical_local_90):
        ax.text(n_val, d_loc - 0.05, f"δ={d_loc}", ha='center', va='top', fontsize=9.5, fontweight='bold', color='#1d4ed8')
    for n_val, d_ibm in zip(key_sizes, empirical_ibm_90):
        if d_ibm != empirical_local_90[key_sizes.index(n_val)]:
            ax.text(n_val, d_ibm + 0.04, f"δ={d_ibm}", ha='center', va='bottom', fontsize=9.5, fontweight='bold', color='#c2410c')

    ax.set_title("Optimal Safety Margin δ* vs. Target Key Size n\n[100 Trials per Test Case]", pad=12, fontsize=12)
    ax.set_xlabel("Target Key Size n (bits)  [1 to 5 ASCII Characters]", labelpad=8)
    ax.set_ylabel("Minimum Safety Margin δ* for ≥ 90% Success", labelpad=8)
    ax.set_xticks(key_sizes)
    ax.set_xticklabels([f"n = {n}\n({n//8} char)" for n in key_sizes])
    ax.set_ylim(0.2, 1.2)
    ax.grid(True, zorder=0)
    ax.legend(loc='upper right', framealpha=0.95, fontsize=10)

    save_fig(fig, "keysizing_graph2_optimal_delta_vs_keysize.png")
    plt.close(fig)


def main():
    make_graph1(trials=100)
    make_graph2(trials=100)
    print("\n[OK] Both graphs successfully generated with exactly 100 trials per case!")


if __name__ == "__main__":
    main()
