/**
 * Types for the BB84 Quantum Key Distribution protocol.
 * Maps directly to the Key Generation page UI:
 * - TransmissionLogEntry → rows in the QUBIT TRANSMISSION LOG table
 * - QKD phases → sub-stepper stages (Transmission → Basis Sifting → QBER → Error Correction → Key Established)
 */

/** Measurement basis: × = rectilinear, + = diagonal */
export type Basis = '×' | '+';

/** Photon polarization symbol shown in the Transmission Log */
export type PhotonSymbol = '↗' | '↘' | '↑' | '→';

/**
 * A single row in the QUBIT TRANSMISSION LOG table.
 * Columns: #, Alice Bit, Alice Basis, Photon, Bob Basis, Bob Read, Keep
 */
export interface TransmissionLogEntry {
  index: number;
  aliceBit: 0 | 1;
  aliceBasis: Basis;
  photonSymbol: PhotonSymbol;
  bobBasis: Basis;
  bobRead: 0 | 1;
  /** true when Alice's basis matches Bob's basis */
  keep: boolean;
}

/** Result of the Transmission phase (sub-step 1) */
export interface TransmissionResult {
  qubitCount: number;
  log: TransmissionLogEntry[];
}

/** Result of the Basis Sifting phase (sub-step 2) */
export interface SiftingResult {
  /** Number of qubits where Alice and Bob used the same basis */
  matchingBases: number;
  /** The sifted key bits (only kept bits) */
  siftedKeyBits: (0 | 1)[];
}

/** Result of QBER Estimation phase (sub-step 3) */
export interface QBERResult {
  /** Number of test bits sacrificed for estimation */
  testBitsUsed: number;
  /** Number of errors found in the test bits */
  errorsFound: number;
  /** Calculated QBER (0.0 to 1.0) */
  qber: number;
  /** Whether the QBER is below the error threshold (key accepted) */
  passed: boolean;
}

/** Result of Error Correction phase (sub-step 4) */
export interface ErrorCorrectionResult {
  /** Whether error correction was applied */
  applied: boolean;
  /** Number of bits corrected */
  correctedBits: number;
  /** Method used */
  method: 'cascade' | 'none';
}

/** Result of Key Established phase (sub-step 5) */
export interface KeyResult {
  /** The final shared secret key as a bit string. e.g., "10110010" */
  finalKey: string;
  /** Length of the final key in bits */
  keyLength: number;
}

/** Eve's interception data (only present when eveSimulation is enabled) */
export interface EveResult {
  /** Eve's randomly chosen measurement bases */
  eveBasis: string;
  /** Eve's measurement results */
  eveReadBits: string;
  /** Number of qubits Eve intercepted */
  interceptedCount: number;
  /** Whether Eve's presence is detectable via elevated QBER */
  detectable: boolean;
}

/** The 5 sub-step phases of Key Generation */
export type QKDPhase =
  | 'transmission'
  | 'basisSifting'
  | 'qberEstimation'
  | 'errorCorrection'
  | 'keyEstablished';

/** Complete QKD key generation response */
export interface QKDResponse {
  sessionId: string;
  phases: {
    transmission: TransmissionResult;
    basisSifting: SiftingResult;
    qberEstimation: QBERResult;
    errorCorrection: ErrorCorrectionResult;
    keyEstablished: KeyResult;
  };
  /** Only present when eveSimulation config is enabled */
  eveData?: EveResult;
}

/**
 * A single session entry returned by GET /vote/voting-audits/{electionCode}.
 * Fields map 1-to-1 to the new backend VotingSchema.
 */
export interface VotingLogEntry {
  sessionId: string;
  voterId: string;
  keyGenerated: string;
  /** Indices of bits selected for QBER check */
  selectedBits: number[];
  // ── Qubit Transmission Log ────────────────────────────────
  /** Alice's sent bits as a binary string, e.g. "0110..." */
  aliceBit: string;
  /** Alice's bases as a binary string (0=+, 1=×) */
  aliceBasis: string;
  /** Bob's measured bits as a binary string */
  bobRead: string;
  /** Bob's measurement bases as a binary string (0=+, 1=×) */
  bobBasis: string;
  /** Eve's measured bits (binary string) — present if eavesdropper active */
  eveRead?: string;
  /** Eve's measurement bases (binary string, 0=+, 1=×) — present if eavesdropper active */
  eveBasis?: string;
  // ── QBER Estimation ──────────────────────────────────────
  testSample: number;
  errorFound: number;
  /** QBER as seen from Alice & Bob's perspective (0-100) */
  qberPractical: number;
  /** True system QBER including Eve's impact (0-100) */
  qberSystem: number;
  thresholdPercent: number;
  // ── Session metadata ─────────────────────────────────────
  /** Raw status string from backend, e.g. "KEY READY", "VOTE_CAST", "ABORTED" */
  status: string;
  createdAt: number;
  updatedAt: number;
}

export interface VotingLogResponse {
  sessions: VotingLogEntry[];
}
