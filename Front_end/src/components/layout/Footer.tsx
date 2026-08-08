import styles from './Footer.module.css';

export function Footer() {
  return (
    <footer className={styles.footer}>
      <div>QKD BB84 · Cascade EC · Privacy Amplification · OTP · IBM Qiskit Runtime</div>
      <div>Prototype simulation — not for production use</div>
    </footer>
  );
}
