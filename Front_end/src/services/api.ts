import type {
  AuthRequest,
  AuthResponse,
  ProtocolConfig,
  QKDResponse,
  CastVoteRequest,
  CastVoteResponse,
  CandidatesResponse,
  ElectionResultResponse,
  VotingAuditResponse,
} from '../types';

/**
 * API service interface.
 * MockApiService and RealApiService both implement this.
 * Swap between them via the VITE_USE_REAL_API env variable.
 */
export interface ApiService {
  /** Verify voter credentials */
  verifyAuth(request: AuthRequest): Promise<AuthResponse>;

  /** Generate a QKD shared key using BB84 protocol */
  generateKey(voterId: string, electionCode: string, config: ProtocolConfig): Promise<QKDResponse>;

  /** Cast an encrypted vote */
  castVote(request: CastVoteRequest): Promise<CastVoteResponse>;

  /** Get election results */
  getElectionResult(electionCode: string): Promise<ElectionResultResponse>;

  /** Get candidates */
  getCandidates(electionCode: string): Promise<CandidatesResponse>;

  /** Get quantum audit log */
  getVotingAudit(electionCode: string): Promise<VotingAuditResponse>;

  /** Reset all votes (for demo purposes) */
  resetVotes(): Promise<void>;
}
