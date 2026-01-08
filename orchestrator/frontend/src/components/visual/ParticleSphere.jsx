import React, { useRef, useEffect } from 'react';

const ParticleSphere = ({ amplitude = 0, status = 'idle', theme = 'dark' }) => {
    const canvasRef = useRef(null);

    // Use refs to persist animation state across re-renders
    const stateRef = useRef({
        rotation: 0,
        currentExpansion: 1,
        targetExpansion: 1,
        currentSpeed: 0.002,
        targetSpeed: 0.002,
        colorHue: 180, // Cyan base
        particles: []
    });

    useEffect(() => {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        let animationFrameId;

        // Configuration
        const particleCount = 600; // Slightly reduced for performance with lines
        const baseRadius = 200; // Reduced from 250
        const connectionDistance = 40; // Max distance to draw line

        // Initialize particles ONLY ONCE if empty
        if (stateRef.current.particles.length === 0) {
            for (let i = 0; i < particleCount; i++) {
                const theta = Math.random() * 2 * Math.PI;
                const phi = Math.acos((Math.random() * 2) - 1);
                stateRef.current.particles.push({
                    x: baseRadius * Math.sin(phi) * Math.cos(theta),
                    y: baseRadius * Math.sin(phi) * Math.sin(theta),
                    z: baseRadius * Math.cos(phi),
                    // Random slight drift factors
                    vx: (Math.random() - 0.5) * 0.5,
                    vy: (Math.random() - 0.5) * 0.5,
                    vz: (Math.random() - 0.5) * 0.5,
                    colorType: Math.floor(Math.random() * 4) // 0: Blue, 1: Red, 2: Yellow, 3: Green
                });
            }
        }

        // Lerp Helper
        const lerp = (start, end, factor) => start + (end - start) * factor;

        // Google Colors
        const googleColors = [
            { r: 66, g: 133, b: 244 }, // Blue
            { r: 234, g: 67, b: 53 },  // Red
            { r: 251, g: 188, b: 5 },  // Yellow
            { r: 52, g: 168, b: 83 }   // Green
        ];

        const render = () => {
            // Resize canvas
            if (canvas.width !== canvas.parentElement.clientWidth || canvas.height !== canvas.parentElement.clientHeight) {
                canvas.width = canvas.parentElement.clientWidth;
                canvas.height = canvas.parentElement.clientHeight;
            }

            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // --- State Updates ---
            const s = stateRef.current;

            // Initialize smooth transition vars if missing
            if (s.currentMix === undefined) s.currentMix = 0;
            if (s.currentRadiusMult === undefined) s.currentRadiusMult = 1.5;

            // 1. Calculate Targets based on Props
            let targetExp = 1;
            let targetSpd = 0.002;
            let targetMix = 0; // 0 = Base Color, 1 = Google Colors
            let targetRadMult = 1.5;

            if (status === 'listening') {
                targetExp = 1.2 + (amplitude / 70); // React to voice
                targetExp = Math.min(targetExp, 2.2); // Cap Max Size
                targetSpd = 0.015;
                targetMix = 1;
                targetRadMult = 4.0;
            } else if (status === 'processing') {
                targetExp = 0.9;
                targetSpd = 0.04;
                targetMix = 0;
                targetRadMult = 1.5;
            } else {
                // Idle
                targetExp = 1 + Math.sin(Date.now() / 2000) * 0.05;
                targetMix = 0;
                targetRadMult = 1.5;
            }

            // 2. Smoothly Interpolate values
            s.currentExpansion = lerp(s.currentExpansion, targetExp, 0.05);
            s.currentSpeed = lerp(s.currentSpeed, targetSpd, 0.05);
            s.currentMix = lerp(s.currentMix, targetMix, 0.1); // Color mix speed
            s.currentRadiusMult = lerp(s.currentRadiusMult, targetRadMult, 0.1); // Radius change speed

            // Advance Rotation
            s.rotation += s.currentSpeed;

            // --- Rendering ---
            const projected = s.particles.map(p => {
                const rotX = p.x * Math.cos(s.rotation) - p.z * Math.sin(s.rotation);
                const rotZ = p.x * Math.sin(s.rotation) + p.z * Math.cos(s.rotation);
                const tilt = 0.2;
                const finalY = p.y * Math.cos(tilt) - rotZ * Math.sin(tilt);
                const finalZ = p.y * Math.sin(tilt) + rotZ * Math.cos(tilt);

                const expX = rotX * s.currentExpansion;
                const expY = finalY * s.currentExpansion;
                const expZ = finalZ * s.currentExpansion;

                const fov = 400;
                const scale = fov / (fov + expZ + baseRadius + 100);

                return {
                    x: expX * scale + centerX,
                    y: expY * scale + centerY,
                    z: expZ,
                    scale: scale,
                    colorType: p.colorType
                };
            });

            ctx.lineWidth = 0.5;

            let baseR, baseG, baseB;
            if (status === 'processing') { baseR = 167; baseG = 139; baseB = 250; } // Violet
            else { baseR = 34; baseG = 211; baseB = 238; } // Cyan
            if (theme !== 'dark' && status === 'idle') { baseR = 20; baseG = 30; baseB = 90; }

            projected.forEach((p, i) => {
                const alpha = Math.max(0.1, (p.scale - 0.5) * 2);

                // Mix Particle Color
                let targetR = baseR, targetG = baseG, targetB = baseB;

                // Get target color if mixing
                if (s.currentMix > 0.01) {
                    const c = googleColors[p.colorType];
                    // Lerp each channel towards Google color based on currentMix
                    targetR = lerp(baseR, c.r, s.currentMix);
                    targetG = lerp(baseG, c.g, s.currentMix);
                    targetB = lerp(baseB, c.b, s.currentMix);
                }

                // Draw Point
                ctx.beginPath();
                // Smooth radius transition
                const radius = s.currentRadiusMult * p.scale;

                ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(${Math.round(targetR)},${Math.round(targetG)},${Math.round(targetB)},${alpha})`;
                ctx.fill();

                // Draw Lines using the calculated mixed color
                for (let j = i + 1; j < particleCount; j++) {
                    const p2 = projected[j];
                    const dx = p.x - p2.x;
                    const dy = p.y - p2.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    if (dist < connectionDistance * s.currentExpansion) {
                        ctx.beginPath();
                        ctx.moveTo(p.x, p.y);
                        ctx.lineTo(p2.x, p2.y);
                        const lineAlpha = (1 - dist / (connectionDistance * s.currentExpansion)) * alpha * 0.5;
                        ctx.strokeStyle = `rgba(${Math.round(targetR)},${Math.round(targetG)},${Math.round(targetB)},${lineAlpha})`;
                        ctx.stroke();
                    }
                }
            });

            animationFrameId = requestAnimationFrame(render);
        };

        render();

        return () => cancelAnimationFrame(animationFrameId);
    }, [amplitude, status, theme]); // Re-run effect if basic props change, but stateRef keeps positions

    return <canvas ref={canvasRef} className="w-full h-full" />;
};

export default ParticleSphere;
