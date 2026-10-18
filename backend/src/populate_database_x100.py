import asyncio
import os
import json
import random
import time
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Ensure local Aer simulation is used (no IBM cloud queue blocking)
os.environ["USE_REAL_IBM_HARDWARE"] = "false"
os.environ["USE_IBM_QUANTUM"] = "false"

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

from core.database import init_db
from modules.models import ElectionSchema, GenerateKeyInput, CastBallotInput, VotingSession
from modules import service, qkd

def xor_encrypt(plaintext: str, key: str) -> str:
    """OTP Bitwise XOR encryption"""
    return "".join(str(int(p) ^ int(k)) for p, k in zip(plaintext, key))

def decrypt_ballot(encrypted_vote: str, key: str) -> int:
    """OTP Bitwise XOR decryption matching service.cast_ballot logic"""
    key_bit = key[:len(encrypted_vote)]
    decrypted_bits = "".join(str(int(c) ^ int(k)) for c, k in zip(encrypted_vote, key_bit))
    decrypted_text = ""
    if len(decrypted_bits) % 8 == 0:
        try:
            chars = [chr(int(decrypted_bits[i:i+8], 2)) for i in range(0, len(decrypted_bits), 8)]
            decrypted_text = "".join(chars)
        except Exception:
            decrypted_text = ""

    if decrypted_text and decrypted_text.startswith("VT") and decrypted_text[2:].isdigit():
        return int(decrypted_text[2:]) - 1
    return int(decrypted_bits, 2)

async def main():
    print("=" * 70)
    print(">>> INITIALIZING DATABASE & BACKUP <<<")
    print("=" * 70)
    await init_db()

    election = await ElectionSchema.find_one(ElectionSchema.election_code == "ELECT2026")
    if not election:
        raise RuntimeError("Election 'ELECT2026' not found in database!")

    # 1. Backup existing election state
    backup_path = Path(__file__).resolve().parent / "evaluation" / "data" / "election_backup_before_x100.json"
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(election.model_dump(), f, indent=2, default=str)
    print(f"[BACKUP] Existing election data saved to: {backup_path}")
    print(f"Current sessions count: {len(election.sessions)}")
    print(f"Current candidate votes: {[f'{c.candidate_name}: {c.votes}' for c in election.candidates]}")

    # 2. Backfill missing encrypted_vote for existing VOTE_CAST sessions
    # The existing votes were: Sierra: 5, Raul: 6, Gabrielle: 3, Alan: 2 (total 16 for the 16 VOTE_CAST sessions)
    existing_vote_distribution = [0]*5 + [1]*6 + [2]*3 + [3]*2  # exactly 16 votes
    random.shuffle(existing_vote_distribution)
    
    cand_dist_idx = 0
    for s in election.sessions:
        if s.status == "VOTE_CAST":
            target_key = s.bob_key or s.key_generated
            if not target_key:
                # Generate a fallback 24-bit key if session had none
                target_key = "".join(random.choice(["0", "1"]) for _ in range(24))
                s.key_generated = target_key
                s.bob_key = target_key
            
            c_idx = existing_vote_distribution[cand_dist_idx % len(existing_vote_distribution)]
            cand_dist_idx += 1
            cand_bin = bin(c_idx)[2:].zfill(len(target_key))
            s.encrypted_vote = xor_encrypt(cand_bin, target_key)

    print(f"[BACKFILL] Backfilled {cand_dist_idx} existing VOTE_CAST sessions with valid OTP encrypted ballots.")

    # 3. Generate 100 new varied sessions through the real system
    print("\n" + "=" * 70)
    print(">>> RUNNING SYSTEM x100 WITH VARIED SETTINGS <<<")
    print("=" * 70)

    # Various settings pool
    key_lengths = [16, 24, 32, 64]
    qubits_options = [40, 64, 80]
    security_params = [8, 16, 32]
    error_tolerances = [0.0, 0.02, 0.05]

    # Pre-plan ~20 Eve attacks, ~80 normal sessions
    eve_plan = [True] * 20 + [False] * 80
    random.shuffle(eve_plan)

    new_voters = [f"V-2026-{101 + i:04d}" for i in range(100)]
    
    # Candidate choices for cast votes
    # Realistic election distribution: Sierra (35%), Raul (30%), Gabrielle (20%), Alan (15%)
    candidate_weights = [0.35, 0.30, 0.20, 0.15]

    successful_keys = 0
    eavesdropped_aborts = 0
    votes_cast_count = 0
    uncast_keys_count = 0

    t_start = time.time()

    for idx, (voter_id, has_eve) in enumerate(zip(new_voters, eve_plan)):
        target_k = random.choice(key_lengths)
        qubit_chunk = random.choice(qubits_options)
        sec_p = random.choice(security_params)
        err_tol = random.choice(error_tolerances)
        use_qc_noise = (idx % 2 == 0)  # 50% simulated quantum computer noise
        use_pa = (idx % 5 != 0)         # 80% privacy amplification enabled

        payload = GenerateKeyInput(
            voter_id=voter_id,
            election_code="ELECT2026",
            is_using_quantum_computer=use_qc_noise,
            error_correction_enabled=True,
            enable_eavesdropper=has_eve,
            qubit_per_session=qubit_chunk,
            target_key_length=target_k,
            error_tolerance=err_tol,
            privacy_amplification_enabled=use_pa,
            security_parameter=sec_p
        )

        key_resp = await service.create_qkd_key(payload)

        if has_eve or key_resp.qber_percent > 11.0 or not key_resp.key_generated:
            eavesdropped_aborts += 1
            if (idx + 1) % 10 == 0:
                print(f"[{idx+1:03d}/100] Voter {voter_id} -> ABORTED (QBER: {key_resp.qber_percent:.1f}%, Eve: {has_eve})")
        else:
            successful_keys += 1
            # ~95% of successful keys cast their ballot, ~5% leave it uncast
            should_cast = (random.random() < 0.95)
            if should_cast:
                chosen_candidate = random.choices([0, 1, 2, 3], weights=candidate_weights)[0]
                final_key = key_resp.key_generated
                cand_binary = bin(chosen_candidate)[2:].zfill(len(final_key))
                encrypted_ballot = xor_encrypt(cand_binary, final_key)

                cast_input = CastBallotInput(
                    session_id=key_resp.session_id,
                    voter_id=voter_id,
                    encrypted_vote=encrypted_ballot
                )
                await service.cast_ballot(cast_input)
                votes_cast_count += 1
            else:
                uncast_keys_count += 1

            if (idx + 1) % 10 == 0:
                print(f"[{idx+1:03d}/100] Voter {voter_id} -> SUCCESS (Key: {len(key_resp.key_generated)}b, QBER: {key_resp.qber_percent:.1f}%, Cast: {should_cast})")

    elapsed = time.time() - t_start
    print(f"\n[EXECUTION COMPLETE] 100 runs completed in {elapsed:.2f}s ({elapsed/100:.3f}s/run)")
    print(f"Results: {successful_keys} keys generated ({votes_cast_count} votes cast, {uncast_keys_count} uncast), {eavesdropped_aborts} aborted due to eavesdropping.")

    # 4. Scatter all session timestamps over October 2026
    print("\n" + "=" * 70)
    print(">>> SCATTERING ALL TIMESTAMPS OVER OCTOBER 2026 <<<")
    print("=" * 70)

    # Re-fetch the updated election document from DB
    election = await ElectionSchema.find_one(ElectionSchema.election_code == "ELECT2026")
    total_sessions = len(election.sessions)
    print(f"Total sessions in database: {total_sessions}")

    # Timespan: October 1, 2026 to October 16, 2026 (current time ~ 09:15)
    # Generate realistic timestamps across these 16 days
    start_dt = datetime(2026, 10, 1, 8, 30, 0)
    end_dt = datetime(2026, 10, 16, 9, 10, 0)
    total_seconds = (end_dt - start_dt).total_seconds()

    # Generate random sorted points in [0, 1] with slight daytime bias
    timestamps = []
    for _ in range(total_sessions):
        # Pick a day between 1 and 16
        day_offset = random.randint(0, 15)
        # Pick hour between 8 and 20 (on day 15/Oct 16, hour between 6 and 9)
        if day_offset == 15:
            hour = random.randint(6, 8)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
        else:
            # Business hours 8:00 - 20:00
            hour = random.randint(8, 19)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
        dt = datetime(2026, 10, 1, hour, minute, second) + timedelta(days=day_offset)
        timestamps.append(dt.timestamp())

    timestamps.sort()

    for s, ts in zip(election.sessions, timestamps):
        s.timestamp = ts

    # Sort sessions by timestamp ascending
    election.sessions.sort(key=lambda s: s.timestamp)

    print(f"Scattered {len(timestamps)} timestamps from {datetime.fromtimestamp(timestamps[0])} to {datetime.fromtimestamp(timestamps[-1])}")

    # 5. Recount vote results to match
    print("\n" + "=" * 70)
    print(">>> RECOUNTING VOTE RESULTS TO MATCH SESSIONS <<<")
    print("=" * 70)

    recount_tallies = [0, 0, 0, 0]
    total_cast_found = 0

    for s in election.sessions:
        if s.status == "VOTE_CAST":
            target_key = s.bob_key or s.key_generated
            if s.encrypted_vote and target_key:
                cand_idx = decrypt_ballot(s.encrypted_vote, target_key)
                if 0 <= cand_idx < len(election.candidates):
                    recount_tallies[cand_idx] += 1
                    total_cast_found += 1
                else:
                    print(f"[WARN] Decrypted candidate index {cand_idx} out of range for session {s.session_id}")
            else:
                print(f"[WARN] Session {s.session_id} is VOTE_CAST but missing encrypted_vote or key!")

    print(f"Recounted Votes across {total_cast_found} VOTE_CAST sessions:")
    for i, c in enumerate(election.candidates):
        old_v = c.votes
        new_v = recount_tallies[i]
        c.votes = new_v
        pct = (new_v / total_cast_found * 100.0) if total_cast_found > 0 else 0.0
        print(f" - Candidate {i} ({c.candidate_name} / {c.candidate_party}): {old_v} -> {new_v} votes ({pct:.1f}%)")

    print(f"Total Recount Sum: {sum(recount_tallies)} == Total VOTE_CAST: {total_cast_found}")
    assert sum(recount_tallies) == total_cast_found, "Recount mismatch!"

    # Save to MongoDB Atlas
    await election.save()
    print("\n[SUCCESS] Election 'ELECT2026' successfully saved to MongoDB Atlas!")

    # Verify reload from MongoDB
    verify_el = await ElectionSchema.find_one(ElectionSchema.election_code == "ELECT2026")
    print(f"[VERIFIED] Reloaded from DB: {len(verify_el.sessions)} sessions, {sum(c.votes for c in verify_el.candidates)} total votes.")
    first_dt = datetime.fromtimestamp(verify_el.sessions[0].timestamp)
    last_dt = datetime.fromtimestamp(verify_el.sessions[-1].timestamp)
    print(f"[VERIFIED] Timestamp range: {first_dt.strftime('%Y-%m-%d %H:%M:%S')} -> {last_dt.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())
