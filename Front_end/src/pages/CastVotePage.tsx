import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { Stepper } from '../components/layout/Stepper';
import { xorEncrypt } from '../utils/otp';
import { getMockApiService } from '../services';
import type { VoteOption } from '../types';
import styles from './CastVotePage.module.css';

export function CastVotePage() {
  const { state, dispatch, api } = useApp();
  const navigate = useNavigate();
  const [candidates, setCandidates] = useState<VoteOption[]>([]);

  useEffect(() => {
    if (state.auth.electionCode) {
      api.getCandidates(state.auth.electionCode).then(res => {
        setCandidates(res.candidates.map((c, i) => ({
          id: `candidate-${i}`,
          name: c.candidateName,
          party: c.candidateParty,
          // Generate binaryId from index as fallback if API doesn't return one
          binaryId: c.binaryId || i.toString(2).padStart(3, '0'),
          count: 0
        })));
      }).catch(err => console.error("Failed to load candidates", err));
    }
  }, [api, state.auth.electionCode]);

  const selectedId = state.vote.selectedOptionId;
  const selectedCandidate = candidates.find((c) => c.id === selectedId);
  const qkdResult = state.qkd.result;
  const otpKey = qkdResult?.phases.keyEstablished.finalKey || '';

  // Get the key portion to use for encryption. We need as many bits as the candidate's binaryId.
  // Figma shows binaryId is 3 bits ("000", "010").
  const getEncryptedVote = () => {
    if (!selectedCandidate || !otpKey) return null;
    const voteBinary = selectedCandidate.binaryId;
    if (!voteBinary) return null;
    // Just grab the first N bits of the OTP key (where N = voteBinary.length)
    const keyToUse = otpKey.substring(0, voteBinary.length).padEnd(voteBinary.length, '0');
    const encrypted = xorEncrypt(voteBinary, keyToUse);
    return { voteBinary, keyToUse, encrypted };
  };

  const encryption = selectedCandidate ? getEncryptedVote() : null;

  const handleSubmitVote = async () => {
    if (!selectedId || !encryption || !qkdResult) return;

    dispatch({
      type: 'VOTE_SUBMIT_START',
      payload: {
        encryptedVote: encryption.encrypted,
        otpKey: encryption.keyToUse,
      },
    });

    try {
      const response = await api.castVote({
        sessionId: qkdResult.sessionId,   // must match the session stored by generate-key
        voterId: state.auth.voterId,
        encryptedVote: encryption.encrypted,
      });

      if (response.success) {
        // Store vote record in mock service for results page
        const mockService = getMockApiService();
        if (mockService) {
          mockService.storeVoteRecord({
            voteId: response.voteId,
            voterId: state.auth.voterId,
            timestamp: response.timestamp,
            protocolReplay: qkdResult,
            encryptedVote: encryption.encrypted,
            plaintextVote: selectedId,
            otpKey: encryption.keyToUse,
          });
        }

        dispatch({
          type: 'VOTE_SUBMIT_SUCCESS',
          payload: { voteId: response.voteId, timestamp: response.timestamp },
        });
        navigate('/confirmation');
      }
    } catch (err) {
      dispatch({
        type: 'SET_ERROR',
        payload: err instanceof Error ? err.message : 'Vote submission failed',
      });
    }
  };

  if (!qkdResult) {
    navigate('/');
    return null;
  }

  // Helper to space out binary string like "1 0 0" for display
  const spaceBinary = (bin: string) => bin.split('').join(' ');

  return (
    <div className={styles.page}>
      <Stepper currentStep="castVote" />

      <div className={styles.headerSection}>
        <div className={styles.badgeRow}>
          <span className="quantum-badge" style={{ background: '#f0fdf4', color: '#15803d', border: '1px solid #bbf7d0' }}>
            <span className="quantum-pulse"></span> KEY DERIVED VIA BB84: READY
          </span>
        </div>
        <h1 className={styles.title}>Cast Your Secret Ballot</h1>
        <p className={styles.subtitle}>
          Select one candidate. Your vote is encrypted client-side with your single-use Quantum One-Time Pad key before network broadcast.
        </p>
      </div>

      <div className={styles.votingContainer}>
        <div className={styles.candidatesGrid}>
          {candidates.map((candidate) => {
            const isSelected = selectedId === candidate.id;
            const initials = candidate.name
              .split(' ')
              .map(n => n[0])
              .join('')
              .slice(0, 2);

            return (
              <div
                key={candidate.id}
                className={`${styles.candidateCard} ${isSelected ? styles.selected : ''}`}
                onClick={() => dispatch({ type: 'SELECT_VOTE_OPTION', payload: candidate.id })}
              >
                <div className={styles.candidateHeader}>
                  <div className={`${styles.avatar} ${isSelected ? styles.avatarSelected : ''}`}>
                    {initials}
                  </div>
                  <div className={`${styles.radio} ${isSelected ? styles.radioSelected : ''}`}>
                    {isSelected && <span className={styles.radioDot} />}
                  </div>
                </div>

                <div className={styles.candidateInfo}>
                  <span className={styles.candidateName}>{candidate.name}</span>
                  <span className={styles.candidateParty}>{candidate.party}</span>
                </div>

                <div className={styles.candidateFooter}>
                  <span className={styles.candidateBinaryLabel}>BALLOT CODE:</span>
                  <span className={styles.candidateBinaryValue}>{candidate.binaryId}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Interactive One-Time Pad XOR Encryption Visualizer */}
        {encryption && selectedCandidate ? (
          <div className={styles.encryptionCard}>
            <div className={styles.encryptionCardHeader}>
              <div className={styles.encryptionHeaderLeft}>
                <span className={styles.encryptionIcon}>🔐</span>
                <span className={styles.encryptionTitle}>CLIENT-SIDE ONE-TIME PAD (OTP) ENCRYPTION</span>
              </div>
              <span className={styles.encryptionBadge}>UNBREAKABLE (SHANNON 1949)</span>
            </div>

            <div className={styles.mathGrid}>
              <div className={styles.mathBlock}>
                <span className={styles.mathLabel}>1. Ballot Message (m)</span>
                <div className={styles.mathBits}>{spaceBinary(encryption.voteBinary)}</div>
                <span className={styles.mathSub}>"{selectedCandidate.name}"</span>
              </div>

              <div className={styles.mathOperator}>⊕</div>

              <div className={styles.mathBlock}>
                <span className={styles.mathLabel}>2. Quantum Key (k)</span>
                <div className={`${styles.mathBits} ${styles.keyBits}`}>{spaceBinary(encryption.keyToUse)}</div>
                <span className={styles.mathSub}>From BB84 Sifting</span>
              </div>

              <div className={styles.mathOperator}>=</div>

              <div className={styles.mathBlock}>
                <span className={styles.mathLabel}>3. Ciphertext (c)</span>
                <div className={`${styles.mathBits} ${styles.cipherBits}`}>{spaceBinary(encryption.encrypted)}</div>
                <span className={styles.mathSub}>Broadcasted to Ledger</span>
              </div>
            </div>

            <div className={styles.encryptionNote}>
              <span className={styles.noteIcon}>ℹ️</span>
              <span>
                Even with infinite computing power, an attacker cannot decipher the ballot because the key is truly random and used exactly once.
              </span>
            </div>
          </div>
        ) : (
          <div className={styles.placeholderCard}>
            <span className={styles.placeholderIcon}>👆</span>
            <span>Select a candidate card above to preview the real-time OTP XOR encryption.</span>
          </div>
        )}

        <div className={styles.submitBar}>
          <button
            className={styles.primaryButton}
            onClick={handleSubmitVote}
            disabled={!selectedId || state.vote.isSubmitting}
          >
            {state.vote.isSubmitting ? (
              <>
                <span className={styles.spinner}></span>
                <span>Recording Encrypted Ballot on Ledger...</span>
              </>
            ) : (
              <>
                <span className={styles.lockIcon}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                    <path d="M7 11V7a5 5 0 0 1 9.9-1"></path>
                  </svg>
                </span>
                <span>Submit Encrypted Ballot to Ledger</span>
                <span className={styles.btnArrow}>→</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
