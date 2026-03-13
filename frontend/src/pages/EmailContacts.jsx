import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const EmailContacts = () => {
    const [contacts, setContacts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [formData, setFormData] = useState({ nickname: '', email: '' });
    const [statusMsg, setStatusMsg] = useState('');

    const API_URL = "http://localhost:8000/api/contacts";

    useEffect(() => {
        fetchContacts();
    }, []);

    const fetchContacts = async () => {
        try {
            const res = await fetch(API_URL);
            const data = await res.json();
            setContacts(data);
        } catch (error) {
            console.error("Error fetching contacts:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm("Delete this contact?")) return;
        try {
            await fetch(`${API_URL}/${id}`, { method: 'DELETE' });
            fetchContacts();
        } catch (error) {
            console.error("Error deleting contact:", error);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!formData.nickname || !formData.email) return;

        try {
            const res = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            const data = await res.json();
            if (data.success) {
                setStatusMsg("Contact added!");
                setShowModal(false);
                setFormData({ nickname: '', email: '' });
                fetchContacts();
            } else {
                setStatusMsg(data.message || "Failed to add.");
            }
        } catch (error) {
            setStatusMsg("Error connecting to server.");
        }
    };

    return (
        <div className="p-8 text-white h-full overflow-y-auto">
            <div className="flex justify-between items-center mb-8">
                <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
                    Email Contacts
                </h1>
                <button
                    onClick={() => setShowModal(true)}
                    className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg hover:opacity-90 transition shadow-lg"
                >
                    + Add Contact
                </button>
            </div>

            {/* Contact List */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <AnimatePresence>
                    {contacts.map((contact) => (
                        <motion.div
                            key={contact.id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.9 }}
                            className="bg-white/5 backdrop-blur-md border border-white/10 p-6 rounded-xl shadow-xl relative group"
                        >
                            <h3 className="text-xl font-semibold text-blue-200 capitalize">{contact.nickname}</h3>
                            <p className="text-gray-300 mt-1">{contact.email}</p>

                            <button
                                onClick={() => handleDelete(contact.id)}
                                className="absolute top-4 right-4 text-red-400 opacity-0 group-hover:opacity-100 transition hover:text-red-300"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                                </svg>
                            </button>
                        </motion.div>
                    ))}
                </AnimatePresence>

                {contacts.length === 0 && !loading && (
                    <p className="text-gray-500 col-span-full text-center py-10">No contacts found. Add one to get started!</p>
                )}
            </div>

            {/* Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="bg-[#1a1a2e] border border-white/10 p-8 rounded-2xl w-full max-w-md shadow-2xl"
                    >
                        <h2 className="text-2xl font-bold mb-6 text-white">Add New Contact</h2>

                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-gray-400 mb-1 text-sm">Nickname (Voice Name)</label>
                                <input
                                    type="text"
                                    placeholder="e.g. Ravi, Mom, Boss"
                                    className="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-white focus:outline-none focus:border-blue-500 transition"
                                    value={formData.nickname}
                                    onChange={(e) => setFormData({ ...formData, nickname: e.target.value })}
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-gray-400 mb-1 text-sm">Email Address</label>
                                <input
                                    type="email"
                                    placeholder="user@example.com"
                                    className="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-white focus:outline-none focus:border-blue-500 transition"
                                    value={formData.email}
                                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                    required
                                />
                            </div>

                            {statusMsg && <p className="text-sm text-yellow-400">{statusMsg}</p>}

                            <div className="flex justify-end gap-3 mt-6">
                                <button
                                    type="button"
                                    onClick={() => setShowModal(false)}
                                    className="px-4 py-2 text-gray-300 hover:text-white transition"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-6 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white font-medium shadow-lg transition"
                                >
                                    Save Contact
                                </button>
                            </div>
                        </form>
                    </motion.div>
                </div>
            )}
        </div>
    );
};

export default EmailContacts;
