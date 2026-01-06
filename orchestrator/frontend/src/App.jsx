import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Mic, Send, Command, Cpu, Hexagon, Activity, Settings, Sun, Moon, StopCircle, User, Bot, Sparkles } from 'lucide-react'
import { Button } from "@/components/ui/button"
import ParticleSphere from "@/components/visual/ParticleSphere"
import './index.css'

function App() {
    const [theme, setTheme] = useState('dark')
    const [status, setStatus] = useState('idle')
    const [statusText, setStatusText] = useState('System Ready')
    const [messages, setMessages] = useState([])
    const [inputText, setInputText] = useState('')
    const [voiceLevel, setVoiceLevel] = useState(0)
    const ws = useRef(null)
    const messagesEndRef = useRef(null)

    useEffect(() => {
        document.documentElement.classList.remove('light', 'dark')
        document.documentElement.classList.add(theme)
    }, [theme])

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    useEffect(() => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.port === '5173' ? 'localhost:8000' : window.location.host;
        const wsUrl = `${protocol}//${host}/ws`;

        ws.current = new WebSocket(wsUrl)
        ws.current.onopen = () => setStatusText('Connected')

        ws.current.onmessage = (event) => {
            const data = JSON.parse(event.data)
            if (data.type === 'state') {
                setStatus(data.state)
                setStatusText(data.message)
            } else if (data.type === 'log') {
                if (data.source === 'user') {
                    setMessages(prev => [...prev, { text: data.message.replace('User said: ', ''), sender: 'user', time: new Date().toLocaleTimeString() }])
                } else if (data.source === 'system') {
                    setMessages(prev => [...prev, { text: data.message, sender: 'system', time: new Date().toLocaleTimeString() }])
                } else if (data.source === 'error') {
                    setMessages(prev => [...prev, { text: data.message, sender: 'error', time: new Date().toLocaleTimeString() }])
                }
            } else if (data.type === 'volume') {
                setVoiceLevel(Math.min(data.level * 25, 150));
            }
        }
        return () => { if (ws.current) ws.current.close() }
    }, [])

    const handleMicClick = () => {
        status === 'listening' ? ws.current.send('stop_listening') : ws.current.send('start_listening')
    }

    const handleSendText = (e) => {
        e.preventDefault()
        if (!inputText.trim()) return;
        ws.current.send(`text_command:${inputText}`)
        setInputText('')
    }

    const toggleTheme = () => setTheme(prev => prev === 'dark' ? 'light' : 'dark')

    return (
        <div className={`flex h-screen overflow-hidden font-sans transition-colors duration-500 ${theme === 'dark' ? 'bg-[#0B0F1A] text-gray-100' : 'bg-slate-50 text-slate-800'}`}>

            {/* LEFT: MAIN AI VISUALIZER (65%) */}
            <section className="flex-1 flex flex-col relative overflow-hidden">
                {/* Header */}
                <header className="absolute top-0 left-0 w-full p-8 z-20 flex justify-between items-start">
                    <div className="flex items-center gap-4">
                        <div className={`p-2 rounded-xl backdrop-blur-sm border ${theme === 'dark' ? 'bg-cyan-500/10 border-cyan-500/30' : 'bg-indigo-500/10 border-indigo-500/20'}`}>
                            <Hexagon className={`h-6 w-6 ${theme === 'dark' ? 'text-cyan-400' : 'text-indigo-600'}`} />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold tracking-widest uppercase flex items-center gap-2">
                                AI <span className={`${theme === 'dark' ? 'text-cyan-400' : 'text-indigo-600'}`}>ASSISTANT</span>
                            </h1>
                            <div className="flex items-center gap-2 mt-1">
                                <div className={`w-2 h-2 rounded-full shadow-[0_0_8px_currentColor] ${status === 'listening' ? 'bg-cyan-400 text-cyan-400 animate-pulse' : 'bg-emerald-500 text-emerald-500'}`} />
                                <span className={`text-[10px] font-mono uppercase tracking-widest ${theme === 'dark' ? 'text-gray-500' : 'text-slate-400'}`}>
                                    {statusText}
                                </span>
                            </div>
                        </div>
                    </div>
                </header>

                {/* THE ORB */}
                <div className="flex-1 flex items-center justify-center relative z-10">
                    <div className="w-full h-full max-w-5xl max-h-[85vh]">
                        <ParticleSphere amplitude={voiceLevel} status={status} theme={theme} />
                    </div>

                    {/* Status Text - Centered & Glowing */}
                    <div className="absolute bottom-24 text-center pointer-events-none z-20">
                        <AnimatePresence mode="wait">
                            <motion.h2
                                key={status}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                className={`text-3xl font-light tracking-[0.2em] uppercase ${status === 'listening'
                                    ? 'text-cyan-400 drop-shadow-[0_0_15px_rgba(34,211,238,0.8)]'
                                    : status === 'processing'
                                        ? 'text-violet-400 drop-shadow-[0_0_15px_rgba(167,139,250,0.8)]'
                                        : theme === 'dark' ? 'text-gray-600' : 'text-slate-300'
                                    }`}
                            >
                                {status === 'listening' ? "Listening..." : status === 'processing' ? "Processing..." : "Awaiting Command"}
                            </motion.h2>
                        </AnimatePresence>
                    </div>
                </div>
            </section>

            {/* RIGHT: DASHBOARD PANEL (35% - Fixed Width) */}
            <aside className={`w-[450px] flex flex-col relative z-30 border-l backdrop-blur-2xl transition-all duration-300 ${theme === 'dark'
                ? 'bg-[#0E1220]/80 border-white/5 shadow-[-20px_0_40px_rgba(0,0,0,0.3)]'
                : 'bg-white/60 border-indigo-100 shadow-[-10px_0_30px_rgba(0,0,0,0.05)]'
                }`}>

                {/* Top Tools */}
                <div className="p-6 flex justify-end items-center gap-3 border-b border-white/5">
                    <Button variant="ghost" size="icon" onClick={toggleTheme} className="rounded-full hover:bg-white/5">
                        {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
                    </Button>
                    <Button variant="ghost" size="icon" className="rounded-full hover:bg-white/5">
                        <Settings size={18} />
                    </Button>
                </div>

                {/* System Stats Card */}
                <div className="px-6 pt-4 pb-2">
                    <div className={`p-5 rounded-2xl border ${theme === 'dark'
                        ? 'bg-gradient-to-br from-white/5 to-transparent border-white/10'
                        : 'bg-white border-indigo-50 shadow-sm'
                        }`}>
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-xs font-bold uppercase tracking-wider opacity-70 flex items-center gap-2">
                                <Activity size={14} /> System Status
                            </h3>
                            <span className="text-[10px] font-mono opacity-50">ONLINE</span>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <div className="text-[10px] uppercase opacity-50 mb-1">Memory</div>
                                <div className="h-1.5 w-full bg-gray-700/30 rounded-full overflow-hidden">
                                    <div className="h-full bg-cyan-500 w-[45%]" />
                                </div>
                            </div>
                            <div>
                                <div className="text-[10px] uppercase opacity-50 mb-1">CPU Load</div>
                                <div className="h-1.5 w-full bg-gray-700/30 rounded-full overflow-hidden">
                                    <div className="h-full bg-violet-500 w-[12%]" />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Chat History */}
                <div className="flex-1 overflow-y-auto px-6 py-4 space-y-5 scrollbar-thin">
                    <AnimatePresence>
                        {messages.length === 0 && (
                            <div className="h-full flex flex-col items-center justify-center opacity-30 gap-4">
                                <Sparkles size={40} strokeWidth={1} />
                                <div className="text-sm font-light tracking-wide">SYSTEM READY</div>
                            </div>
                        )}
                        {messages.map((msg, idx) => (
                            <motion.div
                                key={idx}
                                initial={{ opacity: 0, x: 20, scale: 0.95 }}
                                animate={{ opacity: 1, x: 0, scale: 1 }}
                                className={`flex flex-col gap-1 ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
                            >
                                <span className="text-[10px] opacity-40 uppercase tracking-wider font-mono px-1">
                                    {msg.sender === 'user' ? 'USER' : 'AI'} • {msg.time}
                                </span>
                                <div className={`px-5 py-3.5 rounded-2xl text-sm leading-relaxed max-w-[90%] shadow-lg backdrop-blur-md border ${msg.sender === 'user'
                                    ? theme === 'dark'
                                        ? 'bg-cyan-500/10 border-cyan-500/20 text-cyan-50 rounded-tr-sm'
                                        : 'bg-indigo-600 text-white rounded-tr-sm shadow-indigo-200'
                                    : theme === 'dark'
                                        ? 'bg-white/5 border-white/10 text-gray-300 rounded-tl-sm'
                                        : 'bg-white border-slate-100 text-slate-700 rounded-tl-sm shadow-sm'
                                    }`}>
                                    {msg.text}
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                    <div ref={messagesEndRef} />
                </div>

                {/* Floating Command Bar */}
                <div className="p-6 relative">
                    <div className={`relative flex items-center p-1.5 rounded-full border shadow-2xl transition-all ${theme === 'dark'
                        ? 'bg-[#131726] border-white/10 focus-within:border-cyan-500/50 focus-within:shadow-[0_0_20px_rgba(34,211,238,0.2)]'
                        : 'bg-white border-slate-200 focus-within:border-indigo-400 focus-within:shadow-xl'
                        }`}>

                        {/* Mic Button with Pulse Ring */}
                        <div className="relative">
                            {status === 'listening' && (
                                <span className={`absolute inset-0 rounded-full animate-ping opacity-75 ${theme === 'dark' ? 'bg-cyan-500' : 'bg-indigo-500'}`} />
                            )}
                            <Button
                                size="icon"
                                className={`rounded-full relative z-10 transition-colors ${status === 'listening'
                                    ? 'bg-red-500 hover:bg-red-600 text-white'
                                    : theme === 'dark' ? 'bg-white/5 hover:bg-white/10 text-gray-400' : 'bg-slate-100 hover:bg-slate-200 text-slate-600'
                                    }`}
                                onClick={handleMicClick}
                            >
                                {status === 'listening' ? <StopCircle size={18} /> : <Mic size={18} />}
                            </Button>
                        </div>

                        <form onSubmit={handleSendText} className="flex-1 px-4">
                            <input
                                type="text"
                                placeholder="Ask or command anything..."
                                className="w-full bg-transparent border-none outline-none text-sm font-medium placeholder:opacity-40 h-full"
                                value={inputText}
                                onChange={(e) => setInputText(e.target.value)}
                            />
                        </form>

                        <Button
                            size="icon"
                            disabled={!inputText.trim()}
                            className={`rounded-full transition-all duration-300 ${inputText.trim()
                                ? theme === 'dark' ? 'bg-cyan-500 hover:bg-cyan-400 text-cyan-950' : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                                : 'opacity-0 scale-90 pointer-events-none'
                                }`}
                            onClick={handleSendText}
                        >
                            <Send size={16} />
                        </Button>
                    </div>
                </div>
            </aside>
        </div>
    )
}

export default App
