"""
Evaluate Confusion Matrix Across Multiple Key Sizes with 500 Runs:
n in [8, 16, 24, 32, 40] bits
500 trials No Eve + 500 trials With Eve per key size (5,000 total QKD runs)

Evaluates:
- True Negative (TN): No Eve, No Alert
- False Positive (FP): No Eve, Alert
- False Negative (FN): Eve, No Alert
- True Positive (TP): Eve, Alert
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

def evaluate_many_keysizes(trials: int = 500):
    random.seed(42)
    np.random.seed(42)
    key_sizes = [8, 16, 24, 32, 40]
    threshold = 11.0
    
    results = {}

    print(f"Starting Confusion Matrix Evaluation across key sizes {key_sizes} ({trials} trials each, total {trials * 2 * len(key_sizes)} runs)...")

    for n in key_sizes:
        total_q = service.calculate_key_length(0.8, n)

        # 1. No Eve (trials runs)
        tn, fp = 0, 0
        for _ in range(trials):
            sim = qkd.simulate_bb84_protocal(key_size=total_q, per_time_bits=total_q, has_eavesdropping=False, use_ibm=False, channel_noise=0.0)
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
            sim = qkd.simulate_bb84_protocal(key_size=total_q, per_time_bits=total_q, has_eavesdropping=True, use_ibm=False, channel_noise=0.0)
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
            "Accuracy": acc, "Recall": rec, "Precision": prec, "Specificity": spec
        }
        print(f"n = {n:2d} bits | TN={tn:3d}, FP={fp:2d}, FN={fn:2d}, TP={tp:3d} | Acc={acc:5.1f}%, Detection Rate={rec:5.1f}%")

    # --------------------------------------------------------------------------
    # Figure 1: Single 24-bit Minimal Confusion Matrix (500 trials)
    # --------------------------------------------------------------------------
    res24 = results[24]
    fig24, ax24 = plt.subplots(figsize=(6.2, 5.2), facecolor='white')
    cell_colors = [
        ['#eff6ff', '#fff1f2'],  # [TN, FP]
        ['#fff1f2', '#eff6ff']   # [FN, TP]
    ]
    matrix24 = [[res24["TN"], res24["FP"]], [res24["FN"], res24["TP"]]]
    for i in range(2):
        for j in range(2):
            val = matrix24[i][j]
            pct = (val / trials) * 100.0
            rect = plt.Rectangle((j, 1 - i), 1, 1, facecolor=cell_colors[i][j], edgecolor='#cbd5e1', linewidth=1.5)
            ax24.add_patch(rect)

            if i == 0 and j == 0:
                desc = "No Eve, No Alert"
                num_color = '#1e40af'
            elif i == 0 and j == 1:
                desc = "No Eve, Alert"
                num_color = '#b91c1c' if val > 0 else '#94a3b8'
            elif i == 1 and j == 0:
                desc = "Eve, No Alert"
                num_color = '#b91c1c' if val > 0 else '#94a3b8'
            else:
                desc = "Eve, Alert"
                num_color = '#1e40af'

            ax24.text(j + 0.5, 1 - i + 0.58, f"{val}", ha='center', va='center', fontsize=26, fontweight='bold', color=num_color)
            ax24.text(j + 0.5, 1 - i + 0.38, f"({pct:.1f}%)", ha='center', va='center', fontsize=11, color='#64748b')
            ax24.text(j + 0.5, 1 - i + 0.20, desc, ha='center', va='center', fontsize=9.5, fontweight='bold', color='#334155')

    ax24.set_xlim(0, 2)
    ax24.set_ylim(0, 2)
    ax24.set_xticks([0.5, 1.5])
    ax24.set_xticklabels(['No Alert (Accept)\n[QBER ≤ 11%]', 'Alert (Abort)\n[QBER > 11%]'], fontsize=10.5, fontweight='bold', color='#0f172a')
    ax24.xaxis.tick_top()
    ax24.xaxis.set_label_position('top')
    ax24.set_xlabel('Predicted Action (System Decision)', fontsize=11, fontweight='bold', labelpad=12, color='#0f172a')
    ax24.set_yticks([0.5, 1.5])
    ax24.set_yticklabels(['Eve Present\n(Attack)', 'No Eve\n(Legitimate)'], fontsize=10.5, fontweight='bold', color='#0f172a')
    ax24.set_ylabel('Actual Condition (Ground Truth)', fontsize=11, fontweight='bold', labelpad=12, color='#0f172a')
    for spine in ax24.spines.values():
        spine.set_visible(False)
    ax24.tick_params(top=False, bottom=False, left=False, right=False)

    summary_text = f"500 Runs per Class (1,000 Total) | Accuracy: {res24['Accuracy']:.1f}% | Recall: {res24['Recall']:.1f}% | False Alarm: {res24['FP']/trials*100:.1f}%"
    fig24.text(0.5, 0.02, summary_text, ha='center', fontsize=9.2, fontweight='bold', color='#475569')

    save_minimal(fig24, "minimal_confusion_matrix.png")
    plt.close(fig24)

    # --------------------------------------------------------------------------
    # Figure 2: Multi-Panel Minimal Confusion Matrices (Side-by-Side)
    # --------------------------------------------------------------------------
    fig, axes = plt.subplots(1, len(key_sizes), figsize=(16.0, 3.8), facecolor='white')

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
                ax.text(j + 0.5, 1 - i + 0.56, f"{val}", ha='center', va='center', fontsize=18, fontweight='bold', color=num_color)
                ax.text(j + 0.5, 1 - i + 0.32, f"({pct:.1f}%)", ha='center', va='center', fontsize=9.5, color='#64748b')

        ax.set_xlim(0, 2)
        ax.set_ylim(0, 2)
        ax.set_xticks([0.5, 1.5])
        ax.set_xticklabels(['No Alert', 'Alert'], fontsize=9, fontweight='bold', color='#1e293b')
        ax.xaxis.tick_top()
        ax.set_title(f"n = {n} bits\n(Accuracy: {res['Accuracy']:.1f}%)", pad=10, fontsize=10.5, fontweight='bold', color='#0f172a')

        if idx == 0:
            ax.set_yticks([0.5, 1.5])
            ax.set_yticklabels(['Eve', 'No Eve'], fontsize=9.5, fontweight='bold', color='#1e293b')
            ax.set_ylabel('Actual Ground Truth', fontsize=10, fontweight='bold', color='#0f172a', labelpad=8)
        else:
            ax.set_yticks([])

        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(top=False, bottom=False, left=False, right=False)

    plt.subplots_adjust(wspace=0.25)
    save_minimal(fig, "minimal_confusion_matrices_by_keysize.png")
    plt.close(fig)

    # --------------------------------------------------------------------------
    # Figure 3: Minimal Scaling Curve of Detection Metrics vs Key Size (500 Runs)
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(6.4, 4.0), facecolor='white')
    recalls = [results[n]["Recall"] for n in key_sizes]
    accuracies = [results[n]["Accuracy"] for n in key_sizes]
    false_alarms = [results[n]["FP"] / trials * 100.0 for n in key_sizes]

    ax.plot(key_sizes, recalls, marker='o', markersize=6, color='#2563eb', linewidth=2.0, label='Detection Rate / Recall (Eve Alert)')
    ax.plot(key_sizes, accuracies, marker='s', markersize=5, color='#059669', linewidth=1.8, label='Overall Accuracy')
    ax.plot(key_sizes, false_alarms, marker='^', markersize=5, color='#94a3b8', linestyle='--', linewidth=1.5, label='False Alarm Rate (No Eve Alert)')

    for i, n in enumerate(key_sizes):
        ax.text(n, recalls[i] + 1.2, f"{recalls[i]:.1f}%", ha='center', fontsize=9, fontweight='bold', color='#1e40af')

    ax.set_title("Eavesdropping Detection vs. Key Size (500 Runs / Case)", pad=12, fontsize=12, fontweight='bold', color='#0f172a')
    ax.set_xlabel("Target Key Size n (bits)", fontsize=10.5, color='#334155')
    ax.set_ylabel("Rate (%)", fontsize=10.5, color='#334155')
    ax.set_xticks(key_sizes)
    ax.set_ylim(-2, 108)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#94a3b8')
    ax.spines['bottom'].set_color('#94a3b8')
    ax.grid(axis='y', linestyle='-', linewidth=0.7, color='#f1f5f9')
    ax.legend(frameon=False, loc='lower right', fontsize=9)

    save_minimal(fig, "minimal_detection_convergence_vs_keysize.png")
    plt.close(fig)

    return results

if __name__ == "__main__":
    evaluate_many_keysizes(trials=500)
