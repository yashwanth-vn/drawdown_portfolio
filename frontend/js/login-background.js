/**
 * login-background.js
 * Generates animated SVG paths for the login page background
 * This script is loaded ONLY on login.html
 */

(function () {
    'use strict';

    // Configuration
    const CONFIG = {
        pathCount: 12,
        viewBox: { width: 1920, height: 1080 },
        colors: {
            dark: ['#3b82f6', '#6366f1', '#8b5cf6', '#0ea5e9'],
            light: ['#2563eb', '#4f46e5', '#7c3aed', '#0284c7']
        }
    };

    /**
     * Generate a smooth bezier curve path
     */
    function generatePath(index, total) {
        const width = CONFIG.viewBox.width;
        const height = CONFIG.viewBox.height;

        // Distribute paths across the viewport
        const yOffset = (height / total) * index;
        const amplitude = 150 + Math.random() * 100;
        const frequency = 2 + Math.random() * 2;

        // Generate control points for smooth curves
        const points = [];
        const segments = 5 + Math.floor(Math.random() * 3);

        for (let i = 0; i <= segments; i++) {
            const x = (width / segments) * i;
            const y = yOffset + Math.sin((i / segments) * Math.PI * frequency) * amplitude;
            points.push({ x, y: Math.max(0, Math.min(height, y)) });
        }

        // Create smooth bezier path
        let d = `M ${points[0].x - 200} ${points[0].y}`;

        for (let i = 0; i < points.length - 1; i++) {
            const curr = points[i];
            const next = points[i + 1];
            const cpX = (curr.x + next.x) / 2;
            d += ` Q ${curr.x + 100} ${curr.y + (Math.random() - 0.5) * 50}, ${cpX} ${(curr.y + next.y) / 2}`;
        }

        d += ` L ${width + 200} ${points[points.length - 1].y}`;

        return d;
    }

    /**
     * Create the SVG background element
     */
    function createBackgroundSVG() {
        const container = document.createElement('div');
        container.className = 'background-paths-container';
        container.id = 'bg-paths';

        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('class', 'background-paths-svg');
        svg.setAttribute('viewBox', `0 0 ${CONFIG.viewBox.width} ${CONFIG.viewBox.height}`);
        svg.setAttribute('preserveAspectRatio', 'xMidYMid slice');

        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');

        // Create gradient definitions
        CONFIG.colors.dark.forEach((color, i) => {
            const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
            gradient.setAttribute('id', `pathGradient${i}`);
            gradient.setAttribute('x1', '0%');
            gradient.setAttribute('y1', '0%');
            gradient.setAttribute('x2', '100%');
            gradient.setAttribute('y2', '0%');

            const stop1 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
            stop1.setAttribute('offset', '0%');
            stop1.setAttribute('stop-color', color);
            stop1.setAttribute('stop-opacity', '0');

            const stop2 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
            stop2.setAttribute('offset', '50%');
            stop2.setAttribute('stop-color', color);
            stop2.setAttribute('stop-opacity', '0.6');

            const stop3 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
            stop3.setAttribute('offset', '100%');
            stop3.setAttribute('stop-color', color);
            stop3.setAttribute('stop-opacity', '0');

            gradient.appendChild(stop1);
            gradient.appendChild(stop2);
            gradient.appendChild(stop3);
            defs.appendChild(gradient);
        });

        svg.appendChild(defs);

        // Create path groups
        for (let g = 0; g < 3; g++) {
            const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            group.setAttribute('class', `path-group-${g + 1}`);

            const pathsPerGroup = Math.floor(CONFIG.pathCount / 3);

            for (let i = 0; i < pathsPerGroup; i++) {
                const globalIndex = g * pathsPerGroup + i;
                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                path.setAttribute('class', 'animated-path');
                path.setAttribute('d', generatePath(globalIndex, CONFIG.pathCount));
                path.setAttribute('stroke', `url(#pathGradient${globalIndex % CONFIG.colors.dark.length})`);
                path.setAttribute('stroke-width', (0.5 + Math.random() * 1.5).toFixed(2));
                path.style.setProperty('--delay', `${globalIndex * 0.5}s`);
                path.style.setProperty('--duration', `${15 + Math.random() * 15}s`);

                group.appendChild(path);
            }

            svg.appendChild(group);
        }

        container.appendChild(svg);

        // Add gradient overlay
        const overlay = document.createElement('div');
        overlay.className = 'background-gradient-overlay';
        container.appendChild(overlay);

        return container;
    }

    /**
     * Initialize the background
     */
    function init() {
        // Only run on the login page
        if (!document.body.classList.contains('auth-body')) {
            return;
        }

        const background = createBackgroundSVG();
        document.body.insertBefore(background, document.body.firstChild);

        // Regenerate paths periodically for variety
        setInterval(() => {
            const paths = document.querySelectorAll('.animated-path');
            paths.forEach((path, index) => {
                path.setAttribute('d', generatePath(index, paths.length));
            });
        }, 30000); // Every 30 seconds
    }

    // Run when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
