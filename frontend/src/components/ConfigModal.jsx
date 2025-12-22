import { useState, useEffect } from 'react';
import { configAPI } from '../services/api';

function ConfigModal({ isOpen, onClose, devices, onSave }) {
    const [availableComPorts, setAvailableComPorts] = useState([]);
    const [showPinDialog, setShowPinDialog] = useState(true);
    const [pinInput, setPinInput] = useState('');
    const [pinError, setPinError] = useState('');
    const [isPinVerified, setIsPinVerified] = useState(false);

    // Single device configuration (slave ID fixed to 1)
    const [deviceConfig, setDeviceConfig] = useState({
        name: 'Pyrometer',
        slave_id: 1, // Fixed to 1 for single device
        baud_rate: 9600,
        com_port: 'COM3',
        enabled: true,
        show_in_graph: true,
        graph_y_min: 600,
        graph_y_max: 2000
    });

    useEffect(() => {
        if (isOpen) {
            // Reset PIN verification when modal opens
            setIsPinVerified(false);
            setShowPinDialog(true);
            setPinInput('');
            setPinError('');
            fetchComPorts();
        }
    }, [isOpen]);

    useEffect(() => {
        if (isOpen && isPinVerified) {
            initializeDevice();
        }
    }, [isOpen, isPinVerified, devices, availableComPorts]);

    const fetchComPorts = async () => {
        try {
            const data = await configAPI.getComPorts();
            setAvailableComPorts(data.ports || []);
            console.log('Available COM ports:', data.ports);

            // Set default COM port if available
            if (data.ports && data.ports.length > 0) {
                setDeviceConfig(prev => ({
                    ...prev,
                    com_port: data.ports[0].port
                }));
            }
        } catch (err) {
            console.error('Error fetching COM ports:', err);
            // Fallback to default COM3 if fetch fails
            setAvailableComPorts([{ port: 'COM3', description: 'Default' }]);
        }
    };

    const handlePinSubmit = async () => {
        try {
            const response = await configAPI.verifyPin(pinInput);
            if (response.valid) {
                setIsPinVerified(true);
                setShowPinDialog(false);
                setPinError('');
            } else {
                setPinError('Invalid PIN. Please try again.');
                setPinInput('');
            }
        } catch (err) {
            console.error('Error verifying PIN:', err);
            setPinError('Error verifying PIN. Please try again.');
        }
    };

    const handlePinKeyPress = (e) => {
        if (e.key === 'Enter') {
            handlePinSubmit();
        }
    };

    const initializeDevice = async () => {
        try {
            if (devices && devices.length > 0) {
                // Load existing device from database (first device if multiple exist)
                console.log('Loading device from backend:', devices[0]);
                const existingDevice = devices[0];
                setDeviceConfig({
                    id: existingDevice.id,
                    name: existingDevice.name || 'Pyrometer',
                    slave_id: 1, // Always 1 for single device
                    baud_rate: existingDevice.baud_rate || 9600,
                    com_port: existingDevice.com_port || (availableComPorts[0]?.port || 'COM3'),
                    enabled: true,
                    show_in_graph: true,
                    graph_y_min: existingDevice.graph_y_min !== null && existingDevice.graph_y_min !== undefined ? existingDevice.graph_y_min : 600,
                    graph_y_max: existingDevice.graph_y_max !== null && existingDevice.graph_y_max !== undefined ? existingDevice.graph_y_max : 2000
                });
            } else {
                // Use default values if no device exists
                console.log('No existing device, using defaults');
            }
        } catch (err) {
            console.error('Error initializing device:', err);
        }
    };

    const handleConfigChange = (field, value) => {
        // Validate Y-range values
        if (field === 'graph_y_min' || field === 'graph_y_max') {
            const numValue = parseFloat(value);
            if (numValue < 600) {
                value = 600;
            } else if (numValue > 2000) {
                value = 2000;
            }
        }
        setDeviceConfig({ ...deviceConfig, [field]: value });
    };

    // Validation helper function
    const getValidationErrors = () => {
        const errors = [];

        // Check device name
        if (!deviceConfig.name || deviceConfig.name.trim() === '') {
            errors.push('Device name cannot be empty');
        }

        // Check Y-range
        if (deviceConfig.graph_y_min < 600 || deviceConfig.graph_y_min > 2000) {
            errors.push('Graph Y-Min must be between 600 and 2000');
        }
        if (deviceConfig.graph_y_max < 600 || deviceConfig.graph_y_max > 2000) {
            errors.push('Graph Y-Max must be between 600 and 2000');
        }
        if (deviceConfig.graph_y_max <= deviceConfig.graph_y_min) {
            errors.push('Graph Y-Max must be greater than Y-Min');
        }

        return errors;
    };


    const handleSave = () => {
        // Validate before saving
        const validationErrors = getValidationErrors();
        if (validationErrors.length > 0) {
            alert('Please fix the following errors:\n\n' + validationErrors.join('\n'));
            return;
        }

        console.log('=== ConfigModal: Saving Single Device Configuration ===');
        console.log('Device Config:', deviceConfig);

        // Send as array with single device for backend compatibility
        onSave([deviceConfig]);
        onClose();
    };

    if (!isOpen) return null;

    // Show PIN dialog first
    if (showPinDialog) {
        return (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-xl font-bold text-gray-800 flex items-center space-x-2">
                            <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                            </svg>
                            <span>Enter Configuration PIN</span>
                        </h2>
                        <button
                            onClick={onClose}
                            className="text-gray-500 hover:text-gray-700 transition"
                        >
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>

                    <p className="text-sm text-gray-600 mb-4">
                        Please enter the 4-digit PIN to access device configuration.
                    </p>

                    <div className="mb-4">
                        <input
                            type="password"
                            value={pinInput}
                            onChange={(e) => {
                                const value = e.target.value.replace(/\D/g, '').slice(0, 4);
                                setPinInput(value);
                                setPinError('');
                            }}
                            onKeyPress={handlePinKeyPress}
                            placeholder="Enter 4-digit PIN"
                            maxLength="4"
                            className="w-full px-4 py-3 text-center text-2xl tracking-widest border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                            autoFocus
                        />
                        {pinError && (
                            <p className="text-red-500 text-sm mt-2 text-center">{pinError}</p>
                        )}
                    </div>

                    <div className="flex space-x-3">
                        <button
                            onClick={onClose}
                            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 transition"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handlePinSubmit}
                            disabled={pinInput.length !== 4}
                            className={`flex-1 px-4 py-2 rounded-lg transition ${
                                pinInput.length === 4
                                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                            }`}
                        >
                            Verify PIN
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-7xl max-h-[90vh] flex flex-col">

                <div className="flex items-center justify-between p-4 border-b">
                    <h2 className="text-xl font-bold text-gray-800 flex items-center space-x-2">
                        <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        <span>Configure Devices</span>
                    </h2>
                    <button
                        onClick={onClose}
                        className="text-gray-500 hover:text-gray-700 transition"
                    >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <div className="flex-1 overflow-auto p-6">
                    <div className="mb-6 text-sm text-gray-600 bg-blue-50 p-4 rounded-lg border border-blue-200">
                        Configure your single pyrometer device. The Instrument ID is fixed to <strong>1</strong> for single-device mode.
                        <br/><br/>
                        <strong>Note:</strong> To configure device parameters like emissivity, use the <strong>Pyrometer Settings</strong> option from the navigation bar.
                    </div>

                    {/* Single Device Configuration Form */}
                    <div className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Device Name
                            </label>
                            <input
                                type="text"
                                value={deviceConfig.name}
                                onChange={(e) => handleConfigChange('name', e.target.value)}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                placeholder="Enter device name (e.g., Furnace 1, Kiln A)"
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    COM Port
                                </label>
                                <select
                                    value={deviceConfig.com_port}
                                    onChange={(e) => handleConfigChange('com_port', e.target.value)}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                >
                                    {availableComPorts.length > 0 ? (
                                        availableComPorts.map((port, idx) => (
                                            <option key={idx} value={port.port}>
                                                {port.port} - {port.description}
                                            </option>
                                        ))
                                    ) : (
                                        <option value="COM3">COM3 (Default)</option>
                                    )}
                                </select>
                                {availableComPorts.length > 0 && (
                                    <p className="text-xs text-green-600 mt-1">
                                        {availableComPorts.length} available port(s) detected
                                    </p>
                                )}
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Baud Rate
                                </label>
                                <select
                                    value={deviceConfig.baud_rate}
                                    onChange={(e) => handleConfigChange('baud_rate', parseInt(e.target.value))}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                >
                                    <option value="1200">1200</option>
                                    <option value="2400">2400</option>
                                    <option value="4800">4800</option>
                                    <option value="9600">9600</option>
                                    <option value="19200">19200</option>
                                    <option value="38400">38400</option>
                                    <option value="57600">57600</option>
                                    <option value="115200">115200</option>
                                </select>
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Instrument ID (Slave ID)
                            </label>
                            <div className="w-full px-4 py-2 bg-gray-100 border border-gray-300 rounded-lg text-gray-600">
                                1 (Fixed for single device mode)
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Graph Y-Min (°C)
                                </label>
                                <input
                                    type="number"
                                    value={deviceConfig.graph_y_min}
                                    onChange={(e) => handleConfigChange('graph_y_min', parseFloat(e.target.value) || 600)}
                                    className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                                        deviceConfig.graph_y_min < 600 || deviceConfig.graph_y_min > 2000 ? 'border-red-500 border-2' : 'border-gray-300'
                                    }`}
                                    min="600"
                                    max="2000"
                                    step="50"
                                    placeholder="600"
                                    title="Must be between 600-2000"
                                />
                                <p className="text-xs text-gray-500 mt-1">Range: 600-2000°C</p>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Graph Y-Max (°C)
                                </label>
                                <input
                                    type="number"
                                    value={deviceConfig.graph_y_max}
                                    onChange={(e) => handleConfigChange('graph_y_max', parseFloat(e.target.value) || 2000)}
                                    className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                                        deviceConfig.graph_y_max < 600 || deviceConfig.graph_y_max > 2000 || deviceConfig.graph_y_max <= deviceConfig.graph_y_min ? 'border-red-500 border-2' : 'border-gray-300'
                                    }`}
                                    min="600"
                                    max="2000"
                                    step="50"
                                    placeholder="2000"
                                    title="Must be between 600-2000 and greater than Y-Min"
                                />
                                <p className="text-xs text-gray-500 mt-1">Range: 600-2000°C, must be {'>'} Y-Min</p>
                            </div>
                        </div>

                        <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                            <p className="text-xs text-gray-600">
                                <strong>Note:</strong> Register settings (register address, function code, etc.) are configured in the backend .env file.
                            </p>
                        </div>
                    </div>
                </div>

                <div className="flex items-center justify-between p-4 border-t bg-gray-50">
                    <div className="text-sm text-gray-600">
                        <span className="font-semibold">Single Device Mode</span> - Instrument ID: 1
                    </div>
                    <div className="flex space-x-3">
                        <button
                            onClick={onClose}
                            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 transition"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleSave}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                        >
                            Save Configuration
                        </button>
                    </div>
                </div>

            </div>
        </div>
    );
}

export default ConfigModal;