import { createContext, useContext, useReducer, useMemo, type ReactNode } from 'react';
import type { AppState, AppAction } from './types';
import { appReducer, initialState } from './reducer';
import { getApiService, type ApiService } from '../services';

interface AppContextValue {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
  api: ApiService;
}

const AppContext = createContext<AppContextValue | null>(null);

/** Provider component — wraps the entire app */
export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);
  const api = useMemo(() => getApiService(), []);

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
