import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import authService from '../../services/authService';
import { Lock } from 'lucide-react';

interface ChangePasswordModalProps {
    isOpen: boolean;
}

const ChangePasswordModal = ({ isOpen }: ChangePasswordModalProps) => {
    const { logout } = useAuth();
    const [oldPassword, setOldPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (newPassword !== confirmPassword) {
            setError("Les nouveaux mots de passe ne correspondent pas");
            return;
        }

        setIsLoading(true);
        try {
            await authService.changePassword(oldPassword, newPassword);
            // Reload window to refresh user state/token or just close modal?
            // Usually relogging in might be safer, or just refreshing user context.
            // For now, let's refresh page to be safe and ensure clean state.
            window.location.reload();
        } catch (err: any) {
            if (err.response?.data?.detail && Array.isArray(err.response.data.detail)) {
                setError(err.response.data.detail.map((e: any) => e.msg).join('\n'));
            } else {
                setError(err.response?.data?.detail || "Erreur lors du changement de mot de passe");
            }
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true"></div>
                <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
                <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                    <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                        <div className="sm:flex sm:items-start">
                            <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10">
                                <Lock className="h-6 w-6 text-red-600" aria-hidden="true" />
                            </div>
                            <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                                <h3 className="text-lg leading-6 font-medium text-gray-900" id="modal-title">
                                    Changement de mot de passe obligatoire
                                </h3>
                                <div className="mt-2 text-sm text-gray-500">
                                    <p>Pour des raisons de sécurité, vous devez changer votre mot de passe temporaire avant de continuer.</p>
                                </div>

                                {error && (
                                    <div className="mt-4 bg-red-50 border-l-4 border-red-400 p-4">
                                        <div className="flex">
                                            <div className="ml-3">
                                                <p className="text-sm text-red-700 whitespace-pre-line">{error}</p>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                <form onSubmit={handleSubmit} className="mt-4 space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700">Mot de passe actuel</label>
                                        <input
                                            type="password"
                                            required
                                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 border p-2"
                                            value={oldPassword}
                                            onChange={(e) => setOldPassword(e.target.value)}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700">Nouveau mot de passe</label>
                                        <input
                                            type="password"
                                            required
                                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 border p-2"
                                            value={newPassword}
                                            onChange={(e) => setNewPassword(e.target.value)}
                                        />
                                        <p className="mt-1 text-xs text-gray-500">
                                            8 caractères minimum, 1 majuscule, 1 minuscule, 1 chiffre.
                                        </p>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700">Confirmer le nouveau mot de passe</label>
                                        <input
                                            type="password"
                                            required
                                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 border p-2"
                                            value={confirmPassword}
                                            onChange={(e) => setConfirmPassword(e.target.value)}
                                        />
                                    </div>
                                    <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                                        <button
                                            type="submit"
                                            disabled={isLoading}
                                            className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
                                        >
                                            {isLoading ? 'Mise à jour...' : 'Mettre à jour'}
                                        </button>
                                        <button
                                            type="button"
                                            onClick={logout}
                                            className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:w-auto sm:text-sm"
                                        >
                                            Se déconnecter
                                        </button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ChangePasswordModal;
