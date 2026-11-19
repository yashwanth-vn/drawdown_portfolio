"use client";

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { AuthManager } from "@/services/auth";

function FloatingPaths({ position }: { position: number }) {
    const paths = Array.from({ length: 36 }, (_, i) => ({
        id: i,
        d: `M-${380 - i * 5 * position} -${189 + i * 6}C-${380 - i * 5 * position
            } -${189 + i * 6} -${312 - i * 5 * position} ${216 - i * 6} ${152 - i * 5 * position
            } ${343 - i * 6}C${616 - i * 5 * position} ${470 - i * 6} ${684 - i * 5 * position
            } ${875 - i * 6} ${684 - i * 5 * position} ${875 - i * 6}`,
        color: `rgba(15,23,42,${0.1 + i * 0.03})`,
        width: 0.5 + i * 0.03,
    }));

    return (
        <div className="absolute inset-0 pointer-events-none">
            <svg
                className="w-full h-full text-slate-950 dark:text-white"
                viewBox="0 0 696 316"
                fill="none"
            >
                <title>Background Paths</title>
                {paths.map((path) => (
                    <motion.path
                        key={path.id}
                        d={path.d}
                        stroke="currentColor"
                        strokeWidth={path.width}
                        strokeOpacity={0.1 + path.id * 0.03}
                        initial={{ pathLength: 0.3, opacity: 0.6 }}
                        animate={{
                            pathLength: 1,
                            opacity: [0.3, 0.6, 0.3],
                            pathOffset: [0, 1, 0],
                        }}
                        transition={{
                            duration: 20 + Math.random() * 10,
                            repeat: Number.POSITIVE_INFINITY,
                            ease: "linear",
                        }}
                    />
                ))}
            </svg>
        </div>
    );
}

export function Login() {
    const navigate = useNavigate();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    const title = "Portfolio Optimizer";
    const words = title.split(" ");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setIsLoading(true);

        const result = await AuthManager.login(email, password);

        if (result.status === "success") {
            navigate("/dashboard");
        } else {
            setError(result.message || "Login failed");
        }

        setIsLoading(false);
    };

    return (
        <div className="relative min-h-screen w-full flex items-center justify-center overflow-hidden bg-white dark:bg-neutral-950">
            {/* Animated Background Paths */}
            <div className="absolute inset-0">
                <FloatingPaths position={1} />
                <FloatingPaths position={-1} />
            </div>

            {/* Main Content */}
            <div className="relative z-10 container mx-auto px-4 md:px-6 text-center">
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 2 }}
                    className="max-w-md mx-auto"
                >
                    {/* Animated Title */}
                    <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold mb-8 tracking-tighter">
                        {words.map((word, wordIndex) => (
                            <span
                                key={wordIndex}
                                className="inline-block mr-3 last:mr-0"
                            >
                                {word.split("").map((letter, letterIndex) => (
                                    <motion.span
                                        key={`${wordIndex}-${letterIndex}`}
                                        initial={{ y: 100, opacity: 0 }}
                                        animate={{ y: 0, opacity: 1 }}
                                        transition={{
                                            delay:
                                                wordIndex * 0.1 +
                                                letterIndex * 0.03,
                                            type: "spring",
                                            stiffness: 150,
                                            damping: 25,
                                        }}
                                        className="inline-block text-transparent bg-clip-text 
                                        bg-gradient-to-r from-neutral-900 to-neutral-700/80 
                                        dark:from-white dark:to-white/80"
                                    >
                                        {letter}
                                    </motion.span>
                                ))}
                            </span>
                        ))}
                    </h1>

                    {/* Login Card */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.8, duration: 0.5 }}
                        className="bg-white/95 dark:bg-black/95 backdrop-blur-lg rounded-2xl p-8 
                        border border-black/10 dark:border-white/10 shadow-xl"
                    >
                        <div className="text-left mb-6">
                            <h2 className="text-xl font-semibold text-neutral-900 dark:text-white">
                                Welcome Back
                            </h2>
                            <p className="text-neutral-600 dark:text-neutral-400 text-sm mt-1">
                                Sign in to access the portfolio dashboard
                            </p>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-4 text-left">
                            <div>
                                <label
                                    htmlFor="email"
                                    className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1.5"
                                >
                                    Email Address
                                </label>
                                <input
                                    type="email"
                                    id="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="name@company.com"
                                    required
                                    className="w-full px-4 py-3 rounded-xl bg-neutral-100 dark:bg-neutral-900 
                                    border border-neutral-200 dark:border-neutral-800 
                                    text-neutral-900 dark:text-white placeholder:text-neutral-500
                                    focus:outline-none focus:ring-2 focus:ring-neutral-400 dark:focus:ring-neutral-600
                                    transition-all"
                                />
                            </div>

                            <div>
                                <label
                                    htmlFor="password"
                                    className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1.5"
                                >
                                    Password
                                </label>
                                <input
                                    type="password"
                                    id="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="••••••••"
                                    required
                                    className="w-full px-4 py-3 rounded-xl bg-neutral-100 dark:bg-neutral-900 
                                    border border-neutral-200 dark:border-neutral-800 
                                    text-neutral-900 dark:text-white placeholder:text-neutral-500
                                    focus:outline-none focus:ring-2 focus:ring-neutral-400 dark:focus:ring-neutral-600
                                    transition-all"
                                />
                            </div>

                            {error && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: "auto" }}
                                    className="text-red-500 text-sm text-center py-2"
                                >
                                    {error}
                                </motion.div>
                            )}

                            <Button
                                type="submit"
                                disabled={isLoading}
                                className="w-full rounded-xl py-6 text-base font-semibold 
                                bg-neutral-900 hover:bg-neutral-800 dark:bg-white dark:hover:bg-neutral-100
                                text-white dark:text-black transition-all duration-300"
                            >
                                {isLoading ? "Signing in..." : "Sign In"}
                                <span className="ml-2">→</span>
                            </Button>
                        </form>

                        {/* Demo Credentials */}
                        <div className="mt-6 pt-6 border-t border-neutral-200 dark:border-neutral-800">
                            <p className="text-xs text-neutral-500 mb-2">Demo Credentials:</p>
                            <div className="space-y-1 text-xs text-neutral-600 dark:text-neutral-400">
                                <div className="flex justify-between">
                                    <span>Admin:</span>
                                    <code className="bg-neutral-100 dark:bg-neutral-900 px-2 py-0.5 rounded">
                                        user@finance.com / password123
                                    </code>
                                </div>
                                <div className="flex justify-between">
                                    <span>Analyst:</span>
                                    <code className="bg-neutral-100 dark:bg-neutral-900 px-2 py-0.5 rounded">
                                        analyst@finance.com / password123
                                    </code>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </motion.div>
            </div>
        </div>
    );
}
