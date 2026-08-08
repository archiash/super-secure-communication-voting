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

          <button
            className={styles.secondaryButton}
            onClick={() => navigate('/configure')}
          >
            ⚙ Configure Protocol
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
              <span className={styles.configLabel}>Qubit count</span>
              <span className={styles.configValue}>{state.config.qubitCount}</span>
            </div>
            
            <div className={styles.configRow}>
              <span className={styles.configLabel}>Error correction</span>
              <span className={styles.configValue}>
                Cascade ({state.config.errorCorrectionEnabled ? 'enabled' : 'disabled'})
              </span>
            </div>
            
            <div className={styles.configRow}>
              <span className={styles.configLabel}>Target key length</span>
              <span className={styles.configValue}>{state.config.targetKeyLength} bits</span>
            </div>
            
            <div className={styles.configRow}>
              <span className={styles.configLabel}>Use real quantum computer</span>
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
