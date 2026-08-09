from fastapi import APIRouter, status, HTTPException
from .models import GenerateKeyInput, GenerateKeyRespond, CastBallotInput
from . import service

router = APIRouter(prefix="/vote")

@router.post("/generate-key", status_code=status.HTTP_200_OK)
async def generate_key(payload: GenerateKeyInput):
    
    return await service.create_qkd_key(payload)

@router.post("/cast-ballot", status_code=status.HTTP_201_CREATED)
async def cast_ballot(payload: CastBallotInput):
    return await service.cast_ballot(payload)


@router.get("/election-results/{election_code}", status_code=200)
async def election_result(election_code: str):
    return await service.get_election_results(election_code)