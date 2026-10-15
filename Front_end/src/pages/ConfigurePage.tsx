import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { DEFAULT_CONFIG, calculatePhotonCount } from '../types';
import type { ProtocolConfig } from '../types';
import styles from './ConfigurePage.module.css';

export function ConfigurePage() {
  const { state, dispatch } = useApp();
  const navigate = useNavigate();

  const [config, setConfig] = useState<ProtocolConfig>({ ...state.config });

  const updateField = <K extends keyof ProtocolConfig>(key: K, value: ProtocolConfig[K]) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = () => {
    dispatch({ type: 'SET_CONFIG', payload: config });
    navigate(-1);
  };

  const handleReset = () => {
    setConfig({ ...DEFAULT_CONFIG });
  };

  const calculatedPhotons = calculatePhotonCount(
    config.targetKeyLength,
    config.errorTolerance,
    config.securityParameter,
    config.privacyAmplificationEnabled
  );

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Protocol Configuration</h1>
          <p className={styles.subtitle}>
            Configure BB84 parameters, post-processing, and simulation settings.
          </p>
        </div>
        <button className={styles.backButton} onClick={() => navigate(-1)}>
          ← Back
        </button>
      </div>

      <div className={styles.grid}>

        {/* ── Left Column ── */}
        <div className={styles.column}>

          {/* TYPE OF SIMULATION */}
          <div className={styles.sectionTitle}>TYPE OF SIMULATION</div>
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <div className={styles.cardTitleArea}>
                <span className={styles.cardTitle}>Use Quantum Computer</span>
                <span className={styles.cardDesc}>This voting simulation will sent data to process on quantum computer</span>
              </div>
              <button
                className={`${styles.toggle} ${config.useRealQuantum ? styles.active : ''}`}
                onClick={() => updateField('useRealQuantum', !config.useRealQuantum)}
              >
                <div className={styles.toggleDot} />
              </button>
            </div>
          </div>
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <div className={styles.cardTitleArea}>
                <span className={styles.cardTitle}>
                  Simulate Eve 
                  {/* <span className={styles.badge}>ATTACK SIM</span> */}
                </span>
                <span className={styles.cardDesc}>Inject intercept-resend attack on the quantum channel</span>
              </div>
              <button
                className={`${styles.toggle} ${config.eveSimulation ? styles.active : ''}`}
                onClick={() => updateField('eveSimulation', !config.eveSimulation)}
              >
                <div className={styles.toggleDot} />
              </button>
            </div>
          </div>

          {/* QUANTUM HARDWARE */}
          <div className={styles.sectionTitle}>QUANTUM HARDWARE</div>
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <div className={styles.cardTitleArea}>
                <span className={styles.cardTitle}>QPU Qubit Capacity</span>
                <span className={styles.cardDesc}>Physical qubits used per circuit run on quantum computer (4 to 64)</span>
              </div>
            </div>
            <div className={styles.sliderContainer}>
              <input
                type="range"
                className={styles.slider}
                min={4}
                max={64}
                step={4}
                value={config.qubitCount}
                onChange={(e) => updateField('qubitCount', parseInt(e.target.value))}
              />
              <input
                type="number"
                className={styles.sliderInput}
                value={config.qubitCount}
                onChange={(e) => updateField('qubitCount', parseInt(e.target.value) || 4)}
              />
            </div>
          </div>

        </div>

        {/* ── Right Column ── */}
        <div className={styles.column}>

          {/* KEY REQUIREMENTS */}
          <div className={styles.sectionTitle}>KEY REQUIREMENTS</div>
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <div className={styles.cardTitleArea}>
                <span className={styles.cardTitle}>Target Key Size (m)</span>
                <span className={styles.cardDesc}>Minimum secret key bits needed for OTP ballot encryption</span>
              </div>
            </div>
            <div className={styles.sliderContainer}>
              <input
                type="range"
                className={styles.slider}
                min={4}
                max={256}
                step={4}
                value={config.targetKeyLength}
                onChange={(e) => updateField('targetKeyLength', parseInt(e.target.value))}
              />
              <input
                type="number"
                className={styles.sliderInput}
                value={config.targetKeyLength}
                onChange={(e) => updateField('targetKeyLength', parseInt(e.target.value) || 4)}
              />
            </div>
          </div>

          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <div className={styles.cardTitleArea}>
                <span className={styles.cardTitle}>
                  Safety Margin <span className={styles.deltaSymbol}>δ</span>
                </span>
                <span className={styles.cardDesc}>Extra qubits to send as a safety buffer. A bigger number is safer, but it uses more qubits. (0 to 2)</span>
              </div>
            </div>
            <div className={styles.sliderContainer}>
              <input
                type="range"
                className={styles.slider}
                min={0}
                max={2}
                step={0.01}
                value={config.errorTolerance}
                onChange={(e) => updateField('errorTolerance', parseFloat(e.target.value))}
              />
              <input
                type="number"
                className={styles.sliderInput}
                min={0}
                max={2}
                step={0.01}
                value={config.errorTolerance.toFixed(2)}
                onChange={(e) => {
                  const val = parseFloat(e.target.value);
                  if (!isNaN(val)) updateField('errorTolerance', val);
                }}
                onBlur={(e) => {
                  const val = parseFloat(e.target.value);
                  if (isNaN(val) || val < 0) updateField('errorTolerance', 0);
                  else if (val > 2) updateField('errorTolerance', 2);
                  else updateField('errorTolerance', parseFloat(val.toFixed(2)));
                }}
              />
            </div>
          </div>

          {/* PRIVACY AMPLIFICATION */}
          <div className={styles.sectionTitle}>PRIVACY AMPLIFICATION</div>
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <div className={styles.cardTitleArea}>
                <span className={styles.cardTitle}>Privacy Amplification</span>
                <span className={styles.cardDesc}>Universal Toeplitz hashing shrinks raw key to eliminate Eve's partial information</span>
              </div>
              <button
                className={`${styles.toggle} ${config.privacyAmplificationEnabled ? styles.active : ''}`}
                onClick={() => updateField('privacyAmplificationEnabled', !config.privacyAmplificationEnabled)}
              >
                <div className={styles.toggleDot} />
              </button>
            </div>
          </div>

          {config.privacyAmplificationEnabled && (
            <div className={styles.card}>
              <div className={styles.cardHeader}>
                <div className={styles.cardTitleArea}>
                  <span className={styles.cardTitle}>
                    Security Parameter <span className={styles.deltaSymbol}>s</span>
                  </span>
                  <span className={styles.cardDesc}>
                    Sacrificed bits guaranteeing Eve information bound <i>I_E ≤ 2<sup>-{config.securityParameter}</sup></i> bits (8 to 32)
                  </span>
                </div>
              </div>
              <div className={styles.sliderContainer}>
                <input
                  type="range"
                  className={styles.slider}
                  min={8}
                  max={32}
                  step={1}
                  value={config.securityParameter}
                  onChange={(e) => updateField('securityParameter', parseInt(e.target.value))}
                />
                <input
                  type="number"
                  className={styles.sliderInput}
                  min={8}
                  max={32}
                  step={1}
                  value={config.securityParameter}
                  onChange={(e) => updateField('securityParameter', parseInt(e.target.value) || 8)}
                />
              </div>
            </div>
          )}

          {/* CHANNEL SIZING FORMULA */}
          <div className={styles.card} style={{ backgroundColor: 'rgba(59, 130, 246, 0.04)', borderColor: 'rgba(59, 130, 246, 0.2)' }}>
            <div className={styles.cardHeader}>
              <div className={styles.cardTitleArea} style={{ maxWidth: '100%' }}>
                <span className={styles.cardTitle} style={{ color: 'var(--color-primary)' }}>
                  Channel Sizing: {calculatedPhotons} Photons Required
                </span>
                <span className={styles.cardDesc} style={{ fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
                  {config.privacyAmplificationEnabled
                    ? `N = ⌈(4 + δ) × (m + s)⌉ = ⌈(4 + ${config.errorTolerance.toFixed(2)}) × (${config.targetKeyLength} + ${config.securityParameter})⌉ = ${calculatedPhotons}`
                    : `N = ⌈(4 + δ) × m⌉ = ⌈(4 + ${config.errorTolerance.toFixed(2)}) × ${config.targetKeyLength}⌉ = ${calculatedPhotons}`
                  }
                </span>
              </div>
            </div>
          </div>

        </div>
      </div>

      <div className={styles.footer}>
        <button className={styles.resetLink} onClick={handleReset}>
          Reset to defaults
        </button>
        <button className={styles.primaryButton} onClick={handleSave}>
          Save & Continue ›
        </button>
      </div>
    </div>
  );
}
