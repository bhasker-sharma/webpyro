import { useState, useEffect } from 'react';
import ConfigModal from '../components/ConfigModal';
import GraphSection from '../components/GraphSection';
import { deviceAPI, readingAPI, pollingAPI, configAPI } from '../services/api';
import { websocketService } from '../services/websocket';

function DashboardPage({ configModalOpen, setConfigModalOpen }) {
    const [devices, setDevices] = useState([]); // Only enabled devices for display
    const [allDevices, setAllDevices] = useState([]); // All devices for modal
    const [devicesWithReadings, setDevicesWithReadings] = useState([]); // Devices enriched with latest readings
    const [pollingStats, setPollingStats] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [wsConnected, setWsConnected] = useState(false); // WebSocket connection state
    const [activeAlarms, setActiveAlarms] = useState(new Set()); // Track devices with active alarms

    useEffect(() => {
        console.log('Dashboard mounted');
        fetchDevices();
        fetchPollingStats();
        // Note: We do NOT fetch readings from database on mount
        // Readings will only come from WebSocket

        // Connect to WebSocket for real-time updates (auto-detects correct URL)
        websocketService.connect();

        // Handle WebSocket connection state changes
        const handleConnection = (data) => {
            console.log('WebSocket connection state:', data.connected);
            setWsConnected(data.connected);

            // Clear readings and alarms when WebSocket disconnects
            if (!data.connected) {
                console.log('WebSocket disconnected - clearing readings and alarms');
                setDevicesWithReadings([]);
                setActiveAlarms(new Set()); // Clear all active alarms
            }
        };

        // Listen for real-time reading updates
        const handleReadingUpdate = (data) => {
            // Check for ambient temperature alarm (> 65°C)
            const AMBIENT_TEMP_THRESHOLD = 65;
            if (data.ambient_temp !== null && data.ambient_temp !== undefined && data.ambient_temp >= AMBIENT_TEMP_THRESHOLD) {
                setActiveAlarms(prev => {
                    const newAlarms = new Set(prev);
                    if (!newAlarms.has(data.device_id)) {
                        newAlarms.add(data.device_id);
                        console.log(`🚨 ALARM TRIGGERED: Device "${data.device_name}" (ID: ${data.device_id}) - Ambient: ${data.ambient_temp.toFixed(1)}°C > ${AMBIENT_TEMP_THRESHOLD}°C`);
                        console.log(`📊 Active alarms now:`, Array.from(newAlarms));
                    }
                    return newAlarms;
                });
            } else {
                // Clear alarm if temperature is back to normal
                setActiveAlarms(prev => {
                    const newAlarms = new Set(prev);
                    if (newAlarms.has(data.device_id)) {
                        newAlarms.delete(data.device_id);
                        console.log(`✅ ALARM CLEARED: Device "${data.device_name}" (ID: ${data.device_id}) - Ambient: ${data.ambient_temp?.toFixed(1)}°C ≤ ${AMBIENT_TEMP_THRESHOLD}°C`);
                        console.log(`📊 Active alarms now:`, Array.from(newAlarms));
                    }
                    return newAlarms;
                });
            }

            // Update the device reading immediately
            setDevicesWithReadings(prev => {
                const updated = [...prev];
                const index = updated.findIndex(r => r.device_id === data.device_id);

                if (index !== -1) {
                    // Update existing device
                    updated[index] = {
                        ...updated[index],
                        latest_reading: {
                            temperature: data.temperature,
                            ambient_temp: data.ambient_temp,
                            status: data.status,
                            timestamp: data.timestamp,
                            raw_hex: data.raw_hex,
                            error_message: data.error_message || ''
                        }
                    };
                } else {
                    // Add new device reading
                    updated.push({
                        device_id: data.device_id,
                        device_name: data.device_name,
                        latest_reading: {
                            temperature: data.temperature,
                            ambient_temp: data.ambient_temp,
                            status: data.status,
                            timestamp: data.timestamp,
                            raw_hex: data.raw_hex,
                            error_message: data.error_message || ''
                        }
                    });
                }

                return updated;
            });
        };

        // Register WebSocket event listeners
        websocketService.on('connection', handleConnection);
        websocketService.on('reading_update', handleReadingUpdate);

        // Only poll for stats (NOT readings from database)
        const intervalId = setInterval(() => {
            fetchPollingStats();
        }, 5000);

        // Cleanup on unmount
        return () => {
            clearInterval(intervalId);
            websocketService.off('connection', handleConnection);
            websocketService.off('reading_update', handleReadingUpdate);
            websocketService.disconnect();
        };
    }, []);

    // Calculate grid columns based on number of devices and screen size
    const getGridColumns = () => {
        const count = devices.length;
        if (count === 0) return 'grid-cols-1';
        if (count === 1) return 'grid-cols-1 sm:grid-cols-1';
        if (count === 2) return 'grid-cols-1 sm:grid-cols-2';
        if (count <= 6) return 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3';
        if (count <= 12) return 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4';
        return 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4';  // 13-16 devices
    };

    const fetchDevices = async () => {
        setLoading(true);
        setError(null);
        try {
            const enabledData = await deviceAPI.getAll(true); // For display
            const allData = await deviceAPI.getAll(false); // For modal
            setDevices(enabledData);
            setAllDevices(allData);
            console.log('Fetched enabled devices:', enabledData);
            console.log('Fetched all devices:', allData);
        } catch (err) {
            setError('Failed to fetch devices from backend');
            console.error('Error fetching devices:', err);
        } finally {
            setLoading(false);
        }
    };

    const fetchLatestReadings = async () => {
        try {
            const readings = await readingAPI.getLatest();
            console.log('Latest readings:', readings);
            setDevicesWithReadings(readings);
        } catch (err) {
            console.error('Error fetching latest readings:', err);
        }
    };

    const fetchPollingStats = async () => {
        try {
            const stats = await pollingAPI.getStats();
            console.log('Polling stats:', stats);
            setPollingStats(stats);
        } catch (err) {
            console.error('Error fetching polling stats:', err);
        }
    };

    // Helper function to format time ago
    const formatTimeAgo = (timestamp) => {
        if (!timestamp) return 'Never';

        try {
            const now = new Date();

            // Backend sends UTC timestamps without 'Z' suffix, so we need to add it
            // to ensure JavaScript parses it as UTC, not local time
            let utcTimestamp = timestamp;
            if (timestamp && !timestamp.endsWith('Z') && !timestamp.includes('+')) {
                utcTimestamp = timestamp + 'Z';
            }

            const past = new Date(utcTimestamp);

            // Check if the parsed date is valid
            if (isNaN(past.getTime())) {
                console.error('Invalid timestamp:', timestamp);
                return 'Invalid time';
            }

            const diffMs = now - past;
            const diffSec = Math.floor(diffMs / 1000);

            // Handle negative time differences (future timestamps or clock issues)
            if (diffSec < 0) {
                console.warn('Timestamp is in the future:', timestamp);
                return 'Just now';
            }

            // Handle very large time differences (likely data issue)
            if (diffSec > 86400 * 365) { // More than 1 year
                console.warn('Timestamp is more than 1 year old:', timestamp);
                return 'Long ago';
            }

            if (diffSec < 60) return `${diffSec}s ago`;
            const diffMin = Math.floor(diffSec / 60);
            if (diffMin < 60) return `${diffMin}m ago`;
            const diffHour = Math.floor(diffMin / 60);
            if (diffHour < 24) return `${diffHour}h ago`;
            const diffDay = Math.floor(diffHour / 24);
            return `${diffDay}d ago`;
        } catch (error) {
            console.error('Error formatting timestamp:', timestamp, error);
            return 'Error';
        }
    };

    const handleSaveDevices = async (configuredDevices) => {
        setLoading(true);
        setError(null);

        try {
            // Step 1: Update or create devices based on configuration
            // This preserves historical data by updating existing records instead of deleting them
            console.log('Updating/creating devices from table:', configuredDevices);

            for (const device of configuredDevices) {
                const devicePayload = {
                    name: device.name,
                    slave_id: device.slave_id,
                    baud_rate: device.baud_rate,
                    com_port: device.com_port,
                    enabled: device.enabled, // Respect the toggle state
                    show_in_graph: device.show_in_graph || false, // Graph display toggle
                    register_address: device.register_address,
                    function_code: device.function_code,
                    start_register: device.start_register,
                    register_count: device.register_count,
                    graph_y_min: device.graph_y_min !== null && device.graph_y_min !== undefined ? device.graph_y_min : 600,
                    graph_y_max: device.graph_y_max !== null && device.graph_y_max !== undefined ? device.graph_y_max : 2000,
                };

                // Check if this device has an ID (existing device) or not (new device)
                if (device.id) {
                    // Update existing device by ID - this preserves all historical readings
                    await deviceAPI.update(device.id, devicePayload);
                    console.log(`Updated device ID ${device.id}: ${device.name} (enabled: ${device.enabled}, show_in_graph: ${device.show_in_graph}, COM: ${device.com_port})`);
                } else {
                    // Create new device (device doesn't have an ID yet)
                    await deviceAPI.create(devicePayload);
                    console.log(`Created new device: ${device.name} (enabled: ${device.enabled}, show_in_graph: ${device.show_in_graph}, COM: ${device.com_port})`);
                }
            }

            // Step 3: Restart polling service to reload new device configs
            console.log('Restarting polling service...');
            await pollingAPI.restart();
            console.log('Polling service restarted');

            // Step 4: Refresh data from database
            await fetchDevices();
            await fetchLatestReadings();
            await fetchPollingStats();

            setConfigModalOpen(false);
            alert('Devices saved and polling service restarted successfully!');
        } catch (err) {
            setError('Failed to save devices');
            console.error('Error saving devices:', err);
            alert('Error saving devices. Check console for details.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="h-screen bg-gray-50 overflow-hidden">
            <div className="container mx-auto px-2 h-full flex flex-col">
                {/* Alarm Banner */}
                {activeAlarms.size > 0 && (
                    <div className="mt-2 bg-red-600 border-2 border-red-700 rounded-lg shadow-lg px-4 py-3 animate-alarm-blink">
                        <div className="flex items-center space-x-3">
                            <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                            </svg>
                            <div className="flex-1">
                                <p className="text-white font-bold text-sm">
                                    AMBIENT TEMPERATURE ALARM!
                                </p>
                                <p className="text-red-100 text-xs">
                                    {activeAlarms.size} device{activeAlarms.size > 1 ? 's' : ''} exceeded 65°C ambient temperature threshold
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Status Bar */}
                {pollingStats && (
                    <div className="mt-2 bg-white rounded-lg shadow-sm border border-gray-200 px-4 py-2">
                        <div className="flex items-center justify-between text-sm">
                            <div className="flex items-center space-x-6">
                                {/* WebSocket Connection Status */}
                                <div className="flex items-center space-x-2">
                                    <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
                                    <span className={`font-medium ${wsConnected ? 'text-green-600' : 'text-red-600'}`}>
                                        WebSocket: {wsConnected ? 'Connected' : 'Disconnected'}
                                    </span>
                                </div>

                                {/* Show warning icon when disconnected */}
                                {!wsConnected && (
                                    <div className="flex items-center space-x-1 text-red-600">
                                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                        </svg>
                                        <span className="text-xs">Real-time updates unavailable</span>
                                    </div>
                                )}

                                <div className="flex items-center space-x-2">
                                    <span className={`w-2 h-2 rounded-full ${pollingStats.is_running ? 'bg-blue-500 animate-pulse' : 'bg-gray-500'}`}></span>
                                    <span className="text-gray-600">Polling: {pollingStats.is_running ? 'Active' : 'Stopped'}</span>
                                </div>
                                {/* <div className="text-gray-600">
                                    Cycle: <span className="font-semibold text-gray-800">{pollingStats.cycle_count}</span>
                                </div> */}
                                <div className="text-gray-600">
                                    Buffer: <span className="font-semibold text-gray-800">{pollingStats.buffer_stats?.buffer_a_size + pollingStats.buffer_stats?.buffer_b_size || 0}</span>/{pollingStats.buffer_stats?.max_size || 100}
                                </div>
                                {/* <div className="text-gray-600">
                                    Saved: <span className="font-semibold text-gray-800">{pollingStats.buffer_stats?.total_saved || 0}</span>
                                </div> */}
                            </div>
                            <div className="text-xs text-gray-500">
                                Real-time mode
                            </div>
                        </div>
                    </div>
                )}

                <div className="flex flex-col gap-2 pt-2" style={{ height: 'calc(100vh - 48px - 48px)' }}>

                    <section
                        className="bg-white rounded-lg shadow-md p-3 flex flex-col overflow-hidden"
                        style={{ minHeight: 'calc(50% - 4px)', maxHeight: 'calc(50% - 4px)' }}
                    >
                        <div className="flex items-center justify-between mb-2 flex-shrink-0">
                            <h2 className="text-base font-semibold text-gray-700 flex items-center space-x-2">
                                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                </svg>
                                <span>Devices</span>
                            </h2>
                            <span className="text-xs text-gray-500">{devices.length} / 16</span>
                        </div>

                        <div className={`grid ${getGridColumns()} auto-rows-fr gap-2 flex-1 overflow-hidden min-h-0`}>
                            {!wsConnected ? (
                                <div className="col-span-full flex flex-col items-center justify-center">
                                    <svg className="w-16 h-16 text-red-400 mb-3" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                    </svg>
                                    <p className="text-red-600 text-lg font-semibold mb-1">WebSocket Disconnected</p>
                                    <p className="text-gray-500 text-sm mb-2">Real-time data unavailable</p>
                                    <p className="text-gray-400 text-xs">Attempting to reconnect...</p>
                                </div>
                            ) : devices.length === 0 ? (
                                <div className="col-span-full flex flex-col items-center justify-center">
                                    <svg className="w-12 h-12 text-gray-300 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                                    </svg>
                                    <p className="text-gray-500 text-sm mb-1">No devices configured</p>
                                    <p className="text-gray-400 text-xs">Click "Configure Devices" to add devices</p>
                                </div>
                            ) : (
                                devices.map((device) => {
                                    // Find matching reading data for this device
                                    const readingData = devicesWithReadings.find(r => r.device_id === device.id);
                                    const hasAlarm = activeAlarms.has(device.id);
                                    return (
                                        <DeviceCard
                                            key={device.id}
                                            device={device}
                                            reading={readingData?.latest_reading}
                                            formatTimeAgo={formatTimeAgo}
                                            hasAlarm={hasAlarm}
                                        />
                                    );
                                })
                            )}
                        </div>
                    </section>

                    <section
                        className="bg-white rounded-lg shadow-md p-3 flex flex-col overflow-hidden"
                        style={{ minHeight: 'calc(50% - 4px)', maxHeight: 'calc(50% - 4px)' }}
                    >
                        <h2 className="text-base font-semibold text-gray-700 mb-2 flex items-center space-x-2 flex-shrink-0">
                            <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                            </svg>
                            <span>Temperature Trends</span>
                        </h2>

                        <div className="flex-1 min-h-0 overflow-hidden">
                            <GraphSection
                                devices={devices}
                                devicesWithReadings={devicesWithReadings}
                            />
                        </div>
                    </section>

                </div>
            </div>

            <ConfigModal
                isOpen={configModalOpen}
                onClose={() => setConfigModalOpen(false)}
                devices={allDevices}
                onSave={handleSaveDevices}
            />
        </div>
    );
}

function DeviceCard({ device, reading, formatTimeAgo, hasAlarm }) {
    const getStatusColor = (status) => {
        switch (status) {
            case 'OK': return 'bg-green-100 text-green-800 border-green-300';
            case 'Stale': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
            case 'Err': return 'bg-red-100 text-red-800 border-red-300';
            default: return 'bg-gray-100 text-gray-800 border-gray-300';
        }
    };

    const getCardGradient = (status) => {
        switch (status) {
            case 'OK': return 'from-green-50 to-green-100 border-green-200';
            case 'Stale': return 'from-yellow-50 to-yellow-100 border-yellow-200';
            case 'Err': return 'from-red-50 to-red-100 border-red-200';
            default: return 'from-blue-50 to-blue-100 border-blue-200';
        }
    };

    const temperature = reading?.temperature;
    const ambientTemp = reading?.ambient_temp;
    const status = reading?.status || 'N/A';
    const timestamp = reading?.timestamp;
    const timeAgo = timestamp ? formatTimeAgo(timestamp) : 'Never';
    const errorMessage = reading?.error_message || '';

    return (
        <div className={`bg-gradient-to-br ${getCardGradient(status)} rounded-lg p-2 border hover:shadow-lg transition flex flex-col justify-between min-h-0 ${hasAlarm ? 'animate-alarm-blink border-4 border-red-600' : ''}`}>
            <div className="flex items-center justify-between mb-1">
                <h3 className="font-semibold text-gray-800 text-xs truncate flex-1">{device.name}</h3>
                <span className="text-[10px] text-gray-500 ml-1">ID:{device.slave_id}</span>
            </div>

            <div className="text-center flex-1 flex flex-col items-center justify-center min-h-0">
                {status === 'Err' ? (
                    <>
                        {/* Error Icon */}
                        <svg className="w-8 h-8 text-red-500 mb-1" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                        </svg>
                        {/* Temperature or placeholder */}
                        <div className="text-xl lg:text-2xl font-bold text-red-600">
                            {temperature !== null && temperature !== undefined ? `${temperature.toFixed(1)}°C` : '--°C'}
                        </div>
                        {/* Ambient Temperature - Enhanced visibility */}
                        {ambientTemp !== null && ambientTemp !== undefined && (
                            <div className={`mt-1 px-2 py-0.5 ${hasAlarm ? 'bg-red-600 border-red-700 text-white' : 'bg-blue-50 border-blue-200 text-blue-700'} border rounded text-xs font-semibold`}>
                                {hasAlarm ? '🚨' : '🌡️'} Ambient: {ambientTemp.toFixed(1)}°C {hasAlarm ? '⚠️' : ''}
                            </div>
                        )}
                        {/* Error Message */}
                        {errorMessage && (
                            <div className="text-[10px] text-red-700 font-medium mt-1 px-2 text-center line-clamp-2">
                                {errorMessage}
                            </div>
                        )}
                    </>
                ) : (
                    <>
                        <div className={`text-xl lg:text-2xl font-bold ${status === 'OK' ? 'text-green-600' : 'text-gray-600'}`}>
                            {temperature !== null && temperature !== undefined ? `${temperature.toFixed(1)}°C` : '--°C'}
                        </div>
                        {/* Ambient Temperature - Enhanced visibility */}
                        {ambientTemp !== null && ambientTemp !== undefined && (
                            <div className={`mt-1 px-2 py-0.5 ${hasAlarm ? 'bg-red-600 border-red-700 text-white' : 'bg-blue-50 border-blue-200 text-blue-700'} border rounded text-xs font-semibold`}>
                                {hasAlarm ? '🚨' : '🌡️'} Ambient: {ambientTemp.toFixed(1)}°C {hasAlarm ? '⚠️' : ''}
                            </div>
                        )}
                    </>
                )}
            </div>

            <div className="space-y-0.5">
                <div className="flex items-center justify-between text-[10px]">
                    <span className="text-gray-600 truncate">{device.com_port}</span>
                    <span className={`px-1.5 py-0.5 rounded-full text-[9px] font-medium border ${getStatusColor(status)}`}>
                        {status}
                    </span>
                </div>
            </div>
        </div>
    );
}

export default DashboardPage;