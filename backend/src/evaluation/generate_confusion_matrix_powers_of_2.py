"""
Evaluate Confusion Matrix Across Key Sizes n in [8, 16, 32, 64, 128, 256]
100 trials No Eve + 100 trials With Eve per key size (1,200 total QKD runs)

Confusion Matrix Schema:
                | Predicted: No Alert (Safe) | Predicted: Alert (Abort)
----------------+----------------------------+-------------------------
Actual: No Eve  | True Negative (TN)         | False Positive (FP)
Actual: Eve     | False Negative (FN)        | True Positive (TP)
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

def evaluate_powers_of_2(trials: int = 500):
    random.seed(42)
    np.random.seed(42)
    key_sizes = [8, 16, 32, 64, 128, 256]
    threshold = 11.0
    
    results = {}

    print(f"Starting Confusion Matrix Evaluation across {key_sizes} ({trials} trials each, total {trials * 2 * len(key_sizes)} runs)...", flush=True)

    for n in key_sizes:
        total_q = service.calculate_key_length(0.8, n)

        # 1. No Eve (trials runs)
        tn, fp = 0, 0
        for _ in range(trials):
            sim = qkd.simulate_bb84_protocal(key_size=total_q, per_time_bits=min(64, total_q), has_eavesdropping=False, use_ibm=False, channel_noise=0.0)
            s_a = qkd.filter_key_by_basis(sim['server_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            s_b = qkd.filter_key_by_basis(sim['client_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            w = len(s_a)
            if w >= 2 * n:
                test_idx = random.sample(range(w), w - n)
                err = sum(1 for idx in test_idx if s_a[idx] != s_b[idx])
                qber = (err / (w - n)) * 100.0
            else:
                qber = 0.0
            
            if qber > threshold:
                fp += 1
            else:
                tn += 1

        # 2. With Eve (trials runs)
        fn, tp = 0, 0
        for _ in range(trials):
            sim = qkd.simulate_bb84_protocal(key_size=total_q, per_time_bits=min(64, total_q), has_eavesdropping=True, use_ibm=False, channel_noise=0.0)
            s_a = qkd.filter_key_by_basis(sim['server_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            s_b = qkd.filter_key_by_basis(sim['client_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            w = len(s_a)
            if w >= 2 * n:
                test_idx = random.sample(range(w), w - n)
                err = sum(1 for idx in test_idx if s_a[idx] != s_b[idx])
                qber = (err / (w - n)) * 100.0
            else:
                qber = 25.0

            if qber > threshold:
                tp += 1
            else:
                fn += 1

        acc = (tp + tn) / (trials * 2) * 100.0
        rec = (tp / (tp + fn)) * 100.0 if (tp + fn) > 0 else 0.0
        prec = (tp / (tp + fp)) * 100.0 if (tp + fp) > 0 else 0.0
        spec = (tn / (tn + fp)) * 100.0 if (tn + fp) > 0 else 0.0

        results[n] = {
            "TN": tn, "FP": fp, "FN": fn, "TP": tp,
            "Accuracy": acc, "Recall": rec, "Precision": prec, "Specificity": spec,
            "qubits": total_q
        }
        print(f"n = {n:3d} bits ({total_q:4d}Q) | TN={tn:3d}, FP={fp:2d}, FN={fn:2d}, TP={tp:3d} | Acc={acc:5.1f}%, Detection Rate={rec:5.1f}%", flush=True)

    # --------------------------------------------------------------------------
    # Figure 1: 2 x 3 Minimal Grid of Confusion Matrices
    # --------------------------------------------------------------------------
    fig, axes = plt.subplots(2, 3, figsize=(13.5, 7.8), facecolor='white')
    axes = axes.flatten()

    cell_colors = [
        ['#eff6ff', '#fff1f2'],  # [TN, FP]
        ['#fff1f2', '#eff6ff']   # [FN, TP]
    ]

    for idx, n in enumerate(key_sizes):
        ax = axes[idx]
        res = results[n]
        matrix = [[res["TN"], res["FP"]], [res["FN"], res["TP"]]]

        for i in range(2):
            for j in range(2):
                val = matrix[i][j]
                pct = (val / trials) * 100.0
                rect = plt.Rectangle((j, 1 - i), 1, 1, facecolor=cell_colors[i][j], edgecolor='#cbd5e1', linewidth=1.2)
                ax.add_patch(rect)

                num_color = '#1e40af' if (i == j) else ('#b91c1c' if val > 0 else '#94a3b8')
                ax.text(j + 0.5, 1 - i + 0.58, f"{val}", ha='center', va='center', fontsize=20, fontweight='bold', color=num_color)
                ax.text(j + 0.5, 1 - i + 0.34, f"({pct:.1f}%)", ha='center', va='center', fontsize=10, color='#64748b')
                
                desc = "No Eve, No Alert" if (i==0 and j==0) else ("No Eve, Alert" if (i==0 and j==1) else ("Eve, No Alert" if (i==1 and j==0) else "Eve, Alert"))
                ax.text(j + 0.5, 1 - i + 0.17, desc, ha='center', va='center', fontsize=8.2, fontweight='bold', color='#475569')

        ax.set_xlim(0, 2)
        ax.set_ylim(0, 2)
        ax.set_xticks([0.5, 1.5])
        ax.set_xticklabels(['No Alert', 'Alert'], fontsize=9.5, fontweight='bold', color='#1e293b')
        ax.xaxis.tick_top()
        ax.set_title(f"n = {n} bits ({res['qubits']} Qubits)\nAccuracy: {res['Accuracy']:.1f}%  |  Detection: {res['Recall']:.1f}%", 
                     pad=10, fontsize=10.5, fontweight='bold', color='#0f172a')

        if idx % 3 == 0:
            ax.set_yticks([0.5, 1.5])
            ax.set_yticklabels(['Eve', 'No Eve'], fontsize=9.5, fontweight='bold', color='#1e293b')
            ax.set_ylabel('Actual Condition', fontsize=9.5, fontweight='bold', color='#0f172a', labelpad=6)
        else:
            ax.set_yticks([])

        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(top=False, bottom=False, left=False, right=False)

    plt.subplots_adjust(wspace=0.28, hspace=0.42)
    save_minimal(fig, "minimal_confusion_matrices_powers_of_2.png")
    plt.close(fig)

    # --------------------------------------------------------------------------
    # Figure 2: Minimal Scaling Curve of Detection Metrics vs Key Size
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(6.8, 4.2), facecolor='white')
    recalls = [results[n]["Recall"] for n in key_sizes]
    accuracies = [results[n]["Accuracy"] for n in key_sizes]
    false_alarms = [results[n]["FP"] / trials * 100.0 for n in key_sizes]
    x_positions = np.arange(len(key_sizes))

    ax.plot(x_positions, recalls, marker='o', markersize=6, color='#2563eb', linewidth=2.0, label='Detection Rate / Recall (Eve Alert)')
    ax.plot(x_positions, accuracies, marker='s', markersize=5, color='#059669', linewidth=1.8, label='Overall Accuracy')
    ax.plot(x_positions, false_alarms, marker='^', markersize=5, color='#94a3b8', linestyle='--', linewidth=1.5, label='False Alarm Rate (No Eve Alert)')

    for i, n in enumerate(key_sizes):
        ax.text(x_positions[i], recalls[i] + 1.5, f"{recalls[i]:.1f}%", ha='center', fontsize=9, fontweight='bold', color='#1e40af')

    ax.set_title("Eavesdropping Detection Convergence (500 Runs / Case)", pad=14, fontsize=12, fontweight='bold', color='#0f172a')
    ax.set_xlabel("Target Key Size n (bits)", fontsize=10.5, color='#334155')
    ax.set_ylabel("Rate (%)", fontsize=10.5, color='#334155')
    ax.set_xticks(x_positions)
    ax.set_xticklabels([f"{n}b\n({results[n]['qubits']}Q)" for n in key_sizes])
    ax.set_ylim(-3, 108)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#94a3b8')
    ax.spines['bottom'].set_color('#94a3b8')
    ax.grid(axis='y', linestyle='-', linewidth=0.7, color='#f1f5f9')
    ax.legend(frameon=False, loc='lower right', fontsize=9)

    save_minimal(fig, "minimal_detection_convergence_powers_of_2.png")
    plt.close(fig)

    return results

if __name__ == "__main__":
    evaluate_powers_of_2(trials=500)
