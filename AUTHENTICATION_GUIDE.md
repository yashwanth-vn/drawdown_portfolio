# Authentication Guide

The Drawdown-Minimization Portfolio Optimizer is now secured with a session-based authentication system.

## 🔐 Credentials

Use the following demo credentials to specific access roles:

| Role | Email | Password |
|------|-------|----------|
| **Admin** | `user@finance.com` | `password123` |
| **Analyst** | `analyst@finance.com` | `password123` |

## 🚀 Features

### **1. Secure Login**
- Protected access to the dashboard.
- Automatic redirection to `/login` for unauthenticated users.

### **2. User Profile**
- Click your avatar in the top-right corner to see your details.
- **Logout** option clears your session securely.

### **3. Theme Personalization**
- Click the **Moon/Sun** icon in the header to toggle between Dark (Institutional) and Light modes.
- Your preference is saved automatically.

## ⚠️ Notes
- The session handling uses a secure secret key. in `api_server.py`.
- Passwords are hashed using SHA-256 (in this demo).
