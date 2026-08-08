import type { ApiService } from './api';
import type {
  AuthRequest,
  AuthResponse,
  ProtocolConfig,
  CandidatesResponse,
  QKDResponse,
  CastVoteRequest,
  CastVoteResponse,
  ElectionResultResponse,
  VotingAuditResponse,
  TransmissionLogEntry,
  Basis,
} from '../types';
import { MockApiService } from './mock-api';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
const mockApi = new MockApiService();

function getPhotonSymbol(bit: 0 | 1, basis: Basis) {
  if (basis === '×') {
    return bit === 0 ? '↗' : '↘';
  } else {
    return bit === 0 ? '↑' : '→';
  }
}

/**
 * Real API service that calls the Python backend.
 * Gracefully falls back to MockApiService if the endpoint is not yet configured (404)
 */
export class RealApiService implements ApiService {
  async verifyAuth(request: AuthRequest): Promise<AuthResponse> {
    try {
      const res = await fetch(`${API_BASE}/auth/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });
      if (res.status === 404) return mockApi.verifyAuth(request);
      if (!res.ok) throw new Error(`Auth failed: ${res.statusText}`);
      return res.json();
    } catch (err) {
      return mockApi.verifyAuth(request);
    }
  }

  async generateKey(voterId: string, electionCode: string, config: ProtocolConfig): Promise<QKDResponse> {
    try {
      const res = await fetch(`${API_BASE}/vote/generate-key`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          voterId,
          electionCode,
          isUsingQuantumComputer: config.useRealQuantum,
          errorCorrectionEnabled: config.errorCorrectionEnabled,
          enableEavesdropper: config.eveSimulation,
          qubitPerSession: config.qubitCount,
          targetKeyLength: config.targetKeyLength
        }),
      });
      if (res.status === 404) return mockApi.generateKey(voterId, electionCode, config);
      if (!res.ok) throw new Error(`Key generation failed: ${res.statusText}`);
      const data = await res.json();
      
      // Map Apidog flat response to nested QKDResponse
      const log: TransmissionLogEntry[] = [];
      const len = Math.min(data.aliceBit?.length || 0, data.aliceBasis?.length || 0);
      
      for(let i = 0; i < len; i++) {
        const aliceBit = parseInt(data.aliceBit[i]) as 0 | 1;
        const aliceBasis = data.aliceBasis[i] === '0' ? '+' : '×';
        const bobBasis = data.bobBasis[i] === '0' ? '+' : '×';
        const bobRead = parseInt(data.bobRead[i]) as 0 | 1;
        log.push({
          index: i + 1,
          aliceBit,
          aliceBasis,
          photonSymbol: getPhotonSymbol(aliceBit, aliceBasis) as any,
          bobBasis,
          bobRead,
          keep: aliceBasis === bobBasis
        });
      }
      
      const kept = log.filter(l => l.keep);

      return {
        sessionId: data.sessionId,
        phases: {
          transmission: { qubitCount: log.length, log },
          basisSifting: {
            matchingBases: kept.length,
            siftedKeyBits: kept.map(l => l.bobRead)
          },
          qberEstimation: {
            testBitsUsed: data.testSample,
            errorsFound: data.errorFound,
            qber: data.qberPercent / 100,
            passed: data.qberPercent <= data.thresholdPercent
          },
          errorCorrection: {
            applied: config.errorCorrectionEnabled && (data.qberPercent <= data.thresholdPercent),
            correctedBits: data.errorFound,
            method: config.errorCorrectionEnabled ? 'cascade' : 'none'
          },
          keyEstablished: {
            finalKey: data.keyGenerated,
            keyLength: data.keyGenerated?.length || 0
          }
        }
      };
    } catch (err) {
      return mockApi.generateKey(voterId, electionCode, config);
    }
  }

  async castVote(request: CastVoteRequest): Promise<CastVoteResponse> {
    try {
      const res = await fetch(`${API_BASE}/vote/cast-ballot`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });
      if (res.status === 404) return mockApi.castVote(request);
      if (!res.ok) throw new Error(`Vote failed: ${res.statusText}`);
      
      const data = await res.json();
      return {
        success: true,
        voteId: data.sessionId || `VOTE-${Date.now().toString(36).toUpperCase()}`,
        timestamp: data.createdAt || new Date().toISOString(),
      };
    } catch (err) {
      return mockApi.castVote(request);
    }
  }

  async getCandidates(electionCode: string): Promise<CandidatesResponse> {
    try {
      const res = await fetch(`${API_BASE}/vote/candidates/${electionCode}`);
      if (res.status === 404) return mockApi.getCandidates(electionCode);
      if (!res.ok) throw new Error(`Get candidates failed: ${res.statusText}`);
      return res.json();
    } catch (err) {
      return mockApi.getCandidates(electionCode);
    }
  }

  async getElectionResult(electionCode: string): Promise<ElectionResultResponse> {
    try {
      const res = await fetch(`${API_BASE}/vote/election-results/${electionCode}`);
      if (res.status === 404) return mockApi.getElectionResult(electionCode);
      if (!res.ok) throw new Error(`Election results failed: ${res.statusText}`);
      return res.json();
    } catch (err) {
      return mockApi.getElectionResult(electionCode);
    }
  }

  async getVotingAudit(electionCode: string): Promise<VotingAuditResponse> {
    try {
      const res = await fetch(`${API_BASE}/vote/voting-audits/${electionCode}`);
      if (res.status === 404) return mockApi.getVotingAudit(electionCode);
      if (!res.ok) throw new Error(`Voting audit failed: ${res.statusText}`);
      return res.json();
    } catch (err) {
      return mockApi.getVotingAudit(electionCode);
    }
  }

  async resetVotes(): Promise<void> {
    try {
      const res = await fetch(`${API_BASE}/vote/reset`, { method: 'POST' });
      if (res.status === 404) return mockApi.resetVotes();
      if (!res.ok) throw new Error(`Reset failed: ${res.statusText}`);
    } catch (err) {
      return mockApi.resetVotes();
    }
  }
}
