import { useState, useEffect, useMemo } from "react";
import { X, Save, RotateCcw, Search, Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import { POPULAR_ASSETS } from "@/lib/assets";

interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
    config: any;
    onSave: (newConfig: any) => Promise<void>;
}

export function SettingsModal({ isOpen, onClose, config, onSave }: SettingsModalProps) {
    const [localConfig, setLocalConfig] = useState<any>(null);
    const [activeTab, setActiveTab] = useState("universe");
    const [isSaving, setIsSaving] = useState(false);
    const [searchTerm, setSearchTerm] = useState("");

    useEffect(() => {
        if (config) {
            setLocalConfig(JSON.parse(JSON.stringify(config)));
        }
    }, [config, isOpen]);

    if (!isOpen || !localConfig) return null;

    const handleSave = async () => {
        setIsSaving(true);
        await onSave(localConfig);
        setIsSaving(false);
        onClose();
    };

    const updateNested = (path: string[], value: any) => {
        setLocalConfig((prev: any) => {
            const next = { ...prev };
            let current = next;
            for (let i = 0; i < path.length - 1; i++) {
                current = current[path[i]];
            }
            current[path[path.length - 1]] = value;
            return next;
        });
    };

    const handleTickerChange = (text: string) => {
        const tickers = text.split(/[\n,]+/).map(t => t.trim()).filter(t => t);
        updateNested(['data', 'tickers'], tickers);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="w-full max-w-2xl bg-card border border-border rounded-xl shadow-2xl flex flex-col max-h-[90vh]">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-border">
                    <h2 className="text-xl font-bold">Pipeline Configuration</h2>
                    <button onClick={onClose} className="p-2 hover:bg-muted rounded-full transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-border px-6">
                    {['universe', 'optimization', 'simulation'].map(tab => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={cn(
                                "px-4 py-3 text-sm font-medium border-b-2 transition-colors capitalize",
                                activeTab === tab ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"
                            )}
                        >
                            {tab}
                        </button>
                    ))}
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {activeTab === 'universe' && (
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-muted-foreground">Start Date</label>
                                    <input
                                        type="date"
                                        className="w-full bg-muted/50 border border-input rounded-md px-3 py-2 text-sm"
                                        value={localConfig.data.start_date}
                                        onChange={(e) => updateNested(['data', 'start_date'], e.target.value)}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-muted-foreground">End Date</label>
                                    <input
                                        type="date"
                                        className="w-full bg-muted/50 border border-input rounded-md px-3 py-2 text-sm"
                                        value={localConfig.data.end_date}
                                        onChange={(e) => updateNested(['data', 'end_date'], e.target.value)}
                                    />
                                </div>
                            </div>

                            <div className="space-y-4">
                                <label className="text-sm font-medium text-muted-foreground">Asset Universe (Tickers)</label>

                                <div className="border border-input rounded-md p-4 space-y-4 bg-muted/20">
                                    <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto">
                                        {localConfig.data.tickers.map((ticker: string) => (
                                            <div key={ticker} className="flex items-center gap-1 bg-primary/10 text-primary border border-primary/20 px-2.5 py-1 rounded-full text-sm font-medium animate-in fade-in zoom-in duration-200">
                                                <span>{ticker}</span>
                                                <button
                                                    onClick={() => {
                                                        const newTickers = localConfig.data.tickers.filter((t: string) => t !== ticker);
                                                        updateNested(['data', 'tickers'], newTickers);
                                                    }}
                                                    className="hover:bg-primary/20 rounded-full p-0.5"
                                                >
                                                    <X className="w-3 h-3" />
                                                </button>
                                            </div>
                                        ))}
                                        {localConfig.data.tickers.length === 0 && (
                                            <span className="text-sm text-muted-foreground italic">No assets selected</span>
                                        )}
                                    </div>

                                    <div className="flex gap-2">
                                        <input
                                            type="text"
                                            placeholder="Add Ticker (e.g. TSLA)"
                                            className="flex-1 bg-background border border-input rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                                            onKeyDown={(e) => {
                                                if (e.key === 'Enter') {
                                                    const val = e.currentTarget.value.trim().toUpperCase();
                                                    if (val && !localConfig.data.tickers.includes(val)) {
                                                        updateNested(['data', 'tickers'], [...localConfig.data.tickers, val]);
                                                        e.currentTarget.value = '';
                                                    }
                                                }
                                            }}
                                        />
                                        <button className="bg-primary text-primary-foreground px-3 py-2 rounded-md text-sm font-medium hover:bg-primary/90">
                                            Add
                                        </button>
                                    </div>
                                    <p className="text-xs text-muted-foreground">Type a ticker and press Enter to add to the universe.</p>
                                </div>

                                {/* Available Assets Selector */}
                                <div className="space-y-3 pt-2">
                                    <div className="flex items-center justify-between">
                                        <h3 className="text-sm font-medium text-muted-foreground">Available Assets</h3>
                                        <div className="relative w-48">
                                            <Search className="absolute left-2 top-2 w-3 h-3 text-muted-foreground" />
                                            <input
                                                type="text"
                                                placeholder="Search assets..."
                                                className="w-full bg-muted/50 border border-input rounded-md pl-8 pr-2 py-1 text-xs"
                                                value={searchTerm}
                                                onChange={(e) => setSearchTerm(e.target.value)}
                                            />
                                        </div>
                                    </div>

                                    <div className="border border-border rounded-md h-64 overflow-y-auto p-4 space-y-6 bg-card">
                                        {Object.entries(POPULAR_ASSETS).map(([category, assets]) => {
                                            const filtered = assets.filter(a =>
                                                a.ticker.toLowerCase().includes(searchTerm.toLowerCase()) ||
                                                a.name.toLowerCase().includes(searchTerm.toLowerCase())
                                            );

                                            if (filtered.length === 0) return null;

                                            return (
                                                <div key={category} className="space-y-2">
                                                    <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider sticky top-0 bg-card py-1">{category}</h4>
                                                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                                                        {filtered.map(asset => {
                                                            const isSelected = localConfig.data.tickers.includes(asset.ticker);
                                                            return (
                                                                <button
                                                                    key={asset.ticker}
                                                                    onClick={() => {
                                                                        if (isSelected) {
                                                                            updateNested(['data', 'tickers'], localConfig.data.tickers.filter((t: string) => t !== asset.ticker));
                                                                        } else {
                                                                            updateNested(['data', 'tickers'], [...localConfig.data.tickers, asset.ticker]);
                                                                        }
                                                                    }}
                                                                    className={cn(
                                                                        "flex flex-col items-start p-2 rounded-md border text-left transition-all hover:shadow-sm",
                                                                        isSelected
                                                                            ? "bg-primary/5 border-primary/50 ring-1 ring-primary/20"
                                                                            : "bg-muted/30 border-border hover:bg-muted hover:border-muted-foreground/30"
                                                                    )}
                                                                >
                                                                    <div className="flex w-full justify-between items-center">
                                                                        <span className="font-bold text-xs">{asset.ticker}</span>
                                                                        {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-primary" />}
                                                                    </div>
                                                                    <span className="text-[10px] text-muted-foreground truncate w-full" title={asset.name}>{asset.name}</span>
                                                                </button>
                                                            )
                                                        })}
                                                    </div>
                                                </div>
                                            );
                                        })}
                                        {searchTerm && Object.values(POPULAR_ASSETS).flat().filter(a => a.ticker.toLowerCase().includes(searchTerm.toLowerCase()) || a.name.toLowerCase().includes(searchTerm.toLowerCase())).length === 0 && (
                                            <div className="text-center text-muted-foreground text-sm py-8">
                                                No assets found matching "{searchTerm}". <br />
                                                Use the custom input above to add it manually.
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'optimization' && (
                        <div className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-muted-foreground">Optimization Method</label>
                                <select
                                    className="w-full bg-muted/50 border border-input rounded-md px-3 py-2 text-sm"
                                    value={localConfig.optimization.method}
                                    onChange={(e) => updateNested(['optimization', 'method'], e.target.value)}
                                >
                                    <option value="kelly">Kelly Criterion</option>
                                    <option value="cvar">CVaR Minimization</option>
                                    <option value="mean_variance">Mean-Variance (Markowitz)</option>
                                    <option value="risk_parity">Risk Parity</option>
                                    <option value="sortino">Max Sortino Ratio</option>
                                    <option value="omega">Max Omega Ratio</option>
                                    <option value="tracking_error">Min Tracking Error</option>
                                    <option value="information_ratio">Max Information Ratio</option>
                                    <option value="max_drawdown">Min Max Drawdown</option>
                                </select>
                            </div>

                            {/* Conditional Parameters */}
                            {localConfig.optimization.method === 'cvar' && (
                                <div className="space-y-2 animate-in fade-in slide-in-from-top-2">
                                    <label className="text-sm font-medium text-muted-foreground">CVaR Alpha (Confidence Level)</label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        min="0.01"
                                        max="0.99"
                                        className="w-full bg-muted/50 border border-input rounded-md px-3 py-2 text-sm"
                                        value={localConfig.optimization.cvar_alpha ?? 0.05}
                                        onChange={(e) => updateNested(['optimization', 'cvar_alpha'], parseFloat(e.target.value))}
                                    />
                                    <p className="text-xs text-muted-foreground">Lower alpha = more extreme tail risk protection (e.g. 0.05 = 95%)</p>
                                </div>
                            )}

                            {localConfig.optimization.method === 'mean_variance' && (
                                <div className="space-y-2 animate-in fade-in slide-in-from-top-2">
                                    <label className="text-sm font-medium text-muted-foreground">Min Expected Return (Daily)</label>
                                    <input
                                        type="number"
                                        step="0.0001"
                                        className="w-full bg-muted/50 border border-input rounded-md px-3 py-2 text-sm"
                                        value={localConfig.optimization.min_expected_return ?? 0.0005}
                                        onChange={(e) => updateNested(['optimization', 'min_expected_return'], parseFloat(e.target.value))}
                                    />
                                </div>
                            )}

                            {localConfig.optimization.method === 'sortino' && (
                                <div className="space-y-2 animate-in fade-in slide-in-from-top-2">
                                    <label className="text-sm font-medium text-muted-foreground">Minimum Acceptable Return (MAR)</label>
                                    <input
                                        type="number"
                                        step="0.0001"
                                        className="w-full bg-muted/50 border border-input rounded-md px-3 py-2 text-sm"
                                        value={localConfig.optimization.mar ?? 0.0}
                                        onChange={(e) => updateNested(['optimization', 'mar'], parseFloat(e.target.value))}
                                    />
                                </div>
                            )}

                            {localConfig.optimization.method === 'omega' && (
                                <div className="space-y-2 animate-in fade-in slide-in-from-top-2">
                                    <label className="text-sm font-medium text-muted-foreground">Omega Threshold</label>
                                    <input
                                        type="number"
                                        step="0.0001"
                                        className="w-full bg-muted/50 border border-input rounded-md px-3 py-2 text-sm"
                                        value={localConfig.optimization.omega_threshold ?? 0.0}
                                        onChange={(e) => updateNested(['optimization', 'omega_threshold'], parseFloat(e.target.value))}
                                    />
                                </div>
                            )}

                            <div className="space-y-2">
                                <label className="text-sm font-medium text-muted-foreground">Initial Capital</label>
                                <input
                                    type="number"
                                    className="w-full bg-muted/50 border border-input rounded-md px-3 py-2 text-sm"
                                    value={localConfig.capital.total_investment}
                                    onChange={(e) => updateNested(['capital', 'total_investment'], parseFloat(e.target.value))}
                                />
                            </div>
                        </div>
                    )}

                    {activeTab === 'simulation' && (
                        <div className="space-y-4">
                            <div className="flex items-center gap-2">
                                <input
                                    type="checkbox"
                                    id="sim-enabled"
                                    checked={localConfig.simulation.enabled}
                                    onChange={(e) => updateNested(['simulation', 'enabled'], e.target.checked)}
                                    className="rounded border-gray-300"
                                />
                                <label htmlFor="sim-enabled" className="text-sm font-medium">Enable Monte Carlo Simulation</label>
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-muted-foreground">Number of Simulations</label>
                                <input
                                    type="number"
                                    className="w-full bg-muted/50 border border-input rounded-md px-3 py-2 text-sm"
                                    value={localConfig.simulation.number_of_simulations}
                                    onChange={(e) => updateNested(['simulation', 'number_of_simulations'], parseInt(e.target.value))}
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-muted-foreground">Simulation Horizon (Days)</label>
                                <input
                                    type="number"
                                    className="w-full bg-muted/50 border border-input rounded-md px-3 py-2 text-sm"
                                    value={localConfig.simulation.simulation_horizon}
                                    onChange={(e) => updateNested(['simulation', 'simulation_horizon'], parseInt(e.target.value))}
                                />
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-border flex justify-end gap-3 bg-muted/20">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm font-medium hover:bg-muted rounded-md transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={isSaving}
                        className="px-6 py-2 bg-primary text-primary-foreground text-sm font-bold rounded-md hover:bg-primary/90 transition-colors flex items-center gap-2"
                    >
                        {isSaving ? <RotateCcw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                        Save Changes
                    </button>
                </div>
            </div>
        </div>
    );
}
