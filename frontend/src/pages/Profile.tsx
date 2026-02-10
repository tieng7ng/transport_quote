import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { Lock, Mail, Shield } from 'lucide-react';

const Profile = () => {
    const { user } = useAuth();
    const [passwordData, setPasswordData] = useState({
        old_password: '',
        new_password: '',
        confirm_password: ''
    });
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    if (!user) return null;

    const handlePasswordChange = async (e: React.FormEvent) => {
        e.preventDefault();
        setMessage(null);

        if (passwordData.new_password !== passwordData.confirm_password) {
            setMessage({ type: 'error', text: 'Les nouveaux mots de passe ne correspondent pas' });
            return;
        }

        setIsLoading(true);
        try {
            await api.post('/auth/change-password', {
                old_password: passwordData.old_password,
                new_password: passwordData.new_password
            });
            setMessage({ type: 'success', text: 'Mot de passe mis à jour avec succès' });
            setPasswordData({ old_password: '', new_password: '', confirm_password: '' });
        } catch (err: any) {
            setMessage({ type: 'error', text: err.response?.data?.detail || 'Erreur lors de la mise à jour' });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="p-6 max-w-4xl mx-auto">
            <h1 className="text-2xl font-bold text-slate-800 mb-8">Mon Profil</h1>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Info Card */}
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 md:col-span-1">
                    <div className="flex flex-col items-center mb-6">
                        <div className="w-24 h-24 rounded-full bg-indigo-100 flex items-center justify-center text-2xl font-bold text-indigo-600 mb-4">
                            {user.first_name.charAt(0)}{user.last_name.charAt(0)}
                        </div>
                        <h2 className="text-xl font-semibold text-slate-800">{user.first_name} {user.last_name}</h2>
                        <span className={`mt-2 px-3 py-1 rounded-full text-xs font-semibold
                            ${user.role === 'SUPER_ADMIN' ? 'bg-purple-100 text-purple-800' :
                                user.role === 'ADMIN' ? 'bg-red-100 text-red-800' :
                                    'bg-indigo-100 text-indigo-800'}`}>
                            {user.role}
                        </span>
                    </div>

                    <div className="space-y-4">
                        <div className="flex items-center gap-3 text-slate-600">
                            <Mail className="w-4 h-4" />
                            <span className="text-sm">{user.email}</span>
                        </div>
                        <div className="flex items-center gap-3 text-slate-600">
                            <Shield className="w-4 h-4" />
                            <span className="text-sm">Compte {user.is_active ? 'Actif' : 'Inactif'}</span>
                        </div>
                    </div>
                </div>

                {/* Password Change Form */}
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 md:col-span-2">
                    <div className="flex items-center gap-2 mb-6">
                        <Lock className="w-5 h-5 text-slate-500" />
                        <h3 className="text-lg font-semibold text-slate-800">Changer de mot de passe</h3>
                    </div>

                    {message && (
                        <div className={`p-4 rounded-lg mb-6 text-sm ${message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
                            }`}>
                            {message.text}
                        </div>
                    )}

                    <form onSubmit={handlePasswordChange} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">
                                Ancien mot de passe
                            </label>
                            <input
                                type="password"
                                required
                                className="w-full rounded-lg border-slate-300 focus:border-indigo-500 focus:ring-indigo-500"
                                value={passwordData.old_password}
                                onChange={e => setPasswordData({ ...passwordData, old_password: e.target.value })}
                            />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">
                                    Nouveau mot de passe
                                </label>
                                <input
                                    type="password"
                                    required
                                    className="w-full rounded-lg border-slate-300 focus:border-indigo-500 focus:ring-indigo-500"
                                    value={passwordData.new_password}
                                    onChange={e => setPasswordData({ ...passwordData, new_password: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">
                                    Confirmer le mot de passe
                                </label>
                                <input
                                    type="password"
                                    required
                                    className="w-full rounded-lg border-slate-300 focus:border-indigo-500 focus:ring-indigo-500"
                                    value={passwordData.confirm_password}
                                    onChange={e => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                                />
                            </div>
                        </div>

                        <div className="pt-4 flex justify-end">
                            <button
                                type="submit"
                                disabled={isLoading}
                                className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                            >
                                {isLoading ? 'Mise à jour...' : 'Mettre à jour le mot de passe'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default Profile;
