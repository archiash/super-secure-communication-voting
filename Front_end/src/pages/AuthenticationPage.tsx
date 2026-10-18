import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { Stepper } from '../components/layout/Stepper';
import styles from './AuthenticationPage.module.css';

const getNextVoterNumber = (): number => {
  const stored = localStorage.getItem('demo_voter_counter');
  let num = stored ? parseInt(stored, 10) : 1;
  if (isNaN(num) || num < 1 || num >= 200) {
    num = 1;
    localStorage.setItem('demo_voter_counter', '1');
  }
  return num;
};

export function AuthenticationPage() {
  const { state, dispatch, api } = useApp();
  const navigate = useNavigate();

  const [voterId, setVoterId] = useState(() => `V-2026-${getNextVoterNumber()}`);
  const [electionCode, setElectionCode] = useState('ELECT2026');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleAuthenticate = async () => {
    setError(null);

    const effectiveVoterId = voterId.trim() || `V-2026-${getNextVoterNumber()}`;
    const effectiveElectionCode = electionCode.trim() || 'ELECT2026';

    if (!voterId.trim()) setVoterId(effectiveVoterId);
    if (!electionCode.trim()) setElectionCode(effectiveElectionCode);

    setIsLoading(true);
    try {
      if (state.auth.sessionId && !state.auth.isReplay) {
        try {
          await api.abortSession(state.auth.sessionId, state.auth.electionCode || effectiveElectionCode);
        } catch (err) {
          console.warn('Failed to abort prior session:', err);
        }
      }

      const response = await api.verifyAuth({ voterId: effectiveVoterId, electionCode: effectiveElectionCode });

      if (!response.valid) {
        setError(response.error || 'Authentication failed.');
        setIsLoading(false);
        return;
      }

      // Increment running demo voter counter for the next session
      const match = effectiveVoterId.match(/V-2026-(\d+)/i);
      const currentNum = match ? parseInt(match[1], 10) : getNextVoterNumber();
      const nextNum = isNaN(currentNum) ? 1 : currentNum + 1;
      localStorage.setItem('demo_voter_counter', nextNum.toString());

      dispatch({
        type: 'AUTHENTICATE',
        payload: {
          voterId: effectiveVoterId,
          electionCode: effectiveElectionCode,
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

      <h1 className={styles.title}>Voter Authentication</h1>
      <p className={styles.subtitle}>
        Verify your credentials to initiate quantum key distribution.
      </p>

      <div className={styles.contentGrid}>
        <div className={styles.form}>
          <div className={styles.formGroup}>
            <label className={styles.label}>Voter ID</label>
            <input
              type="text"
              className={styles.input}
              placeholder="e.g. V-2026-001234"
              value={voterId}
              onChange={(e) => setVoterId(e.target.value)}
            />
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label}>Election Code</label>
            <input
              type="text"
              className={styles.input}
              placeholder="Enter election code"
              value={electionCode}
              onChange={(e) => setElectionCode(e.target.value)}
            />
            <span className={styles.demoHint}>
              Demo code: <strong>ELECT2026</strong>
            </span>
          </div>

          {error && (
            <div className={styles.errorBox}>
              <span className={styles.errorIcon}>❗</span>
              {error}
            </div>
          )}

          <button
            className={styles.primaryButton}
            onClick={handleAuthenticate}
            disabled={isLoading}
          >
            {isLoading ? 'Authenticating...' : 'Authenticate & Generate Quantum Key ›'}
          </button>
        </div>

        {/* ACTIVE CONFIGURATION Card */}
        <div>
          <div className={styles.configCard}>
            <div className={styles.configHeader}>
              <span className={styles.configTitle}>
                ⬡ ACTIVE CONFIGURATION
              </span>
              <span 
                className={styles.editLink}
                onClick={() => navigate('/configure')}
              >
                Edit
              </span>
            </div>

            <div className={styles.configRow}>
              <span className={styles.configLabel}>Target key length (n)</span>
              <span className={styles.configValue}>{state.config.targetKeyLength} bits</span>
            </div>

            <div className={styles.configRow}>
              <span className={styles.configLabel}>Safety margin (δ)</span>
              <span className={styles.configValue}>{state.config.errorTolerance.toFixed(2)}</span>
            </div>

            <div className={styles.configRow}>
              <span className={styles.configLabel}>QPU Qubit capacity</span>
              <span className={styles.configValue}>{state.config.qubitCount} qubits</span>
            </div>
            
            <div className={styles.configRow}>
              <span className={styles.configLabel}>Use quantum computer</span>
              <span className={styles.configValue}>
                {state.config.useRealQuantum ? 'enabled' : 'disabled'}
              </span>
            </div>
            
            <div className={styles.configRow}>
              <span className={styles.configLabel}>Eve simulation</span>
              <span className={`${styles.configValue} ${state.config.eveSimulation ? styles.danger : ''}`}>
                {state.config.eveSimulation ? 'active' : 'inactive'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
