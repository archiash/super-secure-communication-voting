import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import { Header } from './components/layout/Header';
import { Footer } from './components/layout/Footer';
import { AuthenticationPage } from './pages/AuthenticationPage';
import { KeyGenerationPage } from './pages/KeyGenerationPage';
import { CastVotePage } from './pages/CastVotePage';
import { ConfirmationPage } from './pages/ConfirmationPage';
import { ConfigurePage } from './pages/ConfigurePage';
import { ResultsPage } from './pages/ResultsPage';
import { VotingLogsPage } from './pages/VotingLogsPage';

function App() {
  return (
    <BrowserRouter>
      <AppProvider>
        <Header />
        <main style={{ flex: 1, paddingBottom: 64, display: 'flex', flexDirection: 'column' }}>
          <Routes>
            <Route path="/" element={<AuthenticationPage />} />
            <Route path="/key-generation" element={<KeyGenerationPage />} />
            <Route path="/cast-vote" element={<CastVotePage />} />
            <Route path="/confirmation" element={<ConfirmationPage />} />
            <Route path="/configure" element={<ConfigurePage />} />
            <Route path="/results" element={<ResultsPage />} />
            <Route path="/logs" element={<VotingLogsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <Footer />
      </AppProvider>
    </BrowserRouter>
  );
}

export default App;
