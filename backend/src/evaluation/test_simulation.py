"""
Automated Unit and Evaluation Tests for BB84 QKD Simulation and Voting Cryptography.
Run with:
    backend\\.venv\\Scripts\\python.exe -m unittest backend/src/evaluation/test_simulation.py
"""

import os
import sys
import unittest
import numpy as np

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from evaluation.run_evaluations import (
    run_bb84_with_sampling,
    otp_encrypt,
    otp_decrypt,
    text_to_binary,
    binary_to_text
)
from modules import qkd


class TestQKDVotingSimulation(unittest.TestCase):

    def setUp(self):
        np.random.seed(42)

    # =========================================================================
    # Test 1: Key Transmission Lengths vs Desired Key Size
    # =========================================================================
    def test_01_key_length_sufficiency(self):
        """
        Verify that transmitting raw qubits with appropriate multiplier
        (e.g., 2.5x to 3.0x target length) provides sufficient final key bits.
        """
        target_len = 64
        # Multiplier 1.0x (insufficient, only ~32 bits after 50% sifting)
        low_mult_res = [
            run_bb84_with_sampling(raw_qubits=target_len, sample_ratio=0.25, has_eavesdropping=False)["key_len"]
            for _ in range(50)
        ]
        self.assertTrue(all(k < target_len for k in low_mult_res),
                        "1.0x multiplier should not yield sufficient key after sifting and sampling")

        # Multiplier 3.5x (sufficient with >= 95% reliability for 64-bit target and 25% check bits)
        high_mult_res = [
            run_bb84_with_sampling(raw_qubits=int(target_len * 3.5), sample_ratio=0.25, has_eavesdropping=False)["key_len"]
            for _ in range(50)
        ]
        success_rate = sum(1 for k in high_mult_res if k >= target_len) / len(high_mult_res)
        self.assertGreaterEqual(success_rate, 0.95,
                                f"3.5x multiplier should yield >= 95% success rate, got {success_rate*100:.1f}%")

    # =========================================================================
    # Test 2: Eavesdropping Detection & Optimal Threshold
    # =========================================================================
    def test_02_eavesdropping_vs_no_eavesdropping(self):
        """
        Verify that:
        1. Clean channel has QBER ~ 0% (or < 5% with baseline noise)
        2. Eavesdropped channel (100% intercept) has QBER ~ 25% (theoretical expectation)
        3. A threshold of 11% clearly discriminates between clean and eavesdropped sessions.
        """
        raw_qubits = 512
        threshold = 11.0

        # No Eve
        clean_qbers = [
            run_bb84_with_sampling(raw_qubits=raw_qubits, sample_ratio=0.3, has_eavesdropping=False)["sample_qber"]
            for _ in range(50)
        ]
        mean_clean = np.mean(clean_qbers)
        self.assertLess(mean_clean, 2.0, "Clean channel without noise should have QBER near 0%")
        self.assertTrue(all(q < threshold for q in clean_qbers), "All clean sessions should pass 11% threshold")

        # With Eve (100% intercept-resend)
        eve_qbers = [
            run_bb84_with_sampling(raw_qubits=raw_qubits, sample_ratio=0.3, has_eavesdropping=True)["sample_qber"]
            for _ in range(50)
        ]
        mean_eve = np.mean(eve_qbers)
        self.assertAlmostEqual(mean_eve, 25.0, delta=5.0,
                               msg=f"Mean Eve QBER should be approximately 25%, got {mean_eve:.2f}%")
        detection_rate = sum(1 for q in eve_qbers if q > threshold) / len(eve_qbers)
        self.assertGreaterEqual(detection_rate, 0.98,
                                f"Detection rate for full Eve should be >= 98%, got {detection_rate*100:.1f}%")


    # =========================================================================
    # Test 4: Difference between Sample QBER and Secret Key QBER
    # =========================================================================
    def test_04_qber_sample_vs_key_difference(self):
        """
        Verify that:
        1. Sample QBER is an unbiased estimator of Secret Key QBER: E[QBER_sample - QBER_key] ≈ 0
        2. Increasing the sample size or raw qubit size reduces estimation error |QBER_sample - QBER_key|
        """
        # Run 100 trials with Eve
        trials = 100
        results_small = [
            run_bb84_with_sampling(raw_qubits=128, sample_ratio=0.15, has_eavesdropping=True)
            for _ in range(trials)
        ]
        results_large = [
            run_bb84_with_sampling(raw_qubits=512, sample_ratio=0.33, has_eavesdropping=True)
            for _ in range(trials)
        ]

        signed_err_small = np.mean([r["signed_diff"] for r in results_small])
        signed_err_large = np.mean([r["signed_diff"] for r in results_large])

        # Unbiasedness: Signed mean error should be close to 0 (< 3.0%)
        self.assertAlmostEqual(signed_err_small, 0.0, delta=3.0,
                               msg=f"Signed error must be near 0 for unbiased estimation, got {signed_err_small:.2f}%")
        self.assertAlmostEqual(signed_err_large, 0.0, delta=2.0,
                               msg=f"Signed error must be near 0 for unbiased estimation, got {signed_err_large:.2f}%")

        # Estimation accuracy improves with larger sample size
        mae_small = np.mean([r["qber_diff"] for r in results_small])
        mae_large = np.mean([r["qber_diff"] for r in results_large])

        self.assertLess(mae_large, mae_small,
                        f"Larger sample size must reduce mean absolute estimation error: {mae_large:.2f}% vs {mae_small:.2f}%")


if __name__ == "__main__":
    unittest.main(verbosity=2)
