import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { DEFAULT_CONFIG } from '../types';
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
    navigate('/');
  };

  const handleReset = () => {
    setConfig({ ...DEFAULT_CONFIG });
  };

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
        {/* Left Column */}
        <div className={styles.section}>
          <div className={styles.sectionTitle}>TYPE OF SIMULATION</div>
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <div className={styles.cardTitleArea}>
                <span className={styles.cardTitle}>Use Real Quantum Computer</span>
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
        </div>

        {/* Right Column */}
        <div className={styles.section}>
          <div className={styles.sectionTitle}>POST-PROCESSING</div>
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <div className={styles.cardTitleArea}>
                <span className={styles.cardTitle}>Error Correction</span>
                <span className={styles.cardDesc}>Cascade protocol — finds and corrects bit errors in the sifted key</span>
              </div>
              <button
                className={`${styles.toggle} ${config.errorCorrectionEnabled ? styles.active : ''}`}
                onClick={() => updateField('errorCorrectionEnabled', !config.errorCorrectionEnabled)}
              >
                <div className={styles.toggleDot} />
              </button>
            </div>
          </div>
        </div>

        {/* Left Column */}
        <div className={styles.section}>
          <div className={styles.sectionTitle}>QUANTUM CHANNEL</div>
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <div className={styles.cardTitleArea}>
                <span className={styles.cardTitle}>Qubit Count</span>
                <span className={styles.cardDesc}>Number of photons transmitted per session</span>
              </div>
            </div>
            <div className={styles.sliderContainer}>
              <input
                type="range"
                className={styles.slider}
                min={8}
                max={128}
                step={8}
                value={config.qubitCount}
                onChange={(e) => updateField('qubitCount', parseInt(e.target.value))}
              />
              <input
                type="number"
                className={styles.sliderInput}
                value={config.qubitCount}
                onChange={(e) => updateField('qubitCount', parseInt(e.target.value) || 8)}
              />
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className={styles.section}>
          <div className={styles.sectionTitle}>KEY REQUIREMENTS</div>
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <div className={styles.cardTitleArea}>
                <span className={styles.cardTitle}>Target Key Length</span>
                <span className={styles.cardDesc}>Minimum key bits needed for OTP ballot encryption</span>
              </div>
            </div>
            <div className={styles.sliderContainer}>
              <input
                type="range"
                className={styles.slider}
                min={4}
                max={32}
                step={4}
                value={config.targetKeyLength}
                onChange={(e) => updateField('targetKeyLength', parseInt(e.target.value))}
              />
              <span className={styles.sliderLabel}>{config.targetKeyLength} bits</span>
            </div>
          </div>
        </div>

        {/* Left Column */}
        <div className={styles.section}>
          <div className={styles.sectionTitle}>EAVESDROPPER SIMULATION</div>
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <div className={styles.cardTitleArea}>
                <span className={styles.cardTitle}>
                  Simulate Eve <span className={styles.badge}>ATTACK SIM</span>
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
        </div>

        {/* Right Column */}
        <div className={styles.section}>
          <div className={styles.sectionTitle}>VISUALIZATION</div>
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <div className={styles.cardTitleArea}>
                <span className={styles.cardTitle}>Sifting Table</span>
                <span className={styles.cardDesc}>Show full qubit-by-qubit transmission log during QKD</span>
              </div>
              <button
                className={`${styles.toggle} ${true ? styles.active : ''}`}
                // This is UI only for the mock, assuming true for now
              >
                <div className={styles.toggleDot} />
              </button>
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
