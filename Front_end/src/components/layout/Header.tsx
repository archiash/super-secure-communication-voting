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
        <button className={styles.navLink} onClick={() => navigate('/results')}>
          <span className={styles.navLinkIcon}>📊</span>
          Results
        </button>
        <span className={styles.prototypeBadge}>PROTOTYPE</span>
      </nav>
    </header>
  );
}
