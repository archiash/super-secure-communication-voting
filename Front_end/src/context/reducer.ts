import { DEFAULT_CONFIG } from '../types';
import type { AppState, AppAction } from './types';

/** Initial application state */
export const initialState: AppState = {
  wizardStep: 'authentication',
  config: { ...DEFAULT_CONFIG },
  auth: {
    voterId: '',
    electionCode: '',
    sessionId: '',
    isAuthenticated: false,
  },
  qkd: {
    isGenerating: false,
    result: null,
    error: null,
    currentPhase: 'transmission',
    isBlurred: true,
    isTransmitting: false,
  },
  vote: {
    selectedOptionId: null,
    encryptedVote: null,
    otpKey: null,
    voteId: null,
    timestamp: null,
    isSubmitting: false,
  },
  results: null,
  error: null,
};

/** Root reducer for all app state transitions */
export function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_CONFIG':
      return { ...state, config: action.payload };

    case 'AUTHENTICATE':
      return {
        ...state,
        auth: {
          voterId: action.payload.voterId,
          electionCode: action.payload.electionCode,
          sessionId: action.payload.sessionId,
          isAuthenticated: true,
        },
        wizardStep: 'keyGeneration',
      };

    case 'SET_WIZARD_STEP':
      return { ...state, wizardStep: action.payload };

    case 'QKD_START':
      return {
        ...state,
        qkd: { ...state.qkd, isGenerating: true, result: null, error: null, currentPhase: 'transmission', isBlurred: true, isTransmitting: true },
      };

    case 'QKD_SUCCESS':
      return {
        ...state,
        qkd: { ...state.qkd, isGenerating: false, result: action.payload, error: null, isTransmitting: true, currentPhase: 'transmission' },
      };

    case 'SET_QKD_PHASE':
      return {
        ...state,
        qkd: {
          ...state.qkd,
          currentPhase: action.payload.currentPhase,
          isBlurred: action.payload.isBlurred ?? state.qkd.isBlurred,
          isTransmitting: action.payload.isTransmitting ?? state.qkd.isTransmitting,
        },
      };

    case 'QKD_ERROR':
      return {
        ...state,
        qkd: { ...state.qkd, isGenerating: false, error: action.payload },
      };

    case 'SELECT_VOTE_OPTION':
      return {
        ...state,
        vote: { ...state.vote, selectedOptionId: action.payload },
      };

    case 'VOTE_SUBMIT_START':
      return {
        ...state,
        vote: {
          ...state.vote,
          encryptedVote: action.payload.encryptedVote,
          otpKey: action.payload.otpKey,
          isSubmitting: true,
        },
      };

    case 'VOTE_SUBMIT_SUCCESS':
      return {
        ...state,
        vote: {
          ...state.vote,
          voteId: action.payload.voteId,
          timestamp: action.payload.timestamp,
          isSubmitting: false,
        },
        wizardStep: 'confirmation',
      };

    case 'SET_RESULTS':
      return { ...state, results: action.payload };

    case 'SET_ERROR':
      return { ...state, error: action.payload };

    case 'CLEAR_ERROR':
      return { ...state, error: null };

    case 'RESET_SESSION':
      return {
        ...initialState,
        config: state.config, // Preserve config across sessions
        results: state.results, // Preserve accumulated results
      };

    default:
      return state;
  }
}
