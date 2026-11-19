/*
   pipeline.js
   Manages API communication and execution state.
*/

const API_BASE = '/api';

export const Pipeline = {
    async getConfig() {
        try {
            const res = await fetch(`${API_BASE}/config`);
            const data = await res.json();
            return data.status === 'success' ? data.data : null;
        } catch (e) {
            console.error("Config Load Error:", e);
            return null;
        }
    },

    async updateConfig(newConfig) {
        try {
            const res = await fetch(`${API_BASE}/config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newConfig)
            });
            return await res.json();
        } catch (e) {
            console.error("Config Update Error:", e);
            return { status: 'error', message: e.message };
        }
    },

    async startExecution() {
        try {
            const res = await fetch(`${API_BASE}/execute`, { method: 'POST' });
            return await res.json();
        } catch (e) {
            console.error("Execution Start Error:", e);
            return { status: 'error', message: e.message };
        }
    },

    async getStatus() {
        try {
            const res = await fetch(`${API_BASE}/status`);
            return await res.json();
        } catch (e) {
            console.error("Status Check Error:", e);
            return null;
        }
    },

    async getResults() {
        try {
            const res = await fetch(`${API_BASE}/results`);
            const data = await res.json();
            return data.status === 'success' ? data.data : null;
        } catch (e) {
            console.error("Results Fetch Error:", e);
            return null;
        }
    }
};
