import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { Stepper } from '../components/layout/Stepper';
import type { VoteOption } from '../types';
import styles from './ConfirmationPage.module.css';

// Same candidates array to get the name
const CANDIDATES: VoteOption[] = [
  { id: 'candidate-a', name: 'Alexandra Chen', party: 'Progressive Alliance', binaryId: '000', count: 0 },
  { id: 'candidate-b', name: 'Marcus Webb', party: 'National Coalition', binaryId: '001', count: 0 },
  { id: 'candidate-c', name: 'Priya Sharma', party: 'Reform Movement', binaryId: '010', count: 0 },
  { id: 'candidate-d', name: "James O'Brien", party: 'Citizens First', binaryId: '011', count: 0 },
];

export function ConfirmationPage() {
  const { state, dispatch } = useApp();
  const navigate = useNavigate();

  const qkdResult = state.qkd.result;
  const { vote, auth } = state;

  if (!qkdResult || !vote.voteId) {
    navigate('/');
    return null;
  }

  const selectedCandidate = CANDIDATES.find(c => c.id === vote.selectedOptionId);
  const voteBinary = selectedCandidate?.binaryId || '';

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
          <span className={styles.icon}>📊</span> View Results
        </button>
        <button className={styles.primaryButton} onClick={handleVoteAgain}>
          New Session
        </button>
      </div>
    </div>
  );
}
