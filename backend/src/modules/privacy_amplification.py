import secrets
import math
from typing import Dict, Any
import numpy as np


def generate_toeplitz_seed(input_len: int, output_len: int) -> str:
    """
    Generate a cryptographically secure random bitstring for Toeplitz matrix hashing.
    An m x n Toeplitz matrix requires exactly n + m - 1 random bits.
    """
    if input_len <= 0 or output_len <= 0:
        raise ValueError("Key lengths must be positive integers.")
    seed_len = input_len + output_len - 1
    return "".join(secrets.choice("01") for _ in range(seed_len))


def construct_toeplitz_matrix(seed: str, m: int, n: int) -> np.ndarray:
    """
    Construct an m x n Toeplitz matrix A over GF(2) from a public seed.
    Guarantees that every descending diagonal A[i, j] == A[i+1, j+1] is constant:
    A[i, j] = int(seed[m - 1 - i + j]) for 0 <= i < m, 0 <= j < n.
    """
    if len(seed) < n + m - 1:
        raise ValueError(
            f"Seed length ({len(seed)}) is shorter than required dimension ({n + m - 1})."
        )
    A = np.zeros((m, n), dtype=np.uint8)
    for i in range(m):
        for j in range(n):
            A[i, j] = int(seed[m - 1 - i + j])
    return A


def toeplitz_hash(key_bits: str, seed_bits: str, output_len: int) -> str:
    """
    Apply 2-universal Toeplitz matrix multiplication over GF(2).
    Extracts an output_len bit secret key from an input key_bits string.
    k_out = (T * x) mod 2.
    """
    n = len(key_bits)
    m = output_len
    if n == 0 or m == 0:
        return ""
    if m > n:
        raise ValueError(f"Output length ({m}) cannot exceed raw key length ({n}).")
    if len(seed_bits) < n + m - 1:
        raise ValueError(
            f"Seed length ({len(seed_bits)}) is too short for input {n} and output {m} (needs {n + m - 1})."
        )

    x = np.array([int(b) for b in key_bits], dtype=np.uint8)
    A = construct_toeplitz_matrix(seed_bits, m, n)
    y = np.dot(A, x) % 2
    return "".join(str(int(bit)) for bit in y)


def binary_entropy(p: float) -> float:
    """Calculate Shannon binary entropy h(p) = -p log2(p) - (1-p) log2(1-p)."""
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)


def estimate_eve_information(qber: float, key_length: int, model: str = "intercept_resend") -> float:
    """
    Estimate the upper bound on Eve's mutual information in bits.
    - 'intercept_resend': I_E = 2 * qber * key_length
    - 'shannon': I_E = h(qber) * key_length
    """
    if qber <= 0.0:
        return 0.0
    if model == "shannon":
        return binary_entropy(qber) * key_length
    return min(float(key_length), 2.0 * qber * key_length)


def calculate_amplified_key_length(
    raw_key_length: int,
    security_parameter: int = 16,
    qber: float = 0.0,
    ec_leak_bits: int = 0
) -> int:
    """
    Calculate the secure post-hash key length m under the Leftover Hash Lemma:
    m = max(0, raw_key_length - I_E - ec_leak_bits - security_parameter)
    """
    eve_info = estimate_eve_information(qber, raw_key_length)
    effective_reduction = math.ceil(eve_info) + ec_leak_bits + security_parameter
    return max(0, raw_key_length - effective_reduction)


def calculate_required_raw_length(
    target_key_length: int,
    security_parameter: int = 16,
    qber: float = 0.0,
    ec_leak_bits: int = 0
) -> int:
    """
    Calculate the raw key length needed before privacy amplification to yield target_key_length:
    n_raw >= (target_key_length + ec_leak_bits + security_parameter) / (1 - 2*qber)
    For zero error (qber = 0, ec_leak = 0), this simplifies to: target_key_length + security_parameter.
    """
    if qber <= 0.0:
        return target_key_length + ec_leak_bits + security_parameter
    headroom_factor = max(0.01, 1.0 - 2.0 * qber)
    return math.ceil((target_key_length + ec_leak_bits + security_parameter) / headroom_factor)
