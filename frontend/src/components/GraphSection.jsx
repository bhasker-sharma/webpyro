import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getDeviceColor } from '../utils/graphColors';

function GraphSection({ devices, devicesWithReadings }) {
    const [timeRange, setTimeRange] = useState(10); // Default 10 minutes
    const [graphData, setGraphData] = useState([]);

    // Filter devices that should be shown in graph (show_in_graph = true)
    const graphDevices = devices.filter(d => d.show_in_graph);

    // Format time for X-axis
    const formatTime = (timestamp) => {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
    };

    // Get current time range for display
    const getCurrentTimeRange = () => {
        const now = new Date();
        const start = new Date(now.getTime() - timeRange * 60 * 1000);
        return {
            start: start.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true }),
            end: now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })
        };
    };

    const timeRangeDisplay = getCurrentTimeRange();

    return (
        <div className="flex gap-2 h-full">
            {/* Graph Area - Maximum Width & Height */}
            <div className="flex-1">
                <div className="h-full border-2 border-gray-300 rounded-lg bg-gray-50 flex items-center justify-center">
                    {graphDevices.length === 0 ? (
                        <div className="text-center">
                            <svg className="w-16 h-16 mx-auto text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                            </svg>
                            <p className="text-gray-500 text-base mb-1">No devices selected for graphing</p>
                            <p className="text-gray-400 text-sm">Check the "Graph" checkbox in device configuration</p>
                        </div>
                    ) : (
                        <div className="text-center">
                            <p className="text-gray-500 text-sm">Graph will appear here</p>
                            <p className="text-gray-400 text-xs mt-1">{graphDevices.length} device(s) selected</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Compact Side Panel - Settings & Legend */}
            <div className="w-44 flex flex-col gap-2">
                {/* Time Range Settings */}
                <div className="border border-gray-300 rounded-lg bg-white">
                    <div className="px-2 py-1 bg-gray-100 border-b border-gray-300">
                        <h3 className="text-xs font-semibold text-gray-700">Time Range</h3>
                    </div>
                    <div className="p-2">
                        <select
                            value={timeRange}
                            onChange={(e) => setTimeRange(Number(e.target.value))}
                            className="w-full px-2 py-1 text-xs border border-gray-300 rounded bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                        >
                            <option value={5}>Last 5 minutes</option>
                            <option value={10}>Last 10 minutes</option>
                            <option value={30}>Last 30 minutes</option>
                            <option value={60}>Last 1 hour</option>
                            <option value={180}>Last 3 hours</option>
                        </select>
                        <div className="text-[10px] text-gray-500 mt-1 text-center">
                            {timeRangeDisplay.start} - {timeRangeDisplay.end}
                        </div>
                    </div>
                </div>

                {/* Legend Section */}
                <div className="flex-1 border border-gray-300 rounded-lg overflow-hidden bg-white flex flex-col min-h-0">
                    <div className="px-2 py-1 bg-gray-100 border-b border-gray-300">
                        <h3 className="text-xs font-semibold text-gray-700">Legend</h3>
                    </div>
                    <div className="flex-1 overflow-y-auto">
                        <table className="w-full text-xs">
                            <tbody>
                                {graphDevices.length === 0 ? (
                                    <tr>
                                        <td colSpan="2" className="px-2 py-4 text-center text-[10px] text-gray-400">
                                            No devices
                                        </td>
                                    </tr>
                                ) : (
                                    graphDevices.map((device) => {
                                        const color = getDeviceColor(device.slave_id);
                                        return (
                                            <tr key={device.id} className="border-b border-gray-100 hover:bg-gray-50">
                                                <td className="px-2 py-1">
                                                    <div
                                                        className="w-3 h-3 rounded-full border border-gray-300"
                                                        style={{ backgroundColor: color }}
                                                    ></div>
                                                </td>
                                                <td className="px-1 py-1">
                                                    <div className="text-[11px] text-gray-800 font-medium truncate">{device.name}</div>
                                                    <div className="text-[9px] text-gray-500">ID:{device.slave_id}</div>
                                                </td>
                                            </tr>
                                        );
                                    })
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default GraphSection;
