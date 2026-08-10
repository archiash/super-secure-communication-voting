import type { ApiService } from './api';
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
  TransmissionLogEntry,
  Basis,
  PhotonSymbol,
  VoteRecord,
  VoteOption,
} from '../types';
import { generateSessionId } from '../utils/session';

/** Valid demo election code */
const DEMO_ELECTION_CODE = 'ELECT2026';

/** Default candidates for the demo election */
const DEFAULT_OPTIONS: VoteOption[] = [
  { id: 'candidate-a', name: 'Sierra', party: 'Ashleigh_Emmerich', binaryId: '000', count: 27 },
  { id: 'candidate-b', name: 'Raul', party: 'Guiseppe_Waters', binaryId: '001', count: 32 },
  { id: 'candidate-c', name: 'Gabrielle', party: 'Daren81', binaryId: '010', count: 41 },
  { id: 'candidate-d', name: 'Alan', party: 'Willmax_Robinson', binaryId: '011', count: 41 },
];

/**
 * Mock API service that simulates BB84 QKD protocol locally.
 * No real quantum hardware involved — all randomness is classical.
 */
export class MockApiService implements ApiService {
  private votes: VoteRecord[] = [];
  private options: VoteOption[] = JSON.parse(JSON.stringify(DEFAULT_OPTIONS));

  async verifyAuth(request: AuthRequest): Promise<AuthResponse> {
    // Simulate network delay
    await this.delay(300);

    if (!request.voterId.trim()) {
      return { valid: false, sessionId: '', error: 'Voter ID is required.' };
    }
    if (request.electionCode !== DEMO_ELECTION_CODE) {
      return { valid: false, sessionId: '', error: 'Invalid election code.' };
    }

    // Check if this voter already voted
    const alreadyVoted = this.votes.some((v) => v.voterId === request.voterId);
    if (alreadyVoted) {
      return { valid: false, sessionId: '', error: 'This Voter ID has already cast a vote.' };
    }

    return {
      valid: true,
      sessionId: generateSessionId(),
    };
  }

  async generateKey(_voterId: string, _electionCode: string, config: ProtocolConfig): Promise<QKDResponse> {
    await this.delay(200);
    const sessionId = generateSessionId();

    // --- Phase 1: Transmission ---
    const log = this.simulateTransmission(config.qubitCount, config.eveSimulation);

    // --- Phase 2: Basis Sifting ---
    const keptEntries = log.filter((e) => e.keep);
    const siftedKeyBits = keptEntries.map((e) => e.bobRead);

    // --- Phase 3: QBER Estimation ---
    const testBitCount = Math.min(config.testBitCount, siftedKeyBits.length);
    // Use the first N sifted bits as test bits
    const aliceTestBits = keptEntries.slice(0, testBitCount).map((e) => e.aliceBit);
    const bobTestBits = siftedKeyBits.slice(0, testBitCount);

    let errorsFound = 0;
    for (let i = 0; i < testBitCount; i++) {
      if (aliceTestBits[i] !== bobTestBits[i]) {
        errorsFound++;
      }
    }
    const qber = testBitCount > 0 ? errorsFound / testBitCount : 0;
    // this funtion is use to force the QBER to be clearly above threshold so Eve is reliably detected every run.
    //let qber = testBitCount > 0 ? errorsFound / testBitCount : 0;

    // When Eve is simulated, she ALWAYS causes a detectable disturbance (≥25% QBER).
    // If the random sampling didn't catch enough errors, we force the QBER to be
    // clearly above threshold so Eve is reliably detected every run.
    //if (config.eveSimulation && qber <= config.errorThreshold) {
    // Target a QBER that is visibly above threshold (e.g. 25%)
    //const targetQber = Math.max(0.25, config.errorThreshold + 0.1);
    //errorsFound = Math.ceil(targetQber * testBitCount);
    //qber = testBitCount > 0 ? errorsFound / testBitCount : targetQber;
    //}

    const passed = qber <= config.errorThreshold;

    // Remove test bits from the key
    const remainingBits = siftedKeyBits.slice(testBitCount);

    // --- Phase 4: Error Correction ---
    let correctedBits = 0;
    const correctedKey = [...remainingBits];
    if (config.errorCorrectionEnabled && passed) {
      // Simple simulation: if there are errors, "correct" them
      const originalAliceBits = keptEntries.slice(testBitCount).map((e) => e.aliceBit);
      for (let i = 0; i < correctedKey.length; i++) {
        if (correctedKey[i] !== originalAliceBits[i]) {
          correctedKey[i] = originalAliceBits[i];
          correctedBits++;
        }
      }
    }

    // --- Phase 5: Key Established ---
    // Truncate to target key length
    const finalKeyBits = correctedKey.slice(0, config.targetKeyLength);
    const finalKey = finalKeyBits.join('');

    // --- Eve data ---
    let eveData = undefined;
    if (config.eveSimulation) {
      const eveBasis = log.map(() => this.randomBasis()).join('');
      const eveReadBits = log.map(() => this.randomBit().toString()).join('');
      eveData = {
        eveBasis,
        eveReadBits,
        interceptedCount: config.qubitCount,
        detectable: qber > config.errorThreshold,
      };
    }

    const result: QKDResponse = {
      sessionId,
      phases: {
        transmission: {
          qubitCount: config.qubitCount,
          log,
        },
        basisSifting: {
          matchingBases: keptEntries.length,
          siftedKeyBits: siftedKeyBits as (0 | 1)[],
        },
        qberEstimation: {
          testBitsUsed: testBitCount,
          errorsFound,
          qber,
          passed,
        },
        errorCorrection: {
          applied: config.errorCorrectionEnabled && passed,
          correctedBits,
          method: config.errorCorrectionEnabled ? 'cascade' : 'none',
        },
        keyEstablished: {
          finalKey,
          keyLength: finalKey.length,
        },
      },
      eveData,
    };
    console.log('[MockApiService] generateKey result:', result);
    return result;
  }

  async castVote(_request: CastVoteRequest): Promise<CastVoteResponse> {
    await this.delay(200);

    const voteId = `VOTE-${Date.now().toString(36).toUpperCase()}`;
    const timestamp = new Date().toISOString();

    return {
      success: true,
      voteId,
      timestamp,
    };
  }

  /**
   * Store a full vote record (called by the frontend after casting).
   * This is a mock-only method to accumulate demo results.
   */
  storeVoteRecord(record: VoteRecord): void {
    this.votes.push(record);
    const option = this.options.find((o) => o.id === record.plaintextVote);
    if (option) {
      option.count++;
    }
  }

  async getCandidates(_electionCode: string): Promise<CandidatesResponse> {
    await this.delay(100);
    return {
      candidates: this.options.map(o => ({
        candidateName: o.name,
        candidateParty: o.party,
        binaryId: o.binaryId,
      })),
    };
  }

  async getElectionResult(_electionCode: string): Promise<ElectionResultResponse> {
    await this.delay(100);
    return {
      candidates: this.options.map(o => ({
        candidateName: o.name,
        candidateParty: o.party,
        votes: o.count
      }))
    };
  }

  async getVotingAudit(_electionCode: string): Promise<VotingAuditResponse> {
    await this.delay(100);

    if (this.votes.length === 0) {
      return {
        sessions: [
          {
            sessionId: "sess_x8j9F3nL",
            voterId: "voter_8491",
            encryptedVote: "101",
            keyBits: "101",
            timeStamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString()
          },
          {
            sessionId: "sess_k2L9mX4b",
            voterId: "voter_1120",
            encryptedVote: "010",
            keyBits: "001",
            timeStamp: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString()
          },
          {
            sessionId: "sess_p9q4Nv7R",
            voterId: "voter_6382",
            encryptedVote: "000",
            keyBits: "010",
            timeStamp: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString()
          }
        ]
      };
    }

    return {
      sessions: this.votes.map(v => ({
        sessionId: v.protocolReplay.sessionId,
        voterId: v.voterId,
        encryptedVote: v.encryptedVote,
        keyBits: v.otpKey,
        timeStamp: v.timestamp
      }))
    };
  }

  async resetVotes(): Promise<void> {
    this.votes = [];
    this.options = JSON.parse(JSON.stringify(DEFAULT_OPTIONS));
  }

  // ── Private simulation helpers ──

  private simulateTransmission(
    qubitCount: number,
    evePresent: boolean
  ): TransmissionLogEntry[] {
    const log: TransmissionLogEntry[] = [];

    for (let i = 0; i < qubitCount; i++) {
      const aliceBit = this.randomBit();
      const aliceBasis = this.randomBasis();
      const bobBasis = this.randomBasis();

      // Determine what Bob reads
      let bobRead: 0 | 1;
      if (evePresent) {
        // Eve intercepts with a random basis, potentially disturbing the qubit
        const eveBasis = this.randomBasis();
        if (eveBasis === aliceBasis) {
          // Eve measures correctly, qubit undisturbed for Eve's part
          if (bobBasis === aliceBasis) {
            bobRead = aliceBit; // Both bases match, Bob gets correct bit
          } else {
            bobRead = this.randomBit(); // Bob uses wrong basis, random result
          }
        } else {
          // Eve uses wrong basis, qubit is disturbed
          if (bobBasis === aliceBasis) {
            // Bob uses right basis but qubit was disturbed by Eve
            // 50% chance of correct, 50% chance of error
            bobRead = Math.random() < 0.5 ? aliceBit : ((1 - aliceBit) as 0 | 1);
          } else {
            bobRead = this.randomBit(); // Both wrong, fully random
          }
        }
      } else {
        // No Eve — standard BB84
        if (bobBasis === aliceBasis) {
          bobRead = aliceBit; // Same basis → Bob reads Alice's bit correctly
        } else {
          bobRead = this.randomBit(); // Different basis → random result
        }
      }

      const keep = aliceBasis === bobBasis;
      const photonSymbol = this.getPhotonSymbol(aliceBit, aliceBasis);

      log.push({
        index: i + 1,
        aliceBit,
        aliceBasis,
        photonSymbol,
        bobBasis,
        bobRead,
        keep,
      });
    }

    return log;
  }

  /**
   * Get the photon polarization symbol based on bit value and basis.
   * Matches the Figma design's arrow symbols:
   * - Rectilinear (×): 0 → ↗ (45° up-right), 1 → ↘ (45° down-right)
   *   Wait — looking at the Figma more carefully:
   *   × basis with bit 0 → ↗, × basis with bit 1 → ↘
   * - Diagonal (+): 0 → ↑ (vertical), 1 → → (horizontal)
   */
  private getPhotonSymbol(bit: 0 | 1, basis: Basis): PhotonSymbol {
    if (basis === '×') {
      return bit === 0 ? '↗' : '↘';
    } else {
      return bit === 0 ? '↑' : '→';
    }
  }

  private randomBit(): 0 | 1 {
    return Math.random() < 0.5 ? 0 : 1;
  }

  private randomBasis(): Basis {
    return Math.random() < 0.5 ? '×' : '+';
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
