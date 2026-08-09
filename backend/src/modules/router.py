from fastapi import APIRouter, status, HTTPException
from .models import GenerateKeyInput, GenerateKeyRespond
from . import service

router = APIRouter(prefix="/vote")

@router.post("/generate-key", response_model=GenerateKeyRespond, status_code=status.HTTP_200_OK)
async def generate_key(payload: GenerateKeyInput):
    
    return await service.create_qkd_key()

@router.post("/cast-ballot", status_code=status.HTTP_201_CREATED)
async def cast_ballot():
    try:
        return None
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/election-results/{election_code}", status_code=200)
async def election_result(election_code: str):
    return await service.get_election_results(election_code)