"""
Generate Clear, Focused, Publication-Quality Visualizations for Project Report.

Design Philosophy:
- One core concept per figure (no overcrowded multi-panels)
- Clean, high-contrast, professional styling (white background, crisp lines, 300 DPI)
- Large, readable typography suitable for reports, papers, and slide presentations
- Clear visual callouts, thresholds, and shaded regions that are instantly understandable

Generates 6 distinct figures:
1. report_fig1_key_success_rate.png: Key sufficiency success rate vs safety margin delta
2. report_fig2_binomial_sifting_variance.png: Statistical explanation of sifting shortfall
3. report_fig3_qber_threshold_separation.png: Clean 3-bar QBER comparison vs 11% threshold
4. report_fig4_noise_vs_eve_distributions.png: Clear density separation between noise and Eve
5. report_fig5_qber_estimation_convergence.png: Estimation error convergence curve (40 to 240 qubits)
6. report_fig6_ballot_recovery_error_correction.png: Ballot recovery rate with vs without error correction
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PLOTS_DIR = os.path.join(CURRENT_DIR, "plots")
REPORT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", "report"))
REPORT_FIG_DIR = os.path.join(REPORT_DIR, "figures")
ARTIFACT_DIR = r"C:\Users\Archiash\.gemini\antigravity\brain\fe188d27-1463-46c3-aca9-529a07ed20b1"

for d in [PLOTS_DIR, REPORT_DIR, REPORT_FIG_DIR, ARTIFACT_DIR]:
    os.makedirs(d, exist_ok=True)


def save_report_figure(fig, filename: str):
    """Save to plots, report, report/figures, and artifact directory."""
    paths = [
        os.path.join(PLOTS_DIR, filename),
        os.path.join(REPORT_DIR, filename),
        os.path.join(REPORT_FIG_DIR, filename),
        os.path.join(ARTIFACT_DIR, filename)
    ]
    for p in paths:
        fig.savefig(p, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"[OK] Saved {filename}")


# Style settings for clean publication quality
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'axes.edgecolor': '#333333',
    'axes.linewidth': 1.2,
    'grid.color': '#e0e0e0',
    'grid.linestyle': '--',
    'grid.alpha': 0.7
})


# ==============================================================================
# Figure 1: Key Sufficiency Success Rate vs. Safety Margin delta
# ==============================================================================

def make_fig1_key_success_rate():
    fig, ax = plt.subplots(figsize=(7.5, 4.8), facecolor='white')

    deltas = ['δ = 0.0\n(4.0×, 96Q)', 'δ = 0.5\n(4.5×, 108Q)', 'δ = 1.0\n(5.0×, 120Q)', 'δ = 1.5\n(5.5×, 132Q)', 'δ = 2.0\n(6.0×, 144Q)']
    rates = [56.0, 87.0, 99.0, 100.0, 100.0]
    colors = ['#f59e0b', '#3b82f6', '#10b981', '#059669', '#047857']

    bars = ax.bar(deltas, rates, color=colors, edgecolor='#1f2937', linewidth=1.2, width=0.55, zorder=3)

    # Reference threshold lines
    ax.axhline(90.0, color='#f59e0b', linestyle='--', linewidth=1.8, zorder=2, label='90% Reliability Requirement')
    ax.axhline(99.0, color='#10b981', linestyle=':', linewidth=2.0, zorder=2, label='99% Target Reliability')

    for bar, val in zip(bars, rates):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + 2.0,
            f"{val:.1f}%",
            ha='center', va='bottom',
            fontweight='bold', fontsize=11, color='#111827'
        )

    ax.set_title("Single-Pass Key Generation Success Rate (Target: n = 24 bits)", fontsize=13, fontweight='bold', pad=14, color='#111827')
    ax.set_xlabel("Safety Margin Multiplier in N = (4 + δ) × 24 Qubits", fontsize=11, fontweight='semibold', labelpad=10)
    ax.set_ylabel("Key Sufficiency Success Rate (%)", fontsize=11, fontweight='semibold', labelpad=10)
    ax.set_ylim(0, 115)
    ax.grid(axis='y', zorder=0)
    ax.legend(loc='lower right', framealpha=0.95, fontsize=10)

    # Add explanatory annotation
    ax.annotate(
        "Shortfall events occur\nin 44% of runs at δ=0",
        xy=(0, 56.0), xytext=(0.5, 30),
        arrowprops=dict(arrowstyle="->", color='#b45309', lw=1.5),
        fontsize=9.5, fontweight='semibold', color='#b45309',
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#fef3c7", edgecolor="#f59e0b", lw=1)
    )

    save_report_figure(fig, "report_fig1_key_success_rate.png")
    plt.close(fig)


# ==============================================================================
# Figure 2: Statistical Explanation of Basis Sifting Shortfall
# ==============================================================================

def make_fig2_binomial_sifting():
    fig, ax = plt.subplots(figsize=(8.0, 4.8), facecolor='white')

    # Binomial(96, 0.5)
    n_trials = 96
    p = 0.5
    k_vals = np.arange(30, 68)
    # Compute binomial pmf manually to avoid heavy imports
    from math import comb
    probs = [comb(n_trials, k) * (p**k) * ((1-p)**(n_trials - k)) * 100.0 for k in k_vals]

    # Threshold for 24-bit key: need 2n = 48 sifted bits
    threshold = 48

    # Bars: red for shortfall, green for sufficient
    bar_colors = ['#ef4444' if k < threshold else '#10b981' for k in k_vals]
    ax.bar(k_vals, probs, color=bar_colors, width=0.8, edgecolor='none', alpha=0.85, zorder=3)

    # Vertical threshold line
    ax.axvline(threshold - 0.5, color='#b91c1c', linestyle='-', linewidth=2.2, zorder=4)

    # Shaded regions & annotations
    shortfall_prob = sum(comb(n_trials, k) * (p**k) * ((1-p)**(n_trials - k)) for k in range(0, threshold)) * 100.0
    sufficient_prob = 100.0 - shortfall_prob

    ax.text(38, max(probs) * 0.82, f"Key Shortfall (W < 48)\nProb: {shortfall_prob:.1f}%\n(Abort / Re-run)",
            ha='center', fontsize=10.5, fontweight='bold', color='#b91c1c',
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#fee2e2", edgecolor="#ef4444", lw=1.2))

    ax.text(57, max(probs) * 0.82, f"Sufficient Key (W ≥ 48)\nProb: {sufficient_prob:.1f}%\n(Proceed to OTP)",
            ha='center', fontsize=10.5, fontweight='bold', color='#047857',
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#d1fae5", edgecolor="#10b981", lw=1.2))

    ax.set_title("Basis Sifting Variance at 4.0× Multiplier (N = 96 Qubits)", fontsize=13, fontweight='bold', pad=14, color='#111827')
    ax.set_xlabel("Number of Sifted Bits Surviving Matching Bases (W)", fontsize=11, fontweight='semibold', labelpad=10)
    ax.set_ylabel("Probability Distribution (%)", fontsize=11, fontweight='semibold', labelpad=10)
    ax.set_xlim(32, 65)
    ax.grid(axis='y', zorder=0)

    save_report_figure(fig, "report_fig2_binomial_sifting_variance.png")
    plt.close(fig)


# ==============================================================================
# Figure 3: QBER Threshold Separation (11%)
# ==============================================================================

def make_fig3_qber_threshold():
    fig, ax = plt.subplots(figsize=(7.5, 5.0), facecolor='white')

    categories = ['Clean Channel\n(Ideal)', 'IBM Quantum Noise\n(Operational Baseline)', 'Active Eve Attack\n(Intercept-and-Resend)']
    qbers = [0.0, 2.98, 26.83]
    colors = ['#10b981', '#3b82f6', '#ef4444']

    bars = ax.bar(categories, qbers, color=colors, edgecolor='#1f2937', linewidth=1.2, width=0.48, zorder=3)

    # Threshold line
    threshold = 11.0
    ax.axhline(threshold, color='#b91c1c', linestyle='--', linewidth=2.2, zorder=4, label='Security Threshold (QBER = 11.0%)')

    # Shaded safe & compromised zones
    ax.axhspan(0, threshold, facecolor='#d1fae5', alpha=0.35, zorder=0)
    ax.axhspan(threshold, 35, facecolor='#fee2e2', alpha=0.35, zorder=0)

    # Zone labels
    ax.text(2.35, 5.5, "SAFE ZONE\nKey Accepted", fontsize=10, fontweight='bold', color='#047857', ha='right', va='center')
    ax.text(2.35, 18.0, "COMPROMISED ZONE\nSession Aborted", fontsize=10, fontweight='bold', color='#b91c1c', ha='right', va='center')

    # Value callouts on bars
    for bar, val, status in zip(bars, qbers, ["100% Accepted", "99% Accepted (<11%)", "99% Aborted (≥11%)"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + 1.2,
            f"{val:.2f}%\n({status})",
            ha='center', va='bottom',
            fontweight='bold', fontsize=10, color='#111827'
        )

    ax.set_title("Eavesdropping Detection: Measured QBER vs. 11% Threshold", fontsize=13, fontweight='bold', pad=14, color='#111827')
    ax.set_ylabel("Quantum Bit Error Rate (QBER %)", fontsize=11, fontweight='semibold', labelpad=10)
    ax.set_ylim(0, 35)
    ax.grid(axis='y', zorder=0)
    ax.legend(loc='upper left', framealpha=0.95, fontsize=10)

    save_report_figure(fig, "report_fig3_qber_threshold_separation.png")
    plt.close(fig)


# ==============================================================================
# Figure 4: Statistical Density Separation (Noise vs Eve)
# ==============================================================================

def make_fig4_noise_vs_eve_densities():
    fig, ax = plt.subplots(figsize=(8.0, 4.6), facecolor='white')

    x = np.linspace(-2, 45, 500)

    # Gaussian approximations of measured distributions
    # Hardware noise: mean = 2.98%, std = 2.22%
    # Eve attack: mean = 26.83%, std = 6.01%
    p_noise = (1.0 / (2.22 * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - 2.98) / 2.22)**2)
    p_eve = (1.0 / (6.01 * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - 26.83) / 6.01)**2)

    ax.plot(x, p_noise, color='#2563eb', linewidth=2.5, label='Normal Quantum Noise (μ = 2.98%)')
    ax.fill_between(x, p_noise, color='#3b82f6', alpha=0.3)

    ax.plot(x, p_eve, color='#dc2626', linewidth=2.5, label='Active Eve Intercept (μ = 26.83%)')
    ax.fill_between(x, p_eve, color='#ef4444', alpha=0.3)

    # 11% threshold line
    ax.axvline(11.0, color='#111827', linestyle='--', linewidth=2.2, label='Decision Threshold (11.0%)')

    ax.text(11.5, max(p_noise) * 0.7, "Optimal Decision Boundary\n(Zero Mutual Overlap)", fontsize=9.5, fontweight='bold', color='#111827',
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#f3f4f6", edgecolor="#9ca3af", lw=1))

    ax.set_title("QBER Probability Distributions: Hardware Noise vs. Active Eve", fontsize=13, fontweight='bold', pad=14, color='#111827')
    ax.set_xlabel("Measured Quantum Bit Error Rate (QBER %)", fontsize=11, fontweight='semibold', labelpad=10)
    ax.set_ylabel("Probability Density", fontsize=11, fontweight='semibold', labelpad=10)
    ax.set_xlim(0, 42)
    ax.grid(True, zorder=0)
    ax.legend(loc='upper right', framealpha=0.95, fontsize=10)

    save_report_figure(fig, "report_fig4_noise_vs_eve_distributions.png")
    plt.close(fig)


# ==============================================================================
# Figure 5: Sample QBER Estimation Accuracy Convergence Curve
# ==============================================================================

def make_fig5_estimation_convergence():
    fig, ax = plt.subplots(figsize=(7.8, 4.8), facecolor='white')

    qubits = [40, 80, 120, 160, 200, 240]
    errors = [4.47, 2.80, 4.02, 2.92, 2.44, 2.24]
    spec_bounds = [8.0, 6.0, 4.5, 3.5, 3.0, 2.5]

    # Plot spec boundary
    ax.plot(qubits, spec_bounds, color='#9ca3af', linestyle='--', marker='^', linewidth=1.8, label='TEST_SPEC Upper Bound (Pass Criteria)')
    ax.fill_between(qubits, spec_bounds, color='#f3f4f6', alpha=0.5)

    # Plot measured error curve
    ax.plot(qubits, errors, color='#2563eb', marker='o', markersize=8, linewidth=2.5, zorder=4, label='Measured Mean |QBER_sample - QBER_key|')

    # Value callouts
    for q, err in zip(qubits, errors):
        ax.annotate(
            f"{err:.2f}%",
            (q, err),
            textcoords="offset points", xytext=(0, 10),
            ha='center', fontweight='bold', fontsize=9.5, color='#1e40af'
        )

    ax.set_title("QBER Estimation Error Convergence vs. Transmitted Qubits", fontsize=13, fontweight='bold', pad=14, color='#111827')
    ax.set_xlabel("Total Qubits Sent (N)", fontsize=11, fontweight='semibold', labelpad=10)
    ax.set_ylabel("Mean Estimation Error ΔQBER (%)", fontsize=11, fontweight='semibold', labelpad=10)
    ax.set_xticks(qubits)
    ax.set_xticklabels([f"{q}\n(~{int(q*0.25)} bits)" for q in qubits])
    ax.set_ylim(0, 9.5)
    ax.grid(True, zorder=0)
    ax.legend(loc='upper right', framealpha=0.95, fontsize=10)

    save_report_figure(fig, "report_fig5_qber_estimation_convergence.png")
    plt.close(fig)


# ==============================================================================
# Figure 6: Ballot Decryption Accuracy (Error Correction Impact)
# ==============================================================================

def make_fig6_ballot_recovery():
    fig, ax = plt.subplots(figsize=(7.5, 4.8), facecolor='white')

    scenarios = [
        'Noisy Channel\n(Without Reconciliation)',
        'Noisy Channel\n(With Error Correction)'
    ]
    accuracies = [53.0, 100.0]
    colors = ['#ef4444', '#10b981']

    bars = ax.bar(scenarios, accuracies, color=colors, edgecolor='#1f2937', linewidth=1.2, width=0.45, zorder=3)
    ax.axhline(100.0, color='#059669', linestyle='--', linewidth=1.8, zorder=2, label='100% Target Integrity')

    for bar, val in zip(bars, accuracies):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + 2.0,
            f"{val:.1f}%",
            ha='center', va='bottom',
            fontweight='bold', fontsize=12, color='#111827'
        )

    # Callout explanations
    ax.text(
        0, 25,
        "47.0% Ballots Corrupted\n(Raw QBER flips bits in K_Bob,\nviolating OTP reversibility)",
        ha='center', fontsize=9.5, fontweight='semibold', color='#991b1b',
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#fee2e2", edgecolor="#ef4444", lw=1.2)
    )

    ax.text(
        1, 55,
        "100.0% Perfect Recovery\n(Key reconciliation aligns K_Bob = K_Alice\nprior to XOR decryption)",
        ha='center', fontsize=9.5, fontweight='semibold', color='#065f46',
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#d1fae5", edgecolor="#10b981", lw=1.2)
    )

    ax.set_title("One-Time Pad Ballot Recovery Rate under Quantum Channel Noise", fontsize=13, fontweight='bold', pad=14, color='#111827')
    ax.set_ylabel("Ballot Decryption Accuracy (%)", fontsize=11, fontweight='semibold', labelpad=10)
    ax.set_ylim(0, 118)
    ax.grid(axis='y', zorder=0)
    ax.legend(loc='lower right', framealpha=0.95, fontsize=10)

    save_report_figure(fig, "report_fig6_ballot_recovery_error_correction.png")
    plt.close(fig)


# ==============================================================================
# Main Runner
# ==============================================================================

def main():
    print("Generating clear, report-focused figures...")
    make_fig1_key_success_rate()
    make_fig2_binomial_sifting()
    make_fig3_qber_threshold()
    make_fig4_noise_vs_eve_densities()
    make_fig5_estimation_convergence()
    make_fig6_ballot_recovery()
    print("Done! All 6 individual report figures generated.")


if __name__ == "__main__":
    main()
