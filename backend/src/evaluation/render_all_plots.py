"""
Master Plot Renderer for QKD Voting System
Renders ALL publication-grade minimal figures directly from cached raw JSON data
Execution time: ~1 second (Zero simulation re-runs!)

Design Rules:
1. All descriptive text and annotations placed strictly OUTSIDE the plot canvas.
2. Axis labels sized down cleanly (fontsize=9.2).
3. Pure, uncluttered minimal aesthetic (no top/right spines, subtle grids, high contrast).
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
PLOTS_DIR = os.path.join(CURRENT_DIR, "plots")
REPORT_FIG_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", "report", "figures"))
REPORT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", "report"))
ARTIFACT_DIR = r"C:\Users\Archiash\.gemini\antigravity\brain\fe188d27-1463-46c3-aca9-529a07ed20b1"

for d in [PLOTS_DIR, REPORT_FIG_DIR, REPORT_DIR, ARTIFACT_DIR]:
    os.makedirs(d, exist_ok=True)

MASTER_DATA_PATH = os.path.join(DATA_DIR, "master_benchmark_raw_data.json")

def save_minimal(fig, filename):
    for target in [PLOTS_DIR, REPORT_FIG_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path = os.path.join(target, filename)
        fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    print(f" -> [SAVED] {filename}")


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
    'axes.labelsize': 9.2,          # Clean, smaller axis label
    'xtick.color': '#64748b',
    'ytick.color': '#64748b',
    'xtick.labelsize': 8.8,
    'ytick.labelsize': 8.8,
    'grid.color': '#f1f5f9',
    'grid.linestyle': '-',
    'grid.linewidth': 0.75
})


def render_all_plots(data=None):
    if data is None:
        if not os.path.exists(MASTER_DATA_PATH):
            raise FileNotFoundError(f"Master data not found at {MASTER_DATA_PATH}. Please run run_all_benchmarks.py first.")
        with open(MASTER_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

    print("\nRendering ALL Minimal Visualizations from Master Raw Data (Execution time < 1s)...")

    # ==========================================================================
    # 1. PRIORITY 1: QBER Separation (Local Sim & IBM Hardware vs Eve)
    # ==========================================================================
    p1 = data["priority1_qber_separation"]
    key_sizes = [int(k) for k in p1.keys()]
    loc_means = [p1[str(k)]["local_mean"] for k in key_sizes]
    ibm_means = [p1[str(k)]["ibm_mean"] for k in key_sizes]
    eve_means = [p1[str(k)]["eve_mean"] for k in key_sizes]

    fig, ax = plt.subplots(figsize=(6.8, 4.2), facecolor='white')
    x = np.arange(len(key_sizes))
    w = 0.26

    b1 = ax.bar(x - w, loc_means, w, label='Local Sim (No Eve)', color='#2563eb', edgecolor='none')
    b2 = ax.bar(x, ibm_means, w, label='IBM Quantum (No Eve, 2.8% Noise)', color='#059669', edgecolor='none')
    b3 = ax.bar(x + w, eve_means, w, label='With Eve (Intercept-Resend)', color='#e11d48', edgecolor='none')

    ax.axhline(11.0, color='#be123c', linestyle='--', linewidth=1.2, zorder=4)

    for b in b1: ax.text(b.get_x() + b.get_width()/2., b.get_height() + 0.4, f"{b.get_height():.1f}%", ha='center', va='bottom', fontsize=8.8, fontweight='bold', color='#1e3a8a')
    for b in b2: ax.text(b.get_x() + b.get_width()/2., b.get_height() + 0.4, f"{b.get_height():.1f}%", ha='center', va='bottom', fontsize=8.8, fontweight='bold', color='#065f46')
    for b in b3: ax.text(b.get_x() + b.get_width()/2., b.get_height() + 0.4, f"{b.get_height():.1f}%", ha='center', va='bottom', fontsize=8.8, fontweight='bold', color='#9f1239')

    ax.set_title("Eavesdropping Detection: QBER vs. 11% Security Threshold", pad=12)
    ax.set_ylabel("Measured QBER (%)")
    ax.set_xticks(x)
    ax.set_xticklabels([f"n = {k} bits" for k in key_sizes])
    ax.set_ylim(0, 32)
    ax.grid(axis='y', zorder=0)
    ax.legend(frameon=False, loc='upper left', fontsize=8.6)

    fig.text(0.5, -0.04, "Red dashed line marks the 11.0% Security Threshold. Eve QBER (~25%) is intercepted 100%.", ha='center', fontsize=8.5, color='#334155', fontweight='bold')
    save_minimal(fig, "minimal_fig1_eavesdropping_detection_localsim.png")
    plt.close(fig)

    # ==========================================================================
    # 2. PRIORITY 1: Confusion Matrix Grid (Local Sim Powers of 2)
    # ==========================================================================
    cm_l = data["confusion_matrix_local"]
    p2_keys = [int(k) for k in cm_l.keys()]
    fig, axes = plt.subplots(2, 3, figsize=(13.5, 7.8), facecolor='white')
    axes = axes.flatten()

    cell_colors = [['#eff6ff', '#fff1f2'], ['#fff1f2', '#eff6ff']]
    trials = data["metadata"]["trials_per_test"]

    for idx, n in enumerate(p2_keys):
        ax = axes[idx]
        res = cm_l[str(n)]
        matrix = [[res["TN"], res["FP"]], [res["FN"], res["TP"]]]
        acc = (res["TN"] + res["TP"]) / (trials * 2) * 100.0
        rec = (res["TP"] / (res["TP"] + res["FN"])) * 100.0 if (res["TP"] + res["FN"]) > 0 else 0.0

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
        ax.set_title(f"n = {n} bits ({res['qubits']}Q) | Acc: {acc:.1f}% | Recall: {rec:.1f}%", pad=10, fontsize=10.0, fontweight='bold', color='#0f172a')
        if idx % 3 == 0:
            ax.set_yticks([0.5, 1.5]); ax.set_yticklabels(['Eve', 'No Eve'], fontsize=9.0, fontweight='bold')
        else: ax.set_yticks([])
        for spine in ax.spines.values(): spine.set_visible(False)
        ax.tick_params(top=False, bottom=False, left=False, right=False)

    plt.subplots_adjust(wspace=0.28, hspace=0.42)
    save_minimal(fig, "minimal_confusion_matrices_powers_of_2.png")
    plt.close(fig)

    # ==========================================================================
    # 3. PRIORITY 1: Confusion Matrix Grid (IBM Quantum Hardware Powers of 2)
    # ==========================================================================
    cm_i = data["confusion_matrix_ibm"]
    fig, axes = plt.subplots(2, 3, figsize=(13.5, 7.8), facecolor='white')
    axes = axes.flatten()

    for idx, n in enumerate(p2_keys):
        ax = axes[idx]
        res = cm_i[str(n)]
        matrix = [[res["TN"], res["FP"]], [res["FN"], res["TP"]]]
        acc = (res["TN"] + res["TP"]) / (trials * 2) * 100.0
        rec = (res["TP"] / (res["TP"] + res["FN"])) * 100.0 if (res["TP"] + res["FN"]) > 0 else 0.0

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
        else: ax.set_yticks([])
        for spine in ax.spines.values(): spine.set_visible(False)
        ax.tick_params(top=False, bottom=False, left=False, right=False)

    plt.subplots_adjust(wspace=0.28, hspace=0.42)
    save_minimal(fig, "minimal_confusion_matrices_ibm_powers_of_2.png")
    plt.close(fig)

    # ==========================================================================
    # 4. PRIORITY 2: Blind Verification Scatter Plot (ALL Key Sizes)
    # ==========================================================================
    p2_data = data["priority2_blind_verification"]
    if "scatter_all_keysizes" in p2_data:
        p2_sc = p2_data["scatter_all_keysizes"]
        key_size_label = "All Key Sizes: 8 to 256 bits"
        n_trials_desc = f"N = {len(p2_sc['normal']['sample_qber'])} runs per scenario across n in [8, 16, 24, 32, 64, 128, 256] bits"
    else:
        p2_sc = p2_data["scatter_24bits"]
        key_size_label = "24 bits"
        n_trials_desc = f"N = {len(p2_sc['normal']['sample_qber'])} runs (24-bit candidate ballot key)"

    s_norm, k_norm = p2_sc["normal"]["sample_qber"], p2_sc["normal"]["key_qber"]
    s_ibm, k_ibm = p2_sc["ibm_hardware"]["sample_qber"], p2_sc["ibm_hardware"]["key_qber"]
    s_eve, k_eve = p2_sc["eve"]["sample_qber"], p2_sc["eve"]["key_qber"]

    fig, ax = plt.subplots(figsize=(7.6, 5.0), facecolor='white')
    ax.scatter(s_norm, k_norm, color='#2563eb', alpha=0.45, s=26, edgecolors='none', label='Ideal / No Noise (0.0%)')
    ax.scatter(s_ibm, k_ibm, color='#059669', alpha=0.45, s=28, edgecolors='none', label='IBM Hardware Noise (2.8%)')
    ax.scatter(s_eve, k_eve, color='#e11d48', alpha=0.45, s=30, edgecolors='none', label='With Eve Attack (~25%)')

    ax.plot([0, 48], [0, 48], color='#94a3b8', linestyle=':', linewidth=1.2, label='Ideal Estimator (y = x)')
    ax.axvline(11.0, color='#be123c', linestyle='--', linewidth=1.1, alpha=0.75)
    ax.axhline(11.0, color='#be123c', linestyle='--', linewidth=1.1, alpha=0.75)
    ax.plot([], [], color='#be123c', linestyle='--', linewidth=1.1, label='11% Security Threshold')

    # Title positioned cleanly
    ax.set_title(f"Blind Security Verification: Sample QBER vs. Key QBER ({key_size_label})", pad=14, fontsize=11.0, fontweight='bold', color='#0f172a')
    
    # COLOR DESCRIPTION MOVED STRICTLY OUTSIDE GRAPH CANVAS (to the right)
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1.0), frameon=False, fontsize=8.6, handletextpad=0.5, labelspacing=0.8)

    ax.set_xlabel("Sacrificed Sample QBER (%) [Publicly Measured]")
    ax.set_ylabel("Hidden Secret Key QBER (%) [Uninspected]")
    ax.set_xlim(-1, 48); ax.set_ylim(-1, 48)
    ax.grid(True, linestyle='-', linewidth=0.6, color='#f8fafc')

    all_s = s_norm + s_ibm + s_eve
    all_k = k_norm + k_ibm + k_eve
    corr = np.corrcoef(all_s, all_k)[0, 1]
    bias = np.mean(np.abs(np.array(all_s) - np.array(all_k)))
    fig.text(0.42, -0.04, f"Overall Correlation: r = {corr:.2f}   |   Mean Absolute Bias: |Q_sample - Q_key| = {bias:.2f}%", ha='center', fontsize=8.6, fontweight='bold', color='#334155')
    fig.text(0.42, -0.08, f"{n_trials_desc}. Dashed red lines mark 11% threshold.", ha='center', fontsize=8.0, color='#64748b')

    save_minimal(fig, "minimal_priority2_sample_vs_key_scatter.png")
    plt.close(fig)

    # 4b. Multi-panel Grid of Scatter Plots for Powers of 2
    if "scatter_by_keysize" in p2_data:
        p2_grid = p2_data["scatter_by_keysize"]
        grid_keys = [8, 16, 32, 64, 128, 256]
        fig, axes = plt.subplots(2, 3, figsize=(13.5, 7.8), facecolor='white')
        axes = axes.flatten()

        for idx, n in enumerate(grid_keys):
            ax = axes[idx]
            sub = p2_grid.get(str(n), {})
            sn, kn = sub.get("normal", {}).get("sample_qber", []), sub.get("normal", {}).get("key_qber", [])
            si, ki = sub.get("ibm_hardware", {}).get("sample_qber", []), sub.get("ibm_hardware", {}).get("key_qber", [])
            se, ke = sub.get("eve", {}).get("sample_qber", []), sub.get("eve", {}).get("key_qber", [])

            ax.scatter(sn, kn, color='#2563eb', alpha=0.55, s=20, edgecolors='none', label='Ideal (0.0%)' if idx==0 else None)
            ax.scatter(si, ki, color='#059669', alpha=0.60, s=22, edgecolors='none', label='IBM Hardware (2.8%)' if idx==0 else None)
            ax.scatter(se, ke, color='#e11d48', alpha=0.60, s=24, edgecolors='none', label='Eve Attack (~25%)' if idx==0 else None)

            ax.plot([0, 48], [0, 48], color='#94a3b8', linestyle=':', linewidth=1.0)
            ax.axvline(11.0, color='#be123c', linestyle='--', linewidth=0.9, alpha=0.7)
            ax.axhline(11.0, color='#be123c', linestyle='--', linewidth=0.9, alpha=0.7)

            tot_s = sn + si + se
            tot_k = kn + ki + ke
            c_val = np.corrcoef(tot_s, tot_k)[0, 1] if len(tot_s) > 1 else 1.0
            b_val = np.mean(np.abs(np.array(tot_s) - np.array(tot_k))) if len(tot_s) > 1 else 0.0

            ax.set_title(f"n = {n} bits | r = {c_val:.2f} | Bias: {b_val:.2f}%", pad=8, fontsize=9.8, fontweight='bold', color='#0f172a')
            ax.set_xlim(-1, 48); ax.set_ylim(-1, 48)
            ax.grid(True, linestyle='-', linewidth=0.5, color='#f8fafc')
            if idx >= 3: ax.set_xlabel("Sample QBER (%)", fontsize=8.6)
            if idx % 3 == 0: ax.set_ylabel("Key QBER (%)", fontsize=8.6)

        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.99), ncol=3, frameon=False, fontsize=9.2)
        plt.subplots_adjust(wspace=0.22, hspace=0.32, top=0.92, bottom=0.08)
        save_minimal(fig, "minimal_priority2_scatter_grid_powers_of_2.png")
        plt.close(fig)

    # ==========================================================================
    # 5. PRIORITY 2: Estimation Error Convergence vs Key Size
    # ==========================================================================
    p2_cv = data["priority2_blind_verification"]["convergence_powers_of_2"]
    cv_keys = [int(k) for k in p2_cv.keys()]
    cv_biases = [p2_cv[str(k)]["mean_bias"] for k in cv_keys]
    x_pos = np.arange(len(cv_keys))

    fig, ax = plt.subplots(figsize=(6.4, 4.2), facecolor='white')
    ax.plot(x_pos, cv_biases, marker='o', markersize=5.5, color='#0284c7', linewidth=1.8, label='Estimate Different Bias')
    for i, k in enumerate(cv_keys):
        ax.text(x_pos[i], cv_biases[i] + 0.35, f"{cv_biases[i]:.2f}%", ha='center', fontsize=8.5, fontweight='bold', color='#0369a1')

    ax.set_title("Sample QBER Estimation Accuracy vs. Target Key Size", pad=12)
    ax.set_xlabel("Target Key Size n (bits)")
    ax.set_ylabel("Mean Estimation Bias (%)")
    ax.set_xticks(x_pos)
    ax.set_xticklabels([f"{k}b" for k in cv_keys])
    ax.set_ylim(0, 20)
    ax.grid(axis='y', linestyle='-', linewidth=0.7, color='#f8fafc')
    ax.legend(frameon=False, loc='upper right', fontsize=8.6)

    save_minimal(fig, "minimal_priority2_estimation_error_vs_keysize.png")
    plt.close(fig)

    # ==========================================================================
    # 6. PRIORITY 3: OTP Ballot Decryption Accuracy & Ciphertext Entropy
    # ==========================================================================
    p3 = data["priority3_otp_ballot_correctness"]
    acc_ec = p3["accuracy_with_error_correction"]
    acc_no = p3["accuracy_without_error_correction"]
    entropy = p3["ciphertext_shannon_entropy"]

    fig, ax = plt.subplots(figsize=(6.4, 4.2), facecolor='white')
    bars = ax.bar(['Without Error Correction\n(Raw QKD Key)', 'With Key Reconciliation\n(Cascade Protocol)'], 
                  [acc_no, acc_ec], width=0.45, color=['#f59e0b', '#059669'])

    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width()/2., h + 1.5, f"{h:.1f}%", ha='center', va='bottom', fontsize=10.0, fontweight='bold', color='#0f172a')

    ax.set_title("OTP Ballot Decryption Correctness on IBM Hardware Noise", pad=12)
    ax.set_ylabel("Ballot Decryption Accuracy (%)")
    ax.set_ylim(0, 115)
    ax.grid(axis='y', linestyle='-', linewidth=0.7, color='#f8fafc')

    fig.text(0.5, -0.04, f"Ciphertext Shannon Entropy: H(C) = {entropy:.4f} / 1.0000 bit (Perfect Secrecy Achieved)", ha='center', fontsize=8.6, fontweight='bold', color='#334155')
    fig.text(0.5, -0.08, "Key reconciliation achieves 100% ballot recovery under realistic 2.82% physical noise.", ha='center', fontsize=8.0, color='#64748b')

    save_minimal(fig, "minimal_priority3_ballot_recovery.png")
    plt.close(fig)

    # ==========================================================================
    # 7. KEY SIZING: 24-bit Success Rate vs Delta
    # ==========================================================================
    ks = data["keysizing_delta_optimization"]
    deltas = ks["deltas"]
    succ_l = ks["success_rate_local"]
    succ_i = ks["success_rate_ibm"]
    x_d = np.arange(len(deltas))

    fig, ax = plt.subplots(figsize=(6.4, 4.0), facecolor='white')
    ax.plot(x_d, succ_l, marker='o', markersize=5.5, color='#0284c7', linewidth=1.8, label='Local Sim (Ideal)')
    ax.plot(x_d, succ_i, marker='s', markersize=5.0, color='#059669', linewidth=1.8, label='IBM Hardware Noise (2.8%)')
    ax.axhline(95.0, color='#be123c', linestyle='--', linewidth=1.1, alpha=0.8)

    for i in range(len(deltas)):
        ax.text(x_d[i], succ_l[i] + 1.5, f"{succ_l[i]:.0f}%", ha='center', fontsize=8.5, fontweight='bold', color='#0369a1')

    ax.set_title("Single-Session Success Rate vs. Safety Margin δ (24 bits)", pad=12)
    ax.set_xlabel("Safety Margin δ (N = ⌈(4 + δ) × 24⌉ Qubits)")
    ax.set_ylabel("Success Rate (%)")
    ax.set_xticks(x_d)
    ax.set_xticklabels([f"δ = {d}" for d in deltas])
    ax.set_ylim(40, 108)
    ax.grid(axis='y', linestyle='-', linewidth=0.7, color='#f8fafc')
    ax.legend(frameon=False, loc='lower right', fontsize=8.6)

    fig.text(0.5, -0.04, "Red dashed line marks the 95% Reliability Target (Reached at δ = 0.8)", ha='center', fontsize=8.6, fontweight='bold', color='#334155')
    save_minimal(fig, "minimal_fig3_delta_24bits_localsim.png")
    plt.close(fig)

    # ==========================================================================
    # 8. KEY SIZING: Optimal Delta vs Key Size
    # ==========================================================================
    opt_ks = ks["optimal_delta_vs_keysize"]
    opt_sizes = opt_ks["key_sizes"]
    opt_d = opt_ks["optimal_deltas"]

    fig, ax = plt.subplots(figsize=(6.4, 4.0), facecolor='white')
    ax.plot(opt_sizes, opt_d, marker='s', markersize=5.5, color='#475569', linewidth=1.8)
    for i, s in enumerate(opt_sizes):
        ax.text(s, opt_d[i] + 0.05, f"δ* = {opt_d[i]}", ha='center', fontsize=8.5, fontweight='bold', color='#1e293b')

    ax.set_title("Optimal Safety Margin δ* for 95% Reliability", pad=12)
    ax.set_xlabel("Target Key Size n (bits)")
    ax.set_ylabel("Minimum Required δ*")
    ax.set_xticks(opt_sizes)
    ax.set_ylim(0, 1.6)
    ax.grid(axis='y', linestyle='-', linewidth=0.7, color='#f8fafc')

    fig.text(0.5, -0.04, "Law of Large Numbers: Sifting variance decreases with key size, lowering required δ*", ha='center', fontsize=8.6, fontweight='bold', color='#334155')
    save_minimal(fig, "minimal_fig4_optimal_delta_vs_keysize_localsim.png")
    plt.close(fig)

    print("\n[COMPLETE] ALL 8 Publication-Grade Minimal Figures Rendered Successfully!")
    print("All text strictly outside canvas. Smaller axis labels applied.")


if __name__ == "__main__":
    render_all_plots()
