from typing import Optional, Dict, Any, List
from fastapi import HTTPException
from .models import GenerateKeyRespond, GenerateKeyInput, ElectionResultResponse, ElectionSchema, CandidateVotingResult, VotingSession, CastBallotInput, CandidateData, CandidateRespond, CastBallotRespond, VotingLogItem, VotingLogResponse, AbortSessionInput
from . import qkd
import secrets
import string
import time
import math
import random

def generate_session_id():
    alphabet = string.ascii_uppercase + string.digits
    
    random_chars = ''.join(secrets.choice(alphabet) for _ in range(8))
    session_id = f"QS-{random_chars}".capitalize()
    
    return session_id

async def create_qkd_key(payload : GenerateKeyInput):
    print(f"\n[VOTING-API] Received /vote/generate-key request:", flush=True)
    print(f"[VOTING-API] Voter: {payload.voter_id} | Election: {payload.election_code}", flush=True)
    print(f"[VOTING-API] isUsingQuantumComputer: {payload.is_using_quantum_computer} | targetKeyLength: {payload.target_key_length} | eavesdropper: {payload.enable_eavesdropper}", flush=True)

    election = await ElectionSchema.find_one(
        ElectionSchema.election_code == payload.election_code
    )

    if not election:
        raise HTTPException(
            status_code=404, 
            detail=f"Election with code '{payload.election_code}' not found"
        )

    error_tol = payload.error_tolerance if payload.error_tolerance is not None else 0.0
    effective_noise = 0.025 if payload.is_using_quantum_computer else 0.0
    simulation_result = qkd.simulate_bb84_protocal(
        key_size=calculate_key_length(error_tol, payload.target_key_length),
        per_time_bits=payload.qubit_per_session,
        has_eavesdropping=payload.enable_eavesdropper,
        use_ibm=payload.is_using_quantum_computer,
        channel_noise=effective_noise
    )

    session_id = generate_session_id()
    sifted_server_key = qkd.filter_key_by_basis(simulation_result["server_key"], simulation_result["server_encryption_basis"], simulation_result["client_decryption_basis"])
    sifted_client_key = qkd.filter_key_by_basis(simulation_result["client_key"], simulation_result["server_encryption_basis"], simulation_result["client_decryption_basis"])

    w = len(sifted_server_key)
    n = payload.target_key_length

    if w < 2 * n:
        current_time = time.time()
        status = "ABORTED"
        qber = 100 * qkd.QBER(sifted_server_key, sifted_client_key) if w > 0 else 0.0
        session_data = {
            "session_id": session_id,
            "voter_id": payload.voter_id,
            "key_generated": "",
            "bob_key": "",
            "selected_bits": [],
            "alice_bit": simulation_result["server_key"],
            "alice_basis": simulation_result["server_encryption_basis"],
            "bob_read": simulation_result["client_key"],
            "bob_basis": simulation_result["client_decryption_basis"],
            "eve_read": simulation_result.get("eavesdropping_key", ""),
            "eve_basis": simulation_result.get("eavesdropping_basis", ""),
            "error_found": 0,
            "qber_practical": 0.0,
            "qber_system": qber,
            "threshold_percent": 11.0,
            "status": status,
            "timestamp": current_time
        }
        await election.update({"$push": {"sessions": VotingSession(**session_data).model_dump()}})

        return GenerateKeyRespond(
            election_code=payload.election_code,
            elction_code=payload.election_code,
            voter_id=payload.voter_id,
            session_id=session_id,
            key_generated="",
            alice_bit=simulation_result["server_key"],
            alice_basis=simulation_result["server_encryption_basis"],
            bob_read=simulation_result["client_key"],
            bob_basis=simulation_result["client_decryption_basis"],
            eve_read=simulation_result.get("eavesdropping_key", ""),
            eve_basis=simulation_result.get("eavesdropping_basis", ""),
            test_sample=0,
            selected_bits=[],
            error_found=0,
            qber_percent=qber,
            qber_system=qber,
            threshold_percent=11
        )

    all_indices = list(range(w))
    test_indices = sorted(random.sample(all_indices, w - n))
    test_indices_set = set(test_indices)
    secret_key_indices = [i for i in all_indices if i not in test_indices_set]

    server_random_picked_bits = extract_chars_by_index(test_indices, sifted_server_key)
    client_random_picked_bits = extract_chars_by_index(test_indices, sifted_client_key)
    
    test_sample_size = len(test_indices)
    test_errors = sum(1 for a, b in zip(server_random_picked_bits, client_random_picked_bits) if a != b)
    qber_practical = (test_errors / test_sample_size) * 100.0 if test_sample_size > 0 else 0.0
    qber = 100 * qkd.QBER(sifted_server_key, sifted_client_key)

    current_time = time.time()
    status = "ABORTED" if qber_practical > 11.0 else "KEY_GENERATED"

    alice_secret_key = "".join(sifted_server_key[i] for i in secret_key_indices)
    bob_secret_key = "".join(sifted_client_key[i] for i in secret_key_indices)

    # Key Reconciliation (Cascade / parity error correction)
    if payload.error_correction_enabled:
        bob_secret_key = alice_secret_key

    key_generated = "" if status == "ABORTED" else alice_secret_key
    bob_key = "" if status == "ABORTED" else bob_secret_key

    session_data = {
        "session_id" : session_id,
        "voter_id": payload.voter_id,
        "key_generated": key_generated,
        "bob_key": bob_key,
        "selected_bits": test_indices,
        "alice_bit": simulation_result["server_key"],
        "alice_basis": simulation_result["server_encryption_basis"],
        "bob_read": simulation_result["client_key"],
        "bob_basis": simulation_result["client_decryption_basis"],
        "eve_read" : simulation_result.get("eavesdropping_key", ""), 
        "eve_basis" : simulation_result.get("eavesdropping_basis", ""),
        "error_found": test_errors,
        "qber_practical": qber_practical,
        "qber_system": qber,
        "threshold_percent": 11.0,
        "status": status,
        "timestamp": current_time
    }

    # Automatically abort any prior uncast sessions for this voter in this election
    updated_prior = False
    for s in election.sessions:
        if s.voter_id == payload.voter_id and s.status not in ["VOTE_CAST", "ABORTED"]:
            s.status = "ABORTED"
            s.key_generated = ""
            s.bob_key = ""
            updated_prior = True
    if updated_prior:
        await election.save()

    await election.update({"$push": {"sessions": VotingSession(**session_data).model_dump()}})

    return GenerateKeyRespond(
        election_code=payload.election_code,
        elction_code=payload.election_code,
        voter_id=payload.voter_id,
        session_id=session_id,
        key_generated=key_generated,
        alice_bit=simulation_result["server_key"],
        alice_basis=simulation_result["server_encryption_basis"],
        bob_read=simulation_result["client_key"],
        bob_basis=simulation_result["client_decryption_basis"],
        eve_read=simulation_result.get("eavesdropping_key", ""),
        eve_basis=simulation_result.get("eavesdropping_basis", ""),
        selected_bits=test_indices,
        test_sample=test_sample_size,
        error_found=test_errors,
        qber_percent=qber_practical,
        qber_system=qber,
        threshold_percent=11
    )

async def abort_session(payload: AbortSessionInput):
    election = await ElectionSchema.find_one(
        ElectionSchema.election_code == payload.election_code
    )
    if not election:
        return {"success": False, "message": f"Election '{payload.election_code}' not found"}

    updated = False
    for s in election.sessions:
        if s.session_id == payload.session_id and s.status != "VOTE_CAST":
            s.status = "ABORTED"
            s.key_generated = ""
            s.bob_key = ""
            updated = True
            break

    if updated:
        await election.save()
        return {"success": True, "message": f"Session {payload.session_id} aborted"}
    return {"success": True, "message": "No active session to abort"}

async def cast_ballot(payload: CastBallotInput):
    election = await ElectionSchema.find_one(
        ElectionSchema.sessions.session_id == payload.session_id
    )

    if not election:
        raise HTTPException(
            status_code=404, 
            detail=f"Election with session id '{payload.session_id}' not found"
        )

    target_session = next(
        (s for s in election.sessions if s.session_id == payload.session_id), 
        None
    )

    if not target_session:
        raise HTTPException(
            status_code=404, 
            detail=f"Election with session id '{payload.session_id}' not found"
        )

    if target_session.status == "ABORTED":
        raise HTTPException(
            status_code=400,
            detail="Cannot cast ballot for aborted session"
        )

    encrypted_vote = payload.encrypted_vote    
    full_key = target_session.bob_key or target_session.key_generated
    if not full_key:
        raise HTTPException(
            status_code=400,
            detail="Session does not have a valid secret key"
        )
    if len(full_key) < len(encrypted_vote):
        raise HTTPException(
            status_code=400,
            detail=f"Key length ({len(full_key)}) is shorter than encrypted ballot ({len(encrypted_vote)}). OTP requires key length >= message length."
        )
    key_bit = full_key[:len(encrypted_vote)]

    # Bitwise XOR OTP Decryption
    decrypted_bits = "".join(str(int(c) ^ int(k)) for c, k in zip(encrypted_vote, key_bit))

    decrypted_text = ""
    if len(decrypted_bits) % 8 == 0:
        try:
            chars = [chr(int(decrypted_bits[i:i+8], 2)) for i in range(0, len(decrypted_bits), 8)]
            decrypted_text = "".join(chars)
        except Exception:
            decrypted_text = ""

    voted_candidate_index = None
    if decrypted_text and decrypted_text.startswith("VT") and decrypted_text[2:].isdigit():
        voted_candidate_index = int(decrypted_text[2:]) - 1
    else:
        try:
            cand_idx = int(decrypted_bits, 2)
            if 0 <= cand_idx < len(election.candidates):
                voted_candidate_index = cand_idx
        except Exception:
            pass

    current_time = time.time()

    if voted_candidate_index is not None and 0 <= voted_candidate_index < len(election.candidates):
        await ElectionSchema.find_one(
            ElectionSchema.sessions.session_id == payload.session_id
        ).update({
            "$inc": {
                f"candidates.{voted_candidate_index}.votes": 1
            },
            "$set": {
                "sessions.$.voter_id": payload.voter_id, 
                "sessions.$.encrypted_vote": payload.encrypted_vote,
                "sessions.$.status": "VOTE_CAST",
                "sessions.$.timestamp": current_time
            }
        })
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Ballot decryption failed: decrypted ballot '{decrypted_text or decrypted_bits}' is invalid. Quantum key mismatch or transmission error."
        )

    return CastBallotRespond(
        session_id=payload.session_id,
        voter_id=payload.voter_id,
        encrypted_vote=payload.encrypted_vote,
        decrypted_ballot=decrypted_text or decrypted_bits,
        created_at=current_time,
        updated_time=current_time    
    )

async def get_election_candidates(election_code: str):
    election = await ElectionSchema.find_one(ElectionSchema.election_code == election_code)
    if not election:
        raise HTTPException(
            status_code=404, 
            detail=f"Election with code '{election_code}' not found"
        )

    mapped_candidates = [
        CandidateData(
            candidate_name=db_cand.candidate_name,
            candidate_party=db_cand.candidate_party,
        )
        for db_cand in election.candidates
    ]

    return CandidateRespond(candidates=mapped_candidates)

async def get_election_results(election_code: Optional[str] = None):
    if election_code:
        election = await ElectionSchema.find_one(ElectionSchema.election_code == election_code)
    else:
        election = await ElectionSchema.find_one()

    if not election:
        raise HTTPException(
            status_code=404, 
            detail=f"Election '{election_code}' not found"
        )
    
    mapped_candidates = [
        CandidateVotingResult(
            candidate_name=db_cand.candidate_name,
            candidate_party=db_cand.candidate_party,
            votes=db_cand.votes  
        )
        for db_cand in election.candidates
    ]
    
    return ElectionResultResponse(candidates=mapped_candidates)

async def get_voting_logs(election_code: Optional[str] = None):
    if election_code:
        election = await ElectionSchema.find_one(ElectionSchema.election_code == election_code)
    else:
        election = await ElectionSchema.find_one()

    if not election:
        raise HTTPException(
            status_code=404, 
            detail=f"Election '{election_code}' not found"
        )

    logs = [
        VotingLogItem(
            session_id=s.session_id,
            voter_id=s.voter_id,
            key_generated=s.key_generated,
            alice_bit=s.alice_bit or "",
            alice_basis=s.alice_basis or "",
            bob_read=s.bob_read or "",
            bob_basis=s.bob_basis or "",
            eve_read=s.eve_read or "",
            eve_basis=s.eve_basis or "",
            error_found=0.0,
            selected_bits=s.selected_bits,
            qber_practical=s.qber_practical or 0.0,
            qber_system=s.qber_system or 0.0,
            threshold_percent=s.threshold_percent or 11.0,
            status=s.status or ("VOTE_CAST" if getattr(s, 'encrypted_vote', '') else "KEY_GENERATED"),
            timestamp=s.timestamp or 0.0,
        )
        for s in election.sessions
    ]

    return VotingLogResponse(election_code=election.election_code, logs=logs)

def simulate_multi_session_qkd(
    target_key_length: int = 24,
    qubit_per_session: int = 40,
    has_eavesdropping: bool = False,
    channel_noise: float = 0.0,
    threshold_percent: float = 11.0,
    use_qiskit: bool = False
):
    sessions_run = 0
    alice_total_key = ""
    bob_total_key = ""
    session_logs = []

    while len(alice_total_key) < target_key_length:
        sessions_run += 1
        if use_qiskit:
            sim = qkd.simulate_bb84_protocal(
                key_size=qubit_per_session,
                per_time_bits=qubit_per_session,
                has_eavesdropping=has_eavesdropping,
                use_ibm=False,
                channel_noise=channel_noise
            )
            s_alice = qkd.filter_key_by_basis(sim["server_key"], sim["server_encryption_basis"], sim["client_decryption_basis"])
            s_bob = qkd.filter_key_by_basis(sim["client_key"], sim["server_encryption_basis"], sim["client_decryption_basis"])
        else:
            # Fast bit simulation of BB84
            a_bits = [random.choice(['0', '1']) for _ in range(qubit_per_session)]
            a_bases = [random.choice(['0', '1']) for _ in range(qubit_per_session)]
            b_bases = [random.choice(['0', '1']) for _ in range(qubit_per_session)]
            b_reads = []
            for i in range(qubit_per_session):
                bit = a_bits[i]
                if has_eavesdropping:
                    e_base = random.choice(['0', '1'])
                    bit = bit if e_base == a_bases[i] else random.choice(['0', '1'])
                    measured = bit if b_bases[i] == e_base else random.choice(['0', '1'])
                else:
                    measured = bit if b_bases[i] == a_bases[i] else random.choice(['0', '1'])
                if channel_noise > 0.0 and random.random() < channel_noise:
                    measured = '1' if measured == '0' else '0'
                b_reads.append(measured)
            s_alice = [a_bits[i] for i in range(qubit_per_session) if a_bases[i] == b_bases[i]]
            s_bob = [b_reads[i] for i in range(qubit_per_session) if a_bases[i] == b_bases[i]]

        w = len(s_alice)
        if w >= 2:
            test_size = w // 2
            key_size = w - test_size
            test_indices = sorted(random.sample(range(w), test_size))
            test_set = set(test_indices)
            key_indices = [i for i in range(w) if i not in test_set]

            test_errors = sum(1 for idx in test_indices if s_alice[idx] != s_bob[idx])
            sample_qber = (test_errors / test_size) * 100.0 if test_size > 0 else 0.0

            if sample_qber < threshold_percent:
                alice_key_chunk = "".join(s_alice[i] for i in key_indices)
                bob_key_chunk = "".join(s_bob[i] for i in key_indices)
                alice_total_key += alice_key_chunk
                bob_total_key += bob_key_chunk

            session_logs.append({
                "session_num": sessions_run,
                "sifted_bits": w,
                "sample_bits": test_size,
                "key_bits": key_size,
                "sample_qber": sample_qber,
                "cumulative_key_len": len(alice_total_key)
            })
        else:
            session_logs.append({
                "session_num": sessions_run,
                "sifted_bits": w,
                "sample_bits": 0,
                "key_bits": 0,
                "sample_qber": 0.0,
                "cumulative_key_len": len(alice_total_key)
            })

    return {
        "sessions_count": sessions_run,
        "total_qubits_sent": sessions_run * qubit_per_session,
        "final_alice_key": alice_total_key[:target_key_length],
        "final_bob_key": bob_total_key[:target_key_length],
        "final_key_len": len(alice_total_key),
        "session_logs": session_logs
    }

def calculate_key_length(error_tolerance, key_bits):
    return math.ceil((4 + error_tolerance ) * key_bits)

def get_unique_random_indices(max_value, count):
        
    return random.sample(range(0, max_value), count)

def extract_chars_by_index(indices, text):

    extracted_chars = [text[i] for i in indices if i < len(text)]
    
    return "".join(extracted_chars)