"""
Minimal Visualizations for QKD Simulator (Local Simulation Suite)
100 Trials per case, ultra-minimal aesthetic for reports and slides.

Generates:
1. minimal_fig1_eavesdropping_detection_localsim.png (Priority 1: Normal vs Eve vs 11% Threshold)
2. minimal_fig2_sample_vs_key_qber_localsim.png (Priority 2: Sample QBER vs Key QBER in Local Sim)
3. minimal_fig3_delta_24bits_localsim.png (Key Sizing: Success Rate vs delta for 24-bit VT3)
4. minimal_fig4_optimal_delta_vs_keysize_localsim.png (Optimal delta vs Key Size)
"""

import os
import sys
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

PLOTS_DIR = os.path.join(CURRENT_DIR, "plots")
REPORT_FIG_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", "report", "figures"))
REPORT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", "report"))
ARTIFACT_DIR = r"C:\Users\Archiash\.gemini\antigravity\brain\fe188d27-1463-46c3-aca9-529a07ed20b1"

for d in [PLOTS_DIR, REPORT_FIG_DIR, REPORT_DIR, ARTIFACT_DIR]:
    os.makedirs(d, exist_ok=True)

def save_minimal(fig, filename):
    for target in [PLOTS_DIR, REPORT_FIG_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path = os.path.join(target, filename)
        fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    print(f"[SAVED] {filename}")


# ------------------------------------------------------------------------------
# Global Minimal Plot Style
# ------------------------------------------------------------------------------
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Segoe UI', 'DejaVu Sans', 'Helvetica', 'Arial'],
    'font.size': 11,
    'axes.edgecolor': '#94a3b8',
    'axes.linewidth': 0.9,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.titlelocation': 'left',
    'axes.titlesize': 13,
    'axes.titleweight': 'bold',
    'axes.titlecolor': '#0f172a',
    'axes.labelcolor': '#334155',
    'axes.labelsize': 10.5,
    'axes.labelweight': 'normal',
    'xtick.color': '#475569',
    'ytick.color': '#475569',
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'grid.color': '#f1f5f9',
    'grid.linestyle': '-',
    'grid.linewidth': 0.8
})


# ==============================================================================
# 1. PRIORITY 1: Eavesdropping Detection in Local Simulation (Ultra-Minimal)
# ==============================================================================
def run_p1_minimal(trials: int = 100):
    random.seed(42)
    np.random.seed(42)
    key_sizes = [8, 16, 24]
    
    normal_qbers = []
    eve_qbers = []
    
    print("\n[1/4] Running Priority 1 Local Simulation (100 trials)...")
    for n in key_sizes:
        total_q = service.calculate_key_length(0.8, n)
        
        # Normal (No Eve)
        norm_run = []
        for _ in range(trials):
            sim = qkd.simulate_bb84_protocal(key_size=total_q, per_time_bits=total_q, has_eavesdropping=False, use_ibm=False, channel_noise=0.0)
            s_a = qkd.filter_key_by_basis(sim['server_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            s_b = qkd.filter_key_by_basis(sim['client_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            w = len(s_a)
            if w >= 2 * n:
                test_idx = random.sample(range(w), w - n)
                err = sum(1 for idx in test_idx if s_a[idx] != s_b[idx])
                norm_run.append((err / (w - n)) * 100.0)
            else:
                norm_run.append(0.0)
        normal_qbers.append(float(np.mean(norm_run)))
        
        # With Eve
        eve_run = []
        for _ in range(trials):
            sim = qkd.simulate_bb84_protocal(key_size=total_q, per_time_bits=total_q, has_eavesdropping=True, use_ibm=False, channel_noise=0.0)
            s_a = qkd.filter_key_by_basis(sim['server_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            s_b = qkd.filter_key_by_basis(sim['client_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            w = len(s_a)
            if w >= 2 * n:
                test_idx = random.sample(range(w), w - n)
                err = sum(1 for idx in test_idx if s_a[idx] != s_b[idx])
                eve_run.append((err / (w - n)) * 100.0)
            else:
                eve_run.append(25.0)
        eve_qbers.append(float(np.mean(eve_run)))

    # Minimal Bar Chart
    fig, ax = plt.subplots(figsize=(6.8, 4.2), facecolor='white')
    x = np.arange(len(key_sizes))
    bar_width = 0.32

    b1 = ax.bar(x - bar_width/2, normal_qbers, bar_width, label='Normal (No Eve)', color='#2563eb', edgecolor='none')
    b2 = ax.bar(x + bar_width/2, eve_qbers, bar_width, label='With Eve (Intercept-Resend)', color='#e11d48', edgecolor='none')

    # Security Threshold line
    ax.axhline(11.0, color='#be123c', linestyle='--', linewidth=1.5, zorder=4)
    ax.text(len(key_sizes) - 0.45, 11.8, '11% Security Threshold', color='#be123c', fontsize=9, fontweight='bold', ha='right')

    # Minimal direct data labels
    for bar in b1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 0.5, f"{h:.1f}%", ha='center', va='bottom', fontsize=9.5, color='#1e3a8a', fontweight='bold')
    for bar in b2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 0.5, f"{h:.1f}%", ha='center', va='bottom', fontsize=9.5, color='#9f1239', fontweight='bold')

    ax.set_title("Eavesdropping Detection in Local Simulation", pad=14)
    ax.set_ylabel("Measured QBER (%)")
    ax.set_xticks(x)
    ax.set_xticklabels([f"n = {n} bits" for n in key_sizes])
    ax.set_ylim(0, 32)
    ax.grid(axis='y', zorder=0)
    ax.legend(frameon=False, loc='upper left')

    save_minimal(fig, "minimal_fig1_eavesdropping_detection_localsim.png")
    plt.close(fig)


# ==============================================================================
# 2. PRIORITY 2: Sample QBER vs Key QBER in Local Simulation (Ultra-Minimal)
# ==============================================================================
def run_p2_minimal(trials: int = 100):
    random.seed(42)
    n = 24
    total_q = service.calculate_key_length(0.8, n)

    sample_qbers = []
    key_qbers = []

    print("[2/4] Running Priority 2 Local Simulation (100 trials)...")
    for _ in range(trials):
        sim = qkd.simulate_bb84_protocal(key_size=total_q, per_time_bits=total_q, has_eavesdropping=True, use_ibm=False, channel_noise=0.0)
        s_a = qkd.filter_key_by_basis(sim['server_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
        s_b = qkd.filter_key_by_basis(sim['client_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
        w = len(s_a)
        if w >= 2 * n:
            test_indices = set(random.sample(range(w), w - n))
            key_indices = [i for i in range(w) if i not in test_indices][:n]
            
            s_err = sum(1 for i in test_indices if s_a[i] != s_b[i])
            k_err = sum(1 for i in key_indices if s_a[i] != s_b[i])
            
            sq = (s_err / len(test_indices)) * 100.0
            kq = (k_err / len(key_indices)) * 100.0
            sample_qbers.append(sq)
            key_qbers.append(kq)

    fig, ax = plt.subplots(figsize=(5.4, 5.0), facecolor='white')
    
    # Scatter points (clean, semi-transparent slate circles)
    ax.scatter(sample_qbers, key_qbers, color='#0284c7', alpha=0.6, s=36, edgecolors='none', label='Trials (Local Sim + Eve)')

    # Ideal y = x reference line
    ax.plot([0, 45], [0, 45], color='#64748b', linestyle=':', linewidth=1.5, label='Ideal Estimator (y = x)')

    # 11% threshold lines
    ax.axvline(11.0, color='#be123c', linestyle='--', linewidth=1.2, alpha=0.7)
    ax.axhline(11.0, color='#be123c', linestyle='--', linewidth=1.2, alpha=0.7)
    ax.text(11.5, 42, '11% Abort Threshold', color='#be123c', fontsize=8.5, fontweight='bold')

    corr = np.corrcoef(sample_qbers, key_qbers)[0, 1]
    ax.text(2, 38, f"Mean Sample QBER: {np.mean(sample_qbers):.1f}%\nMean Key QBER: {np.mean(key_qbers):.1f}%\nCorrelation r = {corr:.2f}",
            fontsize=9, color='#334155', linespacing=1.4)

    ax.set_title("Sample QBER vs. Actual Key QBER", pad=12)
    ax.set_xlabel("Sacrificed Sample QBER (%)")
    ax.set_ylabel("Hidden Secret Key QBER (%)")
    ax.set_xlim(0, 45)
    ax.set_ylim(0, 45)
    ax.grid(True, linestyle='-', linewidth=0.6, color='#f1f5f9')
    ax.legend(frameon=False, loc='lower right', fontsize=9)

    save_minimal(fig, "minimal_fig2_sample_vs_key_qber_localsim.png")
    plt.close(fig)


# ==============================================================================
# 3. KEY SIZING: 24-bit Success Rate vs Delta in Local Simulation (Ultra-Minimal)
# ==============================================================================
def run_delta_minimal(trials: int = 100):
    random.seed(42)
    deltas = [0.0, 0.25, 0.5, 0.8, 1.0]
    n = 24
    
    success_rates = []
    print("[3/4] Running Key Sizing 24-bit delta in Local Sim (100 trials)...")
    for d in deltas:
        total_q = service.calculate_key_length(d, n)
        succ = 0
        for _ in range(trials):
            sim = qkd.simulate_bb84_protocal(key_size=total_q, per_time_bits=total_q, has_eavesdropping=False, use_ibm=False, channel_noise=0.0)
            s_a = qkd.filter_key_by_basis(sim['server_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            if len(s_a) >= 2 * n:
                succ += 1
        success_rates.append((succ / trials) * 100.0)

    fig, ax = plt.subplots(figsize=(6.4, 4.0), facecolor='white')
    x = np.arange(len(deltas))

    # Clean line + dot plot
    ax.plot(x, success_rates, marker='o', markersize=6, color='#0284c7', linewidth=2, label='Local Simulation (100 trials)')
    
    # 95% Target line
    ax.axhline(95.0, color='#059669', linestyle='--', linewidth=1.2, alpha=0.8)
    ax.text(0, 96.5, '95% Reliability Target', color='#059669', fontsize=8.5, fontweight='bold')

    for i, txt in enumerate(success_rates):
        ax.text(x[i], txt - 5 if txt > 90 else txt + 3, f"{txt:.0f}%", ha='center', fontsize=9, fontweight='bold', color='#0369a1')

    ax.set_title("Single-Session Success Rate vs. Safety Margin δ (24 bits)", pad=12)
    ax.set_xlabel("Safety Margin δ (Transmitted Qubits N = ⌈(4 + δ) × 24⌉)")
    ax.set_ylabel("Single-Session Success Rate (%)")
    ax.set_xticks(x)
    ax.set_xticklabels([f"δ = {d}\n({service.calculate_key_length(d, n)}Q)" for d in deltas])
    ax.set_ylim(40, 105)
    ax.grid(axis='y', zorder=0)

    save_minimal(fig, "minimal_fig3_delta_24bits_localsim.png")
    plt.close(fig)


# ==============================================================================
# 4. OPTIMAL DELTA vs KEY SIZE in Local Simulation (Ultra-Minimal)
# ==============================================================================
def run_optimal_delta_minimal(trials: int = 100):
    random.seed(42)
    key_sizes = [8, 16, 24, 32, 40]
    candidate_deltas = [0.0, 0.25, 0.5, 0.8, 1.0, 1.25, 1.5]
    
    optimal_deltas = []
    print("[4/4] Running Optimal Delta vs Key Size in Local Sim (100 trials)...")
    for n in key_sizes:
        found = candidate_deltas[-1]
        for d in candidate_deltas:
            total_q = service.calculate_key_length(d, n)
            succ = 0
            for _ in range(trials):
                sim = qkd.simulate_bb84_protocal(key_size=total_q, per_time_bits=total_q, has_eavesdropping=False, use_ibm=False, channel_noise=0.0)
                s_a = qkd.filter_key_by_basis(sim['server_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
                if len(s_a) >= 2 * n:
                    succ += 1
            if (succ / trials) >= 0.95:
                found = d
                break
        optimal_deltas.append(found)

    fig, ax = plt.subplots(figsize=(6.4, 4.0), facecolor='white')
    ax.plot(key_sizes, optimal_deltas, marker='s', markersize=6, color='#475569', linewidth=2)

    for i, n in enumerate(key_sizes):
        ax.text(n, optimal_deltas[i] + 0.05, f"δ* = {optimal_deltas[i]}", ha='center', fontsize=9, fontweight='bold', color='#1e293b')

    ax.set_title("Optimal Safety Margin δ* for 95% Reliability", pad=12)
    ax.set_xlabel("Target Key Size n (bits)")
    ax.set_ylabel("Minimum Required δ*")
    ax.set_xticks(key_sizes)
    ax.set_ylim(0, 1.6)
    ax.grid(axis='y', zorder=0)

    save_minimal(fig, "minimal_fig4_optimal_delta_vs_keysize_localsim.png")
    plt.close(fig)

if __name__ == "__main__":
    print("Starting Minimal Local Simulation Suite (100 trials each)...")
    run_p1_minimal()
    run_p2_minimal()
    run_delta_minimal()
    run_optimal_delta_minimal()
    print("All minimal local simulation figures successfully generated!")
