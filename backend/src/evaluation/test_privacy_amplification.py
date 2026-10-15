import os
import sys
import unittest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from modules import privacy_amplification as pa


class TestPrivacyAmplification(unittest.TestCase):
    def test_seed_generation(self):
        seed = pa.generate_toeplitz_seed(input_len=40, output_len=24)
        self.assertEqual(len(seed), 40 + 24 - 1)
        self.assertTrue(all(c in "01" for c in seed))

    def test_toeplitz_matrix_diagonals(self):
        m, n = 5, 8
        seed = pa.generate_toeplitz_seed(n, m)
        A = pa.construct_toeplitz_matrix(seed, m, n)
        self.assertEqual(A.shape, (m, n))
        for i in range(m - 1):
            for j in range(n - 1):
                self.assertEqual(A[i, j], A[i + 1, j + 1])

    def test_hash_determinism(self):
        key = "1011001010111100001010110011010101011001"
        m = 24
        seed = pa.generate_toeplitz_seed(len(key), m)
        out1 = pa.toeplitz_hash(key, seed, m)
        out2 = pa.toeplitz_hash(key, seed, m)
        self.assertEqual(out1, out2)
        self.assertEqual(len(out1), m)

    def test_alice_bob_symmetry(self):
        alice_key = "1100101011110000101011001101010101011001"
        bob_key = "1100101011110000101011001101010101011001"
        m = 24
        seed = pa.generate_toeplitz_seed(len(alice_key), m)
        alice_out = pa.toeplitz_hash(alice_key, seed, m)
        bob_out = pa.toeplitz_hash(bob_key, seed, m)
        self.assertEqual(alice_out, bob_out)

    def test_short_seed_raises(self):
        key = "1011"
        seed = "101"
        with self.assertRaises(ValueError):
            pa.toeplitz_hash(key, seed, 3)

    def test_expansion_raises(self):
        key = "1011"
        seed = "10110011"
        with self.assertRaises(ValueError):
            pa.toeplitz_hash(key, seed, 8)

    def test_sizing_calculation(self):
        # Target 24 bits, s = 16, qber = 0
        raw_len = pa.calculate_required_raw_length(target_key_length=24, security_parameter=16, qber=0.0)
        self.assertEqual(raw_len, 40)
        out_len = pa.calculate_amplified_key_length(raw_key_length=40, security_parameter=16, qber=0.0)
        self.assertEqual(out_len, 24)

    def test_eve_information_bound(self):
        info_zero = pa.estimate_eve_information(qber=0.0, key_length=40)
        self.assertEqual(info_zero, 0.0)
        info_11 = pa.estimate_eve_information(qber=0.11, key_length=40)
        self.assertAlmostEqual(info_11, 8.8, places=1)


if __name__ == "__main__":
    unittest.main()
