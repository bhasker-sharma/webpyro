import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// Get API base URL from environment variable or auto-detect from current hostname
const getApiBaseUrl = () => {
    // If environment variable is set, use it
    if (import.meta.env.VITE_API_BASE_URL) {
        return import.meta.env.VITE_API_BASE_URL;
    }

    // Otherwise, auto-detect based on current hostname
    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
    const hostname = window.location.hostname;
    return `${protocol}//${hostname}:8000`;
};

const API_BASE_URL = getApiBaseUrl();

function PreviewPage() {
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [selectedDevice, setSelectedDevice] = useState('');
    const [devices, setDevices] = useState([]);
    const [previewData, setPreviewData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Set default datetime values on mount
    useEffect(() => {
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0);
        const endOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59);

        // Format to datetime-local format (YYYY-MM-DDTHH:MM)
        const formatDateTime = (date) => {
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            return `${year}-${month}-${day}T${hours}:${minutes}`;
        };

        setStartDate(formatDateTime(today));
        setEndDate(formatDateTime(endOfDay));

        // Fetch devices on mount
        fetchDevices();
    }, []);

    const fetchDevices = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/devices`);
            if (!response.ok) throw new Error('Failed to fetch devices');
            const data = await response.json();
            setDevices(data);
        } catch (err) {
            console.error('Error fetching devices:', err);
            setError('Failed to load devices');
        }
    };

    const handleFilter = async () => {
        if (!selectedDevice) {
            setError('Please select a device');
            return;
        }

        if (!startDate || !endDate) {
            setError('Please select both start and end date');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            // Send datetime as-is without timezone conversion
            // Format: "YYYY-MM-DDTHH:MM:SS"
            const startFormatted = startDate.replace(' ', 'T');
            const endFormatted = endDate.replace(' ', 'T');

            console.log('Filter request:', {
                startDate: startFormatted,
                endDate: endFormatted,
                device_id: selectedDevice
            });

            const url = `${API_BASE_URL}/api/reading/filter?device_id=${selectedDevice}&start_date=${encodeURIComponent(startFormatted)}&end_date=${encodeURIComponent(endFormatted)}`;
            const response = await fetch(url);

            if (!response.ok) throw new Error('Failed to fetch readings');

            const data = await response.json();
            console.log('Filter response:', data);
            setPreviewData(data.readings || []);

            if (data.readings.length === 0) {
                setError('No data found for the selected filters');
            }
        } catch (err) {
            console.error('Error filtering data:', err);
            setError('Failed to load data. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleExportCSV = async () => {
        if (!selectedDevice) {
            setError('Please select a device');
            return;
        }

        if (!startDate || !endDate) {
            setError('Please select both start and end date');
            return;
        }

        try {
            // Send datetime as-is without timezone conversion
            // Format: "YYYY-MM-DDTHH:MM:SS"
            const startFormatted = startDate.replace(' ', 'T');
            const endFormatted = endDate.replace(' ', 'T');

            const url = `${API_BASE_URL}/api/reading/export/csv?device_id=${selectedDevice}&start_date=${encodeURIComponent(startFormatted)}&end_date=${encodeURIComponent(endFormatted)}`;

            // Get device name for filename
            const deviceName = devices.find(d => d.id == selectedDevice)?.name || 'device';
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
            const filename = `${deviceName}_readings_${timestamp}.csv`;

            // Fetch the CSV data
            const response = await fetch(url);
            if (!response.ok) throw new Error('Failed to fetch CSV');
            const blob = await response.blob();

            // Check if File System Access API is supported and if we're in a secure context
            const isSecureContext = window.isSecureContext;
            const hasFilePicker = 'showSaveFilePicker' in window;

            if (hasFilePicker && isSecureContext) {
                try {
                    // Show save dialog (only works on HTTPS or localhost)
                    const handle = await window.showSaveFilePicker({
                        suggestedName: filename,
                        types: [{
                            description: 'CSV Files',
                            accept: { 'text/csv': ['.csv'] }
                        }]
                    });

                    // Write the file
                    const writable = await handle.createWritable();
                    await writable.write(blob);
                    await writable.close();

                    setError(null);
                } catch (err) {
                    // User cancelled the dialog
                    if (err.name !== 'AbortError') {
                        throw err;
                    }
                }
            } else {
                // Fallback: Download directly to browser's default download location
                const blobUrl = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = blobUrl;
                link.download = filename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(blobUrl);

                setError(null);
            }
        } catch (err) {
            console.error('Error exporting data:', err);
            setError('Failed to export data. Please try again.');
        }
    };

    const handleExportPDF = async () => {
        if (!selectedDevice) {
            setError('Please select a device');
            return;
        }

        if (!startDate || !endDate) {
            setError('Please select both start and end date');
            return;
        }

        try {
            // Send datetime as-is without timezone conversion
            // Format: "YYYY-MM-DDTHH:MM:SS"
            const startFormatted = startDate.replace(' ', 'T');
            const endFormatted = endDate.replace(' ', 'T');

            const url = `${API_BASE_URL}/api/reading/export/pdf?device_id=${selectedDevice}&start_date=${encodeURIComponent(startFormatted)}&end_date=${encodeURIComponent(endFormatted)}`;

            // Get device name for filename
            const deviceName = devices.find(d => d.id == selectedDevice)?.name || 'device';
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
            const filename = `${deviceName}_report_${timestamp}.pdf`;

            // Fetch the PDF data
            const response = await fetch(url);
            if (!response.ok) throw new Error('Failed to fetch PDF');
            const blob = await response.blob();

            // Download directly to browser's default download location (works on HTTP)
            const blobUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = blobUrl;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(blobUrl);

            setError(null);
        } catch (err) {
            console.error('Error exporting PDF:', err);
            setError('Failed to export PDF. Please try again.');
        }
    };

    const formatDateTime = (isoString) => {
        if (!isoString) return 'N/A';
        // Extract timestamp string without timezone conversion
        // Format: "YYYY-MM-DD HH:MM:SS" exactly as stored in database
        const timestamp = isoString.replace('T', ' ').replace('Z', '').split('.')[0];
        return timestamp;
    };

    const formatTimeForGraph = (timestamp) => {
        // Extract time portion without timezone conversion
        if (typeof timestamp === 'string') {
            // If timestamp is ISO string, extract time part
            const timePart = timestamp.replace('T', ' ').replace('Z', '').split('.')[0].split(' ')[1];
            return timePart || timestamp;
        }
        // If timestamp is a number (milliseconds), convert to ISO and extract time
        const isoString = new Date(timestamp).toISOString();
        const timePart = isoString.replace('T', ' ').replace('Z', '').split('.')[0].split(' ')[1];
        return timePart;
    };

    // Prepare graph data from preview data
    const graphData = previewData.map(reading => ({
        timestamp: new Date(reading.timestamp).getTime(),
        temperature: reading.value,
        timestampStr: reading.timestamp
    })).sort((a, b) => a.timestamp - b.timestamp);

    return (
        <div className="min-h-screen bg-gray-50">
            <div className="container mx-auto px-4 py-6">
                {/* Header */}
                <div className="mb-6 flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-800 mb-2">Data Preview & Export</h1>
                        <p className="text-gray-600">Filter historical data and export to CSV or PDF</p>
                    </div>
                    <Link
                        to="/"
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center space-x-2 font-medium shadow-md"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                        </svg>
                        <span>Dashboard</span>
                    </Link>
                </div>

                {/* Error Message */}
                {error && (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
                        {error}
                    </div>
                )}

                {/* Filter Section */}
                <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                    <h2 className="text-xl font-semibold text-gray-700 mb-4 flex items-center space-x-2">
                        <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                        </svg>
                        <span>Filter Data</span>
                    </h2>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                        {/* Start Date */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Start Date & Time
                            </label>
                            <input
                                type="datetime-local"
                                value={startDate}
                                onChange={(e) => setStartDate(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                step="60"
                            />
                        </div>

                        {/* End Date */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                End Date & Time
                            </label>
                            <input
                                type="datetime-local"
                                value={endDate}
                                onChange={(e) => setEndDate(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                step="60"
                            />
                        </div>

                        {/* Device Selection */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Select Device
                            </label>
                            <select
                                value={selectedDevice}
                                onChange={(e) => setSelectedDevice(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            >
                                <option value="">-- Select a Device --</option>
                                {devices.map((device) => (
                                    <option key={device.id} value={device.id}>
                                        {device.name}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex space-x-4">
                        <button
                            onClick={handleFilter}
                            disabled={loading}
                            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-2"
                        >
                            {loading ? (
                                <>
                                    <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    <span>Loading...</span>
                                </>
                            ) : (
                                <>
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                    </svg>
                                    <span>Apply Filter</span>
                                </>
                            )}
                        </button>

                        <button
                            onClick={handleExportCSV}
                            disabled={previewData.length === 0}
                            className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-2"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            <span>Export to CSV</span>
                        </button>

                        <button
                            onClick={handleExportPDF}
                            disabled={previewData.length === 0}
                            className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-2"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                            </svg>
                            <span>Export to PDF</span>
                        </button>
                    </div>
                </div>

                {/* Data Preview Section - Split View */}
                <div className="bg-white rounded-lg shadow-md p-6">
                    <h2 className="text-xl font-semibold text-gray-700 mb-4 flex items-center space-x-2">
                        <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <span>Data Preview</span>
                        {previewData.length > 0 && (
                            <span className="text-sm text-gray-500 ml-2">({previewData.length} records)</span>
                        )}
                    </h2>

                    {previewData.length === 0 ? (
                        <div className="text-center py-12">
                            <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            <p className="text-gray-500 text-lg">No data to display</p>
                            <p className="text-gray-400 text-sm mt-2">Apply filters to preview data</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-2 gap-4">
                            {/* Left Side - Data Table with Scroll */}
                            <div className="border border-gray-200 rounded-lg">
                                <div className="bg-gray-50 px-4 py-2 border-b border-gray-200 rounded-t-lg">
                                    <h3 className="text-sm font-semibold text-gray-700">Filtered Data</h3>
                                </div>
                                <div className="overflow-auto" style={{ maxHeight: '500px' }}>
                                    <table className="min-w-full divide-y divide-gray-200">
                                        <thead className="bg-gray-50 sticky top-0">
                                            <tr>
                                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Serial No.
                                                </th>
                                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Timestamp
                                                </th>
                                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Temperature
                                                </th>
                                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Ambient Temp
                                                </th>
                                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Status
                                                </th>
                                            </tr>
                                        </thead>
                                        <tbody className="bg-white divide-y divide-gray-200">
                                            {previewData.map((reading, index) => (
                                                <tr key={reading.id} className="hover:bg-gray-50">
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                                                        {index + 1}
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                                                        {formatDateTime(reading.timestamp)}
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                                                        {reading.value}°C
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                                                        {reading.ambient_temp !== null && reading.ambient_temp !== undefined
                                                            ? `${reading.ambient_temp}°C`
                                                            : '--'}
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap">
                                                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                                            reading.status === 'OK'
                                                                ? 'bg-green-100 text-green-800'
                                                                : reading.status === 'Err'
                                                                ? 'bg-red-100 text-red-800'
                                                                : 'bg-yellow-100 text-yellow-800'
                                                        }`}>
                                                            {reading.status}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            {/* Right Side - Graph */}
                            <div className="border border-gray-200 rounded-lg">
                                <div className="bg-gray-50 px-4 py-2 border-b border-gray-200 rounded-t-lg">
                                    <h3 className="text-sm font-semibold text-gray-700">Temperature vs Time</h3>
                                </div>
                                <div className="p-4" style={{ height: '500px' }}>
                                    {graphData.length === 0 ? (
                                        <div className="flex items-center justify-center h-full">
                                            <div className="text-center">
                                                <svg className="w-12 h-12 mx-auto text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                                                </svg>
                                                <p className="text-gray-500 text-sm">No graph data available</p>
                                            </div>
                                        </div>
                                    ) : (
                                        <ResponsiveContainer width="100%" height="100%">
                                            <LineChart data={graphData} margin={{ top: 10, right: 30, left: 0, bottom: 5 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                                                <XAxis
                                                    dataKey="timestamp"
                                                    type="number"
                                                    domain={['dataMin', 'dataMax']}
                                                    tickFormatter={formatTimeForGraph}
                                                    stroke="#6b7280"
                                                    style={{ fontSize: '11px' }}
                                                    scale="time"
                                                />
                                                <YAxis
                                                    stroke="#6b7280"
                                                    style={{ fontSize: '11px' }}
                                                    label={{
                                                        value: 'Temperature (°C)',
                                                        angle: -90,
                                                        position: 'insideLeft',
                                                        style: { fontSize: '12px', fill: '#6b7280' }
                                                    }}
                                                    domain={['auto', 'auto']}
                                                />
                                                <Tooltip
                                                    labelFormatter={formatTimeForGraph}
                                                    contentStyle={{
                                                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                                                        border: '1px solid #d1d5db',
                                                        borderRadius: '6px',
                                                        fontSize: '12px'
                                                    }}
                                                    formatter={(value) => [`${value.toFixed(1)}°C`, 'Temperature']}
                                                />
                                                <Line
                                                    type="monotone"
                                                    dataKey="temperature"
                                                    stroke="#3b82f6"
                                                    strokeWidth={2}
                                                    dot={false}
                                                    name="Temperature"
                                                    connectNulls={true}
                                                    isAnimationActive={false}
                                                />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default PreviewPage;
