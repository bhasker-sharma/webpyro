import axios from 'axios';

// Get API base URL from environment variable or auto-detect from current hostname
const getApiBaseUrl = () => {
    // If environment variable is set, use it
    if (import.meta.env.VITE_API_BASE_URL) {
        return `${import.meta.env.VITE_API_BASE_URL}/api`;
    }

    // Otherwise, auto-detect based on current hostname
    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
    const hostname = window.location.hostname;
    return `${protocol}//${hostname}:8000/api`;
};

const API_BASE_URL = getApiBaseUrl();

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const deviceAPI = {
    getAll: async (enabledOnly = false) => {
        const response = await api.get(`/devices?enabled_only=${enabledOnly}`);
        return response.data;
    },

    getById: async (id) => {
        const response = await api.get(`/devices/${id}`);
        return response.data;
    },

    create: async (deviceData) => {
        const response = await api.post('/devices', deviceData);
        return response.data;
    },

    update: async (id, deviceData) => {
        const response = await api.put(`/devices/${id}`, deviceData);
        return response.data;
    },

    delete: async (id) => {
        await api.delete(`/devices/${id}`);
    },

    getWithReadings: async () => {
        const response = await api.get('/devices/with-readings');
        return response.data;
    },
};

export const healthAPI = {
    check: async () => {
        const response = await api.get('/health');
        return response.data;
    },
};

// ============================================================================
// READING API FUNCTIONS
// ============================================================================

export const readingAPI = {
    /**
     * Get latest readings for all devices
     */
    getLatest: async () => {
        const response = await api.get('/reading/latest');
        return response.data;
    },

    /**
     * Get reading history for a specific device
     */
    getDeviceReadings: async (deviceId, limit = 100) => {
        const response = await api.get(`/reading/device/${deviceId}?limit=${limit}`);
        return response.data;
    },

    /**
     * Get overall reading statistics
     */
    getStats: async () => {
        const response = await api.get('/reading/stats');
        return response.data;
    },
};

// ============================================================================
// POLLING API FUNCTIONS
// ============================================================================

export const pollingAPI = {
    /**
     * Get polling service statistics
     */
    getStats: async () => {
        const response = await api.get('/polling/stats');
        return response.data;
    },

    /**
     * Restart the polling service
     * Call this after updating device configurations
     */
    restart: async () => {
        const response = await api.post('/polling/restart');
        return response.data;
    },
};

// ============================================================================
// CONFIG API FUNCTIONS
// ============================================================================

export const configAPI = {
    /**
     * Get available COM ports on the system
     */
    getComPorts: async () => {
        const response = await api.get('/config/com-ports');
        return response.data;
    },

    /**
     * Verify configuration access PIN
     */
    verifyPin: async (pin) => {
        const response = await api.post('/config/verify-pin', { pin });
        return response.data;
    },

    /**
     * Clear all device settings from database
     */
    clearSettings: async () => {
        const response = await api.post('/config/clear-settings');
        return response.data;
    },
};

// ============================================================================
// PYROMETER API FUNCTIONS
// ============================================================================

export const pyrometerAPI = {
    /**
     * Get current emissivity value from pyrometer device
     * @param {number} slaveId - Device slave ID (1-16)
     * @param {string} comPort - COM port (e.g., 'COM3')
     */
    getEmissivity: async (slaveId = 1, comPort = null) => {
        const params = new URLSearchParams();
        params.append('slave_id', slaveId);
        if (comPort) {
            params.append('com_port', comPort);
        }
        const response = await api.get(`/pyrometer/emissivity?${params.toString()}`);
        return response.data;
    },

    /**
     * Set emissivity value on pyrometer device
     * @param {number} emissivity - Emissivity value (0.20-1.00)
     * @param {number} slaveId - Device slave ID (1-16)
     * @param {string} comPort - COM port (e.g., 'COM3')
     */
    setEmissivity: async (emissivity, slaveId = 1, comPort = null) => {
        const response = await api.post('/pyrometer/emissivity', {
            emissivity,
            slave_id: slaveId,
            com_port: comPort
        });
        return response.data;
    },

    /**
     * Test RS-485 connection to pyrometer device
     */
    testConnection: async () => {
        const response = await api.get('/pyrometer/test-connection');
        return response.data;
    },

    /**
     * Pause polling service to avoid COM port conflicts
     */
    pausePolling: async () => {
        const response = await api.post('/polling/pause');
        return response.data;
    },

    /**
     * Resume polling service after parameter configuration
     */
    resumePolling: async () => {
        const response = await api.post('/polling/resume');
        return response.data;
    },
};

export default api;