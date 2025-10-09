import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

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

export default api;