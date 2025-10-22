/**
 * Graph Color Utility
 * Assigns unique colors to devices based on their Slave ID
 */

// 16 distinct, colorblind-friendly colors for graph lines
export const GRAPH_COLORS = [
    '#3B82F6', // blue
    '#EF4444', // red
    '#10B981', // green
    '#F59E0B', // amber
    '#8B5CF6', // purple
    '#EC4899', // pink
    '#14B8A6', // teal
    '#F97316', // orange
    '#6366F1', // indigo
    '#84CC16', // lime
    '#06B6D4', // cyan
    '#F43F5E', // rose
    '#A855F7', // violet
    '#22D3EE', // sky
    '#FB923C', // orange-400
    '#A3E635', // lime-400
];

/**
 * Get color for a device based on its Slave ID
 * @param {number} slaveId - Modbus slave ID (1-247)
 * @returns {string} Hex color code
 */
export const getDeviceColor = (slaveId) => {
    return GRAPH_COLORS[(slaveId - 1) % GRAPH_COLORS.length];
};

/**
 * Get color name for display in legend
 * @param {number} slaveId - Modbus slave ID
 * @returns {string} Color name
 */
const COLOR_NAMES = [
    'Blue', 'Red', 'Green', 'Amber', 'Purple', 'Pink',
    'Teal', 'Orange', 'Indigo', 'Lime', 'Cyan', 'Rose',
    'Violet', 'Sky', 'Orange', 'Lime'
];

export const getColorName = (slaveId) => {
    return COLOR_NAMES[(slaveId - 1) % COLOR_NAMES.length];
};
