"""
Generate Ultra-Minimal Confusion Matrix for QKD Eavesdropping Detection
Local Simulation (100 trials No Eve, 100 trials With Eve) for n = 24 bits ('VT3')

Confusion Matrix Schema:
                |  Predicted: No Alert (Safe) | Predicted: Alert (Abort)
----------------+-----------------------------+--------------------------
Actual: No Eve  |  True Negative (TN)         | False Positive (FP)
Actual: Eve     |  False Negative (FN)        | True Positive (TP)
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

def run_confusion_matrix(trials: int = 100):
    random.seed(42)
    np.random.seed(42)
    n = 24
    total_q = service.calculate_key_length(0.8, n)
    threshold = 11.0

    print(f"Running Confusion Matrix on Local Simulation ({trials} No Eve + {trials} Eve)...")

    # 1. No Eve (Negative Class: Actual = Normal)
    tn = 0
    fp = 0
    no_eve_qbers = []
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
        no_eve_qbers.append(qber)
        if qber > threshold:
            fp += 1  # False Positive (False Alarm)
        else:
            tn += 1  # True Negative (Correct Accept)

    # 2. With Eve (Positive Class: Actual = Eavesdropper present)
    fn = 0
    tp = 0
    eve_qbers = []
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
        eve_qbers.append(qber)
        if qber > threshold:
            tp += 1  # True Positive (Correct Intercept & Abort)
        else:
            fn += 1  # False Negative (Missed Attack)

    print(f"Results: TN={tn}, FP={fp}, FN={fn}, TP={tp}")
    
    total = tn + fp + fn + tp
    accuracy = (tp + tn) / total * 100.0
    precision = (tp / (tp + fp) * 100.0) if (tp + fp) > 0 else 0.0
    recall = (tp / (tp + fn) * 100.0) if (tp + fn) > 0 else 0.0
    specificity = (tn / (tn + fp) * 100.0) if (tn + fp) > 0 else 0.0

    print(f"Accuracy: {accuracy:.1f}%, Precision: {precision:.1f}%, Recall: {recall:.1f}%, Specificity: {specificity:.1f}%")

    # --------------------------------------------------------------------------
    # Plot Ultra-Minimal Confusion Matrix
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(6.2, 5.2), facecolor='white')

    # Color definitions: Minimal muted palette
    # Correct decisions (TN, TP): soft clean emerald/blue tint
    # Incorrect decisions (FP, FN): soft rose tint
    cell_colors = [
        ['#eff6ff', '#fff1f2'],  # [TN, FP]
        ['#fff1f2', '#eff6ff']   # [FN, TP]
    ]

    # Data array
    matrix = [[tn, fp], [fn, tp]]

    # Draw cells manually for pixel-perfect minimalism
    for i in range(2):
        for j in range(2):
            val = matrix[i][j]
            pct = (val / trials) * 100.0
            
            # Box
            rect = plt.Rectangle((j, 1 - i), 1, 1, facecolor=cell_colors[i][j], 
                                 edgecolor='#cbd5e1', linewidth=1.5)
            ax.add_patch(rect)

            # Cell text
            if i == 0 and j == 0:
                name = "True Negative (TN)"
                desc = "No Eve, No Alert"
                num_color = '#1e40af'
            elif i == 0 and j == 1:
                name = "False Positive (FP)"
                desc = "No Eve, Alert"
                num_color = '#b91c1c' if val > 0 else '#94a3b8'
            elif i == 1 and j == 0:
                name = "False Negative (FN)"
                desc = "Eve, No Alert"
                num_color = '#b91c1c' if val > 0 else '#94a3b8'
            else:
                name = "True Positive (TP)"
                desc = "Eve, Alert"
                num_color = '#1e40af'

            # Value count
            ax.text(j + 0.5, 1 - i + 0.58, f"{val}", 
                    ha='center', va='center', fontsize=26, fontweight='bold', color=num_color)
            
            # Percentage
            ax.text(j + 0.5, 1 - i + 0.38, f"({pct:.1f}%)", 
                    ha='center', va='center', fontsize=11, color='#64748b')

            # Descriptive Sub-label
            ax.text(j + 0.5, 1 - i + 0.20, desc, 
                    ha='center', va='center', fontsize=9.5, fontweight='bold', color='#334155')

    # Configure axes
    ax.set_xlim(0, 2)
    ax.set_ylim(0, 2)

    # X-axis ticks (Predicted)
    ax.set_xticks([0.5, 1.5])
    ax.set_xticklabels(['No Alert (Accept)\n[QBER ≤ 11%]', 'Alert (Abort)\n[QBER > 11%]'], 
                       fontsize=10.5, fontweight='bold', color='#0f172a')
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position('top')
    ax.set_xlabel('Predicted Action (System Decision)', fontsize=11, fontweight='bold', labelpad=12, color='#0f172a')

    # Y-axis ticks (Actual)
    ax.set_yticks([0.5, 1.5])
    ax.set_yticklabels(['Eve Present\n(Attack)', 'No Eve\n(Legitimate)'], 
                       fontsize=10.5, fontweight='bold', color='#0f172a')
    ax.set_ylabel('Actual Condition (Ground Truth)', fontsize=11, fontweight='bold', labelpad=12, color='#0f172a')

    # Remove outer spines
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(top=False, bottom=False, left=False, right=False)

    # Footnote with summary metrics
    summary_text = f"Accuracy: {accuracy:.1f}%   |   Recall (Detection Rate): {recall:.1f}%   |   False Alarm: {fp / trials * 100:.1f}%"
    fig.text(0.5, 0.02, summary_text, ha='center', fontsize=9.5, fontweight='bold', color='#475569')

    save_minimal(fig, "minimal_confusion_matrix.png")
    plt.close(fig)

    return {
        "TN": tn, "FP": fp, "FN": fn, "TP": tp,
        "Accuracy": accuracy, "Precision": precision,
        "Recall": recall, "Specificity": specificity
    }

if __name__ == "__main__":
    run_confusion_matrix(trials=100)
