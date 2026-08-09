from fastapi import HTTPException
from .models import GenerateKeyRespond, GenerateKeyInput, ElectionResultResponse, ElectionSchema, CandidateVotingResult, VotingSession, CastBallotInput
from . import qkd
import secrets
import string
import time

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

    simulation_result = qkd.simulate_bb84_protocal(key_size= payload.target_key_length, per_time_bits= payload.qubit_per_session, has_eavesdropping= payload.enable_eavesdropper, use_ibm= payload.is_using_quantum_computer)
    session_id = generate_session_id()
    key_generated = qkd.sifting(simulation_result["server_key"], simulation_result["server_encryption_basis"], simulation_result["client_decryption_basis"])

    session_data = {
        "session_id" : session_id,
        "voter_id": payload.voter_id,
        "encrytped_vote": "",
        "key_generated": key_generated,
        "timestamp": 0.0
    }

    await election.update({"$push": {"sessions": VotingSession(**session_data).model_dump()}})

    return {
        "election_code": payload.election_code,
        "session_id" : session_id,
        "key_generated": key_generated,
        "alice_bit": simulation_result["server_key"],
        "alice_basis": simulation_result["server_encryption_basis"],
        "bob_read": simulation_result["client_decryption_basis"],
        "bob_basis": simulation_result["client_key"],
        "test_sample": 0,
        "error_found": 0,
        "qber_percent": 0,
        "threshold_percent": 11
    }

async def cast_ballot(payload: CastBallotInput):
    # 1. Fetch the document just to validate it exists and extract the key
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

    # 2. THE FIX: Chain the update directly to the find_one query
    # This forces MongoDB to remember the array match for the '$' operator
    await ElectionSchema.find_one(
        ElectionSchema.sessions.session_id == payload.session_id
    ).update({
        "$inc": {
            f"candidates.{voted_candidate_index}.vote": 1
        },
        "$set": {
            # Note: I changed target_session.voter_id to payload.voter_id
            # so it actually saves the incoming voter ID instead of the old one!
            "sessions.$.voter_id": payload.voter_id, 
            "sessions.$.encrypted_vote": payload.encrypted_vote,
            "sessions.$.timestamp": current_time
        }
    })

    return {
        "session_id": payload.session_id,
        "voter_id": payload.voter_id,
        "encrypted_vote": payload.encrypted_vote,
        "created_at": current_time,
        "updated_time": current_time
    }

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
