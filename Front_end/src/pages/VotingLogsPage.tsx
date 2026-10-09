import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import type { VotingLogEntry } from '../types';
import styles from './VotingLogsPage.module.css';

type ViewMode = 'practical' | 'system';

// ── Helpers ────────────────────────────────────────────────────────────────

function parseBit(ch: string): 0 | 1 {
  return ch === '1' ? 1 : 0;
}

function parseBasis(ch: string): '+' | '×' {
  return ch === '0' ? '+' : '×';
}

/** Strip the "0b" prefix that the backend adds to binary strings */
function stripBinPrefix(s: string): string {
  return s && s.startsWith('0b') ? s.slice(2) : (s || '');
}

function getPhotonSymbol(bit: 0 | 1, basis: '+' | '×'): string {
  if (basis === '+') return bit === 1 ? '↑' : '→';
  return bit === 1 ? '↖' : '↗';
}

// ── ViewToggle component ───────────────────────────────────────────────────

function ViewToggle({
  view,
  onChange,
}: {
  view: ViewMode;
  onChange: (v: ViewMode) => void;
}) {
  return (
    <div className={styles.viewToggleWrap}>
      <button
        className={`${styles.viewToggleBtn} ${view === 'practical' ? styles.viewToggleActive : ''}`}
        onClick={() => onChange('practical')}
      >
        <span className={styles.viewToggleLabel}>Practical view</span>
        <span className={styles.viewToggleSub}>Alice &amp; Bob</span>
      </button>
      <button
        className={`${styles.viewToggleBtn} ${view === 'system' ? styles.viewToggleActive : ''}`}
        onClick={() => onChange('system')}
      >
        <span className={styles.viewToggleLabel}>System view</span>
        <span className={styles.viewToggleSub}>Ground truth</span>
      </button>
    </div>
  );
}

// ── TransmissionTable component ────────────────────────────────────────────

type Actor = 'alice' | 'eve' | 'bob';

function TransmissionTable({
  log,
  view,
}: {
  log: VotingLogEntry;
  view: ViewMode;
}) {
  const [shown, setShown] = useState<Set<Actor>>(
    view === 'practical' ? new Set(['alice', 'bob']) : new Set(['alice', 'eve', 'bob'])
  );

  // Reset when view changes
  useEffect(() => {
    setShown(
      view === 'practical'
        ? new Set(['alice', 'bob'])
        : new Set(['alice', 'eve', 'bob'])
    );
  }, [view]);

  const toggleActor = (actor: Actor) => {
    if (view === 'practical' && actor === 'eve') return; // Eve hidden in practical
    // Prevent removing the last visible actor
    if (shown.has(actor) && shown.size === 1) return;
    setShown((prev) => {
      const next = new Set(prev);
      if (next.has(actor)) {
        next.delete(actor);
      } else {
        next.add(actor);
      }
      return next;
    });
  };

  // Strip "0b" prefix the real API adds to all binary strings
  const rawAliceBit    = stripBinPrefix(log.aliceBit);
  const rawAliceBasis  = stripBinPrefix(log.aliceBasis);
  const rawBobBasis    = stripBinPrefix(log.bobBasis);
  const rawBobRead     = stripBinPrefix(log.bobRead);
  const rawEveRead     = log.eveRead  ? stripBinPrefix(log.eveRead)  : '';
  const rawEveBasis    = log.eveBasis ? stripBinPrefix(log.eveBasis) : '';

  const len = rawAliceBit.length || 0;

  // Use real Eve data from API when available, otherwise no Eve rows
  const hasEveData = !!(rawEveRead && rawEveBasis && rawEveRead.length > 0);

  // Build per-qubit data
  const qubits = Array.from({ length: len }, (_, i) => {
    const aBit   = parseBit(rawAliceBit[i]   || '0');
    const aBasis = parseBasis(rawAliceBasis[i] || '0');
    const bBasis = parseBasis(rawBobBasis[i]   || '0');
    const bRead  = parseBit(rawBobRead[i]     || '0');

    // Eve data: use real API values when present
    const eveBasisChar = hasEveData ? parseBasis(rawEveBasis[i] || '0') : aBasis;
    const eveBit       = hasEveData ? parseBit(rawEveRead[i]   || '0') : aBit;

    const sameBasis = aBasis === bBasis;
    const bitMatch  = aBit === bRead;
    const isTest    = log.selectedBits?.includes(i) || false;
    const isKept    = sameBasis && !isTest;
    const isError   = sameBasis && !bitMatch;

    return {
      aBit, aBasis,
      photon: getPhotonSymbol(aBit, aBasis),
      eveBasis: eveBasisChar, eveBit,
      evePhoton: getPhotonSymbol(eveBit, eveBasisChar),
      bBasis, bRead,
      sameBasis, isKept, isError, isTest,
    };
  });

  const matchingBases   = qubits.filter(q => q.sameBasis).length;
  const errorsInSifted  = qubits.filter(q => q.isError).length;
  // Count Eve-intercepted qubits: length of eveRead (stripped) if present
  const eveIntercepted  = hasEveData ? rawEveRead.length : 0;

  const actorColor: Record<Actor, string> = {
    alice: '#2563eb',
    eve: '#dc2626',
    bob: '#16a34a',
  };

  const actorLabel: Record<Actor, string> = {
    alice: 'Alice',
    eve: 'Eve',
    bob: 'Bob',
  };

  return (
    <div className={styles.txTableWrap}>
      {/* Header */}
      <div className={styles.txTableHeader}>
        <span className={styles.txTableTitle}>
          QUBIT TRANSMISSION LOG · {view === 'practical' ? 'PRACTICAL VIEW' : 'SYSTEM VIEW'}
        </span>
        <span className={styles.txTableStats}>
          {len} photons · {matchingBases} matching bases
        </span>
      </div>

      {/* Actor filter buttons */}
      <div className={styles.txActorRow}>
        <span className={styles.txActorLabel}>SHOW</span>
        {(['alice', ...(view === 'system' ? ['eve'] : []), 'bob'] as Actor[]).map((actor) => {
          const active = shown.has(actor);
          // Last remaining actor — cannot be deselected
          const isLastActive = active && shown.size === 1;
          return (
            <button
              key={actor}
              className={styles.txActorBtn}
              style={{
                borderColor: actorColor[actor],
                // Active: slightly transparent background so text stays readable
                backgroundColor: active
                  ? `color-mix(in srgb, ${actorColor[actor]} 75%, transparent)`
                  : 'transparent',
                color: active ? '#fff' : actorColor[actor],
                // Last actor: not-allowed cursor
                cursor: isLastActive ? 'not-allowed' : 'pointer',
              }}
              onClick={() => toggleActor(actor)}
            >
              <span
                className={styles.txActorDot}
                style={{ backgroundColor: actorColor[actor] }}
              />
              {actorLabel[actor]}
            </button>
          );
        })}
      </div>

      {/* Scrollable table */}
      <div className={styles.txScrollWrap}>
        <table className={styles.txTable}>
          <thead>
            <tr>
              <td className={styles.txRowLabel} />
              {qubits.map((_, i) => (
                <th key={i} className={styles.txColNum}>{i + 1}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* ── Alice rows ── */}
            {shown.has('alice') && (
              <>
                <tr>
                  <td className={styles.txRowLabel}>
                    <span style={{ color: actorColor.alice }}>● Alice</span> Bit sent
                  </td>
                  {qubits.map((q, i) => (
                    <td key={i} className={styles.txCell}>
                      <span
                        className={styles.txBit}
                        style={{ backgroundColor: q.aBit === 1 ? actorColor.alice : 'transparent', color: q.aBit === 1 ? '#fff' : 'inherit' }}
                      >
                        {q.aBit}
                      </span>
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className={styles.txRowLabel}>
                    <span className={styles.txDim}>●</span> Basis
                  </td>
                  {qubits.map((q, i) => (
                    <td key={i} className={`${styles.txCell} ${styles.txDim}`}>{q.aBasis}</td>
                  ))}
                </tr>
                <tr>
                  <td className={styles.txRowLabel}>
                    <span className={styles.txDim}>●</span> Photon sent
                  </td>
                  {qubits.map((q, i) => (
                    <td key={i} className={`${styles.txCell} ${styles.txDim}`}>{q.photon}</td>
                  ))}
                </tr>
              </>
            )}

            {/* ── Eve rows (system view only, only when real Eve data exists) ── */}
            {view === 'system' && shown.has('eve') && hasEveData && (
              <>
                <tr>
                  <td className={styles.txRowLabel}>
                    <span style={{ color: actorColor.eve }}>● Eve</span> Basis
                  </td>
                  {qubits.map((q, i) => (
                    <td key={i} className={`${styles.txCell} ${styles.txDim}`}>{q.eveBasis}</td>
                  ))}
                </tr>
                <tr>
                  <td className={styles.txRowLabel}>
                    <span className={styles.txDim} style={{ color: actorColor.eve }}>●</span> Bit measured
                  </td>
                  {qubits.map((q, i) => (
                    <td key={i} className={styles.txCell}>
                      <span
                        className={styles.txBit}
                        style={{ backgroundColor: q.eveBit === 1 ? actorColor.eve : 'transparent', color: q.eveBit === 1 ? '#fff' : 'inherit' }}
                      >
                        {q.eveBit}
                      </span>
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className={styles.txRowLabel}>
                    <span className={styles.txDim} style={{ color: actorColor.eve }}>●</span> Photon resent
                  </td>
                  {qubits.map((q, i) => (
                    <td key={i} className={`${styles.txCell} ${styles.txDim}`} style={{ color: actorColor.eve }}>{q.evePhoton}</td>
                  ))}
                </tr>
              </>
            )}

            {/* ── Bob rows ── */}
            {shown.has('bob') && (
              <>
                <tr>
                  <td className={styles.txRowLabel}>
                    <span style={{ color: actorColor.bob }}>● Bob</span> Basis
                  </td>
                  {qubits.map((q, i) => (
                    <td key={i} className={`${styles.txCell} ${styles.txDim}`}>{q.bBasis}</td>
                  ))}
                </tr>
                <tr>
                  <td className={styles.txRowLabel}>
                    <span className={styles.txDim} style={{ color: actorColor.bob }}>●</span> Bit measured
                  </td>
                  {qubits.map((q, i) => (
                    <td key={i} className={styles.txCell}>
                      <span
                        className={styles.txBit}
                        style={{
                          backgroundColor: q.bRead === 1 ? actorColor.bob : 'transparent',
                          color: q.bRead === 1 ? '#fff' : 'inherit',
                          outline: q.isError ? `2px solid ${actorColor.eve}` : undefined,
                        }}
                      >
                        {q.bRead}
                      </span>
                    </td>
                  ))}
                </tr>
              </>
            )}

            {/* ── Bases match row ── only in system view, or practical with BOTH alice+bob visible */}
            {(view === 'system' || (shown.has('alice') && shown.has('bob'))) && (
              <tr>
                <td className={styles.txRowLabel}>Bases match</td>
                {qubits.map((q, i) => (
                  <td key={i} className={`${styles.txCell} ${styles.txDim}`}>
                    {q.sameBasis
                      ? <span style={{ color: '#16a34a' }}>✓</span>
                      : <span>✗</span>}
                  </td>
                ))}
              </tr>
            )}

            {/* ── Public check row ── only in system view, or practical with BOTH alice+bob visible */}
            {(view === 'system' || (shown.has('alice') && shown.has('bob'))) && (
              <tr>
                <td className={styles.txRowLabel}>Public check</td>
                {qubits.map((q, i) => (
                  <td key={i} className={`${styles.txCell} ${styles.txDim}`} style={{ fontSize: '11px' }}>
                    {q.sameBasis ? (
                      q.isTest ? (
                        <span style={{ color: q.isError ? '#dc2626' : '#d97706' }}>
                          {q.isError ? 'err' : 'chk'}
                        </span>
                      ) : (
                        'key'
                      )
                    ) : '–'}
                  </td>
                ))}
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className={styles.txLegend}>
        <span>+ rectilinear · × diagonal basis</span>
        <span>→ ↑ ↖ ↗ photon polarization</span>
        {view === 'system' && hasEveData && (
          <span>
            Eve intercepted <strong>{eveIntercepted}/{len}</strong>
          </span>
        )}
        <span>
          Errors in {view === 'system' ? 'all' : 'check'} sifted bits{' '}
          <strong style={{ color: errorsInSifted > 0 ? '#dc2626' : 'inherit' }}>
            {errorsInSifted}
          </strong>
        </span>
      </div>
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────

export function VotingLogsPage() {
  const { state, api } = useApp();
  const navigate = useNavigate();
  const [logs, setLogs] = useState<VotingLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'VOTE_CAST' | 'KEY_GENERATED' | 'KEY_READY' | 'ABORTED'>('ALL');
  const [selectedLog, setSelectedLog] = useState<VotingLogEntry | null>(null);

  // View modes
  const [reportView, setReportView] = useState<ViewMode>('practical');
  const [modalView, setModalView] = useState<ViewMode>('practical');

  const electionCode = state.auth.electionCode || 'ELECT2026';

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await api.getVotingLogs(electionCode);
      setLogs(res.sessions || []);
    } catch (err) {
      console.error('Failed to fetch voting logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [electionCode]);

  // Reset modal view to practical when a new log is selected
  useEffect(() => {
    if (selectedLog) setModalView('practical');
  }, [selectedLog]);

  // Normalize status: API may return "VOTE_CAST", "KEY READY", "KEY_GENERATED", "ABORTED", etc.
  const normalizeStatus = (status: string) => status.replace(/\s+/g, '_').toUpperCase();

  const filteredLogs = logs.filter((log) => {
    const matchesSearch =
      log.sessionId.toLowerCase().includes(search.toLowerCase()) ||
      log.voterId.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || normalizeStatus(log.status) === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const totalSessions = logs.length;
  const votesCastCount = logs.filter((l) => normalizeStatus(l.status) === 'VOTE_CAST').length;
  const keysCount = logs.filter((l) => {
    const s = normalizeStatus(l.status);
    return s === 'KEY_GENERATED' || s === 'KEY_READY' || s === 'VOTE_CAST';
  }).length;
  const abortedCount = logs.filter((l) => normalizeStatus(l.status) === 'ABORTED').length;
  // Average QBER: use practical or system depending on report view
  const avgQber = logs.length
    ? (logs.reduce((acc, l) => acc + (reportView === 'practical' ? l.qberPractical : l.qberSystem), 0) / logs.length).toFixed(1)
    : '0.0';

  const formatTimestamp = (ts: number) => {
    if (!ts) return 'N/A';
    // Handle cases where the backend just sends a year number (like 2026)
    if (ts < 10000) return ts.toString();
    const date = new Date(ts * 1000);
    return date.toLocaleString();
  };

  // Render QBER badge: practical uses qberPractical, system uses qberSystem
  const renderQberCell = (log: VotingLogEntry) => {
    const qber = reportView === 'practical' ? log.qberPractical : log.qberSystem;
    const isHighQber = qber > log.thresholdPercent;
    const pct = qber.toFixed(0);
    return (
      <span className={`${styles.qberBadge} ${isHighQber ? styles.qberHigh : styles.qberGood}`}>
        {reportView === 'practical' ? `${pct}% (Practical)` : `${pct}%`}
      </span>
    );
  };

  // Status: normalize API status strings before matching
  const renderStatusCell = (log: VotingLogEntry) => {
    const ns = log.status.replace(/\s+/g, '_').toUpperCase();
    if (reportView === 'practical') {
      if (ns === 'VOTE_CAST') return <span className={`${styles.statusBadge} ${styles.statusVoteCast}`}>✓ Vote Cast</span>;
      if (ns === 'KEY_GENERATED' || ns === 'KEY_READY') return <span className={`${styles.statusBadge} ${styles.statusKeyGenerated}`}>🔑 Key Ready</span>;
      if (ns === 'ABORTED') return <span className={`${styles.statusBadge} ${styles.statusAborted}`}>⚠ Aborted</span>;
      // Fallback for unknown statuses
      return <span className={`${styles.statusBadge} ${styles.statusKeyGenerated}`}>{log.status}</span>;
    } else {
      if (ns === 'VOTE_CAST') return <span className={`${styles.statusBadge} ${styles.statusVoteCast}`}>✓ VOTE_CAST</span>;
      if (ns === 'KEY_GENERATED' || ns === 'KEY_READY') return <span className={`${styles.statusBadge} ${styles.statusKeyGenerated}`}>🔑 KEY_GENERATED</span>;
      if (ns === 'ABORTED') return <span className={`${styles.statusBadge} ${styles.statusAborted}`}>⚠ ABORTED</span>;
      return <span className={`${styles.statusBadge} ${styles.statusKeyGenerated}`}>{log.status}</span>;
    }
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
          {/* ── Practical / System toggle below description ── */}
          <ViewToggle view={reportView} onChange={setReportView} />
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
          <div className={styles.statSubtext}>QBER &gt; threshold</div>
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
          <button className={`${styles.filterButton} ${statusFilter === 'ALL' ? styles.active : ''}`} onClick={() => setStatusFilter('ALL')}>
            All ({logs.length})
          </button>
          <button className={`${styles.filterButton} ${statusFilter === 'VOTE_CAST' ? styles.active : ''}`} onClick={() => setStatusFilter('VOTE_CAST')}>
            Vote Cast ({votesCastCount})
          </button>
          <button className={`${styles.filterButton} ${statusFilter === 'KEY_GENERATED' ? styles.active : ''}`} onClick={() => setStatusFilter('KEY_GENERATED')}>
            Key Ready ({logs.filter(l => l.status === 'KEY_GENERATED').length})
          </button>
          <button className={`${styles.filterButton} ${statusFilter === 'ABORTED' ? styles.active : ''}`} onClick={() => setStatusFilter('ABORTED')}>
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
                filteredLogs.map((log) => (
                  <tr key={log.sessionId}>
                    <td className={styles.sessionId}>{log.sessionId}</td>
                    <td className={styles.voterId}>{log.voterId}</td>
                    <td>{renderQberCell(log)}</td>
                    <td>{renderStatusCell(log)}</td>
                    <td>
                      <span className={styles.keyBits}>
                        {log.keyGenerated ? stripBinPrefix(log.keyGenerated) : '—'}
                      </span>
                    </td>
                    <td>{formatTimestamp(log.createdAt)}</td>
                    <td>
                      <button className={styles.inspectButton} onClick={() => setSelectedLog(log)}>
                        Inspect BB84
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Inspect BB84 Detail Modal ── */}
      {selectedLog && (
        <div className={styles.modalBackdrop} onClick={() => setSelectedLog(null)}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h3 className={styles.modalTitle}>
                BB84 QKD Simulation Trace — <span className={styles.sessionId}>{selectedLog.sessionId}</span>
              </h3>
              <button className={styles.modalClose} onClick={() => setSelectedLog(null)}>✕</button>
            </div>

            <div className={styles.modalBody}>
              {/* Practical / System toggle above the diagnostic trace */}
              <ViewToggle view={modalView} onChange={setModalView} />

              {/* Diagnostic note */}
              <div style={{ padding: '10px 14px', backgroundColor: 'var(--color-accent-light)', border: '1px solid var(--color-border-light)', borderRadius: 'var(--radius-md)', fontSize: '12px', color: 'var(--color-accent)', display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span>ℹ</span>
                <span>
                  <strong>Simulation Diagnostic Trace:</strong>{' '}
                  {modalView === 'practical'
                    ? 'Practical view shows Alice &amp; Bob&apos;s perspective — as seen in a real QKD channel.'
                    : 'System view reveals ground truth including Eve&apos;s interception data — only visible in simulation.'}
                </span>
              </div>

              {/* Session meta */}
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
                  {(() => {
                    const qber = modalView === 'practical' ? selectedLog.qberPractical : selectedLog.qberSystem;
                    const isHigh = qber > selectedLog.thresholdPercent;
                    return (
                      <span className={styles.detailValue} style={{ color: isHigh ? 'var(--color-danger)' : 'var(--color-success)' }}>
                        {qber.toFixed(0)}%{modalView === 'practical' ? ' (Practical)' : ' (System)'} · Limit: {selectedLog.thresholdPercent}%
                      </span>
                    );
                  })()}
                </div>
                <div className={styles.detailBlock}>
                  <span className={styles.detailLabel}>Created At</span>
                  <span className={styles.detailValue}>{formatTimestamp(selectedLog.createdAt)}</span>
                </div>
              </div>

              {/* Generated OTP Key */}
              <div>
                <div className={styles.sectionHeader}>Generated OTP Key</div>
                <div className={styles.keyBits} style={{ width: '100%', maxWidth: 'none', padding: '10px 14px', fontSize: '13px' }}>
                  {stripBinPrefix(selectedLog.keyGenerated) || 'Key Generation Aborted'}
                </div>
              </div>

              {/* No encryptedVote in new schema */}

              {/* ── New Transmission Table ── */}
              <div>
                <div className={styles.sectionHeader}>BB84 Qubit Basis &amp; Bit Sequence</div>
                <TransmissionTable log={selectedLog} view={modalView} />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
