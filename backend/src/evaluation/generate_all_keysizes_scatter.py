"""
Generate Priority 2 Blind Verification Scatter Data Across ALL Key Sizes
Key sizes: 8, 16, 24, 32, 64, 128, 256 bits.
Saves results into master_benchmark_raw_data.json and renders both:
1. minimal_priority2_sample_vs_key_scatter.png (Combined across all key sizes)
2. minimal_priority2_scatter_grid_powers_of_2.png (2x3 grid breakdown)
"""
import sys
import os
import json
import random
import numpy as np

# Ensure backend root is on path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_SRC = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_SRC not in sys.path:
    sys.path.insert(0, BACKEND_SRC)

from modules import qkd, service

DATA_PATH = os.path.join(CURRENT_DIR, "data", "master_benchmark_raw_data.json")

def main():
    print("=" * 70)
    print("GENERATING SCATTER DATA FOR ALL KEY SIZES (Priority 2)")
    print("Key sizes: [8, 16, 24, 32, 64, 128, 256] bits")
    print("=" * 70)

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        master_data = json.load(f)

    key_sizes = [8, 16, 24, 32, 64, 128, 256]
    trials = 100

    scatter_by_keysize = {}
    combined_normal = {"sample_qber": [], "key_qber": [], "key_size": []}
    combined_ibm = {"sample_qber": [], "key_qber": [], "key_size": []}
    combined_eve = {"sample_qber": [], "key_qber": [], "key_size": []}

    for ks in key_sizes:
        print(f" -> Simulating key size n = {ks} bits (100 trials per scenario)...")
        total_q = service.calculate_key_length(0.8, ks)
        
        s_norm, k_norm = [], []
        s_ibm, k_ibm = [], []
        s_eve, k_eve = [], []

        for _ in range(trials):
            # Normal (Ideal, no noise)
            sim = qkd.simulate_bb84_protocal(key_size=total_q, per_time_bits=min(64, total_q), has_eavesdropping=False, use_ibm=False, channel_noise=0.0)
            s_a = qkd.filter_key_by_basis(sim['server_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            s_b = qkd.filter_key_by_basis(sim['client_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            w = len(s_a)
            if w >= 2 * ks:
                t_idx = set(random.sample(range(w), w - ks))
                k_idx = [i for i in range(w) if i not in t_idx][:ks]
                s_norm.append(float((sum(1 for i in t_idx if s_a[i] != s_b[i]) / len(t_idx)) * 100.0))
                k_norm.append(float((sum(1 for i in k_idx if s_a[i] != s_b[i]) / len(k_idx)) * 100.0))

            # IBM Hardware Noise (2.82%)
            sim = qkd.simulate_bb84_protocal(key_size=total_q, per_time_bits=min(64, total_q), has_eavesdropping=False, use_ibm=True, channel_noise=0.0282)
            s_a = qkd.filter_key_by_basis(sim['server_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            s_b = qkd.filter_key_by_basis(sim['client_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            w = len(s_a)
            if w >= 2 * ks:
                t_idx = set(random.sample(range(w), w - ks))
                k_idx = [i for i in range(w) if i not in t_idx][:ks]
                s_ibm.append(float((sum(1 for i in t_idx if s_a[i] != s_b[i]) / len(t_idx)) * 100.0))
                k_ibm.append(float((sum(1 for i in k_idx if s_a[i] != s_b[i]) / len(k_idx)) * 100.0))

            # Eve Attack (Intercept-Resend ~25%)
            sim = qkd.simulate_bb84_protocal(key_size=total_q, per_time_bits=min(64, total_q), has_eavesdropping=True, use_ibm=False, channel_noise=0.0)
            s_a = qkd.filter_key_by_basis(sim['server_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            s_b = qkd.filter_key_by_basis(sim['client_key'], sim['server_encryption_basis'], sim['client_decryption_basis'])
            w = len(s_a)
            if w >= 2 * ks:
                t_idx = set(random.sample(range(w), w - ks))
                k_idx = [i for i in range(w) if i not in t_idx][:ks]
                s_eve.append(float((sum(1 for i in t_idx if s_a[i] != s_b[i]) / len(t_idx)) * 100.0))
                k_eve.append(float((sum(1 for i in k_idx if s_a[i] != s_b[i]) / len(k_idx)) * 100.0))

        scatter_by_keysize[str(ks)] = {
            "normal": {"sample_qber": s_norm, "key_qber": k_norm},
            "ibm_hardware": {"sample_qber": s_ibm, "key_qber": k_ibm},
            "eve": {"sample_qber": s_eve, "key_qber": k_eve}
        }

        combined_normal["sample_qber"].extend(s_norm)
        combined_normal["key_qber"].extend(k_norm)
        combined_normal["key_size"].extend([ks] * len(s_norm))

        combined_ibm["sample_qber"].extend(s_ibm)
        combined_ibm["key_qber"].extend(k_ibm)
        combined_ibm["key_size"].extend([ks] * len(s_ibm))

        combined_eve["sample_qber"].extend(s_eve)
        combined_eve["key_qber"].extend(k_eve)
        combined_eve["key_size"].extend([ks] * len(s_eve))

    # Update master_data
    if "priority2_blind_verification" not in master_data:
        master_data["priority2_blind_verification"] = {}

    master_data["priority2_blind_verification"]["scatter_by_keysize"] = scatter_by_keysize
    master_data["priority2_blind_verification"]["scatter_all_keysizes"] = {
        "normal": combined_normal,
        "ibm_hardware": combined_ibm,
        "eve": combined_eve
    }
    # Keep 24bits for backward compatibility
    if "24" in scatter_by_keysize:
        master_data["priority2_blind_verification"]["scatter_24bits"] = scatter_by_keysize["24"]

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(master_data, f, indent=2)

    print(f"\n[CACHE UPDATED] Successfully saved all key sizes scatter data into {DATA_PATH}")

if __name__ == "__main__":
    main()
