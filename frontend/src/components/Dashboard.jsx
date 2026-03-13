import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, Circle, Plus, FileText, Calendar, TrendingUp, Clock, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';

// --- Calendar Component ---
// --- Calendar Component ---
const CalendarWidget = ({ tasks, onDateSelect, selectedDate, showMarkers = true, variant = 'default' }) => {
    const [currentMonth, setCurrentMonth] = useState(new Date());

    const nextMonth = () => {
        setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1));
    };

    const prevMonth = () => {
        setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1));
    };

    const formatDate = (date) => {
        return date.toISOString().split('T')[0];
    };

    const renderHeader = () => {
        return (
            <div className={`flex justify-between items-center mb-4 px-2 ${variant === 'minimal' ? 'text-slate-600' : 'text-slate-700'}`}>
                <Button variant="ghost" size="icon" onClick={prevMonth} className="hover:bg-blue-50 text-slate-400 hover:text-blue-600 h-8 w-8"><ChevronLeft size={18} /></Button>
                <span className="font-bold text-base capitalize">
                    {currentMonth.toLocaleString('default', { month: 'long', year: 'numeric' })}
                </span>
                <Button variant="ghost" size="icon" onClick={nextMonth} className="hover:bg-blue-50 text-slate-400 hover:text-blue-600 h-8 w-8"><ChevronRight size={18} /></Button>
            </div>
        );
    };

    const renderDays = () => {
        const days = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];
        return (
            <div className="grid grid-cols-7 mb-2 text-center text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                {days.map((day, i) => <div key={i}>{day}</div>)}
            </div>
        );
    };

    const renderCells = () => {
        const monthStart = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1);
        const monthEnd = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 0);
        const startDate = new Date(monthStart);
        startDate.setDate(startDate.getDate() - monthStart.getDay());
        const endDate = new Date(monthEnd);
        endDate.setDate(endDate.getDate() + (6 - monthEnd.getDay()));

        const rows = [];
        let days = [];
        let day = startDate;
        let formattedDate = "";

        while (day <= endDate) {
            for (let i = 0; i < 7; i++) {
                formattedDate = formatDate(day);
                const cloneDay = day;
                const isSelected = selectedDate === formattedDate;
                const isCurrentMonth = day.getMonth() === currentMonth.getMonth();
                const isToday = formattedDate === formatDate(new Date());

                // Check if any task exists on this date
                const hasTask = tasks.some(t => t.due_date && t.due_date.startsWith(formattedDate));

                days.push(
                    <div
                        key={day}
                        className={`p-1 h-8 flex items-center justify-center relative cursor-pointer rounded-full transition-all duration-200
                            ${!isCurrentMonth ? "text-slate-200" : "text-slate-600 hover:bg-blue-50"}
                            ${isSelected ? "bg-blue-600 text-white shadow-md hover:bg-blue-700 font-semibold" : ""}
                            ${isToday && !isSelected ? "text-blue-600 font-bold bg-blue-50/50" : ""}
                        `}
                        onClick={() => onDateSelect(formatDate(cloneDay))}
                    >
                        <span className="text-xs">{day.getDate()}</span>
                        {showMarkers && hasTask && !isSelected && (
                            <div className="absolute bottom-1 w-1 h-1 bg-blue-400 rounded-full"></div>
                        )}
                        {showMarkers && hasTask && isSelected && (
                            <div className="absolute bottom-1 w-1 h-1 bg-white rounded-full"></div>
                        )}
                    </div>
                );
                day = new Date(day.getFullYear(), day.getMonth(), day.getDate() + 1);
            }
            rows.push(
                <div className="grid grid-cols-7 gap-y-1" key={day}>
                    {days}
                </div>
            );
            days = [];
        }
        return <div className="">{rows}</div>;
    };

    if (variant === 'minimal') {
        return (
            <div className="p-2">
                {renderHeader()}
                {renderDays()}
                {renderCells()}
            </div>
        );
    }

    return (
        <div className="glass rounded-3xl p-6 shadow-sm border border-slate-100">
            {renderHeader()}
            {renderDays()}
            {renderCells()}
        </div>
    );
};

// --- Tab Component ---
const TabButton = ({ active, label, onClick, icon }) => (
    <button
        onClick={onClick}
        className={`flex items-center space-x-2 px-4 py-2 rounded-full transition-all duration-300 ${active ? 'bg-blue-600 text-white shadow-lg' : 'bg-white text-slate-500 hover:bg-slate-50'}`}
    >
        {icon}
        <span className="font-medium text-sm">{label}</span>
    </button>
);

const Dashboard = ({ tasks, notes, plans = [], onAdd, onUpdate, onTypingStart, onTypingStop }) => {
    const [activeTab, setActiveTab] = useState('tasks');
    const [newTask, setNewTask] = useState("");
    const [newDate, setNewDate] = useState("");
    const [newNote, setNewNote] = useState("");
    const [newPlan, setNewPlan] = useState("");

    // State for different calendars
    const [isInputCalendarOpen, setIsInputCalendarOpen] = useState(false); // For Add Task
    const [isGlobalCalendarOpen, setIsGlobalCalendarOpen] = useState(false); // Bottom Right
    const [isFilterCalendarOpen, setIsFilterCalendarOpen] = useState(false); // Filter

    const [taskFilter, setTaskFilter] = useState('pending');
    const [filterDate, setFilterDate] = useState(new Date().toISOString());

    // Refs for click outside
    const inputCalendarRef = useRef(null);
    const globalCalendarRef = useRef(null);
    const filterWrapperRef = useRef(null);

    // Handle Click Outside
    useEffect(() => {
        function handleClickOutside(event) {
            // Close Input Calendar
            if (inputCalendarRef.current && !inputCalendarRef.current.contains(event.target)) {
                setIsInputCalendarOpen(false);
            }
            // Close Global Calendar
            if (globalCalendarRef.current && !globalCalendarRef.current.contains(event.target)) {
                setIsGlobalCalendarOpen(false);
            }
            // Close Filter Popup
            if (filterWrapperRef.current && !filterWrapperRef.current.contains(event.target)) {
                setIsFilterCalendarOpen(false);
            }
        }
        // Bind the event listener
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            // Unbind the event listener on clean up
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [inputCalendarRef, globalCalendarRef, filterWrapperRef]);


    const activeTasks = tasks.filter(t => t.status !== 'completed');
    const completedTasks = tasks.filter(t => t.status === 'completed');

    const handleAddTask = () => {
        if (newTask.trim()) {
            // Default to today if no date selected
            const dateToUse = newDate || new Date().toISOString();
            onAdd('task', { title: newTask, priority: 'medium' }, dateToUse);
            setNewTask("");
            setNewDate("");
        }
    };

    const handleToggleTask = (task) => {
        const newStatus = task.status === 'completed' ? 'pending' : 'completed';
        onUpdate('task', task.id, { status: newStatus });
    };

    const handleAddNote = () => {
        if (newNote.trim()) {
            onAdd('note', { content: newNote });
            setNewNote("");
        }
    };

    const handleAddPlan = () => {
        if (newPlan.trim()) {
            onAdd('plan', { title: newPlan });
            setNewPlan("");
        }
    };

    // Auto-select date from calendar touches input
    const handleDateSelect = (dateStr) => {
        setNewDate(dateStr);
    };

    return (
        <div className="w-full h-full p-6 overflow-hidden flex flex-col relative">
            {/* Header / Tabs */}
            <div className="flex items-center justify-between mb-6 shrink-0">
                <div className="flex space-x-3">
                    <TabButton active={activeTab === 'tasks'} label="Tasks" icon={<CheckCircle size={18} />} onClick={() => setActiveTab('tasks')} />
                    <TabButton active={activeTab === 'notes'} label="Notes" icon={<FileText size={18} />} onClick={() => setActiveTab('notes')} />
                    <TabButton active={activeTab === 'plans'} label="Future Plans" icon={<TrendingUp size={18} />} onClick={() => setActiveTab('plans')} />
                </div>
                <div className="text-slate-400 text-xs font-medium uppercase tracking-widest">
                    Workspace
                </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto scrollbar-hide pb-20">

                {/* TASKS VIEW */}
                {activeTab === 'tasks' && (
                    <div className="h-full grid grid-cols-1 lg:grid-cols-2 gap-8 animate-in fade-in slide-in-from-bottom-4 duration-500">

                        {/* LEFT COLUMN: Add Task & Controls */}
                        <div className="glass rounded-3xl p-8 shadow-sm border border-white/50 relative flex flex-col justify-center">
                            {/* Decorative Background Blur */}
                            <div className="absolute -top-20 -right-20 w-60 h-60 bg-blue-400/10 rounded-full blur-3xl pointer-events-none"></div>

                            <div className="mb-8 text-center lg:text-left z-10">
                                <h2 className="text-3xl font-bold text-slate-800 mb-2">My Day</h2>
                                <p className="text-slate-500">Focus on what matters today.</p>
                            </div>

                            {/* Premium Input Bar */}
                            {/* Clean Light Input Area */}
                            <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-6 relative group transition-all hover:shadow-md h-64 flex flex-col">
                                <textarea
                                    value={newTask}
                                    onChange={(e) => setNewTask(e.target.value)}
                                    placeholder="What do you want to accomplish today?"
                                    className="w-full flex-1 resize-none outline-none text-xl bg-transparent placeholder:text-slate-300 text-slate-700 font-medium scrollbar-hide"
                                    onFocus={onTypingStart}
                                    onBlur={onTypingStop}
                                    onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleAddTask())}
                                />

                                {/* Footer Controls */}
                                <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-50">
                                    <div className="flex items-center space-x-2">
                                        <div className="flex items-center space-x-2 mr-2 relative">
                                            {newDate && (
                                                <motion.div
                                                    initial={{ scale: 0.8, opacity: 0 }}
                                                    animate={{ scale: 1, opacity: 1 }}
                                                    className="flex items-center space-x-1 px-3 py-1.5 bg-blue-50 text-blue-600 rounded-lg text-xs font-bold uppercase tracking-wide cursor-pointer hover:bg-blue-100 transition-colors"
                                                    onClick={() => setIsInputCalendarOpen(true)}
                                                >
                                                    <span>{new Date(newDate).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</span>
                                                    <button onClick={(e) => { e.stopPropagation(); setNewDate(""); }} className="ml-1 hover:text-blue-800">×</button>
                                                </motion.div>
                                            )}
                                            <Button
                                                size="icon"
                                                variant="ghost"
                                                onClick={() => setIsInputCalendarOpen(!isInputCalendarOpen)}
                                                className={`rounded-xl ${newDate ? 'text-blue-600 bg-blue-50' : 'text-slate-400 hover:text-blue-500 hover:bg-blue-50 '}`}
                                            >
                                                <Calendar size={20} />
                                            </Button>

                                            {/* Floating Calendar for Input - Anchored here */}
                                            {isInputCalendarOpen && (
                                                <div ref={inputCalendarRef} className="absolute bottom-full left-0 mb-2 bg-white border border-slate-100 shadow-xl rounded-2xl p-2 z-50 w-64 animate-in fade-in zoom-in-95 duration-200">
                                                    <CalendarWidget
                                                        tasks={tasks}
                                                        onDateSelect={(date) => {
                                                            handleDateSelect(date);
                                                            setIsInputCalendarOpen(false);
                                                        }}
                                                        selectedDate={newDate}
                                                        showMarkers={false}
                                                        variant="minimal"
                                                    />
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    <Button
                                        onClick={handleAddTask}
                                        className="h-10 px-6 rounded-xl bg-slate-900 hover:bg-slate-800 text-white shadow-lg shadow-slate-200 transition-transform active:scale-95 text-sm font-semibold tracking-wide"
                                    >
                                        Add Task
                                    </Button>
                                </div>
                            </div>
                        </div>

                        {/* RIGHT COLUMN: Today's Tasks List */}
                        <div className="glass rounded-3xl p-8 shadow-sm border border-white/50 overflow-y-auto relative flex flex-col">
                            {/* Filter tasks for today or explicit dates */}
                            {(() => {
                                // Use filterDate state
                                const targetDateStr = new Date(filterDate).toISOString().split('T')[0];
                                const isToday = targetDateStr === new Date().toISOString().split('T')[0];
                                const dateDisplay = isToday ? "Today" : new Date(filterDate).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });

                                const todaysActive = activeTasks.filter(t => !t.due_date || t.due_date.startsWith(targetDateStr));
                                const todaysCompleted = completedTasks.filter(t => !t.due_date || t.due_date.startsWith(targetDateStr));

                                const hasActive = todaysActive.length > 0;
                                const hasCompleted = todaysCompleted.length > 0;

                                return (
                                    <>
                                        {/* Mini Navbar for Right Column */}
                                        <div className="flex items-center justify-between mb-6 border-b border-slate-100/50 pb-2">
                                            <div className="flex items-center space-x-6">
                                                <button
                                                    onClick={() => setTaskFilter('pending')}
                                                    className={`pb-2 text-sm font-bold uppercase tracking-wide transition-all relative ${taskFilter === 'pending' ? 'text-blue-600' : 'text-slate-400 hover:text-slate-600'}`}
                                                >
                                                    Pending
                                                    {taskFilter === 'pending' && <motion.div layoutId="underline" className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 rounded-full" />}
                                                    <span className="ml-2 bg-slate-100 text-slate-500 py-0.5 px-2 rounded-full text-[10px]">{todaysActive.length}</span>
                                                </button>
                                                <button
                                                    onClick={() => setTaskFilter('completed')}
                                                    className={`pb-2 text-sm font-bold uppercase tracking-wide transition-all relative ${taskFilter === 'completed' ? 'text-emerald-600' : 'text-slate-400 hover:text-slate-600'}`}
                                                >
                                                    Completed
                                                    {taskFilter === 'completed' && <motion.div layoutId="underline" className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-600 rounded-full" />}
                                                    <span className="ml-2 bg-slate-100 text-slate-500 py-0.5 px-2 rounded-full text-[10px]">{todaysCompleted.length}</span>
                                                </button>
                                            </div>

                                            {/* Date Filter */}
                                            <div className="flex items-center relative" ref={filterWrapperRef}>
                                                <span className="text-xs font-bold uppercase text-slate-400 mr-2">{dateDisplay}</span>
                                                <Button
                                                    size="icon"
                                                    variant="ghost"
                                                    onClick={() => setIsFilterCalendarOpen(!isFilterCalendarOpen)}
                                                    className={`rounded-xl ${isFilterCalendarOpen ? 'bg-blue-50 text-blue-600' : 'text-slate-400 hover:bg-slate-50'} `}
                                                >
                                                    <Calendar size={16} />
                                                </Button>

                                                {/* Filter Calendar Popup */}
                                                {isFilterCalendarOpen && (
                                                    <div className="absolute top-10 right-0 bg-white border border-slate-100 shadow-xl rounded-2xl p-2 z-50 w-64 animate-in fade-in zoom-in-95 duration-200">
                                                        <input
                                                            type="date"
                                                            className="w-full text-sm p-2 border border-slate-100 rounded-lg text-slate-600 outline-none focus:ring-2 focus:ring-blue-100"
                                                            onChange={(e) => {
                                                                if (e.target.value) {
                                                                    setFilterDate(new Date(e.target.value).toISOString());
                                                                    setIsFilterCalendarOpen(false);
                                                                }
                                                            }}
                                                        />
                                                        <div className="mt-2 text-right">
                                                            <button
                                                                onClick={() => {
                                                                    setFilterDate(new Date().toISOString());
                                                                    setIsFilterCalendarOpen(false);
                                                                }}
                                                                className="text-xs font-bold text-blue-600 hover:underline px-2"
                                                            >
                                                                Reset to Today
                                                            </button>
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        <div className="flex-1 overflow-y-auto pr-2 space-y-3 scrollbar-hide">
                                            {/* PENDING VIEW */}
                                            {taskFilter === 'pending' && (
                                                <>
                                                    {todaysActive.length === 0 && (
                                                        <div className="h-full flex flex-col items-center justify-center opacity-60">
                                                            <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-4 text-slate-300">
                                                                <CheckCircle size={32} />
                                                            </div>
                                                            <p className="text-slate-400 text-sm font-medium">No pending tasks for {dateDisplay}.</p>
                                                            <p className="text-slate-300 text-xs">Enjoy your free time!</p>
                                                        </div>
                                                    )}
                                                    {todaysActive.map((task, i) => (
                                                        <motion.div
                                                            key={task.id}
                                                            initial={{ opacity: 0, y: 10 }}
                                                            animate={{ opacity: 1, y: 0 }}
                                                            transition={{ delay: i * 0.05 }}
                                                            className="group flex items-center p-4 rounded-2xl bg-white border border-slate-100 hover:border-blue-200 hover:shadow-md transition-all cursor-pointer relative overflow-hidden"
                                                        >
                                                            <div className="absolute inset-0 bg-blue-50/50 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                                                            <div className="relative flex-1 flex items-center z-10">
                                                                <button
                                                                    onClick={() => handleToggleTask(task)}
                                                                    className="mr-4 text-slate-300 hover:text-blue-500 transition-colors p-1"
                                                                >
                                                                    <Circle size={22} />
                                                                </button>
                                                                <div className="flex-1">
                                                                    <span className="text-base text-slate-700 font-medium group-hover:text-blue-900 transition-colors block">{task.title}</span>
                                                                    {task.due_date && (
                                                                        <span className="text-xs text-slate-400 font-medium flex items-center mt-1">
                                                                            <Clock size={12} className="mr-1" />
                                                                            {new Date(task.due_date).toLocaleDateString()}
                                                                        </span>
                                                                    )}
                                                                </div>
                                                            </div>
                                                        </motion.div>
                                                    ))}
                                                </>
                                            )}

                                            {/* COMPLETED VIEW */}
                                            {taskFilter === 'completed' && (
                                                <>
                                                    {todaysCompleted.length === 0 && (
                                                        <div className="h-full flex flex-col items-center justify-center opacity-60">
                                                            <p className="text-slate-400 text-sm">No completed tasks for {dateDisplay}.</p>
                                                        </div>
                                                    )}
                                                    {todaysCompleted.map((task, i) => (
                                                        <motion.div
                                                            key={task.id}
                                                            initial={{ opacity: 0 }}
                                                            animate={{ opacity: 1 }}
                                                            className="group flex items-center p-4 rounded-2xl bg-slate-50/50 border border-slate-100 transition-all cursor-pointer"
                                                        >
                                                            <button
                                                                onClick={() => handleToggleTask(task)}
                                                                className="mr-4 text-emerald-500 hover:text-emerald-600 transition-colors p-1"
                                                            >
                                                                <CheckCircle size={22} className="fill-emerald-100" />
                                                            </button>
                                                            <div className="flex-1">
                                                                <span className="text-sm text-slate-500 line-through decoration-slate-300 font-medium">{task.title}</span>
                                                            </div>
                                                            <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full uppercase tracking-wider">Done</span>
                                                        </motion.div>
                                                    ))}
                                                </>
                                            )}
                                        </div>
                                    </>
                                );
                            })()}
                        </div>
                    </div>
                )}

                {/* NOTES VIEW */}
                {activeTab === 'notes' && (
                    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <div className="glass rounded-3xl p-8 shadow-sm border border-white/50 relative overflow-hidden">
                            <div className="absolute -top-20 -left-20 w-60 h-60 bg-yellow-400/10 rounded-full blur-3xl pointer-events-none"></div>

                            {/* Premium Input Bar */}
                            <div className="relative group z-10 mb-8">
                                <div className="absolute -inset-0.5 bg-gradient-to-r from-yellow-300 to-orange-300 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-500"></div>
                                <div className="relative flex items-center bg-white rounded-2xl shadow-sm border border-slate-100 p-2 transition-all focus-within:ring-2 focus-within:ring-yellow-100 focus-within:border-yellow-200">
                                    <div className="pl-4 text-slate-400">
                                        <FileText size={20} />
                                    </div>
                                    <Input
                                        value={newNote}
                                        onChange={(e) => setNewNote(e.target.value)}
                                        placeholder="Capture an idea..."
                                        className="h-12 bg-transparent border-transparent focus:ring-0 text-lg placeholder:text-slate-400 text-slate-700 flex-1"
                                        onFocus={onTypingStart}
                                        onBlur={onTypingStop}
                                        onKeyDown={(e) => e.key === 'Enter' && handleAddNote()}
                                    />
                                    <Button
                                        size="icon"
                                        onClick={handleAddNote}
                                        className="h-12 w-12 rounded-xl bg-gradient-to-br from-yellow-400 to-orange-500 hover:from-yellow-500 hover:to-orange-600 text-white shadow-lg shadow-yellow-200 transition-transform active:scale-95"
                                    >
                                        <Plus size={24} />
                                    </Button>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {notes.length === 0 && <div className="col-span-2 text-center text-slate-400 py-10">No notes yet.</div>}
                                {notes.map((note, i) => (
                                    <motion.div
                                        key={note.id}
                                        initial={{ opacity: 0, scale: 0.95 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        className="p-6 rounded-2xl bg-amber-50/50 border border-amber-100 hover:bg-amber-50 transition-colors relative group"
                                    >
                                        <div className="absolute top-4 right-4 text-amber-200 group-hover:text-amber-300 transition-colors">
                                            <FileText size={20} />
                                        </div>
                                        <p className="text-xs text-slate-400 mb-3 font-mono uppercase tracking-wider">{note.created_at?.split(' ')[0] || 'TODAY'}</p>
                                        <p className="text-slate-800 leading-relaxed font-medium text-lg">{note.content}</p>
                                    </motion.div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* PLANS VIEW */}
                {activeTab === 'plans' && (
                    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <div className="glass rounded-3xl p-8 shadow-sm border border-white/50 relative overflow-hidden">
                            <div className="absolute bottom-0 right-0 w-80 h-80 bg-purple-400/10 rounded-full blur-3xl pointer-events-none"></div>

                            {/* Premium Input Bar */}
                            <div className="relative group z-10 mb-8">
                                <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-300 to-pink-300 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-500"></div>
                                <div className="relative flex items-center bg-white rounded-2xl shadow-sm border border-slate-100 p-2 transition-all focus-within:ring-2 focus-within:ring-purple-100 focus-within:border-purple-200">
                                    <div className="pl-4 text-slate-400">
                                        <TrendingUp size={20} />
                                    </div>
                                    <Input
                                        value={newPlan}
                                        onChange={(e) => setNewPlan(e.target.value)}
                                        placeholder="Add a major goal..."
                                        className="h-12 bg-transparent border-transparent focus:ring-0 text-lg placeholder:text-slate-400 text-slate-700 flex-1"
                                        onFocus={onTypingStart}
                                        onBlur={onTypingStop}
                                        onKeyDown={(e) => e.key === 'Enter' && handleAddPlan()}
                                    />
                                    <Button
                                        size="icon"
                                        onClick={handleAddPlan}
                                        className="h-12 w-12 rounded-xl bg-gradient-to-br from-purple-600 to-fuchsia-600 hover:from-purple-700 hover:to-fuchsia-700 text-white shadow-lg shadow-purple-200 transition-transform active:scale-95"
                                    >
                                        <Plus size={24} />
                                    </Button>
                                </div>
                            </div>

                            {plans && plans.length === 0 && (
                                <div className="text-center py-12">
                                    <div className="w-16 h-16 bg-purple-50 rounded-full flex items-center justify-center mx-auto mb-4 text-purple-200">
                                        <TrendingUp size={32} />
                                    </div>
                                    <p className="text-slate-400">No long-term plans yet. Dream big!</p>
                                </div>
                            )}

                            <div className="space-y-4">
                                {plans && plans.map((plan, i) => (
                                    <div key={i} className="bg-white border border-slate-100 p-6 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
                                        <div className="flex justify-between items-start mb-4">
                                            <div>
                                                <h3 className="font-bold text-slate-800 text-xl mb-1">{plan.title}</h3>
                                                <p className="text-slate-500 text-sm">{plan.description || "No description set"}</p>
                                            </div>
                                            <span className="text-xs font-bold text-purple-600 bg-purple-50 px-3 py-1.5 rounded-lg uppercase tracking-wider">{plan.progress}% Complete</span>
                                        </div>
                                        {/* Progress Bar */}
                                        <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
                                            <div className="bg-gradient-to-r from-purple-500 to-fuchsia-600 h-full rounded-full shadow-lg shadow-purple-200" style={{ width: `${plan.progress}% ` }}></div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* Floating Global Calendar - Always Available */}
                <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end pointer-events-none" ref={globalCalendarRef}>
                    <div className="pointer-events-auto">
                        {isGlobalCalendarOpen && (
                            <motion.div
                                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.9, y: 20 }}
                                className="mb-4 w-80 bg-white/90 backdrop-blur-xl border border-white/50 shadow-2xl rounded-3xl overflow-hidden"
                            >
                                <div className="p-1">
                                    <CalendarWidget
                                        tasks={tasks}
                                        selectedDate={new Date(filterDate).toISOString().split('T')[0]}
                                        onDateSelect={(date) => {
                                            setFilterDate(new Date(date).toISOString());
                                            setIsGlobalCalendarOpen(false);
                                        }}
                                        showMarkers={true}
                                    />
                                </div>
                            </motion.div>
                        )}
                    </div>

                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => setIsGlobalCalendarOpen(!isGlobalCalendarOpen)}
                        className={`pointer-events-auto h-14 w-14 rounded-full shadow-xl flex items-center justify-center transition-all duration-300 ${isGlobalCalendarOpen ? 'bg-slate-800 text-white rotate-45' : 'bg-blue-600 text-white hover:bg-blue-700'}`}
                    >
                        {isGlobalCalendarOpen ? <Plus size={24} /> : <Calendar size={24} />}
                    </motion.button>
                </div>
            </div>
        </div>
    );
};
export default Dashboard;
