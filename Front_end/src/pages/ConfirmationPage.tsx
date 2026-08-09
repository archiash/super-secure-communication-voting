import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { Stepper } from '../components/layout/Stepper';
import type { VoteOption } from '../types';
import styles from './ConfirmationPage.module.css';

export function ConfirmationPage() {
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
          binaryId: c.binaryId || i.toString(2).padStart(3, '0'),
          count: 0
        })));
      }).catch(err => console.error('Failed to load candidates', err));
    }
  }, [api, state.auth.electionCode]);

  const qkdResult = state.qkd.result;
  const { vote, auth } = state;

  if (!qkdResult || !vote.voteId) {
    navigate('/');
    return null;
  }

  const selectedCandidate = candidates.find(c => c.id === vote.selectedOptionId);
  const voteBinary = selectedCandidate?.binaryId || vote.otpKey?.substring(0, 3) || '';

  const handleVoteAgain = () => {
    dispatch({ type: 'RESET_SESSION' });
    navigate('/');
  };

  const handleViewResults = () => {
    navigate('/results');
  };

  return (
    <div className={styles.page}>
      <Stepper currentStep="confirmation" />

      <div className={styles.successBanner}>
        <div className={styles.successIcon}>✓</div>
        <div className={styles.successText}>
          <h2>Ballot Submitted</h2>
          <p>
            Your encrypted vote has been recorded on the quantum-secured ledger.
          </p>
        </div>
      </div>

      <div className={styles.receiptCard}>
        <div className={styles.receiptHeader}>
          <span className={styles.receiptTitle}>BALLOT RECEIPT</span>
          <span className={styles.receiptTime}>
            {vote.timestamp ? new Date(vote.timestamp).toLocaleString() : ''}
          </span>
        </div>

        <div className={styles.receiptRow}>
          <span className={styles.receiptLabel}>Voter ID</span>
          <span className={styles.receiptValue}>{auth.voterId}</span>
        </div>
        <div className={styles.receiptRow}>
          <span className={styles.receiptLabel}>Session ID</span>
          <span className={`${styles.receiptValue} ${styles.mono}`}>{auth.sessionId}</span>
        </div>
        <div className={styles.receiptRow}>
          <span className={styles.receiptLabel}>Vote (plaintext)</span>
          <span className={`${styles.receiptValue} ${styles.mono}`}>{voteBinary}</span>
        </div>
        <div className={styles.receiptRow}>
          <span className={styles.receiptLabel}>Key bits used</span>
          <span className={`${styles.receiptValue} ${styles.mono}`}>{vote.otpKey}</span>
        </div>
        <div className={styles.receiptRow}>
          <span className={styles.receiptLabel}>Encrypted vote</span>
          <span className={`${styles.receiptValue} ${styles.mono}`}>{vote.encryptedVote}</span>
        </div>
        <div className={styles.receiptRow}>
          <span className={styles.receiptLabel}>Candidate</span>
          <span className={styles.receiptValue}>{selectedCandidate?.name}</span>
        </div>
      </div>

      <div className={styles.warningBox}>
        <strong>Prototype note:</strong> Plaintext vote and key bits shown for demonstration only. A production system stores only the encrypted value.
      </div>

      <div className={styles.actions}>
        <button className={styles.secondaryButton} onClick={handleViewResults}>
          <span className={styles.icon}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="20" x2="18" y2="10"></line>
              <line x1="12" y1="20" x2="12" y2="4"></line>
              <line x1="6" y1="20" x2="6" y2="14"></line>
            </svg>
          </span> View Results
        </button>
        <button className={styles.primaryButton} onClick={handleVoteAgain}>
          New Session
        </button>
      </div>
    </div>
  );
}
