import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useState } from 'react';
import Navbar from './components/Navbar';
import DashboardPage from './pages/DashboardPage';

function App() {
  const [configModalOpen, setConfigModalOpen] = useState(false);

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navbar onConfigureClick={() => setConfigModalOpen(true)} />

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
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;