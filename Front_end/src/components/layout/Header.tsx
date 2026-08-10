import { useNavigate } from 'react-router-dom';
import styles from './Header.module.css';

export function Header() {
  const navigate = useNavigate();

  return (
    <header className={styles.header}>
      <div className={styles.logo}>
        <div className={styles.logoIcon}>◇</div>
        <div className={styles.logoText}>
          <span className={styles.logoTitle}>Quantum Secured Voting System</span>
          <span className={styles.logoSubtitle}>
            IBM Quantum Simulation · QKD BB84 · One-Time Pad
          </span>
        </div>
      </div>

      <nav className={styles.nav}>
        <button className={styles.navLink} onClick={() => navigate('/configure')}>
          <span className={styles.navLinkIcon}>⚙</span>
          Configure
        </button>
        <button className={styles.navLink} onClick={() => navigate('/logs')}>
          <span className={styles.navLinkIcon}>📜</span>
          Voting Log
        </button>
        <button className={styles.navLink} onClick={() => navigate('/results')}>
          {/*<span className={styles.navLinkIcon}>📊</span>*/}
          <span className={styles.navLinkIcon}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="20" x2="18" y2="10"></line>
              <line x1="12" y1="20" x2="12" y2="4"></line>
              <line x1="6" y1="20" x2="6" y2="14"></line>
            </svg>
          </span>
          Results
        </button>
        <span className={styles.prototypeBadge}>PROTOTYPE</span>
      </nav>
    </header>
  );
}
