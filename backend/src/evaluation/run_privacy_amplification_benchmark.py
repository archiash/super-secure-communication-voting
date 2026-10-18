"""
Privacy Amplification Benchmark & Eve Knowledge Elimination Suite
Evaluates the scenario where eavesdropping occurs and goes undetected (QBER <= 11% threshold).
Quantifies:
1. Number of bits Eve knows BEFORE Privacy Amplification (k_before)
2. Number of bits Eve knows AFTER Privacy Amplification (k_after via GF(2) rank analysis)
3. Percentage of sessions where Eve's knowledge FULLY disappears (k_after == 0)
Tested across:
- Key sizes: n in [8, 16, 32, 64, 128, 256] bits
- Security parameters: s in [8, 16, 32] bits
Caches raw data and renders publication-grade minimal visualizations.
"""

import os
import sys
import json
import math
import numpy as np
import matplotlib.pyplot as plt

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from modules import privacy_amplification as pa

DATA_DIR = os.path.join(CURRENT_DIR, "data")
PLOTS_DIR = os.path.join(CURRENT_DIR, "plots")
REPORT_FIG_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", "report", "figures"))
REPORT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", "report"))
ARTIFACT_DIR = r"C:\Users\Archiash\.gemini\antigravity\brain\fe188d27-1463-46c3-aca9-529a07ed20b1"

for d in [DATA_DIR, PLOTS_DIR, REPORT_FIG_DIR, REPORT_DIR, ARTIFACT_DIR]:
    os.makedirs(d, exist_ok=True)

RAW_DATA_PATH = os.path.join(DATA_DIR, "privacy_amplification_raw_data.json")
MASTER_DATA_PATH = os.path.join(DATA_DIR, "master_benchmark_raw_data.json")


def gf2_rank(matrix: np.ndarray) -> int:
    """Compute the rank of a binary matrix over GF(2) using Gaussian elimination."""
    M = matrix.copy() % 2
    nrows, ncols = M.shape
    r = 0
    for c in range(ncols):
        pivot = -1
        for row in range(r, nrows):
            if M[row, c] == 1:
                pivot = row
                break
        if pivot == -1:
            continue
        M[[r, pivot]] = M[[pivot, r]]
        for row in range(r + 1, nrows):
            if M[row, c] == 1:
                M[row] ^= M[r]
        r += 1
        if r == nrows:
            break
    return r


def run_benchmark(trials: int = 100, force_retest: bool = False) -> dict:
    if os.path.exists(RAW_DATA_PATH) and not force_retest:
        print(f"[CACHE FOUND] Loading Privacy Amplification data from: {RAW_DATA_PATH}")
        with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    print("=" * 75)
    print("RUNNING PRIVACY AMPLIFICATION BENCHMARK: EVE KNOWLEDGE ELIMINATION")
    print(f"Trials per condition: {trials} | Key sizes: [8, 16, 32, 64, 128, 256] | s: [8, 16, 32]")
    print("=" * 75)

    key_sizes = [8, 16, 32, 64, 128, 256]
    security_params = [8, 16, 32]
    # Stealth eavesdropping: Eve attacks fraction eta such that QBER = 8.0% (< 11% threshold)
    # Undetected: Alice and Bob accept the key and proceed to Privacy Amplification
    undetected_qber = 0.08
    results = {}

    for n in key_sizes:
        results[str(n)] = {}
        for s in security_params:
            print(f" -> Testing Target Key Size n = {n:3d} bits | Security Parameter s = {s:2d} bits...")
            N_raw = pa.calculate_required_raw_length(target_key_length=n, security_parameter=s, qber=undetected_qber)
            
            k_before_list = []
            k_after_list = []
            disappeared_count = 0

            for _ in range(trials):
                # Eve intercepts qubits with probability eta = 4 * qber = 0.32
                # In sifted key, Eve knows bit if her basis matched Alice's (prob = 0.5 * eta = 2 * qber = 0.16)
                known_mask = np.random.rand(N_raw) < (2.0 * undetected_qber)
                k_before = int(np.sum(known_mask))
                k_before_list.append(k_before)

                unknown_indices = np.where(~known_mask)[0]
                seed = pa.generate_toeplitz_seed(N_raw, n)
                T = pa.construct_toeplitz_matrix(seed, n, N_raw)
                
                # Unknown columns to Eve
                T_unknown = T[:, unknown_indices]
                r = gf2_rank(T_unknown)
                k_after = max(0, n - r)
                k_after_list.append(k_after)

                if k_after == 0:
                    disappeared_count += 1

            pct_disappeared = (disappeared_count / trials) * 100.0
            results[str(n)][str(s)] = {
                "n_target": n,
                "security_parameter": s,
                "n_raw_input": N_raw,
                "undetected_qber": undetected_qber,
                "k_before_mean": float(np.mean(k_before_list)),
                "k_before_std": float(np.std(k_before_list)),
                "k_after_mean": float(np.mean(k_after_list)),
                "k_after_max": int(np.max(k_after_list)),
                "pct_fully_disappeared": float(pct_disappeared),
                "leftover_hash_leakage_bound": float(2.0 ** (-s) / math.log(2))
            }

    raw_data = {
        "metadata": {
            "trials_per_condition": trials,
            "undetected_qber_scenario": undetected_qber,
            "key_sizes": key_sizes,
            "security_parameters": security_params,
            "hash_family": "2-Universal Toeplitz Hashing over GF(2)"
        },
        "results": results
    }

    with open(RAW_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, indent=2)
    print(f"\n[CACHE SAVED] Raw data saved to {RAW_DATA_PATH}")

    # Also update master_benchmark_raw_data.json
    if os.path.exists(MASTER_DATA_PATH):
        try:
            with open(MASTER_DATA_PATH, "r", encoding="utf-8") as f:
                master = json.load(f)
            master["privacy_amplification_analysis"] = raw_data
            with open(MASTER_DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(master, f, indent=2)
            print(f"[MASTER SYNC] Synced Privacy Amplification results into master cache.")
        except Exception as e:
            print(f"[MASTER SYNC WARNING] {e}")

    return raw_data


def save_minimal(fig, filename):
    for target in [PLOTS_DIR, REPORT_FIG_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path = os.path.join(target, filename)
        fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    print(f" -> [SAVED] {filename}")


def plot_results(data: dict):
    # Minimalist matplotlib settings
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Segoe UI', 'DejaVu Sans', 'Arial'],
        'axes.edgecolor': '#94a3b8',
        'axes.linewidth': 0.85,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.titlelocation': 'left',
        'axes.titlesize': 11.0,
        'axes.titleweight': 'bold',
        'axes.titlecolor': '#0f172a',
        'axes.labelcolor': '#475569',
        'axes.labelsize': 9.2,
        'xtick.color': '#64748b',
        'ytick.color': '#64748b',
        'xtick.labelsize': 8.8,
        'ytick.labelsize': 8.8,
        'grid.color': '#f8fafc',
        'grid.linestyle': '-',
        'grid.linewidth': 0.75
    })

    results = data["results"]
    key_sizes = [int(k) for k in results.keys()]
    sec_params = [8, 16, 32]
    x_pos = np.arange(len(key_sizes))

    # ==========================================================================
    # FIGURE 1: Eve Known Bits Before vs. After Privacy Amplification
    # ==========================================================================
    fig, ax = plt.subplots(figsize=(7.6, 4.8), facecolor='white')
    
    # We plot Before PA for s=16 (baseline) vs After PA for s=8, s=16, s=32
    before_s16 = [results[str(k)]["16"]["k_before_mean"] for k in key_sizes]
    after_s8 = [results[str(k)]["8"]["k_after_mean"] for k in key_sizes]
    after_s16 = [results[str(k)]["16"]["k_after_mean"] for k in key_sizes]
    after_s32 = [results[str(k)]["32"]["k_after_mean"] for k in key_sizes]

    w = 0.20
    b0 = ax.bar(x_pos - 1.5 * w, before_s16, w, label='Before PA (Eve Raw Knowledge)', color='#e11d48', alpha=0.9, edgecolor='none')
    b1 = ax.bar(x_pos - 0.5 * w, after_s8, w, label='After PA (s = 8 bits)', color='#f59e0b', alpha=0.9, edgecolor='none')
    b2 = ax.bar(x_pos + 0.5 * w, after_s16, w, label='After PA (s = 16 bits)', color='#0284c7', alpha=0.9, edgecolor='none')
    b3 = ax.bar(x_pos + 1.5 * w, after_s32, w, label='After PA (s = 32 bits)', color='#059669', alpha=0.9, edgecolor='none')

    # Value annotations for Figure 1
    for i in range(len(key_sizes)):
        ax.text(x_pos[i] - 1.5 * w, before_s16[i] + 0.8, f"{before_s16[i]:.1f}b", ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#9f1239')
        v8 = after_s8[i]
        v16 = after_s16[i]
        v32 = after_s32[i]
        txt8 = f"{v8:.2f}" if v8 > 0 else "0"
        txt16 = f"{v16:.2f}" if v16 > 0 else "0"
        txt32 = f"{v32:.2f}" if v32 > 0 else "0"
        ax.text(x_pos[i] - 0.5 * w, max(0.4, v8) + 0.5, txt8, ha='center', va='bottom', fontsize=7.8, fontweight='bold', color='#b45309', rotation=90)
        ax.text(x_pos[i] + 0.5 * w, max(0.4, v16) + 0.5, txt16, ha='center', va='bottom', fontsize=7.8, fontweight='bold', color='#0369a1', rotation=90)
        ax.text(x_pos[i] + 1.5 * w, max(0.4, v32) + 0.5, txt32, ha='center', va='bottom', fontsize=7.8, fontweight='bold', color='#047857', rotation=90)

    ax.set_title("Eve Eavesdropping Knowledge: Before vs. After Privacy Amplification", pad=14)
    ax.set_xlabel("Target Key Size n (bits)")
    ax.set_ylabel("Eve Known Bits (bits)")
    ax.set_xticks(x_pos)
    ax.set_xticklabels([f"{k}b" for k in key_sizes])
    ax.set_ylim(0, max(before_s16) * 1.18)
    ax.grid(axis='y', linestyle='-', linewidth=0.7, color='#f1f5f9')
    
    # Legend placed strictly outside to the right
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1.0), frameon=False, fontsize=8.6, handletextpad=0.5, labelspacing=0.8)

    save_minimal(fig, "minimal_privacy_amplification_before_after.png")
    plt.close(fig)

    # ==========================================================================
    # FIGURE 2: Percentage of Sessions Where Eve Knowledge Fully Disappeared
    # ==========================================================================
    fig, ax = plt.subplots(figsize=(7.6, 4.6), facecolor='white')

    pct_s8 = [results[str(k)]["8"]["pct_fully_disappeared"] for k in key_sizes]
    pct_s16 = [results[str(k)]["16"]["pct_fully_disappeared"] for k in key_sizes]
    pct_s32 = [results[str(k)]["32"]["pct_fully_disappeared"] for k in key_sizes]

    ax.plot(x_pos, pct_s32, marker='s', markersize=6.5, color='#059669', linewidth=2.0, label=f'Security Parameter s = 32 (Avg: {np.mean(pct_s32):.1f}% Erased)')
    ax.plot(x_pos, pct_s16, marker='o', markersize=6.0, color='#0284c7', linewidth=1.8, label=f'Security Parameter s = 16 (Avg: {np.mean(pct_s16):.1f}% Erased)')
    ax.plot(x_pos, pct_s8, marker='^', markersize=6.0, color='#f59e0b', linewidth=1.6, linestyle='--', label=f'Security Parameter s = 8 (Avg: {np.mean(pct_s8):.1f}% Erased)')

    for i in range(len(key_sizes)):
        ax.text(x_pos[i], pct_s32[i] + 1.2, f"{pct_s32[i]:.0f}%", ha='center', va='bottom', fontsize=8.4, fontweight='bold', color='#047857')
        if pct_s16[i] < 100.0:
            ax.text(x_pos[i] + 0.15, pct_s16[i] - 1.6, f"{pct_s16[i]:.0f}%", ha='left', va='top', fontsize=8.2, fontweight='bold', color='#0369a1')
        ax.text(x_pos[i], pct_s8[i] - 1.5, f"{pct_s8[i]:.0f}%", ha='center', va='top', fontsize=8.2, fontweight='bold', color='#b45309')

    ax.set_title("Probability of Complete Eve Knowledge Elimination (k_after = 0 bits)", pad=14)
    ax.set_xlabel("Target Key Size n (bits)")
    ax.set_ylabel("Full Elimination Percentage (%)")
    ax.set_xticks(x_pos)
    ax.set_xticklabels([f"{k}b" for k in key_sizes])
    min_pct = min(min(pct_s8), min(pct_s16), min(pct_s32))
    ax.set_ylim(min(75, min_pct - 5), 106)
    
    # Legend strictly outside to the right
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1.0), frameon=False, fontsize=8.6, handletextpad=0.5, labelspacing=0.8)

    save_minimal(fig, "minimal_privacy_amplification_elimination_rate.png")
    plt.close(fig)

    # ==========================================================================
    # FIGURE 3: Unified 2-Panel Summary (Before/After Knowledge & Elimination Rate)
    # ==========================================================================
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.2, 5.4), facecolor='white')
    
    # Subplot 1: Before vs After PA (Bar Chart)
    b0 = ax1.bar(x_pos - 1.5 * w, before_s16, w, label='Before PA (Eve Raw Knowledge)', color='#e11d48', alpha=0.9, edgecolor='none')
    b1 = ax1.bar(x_pos - 0.5 * w, [max(0.3, v) for v in after_s8], w, label='After PA (s = 8b)', color='#f59e0b', alpha=0.9, edgecolor='none')
    b2 = ax1.bar(x_pos + 0.5 * w, [max(0.3, v) for v in after_s16], w, label='After PA (s = 16b)', color='#0284c7', alpha=0.9, edgecolor='none')
    b3 = ax1.bar(x_pos + 1.5 * w, [max(0.3, v) for v in after_s32], w, label='After PA (s = 32b)', color='#059669', alpha=0.9, edgecolor='none')

    for i in range(len(key_sizes)):
        ax1.text(x_pos[i] - 1.5 * w, before_s16[i] + 0.8, f"{before_s16[i]:.1f}b", ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#9f1239')
        v8 = after_s8[i]
        v16 = after_s16[i]
        v32 = after_s32[i]
        txt8 = f"{v8:.2f}" if v8 > 0 else "0"
        txt16 = f"{v16:.2f}" if v16 > 0 else "0"
        txt32 = f"{v32:.2f}" if v32 > 0 else "0"
        ax1.text(x_pos[i] - 0.5 * w, max(0.4, v8) + 0.5, txt8, ha='center', va='bottom', fontsize=7.8, fontweight='bold', color='#b45309', rotation=90)
        ax1.text(x_pos[i] + 0.5 * w, max(0.4, v16) + 0.5, txt16, ha='center', va='bottom', fontsize=7.8, fontweight='bold', color='#0369a1', rotation=90)
        ax1.text(x_pos[i] + 1.5 * w, max(0.4, v32) + 0.5, txt32, ha='center', va='bottom', fontsize=7.8, fontweight='bold', color='#047857', rotation=90)

    ax1.set_title("A. Eve Known Bits: Before vs. After Privacy Amplification", pad=14, fontsize=10.5, fontweight='bold')
    ax1.set_xlabel("Target Key Size n (bits)")
    ax1.set_ylabel("Eve Known Bits (bits)")
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels([f"{k}b" for k in key_sizes])
    ax1.set_ylim(0, max(before_s16) * 1.18)
    ax1.grid(axis='y', linestyle='-', linewidth=0.7, color='#f1f5f9')
    ax1.legend(loc='upper left', frameon=False, fontsize=8.4)

    # Subplot 2: Full Knowledge Disappearance Rate (%)
    ax2.plot(x_pos, pct_s32, marker='s', markersize=6.5, color='#059669', linewidth=2.0, label=f's = 32 bits (Avg: {np.mean(pct_s32):.1f}% Erased)')
    ax2.plot(x_pos, pct_s16, marker='o', markersize=6.0, color='#0284c7', linewidth=1.8, label=f's = 16 bits (Avg: {np.mean(pct_s16):.1f}% Erased)')
    ax2.plot(x_pos, pct_s8, marker='^', markersize=6.0, color='#f59e0b', linewidth=1.6, linestyle='--', label=f's = 8 bits (Avg: {np.mean(pct_s8):.1f}% Erased)')

    for i in range(len(key_sizes)):
        ax2.text(x_pos[i], pct_s32[i] + 1.2, f"{pct_s32[i]:.0f}%", ha='center', va='bottom', fontsize=8.4, fontweight='bold', color='#047857')
        if pct_s16[i] < 100.0:
            ax2.text(x_pos[i] + 0.15, pct_s16[i] - 1.6, f"{pct_s16[i]:.0f}%", ha='left', va='top', fontsize=8.2, fontweight='bold', color='#0369a1')
        ax2.text(x_pos[i], pct_s8[i] - 1.5, f"{pct_s8[i]:.0f}%", ha='center', va='top', fontsize=8.2, fontweight='bold', color='#b45309')

    ax2.set_title("B. Probability of Complete Knowledge Elimination (k_after = 0)", pad=14, fontsize=10.5, fontweight='bold')
    ax2.set_xlabel("Target Key Size n (bits)")
    ax2.set_ylabel("Full Elimination Percentage (%)")
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels([f"{k}b" for k in key_sizes])
    ax2.set_ylim(min(75, min_pct - 5), 106)
    ax2.grid(axis='y', linestyle='-', linewidth=0.7, color='#f1f5f9')
    ax2.legend(loc='lower left', frameon=False, fontsize=8.4)

    plt.subplots_adjust(wspace=0.22)
    save_minimal(fig, "minimal_privacy_amplification_summary.png")
    plt.close(fig)

    print("\n[COMPLETE] All Privacy Amplification evaluation figures generated successfully!")


if __name__ == "__main__":
    raw_data = run_benchmark(trials=100, force_retest=True)
    plot_results(raw_data)
