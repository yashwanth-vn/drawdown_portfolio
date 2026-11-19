export interface User {
    email: string;
    name: string;
    role: string;
}

export interface AuthResult {
    status: "success" | "error";
    message?: string;
    user?: User;
}

export class AuthManager {
    private static USER_KEY = "portfolio_user";

    static async login(email: string, password: string): Promise<AuthResult> {
        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            const data = await res.json();

            if (data.status === 'success' && data.user) {
                localStorage.setItem(this.USER_KEY, JSON.stringify(data.user));
                return { status: "success", user: data.user };
            } else {
                return { status: "error", message: data.message || "Login failed" };
            }
        } catch (e) {
            console.error("Login Error:", e);
            return { status: "error", message: "Network error occurred" };
        }
    }

    static logout(): void {
        localStorage.removeItem(this.USER_KEY);
        // Optional: Call server logout endpoint
        fetch('/api/auth/logout', { method: 'POST' }).catch(console.error);
    }

    static getUser(): User | null {
        const stored = localStorage.getItem(this.USER_KEY);
        if (stored) {
            try {
                return JSON.parse(stored) as User;
            } catch {
                return null;
            }
        }
        return null; // Return null if nothing stored
    }

    static isAuthenticated(): boolean {
        return this.getUser() !== null;
    }

    // Helper helper to check session validity with server
    static async validateSession(): Promise<boolean> {
        try {
            const res = await fetch('/api/auth/validate');
            const data = await res.json();
            if (data.status === 'success') {
                return true;
            }
            return false;
        } catch {
            return false;
        }
    }
}
