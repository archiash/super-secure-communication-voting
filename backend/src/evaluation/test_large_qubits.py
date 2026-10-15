import sys
sys.path.insert(0, "backend/src")
from modules import qkd, service

for n in [8, 16, 32, 64, 128, 256]:
    total_q = service.calculate_key_length(0.8, n)
    print(f"Testing n={n}, total_q={total_q}...")
    sim = qkd.simulate_bb84_protocal(key_size=total_q, per_time_bits=min(64, total_q), has_eavesdropping=True, use_ibm=False, channel_noise=0.0)
    print(f"n={n} success, result keys len={len(sim['server_key'])}")
