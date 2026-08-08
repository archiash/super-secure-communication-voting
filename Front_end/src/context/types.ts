import type { ProtocolConfig, QKDResponse, VoteResultsResponse } from '../types';

/** The 4 wizard steps shown in the top stepper */
export type WizardStep = 'authentication' | 'keyGeneration' | 'castVote' | 'confirmation';

/** Complete application state */
export interface AppState {
  /** Current wizard step */
  wizardStep: WizardStep;

  /** Protocol configuration (shown in ACTIVE CONFIGURATION sidebar) */
  config: ProtocolConfig;

  /** Authentication state */
  auth: {
    voterId: string;
    electionCode: string;
    sessionId: string;
    isAuthenticated: boolean;
  };

  /** QKD key generation results */
  qkd: {
    isGenerating: boolean;
    result: QKDResponse | null;
    error: string | null;
  };

  /** Vote state */
  vote: {
    selectedOptionId: string | null;
    encryptedVote: string | null;
    otpKey: string | null;
    voteId: string | null;
    timestamp: string | null;
    isSubmitting: boolean;
  };

  /** Cached results */
  results: VoteResultsResponse | null;

  /** Global error state */
  error: string | null;
}

/** Action types for the reducer */
export type AppAction =
  | { type: 'SET_CONFIG'; payload: ProtocolConfig }
  | {
      type: 'AUTHENTICATE';
      payload: { voterId: string; electionCode: string; sessionId: string };
    }
  | { type: 'SET_WIZARD_STEP'; payload: WizardStep }
  | { type: 'QKD_START' }
  | { type: 'QKD_SUCCESS'; payload: QKDResponse }
  | { type: 'QKD_ERROR'; payload: string }
  | { type: 'SELECT_VOTE_OPTION'; payload: string }
  | {
      type: 'VOTE_SUBMIT_START';
      payload: { encryptedVote: string; otpKey: string };
    }
  | {
      type: 'VOTE_SUBMIT_SUCCESS';
      payload: { voteId: string; timestamp: string };
    }
  | { type: 'SET_RESULTS'; payload: VoteResultsResponse }
  | { type: 'SET_ERROR'; payload: string }
  | { type: 'CLEAR_ERROR' }
  | { type: 'RESET_SESSION' };
