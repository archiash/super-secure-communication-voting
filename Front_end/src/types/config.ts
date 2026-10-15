/**
 * Protocol configuration for the QKD BB84 simulation.
 * These parameters are set on the Configure page and displayed
 * in the ACTIVE CONFIGURATION sidebar card.
 */
export interface ProtocolConfig {
  /** Number of physical qubits allocated per quantum circuit execution batch on quantum computer/simulator (e.g. 4, 16, 32, 64) */
  qubitCount: number;

  /** Desired final key length in bits after sifting + error correction (n). e.g., 64 */
  targetKeyLength: number;

  /** Whether to use a real IBM Quantum computer or simulated backend */
  useRealQuantum: boolean;

  /** Whether to simulate an eavesdropper (Eve) intercepting qubits */
  eveSimulation: boolean;

  /** Whether Cascade error correction is enabled */
  errorCorrectionEnabled: boolean;

  /** Whether Privacy Amplification (Toeplitz universal hashing) is enabled */
  privacyAmplificationEnabled: boolean;

  /** Security parameter s in bits (e.g. 16) ensuring Eve information <= 2^-s */
  securityParameter: number;

  /** Maximum acceptable QBER before key is rejected. e.g., 0.11 (11%) */
  errorThreshold: number;

  /** Number of sifted key bits sacrificed for QBER estimation. e.g., 4 */
  testBitCount: number;

  /** Error tolerance (δ) — acceptable error margin buffer in the range [0, 2]. e.g., 0.05 */
  errorTolerance: number;
}

/**
 * Calculate the total number of polarized photons to transmit in the channel:
 * With Privacy Amplification: N_photons = ceil((4 + delta) * (targetKeyLength + s))
 * Without Privacy Amplification: N_photons = ceil((4 + delta) * targetKeyLength)
 */
export function calculatePhotonCount(
  targetKeyLength: number,
  errorTolerance: number,
  securityParameter: number = 16,
  privacyAmplificationEnabled: boolean = true
): number {
  if (privacyAmplificationEnabled) {
    return Math.ceil((4 + errorTolerance) * (targetKeyLength + securityParameter));
  }
  return Math.ceil((4 + errorTolerance) * targetKeyLength);
}

/** Default configuration */
export const DEFAULT_CONFIG: ProtocolConfig = {
  qubitCount: 4, // physical QPU qubits per run
  targetKeyLength: 64, // target final secret key length n
  useRealQuantum: true,
  eveSimulation: false,
  errorCorrectionEnabled: false,
  privacyAmplificationEnabled: true,
  securityParameter: 16,
  errorThreshold: 0.11,
  testBitCount: 4,
  errorTolerance: 0.05,
};
