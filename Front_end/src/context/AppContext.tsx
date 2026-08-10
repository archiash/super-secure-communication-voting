import { createContext, useContext, useReducer, useMemo, useEffect, type ReactNode } from 'react';
import type { AppState, AppAction } from './types';
import { appReducer, initialState } from './reducer';
import { getApiService, type ApiService } from '../services';
import { DEFAULT_CONFIG } from '../types';
import type { ProtocolConfig } from '../types';

const CONFIG_STORAGE_KEY = 'qkd-voting-config';

/** Load saved config from localStorage, falling back to defaults */
function loadSavedConfig(): ProtocolConfig {
  try {
    const saved = localStorage.getItem(CONFIG_STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved);
      // Merge with defaults so new fields added in future are picked up
      return { ...DEFAULT_CONFIG, ...parsed };
    }
  } catch {
    // Corrupted data — ignore and use defaults
  }
  return { ...DEFAULT_CONFIG };
}

/** Save config to localStorage */
function saveConfig(config: ProtocolConfig): void {
  try {
    localStorage.setItem(CONFIG_STORAGE_KEY, JSON.stringify(config));
  } catch {
    // Storage full or unavailable — silently ignore
  }
}

interface AppContextValue {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
  api: ApiService;
}

const AppContext = createContext<AppContextValue | null>(null);

/** Provider component — wraps the entire app */
export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, {
    ...initialState,
    config: loadSavedConfig(),
  });
  const api = useMemo(() => getApiService(), []);

  // Persist config to localStorage whenever it changes
  useEffect(() => {
    saveConfig(state.config);
  }, [state.config]);

  const value = useMemo(
    () => ({ state, dispatch, api }),
    [state, dispatch, api]
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

/** Hook to access app state, dispatch, and API service */
export function useApp(): AppContextValue {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
