import React from 'react';
import { motion } from 'framer-motion';

const GoogleDots = ({ state }) => {
    const colors = ["#4285F4", "#DB4437", "#F4B400", "#0F9D58"]; // Blue, Red, Yellow, Green

    const containerVariants = {
        idle: {
            transition: { staggerChildren: 0.2 }
        },
        listening: {
            transition: { staggerChildren: 0.1 }
        },
        processing: {
            rotate: 360,
            transition: { duration: 1, repeat: Infinity, ease: "linear" }
        },
        speaking: {
            transition: { staggerChildren: 0.1 }
        }
    };

    const dotVariants = {
        idle: {
            y: [0, -5, 0],
            scale: 1,
            opacity: 0.8,
            transition: { duration: 1.5, repeat: Infinity, ease: "easeInOut" }
        },
        listening: {
            y: [0, -15, 0],
            scale: 1.2,
            opacity: 1,
            transition: { duration: 0.6, repeat: Infinity, ease: "easeInOut" }
        },
        processing: {
            scale: [1, 0.8, 1],
            transition: { duration: 0.5, repeat: Infinity } // Rotating in container
        },
        speaking: {
            y: [0, -30, 0], // Higher bounce for speaking
            scale: 1,
            transition: { duration: 0.5, repeat: Infinity, ease: "easeOut" }
        }
    };

    return (
        <div className="flex items-center justify-center p-10 mt-10">
            <motion.div
                className="flex space-x-6"
                variants={containerVariants}
                animate={state === 'speaking' || state === 'processing' ? state : 'idle'}
            >
                {/* If we are just listening/idle, we treat dots individually but mapped */}
                {/* Handling explicit states for easier control */}

                {colors.map((color, i) => (
                    <motion.div
                        key={i}
                        className="w-8 h-8 rounded-full shadow-lg"
                        style={{ backgroundColor: color }}
                        variants={dotVariants}
                        animate={state}
                        // Add slight delay offset for wave effect in speaking/listening
                        transition={{
                            delay: i * 0.1,
                            repeat: Infinity,
                            duration: state === 'speaking' ? 0.6 : (state === 'listening' ? 0.8 : 1.5)
                        }}
                    />
                ))}
            </motion.div>
        </div>
    );
};

export default GoogleDots;
