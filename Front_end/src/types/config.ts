/**
 * Protocol configuration for the QKD BB84 simulation.
 * These parameters are set on the Configure page and displayed
 * in the ACTIVE CONFIGURATION sidebar card.
 */
export interface ProtocolConfig {
  /** Number of qubits transmitted in the BB84 protocol (before sifting). e.g., 40 */
  qubitCount: number;

  /** Desired final key length in bits after sifting + error correction. e.g., 8 */
  targetKeyLength: number;

  /** Whether to use a real IBM Quantum computer or simulated backend */
  useRealQuantum: boolean;

  /** Whether to simulate an eavesdropper (Eve) intercepting qubits */
  eveSimulation: boolean;

  /** Whether Cascade error correction is enabled */
  errorCorrectionEnabled: boolean;

  /** Maximum acceptable QBER before key is rejected. e.g., 0.11 (11%) */
  errorThreshold: number;

  /** Number of sifted key bits sacrificed for QBER estimation. e.g., 4 */
  testBitCount: number;
}

/** Default configuration matching the Figma "ACTIVE CONFIGURATION" card */
export const DEFAULT_CONFIG: ProtocolConfig = {
  qubitCount: 32,
  targetKeyLength: 64,
  useRealQuantum: false,
  eveSimulation: false,
  errorCorrectionEnabled: false,
  errorThreshold: 0.11,
  testBitCount: 4,
};
