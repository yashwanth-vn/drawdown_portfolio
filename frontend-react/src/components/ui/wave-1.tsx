"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";

interface WaveShaderProps {
    className?: string;
}

export function WaveShader({ className }: WaveShaderProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        let animationFrameId: number;
        let time = 0;

        const resize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };

        window.addEventListener("resize", resize);
        resize();

        const draw = () => {
            time += 0.01;
            const { width, height } = canvas;
            ctx.clearRect(0, 0, width, height);

            const amplitude = 50;
            const frequency = 0.01;
            const yOffset = height / 2;

            ctx.beginPath();
            ctx.moveTo(0, height);
            ctx.lineTo(0, yOffset + Math.sin(time) * amplitude);

            for (let x = 0; x <= width; x += 10) {
                const y =
                    yOffset +
                    Math.sin(x * frequency + time) * amplitude +
                    Math.sin(x * frequency * 2 + time * 0.5) * (amplitude / 2);
                ctx.lineTo(x, y);
            }

            ctx.lineTo(width, height);
            ctx.fillStyle = "rgba(255, 255, 255, 0.03)";
            ctx.fill();

            // Second wave
            ctx.beginPath();
            ctx.moveTo(0, height);
            for (let x = 0; x <= width; x += 10) {
                const y =
                    yOffset +
                    Math.sin(x * frequency + time + 2) * (amplitude * 0.8) +
                    Math.sin(x * frequency * 1.5 + time * 0.7) * (amplitude * 0.4);
                ctx.lineTo(x, y);
            }
            ctx.lineTo(width, height);
            ctx.fillStyle = "rgba(4, 169, 213, 0.05)"; // Subtle blue
            ctx.fill();

            animationFrameId = requestAnimationFrame(draw);
        };

        draw();

        return () => {
            window.removeEventListener("resize", resize);
            cancelAnimationFrame(animationFrameId);
        };
    }, []);

    return <canvas ref={canvasRef} className={cn("block", className)} />;
}

export default WaveShader;
