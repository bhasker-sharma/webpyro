import { useState, useEffect } from 'react';
import ConfigModal from '../components/ConfigModal';

function DashboardPage({ configModalOpen, setConfigModalOpen }) {
    const [devices, setDevices] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        console.log('Dashboard mounted');
    }, []);

    const handleSaveDevices = (allDevices) => {
        console.log('Saving devices:', allDevices);
        // Filter only enabled devices for display
        const enabledOnly = allDevices.filter(device => device.enabled);
        setDevices(enabledOnly);
        setConfigModalOpen(false);
    };

    // Calculate grid columns based on number of devices
    const getGridColumns = () => {
        const count = devices.length;
        if (count === 0) return 'grid-cols-1';
        if (count === 1) return 'grid-cols-1';
        if (count === 2) return 'grid-cols-2';
        if (count <= 6) return 'grid-cols-3';
        if (count <= 12) return 'grid-cols-4';
        return 'grid-cols-4';  // 13-16 devices also use 4 columns
    };

    const fetchDevices = async () => {
        setLoading(true);
        try {
            // const response = await axios.get('http://localhost:8000/api/devices');
            // setDevices(response.data);
        } catch (err) {
            setError('Failed to fetch devices');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="h-screen bg-gray-50 overflow-hidden">
            <div className="container mx-auto px-2 h-full flex flex-col">
                <div className="flex flex-col gap-2 pt-2" style={{ height: 'calc(100vh - 48px)' }}>

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
                            {devices.length === 0 ? (
                                <div className="col-span-full flex flex-col items-center justify-center">
                                    <svg className="w-12 h-12 text-gray-300 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                                    </svg>
                                    <p className="text-gray-500 text-sm mb-1">No devices configured</p>
                                    <p className="text-gray-400 text-xs">Click "Configure Devices" to add devices</p>
                                </div>
                            ) : (
                                devices.map((device) => <DeviceCard key={device.id} device={device} />)
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

                        <div className="flex-1 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center">
                            <div className="text-center">
                                <svg className="w-12 h-12 mx-auto text-gray-300 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                                </svg>
                                <p className="text-gray-400 text-sm">Graphs Section</p>
                                <p className="text-gray-400 text-xs">Future implementation</p>
                            </div>
                        </div>
                    </section>

                </div>
            </div>

            <ConfigModal
                isOpen={configModalOpen}
                onClose={() => setConfigModalOpen(false)}
                devices={devices}
                onSave={handleSaveDevices}
            />
        </div>
    );
}

function DeviceCard({ device }) {
    const getStatusColor = (status) => {
        switch (status) {
            case 'OK': return 'bg-green-100 text-green-800 border-green-300';
            case 'Stale': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
            case 'Err': return 'bg-red-100 text-red-800 border-red-300';
            default: return 'bg-gray-100 text-gray-800 border-gray-300';
        }
    };

    return (
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-2 border border-blue-200 hover:shadow-lg transition flex flex-col justify-between min-h-0">
            <div className="flex items-center justify-between mb-1">
                <h3 className="font-semibold text-gray-800 text-xs truncate flex-1">{device.name}</h3>
                <span className="text-[10px] text-gray-500 ml-1">ID:{device.slave_id}</span>
            </div>

            <div className="text-center flex-1 flex items-center justify-center min-h-0">
                <div className="text-xl lg:text-2xl font-bold text-blue-600">
                    {device.temperature || '--'}°C
                </div>
            </div>

            <div className="space-y-0.5">
                <div className="flex items-center justify-between text-[10px]">
                    <span className="text-gray-600 truncate">{device.com_port}</span>
                    <span className={`px-1.5 py-0.5 rounded-full text-[9px] font-medium border ${getStatusColor(device.status || 'N/A')}`}>
                        {device.status || 'N/A'}
                    </span>
                </div>
                <div className="text-[10px] text-gray-500 text-center truncate">
                    {device.last_updated || 'Never'}
                </div>
            </div>
        </div>
    );
}

export default DashboardPage;