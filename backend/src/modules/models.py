from beanie import Document
from typing import Optional
from core.schemas import CamelModel 
from pydantic import BaseModel

class GenerateKeyInput(CamelModel):
    voter_id: str
    election_code: str
    is_using_quantum_computer: bool
    error_correction_enabled: bool
    enable_eavesdropper: bool
    qubit_per_session: int
    target_key_length: int

class GenerateKeyRespond(CamelModel):
    voter_id: str
    elction_code: str
    session_id: str
    key_generated: str
    alice_bit: str
    alice_basis: str
    bob_read: str
    bob_basis: str
    test_sample: int
    qber_percent: int
    thresholdPercent: int

class CandidateVotingResult(CamelModel):
    candidate_name: str
    candidate_party: str
    votes: int

class ElectionResultResponse(CamelModel):
    candidates: list[CandidateVotingResult]

class CastBallotInput(CamelModel):
    session_id: str
    voter_id: str
    encrypted_vote: str

# MongoDB Schema Below
class Candidate(BaseModel):
    candidate_name: str
    candidate_party: str
    votes: int

class VotingSession(BaseModel):
    session_id: str
    voter_id: str
    encrypted_vote: Optional[str] = None 
    key_generated: str
    timestamp: float

class ElectionSchema(Document):
    candidates: list[Candidate]
    sessions: list[VotingSession]
    election_code: str

    class Settings:
        name = "elections"