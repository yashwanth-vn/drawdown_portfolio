import { ArrowRight, Activity, TrendingUp, ShieldCheck, Zap } from "lucide-react";
import { Link } from "react-router-dom";
import { WaveShader } from "@/components/ui/wave-1";
import { DitheringShader } from "@/components/ui/dithering-shader";

export function Intro() {
    return (
        <div className="relative min-h-screen w-full overflow-hidden bg-gradient-to-br from-[#050b1a] via-[#07142c] to-[#030712] font-sans text-white selection:bg-blue-500/30">

            {/* Background Shaders */}
            <div className="absolute inset-0 z-0 opacity-40">
                <DitheringShader opacity={0.3} />
            </div>

            {/* Wave Animation - positioned at bottom/center */}
            <div className="absolute bottom-0 left-0 right-0 z-0 h-[50vh] opacity-30">
                <WaveShader className="h-full w-full" />
            </div>

            {/* Main Content Container */}
            <div className="relative z-10 flex min-h-screen flex-col items-center justify-center p-4 sm:p-8">

                {/* Glassmorphic Card */}
                <div className="w-full max-w-xl animate-in fade-in slide-in-from-bottom-8 duration-1000">
                    <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-8 shadow-2xl backdrop-blur-xl sm:p-12">

                        {/* Inner Glow Gradient */}
                        <div className="pointer-events-none absolute -left-1/2 -top-1/2 h-full w-full bg-blue-500/10 blur-[100px]" />

                        <div className="relative z-20 flex flex-col items-center text-center">

                            {/* Header */}
                            <div className="mb-8 space-y-4">
                                <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl md:text-6xl drop-shadow-sm">
                                    Drawdown-Minimization <br />
                                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-200 to-indigo-400">
                                        Portfolio Optimizer
                                    </span>
                                </h1>
                                <p className="mx-auto max-w-md text-lg text-white/70 leading-relaxed">
                                    Advanced quantitative risk management engine built for institutional-grade portfolio construction and drawdown control.
                                </p>
                            </div>

                            {/* Feature Pills */}
                            <div className="mb-10 flex flex-wrap justify-center gap-3">
                                <FeaturePill icon={Activity} label="Live Market Data" />
                                <FeaturePill icon={ShieldCheck} label="CVaR Optimization" />
                                <FeaturePill icon={TrendingUp} label="Monte Carlo Simulation" />
                                <FeaturePill icon={Zap} label="Risk-Adjusted Returns" />
                            </div>

                            {/* CTA Button */}
                            <Link to="/login" className="group relative focus:outline-none focus:ring-2 focus:ring-blue-500/50 rounded-full">
                                <div className="absolute -inset-0.5 rounded-full bg-gradient-to-r from-blue-400 to-indigo-600 opacity-70 blur opacity-40 transition duration-200 group-hover:opacity-75"></div>
                                <button className="relative flex items-center gap-2 rounded-full bg-gradient-to-r from-blue-600 to-indigo-700 px-8 py-4 text-lg font-medium text-white shadow-lg transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]">
                                    Continue to Optimizer
                                    <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
                                </button>
                            </Link>

                        </div>
                    </div>

                    {/* Copyright / Footer minimal */}
                    <div className="mt-8 text-center text-xs text-white/30 font-light tracking-wider uppercase">
                        Institutional Risk Systems · v2.0
                    </div>

                </div>
            </div>
        </div>
    );
}

function FeaturePill({ icon: Icon, label }: { icon: any; label: string }) {
    return (
        <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-sm font-medium text-blue-100/90 backdrop-blur-sm transition-colors hover:bg-white/10 shadow-sm">
            <Icon className="h-4 w-4 text-blue-300" />
            <span>{label}</span>
        </div>
    );
}
