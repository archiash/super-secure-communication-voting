import styles from './Footer.module.css';

export function Footer() {
  return (
    <footer className={styles.footer}>
      <div>BB84 Quantum Key Distribution & One-Time Pad Verification</div>
      <div>IBM Quantum & Qiskit Aer Runtime</div>
    </footer>
  );
}
