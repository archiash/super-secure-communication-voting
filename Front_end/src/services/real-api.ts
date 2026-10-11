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
  VotingLogResponse,
  TransmissionLogEntry,
  Basis,
} from '../types';
import { MockApiService } from './mock-api';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8888';
const mockApi = new MockApiService();

function getPhotonSymbol(bit: 0 | 1, basis: Basis) {
  if (basis === '×') {
    return bit === 0 ? '↗' : '↘';
  } else {
    return bit === 0 ? '↑' : '→';
  }
}

/**
 * Real API service that calls the Python backend at localhost:8001.
 * Falls back to MockApiService if the endpoint returns 404 or errors.
 */
export class RealApiService implements ApiService {
  async verifyAuth(request: AuthRequest): Promise<AuthResponse> {
    // Auth is handled by the mock — the real backend does not have a /auth endpoint
    const result = await mockApi.verifyAuth(request);
    console.log('[API Call] verifyAuth result:', result);
    return result;
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
          targetKeyLength: config.targetKeyLength,
          errorTolerance: config.errorTolerance,
        }),
      });
      if (!res.ok) throw new Error(`Key generation failed: ${res.statusText}`);
      const data = await res.json();
      console.log('[API Call] generateKey response from backend:', data);

      // Map flat response to nested QKDResponse
      const log: TransmissionLogEntry[] = [];
      const len = Math.min(data.aliceBit?.length || 0, data.aliceBasis?.length || 0);

      for (let i = 0; i < len; i++) {
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
          keep: aliceBasis === bobBasis,
        });
      }

      const kept = log.filter((l) => l.keep);

      const result: QKDResponse = {
        sessionId: data.sessionId,
        phases: {
          transmission: { qubitCount: log.length, log },
          basisSifting: {
            matchingBases: kept.length,
            siftedKeyBits: kept.map((l) => l.bobRead),
          },
          qberEstimation: {
            testBitsUsed: data.testSample,
            errorsFound: data.errorFound,
            qber: data.qberPercent / 100,
            passed: data.qberPercent <= data.thresholdPercent,
          },
          errorCorrection: {
            applied: config.errorCorrectionEnabled && data.qberPercent <= data.thresholdPercent,
            correctedBits: data.errorFound,
            method: config.errorCorrectionEnabled ? 'cascade' : 'none',
          },
          keyEstablished: {
            finalKey: data.keyGenerated,
            keyLength: data.keyGenerated?.length || 0,
          },
        },
      };
      console.log('[API Call] generateKey mapped result:', result);
      return result;
    } catch (err) {
      console.warn('[RealApiService] generateKey failed:', err);
      throw err;
    }
  }

  async castVote(request: CastVoteRequest): Promise<CastVoteResponse> {
    try {
      const res = await fetch(`${API_BASE}/vote/cast-ballot`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });
      if (!res.ok) throw new Error(`Vote failed: ${res.statusText}`);

      const data = await res.json();
      console.log('[API Call] castVote response from backend:', data);
      const result: CastVoteResponse = {
        success: true,
        voteId: data.sessionId || `VOTE-${Date.now().toString(36).toUpperCase()}`,
        timestamp: data.createdAt || new Date().toISOString(),
      };
      console.log('[API Call] castVote result:', result);
      return result;
    } catch (err) {
      console.warn('[RealApiService] castVote failed:', err);
      throw err;
    }
  }

  async getCandidates(electionCode: string): Promise<CandidatesResponse> {
    try {
      const res = await fetch(`${API_BASE}/vote/candidates/${electionCode}`);
      if (!res.ok) throw new Error(`Get candidates failed: ${res.statusText}`);
      const data = await res.json();
      console.log('[API Call] getCandidates result:', data);
      return data;
    } catch (err) {
      console.warn('[RealApiService] getCandidates failed:', err);
      throw err;
    }
  }

  async getElectionResult(electionCode: string): Promise<ElectionResultResponse> {
    try {
      const res = await fetch(`${API_BASE}/vote/election-results/${electionCode}`);
      if (!res.ok) throw new Error(`Election results failed: ${res.statusText}`);
      const data = await res.json();
      console.log('[API Call] getElectionResult result:', data);
      return data;
    } catch (err) {
      console.warn('[RealApiService] getElectionResult failed:', err);
      throw err;
    }
  }

  async getVotingAudit(electionCode: string): Promise<VotingAuditResponse> {
    try {
      const res = await fetch(`${API_BASE}/vote/logs/${electionCode}`);
      if (!res.ok) throw new Error(`Voting audit failed: ${res.statusText}`);
      const data = await res.json();
      console.log('[API Call] getVotingAudit result:', data);
      
      // Map the backend's `logs` array to the `sessions` array expected by ResultsPage
      return {
        sessions: (data.logs || []).map((log: any) => ({
          sessionId: log.sessionId,
          voterId: log.voterId,
          encryptedVote: log.encryptedVote || '',
          keyBits: log.keyGenerated || '',
          timeStamp: log.timestamp || log.createdAt
        }))
      };
    } catch (err) {
      console.warn('[RealApiService] getVotingAudit failed:', err);
      throw err;
    }
  }

  async getVotingLogs(electionCode: string): Promise<VotingLogResponse> {
    try {
      const res = await fetch(`${API_BASE}/vote/logs/${electionCode}`);
      if (!res.ok) throw new Error(`Voting audit failed: ${res.status} ${res.statusText}`);
      const data = await res.json();
      console.log('[API Call] getVotingLogs (audit) result:', data);
      
      // Map the backend's `logs` array to the `sessions` array expected by VotingLogsPage
      return {
        sessions: (data.logs || []).map((log: any) => ({
          ...log,
          createdAt: log.timestamp || log.createdAt,
          updatedAt: log.timestamp || log.updatedAt,
        }))
      };
    } catch (err) {
      console.warn('[RealApiService] getVotingLogs failed:', err);
      throw err;
    }
  }

  async resetVotes(): Promise<void> {
    try {
      const res = await fetch(`${API_BASE}/vote/reset`, { method: 'POST' });
      if (!res.ok) throw new Error(`Reset failed: ${res.statusText}`);
      console.log('[API Call] resetVotes result: success');
    } catch (err) {
      console.warn('[RealApiService] resetVotes failed:', err);
      throw err;
    }
  }
}
