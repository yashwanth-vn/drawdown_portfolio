/*
   main.js
   Core application controller with Auth and Theme integration.
*/

import { Pipeline } from './pipeline.js';
import { initCharts, updateCharts } from './charts.js';
import { AuthManager } from './auth.js';
import { ThemeManager } from './theme.js';
import { AssetManager } from './asset_manager.js';

// DOM Elements
const els = {
    startBtn: document.getElementById('start-btn'),
    runBtn: document.getElementById('run-pipeline-btn'),
    pipelineStatus: document.getElementById('pipeline-status'),
    steps: document.querySelectorAll('.step'),

    // Auth & Theme
    themeBtn: document.getElementById('theme-btn'),
    themeIcon: document.getElementById('theme-icon'),
    userProfileMenu: document.getElementById('user-profile-menu'),
    dropdownMenu: document.querySelector('.dropdown-menu'),
    logoutBtn: document.getElementById('logout-btn'),
    userAvatar: document.getElementById('user-avatar'),
    userNameDisplay: document.getElementById('user-name-display'),

    // Data Elements
    assetList: document.getElementById('asset-list'),
    dataParams: document.getElementById('data-params'),

    // Metrics & Report
    worstDD: document.getElementById('val-worst-dd'),
    percentileDD: document.getElementById('val-95-dd'),
    medianDD: document.getElementById('val-median-dd'),
    resTotalReturn: document.getElementById('res-total-return'),
    resVolatility: document.getElementById('res-volatility'),
    resMaxDD: document.getElementById('res-max-dd'),
    resCalmar: document.getElementById('res-calmar'),
    resCvar: document.getElementById('res-cvar'),

    // New Metrics
    valAvgDD: document.getElementById('val-average-dd'),
    valSimCount: document.getElementById('val-sim-count'),
    weightsTableBody: document.querySelector('#weights-table tbody')
};

let pollingInterval = null;
let assetManager = null; // Global instance for modal

async function init() {
    console.log("Initializing Portfolio Optimizer Frontend...");

    // 1. Check Authentication (Redirects if not logged in)
    AuthManager.requireAuth();

    // 2. Initialize Theme
    ThemeManager.init();
    updateThemeIcon();

    // 3. Initialize UI Components
    initCharts();
    setupEventListeners();

    // 4. Load Configuration (Protected Call)
    const config = await Pipeline.getConfig();
    if (config) {
        renderConfig(config);
    }
}

// Exposed to global scope for AuthManager to call
window.initUserProfile = (user) => {
    if (user) {
        els.userAvatar.textContent = user.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
        els.userNameDisplay.textContent = user.name;
    }
};

function setupEventListeners() {
    // Navigation
    els.startBtn.addEventListener('click', () => {
        document.getElementById('pipeline-nav').scrollIntoView({ behavior: 'smooth' });
    });

    // Pipeline
    els.runBtn.addEventListener('click', runPipeline);

    // Theme Toggle
    els.themeBtn.addEventListener('click', () => {
        ThemeManager.toggle();
        updateThemeIcon();
    });

    // Profile Dropdown
    els.userProfileMenu.addEventListener('click', (e) => {
        e.stopPropagation();
        els.dropdownMenu.classList.toggle('show');
    });

    // Close dropdown on outside click
    document.addEventListener('click', () => {
        els.dropdownMenu.classList.remove('show');
    });

    // Logout
    els.logoutBtn.addEventListener('click', () => {
        AuthManager.logout();
    });

    // Settings Modal
    setupSettingsModal();
}

function setupSettingsModal() {
    const settingsBtn = document.getElementById('settings-btn');
    const settingsModal = document.getElementById('settings-modal');
    const closeModal = document.querySelector('.close-modal');
    const saveSettingsBtn = document.getElementById('save-settings-btn');

    // Inputs
    const optMethod = document.getElementById('opt-method');
    const optCvarAlpha = document.getElementById('opt-cvar-alpha');
    const optMinReturn = document.getElementById('opt-min-return');
    // optTickers removed, handled by AssetManager
    const optCapital = document.getElementById('opt-capital');

    if (settingsBtn) {
        settingsBtn.addEventListener('click', () => {
            settingsModal.style.display = 'block';
        });
    }

    if (closeModal) {
        closeModal.addEventListener('click', () => {
            settingsModal.style.display = 'none';
        });
    }

    if (window) {
        window.addEventListener('click', (e) => {
            if (e.target === settingsModal) {
                settingsModal.style.display = 'none';
            }
        });
    }

    if (saveSettingsBtn) {
        saveSettingsBtn.addEventListener('click', async () => {
            saveSettingsBtn.disabled = true;
            saveSettingsBtn.textContent = "Saving...";

            // Get tickers from Asset Manager
            const tickers = assetManager ? assetManager.getAllTickers() : [];
            const capital = optCapital ? parseFloat(optCapital.value) : 100000;

            if (tickers.length === 0) {
                alert("Please select at least one asset.");
                saveSettingsBtn.disabled = false;
                saveSettingsBtn.textContent = "Save Configuration";
                return;
            }

            const newConfig = {
                optimization: {
                    method: optMethod.value,
                    cvar_alpha: parseFloat(optCvarAlpha.value),
                    min_expected_return: parseFloat(optMinReturn.value)
                },
                data: {
                    tickers: tickers
                },
                capital: {
                    total_investment: capital
                }
            };

            const res = await Pipeline.updateConfig(newConfig);

            if (res.status === 'success') {
                renderConfig(res.data);
                settingsModal.style.display = 'none';
                alert("Configuration Saved!");
            } else {
                alert("Failed to save: " + res.message);
            }

            saveSettingsBtn.disabled = false;
            saveSettingsBtn.textContent = "Save Configuration";
        });
    }
}

function updateThemeIcon() {
    const isLight = document.documentElement.getAttribute('data-theme') === 'light';
    els.themeIcon.textContent = isLight ? '☀️' : '🌙';
}

function renderConfig(config) {
    if (!config) return;
    const tickers = config.data?.tickers || [];
    els.assetList.innerHTML = tickers.map(t => `<li>${t}</li>`).join('');

    const p = config.optimization || {};
    els.dataParams.innerHTML = `
        <div class="kv-item"><span>Start Date</span><strong>${config.data.start_date}</strong></div>
        <div class="kv-item"><span>Strategy</span><strong>${(p.method || 'CVaR').toUpperCase()}</strong></div>
        <div class="kv-item"><span>Solver</span><strong>${p.solver}</strong></div>
        <div class="kv-item"><span>Capital</span><strong>$${(config.capital?.total_investment || 100000).toLocaleString()}</strong></div>
    `;

    // Update Modal Inputs
    const optMethod = document.getElementById('opt-method');
    const optCvarAlpha = document.getElementById('opt-cvar-alpha');
    const optMinReturn = document.getElementById('opt-min-return');
    const optCapital = document.getElementById('opt-capital');

    if (optMethod) optMethod.value = p.method || 'cvar';
    if (optCvarAlpha) optCvarAlpha.value = p.cvar_alpha || 0.05;
    if (optMinReturn) optMinReturn.value = p.min_expected_return || 0.0002;
    if (optCapital) optCapital.value = config.capital?.total_investment || 100000;

    // Initialize Asset Manager with tickers
    if (!assetManager) {
        assetManager = new AssetManager('asset-manager-root', tickers);
    } else {
        assetManager.init(tickers);
    }
}

async function runPipeline() {
    els.runBtn.disabled = true;
    els.runBtn.textContent = "Requesting...";

    const res = await Pipeline.startExecution();

    if (res.status === 'success') {
        els.runBtn.textContent = "Running...";
        els.pipelineStatus.textContent = "Initializing backend...";
        startPolling();
    } else {
        els.runBtn.disabled = false;
        els.runBtn.textContent = "Run Pipeline";
        alert("Failed to start pipeline: " + (res.message || 'Unknown error'));
    }
}

function startPolling() {
    if (pollingInterval) clearInterval(pollingInterval);

    pollingInterval = setInterval(async () => {
        const state = await Pipeline.getStatus();
        if (!state) return;

        updateUI(state);

        if (!state.is_running && state.status !== 'idle') {
            clearInterval(pollingInterval);
            finishExecution(state);
        }
    }, 1000);
}

function updateUI(state) {
    els.pipelineStatus.textContent = state.step_details;

    els.steps.forEach(step => {
        const stepNum = parseInt(step.dataset.step);
        step.classList.remove('active', 'completed');

        if (stepNum < state.current_step) {
            step.classList.add('completed');
        } else if (stepNum === state.current_step) {
            step.classList.add('active');
        }
    });
}

function finishExecution(state) {
    els.runBtn.disabled = false;
    els.runBtn.textContent = "Run Pipeline";

    if (state.status === 'completed' && state.results) {
        renderResults(state.results);
        updateCharts(state.results);
        els.pipelineStatus.textContent = "Execution Completed Successfully";
    } else {
        els.pipelineStatus.textContent = "Execution Failed";
        console.error(state.error);
    }
}

function renderResults(results) {
    const m = results.metrics || {};
    const sim = results.monte_carlo || {};
    const w = results.weights || {};
    const alloc = results.allocation || {};

    // Metrics
    els.resTotalReturn.textContent = fmtPct(m.total_return);
    els.resVolatility.textContent = fmtPct(m.volatility);
    els.resMaxDD.textContent = fmtPct(m.max_drawdown);
    els.resCalmar.textContent = m.calmar_ratio?.toFixed(2);
    els.resCvar.textContent = fmtPct(m.cvar);

    // Simulation
    els.worstDD.textContent = fmtPct(sim.worst_case);
    els.percentileDD.textContent = fmtPct(sim.percentile_95);
    els.medianDD.textContent = fmtPct(sim.median);

    // Additional Simulation Metrics
    if (els.valAvgDD) els.valAvgDD.textContent = fmtPct(sim.average);
    if (els.valSimCount) els.valSimCount.textContent = sim.simulations || '--';

    // Weights Table with Allocation
    if (els.weightsTableBody) {
        const weightEntries = Object.entries(w);

        // Get total investment from config for fallback allocation
        const totalInvestment = results.total_investment || 100000;

        // Compute rounded percentages and adjust so they sum to exactly 100.00%
        let rawPcts = weightEntries.map(([, weight]) => Math.round(weight * 10000) / 100);
        let pctSum = rawPcts.reduce((a, b) => a + b, 0);
        // Fix rounding discrepancy by adjusting the largest weight
        if (rawPcts.length > 0 && Math.abs(pctSum - 100) > 0.001) {
            let maxIdx = 0;
            for (let i = 1; i < rawPcts.length; i++) {
                if (rawPcts[i] > rawPcts[maxIdx]) maxIdx = i;
            }
            rawPcts[maxIdx] = Math.round((rawPcts[maxIdx] + (100 - pctSum)) * 100) / 100;
        }

        // Build table rows
        let totalAllocation = 0;
        const rows = weightEntries.map(([ticker, weight], idx) => {
            let amount = alloc[ticker];
            if (amount === undefined) {
                amount = weight * totalInvestment;
            }
            totalAllocation += amount;
            const pctDisplay = rawPcts[idx].toFixed(2);

            return `
                <tr>
                    <td>${ticker}</td>
                    <td style="font-family: var(--font-mono);">${pctDisplay}%</td>
                    <td style="font-family: var(--font-mono);">$${amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                </tr>
            `;
        }).join('');

        // Add total row (always 100.00%)
        const totalRow = `
            <tr style="border-top: 2px solid var(--color-border); font-weight: 600; background: var(--color-surface);">
                <td>TOTAL</td>
                <td style="font-family: var(--font-mono);">100.00%</td>
                <td style="font-family: var(--font-mono);">$${totalAllocation.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
            </tr>
        `;

        els.weightsTableBody.innerHTML = rows + totalRow;
    }
}

function fmtPct(val) {
    if (val === undefined || val === null) return '--';
    return (val * 100).toFixed(2) + '%';
}

init();
