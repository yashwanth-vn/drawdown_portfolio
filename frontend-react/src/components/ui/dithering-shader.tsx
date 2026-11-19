"use client";

import { cn } from "@/lib/utils";

interface DitheringShaderProps {
    className?: string;
    opacity?: number;
}

export function DitheringShader({
    className,
    opacity = 0.1,
}: DitheringShaderProps) {
    // Simulating a dithering noise effect using strictly CSS/SVG patterns for performance
    // This matches the "fintech" gritty texture look.

    return (
        <div
            className={cn("pointer-events-none absolute inset-0 z-0", className)}
            style={{ opacity }}
        >
            <svg
                className="h-full w-full opacity-[0.6]"
                xmlns="http://www.w3.org/2000/svg"
            >
                <filter id="noiseFilter">
                    <feTurbulence
                        type="fractalNoise"
                        baseFrequency="0.8"
                        numOctaves="3"
                        stitchTiles="stitch"
                    />
                </filter>
                <rect width="100%" height="100%" filter="url(#noiseFilter)" />
            </svg>
            {/* Overlay gradient to soften the noise */}
            <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent" />
        </div>
    );
}

export default DitheringShader;
