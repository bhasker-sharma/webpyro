/**
 * Navbar.jsx - Navigation Bar Component
 * 
 * Purpose: Top navigation bar that appears on all pages
 * 
 * Features:
 * - Shows app title/logo
 * - "Configure Devices" button (will open modal later)
 * - "Dashboard" link to go back to main page
 * 
 * State: None (stateless component for now)
 */

import { Link } from 'react-router-dom';

function Navbar() {
    /**
     * handleConfigureClick - Opens configuration modal
     * TODO: This will be implemented in Step 3 when we create the modal
     */
    const handleConfigureClick = () => {
        console.log('Configure Devices clicked - Modal will open here');
        // Modal opening logic will be added in Step 3
    };

    return (
        <nav className="bg-gradient-to-r from-blue-600 to-blue-800 text-white shadow-lg">
            <div className="container mx-auto px-4">
                <div className="flex items-center justify-between h-10">

                    {/* Left side - App Logo/Title */}
                    <div className="flex items-center space-x-3">
                        <Link to="/" className="flex items-center space-x-2 hover:opacity-80 transition">
                            {/* Icon placeholder */}
                            <svg
                                className="w-6 h-6"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                                />
                            </svg>
                            <span className="text-xl font-bold">TIPL Pyrometer Monitor</span>
                        </Link>
                    </div>

                    {/* Right side - Navigation Buttons */}
                    <div className="flex items-center space-x-3">

                        {/* Configure Devices Button */}
                        <button
                            onClick={handleConfigureClick}
                            className="px-3 py-1.5 bg-white text-blue-600 rounded-lg hover:bg-gray-100 transition flex items-center space-x-2 font-medium shadow-md text-sm"
                        >
                        <svg 
                            className="w-4 h-4" 
                            fill="none" 
                            stroke="currentColor" 
                            viewBox="0 0 24 24"
                        >
                            <path 
                            strokeLinecap="round" 
                            strokeLinejoin="round" 
                            strokeWidth={2} 
                            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" 
                            />
                            <path 
                            strokeLinecap="round" 
                            strokeLinejoin="round" 
                            strokeWidth={2} 
                            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" 
                            />
                        </svg>
                            <span>Configure Devices</span>
                        </button>
                    </div>
                </div>
            </div>
        </nav>
    );
}

export default Navbar;