/*
    asset_manager.js
    Manages the dynamic column-based asset selection UI.
    Enhanced with Live Asset Discovery and Multi-Select Lists.
*/

export class AssetManager {
    constructor(containerId, initialTickers = []) {
        this.container = document.getElementById(containerId);
        this.columns = [];
        this.assetUniverse = new Set();

        this.assetTypes = [
            { id: 'equity', label: 'Equities (Stocks)' },
            { id: 'etf', label: 'ETFs' },
            { id: 'index', label: 'Market Indices' },
            { id: 'crypto', label: 'Cryptocurrencies' },
            { id: 'forex', label: 'Forex' },
            { id: 'commodity', label: 'Commodities' },
            { id: 'fixed_income', label: 'Fixed Income' }
        ];

        this.init(initialTickers);
    }

    init(initialTickers) {
        this.container.innerHTML = '';
        this.assetUniverse.clear();
        this.columns = [];

        // Controls
        this.controlsContainer = document.createElement('div');
        this.controlsContainer.className = 'asset-controls';

        const addBtn = document.createElement('button');
        addBtn.className = 'btn btn-secondary btn-sm';
        addBtn.innerHTML = '＋ Add Asset Column';
        addBtn.onclick = () => this.addColumn();
        this.controlsContainer.appendChild(addBtn);

        this.container.appendChild(this.controlsContainer);

        // Initial setup
        if (initialTickers && initialTickers.length > 0) {
            // Create a general column to hold existing assets
            // In a real app we'd query their type, but for now we'll put them in a Mixed/Equity column
            // Or better, we just start fresh if the user wants discovery, 
            // but we must preserve state.
            // Let's create one column and add them.
            const col = this.addColumn('equity');
            initialTickers.forEach(t => this.addAssetToColumn(col, t, { symbol: t, name: t }));
        } else {
            this.addColumn();
        }
    }

    addColumn(defaultType = 'equity') {
        const colId = `col-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const col = {
            id: colId,
            type: defaultType,
            assets: new Set(), // selected assets in this column
            availableAssets: [] // loaded from backend
        };

        const colEl = document.createElement('div');
        colEl.className = 'asset-column';
        colEl.id = colId;
        colEl.innerHTML = `
            <div class="column-header">
                <select class="form-control asset-type-select">
                    ${this.assetTypes.map(t => `<option value="${t.id}" ${t.id === defaultType ? 'selected' : ''}>${t.label}</option>`).join('')}
                </select>
                <button class="remove-col-btn" title="Remove Column">×</button>
            </div>
            <div class="asset-search-box">
                 <input type="text" class="form-control asset-filter" placeholder="Search assets...">
            </div>
            <div class="asset-multi-select-list">
                <div class="loading-indicator">Loading assets...</div>
            </div>
            <div class="column-footer">
                <small class="asset-count">0 selected</small>
            </div>
        `;

        this.container.insertBefore(colEl, this.controlsContainer);
        this.columns.push(col);

        // Event Listeners
        const select = colEl.querySelector('.asset-type-select');
        select.addEventListener('change', (e) => {
            col.type = e.target.value;
            this.fetchAssetsForColumn(col);
        });

        const removeColBtn = colEl.querySelector('.remove-col-btn');
        removeColBtn.addEventListener('click', () => this.removeColumn(colId));

        const filterInput = colEl.querySelector('.asset-filter');
        filterInput.addEventListener('input', (e) => {
            this.renderAssetList(col, e.target.value);
        });

        // Initial Fetch
        this.fetchAssetsForColumn(col);

        return col;
    }

    async fetchAssetsForColumn(column) {
        const listEl = document.getElementById(column.id).querySelector('.asset-multi-select-list');
        listEl.innerHTML = '<div class="loading-indicator">Fetching live market data...</div>';

        try {
            const res = await fetch(`/api/assets/discover?type=${column.type}`, {
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await res.json();

            if (data.status === 'success') {
                column.availableAssets = data.data || [];
                this.renderAssetList(column);
            } else {
                listEl.innerHTML = `<div class="error-msg">Failed to load: ${data.message}</div>`;
            }
        } catch (e) {
            listEl.innerHTML = `<div class="error-msg">Error: ${e.message}</div>`;
        }
    }

    renderAssetList(column, filterText = '') {
        const listEl = document.getElementById(column.id).querySelector('.asset-multi-select-list');
        listEl.innerHTML = '';

        const filterLower = filterText.toLowerCase();

        // Combine available assets with already selected ones (in case selected are not in top 50 discovery)
        // Actually, we should merge.

        const assetsToShow = column.availableAssets.filter(a =>
            a.symbol.toLowerCase().includes(filterLower) ||
            a.name.toLowerCase().includes(filterLower)
        );

        if (assetsToShow.length === 0) {
            if (filterText) {
                listEl.innerHTML = `<div class="empty-state">No assets match "${filterText}"</div>`;
            } else {
                // Should not happen with backend fallbacks, but just in case
                listEl.innerHTML = '<div class="empty-state">No assets found. Try adding manually.</div>';
            }
            return;
        }

        assetsToShow.forEach(asset => {
            const isSelected = column.assets.has(asset.symbol);

            const item = document.createElement('div');
            item.className = `asset-option ${isSelected ? 'selected' : ''}`;
            item.innerHTML = `
                <div class="asset-info">
                    <span class="symbol">${asset.symbol}</span>
                    <span class="name">${asset.name}</span>
                </div>
                <div class="checkbox">${isSelected ? '✔' : ''}</div>
            `;

            item.addEventListener('click', () => {
                this.toggleAsset(column, asset);
            });

            listEl.appendChild(item);
        });
    }

    toggleAsset(column, asset) {
        if (column.assets.has(asset.symbol)) {
            column.assets.delete(asset.symbol);
            this.assetUniverse.delete(asset.symbol);
        } else {
            column.assets.add(asset.symbol);
            this.assetUniverse.add(asset.symbol);
        }

        // Re-render to update checkbox visual (simple way)
        // Optimization: just toggle class
        // But we need to update search filter context too generally.
        // Let's just update the specific item visual logic if possible, or re-render.
        // Re-rendering is fast enough for <100 items.
        // To persist filter:
        const filterVal = document.getElementById(column.id).querySelector('.asset-filter').value;
        this.renderAssetList(column, filterVal);
        this.updateFooter(column);
    }

    // Fallback for manually added assets if we kept that... 
    // The prompt removed the manual add requirement in favor of "Select Type -> Fetch All".
    // But we need to support "already selected" assets if they aren't in the fetch list.
    addAssetToColumn(column, ticker, assetObj) {
        column.assets.add(ticker);
        this.assetUniverse.add(ticker);
        // We push it to available so it renders
        if (!column.availableAssets.find(a => a.symbol === ticker)) {
            column.availableAssets.unshift(assetObj);
        }
        this.updateFooter(column);
    }

    updateFooter(column) {
        const countEl = document.getElementById(column.id).querySelector('.asset-count');
        countEl.textContent = `${column.assets.size} selected`;
    }

    removeColumn(colId) {
        const idx = this.columns.findIndex(c => c.id === colId);
        if (idx > -1) {
            this.columns[idx].assets.forEach(t => this.assetUniverse.delete(t));
            this.columns.splice(idx, 1);
            document.getElementById(colId).remove();
        }
    }

    getAllTickers() {
        return Array.from(this.assetUniverse);
    }
}
