from fastapi import HTTPException
from .models import GenerateKeyRespond, GenerateKeyInput, ElectionResultResponse, ElectionSchema, CandidateVotingResult

async def create_qkd_key(payload : GenerateKeyInput) -> dict:
    return {"key": "generated_key_value", "status": "success"}

async def get_election_results(election_code: str) -> ElectionResultResponse:
    election = await ElectionSchema.find_one(ElectionSchema.election_code == election_code)
    # all_docs = ElectionSchema.find_all().to_list()

    # for e in all_docs: 
    #     print(e.election_code)

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