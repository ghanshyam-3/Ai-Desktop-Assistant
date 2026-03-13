import React, { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';
import ParticleSphere from './components/ParticleSphere';
import Dashboard from './components/Dashboard';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff, Send, Menu, Clock, Home, Settings, Box, PlusCircle, Search, MessageSquare, ListTodo, Mail } from 'lucide-react';
import EmailContacts from './pages/EmailContacts';

const socket = io('http://localhost:8000');

function App() {
  const [status, setStatus] = useState('idle');
  const [isMicActive, setIsMicActive] = useState(true);
  const [view, setView] = useState('home'); // 'home' | 'dashboard'
  const [messages, setMessages] = useState([
    { role: 'ai', message: "Hello! I am your AI Assistant. How can I help you?" }
  ]);
  const [tasks, setTasks] = useState([]);
  const [notes, setNotes] = useState([]);
  const [plans, setPlans] = useState([]);
  const [inputText, setInputText] = useState("");
  const messagesEndRef = useRef(null);

  useEffect(() => {
    socket.on('connect', () => {
      console.log('Connected');
      socket.emit('fetch_dashboard');
    });

    socket.on('status', (data) => {
      if (data.state) setStatus(data.state);
    });

    socket.on('chat', (data) => {
      setMessages(prev => [...prev, data]);
    });

    socket.on('dashboard_update', (data) => {
      console.log("Dashboard Update:", data);
      if (data.tasks) setTasks(data.tasks);
      if (data.notes) setNotes(data.notes);
      if (data.plans) setPlans(data.plans);
    });

    socket.on('navigate', (viewName) => {
      console.log("Navigating to:", viewName);
      setView(viewName);
    });

    return () => {
      socket.off('connect');
      socket.off('status');
      socket.off('chat');
      socket.off('dashboard_update');
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleManualAdd = (type, content, date) => {
    socket.emit('add_item_manual', { type, content, date });
  };

  const handleUpdate = (type, id, updates) => {
    socket.emit('update_item', { type, id, updates });
  };

  return (
    <div className="flex h-screen w-full bg-gradient-to-br from-[#f8fafc] via-[#f1f5f9] to-[#e2e8f0] text-slate-800 font-sans overflow-hidden p-2 gap-2">
      {/* Sidebar - Floating Glass Panel */}
      <div className="w-64 glass rounded-2xl flex flex-col p-6 shadow-2xl shadow-blue-900/5 z-20">
        <div className="mb-10 flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-tr from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center text-white font-bold shadow-lg shadow-blue-600/30">
            <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6 stroke-current" strokeWidth="2.5">
              <path d="M12 2a10 10 0 0 1 10 10c0 5.523-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2z" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M12 6v6l4 2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-slate-900 leading-tight">Nova AI</h1>
            <span className="text-xs text-blue-600 font-medium tracking-wide">PRO ASSISTANT</span>
          </div>
        </div>

        <Button
          variant="outline"
          className="w-full justify-start mb-6 shadow-sm h-12 text-slate-600 border-slate-200 hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50/50 transition-all rounded-xl"
          onClick={() => setView('home')} // Reset to chat
        >
          <MessageSquare size={18} className="mr-3 text-blue-500" />
          Chat Now
        </Button>

        <div className="space-y-1">
          <SectionHeader title="Workspace" />
          <NavItem
            icon={<Home size={18} />}
            label="Dashboard"
            active={view === 'dashboard'}
            onClick={() => setView('dashboard')}
          />
          <NavItem
            icon={<MessageSquare size={18} />}
            label="Chat"
            active={view === 'home'}
            onClick={() => setView('home')}
          />
          <NavItem
            icon={<Mail size={18} />}
            label="Email Contacts"
            active={view === 'email_contacts'}
            onClick={() => setView('email_contacts')}
          />
        </div>

        <div className="mt-8 flex-1 overflow-y-auto scrollbar-hide">
          <SectionHeader title="Capabilities" />
          <div className="space-y-2 text-sm text-slate-500 px-2 mt-2">
            <CapabilityItem label="System Control" />
            <CapabilityItem label="Email Automation" />
            <CapabilityItem label="Web Browsing" />
            <CapabilityItem label="App Launching" />
          </div>
        </div>
      </div>

      {/* Main Content - Canvas */}
      <div className="flex-1 flex flex-col relative rounded-2xl glass shadow-2xl shadow-blue-900/5 overflow-hidden">

        {/* Top Header */}
        <div className="h-20 flex items-center justify-between px-8 z-20">
          <div className="flex items-center space-x-2 text-slate-400 text-sm font-medium">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
            <span>{view === 'dashboard' ? 'Dashboard View' : view === 'email_contacts' ? 'Email Contacts' : 'System Online'}</span>
          </div>

          <div className="flex items-center space-x-6">
            {/* Mic Toggle (Integrated into Header) */}
            <Button
              size="sm"
              variant={isMicActive ? "secondary" : "destructive"}
              className={`h-9 px-4 rounded-full flex items-center space-x-2 transition-all duration-300 ${isMicActive ? 'bg-blue-50 text-blue-600 hover:bg-blue-100' : 'bg-red-50 text-red-600 hover:bg-red-100'}`}
              onClick={() => {
                const newState = !isMicActive;
                setIsMicActive(newState);
                socket.emit('toggle_listening', { active: newState });
              }}
            >
              {isMicActive ? <Mic size={16} /> : <MicOff size={16} />}
              <span className="text-xs font-semibold uppercase tracking-wide">{isMicActive ? "Active" : "Muted"}</span>
            </Button>

            {/* Dashboard Link Button */}
            <Button
              size="sm"
              variant="ghost"
              className="h-9 px-3 rounded-full flex items-center space-x-2 text-slate-500 hover:bg-white hover:text-blue-600 hover:shadow-sm transition-all"
              onClick={() => setView('dashboard')}
            >
              <ListTodo size={18} />
              <span className="text-xs font-semibold uppercase tracking-wide">Tasks</span>
            </Button>

            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-slate-200 to-white overflow-hidden ring-2 ring-white shadow-md cursor-pointer hover:ring-blue-100 transition-all">
              <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix" alt="User" />
            </div>
          </div>
        </div>

        {/* VIEW SWITCHER */}
        {view === 'dashboard' ? (
          <Dashboard
            tasks={tasks}
            notes={notes}
            plans={plans}
            onAdd={handleManualAdd}
            onUpdate={handleUpdate}
            onTypingStart={() => socket.emit('start_typing')}
            onTypingStop={() => socket.emit('stop_typing')}
          />
        ) : view === 'email_contacts' ? (
          <EmailContacts />
        ) : (
          <>
            {/* Center Canvas (Visualizer) */}
            <div className="flex-1 flex flex-col items-center justify-center relative overflow-hidden pb-24">
              {/* ... Chat Overlay ... */}
              <div className="absolute top-4 w-full px-20 flex flex-col items-center space-y-4 pointer-events-none z-10">
                <AnimatePresence mode='popLayout'>
                  {messages.slice(-2).map((msg, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 20, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                      className={`px-8 py-5 rounded-3xl max-w-2xl shadow-xl backdrop-blur-md border border-white/50
                                    ${msg.role === 'user'
                          ? 'bg-gradient-to-r from-blue-500/10 to-blue-600/10 text-slate-800 self-end mr-10 rounded-br-none'
                          : 'bg-white/60 text-slate-700 self-start ml-10 rounded-bl-none'}
                                `}
                    >
                      <p className="text-lg font-medium leading-relaxed">{msg.message}</p>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>

              {/* Visualizer - Deep Layer */}
              <div className="relative w-full h-[500px] flex items-center justify-center scale-110 opacity-90 transition-all duration-1000 ease-in-out">
                <div className="absolute inset-0 bg-blue-500/5 blur-[120px] rounded-full animate-pulse"></div>
                <ParticleSphere state={status} />
              </div>

              {/* Status Text - Elegant & Tracking */}
              <div className="absolute bottom-32 flex flex-col items-center space-y-2">
                <h2 className="text-3xl font-light text-slate-400 tracking-[0.2em] uppercase transition-all duration-500">
                  {status === 'idle' ? 'Ready' : status}
                </h2>
                {status !== 'idle' && <div className="w-12 h-1 bg-gradient-to-r from-transparent via-blue-400 to-transparent rounded-full animate-pulse" />}
              </div>
            </div>

            {/* Bottom Input Area - Floating Pill */}
            <div className="absolute bottom-8 left-0 right-0 flex justify-center z-30 px-8">
              <div className="w-full max-w-3xl relative flex items-center group">
                {/* ... Input ... */}
                <div className="absolute -inset-1 bg-gradient-to-r from-blue-400 to-indigo-400 rounded-full blur opacity-20 group-hover:opacity-40 transition duration-500"></div>
                <div className="relative flex-1 flex items-center bg-white/80 backdrop-blur-xl border border-white/60 shadow-2xl rounded-full p-2 transition-all duration-300 focus-within:bg-white focus-within:shadow-blue-200/50">
                  <Input
                    placeholder="Ask anything..."
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onFocus={() => { socket.emit('start_typing'); }}
                    onBlur={() => { socket.emit('stop_typing'); }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && inputText.trim()) {
                        socket.emit('text_command', { text: inputText });
                        setInputText("");
                        socket.emit('stop_typing');
                      }
                    }}
                    className="h-14 bg-transparent border-transparent focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-xl text-slate-800 placeholder:text-slate-400 px-6 w-full"
                  />
                  <Button
                    size="icon"
                    className="h-12 w-12 rounded-full bg-blue-600 hover:bg-blue-700 shadow-lg text-white transition-transform active:scale-90 mr-1"
                    onClick={() => {
                      if (inputText.trim()) {
                        socket.emit('text_command', { text: inputText });
                        setInputText("");
                        socket.emit('stop_typing');
                      }
                    }}
                  >
                    <Send size={20} className="ml-0.5" />
                  </Button>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

const CapabilityItem = ({ label }) => (
  <div className="flex items-center space-x-2 py-1">
    <div className="w-1.5 h-1.5 rounded-full bg-blue-400"></div>
    <span>{label}</span>
  </div>
);

const SectionHeader = ({ title }) => (
  <div className="px-3 py-2 text-xs font-bold text-slate-400 uppercase tracking-widest mb-2 mt-6">
    {title}
  </div>
);

const NavItem = ({ icon, label, active, onClick }) => (
  <div
    onClick={onClick}
    className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg cursor-pointer transition-all duration-300 group ${active ? 'bg-white shadow-sm ring-1 ring-slate-100 text-blue-600 font-medium' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'}`}
  >
    <span className={`${active ? 'text-blue-500' : 'text-slate-400 group-hover:text-slate-600'} transition-colors`}>{icon}</span>
    <span className="text-sm">{label}</span>
  </div>
);

export default App;
