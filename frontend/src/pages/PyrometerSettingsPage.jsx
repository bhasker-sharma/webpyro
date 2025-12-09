import { useState, useEffect } from 'react';
import { pyrometerAPI, deviceAPI, configAPI } from '../services/api';

/**
 * PyrometerSettingsPage Component
 *
 * Modal page for configuring pyrometer device parameters
 * Supports multiple parameters with tabbed interface
 * Automatically pauses polling when opened to avoid COM port conflicts
 */
function PyrometerSettingsPage({ isOpen, onClose }) {
    // Common state
    const [isLoading, setIsLoading] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [message, setMessage] = useState({ type: '', text: '' });
    const [pollingPaused, setPollingPaused] = useState(false);
    const [activeTab, setActiveTab] = useState('emissivity');

    // Device and COM port selection
    const [devices, setDevices] = useState([]);
    const [comPorts, setComPorts] = useState([]);
    const [selectedDevice, setSelectedDevice] = useState(null);
    const [selectedComPort, setSelectedComPort] = useState('');

    // Parameter states
    const [emissivity, setEmissivity] = useState(0.95);
    const [emissivityInput, setEmissivityInput] = useState('0.95');
    const [slope, setSlope] = useState(0.95);
    const [slopeInput, setSlopeInput] = useState('0.95');
    const [measurementMode, setMeasurementMode] = useState(0);
    const [timeInterval, setTimeInterval] = useState(1);
    const [timeIntervalInput, setTimeIntervalInput] = useState('1');
    const [tempLowerLimit, setTempLowerLimit] = useState(0);
    const [tempLowerLimitInput, setTempLowerLimitInput] = useState('0');
    const [tempUpperLimit, setTempUpperLimit] = useState(3000);
    const [tempUpperLimitInput, setTempUpperLimitInput] = useState('3000');

    // Constants
    const MIN_EMISSIVITY = 0.20;
    const MAX_EMISSIVITY = 1.00;
    const MIN_TEMP = 0;
    const MAX_TEMP = 3000;
    const MIN_TIME_INTERVAL = 1;
    const MAX_TIME_INTERVAL = 3600;
    const MEASUREMENT_MODES = {
        0: 'Monochrome',
        1: 'Colorimetric'
    };

    // Tabs configuration
    const tabs = [
        { id: 'emissivity', name: 'Emissivity', icon: '📊' },
        { id: 'slope', name: 'Slope', icon: '📈' },
        { id: 'mode', name: 'Measurement Mode', icon: '🎯' },
        { id: 'interval', name: 'Time Interval', icon: '⏱️' },
        { id: 'limits', name: 'Temperature Limits', icon: '🌡️' },
    ];

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

    // Load all parameters when device or COM port changes
    useEffect(() => {
        if (selectedDevice && pollingPaused) {
            loadAllParameters();
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

    const loadAllParameters = async () => {
        if (!selectedDevice) return;

        setIsLoading(true);
        setMessage({ type: '', text: '' });

        try {
            const slaveId = selectedDevice.slave_id;
            const comPort = selectedDevice.com_port || selectedComPort;

            // Use the all-parameters endpoint to fetch all at once
            const response = await pyrometerAPI.getAllParameters(slaveId, comPort);

            // Update all states
            setEmissivity(response.emissivity);
            setEmissivityInput(response.emissivity.toFixed(2));

            setSlope(response.slope);
            setSlopeInput(response.slope.toFixed(2));

            setMeasurementMode(response.measurement_mode);

            setTimeInterval(response.time_interval);
            setTimeIntervalInput(response.time_interval.toString());

            setTempLowerLimit(response.temp_lower_limit);
            setTempLowerLimitInput(response.temp_lower_limit.toString());

            setTempUpperLimit(response.temp_upper_limit);
            setTempUpperLimitInput(response.temp_upper_limit.toString());

            setMessage({
                type: 'success',
                text: `All parameters loaded from ${selectedDevice.name} (ID: ${slaveId})`
            });
        } catch (error) {
            console.error('Error loading parameters:', error);
            const errorMsg = error.response?.data?.detail || 'Failed to load parameters. Check device connection.';
            setMessage({
                type: 'error',
                text: errorMsg
            });
        } finally {
            setIsLoading(false);
        }
    };

    const handleClose = async () => {
        // Resume polling before closing
        if (pollingPaused) {
            await resumePolling();
        }
        onClose();
    };

    // Tab content renderers
    const renderEmissivityTab = () => (
        <div className="space-y-4">
            {/* Current Value */}
            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-600">Current Emissivity:</span>
                    {isLoading ? (
                        <div className="animate-pulse bg-gray-300 h-6 w-20 rounded"></div>
                    ) : (
                        <span className="text-2xl font-bold text-green-600">{emissivity.toFixed(2)}</span>
                    )}
                </div>
            </div>

            {/* Input */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    New Emissivity Value
                    <span className="text-gray-500 font-normal ml-2">({MIN_EMISSIVITY} - {MAX_EMISSIVITY})</span>
                </label>
                <input
                    type="number"
                    value={emissivityInput}
                    onChange={(e) => {
                        setEmissivityInput(e.target.value);
                        setMessage({ type: '', text: '' });
                    }}
                    step="0.01"
                    min={MIN_EMISSIVITY}
                    max={MAX_EMISSIVITY}
                    disabled={isLoading || isSaving || !selectedDevice || !pollingPaused}
                    className="w-full px-4 py-3 text-lg border-2 rounded-lg focus:outline-none focus:border-green-500 disabled:bg-gray-100"
                    placeholder="Enter emissivity (e.g., 0.95)"
                />
                {/* Range Slider */}
                <div className="mt-4">
                    <input
                        type="range"
                        value={emissivityInput}
                        onChange={(e) => setEmissivityInput(e.target.value)}
                        step="0.01"
                        min={MIN_EMISSIVITY}
                        max={MAX_EMISSIVITY}
                        disabled={isLoading || isSaving || !selectedDevice || !pollingPaused}
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-green-600"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>{MIN_EMISSIVITY}</span>
                        <span>{MAX_EMISSIVITY}</span>
                    </div>
                </div>
            </div>

            {/* Buttons */}
            <div className="flex space-x-3">
                <button
                    onClick={async () => {
                        const value = parseFloat(emissivityInput);
                        if (isNaN(value) || value < MIN_EMISSIVITY || value > MAX_EMISSIVITY) {
                            setMessage({ type: 'error', text: `Invalid emissivity value` });
                            return;
                        }
                        setIsSaving(true);
                        try {
                            const slaveId = selectedDevice.slave_id;
                            const comPort = selectedDevice.com_port || selectedComPort;
                            const response = await pyrometerAPI.setEmissivity(value, slaveId, comPort);
                            setEmissivity(response.emissivity);
                            setEmissivityInput(response.emissivity.toFixed(2));
                            setMessage({ type: 'success', text: 'Emissivity saved successfully' });
                        } catch (error) {
                            setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to save' });
                        } finally {
                            setIsSaving(false);
                        }
                    }}
                    disabled={isLoading || isSaving || !selectedDevice || !pollingPaused}
                    className="flex-1 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed font-semibold"
                >
                    {isSaving ? 'Saving...' : 'Save Emissivity'}
                </button>
                <button
                    onClick={loadAllParameters}
                    disabled={isLoading || isSaving || !selectedDevice || !pollingPaused}
                    className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                >
                    Refresh
                </button>
            </div>

            {/* Info */}
            <div className="p-3 bg-blue-50 rounded-lg text-xs text-blue-800">
                <p className="font-semibold mb-1">About Emissivity:</p>
                <p>Emissivity varies by material surface. Values range from {MIN_EMISSIVITY} (shiny/reflective) to {MAX_EMISSIVITY} (matte/dark).</p>
            </div>
        </div>
    );

    const renderSlopeTab = () => (
        <div className="space-y-4">
            {/* Current Value */}
            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-600">Current Slope:</span>
                    {isLoading ? (
                        <div className="animate-pulse bg-gray-300 h-6 w-20 rounded"></div>
                    ) : (
                        <span className="text-2xl font-bold text-blue-600">{slope.toFixed(2)}</span>
                    )}
                </div>
            </div>

            {/* Input */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    New Slope Value (Colorimetric Emissivity)
                    <span className="text-gray-500 font-normal ml-2">({MIN_EMISSIVITY} - {MAX_EMISSIVITY})</span>
                </label>
                <input
                    type="number"
                    value={slopeInput}
                    onChange={(e) => {
                        setSlopeInput(e.target.value);
                        setMessage({ type: '', text: '' });
                    }}
                    step="0.01"
                    min={MIN_EMISSIVITY}
                    max={MAX_EMISSIVITY}
                    disabled={isLoading || isSaving || !selectedDevice || !pollingPaused}
                    className="w-full px-4 py-3 text-lg border-2 rounded-lg focus:outline-none focus:border-blue-500 disabled:bg-gray-100"
                    placeholder="Enter slope (e.g., 0.95)"
                />
            </div>

            {/* Buttons */}
            <div className="flex space-x-3">
                <button
                    onClick={async () => {
                        const value = parseFloat(slopeInput);
                        if (isNaN(value) || value < MIN_EMISSIVITY || value > MAX_EMISSIVITY) {
                            setMessage({ type: 'error', text: `Invalid slope value` });
                            return;
                        }
                        setIsSaving(true);
                        try {
                            const slaveId = selectedDevice.slave_id;
                            const comPort = selectedDevice.com_port || selectedComPort;
                            await pyrometerAPI.setSlope(value, slaveId, comPort);
                            setSlope(value);
                            setMessage({ type: 'success', text: 'Slope saved successfully' });
                        } catch (error) {
                            setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to save' });
                        } finally {
                            setIsSaving(false);
                        }
                    }}
                    disabled={isLoading || isSaving || !selectedDevice || !pollingPaused}
                    className="flex-1 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed font-semibold"
                >
                    {isSaving ? 'Saving...' : 'Save Slope'}
                </button>
                <button
                    onClick={loadAllParameters}
                    disabled={isLoading || isSaving || !selectedDevice || !pollingPaused}
                    className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                >
                    Refresh
                </button>
            </div>

            {/* Info */}
            <div className="p-3 bg-blue-50 rounded-lg text-xs text-blue-800">
                <p className="font-semibold mb-1">About Slope:</p>
                <p>Slope parameter used for emissivity correction in colorimetric temperature measurement mode.</p>
            </div>
        </div>
    );

    const renderMeasurementModeTab = () => (
        <div className="space-y-4">
            {/* Current Value */}
            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-600">Current Mode:</span>
                    {isLoading ? (
                        <div className="animate-pulse bg-gray-300 h-6 w-32 rounded"></div>
                    ) : (
                        <span className="text-2xl font-bold text-purple-600">
                            {MEASUREMENT_MODES[measurementMode]} ({measurementMode})
                        </span>
                    )}
                </div>
            </div>

            {/* Mode Selection */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Measurement Mode
                </label>
                <div className="space-y-2">
                    {Object.entries(MEASUREMENT_MODES).map(([value, name]) => (
                        <label key={value} className="flex items-center p-3 border-2 rounded-lg cursor-pointer hover:bg-gray-50">
                            <input
                                type="radio"
                                name="measurement-mode"
                                value={value}
                                checked={measurementMode === parseInt(value)}
                                onChange={(e) => setMeasurementMode(parseInt(e.target.value))}
                                disabled={isLoading || isSaving || !selectedDevice || !pollingPaused}
                                className="w-4 h-4 text-purple-600"
                            />
                            <span className="ml-3 text-sm font-medium text-gray-700">{name}</span>
                        </label>
                    ))}
                </div>
            </div>

            {/* Buttons */}
            <div className="flex space-x-3">
                <button
                    onClick={async () => {
                        setIsSaving(true);
                        try {
                            const slaveId = selectedDevice.slave_id;
                            const comPort = selectedDevice.com_port || selectedComPort;
                            await pyrometerAPI.setMeasurementMode(measurementMode, slaveId, comPort);
                            setMessage({ type: 'success', text: 'Measurement mode saved successfully' });
                        } catch (error) {
                            setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to save' });
                        } finally {
                            setIsSaving(false);
                        }
                    }}
                    disabled={isLoading || isSaving || !selectedDevice || !pollingPaused}
                    className="flex-1 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed font-semibold"
                >
                    {isSaving ? 'Saving...' : 'Save Mode'}
                </button>
                <button
                    onClick={loadAllParameters}
                    disabled={isLoading || isSaving || !selectedDevice || !pollingPaused}
                    className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                >
                    Refresh
                </button>
            </div>

            {/* Info */}
            <div className="p-3 bg-blue-50 rounded-lg text-xs text-blue-800">
                <p className="font-semibold mb-1">About Measurement Mode:</p>
                <p>Monochrome: Single wavelength temperature measurement. Colorimetric: Dual wavelength ratio measurement.</p>
            </div>
        </div>
    );

    const renderTimeIntervalTab = () => (
        <div className="space-y-4">
            {/* Current Value */}
            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-600">Current Interval:</span>
                    {isLoading ? (
                        <div className="animate-pulse bg-gray-300 h-6 w-20 rounded"></div>
                    ) : (
                        <span className="text-2xl font-bold text-orange-600">{timeInterval}s</span>
                    )}
                </div>
            </div>

            {/* Input */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Time Interval (seconds)
                    <span className="text-gray-500 font-normal ml-2">({MIN_TIME_INTERVAL} - {MAX_TIME_INTERVAL})</span>
                </label>
                <input
                    type="number"
                    value={timeIntervalInput}
                    onChange={(e) => {
                        setTimeIntervalInput(e.target.value);
                        setMessage({ type: '', text: '' });
                    }}
                    step="1"
                    min={MIN_TIME_INTERVAL}
                    max={MAX_TIME_INTERVAL}
                    disabled={isLoading || isSaving || !selectedDevice || !pollingPaused}
                    className="w-full px-4 py-3 text-lg border-2 rounded-lg focus:outline-none focus:border-orange-500 disabled:bg-gray-100"
                    placeholder="Enter time interval (e.g., 1)"
                />
            </div>

            {/* Buttons */}
            <div className="flex space-x-3">
                <button
                    onClick={async () => {
                        const value = parseInt(timeIntervalInput);
                        if (isNaN(value) || value < MIN_TIME_INTERVAL || value > MAX_TIME_INTERVAL) {
                            setMessage({ type: 'error', text: `Invalid time interval` });
                            return;
                        }
                        setIsSaving(true);
                        try {
                            const slaveId = selectedDevice.slave_id;
                            const comPort = selectedDevice.com_port || selectedComPort;
                            await pyrometerAPI.setTimeInterval(value, slaveId, comPort);
                            setTimeInterval(value);
                            setMessage({ type: 'success', text: 'Time interval saved successfully' });
                        } catch (error) {
                            setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to save' });
                        } finally {
                            setIsSaving(false);
                        }
                    }}
                    disabled={isLoading || isSaving || !selectedDevice || !pollingPaused}
                    className="flex-1 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:bg-gray-300 disabled:cursor-not-allowed font-semibold"
                >
                    {isSaving ? 'Saving...' : 'Save Interval'}
                </button>
                <button
                    onClick={loadAllParameters}
                    disabled={isLoading || isSaving || !selectedDevice || !pollingPaused}
                    className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                >
                    Refresh
                </button>
            </div>

            {/* Info */}
            <div className="p-3 bg-blue-50 rounded-lg text-xs text-blue-800">
                <p className="font-semibold mb-1">About Time Interval:</p>
                <p>Measurement sampling interval in seconds. Defines how often the device takes temperature readings.</p>
            </div>
        </div>
    );

    const renderTemperatureLimitsTab = () => (
        <div className="space-y-4">
            {/* Current Values */}
            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 space-y-3">
                <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-600">Lower Limit:</span>
                    {isLoading ? (
                        <div className="animate-pulse bg-gray-300 h-6 w-20 rounded"></div>
                    ) : (
                        <span className="text-xl font-bold text-blue-600">{tempLowerLimit}°C</span>
                    )}
                </div>
                <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-600">Upper Limit:</span>
                    {isLoading ? (
                        <div className="animate-pulse bg-gray-300 h-6 w-20 rounded"></div>
                    ) : (
                        <span className="text-xl font-bold text-red-600">{tempUpperLimit}°C</span>
                    )}
                </div>
            </div>

            {/* Lower Limit Input */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Lower Temperature Limit (°C)
                    <span className="text-gray-500 font-normal ml-2">({MIN_TEMP} - {MAX_TEMP})</span>
                </label>
                <input
                    type="number"
                    value={tempLowerLimitInput}
                    onChange={(e) => {
                        setTempLowerLimitInput(e.target.value);
                        setMessage({ type: '', text: '' });
                    }}
                    step="1"
                    min={MIN_TEMP}
                    max={MAX_TEMP}
                    disabled={isLoading || isSaving || !selectedDevice || !pollingPaused}
                    className="w-full px-4 py-3 text-lg border-2 rounded-lg focus:outline-none focus:border-blue-500 disabled:bg-gray-100"
                />
            </div>

            {/* Upper Limit Input */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Upper Temperature Limit (°C)
                    <span className="text-gray-500 font-normal ml-2">({MIN_TEMP} - {MAX_TEMP})</span>
                </label>
                <input
                    type="number"
                    value={tempUpperLimitInput}
                    onChange={(e) => {
                        setTempUpperLimitInput(e.target.value);
                        setMessage({ type: '', text: '' });
                    }}
                    step="1"
                    min={MIN_TEMP}
                    max={MAX_TEMP}
                    disabled={isLoading || isSaving || !selectedDevice || !pollingPaused}
                    className="w-full px-4 py-3 text-lg border-2 rounded-lg focus:outline-none focus:border-red-500 disabled:bg-gray-100"
                />
            </div>

            {/* Buttons */}
            <div className="flex space-x-3">
                <button
                    onClick={async () => {
                        const lower = parseInt(tempLowerLimitInput);
                        const upper = parseInt(tempUpperLimitInput);
                        if (isNaN(lower) || isNaN(upper) || lower < MIN_TEMP || upper > MAX_TEMP || lower >= upper) {
                            setMessage({ type: 'error', text: `Invalid temperature limits` });
                            return;
                        }
                        setIsSaving(true);
                        try {
                            const slaveId = selectedDevice.slave_id;
                            const comPort = selectedDevice.com_port || selectedComPort;
                            await pyrometerAPI.setTempLowerLimit(lower, slaveId, comPort);
                            await pyrometerAPI.setTempUpperLimit(upper, slaveId, comPort);
                            setTempLowerLimit(lower);
                            setTempUpperLimit(upper);
                            setMessage({ type: 'success', text: 'Temperature limits saved successfully' });
                        } catch (error) {
                            setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to save' });
                        } finally {
                            setIsSaving(false);
                        }
                    }}
                    disabled={isLoading || isSaving || !selectedDevice || !pollingPaused}
                    className="flex-1 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-300 disabled:cursor-not-allowed font-semibold"
                >
                    {isSaving ? 'Saving...' : 'Save Limits'}
                </button>
                <button
                    onClick={loadAllParameters}
                    disabled={isLoading || isSaving || !selectedDevice || !pollingPaused}
                    className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                >
                    Refresh
                </button>
            </div>

            {/* Info */}
            <div className="p-3 bg-blue-50 rounded-lg text-xs text-blue-800">
                <p className="font-semibold mb-1">About Temperature Limits:</p>
                <p>User-defined temperature measurement range. Values outside this range may trigger alarms or warnings.</p>
            </div>
        </div>
    );

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">

                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b">
                    <div className="flex items-center space-x-3">
                        <div className="bg-green-100 p-2 rounded-lg">
                            <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                            </svg>
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-gray-800">Pyrometer Settings</h2>
                            <p className="text-sm text-gray-500">Configure device parameters</p>
                        </div>
                    </div>
                    <button onClick={handleClose} className="text-gray-500 hover:text-gray-700 transition">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto">
                    <div className="p-6">
                        {/* Polling Paused Banner */}
                        <div className={`mb-6 p-4 rounded-lg border ${
                            pollingPaused ? 'bg-yellow-50 border-yellow-200' : 'bg-blue-50 border-blue-200'
                        }`}>
                            <div className="flex items-center space-x-2">
                                {pollingPaused ? (
                                    <>
                                        <svg className="w-5 h-5 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
                                            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                        </svg>
                                        <p className="text-sm text-yellow-800">
                                            <span className="font-semibold">⚠️ Polling Paused</span> - Will resume when you close this window
                                        </p>
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

                        {/* Device Selection */}
                        <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
                            <h3 className="text-sm font-semibold text-gray-700 mb-3">Device Selection</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-medium text-gray-600 mb-1">Device (Instrument ID)</label>
                                    <select
                                        value={selectedDevice?.id || ''}
                                        onChange={(e) => {
                                            const device = devices.find(d => d.id === parseInt(e.target.value));
                                            setSelectedDevice(device);
                                            if (device && device.com_port) {
                                                setSelectedComPort(device.com_port);
                                            }
                                        }}
                                        disabled={isLoading || isSaving || devices.length === 0 || !pollingPaused}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-green-500 focus:outline-none disabled:bg-gray-100"
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
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-gray-600 mb-1">COM Port</label>
                                    <select
                                        value={selectedComPort}
                                        onChange={(e) => setSelectedComPort(e.target.value)}
                                        disabled={isLoading || isSaving || !pollingPaused}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-green-500 focus:outline-none disabled:bg-gray-100"
                                    >
                                        {comPorts.map((port, idx) => (
                                            <option key={idx} value={port.port}>
                                                {port.port} - {port.description}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                        </div>

                        {/* Tabs */}
                        <div className="mb-6">
                            <div className="flex space-x-1 border-b border-gray-200 overflow-x-auto">
                                {tabs.map(tab => (
                                    <button
                                        key={tab.id}
                                        onClick={() => setActiveTab(tab.id)}
                                        className={`px-4 py-2 font-medium text-sm whitespace-nowrap transition ${
                                            activeTab === tab.id
                                                ? 'border-b-2 border-green-600 text-green-600'
                                                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
                                        }`}
                                    >
                                        <span className="mr-2">{tab.icon}</span>
                                        {tab.name}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Tab Content */}
                        <div className="mb-4">
                            {activeTab === 'emissivity' && renderEmissivityTab()}
                            {activeTab === 'slope' && renderSlopeTab()}
                            {activeTab === 'mode' && renderMeasurementModeTab()}
                            {activeTab === 'interval' && renderTimeIntervalTab()}
                            {activeTab === 'limits' && renderTemperatureLimitsTab()}
                        </div>

                        {/* Message Display */}
                        {message.text && (
                            <div className={`p-3 rounded-lg text-sm ${
                                message.type === 'success'
                                    ? 'bg-green-50 text-green-800 border border-green-200'
                                    : 'bg-red-50 text-red-800 border border-red-200'
                            }`}>
                                {message.text}
                            </div>
                        )}
                    </div>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-end p-4 border-t bg-gray-50">
                    <button
                        onClick={handleClose}
                        className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 transition font-medium"
                    >
                        Close (Resume Polling)
                    </button>
                </div>

            </div>
        </div>
    );
}

export default PyrometerSettingsPage;
