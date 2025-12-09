import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useState } from 'react';
import Navbar from './components/Navbar';
import DashboardPage from './pages/DashboardPage';
import PreviewPage from './pages/PreviewPage';
import PyrometerSettingsPage from './pages/PyrometerSettingsPage';

function App() {
  const [configModalOpen, setConfigModalOpen] = useState(false);
  const [pyrometerSettingsOpen, setPyrometerSettingsOpen] = useState(false);

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navbar
          onConfigureClick={() => setConfigModalOpen(true)}
          onPyrometerSettingsClick={() => setPyrometerSettingsOpen(true)}
        />

        <main>
          <Routes>
            <Route
              path="/"
              element={
                <DashboardPage
                  configModalOpen={configModalOpen}
                  setConfigModalOpen={setConfigModalOpen}
                />
              }
            />
            <Route path="/preview" element={<PreviewPage />} />
          </Routes>
        </main>

        {/* Pyrometer Settings Modal - Global across all pages */}
        <PyrometerSettingsPage
          isOpen={pyrometerSettingsOpen}
          onClose={() => setPyrometerSettingsOpen(false)}
        />
      </div>
    </Router>
  );
}

export default App;