/**
 * API request/response types for authentication.
 */

/** POST /api/auth/verify */
export interface AuthRequest {
  /** e.g., "V-2026-001234" */
  voterId: string;
  /** e.g., "ELECT2026" */
  electionCode: string;
}

export interface AuthResponse {
  valid: boolean;
  /** Unique session identifier, e.g., "QS-EJPCF84N" */
  sessionId: string;
  error?: string;
}

export interface CandidatesData {
  candidateName: string;
  candidateParty: string;
  binaryId: string;
}

export interface CandidatesResponse {
  candidates: CandidatesData[];
}

export interface VotingCandidate {
  candidateName: string;
  candidateParty: string;
  votes: number;
}

export interface ElectionResultResponse {
  candidates: VotingCandidate[];
}

export interface SessionData {
  sessionId: string;
  voterId: string;
  encryptedVote: string;
  keyBits: string;
  timeStamp: string;
}

export interface VotingAuditResponse {
  sessions: SessionData[];
}
