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
          binaryId: c.binaryId,
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
        sessionId: state.auth.sessionId,
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

      <h1 className={styles.title}>Cast Your Ballot</h1>
      <p className={styles.subtitle}>
        Select one candidate. Your choice is encrypted with the quantum-derived key before transmission.
      </p>

      <div className={styles.candidatesGrid}>
        {candidates.map((candidate) => (
          <div
            key={candidate.id}
            className={`${styles.candidateCard} ${selectedId === candidate.id ? styles.selected : ''
              }`}
            onClick={() => dispatch({ type: 'SELECT_VOTE_OPTION', payload: candidate.id })}
          >
            <div className={styles.candidateInfo}>
              <span className={styles.candidateName}>{candidate.name}</span>
              <span className={styles.candidateParty}>{candidate.party}</span>
              <span className={styles.candidateBinaryId}>Binary ID: {candidate.binaryId}</span>
            </div>
            <div className={`${styles.radio} ${selectedId === candidate.id ? styles.selected : ''}`}>
            </div>
          </div>
        ))}
      </div>

      {/* Encryption preview */}
      {encryption && selectedCandidate && (
        <div className={styles.encryptionPreview}>
          <div className={styles.encryptionPreviewTitle}>ONE-TIME PAD ENCRYPTION</div>

          <div className={styles.encryptionRow}>
            <span className={styles.encryptionLabel}>Vote (plaintext)</span>
            <span className={styles.encryptionValue}>{spaceBinary(encryption.voteBinary)}</span>
            <span className={styles.encryptionDesc}>Candidate {parseInt(encryption.voteBinary, 2)}</span>
          </div>

          <div className={styles.encryptionRow}>
            <span className={styles.encryptionLabel}>Key (QKD)</span>
            <span className={`${styles.encryptionValue} ${styles.qkd}`}>{spaceBinary(encryption.keyToUse)}</span>
            <span className={styles.encryptionDesc}>Quantum-derived</span>
          </div>

          <div className={styles.encryptionDivider} />

          <div className={styles.encryptionRow}>
            <span className={styles.encryptionLabel}>Encrypted vote</span>
            <span className={`${styles.encryptionValue} ${styles.encrypted}`}>{spaceBinary(encryption.encrypted)}</span>
            <span className={styles.encryptionDesc}>XOR result</span>
          </div>

          <div className={styles.encryptionFooter}>
            Only the encrypted value is transmitted. Decryption requires the matching quantum key.
          </div>
        </div>
      )}

      <div className={styles.actions}>
        <button
          className={styles.primaryButton}
          onClick={handleSubmitVote}
          disabled={!selectedId || state.vote.isSubmitting}
        >
          <span className={styles.lockIcon}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
              <path d="M7 11V7a5 5 0 0 1 9.9-1"></path>
            </svg>
          </span>
          {state.vote.isSubmitting ? 'Submitting...' : 'Submit Encrypted Ballot'}
        </button>
      </div>
    </div>
  );
}
