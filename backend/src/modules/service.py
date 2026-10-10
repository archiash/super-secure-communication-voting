from fastapi import HTTPException
from .models import GenerateKeyRespond, GenerateKeyInput, ElectionResultResponse, ElectionSchema, CandidateVotingResult, VotingSession, CastBallotInput, CandidateData, CandidateRespond, CastBallotRespond, VotingLogItem, VotingLogResponse
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
    election = await ElectionSchema.find_one(
        ElectionSchema.election_code == payload.election_code
    )

    if not election:
        raise HTTPException(
            status_code=404, 
            detail=f"Election with code '{payload.election_code}' not found"
        )

    simulation_result = qkd.simulate_bb84_protocal(key_size= calculate_key_length(payload.error_tolerance,payload.target_key_length) , per_time_bits= payload.qubit_per_session, has_eavesdropping= payload.enable_eavesdropper, use_ibm= payload.is_using_quantum_computer)

    session_id = generate_session_id()
    key_generated = qkd.filter_key_by_basis(simulation_result["server_key"], simulation_result["server_encryption_basis"], simulation_result["client_decryption_basis"])

    sifted_server_key = qkd.filter_key_by_basis(simulation_result["server_key"], simulation_result["server_encryption_basis"], simulation_result["client_decryption_basis"])
    sifted_client_key = qkd.filter_key_by_basis(simulation_result["client_key"], simulation_result["server_encryption_basis"], simulation_result["client_decryption_basis"])

    random_picked_positions = get_unique_random_indices(len(sifted_client_key),payload.target_key_length)
    server_random_picked_bits = extract_chars_by_index(random_picked_positions, sifted_server_key)
    client_random_picked_bits = extract_chars_by_index(random_picked_positions, sifted_client_key)
    
    qber = 100 * qkd.QBER(sifted_server_key, sifted_client_key)
    qber_practical = 100 * qkd.QBER(server_random_picked_bits, client_random_picked_bits)

    current_time = time.time()
    status = "ABORTED" if qber > 11.0 else "KEY_GENERATED"

    session_data = {
        "session_id" : session_id,
        "voter_id": payload.voter_id,
        "key_generated": key_generated,
        "selected_bits": random_picked_positions,
        "alice_bit": simulation_result["server_key"],
        "alice_basis": simulation_result["server_encryption_basis"],
        "bob_read": simulation_result["client_key"],
        "bob_basis": simulation_result["client_decryption_basis"],
        "eve_read": "",
        "eve_basis": "",
        "error_found": 0,
        "qber_practical": qber_practical,
        "qber_system": qber,
        "threshold_percent": 11.0,
        "status": status,
        "timestamp": current_time
    }

    await election.update({"$push": {"sessions": VotingSession(**session_data).model_dump()}})

    return GenerateKeyRespond(
        elction_code= payload.election_code,
        voter_id= payload.voter_id,
        session_id= session_id,
        key_generated= key_generated,
        alice_bit = simulation_result["server_key"],
        alice_basis = simulation_result["server_encryption_basis"],
        bob_read = simulation_result["client_key"],
        bob_basis = simulation_result["client_decryption_basis"],
        test_sample = 0,
        error_found = 0,
        qber_percent = qber,
        threshold_percent = 11
    )

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

    encrypted_vote = payload.encrypted_vote    
    key_bit = target_session.key_generated[:len(encrypted_vote)] 

    res_binary = bin(int(encrypted_vote, 2) ^ int(key_bit, 2))
    voted_candidate_index = int(res_binary, 2)
    current_time = time.time()

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
    return CastBallotRespond(
        session_id= payload.session_id,
        voter_id = payload.voter_id,
        encrypted_vote = payload.encrypted_vote,
        created_at = current_time,
        updated_time = current_time    
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

async def get_election_results(election_code: str):
    election = await ElectionSchema.find_one(ElectionSchema.election_code == election_code)

    if not election:
        raise HTTPException(
            status_code=404, 
            detail=f"Election with code '{election_code}' not found"
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

async def get_voting_logs(election_code: str):
    election = await ElectionSchema.find_one(ElectionSchema.election_code == election_code)

    if not election:
        raise HTTPException(
            status_code=404, 
            detail=f"Election with code '{election_code}' not found"
        )

    logs = [
        VotingLogItem(
            session_id=s.session_id,
            voter_id=s.voter_id,
            encrypted_vote=s.encrypted_vote or "",
            key_generated=s.key_generated,
            alice_bit=s.alice_bit or "",
            alice_basis=s.alice_basis or "",
            bob_read=s.bob_read or "",
            bob_basis=s.bob_basis or "",
            qber_percent=s.qber_percent or 0.0,
            threshold_percent=s.threshold_percent or 11.0,
            status=s.status or ("VOTE_CAST" if s.encrypted_vote else "KEY_GENERATED"),
            timestamp=s.timestamp or 0.0,
        )
        for s in election.sessions
    ]

    return VotingLogResponse(election_code=election_code, logs=logs)

def calculate_key_length(error_tolerance, key_bits):
    return math.ceil((4 + error_tolerance ) * key_bits)

def get_unique_random_indices(max_value, count):
        
    return random.sample(range(0, max_value), count)

def extract_chars_by_index(indices, text):

    extracted_chars = [text[i] for i in indices if i < len(text)]
    
    return "".join(extracted_chars)