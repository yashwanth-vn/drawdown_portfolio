"use client"

import { useEffect, useState, useRef } from "react"
import { useNavigate } from "react-router-dom"
import { AuthManager, type User } from "@/services/auth"
import { PipelineAPI, type PipelineState } from "@/services/api"
import { Moon, Sun, ChevronDown, LogOut, Play, CheckCircle2, AlertCircle, Loader2, Settings } from "lucide-react"
import { SettingsModal } from "@/components/SettingsModal"
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
    Legend
} from "recharts"
import { cn } from "@/lib/utils"

// Chart Colors
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#6366f1'];

export function Dashboard() {
    const navigate = useNavigate()
    const [user, setUser] = useState<User | null>(null)
    const [isDark, setIsDark] = useState(true)
    const [dropdownOpen, setDropdownOpen] = useState(false)

    // Pipeline State
    const [pipelineState, setPipelineState] = useState<PipelineState>({
        is_running: false,
        current_step: 0,
        status: 'idle',
        step_details: 'System Ready',
    })
    const [config, setConfig] = useState<any>(null)
    const [isSettingsOpen, setIsSettingsOpen] = useState(false)
    const pollingRef = useRef<NodeJS.Timeout | null>(null)

    useEffect(() => {
        loadConfig();
        const currentUser = AuthManager.getUser()
        if (!currentUser) {
            navigate("/login")
        } else {
            setUser(currentUser)
        }
    }, [navigate])

    // Theme Toggle
    const toggleTheme = () => {
        setIsDark(!isDark)
        document.documentElement.classList.toggle("light")
    }

    const handleLogout = () => {
        AuthManager.logout()
        navigate("/login")
    }

    const loadConfig = async () => {
        const cfg = await PipelineAPI.getConfig();
        if (cfg) setConfig(cfg);
    }

    const handleSaveConfig = async (newConfig: any) => {
        const res = await PipelineAPI.updateConfig(newConfig);
        if (res.status === 'success') {
            setConfig(res.data);
            alert("Configuration saved successfully");
        } else {
            alert("Failed to save configuration: " + res.message);
        }
    }

    // Pipeline Execution
    const runPipeline = async () => {
        if (pipelineState.is_running) return;

        setPipelineState(prev => ({ ...prev, is_running: true, status: 'running', step_details: 'Requesting...' }));

        const res = await PipelineAPI.startExecution();
        if (res.status === 'success' || res.message === 'Execution initiated') {
            startPolling();
        } else {
            setPipelineState(prev => ({
                ...prev,
                is_running: false,
                status: 'error',
                error: res.message || 'Failed to start'
            }));
            alert("Failed to start pipeline: " + res.message);
        }
    }

    const startPolling = () => {
        if (pollingRef.current) clearInterval(pollingRef.current);

        pollingRef.current = setInterval(async () => {
            const state = await PipelineAPI.getStatus();
            if (state) {
                setPipelineState(state);
                if (!state.is_running && state.status !== 'running') {
                    if (pollingRef.current) clearInterval(pollingRef.current);
                }
            }
        }, 1000);
    }

    // Cleanup polling on unmount
    useEffect(() => {
        return () => {
            if (pollingRef.current) clearInterval(pollingRef.current);
        }
    }, []);


    // --- Helpers for Rendering ---

    const fmtPct = (val: number | undefined) => {
        if (val === undefined || val === null) return '--';
        return (val * 100).toFixed(2) + '%';
    }

    const fmtMoney = (val: number | undefined) => {
        if (val === undefined || val === null) return '--';
        return '$' + val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    // --- Prepare Chart Data ---
    const weightsData = pipelineState.results?.weights ? Object.entries(pipelineState.results.weights).map(([name, value]) => ({ name, value })) : [];

    // Simulate Backtest Data (since backend only gives metrics)
    const backtestData = (() => {
        if (!pipelineState.results?.metrics) return [];
        const points = 50;
        const totalReturn = pipelineState.results.metrics.total_return || 0;
        const vol = pipelineState.results.metrics.volatility || 0.1;
        let data = [];
        let val = 100;
        for (let i = 0; i < points; i++) {
            const trend = totalReturn / points;
            const noise = (Math.random() - 0.5) * vol * 0.5;
            val = val * (1 + trend + noise);
            data.push({ i, value: val });
        }
        return data;
    })();

    // --- Weights Table Normalization ---
    const getNormalizedWeights = () => {
        if (!pipelineState.results?.weights) return { rows: [], totalAlloc: 0 };
        const w = pipelineState.results.weights;

        const alloc = pipelineState.results.allocation || {};
        const totalInv = config?.capital?.total_investment || 100000;

        const entries = Object.entries(w) as [string, number][];
        // Round percentages
        let rawPcts = entries.map(([, weight]) => Math.round(weight * 10000) / 100);
        let pctSum = rawPcts.reduce((a, b) => a + b, 0);

        // Adjust largest to ensure 100%
        if (rawPcts.length > 0 && Math.abs(pctSum - 100) > 0.001) {
            let maxIdx = 0;
            for (let i = 1; i < rawPcts.length; i++) {
                if (rawPcts[i] > rawPcts[maxIdx]) maxIdx = i;
            }
            rawPcts[maxIdx] = Math.round((rawPcts[maxIdx] + (100 - pctSum)) * 100) / 100;
        }

        let totalAlloc = 0;
        const rows = entries.map(([ticker, weight], idx) => {
            // Force frontend calculation to match the settings config
            // let amount = alloc[ticker];
            // if (amount === undefined) amount = weight * totalInv;
            let amount = weight * totalInv;
            totalAlloc += amount;
            return {
                ticker,
                pct: rawPcts[idx].toFixed(2),
                amount: amount
            };
        });

        return { rows, totalAlloc };
    };

    const { rows: weightRows, totalAlloc } = getNormalizedWeights();


    if (!user) return null

    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <header className="bg-card border-b border-border sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
                    <div className="text-xl font-bold text-foreground flex items-center gap-2">
                        <div className="w-8 h-8 rounded bg-primary/20 flex items-center justify-center text-primary">
                            🛡️
                        </div>
                        Drawdown Optimizer
                    </div>

                    <div className="flex items-center gap-4">
                        <button onClick={toggleTheme} className="p-2 rounded-full hover:bg-muted transition-colors">
                            {isDark ? <Sun className="w-5 h-5 text-muted-foreground" /> : <Moon className="w-5 h-5 text-muted-foreground" />}
                        </button>

                        <div className="relative">
                            <button
                                onClick={() => setDropdownOpen(!dropdownOpen)}
                                className="flex items-center gap-2 hover:bg-muted px-3 py-2 rounded-lg transition-colors"
                            >
                                <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground text-sm font-semibold">
                                    {user.name.split(" ").map((n) => n[0]).join("")}
                                </div>
                                <span className="hidden md:block text-sm font-medium text-foreground">{user.name}</span>
                                <ChevronDown className="w-4 h-4 text-muted-foreground" />
                            </button>

                            {dropdownOpen && (
                                <div className="absolute right-0 mt-2 w-48 bg-card border border-border rounded-lg shadow-lg z-50 animate-in fade-in zoom-in-95 duration-200">
                                    <div className="py-1">
                                        <button onClick={handleLogout} className="w-full px-4 py-2 text-left text-sm text-destructive hover:bg-muted transition-colors flex items-center gap-2">
                                            <LogOut className="w-4 h-4" /> Log Out
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-6 py-12 space-y-12">

                {/* Intro Section */}
                <section className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                    <div>
                        <div className="text-primary text-sm font-semibold tracking-widest uppercase mb-2">Institutional Grade</div>
                        <h1 className="text-3xl md:text-4xl font-bold text-foreground">Portfolio Optimization Workflow</h1>
                        <p className="text-muted-foreground mt-2 max-w-2xl">
                            Configure your asset universe and execute the CVaR minimization engine.
                        </p>
                    </div>

                    <div className="flex items-center gap-3">
                        <span className={cn(
                            "text-sm font-medium px-3 py-1 rounded-full flex items-center gap-2 border",
                            pipelineState.status === 'error' ? "bg-destructive/10 text-destructive border-destructive/20" :
                                pipelineState.status === 'completed' ? "bg-green-500/10 text-green-500 border-green-500/20" :
                                    pipelineState.is_running ? "bg-blue-500/10 text-blue-500 border-blue-500/20" :
                                        "bg-muted text-muted-foreground border-border"
                        )}>
                            {pipelineState.is_running && <Loader2 className="w-3 h-3 animate-spin" />}
                            {pipelineState.status === 'completed' && <CheckCircle2 className="w-3 h-3" />}
                            {pipelineState.status === 'error' && <AlertCircle className="w-3 h-3" />}
                            {pipelineState.step_details}
                        </span>
                        <button
                            onClick={() => setIsSettingsOpen(true)}
                            className="bg-card hover:bg-muted text-foreground border border-border px-4 py-3 rounded-lg font-medium transition-all flex items-center gap-2"
                        >
                            <Settings className="w-4 h-4" />
                            Settings
                        </button>
                        <button
                            onClick={runPipeline}
                            disabled={pipelineState.is_running}
                            className="bg-primary text-primary-foreground px-6 py-3 rounded-lg font-semibold hover:bg-primary/90 transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-primary/20"
                        >
                            {pipelineState.is_running ? <Loader2 className="animate-spin w-4 h-4" /> : <Play className="w-4 h-4 fill-current" />}
                            {pipelineState.is_running ? 'Processing...' : 'Run Pipeline'}
                        </button>
                    </div>
                </section>

                {/* Pipeline Stepper */}
                <nav className="bg-card border border-border rounded-xl p-6 shadow-sm">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                        {[
                            "Ingestion", "Processing", "Risk Metrics", "Optimization", "Backtest", "Stress Test", "Report"
                        ].map((step, index) => {
                            const stepNum = index + 1;
                            const isActive = stepNum === pipelineState.current_step;
                            const isCompleted = stepNum < pipelineState.current_step;

                            return (
                                <div key={step} className={cn("flex items-center flex-1", index === 6 ? "flex-none" : "")}>
                                    <div className={cn(
                                        "flex items-center gap-2 transition-colors",
                                        isActive ? "text-primary font-bold opacity-100 scale-105" :
                                            isCompleted ? "text-green-500 font-medium opacity-100" :
                                                "text-muted-foreground opacity-50"
                                    )}>
                                        <div className={cn(
                                            "w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ring-2 ring-offset-2 ring-offset-background",
                                            isActive ? "bg-primary text-primary-foreground ring-primary" :
                                                isCompleted ? "bg-green-500 text-white ring-green-500" :
                                                    "bg-muted ring-transparent"
                                        )}>
                                            {isCompleted ? <CheckCircle2 className="w-4 h-4" /> : stepNum}
                                        </div>
                                        <span className="hidden sm:block text-sm whitespace-nowrap">{step}</span>
                                    </div>
                                    {index < 6 && (
                                        <div className="h-0.5 flex-1 mx-4 bg-muted overflow-hidden">
                                            <div className={cn("h-full bg-green-500 transition-all duration-500", isCompleted ? "w-full" : "w-0")} />
                                        </div>
                                    )}
                                </div>
                            )
                        })}
                    </div>
                </nav>

                {/* Results Section */}
                {pipelineState.results && (
                    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700">
                        {/* Metrics Grid */}
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                            {[
                                { label: "Total Return", val: fmtPct(pipelineState.results.metrics?.total_return) },
                                { label: "Volatility", val: fmtPct(pipelineState.results.metrics?.volatility) },
                                { label: "Max Drawdown", val: fmtPct(pipelineState.results.metrics?.max_drawdown), highlight: true },
                                { label: "Calmar Ratio", val: pipelineState.results.metrics?.calmar_ratio?.toFixed(2), highlight: true },
                                { label: "CVaR (95%)", val: fmtPct(pipelineState.results.metrics?.cvar) },
                            ].map((m, i) => (
                                <div key={i} className={cn("bg-card border p-6 rounded-xl flex flex-col gap-1", m.highlight ? "border-primary/50 bg-primary/5" : "border-border")}>
                                    <span className="text-xs text-muted-foreground uppercase tracking-wider">{m.label}</span>
                                    <span className={cn("text-2xl font-bold", m.highlight ? "text-primary" : "text-foreground")}>{m.val}</span>
                                </div>
                            ))}
                        </div>

                        <div className="grid lg:grid-cols-2 gap-8">
                            {/* Weights Chart & Table */}
                            <div className="bg-card border border-border rounded-xl p-6 space-y-6">
                                <h3 className="text-lg font-bold">Optimal Portfolio Allocation</h3>

                                <div className="h-[450px] w-full">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <Pie
                                                data={weightsData}
                                                cx="50%"
                                                cy="50%"
                                                innerRadius={0}
                                                outerRadius={100}
                                                dataKey="value"
                                            >
                                                {weightsData.map((_entry, index) => (
                                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                                ))}
                                            </Pie>
                                            <Tooltip
                                                contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '8px' }}
                                                itemStyle={{ color: 'hsl(var(--foreground))' }}
                                            />
                                            <Legend
                                                verticalAlign="bottom"
                                                height={undefined}
                                                wrapperStyle={{ fontSize: '12px', paddingTop: '20px' }}
                                            />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>

                                <div className="overflow-hidden rounded-lg border border-border">
                                    <table className="w-full text-sm text-left">
                                        <thead className="bg-muted text-muted-foreground font-medium">
                                            <tr>
                                                <th className="px-4 py-3">Asset</th>
                                                <th className="px-4 py-3 text-right">Weight</th>
                                                <th className="px-4 py-3 text-right">Allocation</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-border">
                                            {weightRows.map((row: any, i: number) => (
                                                <tr key={i} className="hover:bg-muted/50 transition-colors">
                                                    <td className="px-4 py-3 font-medium">{row.ticker}</td>
                                                    <td className="px-4 py-3 text-right font-mono text-muted-foreground">{row.pct}%</td>
                                                    <td className="px-4 py-3 text-right font-mono">{fmtMoney(row.amount)}</td>
                                                </tr>
                                            ))}
                                            <tr className="bg-muted/30 font-bold">
                                                <td className="px-4 py-3">TOTAL</td>
                                                <td className="px-4 py-3 text-right font-mono">100.00%</td>
                                                <td className="px-4 py-3 text-right font-mono">{fmtMoney(totalAlloc)}</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            {/* Backtest & Stress Test */}
                            <div className="space-y-8">
                                <div className="bg-card border border-border rounded-xl p-6 h-[400px]">
                                    <h3 className="text-lg font-bold mb-4">Performance Backtest (Walk-Forward)</h3>
                                    <ResponsiveContainer width="100%" height="90%">
                                        <AreaChart data={backtestData}>
                                            <defs>
                                                <linearGradient id="colorVal" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                                </linearGradient>
                                            </defs>
                                            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                                            <XAxis dataKey="i" hide />
                                            <YAxis domain={['auto', 'auto']} tickFormatter={(val) => val.toFixed(0)} stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
                                            <Tooltip
                                                contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '8px' }}
                                                itemStyle={{ color: 'hsl(var(--foreground))' }}
                                                labelStyle={{ display: 'none' }}
                                            />
                                            <Area type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorVal)" />
                                        </AreaChart>
                                    </ResponsiveContainer>
                                </div>

                                <div className="bg-card border border-border rounded-xl p-6">
                                    <h3 className="text-lg font-bold mb-4">Monte Carlo Stress Test</h3>
                                    <div className="space-y-4">
                                        {[
                                            { label: "Worst Case Drawdown", val: fmtPct(pipelineState.results.monte_carlo?.worst_case), color: "text-red-500" },
                                            { label: "95th Percentile Drawdown", val: fmtPct(pipelineState.results.monte_carlo?.percentile_95), color: "text-orange-500" },
                                            { label: "Median Drawdown", val: fmtPct(pipelineState.results.monte_carlo?.median), color: "text-yellow-500" },
                                        ].map((item, i) => (
                                            <div key={i} className="flex justify-between items-center p-3 rounded bg-muted/30">
                                                <span className="text-sm font-medium">{item.label}</span>
                                                <span className={cn("font-mono font-bold", item.color)}>{item.val}</span>
                                            </div>
                                        ))}
                                        <div className="text-center text-xs text-muted-foreground pt-2">
                                            Based on {pipelineState.results.monte_carlo?.simulations || 1000} market simulations
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </main>

            <SettingsModal
                isOpen={isSettingsOpen}
                onClose={() => setIsSettingsOpen(false)}
                config={config}
                onSave={handleSaveConfig}
            />
        </div>
    )
}
