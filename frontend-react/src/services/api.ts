export interface PipelineState {
    is_running: boolean;
    current_step: number;
    status: 'idle' | 'running' | 'completed' | 'error';
    step_details: string;
    results?: any;
    error?: string;
}

export const PipelineAPI = {
    async getConfig() {
        try {
            const res = await fetch('/api/config');
            const data = await res.json();
            return data.status === 'success' ? data.data : null;
        } catch (e) {
            console.error("Config Load Error:", e);
            return null;
        }
    },

    async updateConfig(newConfig: any) {
        try {
            const res = await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newConfig)
            });
            return await res.json();
        } catch (e) {
            console.error("Config Update Error:", e);
            return { status: 'error', message: (e as Error).message };
        }
    },

    async startExecution() {
        try {
            const res = await fetch('/api/execute', { method: 'POST' });
            return await res.json();
        } catch (e) {
            console.error("Execution Start Error:", e);
            return { status: 'error', message: (e as Error).message };
        }
    },

    async getStatus(): Promise<PipelineState | null> {
        try {
            const res = await fetch('/api/status');
            return await res.json();
        } catch (e) {
            console.error("Status Check Error:", e);
            return null;
        }
    },

    async getResults() {
        try {
            const res = await fetch('/api/results');
            const data = await res.json();
            return data.status === 'success' ? data.data : null;
        } catch (e) {
            console.error("Results Fetch Error:", e);
            return null;
        }
    }
};
