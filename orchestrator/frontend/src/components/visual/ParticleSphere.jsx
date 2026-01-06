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
                });
            }
        }

        // Lerp Helper
        const lerp = (start, end, factor) => start + (end - start) * factor;

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

            // 1. Calculate Targets based on Props
            let targetExp = 1;
            let targetSpd = 0.002;
            let targetHue = theme === 'dark' ? 180 : 220; // Cyan vs Blue

            if (status === 'listening') {
                targetExp = 1.2 + (amplitude / 50); // React to voice
                targetSpd = 0.015;
                targetHue = 180; // Cyan
            } else if (status === 'processing') {
                targetExp = 0.9; // Contract slightly
                targetSpd = 0.04;
                targetHue = 260; // Violet
            } else {
                // Idle
                targetExp = 1 + Math.sin(Date.now() / 2000) * 0.05; // Breathing
            }

            // 2. Smoothly Interpolate values
            s.currentExpansion = lerp(s.currentExpansion, targetExp, 0.05);
            s.currentSpeed = lerp(s.currentSpeed, targetSpd, 0.05);

            // Advance Rotation
            s.rotation += s.currentSpeed;

            // --- Rendering ---

            // Project particles first to sort or just draw
            // We need 3D coordinates after rotation to check distances for lines
            const projected = s.particles.map(p => {
                // Rotate around Y axis
                const rotX = p.x * Math.cos(s.rotation) - p.z * Math.sin(s.rotation);
                const rotZ = p.x * Math.sin(s.rotation) + p.z * Math.cos(s.rotation);

                // Rotate around X axis (tilt)
                const tilt = 0.2;
                const finalY = p.y * Math.cos(tilt) - rotZ * Math.sin(tilt);
                const finalZ = p.y * Math.sin(tilt) + rotZ * Math.cos(tilt);

                // Apply Expansion
                const expX = rotX * s.currentExpansion;
                const expY = finalY * s.currentExpansion;
                const expZ = finalZ * s.currentExpansion;

                // 3D Projection
                const fov = 400; // Field of view
                const scale = fov / (fov + expZ + baseRadius + 100);

                return {
                    x: expX * scale + centerX,
                    y: expY * scale + centerY,
                    z: expZ, // Keep Z for depth sorting/opacity
                    scale: scale
                };
            });

            // Draw Connections (Plexus Effect) - Only for close particles
            // To save performance, we only check a subset or purely based on 2D proximity? 
            // 2D proximity is faster and looks fine.

            ctx.lineWidth = 0.5;

            // Optimization: Only draw lines if we are somewhat expanded or active, 
            // or just always draw them but fade them out.

            // Set Color
            let r, g, b;
            if (status === 'processing') { r = 167; g = 139; b = 250; } // Violet
            else { r = 34; g = 211; b = 238; } // Cyan

            // Light mode override
            if (theme !== 'dark' && status === 'idle') { r = 20; g = 30; b = 90; }

            // Draw Particles & Lines
            projected.forEach((p, i) => {
                // Opacity based on Z (depth)
                const alpha = Math.max(0.1, (p.scale - 0.5) * 2);

                // Draw Point
                ctx.beginPath();
                ctx.arc(p.x, p.y, 1.5 * p.scale, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(${r},${g},${b},${alpha})`;
                ctx.fill();

                // Draw Lines (The "3D Model" feel)
                // Check neighbors. Simple optimization: only check next few particles? 
                // No, that creates artifacts. Random check or spatial grid is best.
                // For 600 particles, O(N^2) is 360,000 checks. Too slow for JS canvas 60fps? 
                // Let's rely on random sampling or just checking indices nearby in the original array (since they are generated spherically).

                // Better optimization: Only draw lines to particles that are physically close in the list 
                // (Since we generated them roughly in order, this isn't perfect but faster).
                // Or just brute force it but limit the inner loop range.

                for (let j = i + 1; j < particleCount; j++) {
                    const p2 = projected[j];
                    const dx = p.x - p2.x;
                    const dy = p.y - p2.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    if (dist < connectionDistance * s.currentExpansion) {
                        ctx.beginPath();
                        ctx.moveTo(p.x, p.y);
                        ctx.lineTo(p2.x, p2.y);
                        // Line alpha based on distance
                        const lineAlpha = (1 - dist / (connectionDistance * s.currentExpansion)) * alpha * 0.5;
                        ctx.strokeStyle = `rgba(${r},${g},${b},${lineAlpha})`;
                        ctx.stroke();
                    }

                    // Limit connections per particle to avoid hairball
                    // if (j > i + 10) break; // This would look weird.
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
