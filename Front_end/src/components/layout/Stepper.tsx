import type { WizardStep } from '../../context/types';
import styles from './Stepper.module.css';

interface StepperProps {
  currentStep: WizardStep;
}

const STEPS: { key: WizardStep; label: string; number: number }[] = [
  { key: 'authentication', label: 'Authentication', number: 1 },
  { key: 'keyGeneration', label: 'Key Generation', number: 2 },
  { key: 'castVote', label: 'Cast Vote', number: 3 },
  { key: 'confirmation', label: 'Confirmation', number: 4 },
];

function getStepStatus(
  stepKey: WizardStep,
  currentStep: WizardStep
): 'pending' | 'active' | 'completed' {
  const currentIndex = STEPS.findIndex((s) => s.key === currentStep);
  const stepIndex = STEPS.findIndex((s) => s.key === stepKey);

  if (stepIndex < currentIndex) return 'completed';
  if (stepIndex === currentIndex) return 'active';
  return 'pending';
}

export function Stepper({ currentStep }: StepperProps) {
  return (
    <div className={styles.stepper}>
      {STEPS.map((step, i) => {
        const status = getStepStatus(step.key, currentStep);
        return (
          <div key={step.key} style={{ display: 'flex', alignItems: 'center' }}>
            <div className={styles.step}>
              <div className={`${styles.stepCircle} ${styles[status]}`}>
                {status === 'completed' ? (
                  <span className={styles.checkIcon}>✓</span>
                ) : (
                  step.number
                )}
              </div>
              <span className={`${styles.stepLabel} ${styles[status]}`}>
                {step.label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div
                className={`${styles.connector} ${
                  status === 'completed' ? styles.completed : ''
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
