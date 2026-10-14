import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { Stepper } from '../components/layout/Stepper';
import styles from './KeyGenerationPage.module.css';
import { calculatePhotonCount } from '../types';
import type { QKDPhase, TransmissionLogEntry, Basis } from '../types';

type ViewMode = 'voter' | 'system';

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
  const isAborted = Boolean(
    qkdResult && (
      !qkdResult.phases.qberEstimation.passed ||
      !qkdResult.phases.keyEstablished.finalKey ||
      qkdResult.phases.keyEstablished.keyLength === 0
    )
  );
  const isEveAbort = Boolean(
    qkdResult && (qkdResult.phases.qberEstimation.qber > state.config.errorThreshold)
  );
  const errorCorrectionEnabled = state.config.errorCorrectionEnabled;
  const QKD_PHASES = errorCorrectionEnabled
    ? ALL_QKD_PHASES
    : ALL_QKD_PHASES.filter(p => p.id !== 'errorCorrection');
  const currentPhaseIndex = QKD_PHASES.findIndex(p => p.id === currentPhase);

  const [viewMode, setViewMode] = useState<ViewMode>('voter');

  // Derived metrics for detailed visualization
  const totalPhotons = qkdResult?.phases.transmission.qubitCount || calculatePhotonCount(state.config.targetKeyLength, state.config.errorTolerance);
  const matchingBases = qkdResult?.phases.basisSifting.matchingBases || 0;
  const discardedCount = Math.max(0, totalPhotons - matchingBases);
  const siftingEfficiency = totalPhotons > 0 ? ((matchingBases / totalPhotons) * 100).toFixed(1) : '0.0';
  const discardedPct = totalPhotons > 0 ? ((discardedCount / totalPhotons) * 100).toFixed(1) : '0.0';
  const siftedBitstring = qkdResult?.phases.basisSifting.siftedKeyBits.join('') || '';

  const matchingEntries = (qkdResult?.phases.transmission.log || [])
    .map((entry, idx) => ({ ...entry, photonNumber: idx + 1 }))
    .filter(e => e.keep);
  const matchingIndices = matchingEntries.map(e => e.photonNumber);

  const testSampleCount = qkdResult?.phases.qberEstimation.testBitsUsed || state.config.testBitCount || 4;
  const testSamples = matchingEntries.slice(0, testSampleCount);

  // Separate stages: 1) Measure qubits, 2) Sift bases, 3) Calculate QBER
  const [isSiftedLocal, setIsSiftedLocal] = useState(false);
  const isMeasured = !isBlurred || currentPhaseIndex >= 2;
  const isSifted = (isSiftedLocal && !isBlurred) || currentPhaseIndex >= 2;

  const handleMeasure = () => {
    setIsBlurred(false);
    setIsSiftedLocal(false);
  };

  const handleSift = () => {
    setIsSiftedLocal(true);
  };

  const handleCalculateQber = () => {
    setCurrentPhase('qberEstimation');
  };

  const handleNextPhase = () => {
    if (currentPhase === 'qberEstimation' && !isAborted) {
      // Skip error correction phase if disabled
      setCurrentPhase(errorCorrectionEnabled ? 'errorCorrection' : 'keyEstablished');
    } else if (currentPhase === 'errorCorrection') {
      setCurrentPhase('keyEstablished');
    } else if (currentPhase === 'keyEstablished') {
      navigate('/cast-vote');
    }
  };

  const handleRetry = () => {
    setIsSiftedLocal(false);
    startKeyGeneration();
  };

  return (
    <div className={styles.page}>
      <Stepper currentStep="keyGeneration" />

      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>BB84 Quantum Key Distribution</h1>
          <p className={styles.subtitle}>Election Server preparing quantum states &amp; establishing key with Voter Terminal</p>
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
          if (isFailedStep || isQberActiveFailed) iconClass = styles.failed;

          if (isQberActiveFailed) iconClass = styles.active;

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
                {phase.id === 'transmission'
                  ? `${calculatePhotonCount(state.config.targetKeyLength, state.config.errorTolerance)} photons`
                  : phase.subtitle}
              </div>
            </div>
          );
        })}
      </div>

      {isTransmitting && (
        <div className={styles.transmittingBox}>
          <div className={styles.chipIcon}>▣</div>
          <div className={styles.transmittingText}>
            Election Server is preparing &amp; transmitting {calculatePhotonCount(state.config.targetKeyLength, state.config.errorTolerance)} polarized photons...
          </div>
          <div className={styles.transmittingSub}>
            {state.config.useRealQuantum
              ? `ibmq_qasm_simulator · ${state.config.qubitCount} QPU qubits`
              : `local_simulator · ${state.config.qubitCount} QPU qubits`}
          </div>
        </div>
      )}

      {/* Perspective / View Mode Switcher Toolbar */}
      {!isTransmitting && qkdResult && (currentPhaseIndex >= 1) && (
        <div className={styles.viewModeBar}>
          <div className={styles.viewModeInfo}>
            <div className={styles.viewModeTag}>Visualization Perspective</div>
            <div className={styles.viewModeDesc}>
              {viewMode === 'voter'
                ? 'Displaying real Voter Terminal (Bob) perspective — horizontal measurement grid & phased verification cards.'
                : 'Displaying omniscient System Diagnostic view — showing Server quantum states, preparation bases, and full channel ground truth.'}
            </div>
          </div>
          <div className={styles.viewToggleWrap}>
            <button
              type="button"
              className={`${styles.viewToggleBtn} ${viewMode === 'voter' ? styles.viewToggleActive : ''}`}
              onClick={() => setViewMode('voter')}
            >
              <span className={styles.viewToggleLabel}>Voter View (Default)</span>
              <span className={styles.viewToggleSub}>Real client terminal</span>
            </button>
            <button
              type="button"
              className={`${styles.viewToggleBtn} ${viewMode === 'system' ? styles.viewToggleActive : ''}`}
              onClick={() => setViewMode('system')}
            >
              <span className={styles.viewToggleLabel}>System View</span>
              <span className={styles.viewToggleSub}>Omniscient physical trace</span>
            </button>
          </div>
        </div>
      )}

      {/* ── CARD 1: Qubit Transmission / Measurement Log ── */}
      {!isTransmitting && qkdResult && (currentPhaseIndex >= 1) && (
        <div className={styles.tableCard}>
          <div className={styles.tableHeader}>
            <div>
              <span className={styles.tableTitle}>
                {viewMode === 'voter'
                  ? 'VOTER TERMINAL QUBIT MEASUREMENT LOG'
                  : 'SYSTEM QUANTUM TRANSMISSION LOG'}
              </span>
              <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                {viewMode === 'voter'
                  ? 'Photons received by Voter Terminal detector · Basis choice & measurement outcome'
                  : 'Channel: Election Server (Sender) ──[ Quantum Channel ]──▸ Voter Terminal (Receiver)'}
              </div>
            </div>
            <span className={styles.tableStats}>
              {totalPhotons} photons {viewMode === 'voter' ? (!isMeasured ? 'received · measurement pending' : !isSifted ? 'measured · basis sifting pending' : `· ${matchingBases} matching bases`) : `· ${matchingBases} matching bases`}
            </span>
          </div>

          {viewMode === 'voter' ? (
            /* Horizontal Matrix for Voter View */
            <div className={styles.hGridContainer}>
              <table className={styles.hGridTable}>
                <tbody>
                  <tr>
                    <th className={styles.hGridStickyLabel}>Photon #</th>
                    {qkdResult.phases.transmission.log.map((_, idx) => (
                      <th key={idx} className={styles.hGridHeaderCell}>#{idx + 1}</th>
                    ))}
                  </tr>
                  <tr>
                    <th className={styles.hGridStickyLabel}>Basis</th>
                    {qkdResult.phases.transmission.log.map((entry, idx) => (
                      <td key={idx} className={`${styles.hGridCell} ${styles.hGridCellBasis} ${!isMeasured ? styles.blurredArea : ''}`}>
                        {entry.bobBasis}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <th className={styles.hGridStickyLabel}>Measure</th>
                    {qkdResult.phases.transmission.log.map((entry, idx) => (
                      <td key={idx} className={`${styles.hGridCell} ${styles.hGridCellBit} ${!isMeasured ? styles.blurredArea : ''}`}>
                        {entry.bobRead}
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          ) : (
            /* Omniscient Trace Table for System View */
            <div className={styles.logTableWrapper}>
              <table className={styles.logTable}>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Server Bit</th>
                    <th>Server Basis</th>
                    <th>Photon State</th>
                    <th className={!isMeasured ? styles.blurredArea : ''}>Voter Basis</th>
                    <th className={!isMeasured ? styles.blurredArea : ''}>Voter Read</th>
                    <th className={!isSifted ? styles.blurredArea : ''}>Basis Match</th>
                  </tr>
                </thead>
                <tbody>
                  {qkdResult.phases.transmission.log.map((entry, idx) => (
                    <tr key={idx}>
                      <td>{idx + 1}</td>
                      <td>{entry.aliceBit}</td>
                      <td>{entry.aliceBasis}</td>
                      <td className={styles.photonArrow}>{getPhotonSymbol(entry.aliceBit, entry.aliceBasis)}</td>
                      <td className={!isMeasured ? styles.blurredArea : ''}>{entry.bobBasis}</td>
                      <td className={!isMeasured ? styles.blurredArea : ''}>{entry.bobRead}</td>
                      <td className={!isSifted ? styles.blurredArea : ''}>{getKeepStatus(entry)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── CARD 2: Basis Sifting Summary & Result Panel ── */}
      {!isTransmitting && qkdResult && isSifted && (
        <div className={styles.panel}>
          <div className={styles.panelHeader}>
            <div>
              <span className={styles.panelTitle}>
                {viewMode === 'voter'
                  ? 'BASIS SIFTING (RECONCILIATION) RESULT'
                  : 'BASIS SIFTING (RECONCILIATION) RESULT'}
              </span>
              <div className={styles.subHeaderDesc}>
                {viewMode === 'voter'
                  ? 'Voter sent measurement bases to Server. Server publicly announced matching basis indices.'
                  : 'Server and Voter reconciled measurement bases over public authenticated channel.'}
              </div>
            </div>
            <span className={`${styles.statusBadge} ${styles.statusSuccess}`}>
              ✓ RECONCILIATION COMPLETE
            </span>
          </div>

          {viewMode === 'voter' ? (
            /* Voter View: Match Index Header + Horizontal Kept Grid */
            <>
              <div className={styles.hIndexMeta}>
                <span className={styles.hIndexLabel}>Match Index:</span>
                <span className={styles.hIndexValues}>
                  {matchingIndices.length > 0 ? matchingIndices.join(', ') : 'None'}
                </span>
                <span className={styles.hIndexSub}>
                  ({matchingBases} matching bits · {siftingEfficiency}% yield)
                </span>
              </div>

              <div className={styles.hGridContainer}>
                <table className={styles.hGridTable}>
                  <tbody>
                    <tr>
                      <th className={styles.hGridStickyLabel}>Kept</th>
                      {matchingEntries.map((entry) => (
                        <th key={entry.photonNumber} className={styles.hGridHeaderCell}>#{entry.photonNumber}</th>
                      ))}
                    </tr>
                    <tr>
                      <th className={styles.hGridStickyLabel}>Result</th>
                      {matchingEntries.map((entry) => (
                        <td key={entry.photonNumber} className={`${styles.hGridCell} ${styles.hGridCellBit}`} style={{ color: 'var(--color-primary)' }}>
                          {entry.bobRead}
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            /* System View: Broadcast Announcement Box & Raw Stream */
            <>
              <div className={styles.detailBox}>
                <div className={styles.detailBoxHeader}>
                  <span className={styles.detailBoxTitle}>
                    SERVER PUBLIC BROADCAST: MATCHING BASIS INDICES ({matchingIndices.length} POSITIONS)
                  </span>
                  <span className={styles.detailBoxSub}>
                    Broadcast publicly over classical channel · Client retains only these indices
                  </span>
                </div>
                <div className={styles.indicesBox}>
                  {matchingIndices.length > 0 ? matchingIndices.map(i => `#${i}`).join(', ') : 'None'}
                </div>
              </div>

              <div className={styles.detailBox}>
                <div className={styles.detailBoxHeader}>
                  <span className={styles.detailBoxTitle}>
                    RAW SIFTED KEY STREAM ({matchingBases} BITS)
                  </span>
                  <span className={styles.detailBoxSub}>
                    Formed exclusively from photons with identical basis
                  </span>
                </div>
                <div className={styles.bitstreamText}>
                  {siftedBitstring || '—'}
                </div>
              </div>
            </>
          )}

          {/* Sifting Metrics Row */}
          <div className={styles.statsRow} style={{ marginTop: '16px' }}>
            <div className={styles.statCol}>
              <span className={styles.statLabel}>Photons Received</span>
              <span className={styles.statValue}>{totalPhotons}</span>
            </div>
            <div className={styles.statCol}>
              <span className={styles.statLabel}>Matching Bases (Sifted)</span>
              <span className={`${styles.statValue} ${styles.blue}`}>
                {matchingBases} bits
                <span className={styles.statSubValue}> ({siftingEfficiency}% yield)</span>
              </span>
            </div>
            <div className={styles.statCol}>
              <span className={styles.statLabel}>Discarded Positions</span>
              <span className={styles.statValue}>
                {discardedCount} photons
                <span className={styles.statSubValue}> ({discardedPct}%)</span>
              </span>
            </div>
            <div className={styles.statCol}>
              <span className={styles.statLabel}>Target Requirement (n)</span>
              <span className={styles.statValue}>
                ≥ {state.config.targetKeyLength} bits
                <span className={styles.statSubValue} style={{ color: matchingBases >= state.config.targetKeyLength ? 'var(--color-success)' : 'var(--color-danger)' }}>
                  {' '}({matchingBases >= state.config.targetKeyLength ? '✓ Sufficient' : '⚠ Insufficient'})
                </span>
              </span>
            </div>
          </div>

          {/* Sifting Yield Ratio Bar */}
          <div className={styles.ratioBarWrap}>
            <div className={styles.ratioBarLabels}>
              <span>Basis Match Ratio: <strong>{siftingEfficiency}%</strong> (Theoretical ideal ~50%)</span>
              <span>Mismatches Discarded: <strong>{discardedPct}%</strong></span>
            </div>
            <div className={styles.ratioBarTrack}>
              <div
                className={styles.ratioBarFillPrimary}
                style={{ width: `${siftingEfficiency}%` }}
                title={`Matching bases: ${matchingBases} bits`}
              />
              <div
                className={styles.ratioBarFillMuted}
                style={{ width: `${discardedPct}%` }}
                title={`Discarded: ${discardedCount} photons`}
              />
            </div>
          </div>
        </div>
      )}

      {/* ── CARD 3: QBER Estimation & Channel Verification Panel ── */}
      {!isTransmitting && qkdResult && currentPhaseIndex >= 2 && (
        <div className={`${styles.panel} ${!qkdResult.phases.qberEstimation.passed ? styles.danger : ''}`}>
          <div className={styles.panelHeader}>
            <div>
              <span className={styles.panelTitle}>
                QBER ESTIMATION &amp; CHANNEL VERIFICATION
              </span>
              <div className={styles.subHeaderDesc}>
                {viewMode === 'voter'
                  ? 'Server announced test bit indices and disclosed bit values. Parity check verifies channel integrity.'
                  : 'Public parity comparison on sacrificed sample bits to detect quantum measurement disturbance.'}
              </div>
            </div>
            <span className={`${styles.statusBadge} ${qkdResult.phases.qberEstimation.passed ? styles.statusSuccess : styles.statusDanger}`}>
              {qkdResult.phases.qberEstimation.passed ? '✓ CHANNEL INTEGRITY VERIFIED' : '⚠ EAVESDROPPING DETECTED'}
            </span>
          </div>

          {viewMode === 'voter' ? (
            /* Voter View: Test Bits Index Header + Horizontal Test Comparison Grid */
            <>
              <div className={styles.hIndexMeta}>
                <span className={styles.hIndexLabel}>Test Bits Index:</span>
                <span className={styles.hIndexValues}>
                  {testSamples.length > 0 ? testSamples.map(s => s.photonNumber).join(', ') : 'None'}
                </span>
                <span className={styles.hIndexSub}>
                  ({testSamples.length} sample bits sacrificed)
                </span>
              </div>

              {testSamples.length > 0 && (
                <div className={styles.hGridContainer}>
                  <table className={styles.hGridTable}>
                    <tbody>
                      <tr>
                        <th className={styles.hGridStickyLabel}>Test Photon #</th>
                        {testSamples.map((sample) => (
                          <th key={sample.photonNumber} className={styles.hGridHeaderCell}>#{sample.photonNumber}</th>
                        ))}
                      </tr>
                      <tr>
                        <th className={styles.hGridStickyLabel}>Server Disclosed</th>
                        {testSamples.map((sample) => (
                          <td key={sample.photonNumber} className={`${styles.hGridCell} ${styles.hGridCellBit}`} style={{ color: 'var(--color-primary)' }}>
                            {sample.aliceBit}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <th className={styles.hGridStickyLabel}>Voter Measured</th>
                        {testSamples.map((sample) => (
                          <td key={sample.photonNumber} className={`${styles.hGridCell} ${styles.hGridCellBit}`}>
                            {sample.bobRead}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <th className={styles.hGridStickyLabel}>Result</th>
                        {testSamples.map((sample) => {
                          const isMatch = sample.aliceBit === sample.bobRead;
                          return (
                            <td key={sample.photonNumber} className={`${styles.hGridCell} ${isMatch ? styles.hGridResultO : styles.hGridResultX}`}>
                              {isMatch ? 'O' : 'X'}
                            </td>
                          );
                        })}
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}
            </>
          ) : (
            /* System View: Full Diagnostic Trace Table */
            testSamples.length > 0 && (
              <div className={styles.detailBox}>
                <div className={styles.detailBoxHeader}>
                  <span className={styles.detailBoxTitle}>
                    SACRIFICED SAMPLE VERIFICATION TRACE ({testSamples.length} BITS COMPARED)
                  </span>
                  <span className={styles.detailBoxSub}>
                    Disclosed publicly · Permanently discarded from final key
                  </span>
                </div>
                <div className={styles.sampleTableWrap}>
                  <table className={styles.sampleTable}>
                    <thead>
                      <tr>
                        <th>Sample #</th>
                        <th>Photon #</th>
                        <th>Basis</th>
                        <th>Server Sent</th>
                        <th>Voter Measured</th>
                        <th>State Match</th>
                      </tr>
                    </thead>
                    <tbody>
                      {testSamples.map((sample, sIdx) => {
                        const isMatch = sample.aliceBit === sample.bobRead;
                        return (
                          <tr key={sIdx}>
                            <td>#{sIdx + 1}</td>
                            <td>Photon #{sample.photonNumber}</td>
                            <td>{sample.aliceBasis}</td>
                            <td style={{ fontWeight: 700 }}>{sample.aliceBit}</td>
                            <td style={{ fontWeight: 700 }}>{sample.bobRead}</td>
                            <td>
                              {isMatch ? (
                                <span style={{ color: 'var(--color-success)', fontWeight: 600 }}>✓ Verified Match</span>
                              ) : (
                                <span style={{ color: 'var(--color-danger)', fontWeight: 700 }}>✕ Error (Bit Flip)</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )
          )}

          {/* QBER Metrics Row */}
          <div className={styles.statsRow} style={{ marginTop: '16px' }}>
            <div className={styles.statCol}>
              <span className={styles.statLabel}>Sample Bits Tested</span>
              <span className={styles.statValue}>
                {qkdResult.phases.qberEstimation.testBitsUsed} bits
                <span className={styles.statSubValue}> (Sacrificed)</span>
              </span>
            </div>
            <div className={styles.statCol}>
              <span className={styles.statLabel}>Sample Bit Mismatches</span>
              <span className={`${styles.statValue} ${qkdResult.phases.qberEstimation.errorsFound > 0 ? styles.danger : ''}`}>
                {qkdResult.phases.qberEstimation.errorsFound} bits
              </span>
            </div>
            <div className={styles.statCol}>
              <span className={styles.statLabel}>Measured QBER Error Rate</span>
              <span className={`${styles.statValue} ${!qkdResult.phases.qberEstimation.passed ? styles.danger : ''}`}>
                {(qkdResult.phases.qberEstimation.qber * 100).toFixed(1)}%
              </span>
            </div>
            <div className={styles.statCol}>
              <span className={styles.statLabel}>Security Threshold Limit</span>
              <span className={styles.statValue}>{(state.config.errorThreshold * 100).toFixed(0)}% (Max Acceptable)</span>
            </div>
          </div>

          {/* Visual Security Gauge Bar */}
          <div style={{ marginTop: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
              <span>Measured QBER: <strong>{(qkdResult.phases.qberEstimation.qber * 100).toFixed(1)}%</strong></span>
              <span>Security Limit: <strong>{(state.config.errorThreshold * 100).toFixed(0)}%</strong></span>
            </div>
            <div className={styles.barContainer}>
              <div
                className={styles.barFill}
                style={{
                  width: `${Math.min(100, (qkdResult.phases.qberEstimation.qber / 0.5) * 100)}%`,
                  backgroundColor: !qkdResult.phases.qberEstimation.passed ? 'var(--color-danger)' : 'var(--color-success)'
                }}
              />
              <div
                className={styles.barThresholdTick}
                style={{ left: `${(state.config.errorThreshold / 0.5) * 100}%` }}
              />
              <div
                className={styles.barThresholdLabel}
                style={{ left: `${(state.config.errorThreshold / 0.5) * 100}%` }}
              >
                limit ({(state.config.errorThreshold * 100).toFixed(0)}%)
              </div>
            </div>
          </div>

          {/* Mathematical Verification & Security Verdict Callout */}
          <div className={`${styles.verdictCallout} ${qkdResult.phases.qberEstimation.passed ? styles.success : styles.danger}`}>
            <div className={`${styles.verdictTitle} ${qkdResult.phases.qberEstimation.passed ? styles.success : styles.danger}`}>
              {qkdResult.phases.qberEstimation.passed ? (
                <>
                  <span>🛡</span>
                  <span>Channel Integrity Verdict: SECURE</span>
                </>
              ) : (
                <>
                  <span>⚠</span>
                  <span>Channel Integrity Verdict: COMPROMISED</span>
                </>
              )}
            </div>
            <div className={styles.verdictBody}>
              {qkdResult.phases.qberEstimation.passed ? (
                <>
                  Error rate formula: <code>QBER = {qkdResult.phases.qberEstimation.errorsFound} / {qkdResult.phases.qberEstimation.testBitsUsed} = {(qkdResult.phases.qberEstimation.qber * 100).toFixed(1)}%</code>.
                  Since <strong>{(qkdResult.phases.qberEstimation.qber * 100).toFixed(1)}% ≤ {(state.config.errorThreshold * 100).toFixed(0)}%</strong>, parity on publicly revealed sample bits confirms no eavesdropping disturbance. The remaining <strong>{qkdResult.phases.basisSifting.siftedKeyBits.length - qkdResult.phases.qberEstimation.testBitsUsed} sifted bits</strong> were never disclosed and remain unconditionally secret to establish the key.
                </>
              ) : (
                <>
                  Error rate formula: <code>QBER = {qkdResult.phases.qberEstimation.errorsFound} / {qkdResult.phases.qberEstimation.testBitsUsed} = {(qkdResult.phases.qberEstimation.qber * 100).toFixed(1)}%</code>.
                  Since <strong>{(qkdResult.phases.qberEstimation.qber * 100).toFixed(1)}% &gt; {(state.config.errorThreshold * 100).toFixed(0)}%</strong>, quantum measurement collapse caused by Eve's interception exceeds the maximum allowable security threshold. Key distillation cannot proceed.
                </>
              )}
            </div>
          </div>
        </div>
      )}



      {/* Abort State */}
      {!isTransmitting && qkdResult && currentPhaseIndex >= 2 && isAborted && (
        <div className={styles.alertBox}>
          <div className={styles.alertIcon}>⚠</div>
          <div className={styles.alertContent}>
            {isEveAbort ? (
              <>
                <div className={styles.alertTitle}>Session Aborted: Possible Eavesdropper Detected</div>
                <div className={styles.alertText}>
                  The measured QBER ({(qkdResult.phases.qberEstimation.qber * 100).toFixed(1)}%) exceeds the security threshold ({(state.config.errorThreshold * 100).toFixed(0)}%). This is consistent with an intercept-resend attack. The session key has been discarded and no vote can be cast.
                </div>
              </>
            ) : (
              <>
                <div className={styles.alertTitle}>Session Aborted: Insufficient Sifted Bits</div>
                <div className={styles.alertText}>
                  Basis reconciliation yielded fewer matching bits than the required 2n threshold ({qkdResult.phases.basisSifting.matchingBases} sifted bits vs {state.config.targetKeyLength * 2} required). Increase the photon transmission count or safety margin in configuration.
                </div>
              </>
            )}
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
              FINAL KEY · {qkdResult.phases.keyEstablished.keyLength} BITS · {Math.round((qkdResult.phases.keyEstablished.keyLength / (qkdResult.phases.transmission.qubitCount || calculatePhotonCount(state.config.targetKeyLength, state.config.errorTolerance))) * 100)}% CHANNEL EFFICIENCY
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
          {currentPhase === 'basisSifting' && !isMeasured && (
            <button className={styles.primaryButton} onClick={handleMeasure}>
              Measure Qubits ›
            </button>
          )}
          {currentPhase === 'basisSifting' && isMeasured && !isSifted && (
            <button className={styles.primaryButton} onClick={handleSift}>
              Sift Bases (Reconciliation) ›
            </button>
          )}
          {currentPhase === 'basisSifting' && isSifted && (
            <button className={styles.primaryButton} onClick={handleCalculateQber}>
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
