import { useState, useEffect, useRef, useCallback } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getDeviceColor } from '../utils/graphColors';

function GraphSection({ devices, devicesWithReadings }) {
    const [timeRange, setTimeRange] = useState(10); // Default 10 minutes
    const [graphData, setGraphData] = useState([]);
    const [currentTime, setCurrentTime] = useState(Date.now()); // Track current time for sliding window
    const dataBufferRef = useRef(new Map());

    // MEMORY OPTIMIZATION: Fixed buffer size per device (never exceed this)
    const MAX_POINTS_PER_DEVICE = 300; // Enough for smooth graph, prevents memory overflow

    // Filter devices that should be shown in graph (show_in_graph = true)
    const graphDevices = devices.filter(d => d.show_in_graph);

    // Calculate minimum interval between points based on time range
    // This ensures we only store what's needed for smooth rendering
    const getMinSampleInterval = (timeRangeMinutes) => {
        // Distribute MAX_POINTS across the time range
        // Example: 60 min range → store point every 12 seconds
        const totalSeconds = timeRangeMinutes * 60;
        return (totalSeconds / MAX_POINTS_PER_DEVICE) * 1000; // Convert to milliseconds
    };

    // Update current time every second to create sliding window effect
    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentTime(Date.now());
        }, 1000); // Update every second

        return () => clearInterval(interval);
    }, []);

    // Update graph data when new readings arrive via WebSocket
    useEffect(() => {
        if (devicesWithReadings.length === 0) return;

        const now = Date.now();
        const cutoffTime = now - (timeRange * 60 * 1000);
        const minInterval = getMinSampleInterval(timeRange);

        devicesWithReadings.forEach(deviceReading => {
            const device = devices.find(d => d.id === deviceReading.device_id);

            if (!device || !device.show_in_graph) return;

            const reading = deviceReading.latest_reading;

            if (!reading || reading.status === 'Err') return;

            // Parse UTC timestamp correctly by adding 'Z' to indicate UTC
            const timestampStr = reading.timestamp.endsWith('Z') ? reading.timestamp : reading.timestamp + 'Z';
            const timestamp = new Date(timestampStr).getTime();

            // IMMEDIATE CLEANUP: Skip data that's already outside time window
            if (timestamp < cutoffTime) return;

            // Get or create buffer for this device
            if (!dataBufferRef.current.has(device.id)) {
                dataBufferRef.current.set(device.id, []);
            }

            const buffer = dataBufferRef.current.get(device.id);

            // ADAPTIVE SAMPLING: Only add if enough time has passed since last point
            // This prevents buffer from growing too large
            let shouldAdd = false;

            if (buffer.length === 0) {
                shouldAdd = true; // First point always added
            } else {
                const lastPoint = buffer[buffer.length - 1];
                const timeSinceLastPoint = timestamp - lastPoint.timestamp;

                // For recent data (last 10%), store every point for real-time smoothness
                const recentThreshold = now - (timeRange * 60 * 1000 * 0.1);
                if (timestamp > recentThreshold) {
                    shouldAdd = timeSinceLastPoint >= 1000; // Store every second for recent data
                } else {
                    // For older data, use adaptive sampling
                    shouldAdd = timeSinceLastPoint >= minInterval;
                }
            }

            if (shouldAdd && reading.temperature !== null && reading.temperature !== undefined) {
                buffer.push({
                    timestamp: timestamp,
                    temperature: reading.temperature,
                    deviceId: device.id,
                    deviceName: device.name
                });

                // IMMEDIATE OLD DATA REMOVAL: Remove points outside time window
                let validPoints = buffer.filter(point => point.timestamp >= cutoffTime);

                // ENFORCE MAX BUFFER SIZE: Keep only most recent MAX_POINTS_PER_DEVICE
                if (validPoints.length > MAX_POINTS_PER_DEVICE) {
                    validPoints = validPoints.slice(-MAX_POINTS_PER_DEVICE);
                }

                dataBufferRef.current.set(device.id, validPoints);
            }
        });

        // Build graph data structure
        buildGraphData();
    }, [devicesWithReadings, devices, timeRange]);

    // Get downsampling interval for chart rendering based on time range
    const getDownsampleInterval = () => {
        if (timeRange <= 1) return 1;        // 1 min: every point
        if (timeRange <= 5) return 1;        // 5 min: every point (adaptive sampling already limits this)
        if (timeRange <= 10) return 1;       // 10 min: every point
        if (timeRange <= 30) return 2;       // 30 min: every 2nd point
        if (timeRange <= 60) return 2;       // 1 hour: every 2nd point
        return 1;                             // Default: every point
    };

    // Build the graph data from all device buffers with downsampling
    const buildGraphData = useCallback(() => {
        const downsampleInterval = getDownsampleInterval();

        // Collect all unique timestamps from all buffers
        const timestampSet = new Set();
        dataBufferRef.current.forEach((buffer) => {
            buffer.forEach(point => {
                timestampSet.add(point.timestamp);
            });
        });

        // Convert to sorted array
        let timestamps = Array.from(timestampSet).sort((a, b) => a - b);

        // Downsample: keep every Nth timestamp for performance
        if (downsampleInterval > 1 && timestamps.length > 100) {
            const downsampled = [];
            for (let i = 0; i < timestamps.length; i += downsampleInterval) {
                downsampled.push(timestamps[i]);
            }
            // Always include the last (most recent) timestamp
            if (downsampled[downsampled.length - 1] !== timestamps[timestamps.length - 1]) {
                downsampled.push(timestamps[timestamps.length - 1]);
            }
            timestamps = downsampled;
        }

        // Build data points for the graph
        const chartData = timestamps.map(timestamp => {
            const dataPoint = { timestamp };

            // Add temperature for each device at this timestamp
            dataBufferRef.current.forEach((buffer, deviceId) => {
                const point = buffer.find(p => p.timestamp === timestamp);
                if (point) {
                    dataPoint[`device_${deviceId}`] = point.temperature;
                }
            });

            return dataPoint;
        });

        setGraphData(chartData);
    }, [timeRange]);

    // Lightweight periodic cleanup (most cleanup happens immediately on data insert)
    useEffect(() => {
        const interval = setInterval(() => {
            const now = Date.now();
            const cutoffTime = now - (timeRange * 60 * 1000);

            let hasChanges = false;

            dataBufferRef.current.forEach((buffer, deviceId) => {
                // Remove any stale points that slipped through
                let validPoints = buffer.filter(point => point.timestamp >= cutoffTime);

                // ENFORCE MAX BUFFER SIZE (safety check)
                if (validPoints.length > MAX_POINTS_PER_DEVICE) {
                    validPoints = validPoints.slice(-MAX_POINTS_PER_DEVICE);
                }

                if (validPoints.length !== buffer.length) {
                    hasChanges = true;
                    dataBufferRef.current.set(deviceId, validPoints);
                }
            });

            // Only rebuild if something was removed
            if (hasChanges) {
                buildGraphData();
            }
        }, 5000); // Clean every 5 seconds (less frequent since immediate cleanup handles most)

        return () => clearInterval(interval);
    }, [timeRange, buildGraphData]);

    // Generate time ticks for X-axis based on CURRENT TIME (not data)
    const generateTimeTicksFromCurrentTime = () => {
        const now = Date.now();
        const start = now - (timeRange * 60 * 1000); // Fixed window start

        const ticks = [];

        // Determine tick interval based on time range
        let tickInterval;
        if (timeRange <= 1) {
            tickInterval = 10 * 1000; // 10 seconds for 1 min range
        } else if (timeRange <= 5) {
            tickInterval = 60 * 1000; // 1 minute for 5 min range
        } else if (timeRange <= 10) {
            tickInterval = 2 * 60 * 1000; // 2 minutes for 10 min range
        } else if (timeRange <= 30) {
            tickInterval = 5 * 60 * 1000; // 5 minutes for 30 min range
        } else {
            tickInterval = 10 * 60 * 1000; // 10 minutes for 1 hour range (max)
        }

        // Generate ticks from start to NOW (current time)
        for (let tick = start; tick <= now; tick += tickInterval) {
            ticks.push(tick);
        }

        // Ensure current time is included as the last tick
        if (ticks.length === 0 || ticks[ticks.length - 1] < now - tickInterval / 2) {
            ticks.push(now);
        }

        return ticks;
    };

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

    // Calculate Y-axis domain from device configurations
    // All devices share the same Y-axis settings (configured in Common Configuration)
    const getYAxisDomain = () => {
        if (graphDevices.length === 0) {
            return ['auto', 'auto']; // Fallback to auto if no devices
        }

        // Get Y-axis settings from first device (all devices have the same values)
        const firstDevice = graphDevices[0];
        const yMin = firstDevice.graph_y_min;
        const yMax = firstDevice.graph_y_max;

        // If not configured, use auto-scale
        if (yMin === null || yMin === undefined || yMax === null || yMax === undefined) {
            return ['auto', 'auto'];
        }

        return [yMin, yMax];
    };

    return (
        <div className="flex gap-2 h-full">
            {/* Graph Area - Maximum Width & Height */}
            <div className="flex-1">
                <div className="h-full border-2 border-gray-300 rounded-lg bg-white flex items-center justify-center p-2">
                    {graphDevices.length === 0 ? (
                        <div className="text-center">
                            <svg className="w-16 h-16 mx-auto text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                            </svg>
                            <p className="text-gray-500 text-base mb-1">No devices selected for graphing</p>
                            <p className="text-gray-400 text-sm">Check the "Graph" checkbox in device configuration</p>
                        </div>
                    ) : graphData.length === 0 ? (
                        <div className="text-center">
                            <svg className="w-16 h-16 mx-auto text-blue-300 mb-3 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <p className="text-gray-500 text-sm">Waiting for temperature data...</p>
                            <p className="text-gray-400 text-xs mt-1">{graphDevices.length} device(s) enabled</p>
                        </div>
                    ) : (
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={graphData} margin={{ top: 10, right: 10, left: 0, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                                <XAxis
                                    dataKey="timestamp"
                                    type="number"
                                    domain={[
                                        () => {
                                            // Left edge: current time MINUS time range
                                            return Date.now() - (timeRange * 60 * 1000);
                                        },
                                        () => {
                                            // Right edge: always current time
                                            return Date.now();
                                        }
                                    ]}
                                    tickFormatter={formatTime}
                                    stroke="#6b7280"
                                    style={{ fontSize: '11px' }}
                                    scale="time"
                                    ticks={generateTimeTicksFromCurrentTime()}
                                />
                                <YAxis
                                    stroke="#6b7280"
                                    style={{ fontSize: '11px' }}
                                    label={{ value: 'Temperature (°C)', angle: -90, position: 'insideLeft', style: { fontSize: '12px', fill: '#6b7280' } }}
                                    domain={getYAxisDomain()}
                                />
                                <Tooltip
                                    labelFormatter={formatTime}
                                    contentStyle={{
                                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                                        border: '1px solid #d1d5db',
                                        borderRadius: '6px',
                                        fontSize: '12px'
                                    }}
                                    formatter={(value, name, props) => {
                                        // Extract device ID from dataKey (format: "device_123")
                                        const deviceId = parseInt(props.dataKey.replace('device_', ''));
                                        const device = devices.find(d => d.id === deviceId);
                                        return [
                                            `${value.toFixed(1)}°C`,
                                            device ? device.name : `Device ${deviceId}`
                                        ];
                                    }}
                                />
                                {/* Render a line for each device */}
                                {graphDevices.map((device) => (
                                    <Line
                                        key={device.id}
                                        type="monotone"
                                        dataKey={`device_${device.id}`}
                                        stroke={getDeviceColor(device.slave_id)}
                                        strokeWidth={2}
                                        dot={false}
                                        name={device.name}
                                        connectNulls={true}
                                        isAnimationActive={false}
                                    />
                                ))}
                            </LineChart>
                        </ResponsiveContainer>
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
                            <option value={1}>Last 1 minute</option>
                            <option value={5}>Last 5 minutes</option>
                            <option value={10}>Last 10 minutes</option>
                            <option value={30}>Last 30 minutes</option>
                            <option value={60}>Last 1 hour</option>
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
