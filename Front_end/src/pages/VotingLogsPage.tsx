import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import type { VotingLogEntry } from '../types';
import styles from './VotingLogsPage.module.css';

export function VotingLogsPage() {
  const { state, api } = useApp();
  const navigate = useNavigate();
  const [logs, setLogs] = useState<VotingLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'VOTE_CAST' | 'KEY_GENERATED' | 'ABORTED'>('ALL');
  const [selectedLog, setSelectedLog] = useState<VotingLogEntry | null>(null);

  const electionCode = state.auth.electionCode || 'ELECT2026';

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await api.getVotingLogs(electionCode);
      setLogs(res.logs || []);
    } catch (err) {
      console.error('Failed to fetch voting logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [electionCode]);

  const filteredLogs = logs.filter((log) => {
    const matchesSearch =
      log.sessionId.toLowerCase().includes(search.toLowerCase()) ||
      log.voterId.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || log.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const totalSessions = logs.length;
  const votesCastCount = logs.filter((l) => l.status === 'VOTE_CAST').length;
  const keysCount = logs.filter((l) => l.status === 'KEY_GENERATED' || l.status === 'VOTE_CAST').length;
  const abortedCount = logs.filter((l) => l.status === 'ABORTED').length;
  const avgQber = logs.length
    ? (logs.reduce((acc, l) => acc + l.qberPercent, 0) / logs.length).toFixed(1)
    : '0.0';

  const formatTimestamp = (ts: number) => {
    if (!ts) return 'N/A';
    const date = new Date(ts * 1000);
    return date.toLocaleString();
  };

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>
            QKD BB84 Quantum Simulation Report
          </h1>
          <p className={styles.subtitle}>
            Detailed audit report of simulated Quantum Key Distribution (BB84) execution. Displays internal quantum state diagnostics, photon polarization states, measurement bases, quantum bit error rates (QBER), and key exchange results for Election: <strong>{electionCode}</strong>.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button className={styles.refreshButton} onClick={() => navigate('/')}>
            ← Back to Home
          </button>
          <button className={styles.refreshButton} onClick={fetchLogs} disabled={loading}>
            <span>↻</span> {loading ? 'Refreshing...' : 'Refresh Logs'}
          </button>
        </div>
      </div>

      {/* Summary Statistics */}
      <div className={styles.statsGrid}>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Total QKD Sessions</span>
          <div className={styles.statValue}>{totalSessions}</div>
          <div className={styles.statSubtext}>Initiated voting workflows</div>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Ballots Cast</span>
          <div className={styles.statValue} style={{ color: 'var(--color-success)' }}>{votesCastCount}</div>
          <div className={styles.statSubtext}>Encrypted vote submitted</div>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Keys Established</span>
          <div className={styles.statValue} style={{ color: 'var(--color-accent)' }}>{keysCount}</div>
          <div className={styles.statSubtext}>Valid OTP keys generated</div>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Aborted Sessions</span>
          <div className={styles.statValue} style={{ color: 'var(--color-danger)' }}>{abortedCount}</div>
          <div className={styles.statSubtext}>QBER &gt; 11% threshold</div>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Average QBER</span>
          <div className={styles.statValue}>{avgQber}%</div>
          <div className={styles.statSubtext}>Quantum Bit Error Rate</div>
        </div>
      </div>

      {/* Controls & Search */}
      <div className={styles.controlsRow}>
        <div className={styles.searchBox}>
          <span className={styles.searchIcon}>🔍</span>
          <input
            type="text"
            className={styles.searchInput}
            placeholder="Search by Session ID or Voter ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className={styles.filterGroup}>
          <button
            className={`${styles.filterButton} ${statusFilter === 'ALL' ? styles.active : ''}`}
            onClick={() => setStatusFilter('ALL')}
          >
            All ({logs.length})
          </button>
          <button
            className={`${styles.filterButton} ${statusFilter === 'VOTE_CAST' ? styles.active : ''}`}
            onClick={() => setStatusFilter('VOTE_CAST')}
          >
            Vote Cast ({votesCastCount})
          </button>
          <button
            className={`${styles.filterButton} ${statusFilter === 'KEY_GENERATED' ? styles.active : ''}`}
            onClick={() => setStatusFilter('KEY_GENERATED')}
          >
            Key Ready ({logs.filter(l => l.status === 'KEY_GENERATED').length})
          </button>
          <button
            className={`${styles.filterButton} ${statusFilter === 'ABORTED' ? styles.active : ''}`}
            onClick={() => setStatusFilter('ABORTED')}
          >
            Aborted ({abortedCount})
          </button>
        </div>
      </div>

      {/* Logs Table */}
      <div className={styles.tableCard}>
        <div className={styles.tableWrapper}>
          <table className={styles.logsTable}>
            <thead>
              <tr>
                <th>Session ID</th>
                <th>Voter ID</th>
                <th>QBER</th>
                <th>Status</th>
                <th>OTP Key Generated</th>
                <th>Timestamp</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={7} className={styles.emptyState}>
                    {loading ? 'Loading QKD session logs...' : 'No voting session logs found.'}
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => {
                  const isHighQber = log.qberPercent > log.thresholdPercent;
                  return (
                    <tr key={log.sessionId}>
                      <td className={styles.sessionId}>{log.sessionId}</td>
                      <td className={styles.voterId}>{log.voterId}</td>
                      <td>
                        <span className={`${styles.qberBadge} ${isHighQber ? styles.qberHigh : styles.qberGood}`}>
                          {log.qberPercent.toFixed(1)}%
                        </span>
                      </td>
                      <td>
                        {log.status === 'VOTE_CAST' && (
                          <span className={`${styles.statusBadge} ${styles.statusVoteCast}`}>
                            ✓ Vote Cast
                          </span>
                        )}
                        {log.status === 'KEY_GENERATED' && (
                          <span className={`${styles.statusBadge} ${styles.statusKeyGenerated}`}>
                            🔑 Key Ready
                          </span>
                        )}
                        {log.status === 'ABORTED' && (
                          <span className={`${styles.statusBadge} ${styles.statusAborted}`}>
                            ⚠ Aborted
                          </span>
                        )}
                      </td>
                      <td>
                        <span className={styles.keyBits}>
                          {log.keyGenerated ? log.keyGenerated : '—'}
                        </span>
                      </td>
                      <td>{formatTimestamp(log.timestamp)}</td>
                      <td>
                        <button className={styles.inspectButton} onClick={() => setSelectedLog(log)}>
                          Inspect BB84
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Inspect BB84 Detail Modal */}
      {selectedLog && (
        <div className={styles.modalBackdrop} onClick={() => setSelectedLog(null)}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h3 className={styles.modalTitle}>
                BB84 QKD Simulation Trace — <span className={styles.sessionId}>{selectedLog.sessionId}</span>
              </h3>
              <button className={styles.modalClose} onClick={() => setSelectedLog(null)}>
                ✕
              </button>
            </div>
            <div className={styles.modalBody}>
              <div style={{ padding: '10px 14px', backgroundColor: 'var(--color-accent-light)', border: '1px solid var(--color-border-light)', borderRadius: 'var(--radius-md)', fontSize: '12px', color: 'var(--color-accent)', display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span>ℹ</span>
                <span><strong>Simulation Diagnostic Trace:</strong> In a physical QKD hardware implementation, quantum states collapse upon measurement and cannot be inspected in transit. This report provides internal diagnostic data captured from the QKD simulator.</span>
              </div>
              <div className={styles.detailGrid}>
                <div className={styles.detailBlock}>
                  <span className={styles.detailLabel}>Voter ID</span>
                  <span className={styles.detailValue}>{selectedLog.voterId}</span>
                </div>
                <div className={styles.detailBlock}>
                  <span className={styles.detailLabel}>Status</span>
                  <span className={styles.detailValue}>{selectedLog.status}</span>
                </div>
                <div className={styles.detailBlock}>
                  <span className={styles.detailLabel}>QBER Error Rate</span>
                  <span className={styles.detailValue} style={{ color: selectedLog.qberPercent > 11 ? 'var(--color-danger)' : 'var(--color-success)' }}>
                    {selectedLog.qberPercent.toFixed(1)}% (Limit: {selectedLog.thresholdPercent}%)
                  </span>
                </div>
                <div className={styles.detailBlock}>
                  <span className={styles.detailLabel}>Timestamp</span>
                  <span className={styles.detailValue}>{formatTimestamp(selectedLog.timestamp)}</span>
                </div>
              </div>

              <div>
                <div className={styles.sectionHeader}>
                  Generated OTP Key
                </div>
                <div className={styles.keyBits} style={{ width: '100%', maxWidth: 'none', padding: '10px 14px', fontSize: '13px' }}>
                  {selectedLog.keyGenerated || 'Key Generation Aborted'}
                </div>
              </div>

              {selectedLog.encryptedVote && (
                <div>
                  <div className={styles.sectionHeader}>
                    Encrypted Ballot Ciphertext
                  </div>
                  <div className={styles.keyBits} style={{ width: '100%', maxWidth: 'none', padding: '10px 14px', fontSize: '13px', color: 'var(--color-accent)', background: 'var(--color-accent-light)' }}>
                    {selectedLog.encryptedVote}
                  </div>
                </div>
              )}

              {/* Transmission Sequence Table */}
              <div>
                <div className={styles.sectionHeader}>
                  BB84 Qubit Basis & Bit Sequence
                </div>
                <div style={{ maxHeight: '220px', overflowY: 'auto', border: '1px solid var(--color-border-light)', borderRadius: 'var(--radius-md)' }}>
                  <table className={styles.photonTable}>
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Alice Bit</th>
                        <th>Alice Basis</th>
                        <th>Bob Basis</th>
                        <th>Bob Read</th>
                        <th>Basis Match</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Array.from({ length: Math.min(32, selectedLog.aliceBit?.length || 0) }).map((_, i) => {
                        const aBit = selectedLog.aliceBit[i] || '0';
                        const aBasis = selectedLog.aliceBasis[i] === '0' ? '+' : '×';
                        const bBasis = selectedLog.bobBasis[i] === '0' ? '+' : '×';
                        const bRead = selectedLog.bobRead[i] || '0';
                        const isMatch = aBasis === bBasis;

                        return (
                          <tr key={i} className={isMatch ? styles.matchingRow : styles.mismatchRow}>
                            <td>{i + 1}</td>
                            <td>{aBit}</td>
                            <td>{aBasis}</td>
                            <td>{bBasis}</td>
                            <td>{bRead}</td>
                            <td>{isMatch ? '✓ Kept' : '✕ Discarded'}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
