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
    qber_percent: float
    threshold_percent: int

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

class CastBallotRespond(CamelModel):
    session_id: str
    voter_id: str
    encrypted_vote: str
    created_at: float
    updated_time: float

class CandidateData(CamelModel):
    candidate_name: str
    candidate_party: str

class CandidateRespond(CamelModel):
    candidates: list[CandidateData]

class VotingLogItem(CamelModel):
    session_id: str
    voter_id: str
    encrypted_vote: Optional[str] = ""
    key_generated: str
    alice_bit: str
    alice_basis: str
    bob_read: str
    bob_basis: str
    qber_percent: float
    threshold_percent: float
    status: str
    timestamp: float

class VotingLogResponse(CamelModel):
    election_code: str
    logs: list[VotingLogItem]

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
    alice_bit: Optional[str] = ""
    alice_basis: Optional[str] = ""
    bob_read: Optional[str] = ""
    bob_basis: Optional[str] = ""
    qber_percent: Optional[float] = 0.0
    threshold_percent: Optional[float] = 11.0
    status: Optional[str] = "KEY_GENERATED"
    timestamp: float

class ElectionSchema(Document):
    candidates: list[Candidate]
    sessions: list[VotingSession]
    election_code: str

    class Settings:
        name = "elections"
