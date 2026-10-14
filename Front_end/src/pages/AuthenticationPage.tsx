import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { Stepper } from '../components/layout/Stepper';
import styles from './AuthenticationPage.module.css';

export function AuthenticationPage() {
  const { state, dispatch, api } = useApp();
  const navigate = useNavigate();

  const [voterId, setVoterId] = useState('');
  const [electionCode, setElectionCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleAuthenticate = async () => {
    setError(null);

    if (!voterId.trim()) {
      setError('Voter ID is required.');
      return;
    }
    if (!electionCode.trim()) {
      setError('Election Code is required.');
      return;
    }

    setIsLoading(true);
    try {
      const response = await api.verifyAuth({ voterId, electionCode });

      if (!response.valid) {
        setError(response.error || 'Authentication failed.');
        setIsLoading(false);
        return;
      }

      dispatch({
        type: 'AUTHENTICATE',
        payload: {
          voterId,
          electionCode,
          sessionId: response.sessionId,
        },
      });

      // Navigate to key generation. Generation will start on mount there.
      navigate('/key-generation');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <Stepper currentStep="authentication" />

      <div className={styles.headerSection}>
        <div className={styles.badgeRow}>
          <span className="quantum-badge" style={{ background: '#eff6ff', color: '#1d4ed8', border: '1px solid #bfdbfe' }}>
            <span className="quantum-pulse"></span> E2E QUANTUM-SECURED BALLOT
          </span>
        </div>
        <h1 className={styles.title}>Voter Authentication</h1>
        <p className={styles.subtitle}>
          Authenticate your eligible identity to initialize an unconditional quantum key exchange (BB84).
        </p>
      </div>

      <div className={styles.contentGrid}>
        <div className={styles.formCard}>
          <div className={styles.formHeader}>
            <span className={styles.formCardTitle}>VOTER CREDENTIALS</span>
            <span className={styles.formCardSubtitle}>Enter your election authorization tokens</span>
          </div>

          <div className={styles.form}>
            <div className={styles.formGroup}>
              <div className={styles.labelRow}>
                <label className={styles.label}>Voter ID</label>
                <span className={styles.inputHint}>Unique voter token</span>
              </div>
              <input
                type="text"
                className={styles.input}
                placeholder="e.g. V-2026-001234"
                value={voterId}
                onChange={(e) => setVoterId(e.target.value)}
              />
            </div>

            <div className={styles.formGroup}>
              <div className={styles.labelRow}>
                <label className={styles.label}>Election Code</label>
                <span className={styles.inputHint}>Active ballot identifier</span>
              </div>
              <input
                type="text"
                className={styles.input}
                placeholder="Enter election code"
                value={electionCode}
                onChange={(e) => setElectionCode(e.target.value)}
              />
              <div className={styles.quickFillBar}>
                <span className={styles.quickFillLabel}>Quick Test:</span>
                <button
                  type="button"
                  className={styles.quickChip}
                  onClick={() => {
                    setVoterId('V-2026-0842');
                    setElectionCode('ELECT2026');
                  }}
                >
                  ⚡ Auto-fill Demo Credentials
                </button>
              </div>
            </div>

            {error && (
              <div className={styles.errorBox}>
                <span className={styles.errorIcon}>⚠️</span>
                <span>{error}</span>
              </div>
            )}

            <button
              className={styles.primaryButton}
              onClick={handleAuthenticate}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <span className={styles.spinner}></span>
                  <span>Verifying Credentials...</span>
                </>
              ) : (
                <>
                  <span>Begin Quantum Key Exchange</span>
                  <span className={styles.buttonArrow}>→</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* ACTIVE CONFIGURATION & ASSURANCE CARD */}
        <div className={styles.sideStack}>
          <div className={styles.configCard}>
            <div className={styles.configHeader}>
              <div className={styles.configHeaderTitle}>
                <span className={styles.configDot}></span>
                <span className={styles.configTitle}>ACTIVE BB84 PARAMETERS</span>
              </div>
              <button 
                className={styles.editLinkBtn}
                onClick={() => navigate('/configure')}
              >
                Configure ›
              </button>
            </div>

            <div className={styles.configRow}>
              <span className={styles.configLabel}>Photons to transmit</span>
              <span className={styles.configValue}>{state.config.qubitCount} qubits</span>
            </div>
            
            <div className={styles.configRow}>
              <span className={styles.configLabel}>Target key length</span>
              <span className={styles.configValue}>{state.config.targetKeyLength} bits</span>
            </div>

            <div className={styles.configRow}>
              <span className={styles.configLabel}>Max QBER safety margin (δ)</span>
              <span className={styles.configValue}>{(state.config.errorTolerance * 100).toFixed(0)}%</span>
            </div>
            
            <div className={styles.configRow}>
              <span className={styles.configLabel}>Quantum simulation backend</span>
              <span className={styles.configBadge}>
                {state.config.useRealQuantum ? 'Real QPU (IBM Q)' : 'Qiskit Aer Simulator'}
              </span>
            </div>
            
            <div className={styles.configRow}>
              <span className={styles.configLabel}>Adversary simulation</span>
              <span className={`${styles.statusBadge} ${state.config.eveSimulation ? styles.danger : styles.neutral}`}>
                {state.config.eveSimulation ? 'Eve Interception Active' : 'Passive Fiber Channel'}
              </span>
            </div>
          </div>

          <div className={styles.guaranteeCard}>
            <div className={styles.guaranteeHeader}>
              <span className={styles.guaranteeIcon}>🛡️</span>
              <span className={styles.guaranteeTitle}>Cryptographic Guarantee</span>
            </div>
            <p className={styles.guaranteeText}>
              Ballots are encrypted with a One-Time Pad generated dynamically via photon polarization. Under the laws of quantum mechanics, any eavesdropping introduces detectable noise (QBER) and immediately invalidates the channel.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
