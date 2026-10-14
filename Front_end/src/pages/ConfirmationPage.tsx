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

  const [copied, setCopied] = useState(false);

  const handleCopyReceipt = () => {
    const text = `BALLOT VERIFICATION RECEIPT
Election: ${auth.electionCode || 'ELECT2026'}
Session ID: ${auth.sessionId}
Voter ID: ${auth.voterId}
Encrypted Payload: ${vote.encryptedVote}
Key Bits Used: ${vote.otpKey}
Timestamp: ${vote.timestamp ? new Date(vote.timestamp).toISOString() : new Date().toISOString()}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

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

      <div className={styles.receiptContainer}>
        <div className={styles.successBanner}>
          <div className={styles.successIcon}>✓</div>
          <div className={styles.successText}>
            <h2>Ballot Recorded & Sealed</h2>
            <p>
              Your encrypted vote was accepted by the consensus ledger and protected by an unconditional One-Time Pad key.
            </p>
          </div>
        </div>

        <div className={styles.certificate}>
          <div className={styles.certificateHeader}>
            <div className={styles.certSeal}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                <polyline points="9 11 12 14 22 4"></polyline>
              </svg>
            </div>
            <div className={styles.certTitleGroup}>
              <span className={styles.certSuper}>OFFICIAL VERIFICATION PROOF</span>
              <h3 className={styles.certTitle}>Cryptographic Ballot Receipt</h3>
            </div>
            <button className={styles.copyBtn} onClick={handleCopyReceipt}>
              {copied ? '✓ Copied' : '📋 Copy Receipt'}
            </button>
          </div>

          <div className={styles.certBody}>
            <div className={styles.certRow}>
              <span className={styles.certLabel}>Election ID</span>
              <span className={styles.certValue}>{auth.electionCode || 'ELECT2026'}</span>
            </div>

            <div className={styles.certRow}>
              <span className={styles.certLabel}>Voter Identifier</span>
              <span className={styles.certValue}>{auth.voterId}</span>
            </div>

            <div className={styles.certRow}>
              <span className={styles.certLabel}>Session Token</span>
              <span className={`${styles.certValue} ${styles.mono}`}>{auth.sessionId}</span>
            </div>

            <div className={styles.certRow}>
              <span className={styles.certLabel}>Timestamp (UTC)</span>
              <span className={styles.certValue}>
                {vote.timestamp ? new Date(vote.timestamp).toUTCString() : new Date().toUTCString()}
              </span>
            </div>

            <div className={styles.certRowHighlight}>
              <div className={styles.highlightLeft}>
                <span className={styles.certLabel}>Encrypted Ciphertext (c)</span>
                <span className={styles.certHint}>Committed permanently to public ballot ledger</span>
              </div>
              <span className={`${styles.cipherTag} ${styles.mono}`}>{vote.encryptedVote}</span>
            </div>

            <div className={styles.certRow}>
              <span className={styles.certLabel}>Quantum Key Bits Used</span>
              <span className={`${styles.certValue} ${styles.mono}`}>{vote.otpKey}</span>
            </div>

            <div className={styles.certRow}>
              <span className={styles.certLabel}>Plaintext Vote Bitstring</span>
              <span className={`${styles.certValue} ${styles.mono}`}>{voteBinary}</span>
            </div>

            <div className={styles.certRow}>
              <span className={styles.certLabel}>Candidate Voted For</span>
              <span className={styles.certValue}>{selectedCandidate?.name || 'Candidate (Registered)'}</span>
            </div>
          </div>

          <div className={styles.certFooter}>
            <span className={styles.watermark}>QUANTUM-VERIFIED LEDGER ENTRY</span>
            <span className={styles.disclaimer}>
              Demo note: Plaintext vote & key bits are shown for verification illustration. In production, only the encrypted ciphertext is saved.
            </span>
          </div>
        </div>

        <div className={styles.actions}>
          <button className={styles.secondaryButton} onClick={handleViewResults}>
            <span>View Election Audit & Results</span>
            <span>→</span>
          </button>
          <button className={styles.primaryButton} onClick={handleVoteAgain}>
            <span>Cast Ballot with New Session</span>
            <span>↺</span>
          </button>
        </div>
      </div>
    </div>
  );
}
