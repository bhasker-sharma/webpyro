import { useState, useEffect } from 'react';

function ConfigModal({ isOpen, onClose, devices, onSave }) {
    const [configDevices, setConfigDevices] = useState([]);
    // Common configuration fields for all devices
    const [commonConfig, setCommonConfig] = useState({
        com_port: 'COM3',
        register_address: 0,
        function_code: 3,
        start_register: 0,
        register_count: 2
    });

    useEffect(() => {
        if (isOpen) {
            initializeDevices();
        }
    }, [isOpen, devices]);

    const initializeDevices = async () => {
        try {
            if (devices && devices.length > 0) {
                // Load existing devices from database
                console.log('Loading devices from backend:', devices);
                // Extract common config from the first device
                if (devices[0]) {
                    setCommonConfig({
                        com_port: devices[0].com_port || 'COM3',
                        register_address: devices[0].register_address || 0,
                        function_code: devices[0].function_code || 3,
                        start_register: devices[0].start_register || 0,
                        register_count: devices[0].register_count || 2
                    });
                }
                setConfigDevices(devices);
            } else {
                // Start with one empty row if no devices exist
                setConfigDevices([createNewDevice(1)]);
            }
        } catch (err) {
            console.error('Error initializing devices:', err);
        }
    };

    const createNewDevice = (deviceNum) => {
        return {
            id: null, // null for new devices (not yet in DB)
            name: `Device ${deviceNum}`,
            slave_id: deviceNum,
            baud_rate: 9600,
            enabled: true,
            show_in_graph: false
        };
    };

    const handleCommonConfigChange = (field, value) => {
        setCommonConfig({ ...commonConfig, [field]: value });
    };

    const handleChange = (index, field, value) => {
        const updated = [...configDevices];
        updated[index] = { ...updated[index], [field]: value };
        setConfigDevices(updated);
    };

    const handleToggleEnable = (index) => {
        const updated = [...configDevices];
        updated[index] = { ...updated[index], enabled: !updated[index].enabled };
        // If disabling a device, also uncheck graph
        if (!updated[index].enabled) {
            updated[index].show_in_graph = false;
        }
        setConfigDevices(updated);
    };

    const handleToggleGraph = (index) => {
        const updated = [...configDevices];
        // Only allow toggling graph if device is enabled
        if (updated[index].enabled) {
            updated[index] = { ...updated[index], show_in_graph: !updated[index].show_in_graph };
            setConfigDevices(updated);
        }
    };

    const handleAddRow = () => {
        if (configDevices.length < 16) {
            // Find the next available slave_id
            const existingSlaveIds = configDevices.map(d => d.slave_id);
            let nextSlaveId = 1;
            while (existingSlaveIds.includes(nextSlaveId) && nextSlaveId <= 247) {
                nextSlaveId++;
            }
            setConfigDevices([...configDevices, createNewDevice(nextSlaveId)]);
        }
    };

    const handleDeleteRow = (index) => {
        const updated = configDevices.filter((_, i) => i !== index);
        // Keep existing slave_ids, don't reassign them
        setConfigDevices(updated);
    };

    const handleSave = () => {
        // Apply common config to all devices before saving
        const devicesWithCommonConfig = configDevices.map(device => ({
            ...device,
            ...commonConfig
        }));
        console.log('Saving devices:', devicesWithCommonConfig);
        onSave(devicesWithCommonConfig);
        onClose();
    };

    if (!isOpen) return null;

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

                <div className="flex-1 overflow-auto p-4">
                    <div className="mb-4 text-sm text-gray-600">
                        Add devices one by one (maximum 16 devices). Use the + button to add new rows, - button to delete rows, and toggle to enable/disable devices.
                    </div>

                    {/* Common Configuration Section */}
                    <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <h3 className="text-sm font-semibold text-gray-800 mb-3 flex items-center">
                            <svg className="w-4 h-4 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                            </svg>
                            Common Configuration (Applied to All Devices)
                        </h3>
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                            <div>
                                <label className="block text-xs font-medium text-gray-700 mb-1">COM Port</label>
                                <select
                                    value={commonConfig.com_port}
                                    onChange={(e) => handleCommonConfigChange('com_port', e.target.value)}
                                    className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded bg-white"
                                >
                                    {Array.from({ length: 20 }, (_, i) => (
                                        <option key={i} value={`COM${i + 1}`}>COM{i + 1}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-gray-700 mb-1">Register Addr</label>
                                <input
                                    type="number"
                                    value={commonConfig.register_address}
                                    onChange={(e) => handleCommonConfigChange('register_address', parseInt(e.target.value) || 0)}
                                    className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded bg-white"
                                    min="0"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-gray-700 mb-1">Function Code</label>
                                <select
                                    value={commonConfig.function_code}
                                    onChange={(e) => handleCommonConfigChange('function_code', parseInt(e.target.value))}
                                    className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded bg-white"
                                >
                                    <option value="3">3</option>
                                    <option value="4">4</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-gray-700 mb-1">Start Reg</label>
                                <input
                                    type="number"
                                    value={commonConfig.start_register}
                                    onChange={(e) => handleCommonConfigChange('start_register', parseInt(e.target.value) || 0)}
                                    className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded bg-white"
                                    min="0"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-gray-700 mb-1">Reg Count</label>
                                <input
                                    type="number"
                                    value={commonConfig.register_count}
                                    onChange={(e) => handleCommonConfigChange('register_count', parseInt(e.target.value) || 1)}
                                    className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded bg-white"
                                    min="1"
                                />
                            </div>
                        </div>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full border-collapse border border-gray-300">
                            <thead className="bg-gray-100 sticky top-0">
                                <tr>
                                    <th className="border border-gray-300 px-2 py-2 text-left text-xs font-semibold">Enable</th>
                                    <th className="border border-gray-300 px-2 py-2 text-left text-xs font-semibold">Graph</th>
                                    <th className="border border-gray-300 px-2 py-2 text-left text-xs font-semibold">Device #</th>
                                    <th className="border border-gray-300 px-2 py-2 text-left text-xs font-semibold">Name</th>
                                    <th className="border border-gray-300 px-2 py-2 text-left text-xs font-semibold">Slave ID</th>
                                    <th className="border border-gray-300 px-2 py-2 text-left text-xs font-semibold">Baud Rate</th>
                                    <th className="border border-gray-300 px-2 py-2 text-center text-xs font-semibold">Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {configDevices.map((device, index) => (
                                    <tr key={index} className={device.enabled ? "bg-blue-50" : "bg-white"}>
                                        <td className="border border-gray-300 px-2 py-2 text-center">
                                            <button
                                                onClick={() => handleToggleEnable(index)}
                                                className={`w-12 h-6 rounded-full transition ${device.enabled ? 'bg-green-500' : 'bg-gray-300'}`}
                                            >
                                                <div className={`w-5 h-5 bg-white rounded-full shadow transform transition ${device.enabled ? 'translate-x-6' : 'translate-x-0.5'}`} />
                                            </button>
                                        </td>
                                        <td className="border border-gray-300 px-2 py-2 text-center">
                                            {device.enabled ? (
                                                <input
                                                    type="checkbox"
                                                    checked={device.show_in_graph || false}
                                                    onChange={() => handleToggleGraph(index)}
                                                    className="w-5 h-5 cursor-pointer accent-blue-600"
                                                    title="Show in graph"
                                                />
                                            ) : (
                                                <span className="text-gray-300 text-xs">—</span>
                                            )}
                                        </td>
                                        <td className="border border-gray-300 px-2 py-2 text-center font-semibold text-sm">
                                            {index + 1}
                                        </td>
                                        <td className="border border-gray-300 px-2 py-2">
                                            <input
                                                type="text"
                                                value={device.name}
                                                onChange={(e) => handleChange(index, 'name', e.target.value)}
                                                className="w-full px-2 py-1 text-sm border rounded bg-white"
                                                placeholder="Device Name"
                                            />
                                        </td>
                                        <td className="border border-gray-300 px-2 py-2">
                                            <input
                                                type="number"
                                                value={device.slave_id}
                                                onChange={(e) => handleChange(index, 'slave_id', parseInt(e.target.value) || 1)}
                                                className="w-20 px-2 py-1 text-sm border rounded bg-white"
                                                min="1"
                                                max="247"
                                            />
                                        </td>
                                        <td className="border border-gray-300 px-2 py-2">
                                            <select
                                                value={device.baud_rate}
                                                onChange={(e) => handleChange(index, 'baud_rate', parseInt(e.target.value))}
                                                className="w-24 px-2 py-1 text-sm border rounded bg-white"
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
                                        </td>
                                        <td className="border border-gray-300 px-2 py-2 text-center">
                                            {index === configDevices.length - 1 && configDevices.length < 16 ? (
                                                <button
                                                    onClick={handleAddRow}
                                                    className="w-8 h-8 bg-green-500 text-white rounded-full hover:bg-green-600 transition flex items-center justify-center mx-auto font-bold text-lg"
                                                    title="Add new device"
                                                >
                                                    +
                                                </button>
                                            ) : (
                                                <button
                                                    onClick={() => handleDeleteRow(index)}
                                                    className="w-8 h-8 bg-red-500 text-white rounded-full hover:bg-red-600 transition flex items-center justify-center mx-auto font-bold text-lg"
                                                    title="Delete device"
                                                >
                                                    -
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div className="flex items-center justify-between p-4 border-t bg-gray-50">
                    <div className="text-sm text-gray-600">
                        <span className="font-semibold">{configDevices.filter(d => d.enabled).length}</span> enabled /
                        <span className="font-semibold ml-2">{configDevices.filter(d => d.show_in_graph).length}</span> in graph /
                        <span className="font-semibold ml-2">{configDevices.length}</span> total
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