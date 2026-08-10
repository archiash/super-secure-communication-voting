import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import type { ElectionResultResponse, VotingAuditResponse, VotingCandidate } from '../types';
import styles from './ResultsPage.module.css';

const CANDIDATE_COLORS: Record<string, string> = {
  'Sierra': '#3b82f6', // blue
  'Raul': '#10b981', // green
  'Gabrielle': '#8b5cf6', // purple
  'Alan': '#ea580c', // orange
};

// We extract just the last name for the chart labels
const getLastName = (name: string) => name.split(' ').pop() || name;

export function ResultsPage() {
  const { state, api } = useApp();
  const navigate = useNavigate();
  const [electionResult, setElectionResult] = useState<ElectionResultResponse | null>(null);
  const [auditLog, setAuditLog] = useState<VotingAuditResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadResults();
  }, []);

  const loadResults = async () => {
    setIsLoading(true);
    try {
      const electionCode = state.auth.electionCode || 'ELECT2026';
      const [electionData, auditData] = await Promise.all([
        api.getElectionResult(electionCode),
        api.getVotingAudit(electionCode)
      ]);

      // Sort candidates by votes descending
      electionData.candidates.sort((a, b) => b.votes - a.votes);

      setElectionResult(electionData);
      setAuditLog(auditData);
    } catch (err) {
      console.error('Failed to load results:', err);
    }
    setIsLoading(false);
  };

  if (isLoading) {
    return (
      <div className={styles.page}>
        <p>Loading results...</p>
      </div>
    );
  }

  const totalVotes = electionResult?.candidates.reduce((sum, c) => sum + c.votes, 0) || 0;

  if (!electionResult || !auditLog) {
    return (
      <div className={styles.page}>
        <div className={styles.header}>
          <div>
            <h1 className={styles.title}>Election Results</h1>
            <p className={styles.subtitle}>General Election 2026 · 0 encrypted ballots recorded</p>
          </div>
          <button className={styles.backButton} onClick={() => navigate(-1)}>
            ← Back
          </button>
        </div>
        <p>No votes have been cast yet.</p>
      </div>
    );
  }

  const maxCount = Math.max(...electionResult.candidates.map((o) => o.votes), 20); // Scale relative to at least 20

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Election Results</h1>
          <p className={styles.subtitle}>
            General Election 2026 · {totalVotes} encrypted ballot{totalVotes !== 1 ? 's' : ''} recorded
          </p>
        </div>
        <button className={styles.backButton} onClick={() => navigate(-1)}>
          ← Back
        </button>
      </div>

      <div className={styles.chartContainer}>
        <div className={styles.chartTitle}>VOTE DISTRIBUTION</div>

        {/* Vertical Bar Chart */}
        <div className={styles.chartWrapper}>
          <div className={styles.yAxis}>
            <span>{maxCount}</span>
            <span>{Math.floor(maxCount * 0.75)}</span>
            <span>{Math.floor(maxCount * 0.5)}</span>
            <span>{Math.floor(maxCount * 0.25)}</span>
            <span>0</span>
          </div>

          {electionResult.candidates.map((option) => (
            <div key={option.candidateName} className={styles.barColWrapper}>
              <div className={styles.barCol}>
                <div
                  className={styles.barFill}
                  style={{
                    height: `${(option.votes / maxCount) * 100}%`,
                    backgroundColor: CANDIDATE_COLORS[option.candidateName] || '#cbd5e1'
                  }}
                />
              </div>
              <div className={styles.barLabel}>{getLastName(option.candidateName)}</div>
            </div>
          ))}
        </div>

        {/* Candidate Table */}
        <table className={styles.candidateTable}>
          <thead>
            <tr>
              <th>RANK</th>
              <th>CANDIDATE</th>
              <th>PARTY</th>
              <th>VOTES</th>
              <th>SHARE</th>
            </tr>
          </thead>
          <tbody>
            {electionResult.candidates.map((option: VotingCandidate, index: number) => {
              const share = totalVotes > 0
                ? Math.round((option.votes / totalVotes) * 100)
                : 0;

              return (
                <tr key={option.candidateName}>
                  <td>{index + 1}</td>
                  <td className={styles.candidateNameCell}>
                    <div
                      className={styles.colorDot}
                      style={{ backgroundColor: CANDIDATE_COLORS[option.candidateName] || '#cbd5e1' }}
                    />
                    {option.candidateName}
                    {index === 0 && option.votes > 0 && (
                      <span className={styles.leadingBadge}>LEADING</span>
                    )}
                  </td>
                  <td className={styles.candidatePartyCell}>{option.candidateParty}</td>
                  <td className={styles.candidateVotesCell}>{option.votes}</td>
                  <td className={styles.candidateShareCell}>{share}%</td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {/* Toggle Audit Log */}
        {/* <button 
          className={styles.auditToggle}
          onClick={() => setShowAuditLog(!showAuditLog)}
        >
          {showAuditLog ? '👁 Hide' : '👁 Show'} Quantum Audit Log ({auditLog.sessions.length} records)
        </button> */}

        {/* Audit Log Table */}
        {/* {showAuditLog && (
          <table className={styles.auditTable}>
            <thead>
              <tr>
                <th>Session ID</th>
                <th>Voter ID</th>
                <th>Encrypted Vote</th>
                <th>Key Bits</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {auditLog.sessions.map((vote: SessionData) => (
                <tr key={vote.sessionId}>
                  <td className={styles.mono}>{vote.sessionId}</td>
                  <td className={styles.mono}>{vote.voterId}</td>
                  <td className={`${styles.mono} ${styles.blue}`}>{vote.encryptedVote}</td>
                  <td className={styles.mono}>{vote.keyBits}</td>
                  <td>{new Date(vote.timeStamp).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )} */}
      </div>
    </div>
  );
}
