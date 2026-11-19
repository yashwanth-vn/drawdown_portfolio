/*
   auth.js
   Manages user authentication, session validation, and logout.
*/

const API_BASE = '/api/auth';

export const AuthManager = {
    async login(email, password) {
        try {
            const res = await fetch(`${API_BASE}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            return await res.json();
        } catch (e) {
            console.error("Login Error:", e);
            return { status: 'error', message: 'Connection failed' };
        }
    },

    async logout() {
        try {
            await fetch(`${API_BASE}/logout`, { method: 'POST' });
            window.location.href = '/login';
        } catch (e) {
            console.error("Logout Error:", e);
            window.location.href = '/login';
        }
    },

    async validateSession() {
        try {
            const res = await fetch(`${API_BASE}/validate`);
            if (res.status === 401) {
                return null;
            }
            const data = await res.json();
            return data.status === 'success' ? data.user : null;
        } catch (e) {
            return null;
        }
    },

    // Redirect helper
    requireAuth() {
        this.validateSession().then(user => {
            if (!user) {
                window.location.href = '/login';
            } else {
                // Initialize user profile in UI if declared
                if (window.initUserProfile) {
                    window.initUserProfile(user);
                }
            }
        });
    }
};
