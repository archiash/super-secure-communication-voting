import type { QKDResponse } from './qkd';

/**
 * Voting domain types.
 */

/** A candidate/option in the election */
export interface VoteOption {
  id: string;
  name: string;
  party: string;
  binaryId: string;
  count: number;
}

/** Record of a single cast vote */
export interface VoteRecord {
  voteId: string;
  voterId: string;
  timestamp: string;
  /** Full QKD protocol replay data for drilling into this vote */
  protocolReplay: QKDResponse;
  /** The encrypted vote (OTP ciphertext) */
  encryptedVote: string;
  /** The plaintext vote option ID — only exposed in demo mode */
  plaintextVote: string;
  /** The OTP key used for encryption */
  otpKey: string;
}

/** Request to cast a vote */
export interface CastVoteRequest {
  sessionId: string;
  voterId: string;
  /** The vote XOR'd with the OTP key */
  encryptedVote: string;
}

/** Response after casting a vote */
export interface CastVoteResponse {
  success: boolean;
  voteId: string;
  timestamp: string;
  error?: string;
}

/** Full election results */
export interface VoteResultsResponse {
  electionCode: string;
  totalVotes: number;
  options: VoteOption[];
  votes: VoteRecord[];
}
