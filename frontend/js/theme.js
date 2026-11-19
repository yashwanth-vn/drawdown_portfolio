/*
   theme.js
   Manages Dark/Light mode theme switching.
*/

const THEME_KEY = 'portfolio_theme';

export const ThemeManager = {
    init() {
        // specific preference or system preference
        const savedTheme = localStorage.getItem(THEME_KEY);
        if (savedTheme) {
            this.setTheme(savedTheme);
        } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
            this.setTheme('light');
        } else {
            this.setTheme('dark'); // Default
        }
    },

    toggle() {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'light' ? 'dark' : 'light';
        this.setTheme(next);
        return next;
    },

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(THEME_KEY, theme);

        // Update variables if needed or trigger events
        // (CSS variables handle most of it)
    }
};
