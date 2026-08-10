import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { Stepper } from '../components/layout/Stepper';
import styles from './KeyGenerationPage.module.css';
import type { QKDPhase, TransmissionLogEntry, Basis } from '../types';

const ALL_QKD_PHASES: { id: QKDPhase; title: string; subtitle: string }[] = [
  { id: 'transmission', title: 'Transmission', subtitle: '40 photons' },
  { id: 'basisSifting', title: 'Basis Sifting', subtitle: 'Reconciliation' },
  { id: 'qberEstimation', title: 'QBER Estimation', subtitle: 'Error analysis' },
  { id: 'errorCorrection', title: 'Error Correction', subtitle: 'Cascade protocol' },
  { id: 'keyEstablished', title: 'Key Established', subtitle: '' },
];

export function KeyGenerationPage() {
  const { state, dispatch, api } = useApp();
  const navigate = useNavigate();

  // Phase state lives in global store so it survives navigation to/from Configure
  const currentPhase = state.qkd.currentPhase;
  const isBlurred = state.qkd.isBlurred;
  const isTransmitting = state.qkd.isTransmitting;

  const setCurrentPhase = (phase: QKDPhase) =>
    dispatch({ type: 'SET_QKD_PHASE', payload: { currentPhase: phase } });
  const setIsBlurred = (val: boolean) =>
    dispatch({ type: 'SET_QKD_PHASE', payload: { currentPhase, isBlurred: val } });

  // Ref guard to prevent double-call in React StrictMode
  const hasStartedRef = useRef(false);

  // If no auth, go back
  useEffect(() => {
    if (!state.auth.isAuthenticated) {
      navigate('/');
    } else if (!state.qkd.result && !state.qkd.isGenerating && !hasStartedRef.current) {
      hasStartedRef.current = true;
      // Only start generation if we don't already have a result
      startKeyGeneration();
    }
  }, [state.auth.isAuthenticated, navigate, state.qkd.result, state.qkd.isGenerating]);

  const startKeyGeneration = async () => {
    dispatch({ type: 'QKD_START' });
    try {
      const result = await api.generateKey(
        state.auth.voterId,
        state.auth.electionCode,
        state.config
      );

      dispatch({ type: 'QKD_SUCCESS', payload: result });

      // Simulate transmission time then advance to basisSifting
      setTimeout(() => {
        dispatch({ type: 'SET_QKD_PHASE', payload: { currentPhase: 'basisSifting', isTransmitting: false, isBlurred: true } });
      }, 2000);

    } catch (err) {
      dispatch({
        type: 'SET_ERROR',
        payload: err instanceof Error ? err.message : 'Key generation failed',
      });
    }
  };

  const getPhotonSymbol = (bit: number, basis: Basis) => {
    if (basis === '+') {
      return bit === 1 ? '↑' : '→';
    } else {
      return bit === 1 ? '↖' : '↗';
    }
  };

  const getKeepStatus = (entry: TransmissionLogEntry) => {
    if (!entry.keep) return <span className={styles.resultDiscard}>✗</span>;
    if (entry.aliceBit === entry.bobRead) return <span className={styles.resultKeep}>✓</span>;
    return <span className={styles.resultError}>✓!</span>;
  };

  const qkdResult = state.qkd.result;
  const isAborted = qkdResult && !qkdResult.phases.qberEstimation.passed;
  const errorCorrectionEnabled = state.config.errorCorrectionEnabled;
  const QKD_PHASES = errorCorrectionEnabled
    ? ALL_QKD_PHASES
    : ALL_QKD_PHASES.filter(p => p.id !== 'errorCorrection');
  const currentPhaseIndex = QKD_PHASES.findIndex(p => p.id === currentPhase);

  const handleNextPhase = () => {
    if (currentPhase === 'basisSifting') {
      if (isBlurred) {
        setIsBlurred(false);
        // If aborted, we jump to QBER right after revealing to show the error
        if (isAborted) {
          setTimeout(() => {
            setCurrentPhase('qberEstimation');
          }, 1000);
        }
      } else {
        setCurrentPhase('qberEstimation');
      }
    } else if (currentPhase === 'qberEstimation' && !isAborted) {
      // Skip error correction phase if disabled
      setCurrentPhase(errorCorrectionEnabled ? 'errorCorrection' : 'keyEstablished');
    } else if (currentPhase === 'errorCorrection') {
      setCurrentPhase('keyEstablished');
    } else if (currentPhase === 'keyEstablished') {
      navigate('/cast-vote');
    }
  };

  const handleRetry = () => {
    startKeyGeneration();
  };

  return (
    <div className={styles.page}>
      <Stepper currentStep="keyGeneration" />

      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>BB84 Quantum Key Distribution</h1>
          <p className={styles.subtitle}>Establishing shared secret key via quantum channel</p>
        </div>
        <div className={styles.sessionInfo}>
          <div className={styles.sessionLabel}>SESSION</div>
          <div className={styles.sessionId}>{state.auth.sessionId || 'QS-PENDING'}</div>
        </div>
      </div>

      <div className={styles.trackerCard}>
        <div className={styles.trackerLine}>
          <div
            className={styles.trackerLineFill}
            style={{ width: `${(currentPhaseIndex / (QKD_PHASES.length - 1)) * 100}%` }}
          />
        </div>

        {QKD_PHASES.map((phase, idx) => {
          const isActive = idx === currentPhaseIndex;
          const isCompleted = idx < currentPhaseIndex;
          const isFailedStep = isAborted && currentPhaseIndex >= 2 && idx >= 3; // Steps after QBER are failed if aborted and we've reached QBER
          const isQberActiveFailed = isAborted && idx === 2 && currentPhase === 'qberEstimation';

          let iconClass = styles.pending;
          if (isActive) iconClass = styles.active;
          if (isCompleted && !isFailedStep) iconClass = styles.completed;
          if (isFailedStep || isQberActiveFailed) iconClass = styles.failed; // Keep blue dot for active QBER even if failed? Figma shows QBER is blue active dot, Error Correction and Key Estab are red X.

          if (isQberActiveFailed) iconClass = styles.active; // Figma shows QBER is active blue

          return (
            <div key={phase.id} className={styles.trackerStep}>
              <div className={`${styles.stepIcon} ${iconClass}`}>
                {isCompleted && !isFailedStep && '✓'}
                {isFailedStep && '✗'}
                {isActive && <div className={styles.activeDot} />}
                {!isCompleted && !isActive && !isFailedStep && <div className={styles.pendingDot} />}
              </div>
              <div className={styles.stepTitle}>{phase.title}</div>
              <div className={styles.stepDesc}>
                {phase.id === 'transmission' ? `${state.config.qubitCount} photons` : phase.subtitle}
              </div>
            </div>
          );
        })}
      </div>

      {isTransmitting && (
        <div className={styles.transmittingBox}>
          <div className={styles.chipIcon}>▣</div>
          <div className={styles.transmittingText}>
            Transmitting {state.config.qubitCount} polarized photons...
          </div>
          <div className={styles.transmittingSub}>
            {state.config.useRealQuantum ? 'ibmq_qasm_simulator · shots=1024' : 'local_simulator · instant'}
          </div>
        </div>
      )}

      {!isTransmitting && qkdResult && (currentPhaseIndex >= 1) && (
        <div className={styles.tableCard}>
          <div className={styles.tableHeader}>
            <span className={styles.tableTitle}>QUBIT TRANSMISSION LOG</span>
            <span className={styles.tableStats}>
              {state.config.qubitCount} photons · {qkdResult.phases.basisSifting.matchingBases} matching bases
            </span>
          </div>
          <div className={styles.logTableWrapper}>
            <table className={styles.logTable}>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Alice Bit</th>
                  <th>Alice Basis</th>
                  <th>Photon</th>
                  <th className={isBlurred ? styles.blurredArea : ''}>Bob Basis</th>
                  <th className={isBlurred ? styles.blurredArea : ''}>Bob Read</th>
                  <th className={isBlurred ? styles.blurredArea : ''}>Keep</th>
                </tr>
              </thead>
              <tbody>
                {qkdResult.phases.transmission.log.map((entry, idx) => (
                  <tr key={idx}>
                    <td>{idx + 1}</td>
                    <td>{entry.aliceBit}</td>
                    <td>{entry.aliceBasis}</td>
                    <td className={styles.photonArrow}>{getPhotonSymbol(entry.aliceBit, entry.aliceBasis)}</td>
                    <td className={isBlurred ? styles.blurredArea : ''}>{entry.bobBasis}</td>
                    <td className={isBlurred ? styles.blurredArea : ''}>{entry.bobRead}</td>
                    <td className={isBlurred ? styles.blurredArea : ''}>{getKeepStatus(entry)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* QBER Panel */}
      {!isTransmitting && qkdResult && currentPhaseIndex >= 2 && (
        <div className={`${styles.panel} ${!qkdResult.phases.qberEstimation.passed ? styles.danger : ''}`}>
          <div className={styles.panelHeader}>
            <span className={styles.panelTitle}>QBER ESTIMATION</span>
            <span className={`${styles.statusBadge} ${qkdResult.phases.qberEstimation.passed ? styles.statusSuccess : styles.statusDanger}`}>
              {qkdResult.phases.qberEstimation.passed ? 'WITHIN THRESHOLD' : 'EXCEEDS THRESHOLD'}
            </span>
          </div>

          <div className={styles.statsRow}>
            <div className={styles.statCol}>
              <span className={styles.statLabel}>Test sample</span>
              <span className={styles.statValue}>
                {qkdResult.phases.qberEstimation.testBitsUsed} bits
                <span className={styles.statSubValue}> ({Math.round((qkdResult.phases.qberEstimation.testBitsUsed / qkdResult.phases.basisSifting.matchingBases) * 100)}% sifted)</span>
              </span>
            </div>
            <div className={styles.statCol}>
              <span className={styles.statLabel}>Errors found</span>
              <span className={styles.statValue}>{qkdResult.phases.qberEstimation.errorsFound} bits</span>
            </div>
            <div className={styles.statCol}>
              <span className={styles.statLabel}>QBER</span>
              <span className={`${styles.statValue} ${!qkdResult.phases.qberEstimation.passed ? styles.danger : ''}`}>
                {(qkdResult.phases.qberEstimation.qber * 100).toFixed(1)}%
              </span>
            </div>
            <div className={styles.statCol}>
              <span className={styles.statLabel}>Threshold</span>
              <span className={styles.statValue}>{(state.config.errorThreshold * 100).toFixed(0)}%</span>
            </div>
          </div>

          <div className={styles.barContainer}>
            <div
              className={styles.barFill}
              style={{
                width: `${Math.min(100, (qkdResult.phases.qberEstimation.qber / 1.0) * 100)}%`,
                backgroundColor: !qkdResult.phases.qberEstimation.passed ? 'var(--color-danger)' : 'var(--color-border-light)'
              }}
            />
            <div
              className={styles.barThresholdTick}
              style={{ left: `${(state.config.errorThreshold / 1.0) * 100}%` }}
            />
            <div
              className={styles.barThresholdLabel}
              style={{ left: `${(state.config.errorThreshold / 1.0) * 100}%` }}
            >
              threshold
            </div>
          </div>
        </div>
      )}

      {/* Abort State */}
      {!isTransmitting && qkdResult && currentPhaseIndex >= 2 && !qkdResult.phases.qberEstimation.passed && (
        <div className={styles.alertBox}>
          <div className={styles.alertIcon}>⚠</div>
          <div className={styles.alertContent}>
            <div className={styles.alertTitle}>Session Aborted — Possible Eavesdropper Detected</div>
            <div className={styles.alertText}>
              The measured QBER ({(qkdResult.phases.qberEstimation.qber * 100).toFixed(1)}%) exceeds the security threshold ({(state.config.errorThreshold * 100).toFixed(0)}%). This is consistent with an intercept-resend attack. The session key has been discarded and no vote can be cast.
            </div>
            <button className={styles.retryButton} onClick={handleRetry}>
              ↻ Retry Session
            </button>
          </div>
        </div>
      )}

      {/* Error Correction Panel */}
      {!isTransmitting && qkdResult && errorCorrectionEnabled && currentPhaseIndex >= 3 && qkdResult.phases.qberEstimation.passed && (
        <div className={styles.panel}>
          <div className={styles.panelHeader}>
            <span className={styles.panelTitle}>CASCADE ERROR CORRECTION</span>
          </div>
          <div className={styles.statsRow}>
            <div className={styles.statCol}>
              <span className={styles.statLabel}>Input bits</span>
              <span className={styles.statValue}>{qkdResult.phases.basisSifting.siftedKeyBits.length - qkdResult.phases.qberEstimation.testBitsUsed}</span>
            </div>
            <div className={styles.statCol}>
              <span className={styles.statLabel}>Errors corrected</span>
              <span className={styles.statValue}>{qkdResult.phases.errorCorrection.correctedBits}</span>
            </div>
            <div className={styles.statCol}>
              <span className={styles.statLabel}>Bits sacrificed</span>
              <span className={styles.statValue}>{(qkdResult.phases.basisSifting.siftedKeyBits.length - qkdResult.phases.qberEstimation.testBitsUsed) - qkdResult.phases.keyEstablished.keyLength}</span>
            </div>
            <div className={styles.statCol}>
              <span className={styles.statLabel}>Output bits</span>
              <span className={styles.statValue}>{qkdResult.phases.keyEstablished.keyLength}</span>
            </div>
          </div>
          <div className={styles.panelFooterText}>
            Remaining error rate: 0% (all errors corrected via parity checks)
          </div>
        </div>
      )}

      {/* Key Established Panel */}
      {!isTransmitting && qkdResult && currentPhase === 'keyEstablished' && qkdResult.phases.qberEstimation.passed && (
        <div className={styles.panel}>
          <div className={styles.panelHeader}>
            <span className={`${styles.panelTitle} ${styles.blue}`}>
              FINAL KEY · {qkdResult.phases.keyEstablished.keyLength} BITS · {Math.round((qkdResult.phases.keyEstablished.keyLength / state.config.qubitCount) * 100)}% CHANNEL EFFICIENCY
            </span>
            {/*<span>🔒</span>*/}
            <span>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.8 }}>
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
              </svg>
            </span>
          </div>

          <div className={styles.keyText}>
            {qkdResult.phases.keyEstablished.finalKey}
          </div>

          <div className={styles.keyBlocks}>
            {qkdResult.phases.keyEstablished.finalKey.split('').map((bit, i) => (
              <div key={i} className={styles.keyBlock}>{bit}</div>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons for proceeding manually */}
      {!isTransmitting && qkdResult && (
        <div className={styles.actionArea}>
          {currentPhase === 'basisSifting' && isBlurred && (
            <button className={styles.primaryButton} onClick={handleNextPhase}>
              Send key to Bob ›
            </button>
          )}
          {currentPhase === 'basisSifting' && !isBlurred && !isAborted && (
            <button className={styles.primaryButton} onClick={handleNextPhase}>
              Calculate QBER ›
            </button>
          )}
          {currentPhase === 'qberEstimation' && !isAborted && errorCorrectionEnabled && (
            <button className={styles.primaryButton} onClick={handleNextPhase}>
              Run Cascade Protocol ›
            </button>
          )}
          {currentPhase === 'qberEstimation' && !isAborted && !errorCorrectionEnabled && (
            <button className={styles.primaryButton} onClick={handleNextPhase}>
              Establish Key ›
            </button>
          )}
          {currentPhase === 'errorCorrection' && !isAborted && (
            <button className={styles.primaryButton} onClick={handleNextPhase}>
              Establish Key ›
            </button>
          )}
          {currentPhase === 'keyEstablished' && !isAborted && (
            <button className={styles.primaryButton} onClick={handleNextPhase}>
              Proceed to Ballot ›
            </button>
          )}
        </div>
      )}
    </div>
  );
}
