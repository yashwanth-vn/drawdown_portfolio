/*
   charts.js
   Handles Chart.js initialization and data updates.
*/

let weightsChartInstance = null;
let backtestChartInstance = null;

// Color Palette
const COLORS = {
    primary: '#3b82f6',
    success: '#10b981',
    danger: '#ef4444',
    grid: '#334155',
    text: '#94a3b8'
};

export function initCharts() {
    // 1. Weights Chart (Donut)
    const ctxWeights = document.getElementById('weightsChart').getContext('2d');
    weightsChartInstance = new Chart(ctxWeights, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right', labels: { color: COLORS.text } }
            }
        }
    });

    // 2. Backtest Chart (Line - Placeholder initially)
    const ctxBacktest = document.getElementById('backtestChart').getContext('2d');

    // Create gradient
    const gradient = ctxBacktest.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(59, 130, 246, 0.5)'); // Blue top
    gradient.addColorStop(1, 'rgba(59, 130, 246, 0.0)'); // Transparent bottom

    backtestChartInstance = new Chart(ctxBacktest, {
        type: 'line',
        data: {
            labels: Array.from({ length: 20 }, (_, i) => i), // Placeholder
            datasets: [{
                label: 'Cumulative Return',
                data: Array.from({ length: 20 }, () => Math.random() * 0.1 + 1), // Dummy data
                borderColor: COLORS.primary,
                backgroundColor: gradient,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: COLORS.text } }
            },
            scales: {
                y: { grid: { color: COLORS.grid }, ticks: { color: COLORS.text } },
                x: { grid: { display: false }, ticks: { color: COLORS.text } }
            }
        }
    });
}

export function updateCharts(results) {
    if (!results) return;

    // UPDATE WEIGHTS CHART
    if (results.weights) {
        const labels = Object.keys(results.weights);
        const data = Object.values(results.weights);

        weightsChartInstance.data.labels = labels;
        weightsChartInstance.data.datasets[0].data = data;
        weightsChartInstance.update();
    }

    // UPDATE BACKTEST CHART (Simulating curve since we only get metrics effectively in this bridge)
    // In a real scenario, the backend would return time-series data.
    // Here we generate a clean equity curve based on total return and vol.

    if (results.metrics) {
        const points = 100;
        const totalReturn = results.metrics.total_return || 0;
        const volatility = results.metrics.volatility || 0.1;

        let curve = [100]; // Start at 100
        for (let i = 1; i < points; i++) {
            const trend = (totalReturn / points);
            const noise = (Math.random() - 0.5) * volatility;
            curve.push(curve[i - 1] * (1 + trend + noise));
        }

        backtestChartInstance.data.labels = Array.from({ length: points }, (_, i) => i);
        backtestChartInstance.data.datasets[0].data = curve;
        backtestChartInstance.update();

        // Remove placeholder overlay
        const overlay = document.querySelector('.placeholder-overlay');
        if (overlay) overlay.style.display = 'none';
    }
}
