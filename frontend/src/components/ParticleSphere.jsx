import React, { useRef, useEffect } from 'react';

const ParticleSphere = ({ state }) => {
    const canvasRef = useRef(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        let animationFrameId;

        // Configuration
        const particleCount = 400;
        const particles = [];
        let r = 120; // Radius
        let baseSpeed = 0.005;

        // Resize
        const resize = () => {
            canvas.width = canvas.parentElement.clientWidth;
            canvas.height = canvas.parentElement.clientHeight;
        };
        window.addEventListener('resize', resize);
        resize();

        // Init Particles
        for (let i = 0; i < particleCount; i++) {
            const theta = Math.acos(-1 + (2 * i) / particleCount);
            const phi = Math.sqrt(particleCount * Math.PI) * theta;
            particles.push({
                theta,
                phi,
                x: 0,
                y: 0,
                z: 0,
                baseR: r,
                vary: Math.random() * 20
            });
        }

        let angleX = 0;
        let angleY = 0;

        const render = () => {
            // State Logic
            let rotationSpeed = baseSpeed;
            let color = '100, 150, 255'; // Blue default
            let pulseIntensity = 0;

            if (state === 'listening') {
                rotationSpeed = 0.02;
                color = '50, 255, 150'; // Greenish Cyan
                pulseIntensity = 10;
            } else if (state === 'processing') {
                rotationSpeed = 0.04;
                color = '200, 100, 255'; // Purple
            } else if (state === 'speaking') {
                rotationSpeed = 0.01;
                color = '100, 200, 255';
                pulseIntensity = 15 * Math.sin(Date.now() / 100); // Pulse effect
            }

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            const cx = canvas.width / 2;
            const cy = canvas.height / 2;

            angleX += rotationSpeed;
            angleY += rotationSpeed * 0.5;

            // Sort particles by Z for depth
            particles.sort((a, b) => b.z - a.z);

            const time = Date.now() / 500;

            particles.forEach(p => {
                // Calculate 3D position
                let currentR = p.baseR + pulseIntensity;

                // Wiggle effect for speaking/processing
                if (state === 'speaking' || state === 'processing') {
                    currentR += Math.sin(time + p.theta * 10) * 5;
                }

                const pX = currentR * Math.sin(p.theta) * Math.cos(p.phi + angleX);
                const pY = currentR * Math.sin(p.theta) * Math.sin(p.phi + angleX);
                const pZ = currentR * Math.cos(p.theta);

                // Rotate around Y
                const x = pX * Math.cos(angleY) - pZ * Math.sin(angleY);
                const z = pX * Math.sin(angleY) + pZ * Math.cos(angleY);

                // Perspective Projection
                const scale = 300 / (300 + z);
                const alpha = Math.max(0.1, (scale - 0.5) * 1.5); // Fade back particles

                ctx.beginPath();
                ctx.arc(cx + x * scale, cy + pY * scale, 2 * scale, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(${color}, ${alpha})`;
                ctx.fill();

                // Store z for sorting
                p.z = z;
            });

            animationFrameId = requestAnimationFrame(render);
        };

        render();

        return () => {
            window.removeEventListener('resize', resize);
            cancelAnimationFrame(animationFrameId);
        };
    }, [state]);

    return <canvas ref={canvasRef} className="w-full h-full" />;
};

export default ParticleSphere;
