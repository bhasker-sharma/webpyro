/**
 * App.jsx - Main Application Component
 * 
 * Purpose: This is the root component that handles routing between different pages
 * 
 * Structure:
 * - Uses React Router for navigation
 * - Wraps all pages with Navbar component
 * - Defines routes for Dashboard and Configuration
 */

import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import DashboardPage from './pages/DashboardPage';

function App() {
  return (
    // Router wraps entire app to enable navigation
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* Navbar appears on all pages */}
        <Navbar />
        
        {/* Main content area */}
        <main className="container mx-auto">
          <Routes>
            {/* Default route - Dashboard page */}
            <Route path="/" element={<DashboardPage />} />
            
            {/* Additional routes will be added here later */}
            {/* <Route path="/config" element={<ConfigPage />} /> */}
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;