"""
Priority 2 Suite with Data Caching & Minimalist External Text Formatting
Saves raw simulation data to JSON for instant re-plotting without re-testing.

Features:
1. All descriptions and metrics placed OUTSIDE the plot canvas.
2. Axis labels sized down cleanly (fontsize=9.2).
3. Raw trial data saved to backend/src/evaluation/data/priority2_raw_data.json.
4. If raw data exists, re-plots instantly without re-running quantum simulation.
"""

import os
import sys
import json
import random
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from modules import qkd, service

DATA_DIR = os.path.join(CURRENT_DIR, "data")
PLOTS_DIR = os.path.join(CURRENT_DIR, "plots")
REPORT_FIG_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", "report", "figures"))
REPORT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", "report"))
ARTIFACT_DIR = r"C:\Users\Archiash\.gemini\antigravity\brain\fe188d27-1463-46c3-aca9-529a07ed20b1"

for d in [DATA_DIR, PLOTS_DIR, REPORT_FIG_DIR, REPORT_DIR, ARTIFACT_DIR]:
    os.makedirs(d, exist_ok=True)

RAW_DATA_PATH = os.path.join(DATA_DIR, "priority2_raw_data.json")

def save_minimal(fig, filename):
    for target in [PLOTS_DIR, REPORT_FIG_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path = os.path.join(target, filename)
        fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    print(f"[SAVED] {filename}")

# ------------------------------------------------------------------------------
# 1. Simulation & Data Caching
# ------------------------------------------------------------------------------
def generate_or_load_data(trials: int = 100, force_retest: bool = False):
    if os.path.exists(RAW_DATA_PATH) and not force_retest:
        print(f"[CACHE] Loading cached raw data from {RAW_DATA_PATH} (No re-test needed)...")
        with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    print(f"[SIMULATION] Running 100 trials per case and saving raw data to {RAW_DATA_PATH}...")
    random.seed(42)
    np.random.seed(42)

    # 1.1 Scatter Data (n = 24 bits)
    n = 24
    total_q = service.calculate_key_length(0.8, n)

    # Normal (Ideal / Local Sim)
    s_normal, k_normal = [], []
    for _ in range(trials):
        sim = qkd.simulate_bb84_protocal(key_size=total_q, per_time_bits=total_q, has_eavesdropping=False, use_ibm=False, channel_noise=0.0)
        s_a = qkd.filter_key_by_basis(sim['server_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
        s_b = qkd.filter_key_by_basis(sim['client_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
        w = len(s_a)
        if w >= 2 * n:
            test_idx = set(random.sample(range(w), w - n))
            key_idx = [i for i in range(w) if i not in test_idx][:n]
            s_q = (sum(1 for i in test_idx if s_a[i] != s_b[i]) / len(test_idx)) * 100.0
            k_q = (sum(1 for i in key_idx if s_a[i] != s_b[i]) / len(key_idx)) * 100.0
            s_normal.append(s_q)
            k_normal.append(k_q)

    # IBM Hardware Noise (2.82% live QPU noise from ibm_kingston)
    s_ibm, k_ibm = [], []
    for _ in range(trials):
        sim = qkd.simulate_bb84_protocal(key_size=total_q, per_time_bits=total_q, has_eavesdropping=False, use_ibm=True, channel_noise=0.0282)
        s_a = qkd.filter_key_by_basis(sim['server_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
        s_b = qkd.filter_key_by_basis(sim['client_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
        w = len(s_a)
        if w >= 2 * n:
            test_idx = set(random.sample(range(w), w - n))
            key_idx = [i for i in range(w) if i not in test_idx][:n]
            s_q = (sum(1 for i in test_idx if s_a[i] != s_b[i]) / len(test_idx)) * 100.0
            k_q = (sum(1 for i in key_idx if s_a[i] != s_b[i]) / len(key_idx)) * 100.0
            s_ibm.append(s_q)
            k_ibm.append(k_q)

    # Active Eve (Intercept-Resend)
    s_eve, k_eve = [], []
    for _ in range(trials):
        sim = qkd.simulate_bb84_protocal(key_size=total_q, per_time_bits=total_q, has_eavesdropping=True, use_ibm=False, channel_noise=0.0)
        s_a = qkd.filter_key_by_basis(sim['server_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
        s_b = qkd.filter_key_by_basis(sim['client_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
        w = len(s_a)
        if w >= 2 * n:
            test_idx = set(random.sample(range(w), w - n))
            key_idx = [i for i in range(w) if i not in test_idx][:n]
            s_q = (sum(1 for i in test_idx if s_a[i] != s_b[i]) / len(test_idx)) * 100.0
            k_q = (sum(1 for i in key_idx if s_a[i] != s_b[i]) / len(key_idx)) * 100.0
            s_eve.append(s_q)
            k_eve.append(k_q)

    # 1.2 Convergence across Powers of 2
    key_sizes = [8, 16, 32, 64, 128, 256]
    convergence_data = {}
    for ks in key_sizes:
        tq = service.calculate_key_length(0.8, ks)
        biases = []
        for _ in range(trials):
            sim = qkd.simulate_bb84_protocal(key_size=tq, per_time_bits=min(64, tq), has_eavesdropping=True, use_ibm=False, channel_noise=0.0)
            s_a = qkd.filter_key_by_basis(sim['server_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            s_b = qkd.filter_key_by_basis(sim['client_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            w = len(s_a)
            if w >= 2 * ks:
                test_idx = set(random.sample(range(w), w - ks))
                key_idx = [i for i in range(w) if i not in test_idx][:ks]
                sq = (sum(1 for i in test_idx if s_a[i] != s_b[i]) / len(test_idx)) * 100.0
                kq = (sum(1 for i in key_idx if s_a[i] != s_b[i]) / len(key_idx)) * 100.0
                biases.append(abs(sq - kq))
            else:
                biases.append(0.0)
        convergence_data[str(ks)] = {
            "mean_bias": float(np.mean(biases)),
            "std_bias": float(np.std(biases)),
            "qubits": tq,
            "sample_size": tq // 4
        }

    raw_data = {
        "trials": trials,
        "n_voting": 24,
        "scatter": {
            "normal": {"sample_qber": s_normal, "key_qber": k_normal},
            "ibm_hardware": {"sample_qber": s_ibm, "key_qber": k_ibm},
            "eve": {"sample_qber": s_eve, "key_qber": k_eve}
        },
        "convergence": convergence_data
    }

    with open(RAW_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, indent=2)
    print(f"[CACHE SAVED] Raw data saved to {RAW_DATA_PATH}")

    return raw_data


# ------------------------------------------------------------------------------
# 2. Ultra-Clean Minimal Plotting (All text outside, smaller axis labels)
# ------------------------------------------------------------------------------
def plot_priority2(raw_data):
    # Minimalist rcParams
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Segoe UI', 'DejaVu Sans', 'Arial'],
        'axes.edgecolor': '#94a3b8',
        'axes.linewidth': 0.85,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.titlelocation': 'left',
        'axes.titlesize': 11.5,
        'axes.titleweight': 'bold',
        'axes.titlecolor': '#0f172a',
        'axes.labelcolor': '#475569',
        'axes.labelsize': 9.2,          # Made smaller as requested
        'xtick.color': '#64748b',
        'ytick.color': '#64748b',
        'xtick.labelsize': 8.8,
        'ytick.labelsize': 8.8,
        'grid.color': '#f1f5f9',
        'grid.linestyle': '-',
        'grid.linewidth': 0.75
    })

    # ==========================================================================
    # Figure 1: Scatter Plot (Text strictly outside, clean canvas)
    # ==========================================================================
    sc = raw_data["scatter"]
    s_norm, k_norm = sc["normal"]["sample_qber"], sc["normal"]["key_qber"]
    s_ibm, k_ibm = sc["ibm_hardware"]["sample_qber"], sc["ibm_hardware"]["key_qber"]
    s_eve, k_eve = sc["eve"]["sample_qber"], sc["eve"]["key_qber"]

    fig, ax = plt.subplots(figsize=(7.6, 5.0), facecolor='white')

    # Data points
    ax.scatter(s_norm, k_norm, color='#2563eb', alpha=0.55, s=30, edgecolors='none', label='Ideal / No Noise (0.0%)')
    ax.scatter(s_ibm, k_ibm, color='#059669', alpha=0.60, s=32, edgecolors='none', label='IBM Hardware Noise (2.8%)')
    ax.scatter(s_eve, k_eve, color='#e11d48', alpha=0.60, s=34, edgecolors='none', label='With Eve Attack (24.8%)')

    # Ideal diagonal line
    ax.plot([0, 48], [0, 48], color='#94a3b8', linestyle=':', linewidth=1.2, label='Ideal Estimator (y = x)')

    # 11% Abort Threshold lines (NO text inside the canvas)
    ax.axvline(11.0, color='#be123c', linestyle='--', linewidth=1.1, alpha=0.75)
    ax.axhline(11.0, color='#be123c', linestyle='--', linewidth=1.1, alpha=0.75)
    ax.plot([], [], color='#be123c', linestyle='--', linewidth=1.1, label='11% Security Threshold')

    ax.set_title("Blind Security Verification: Sample QBER vs. Key QBER (24 bits)", pad=14, fontsize=11.0, fontweight='bold', color='#0f172a')
    ax.set_xlabel("Sacrificed Sample QBER (%) [Publicly Measured]")
    ax.set_ylabel("Hidden Secret Key QBER (%) [Uninspected]")
    ax.set_xlim(-1, 48)
    ax.set_ylim(-1, 48)
    ax.grid(True, linestyle='-', linewidth=0.6, color='#f8fafc')
    
    # Color description strictly outside graph canvas
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1.0), frameon=False, fontsize=8.6, handletextpad=0.5, labelspacing=0.8)

    # ALL TEXT DESCRIPTIONS OUTSIDE THE GRAPH (below the figure)
    all_s = s_norm + s_ibm + s_eve
    all_k = k_norm + k_ibm + k_eve
    corr = np.corrcoef(all_s, all_k)[0, 1]
    mean_bias = np.mean(np.abs(np.array(all_s) - np.array(all_k)))

    desc_line1 = f"Overall Correlation: r = {corr:.2f}   |   Mean Absolute Bias: |Q_sample - Q_key| = {mean_bias:.2f}%"
    desc_line2 = "Dashed red lines mark the 11% Security Abort Threshold (Safe Zone: <11% | Abort Zone: >11%)"
    fig.text(0.42, -0.04, desc_line1, ha='center', fontsize=8.6, fontweight='bold', color='#334155')
    fig.text(0.42, -0.08, desc_line2, ha='center', fontsize=8.0, color='#64748b')

    save_minimal(fig, "minimal_priority2_sample_vs_key_scatter.png")
    plt.close(fig)

    # ==========================================================================
    # Figure 2: Convergence Curve (Text strictly outside, smaller axis labels)
    # ==========================================================================
    conv = raw_data["convergence"]
    key_sizes = [int(k) for k in conv.keys()]
    mean_biases = [conv[str(k)]["mean_bias"] for k in key_sizes]
    x_positions = np.arange(len(key_sizes))

    fig, ax = plt.subplots(figsize=(6.4, 4.2), facecolor='white')

    ax.plot(x_positions, mean_biases, marker='o', markersize=5.5, color='#0284c7', linewidth=1.8, label='Estimate Different Bias')

    # Minimal numbers directly on points
    for i, n in enumerate(key_sizes):
        ax.text(x_positions[i], mean_biases[i] + 0.35, f"{mean_biases[i]:.2f}%", ha='center', fontsize=8.5, fontweight='bold', color='#0369a1')

    ax.set_title("Sample QBER Estimation Accuracy vs. Target Key Size", pad=12)
    ax.set_xlabel("Target Key Size n (bits)")
    ax.set_ylabel("Mean Estimation Bias (%)")
    ax.set_xticks(x_positions)
    ax.set_xticklabels([f"{n}b" for n in key_sizes])
    ax.set_ylim(0, 20)
    ax.grid(axis='y', linestyle='-', linewidth=0.7, color='#f8fafc')
    ax.legend(frameon=False, loc='upper right', fontsize=8.6)

    save_minimal(fig, "minimal_priority2_estimation_error_vs_keysize.png")
    plt.close(fig)

    print("[SUCCESS] All Priority 2 minimalist graphs generated with outside text descriptions!")


if __name__ == "__main__":
    # Check if raw data exists; if so, load it without retest
    data = generate_or_load_data(trials=100, force_retest=False)
    plot_priority2(data)
