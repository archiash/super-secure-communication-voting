from fastapi import HTTPException
from .models import GenerateKeyRespond, GenerateKeyInput, ElectionResultResponse, ElectionSchema, CandidateVotingResult
from . import qkd

async def create_qkd_key(payload : GenerateKeyInput) -> dict:
    # key_size = 64, per_time_bit = 64, has_eavesdropping = False, use_ibm: bool = USE_IBM_QUANTUM)
    return qkd.simulate_bb84_protocal(key_size= payload.target_key_length, per_time_bits= payload.qubit_per_session, has_eavesdropping= payload.enable_eavesdropper, use_ibm= payload.is_using_quantum_computer)

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
