import { Link } from 'react-router-dom';
import { useState } from 'react';

function Navbar({ onConfigureClick, onPyrometerSettingsClick }) {
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    return (
        <nav className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b-2 border-blue-200 shadow-md">
            <div className="container mx-auto px-4">
                <div className="flex items-center justify-between h-14 sm:h-10">
                    {/* Logo/Brand */}
                    <div className="flex items-center space-x-3">
                        <Link to="/" className="flex items-center space-x-2 hover:opacity-80 transition">
                            <img src="/logo.png" alt="TIPL Logo" className="w-8 h-8 object-contain" />
                            <span className="text-xl font-bold text-gray-800">Multi IR Thermometer</span>
                        </Link>
                    </div>

                    {/* Desktop Navigation (hidden on mobile) */}
                    <div className="hidden sm:flex items-center space-x-3">
                        <Link
                            to="/preview"
                            className="px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center space-x-2 font-medium shadow-md text-sm"
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            <span>Preview & Export</span>
                        </Link>

                        <button
                            onClick={onPyrometerSettingsClick}
                            className="px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition flex items-center space-x-2 font-medium shadow-md text-sm"
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                            </svg>
                            <span>Pyrometer Settings</span>
                        </button>

                        <button
                            onClick={onConfigureClick}
                            className="px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center space-x-2 font-medium shadow-md text-sm"
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                            <span>Configure Devices</span>
                        </button>
                    </div>

                    {/* Mobile Menu Toggle (visible on mobile only) */}
                    <button
                        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                        className="sm:hidden p-2 hover:bg-blue-100 rounded-lg transition text-gray-700"
                        aria-label="Toggle menu"
                    >
                        {mobileMenuOpen ? (
                            // Close icon
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        ) : (
                            // Hamburger icon
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                            </svg>
                        )}
                    </button>
                </div>

                {/* Mobile Menu (shown when toggled) */}
                {mobileMenuOpen && (
                    <div className="sm:hidden border-t border-blue-200 py-2 space-y-1 bg-blue-50">
                        <Link
                            to="/preview"
                            onClick={() => setMobileMenuOpen(false)}
                            className="flex items-center space-x-2 px-4 py-3 text-gray-700 hover:bg-blue-100 rounded-lg transition"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            <span>Preview & Export</span>
                        </Link>

                        <button
                            onClick={() => {
                                onPyrometerSettingsClick();
                                setMobileMenuOpen(false);
                            }}
                            className="w-full flex items-center space-x-2 px-4 py-3 text-gray-700 hover:bg-blue-100 rounded-lg transition text-left"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                            </svg>
                            <span>Pyrometer Settings</span>
                        </button>

                        <button
                            onClick={() => {
                                onConfigureClick();
                                setMobileMenuOpen(false);
                            }}
                            className="w-full flex items-center space-x-2 px-4 py-3 text-gray-700 hover:bg-blue-100 rounded-lg transition text-left"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                            <span>Configure Devices</span>
                        </button>
                    </div>
                )}
            </div>
        </nav>
    );
}

export default Navbar;