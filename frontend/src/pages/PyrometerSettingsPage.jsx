import { useState, useEffect } from 'react';
import { pyrometerAPI, deviceAPI, configAPI } from '../services/api';

/**
 * PyrometerSettingsPage Component
 *
 * Modal page for configuring pyrometer device parameters (emissivity, etc.)
 * Automatically pauses polling when opened to avoid COM port conflicts
 */
function PyrometerSettingsPage({ isOpen, onClose }) {
    const [emissivity, setEmissivity] = useState(0.95);
    const [inputValue, setInputValue] = useState('0.95');
    const [isLoading, setIsLoading] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [message, setMessage] = useState({ type: '', text: '' });
    const [pollingPaused, setPollingPaused] = useState(false);

    // Device and COM port selection
    const [devices, setDevices] = useState([]);
    const [comPorts, setComPorts] = useState([]);
    const [selectedDevice, setSelectedDevice] = useState(null);
    const [selectedComPort, setSelectedComPort] = useState('');

    const MIN_EMISSIVITY = 0.20;
    const MAX_EMISSIVITY = 1.00;

    // Load devices and COM ports on mount, pause polling
    useEffect(() => {
        if (isOpen) {
            loadDevices();
            loadComPorts();
            pausePolling();
        }
    }, [isOpen]);

    // Cleanup: Resume polling when component unmounts or modal closes
    useEffect(() => {
        return () => {
            if (pollingPaused) {
                resumePolling();
            }
        };
    }, [pollingPaused]);

    // Load emissivity when device or COM port changes
    useEffect(() => {
        if (selectedDevice && pollingPaused) {
            // Only load emissivity once polling is paused to avoid conflicts
            loadEmissivity();
        }
    }, [selectedDevice, selectedComPort, pollingPaused]);

    const pausePolling = async () => {
        try {
            console.log('Pausing polling service...');
            await pyrometerAPI.pausePolling();
            setPollingPaused(true);
            console.log('Polling paused successfully');
        } catch (error) {
            console.error('Error pausing polling:', error);
            setMessage({
                type: 'error',
                text: 'Failed to pause polling service. Please try again.'
            });
        }
    };

    const resumePolling = async () => {
        try {
            console.log('Resuming polling service...');
            await pyrometerAPI.resumePolling();
            setPollingPaused(false);
            console.log('Polling resumed successfully');
        } catch (error) {
            console.error('Error resuming polling:', error);
        }
    };

    const loadDevices = async () => {
        try {
            const devicesData = await deviceAPI.getAll(true); // Get enabled devices only
            setDevices(devicesData);

            // Auto-select first device if available
            if (devicesData.length > 0) {
                setSelectedDevice(devicesData[0]);
            }
        } catch (error) {
            console.error('Error loading devices:', error);
            setMessage({
                type: 'error',
                text: 'Failed to load devices from database'
            });
        }
    };

    const loadComPorts = async () => {
        try {
            const portsData = await configAPI.getComPorts();
            setComPorts(portsData.ports || []);

            // Auto-select first COM port or use device's COM port if available
            if (portsData.ports && portsData.ports.length > 0) {
                setSelectedComPort(portsData.ports[0].port);
            }
        } catch (error) {
            console.error('Error loading COM ports:', error);
            // Fallback to COM3
            setComPorts([{ port: 'COM3', description: 'Default' }]);
            setSelectedComPort('COM3');
        }
    };

    const loadEmissivity = async () => {
        if (!selectedDevice) {
            setMessage({
                type: 'error',
                text: 'Please select a device first'
            });
            return;
        }

        setIsLoading(true);
        setMessage({ type: '', text: '' });

        try {
            const slaveId = selectedDevice.slave_id;
            const comPort = selectedDevice.com_port || selectedComPort;

            const response = await pyrometerAPI.getEmissivity(slaveId, comPort);
            const value = response.emissivity;
            setEmissivity(value);
            setInputValue(value.toFixed(2));
            setMessage({
                type: 'success',
                text: `Emissivity loaded from ${selectedDevice.name} (ID: ${slaveId})`
            });
        } catch (error) {
            console.error('Error loading emissivity:', error);
            const errorMsg = error.response?.data?.detail || 'Failed to load emissivity. Check device connection.';
            setMessage({
                type: 'error',
                text: errorMsg
            });
        } finally {
            setIsLoading(false);
        }
    };

    const handleInputChange = (e) => {
        const value = e.target.value;
        setInputValue(value);

        // Clear message when user starts typing
        if (message.text) {
            setMessage({ type: '', text: '' });
        }
    };

    const handleSave = async () => {
        if (!selectedDevice) {
            setMessage({
                type: 'error',
                text: 'Please select a device first'
            });
            return;
        }

        // Validate input
        const numValue = parseFloat(inputValue);

        if (isNaN(numValue)) {
            setMessage({
                type: 'error',
                text: 'Please enter a valid number'
            });
            return;
        }

        if (numValue < MIN_EMISSIVITY || numValue > MAX_EMISSIVITY) {
            setMessage({
                type: 'error',
                text: `Emissivity must be between ${MIN_EMISSIVITY} and ${MAX_EMISSIVITY}`
            });
            return;
        }

        setIsSaving(true);
        setMessage({ type: '', text: '' });

        try {
            const slaveId = selectedDevice.slave_id;
            const comPort = selectedDevice.com_port || selectedComPort;

            const response = await pyrometerAPI.setEmissivity(numValue, slaveId, comPort);
            setEmissivity(response.emissivity);
            setInputValue(response.emissivity.toFixed(2));
            setMessage({
                type: 'success',
                text: `Emissivity set to ${response.emissivity.toFixed(2)} on ${selectedDevice.name} (ID: ${slaveId})`
            });
        } catch (error) {
            console.error('Error setting emissivity:', error);
            const errorMsg = error.response?.data?.detail || 'Failed to set emissivity. Check device connection.';
            setMessage({
                type: 'error',
                text: errorMsg
            });
        } finally {
            setIsSaving(false);
        }
    };

    const handleClose = async () => {
        // Resume polling before closing
        if (pollingPaused) {
            await resumePolling();
        }
        onClose();
    };

    const isValidInput = () => {
        const numValue = parseFloat(inputValue);
        return !isNaN(numValue) && numValue >= MIN_EMISSIVITY && numValue <= MAX_EMISSIVITY;
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">

                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b">
                    <div className="flex items-center space-x-3">
                        <div className="bg-green-100 p-2 rounded-lg">
                            <svg
                                className="w-6 h-6 text-green-600"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
                                />
                            </svg>
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-gray-800">Pyrometer Settings</h2>
                            <p className="text-sm text-gray-500">Configure device parameters</p>
                        </div>
                    </div>
                    <button
                        onClick={handleClose}
                        className="text-gray-500 hover:text-gray-700 transition"
                    >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <div className="p-6">
                    {/* Polling Paused Banner */}
                    <div className={`mb-6 p-4 rounded-lg border ${
                        pollingPaused
                            ? 'bg-yellow-50 border-yellow-200'
                            : 'bg-blue-50 border-blue-200'
                    }`}>
                        <div className="flex items-center space-x-2">
                            {pollingPaused ? (
                                <>
                                    <svg className="w-5 h-5 text-yellow-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                    </svg>
                                    <div className="text-sm">
                                        <p className="font-semibold text-yellow-800">⚠️ Polling Paused</p>
                                        <p className="text-yellow-700">Temperature polling has been paused to allow device parameter configuration. It will resume automatically when you close this window.</p>
                                    </div>
                                </>
                            ) : (
                                <>
                                    <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    <p className="text-sm text-blue-700">Pausing polling service...</p>
                                </>
                            )}
                        </div>
                    </div>

                    {/* Device and COM Port Selection */}
                    <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
                        <h3 className="text-sm font-semibold text-gray-700 mb-3">Device Selection</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Device Dropdown */}
                            <div>
                                <label className="block text-xs font-medium text-gray-600 mb-1">
                                    Device (Instrument ID)
                                </label>
                                <select
                                    value={selectedDevice?.id || ''}
                                    onChange={(e) => {
                                        const device = devices.find(d => d.id === parseInt(e.target.value));
                                        setSelectedDevice(device);
                                        // Update COM port from device if available
                                        if (device && device.com_port) {
                                            setSelectedComPort(device.com_port);
                                        }
                                    }}
                                    disabled={isLoading || isSaving || devices.length === 0 || !pollingPaused}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-green-500 focus:outline-none disabled:bg-gray-100 disabled:cursor-not-allowed"
                                >
                                    {devices.length === 0 ? (
                                        <option value="">No devices configured</option>
                                    ) : (
                                        devices.map(device => (
                                            <option key={device.id} value={device.id}>
                                                {device.name} (ID: {device.slave_id})
                                            </option>
                                        ))
                                    )}
                                </select>
                                {devices.length === 0 && (
                                    <p className="text-xs text-red-600 mt-1">
                                        Configure devices first using "Configure Devices" button
                                    </p>
                                )}
                            </div>

                            {/* COM Port Dropdown */}
                            <div>
                                <label className="block text-xs font-medium text-gray-600 mb-1">
                                    COM Port
                                </label>
                                <select
                                    value={selectedComPort}
                                    onChange={(e) => setSelectedComPort(e.target.value)}
                                    disabled={isLoading || isSaving || !pollingPaused}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-green-500 focus:outline-none disabled:bg-gray-100 disabled:cursor-not-allowed"
                                >
                                    {comPorts.map((port, idx) => (
                                        <option key={idx} value={port.port}>
                                            {port.port} - {port.description}
                                        </option>
                                    ))}
                                </select>
                                {selectedDevice?.com_port && (
                                    <p className="text-xs text-blue-600 mt-1">
                                        Device configured with: {selectedDevice.com_port}
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Current Value Display */}
                    <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
                        <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-gray-600">Current Emissivity:</span>
                            {isLoading ? (
                                <div className="animate-pulse bg-gray-300 h-6 w-20 rounded"></div>
                            ) : (
                                <span className="text-2xl font-bold text-green-600">{emissivity.toFixed(2)}</span>
                            )}
                        </div>
                        {selectedDevice && (
                            <p className="text-xs text-gray-500 mt-2">
                                Device: {selectedDevice.name} | Slave ID: {selectedDevice.slave_id} | Port: {selectedDevice.com_port || selectedComPort}
                            </p>
                        )}
                    </div>

                    {/* Input Section */}
                    <div className="mb-6">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            New Emissivity Value
                            <span className="text-gray-500 font-normal ml-2">({MIN_EMISSIVITY} - {MAX_EMISSIVITY})</span>
                        </label>

                        {/* Number Input */}
                        <input
                            type="number"
                            value={inputValue}
                            onChange={handleInputChange}
                            step="0.01"
                            min={MIN_EMISSIVITY}
                            max={MAX_EMISSIVITY}
                            disabled={isLoading || isSaving || !selectedDevice || !pollingPaused}
                            className={`w-full px-4 py-3 text-lg border-2 rounded-lg focus:outline-none transition ${
                                isValidInput()
                                    ? 'border-gray-300 focus:border-green-500'
                                    : 'border-red-300 focus:border-red-500'
                            } ${
                                (isLoading || isSaving || !selectedDevice || !pollingPaused) ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'
                            }`}
                            placeholder="Enter emissivity (e.g., 0.95)"
                        />

                        {/* Range Slider */}
                        <div className="mt-4">
                            <input
                                type="range"
                                value={inputValue}
                                onChange={handleInputChange}
                                step="0.01"
                                min={MIN_EMISSIVITY}
                                max={MAX_EMISSIVITY}
                                disabled={isLoading || isSaving || !selectedDevice || !pollingPaused}
                                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-green-600 disabled:cursor-not-allowed"
                            />
                            <div className="flex justify-between text-xs text-gray-500 mt-1">
                                <span>{MIN_EMISSIVITY}</span>
                                <span>{MAX_EMISSIVITY}</span>
                            </div>
                        </div>
                    </div>

                    {/* Message Display */}
                    {message.text && (
                        <div className={`mb-4 p-3 rounded-lg text-sm ${
                            message.type === 'success'
                                ? 'bg-green-50 text-green-800 border border-green-200'
                                : 'bg-red-50 text-red-800 border border-red-200'
                        }`}>
                            <div className="flex items-center space-x-2">
                                {message.type === 'success' ? (
                                    <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                    </svg>
                                ) : (
                                    <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                    </svg>
                                )}
                                <span>{message.text}</span>
                            </div>
                        </div>
                    )}

                    {/* Action Buttons */}
                    <div className="space-y-3">
                        {/* Save Button */}
                        <button
                            onClick={handleSave}
                            disabled={isLoading || isSaving || !isValidInput() || !selectedDevice || !pollingPaused}
                            className={`w-full py-3 px-4 rounded-lg font-semibold transition flex items-center justify-center space-x-2 ${
                                isLoading || isSaving || !isValidInput() || !selectedDevice || !pollingPaused
                                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                    : 'bg-green-600 text-white hover:bg-green-700 active:bg-green-800'
                            }`}
                        >
                            {isSaving ? (
                                <>
                                    <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    <span>Saving...</span>
                                </>
                            ) : (
                                <>
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                    </svg>
                                    <span>Save Emissivity</span>
                                </>
                            )}
                        </button>

                        {/* Refresh Button */}
                        <button
                            onClick={loadEmissivity}
                            disabled={isLoading || isSaving || !selectedDevice || !pollingPaused}
                            className="w-full py-2 px-4 border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                            <span className="text-sm font-medium">Refresh Emissivity</span>
                        </button>
                    </div>

                    {/* Info Footer */}
                    <div className="mt-6 p-3 bg-blue-50 rounded-lg">
                        <div className="flex items-start space-x-2">
                            <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                            </svg>
                            <div className="text-xs text-blue-800">
                                <p className="font-semibold mb-1">About Emissivity:</p>
                                <p>Emissivity varies by material surface. Values range from {MIN_EMISSIVITY} (shiny/reflective) to {MAX_EMISSIVITY} (matte/dark). Select the device first, then adjust and save.</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Footer Buttons */}
                <div className="flex items-center justify-end p-4 border-t bg-gray-50 space-x-3">
                    <button
                        onClick={handleClose}
                        className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 transition"
                    >
                        Close (Resume Polling)
                    </button>
                </div>

            </div>
        </div>
    );
}

export default PyrometerSettingsPage;
