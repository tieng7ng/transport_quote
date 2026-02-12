import { useState, useEffect } from 'react';
import type { User, UserCreate } from '../types/auth'; // Ensure UserCreate is exported from types/auth
import userService from '../services/userService';
import { useAuth } from '../context/AuthContext';
import { Pencil, Trash2, UserPlus, Power, ShieldAlert } from 'lucide-react';
import Modal from '../components/common/Modal';

const Users = () => {
    const { user: currentUser } = useAuth();
    const [users, setUsers] = useState<User[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Modal states
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [selectedUser, setSelectedUser] = useState<User | null>(null);

    // Form states
    const [formData, setFormData] = useState<Partial<UserCreate>>({
        role: 'VIEWER',
        is_active: true
    });

    useEffect(() => {
        fetchUsers();
    }, []);

    const fetchUsers = async () => {
        try {
            const data = await userService.getAll();
            setUsers(data);
            setIsLoading(false);
        } catch (err) {
            setError('Failed to fetch users');
            setIsLoading(false);
        }
    };

    const handleOpenCreate = () => {
        setFormData({ role: 'VIEWER', is_active: true });
        setIsCreateModalOpen(true);
    };

    const handleOpenEdit = (user: User) => {
        setSelectedUser(user);
        setFormData({
            login: user.login,
            email: user.email,
            first_name: user.first_name,
            last_name: user.last_name,
            role: user.role,
            is_active: user.is_active
        });
        setIsEditModalOpen(true);
    };

    const handleCloseModals = () => {
        setIsCreateModalOpen(false);
        setIsEditModalOpen(false);
        setSelectedUser(null);
        setFormData({});
        setError(null);
    };

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        try {
            await userService.create(formData as UserCreate);
            fetchUsers();
            handleCloseModals();
        } catch (err: any) {
            console.error("Create user error", err);
            // Handle Pydantic validation errors (array of errors)
            if (err.response?.data?.detail && Array.isArray(err.response.data.detail)) {
                const messages = err.response.data.detail.map((e: any) => e.msg).join('\n');
                setError(messages);
            } else {
                setError(err.response?.data?.detail || 'Failed to create user');
            }
        }
    };

    const handleUpdate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedUser) return;
        try {
            // Filter out empty password if not provided
            const updateData: any = { ...formData };
            if (!updateData.password) delete updateData.password;

            await userService.update(selectedUser.id, updateData);
            fetchUsers();
            handleCloseModals();
        } catch (err: any) {
            console.error("Update user error", err);
            // Handle Pydantic validation errors (array of errors)
            if (err.response?.data?.detail && Array.isArray(err.response.data.detail)) {
                const messages = err.response.data.detail.map((e: any) => e.msg).join('\n');
                setError(messages);
            } else {
                setError(err.response?.data?.detail || 'Failed to update user');
            }
        }
    };

    const handleDelete = async (id: string) => {
        if (!window.confirm('Êtes-vous sûr de vouloir supprimer cet utilisateur ?')) return;
        try {
            await userService.delete(id);
            fetchUsers();
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Failed to delete user');
        }
    };

    const handleToggleStatus = async (user: User) => {
        try {
            await userService.updateStatus(user.id, !user.is_active);
            fetchUsers();
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Failed to update status');
        }
    };

    if (isLoading) return <div className="p-8 text-center text-slate-500">Chargement des utilisateurs...</div>;

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                    <ShieldAlert className="w-6 h-6 text-purple-600" />
                    Gestion des Utilisateurs
                </h1>
                <button
                    onClick={handleOpenCreate}
                    className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
                >
                    <UserPlus className="w-4 h-4 mr-2" />
                    Ajouter un utilisateur
                </button>
            </div>

            {error && <div className="mb-4 p-4 bg-red-100 text-red-700 rounded-lg">{error}</div>}

            <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Login / Email</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Identité</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                            <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Statut</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {users.map((user) => (
                            <tr key={user.id} className="hover:bg-gray-50">
                                <td className="px-6 py-4">
                                    <div className="flex flex-col">
                                        <span className="font-semibold text-gray-900">{user.login}</span>
                                        <span className="text-gray-500 text-sm">{user.email}</span>
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className="text-gray-900">{user.first_name} {user.last_name}</span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                                        ${user.role === 'SUPER_ADMIN' ? 'bg-purple-100 text-purple-800' :
                                            user.role === 'ADMIN' ? 'bg-red-100 text-red-800' :
                                                user.role === 'COMMERCIAL' ? 'bg-blue-100 text-blue-800' :
                                                    user.role === 'OPERATOR' ? 'bg-green-100 text-green-800' :
                                                        'bg-gray-100 text-gray-800'}`}>
                                        {user.role}
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-center">
                                    <button
                                        onClick={() => handleToggleStatus(user)}
                                        disabled={currentUser?.role !== 'SUPER_ADMIN' && user.role === 'SUPER_ADMIN'}
                                        title={user.is_active ? "Désactiver" : "Activer"}
                                        className={`p-1 rounded-full transition-colors ${currentUser?.role !== 'SUPER_ADMIN' && user.role === 'SUPER_ADMIN'
                                            ? 'text-gray-300 cursor-not-allowed'
                                            : user.is_active ? 'text-green-600 hover:bg-green-100' : 'text-gray-400 hover:bg-gray-100'
                                            }`}
                                    >
                                        <Power className="w-5 h-5" />
                                    </button>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                    <div className="flex justify-end gap-3">
                                        {(currentUser?.role === 'SUPER_ADMIN' || user.role !== 'SUPER_ADMIN') && (
                                            <button onClick={() => handleOpenEdit(user)} className="text-indigo-600 hover:text-indigo-900" title="Modifier">
                                                <Pencil className="w-5 h-5" />
                                            </button>
                                        )}
                                        {user.id !== currentUser?.id && (currentUser?.role === 'SUPER_ADMIN' || user.role !== 'SUPER_ADMIN') && (
                                            <button onClick={() => handleDelete(user.id)} className="text-red-600 hover:text-red-900" title="Supprimer">
                                                <Trash2 className="w-5 h-5" />
                                            </button>
                                        )}
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Create Modal */}
            <Modal isOpen={isCreateModalOpen} onClose={handleCloseModals} title="Créer un utilisateur">
                <form onSubmit={handleCreate} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Prénom</label>
                            <input
                                required
                                type="text"
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 border p-2"
                                value={formData.first_name || ''}
                                onChange={e => setFormData({ ...formData, first_name: e.target.value })}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Nom</label>
                            <input
                                required
                                type="text"
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 border p-2"
                                value={formData.last_name || ''}
                                onChange={e => setFormData({ ...formData, last_name: e.target.value })}
                            />
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Login</label>
                        <input
                            required
                            type="text"
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 border p-2"
                            value={formData.login || ''}
                            onChange={e => setFormData({ ...formData, login: e.target.value })}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Email</label>
                        <input
                            required
                            type="email"
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 border p-2"
                            value={formData.email || ''}
                            onChange={e => setFormData({ ...formData, email: e.target.value })}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Mot de passe</label>
                        <input
                            required
                            type="password"
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 border p-2"
                            value={formData.password || ''}
                            onChange={e => setFormData({ ...formData, password: e.target.value })}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Rôle</label>
                        <select
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 border p-2 bg-white"
                            value={formData.role}
                            onChange={e => setFormData({ ...formData, role: e.target.value as any })}
                        >
                            <option value="VIEWER">Viewer</option>
                            <option value="COMMERCIAL">Commercial</option>
                            <option value="OPERATOR">Operator</option>
                            <option value="ADMIN">Admin</option>
                            {currentUser?.role === 'SUPER_ADMIN' && <option value="SUPER_ADMIN">Super Admin</option>}
                        </select>
                    </div>
                    <div className="flex justify-end pt-4">
                        <button
                            type="button"
                            onClick={handleCloseModals}
                            className="mr-3 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                        >
                            Annuler
                        </button>
                        <button
                            type="submit"
                            className="px-4 py-2 text-sm font-medium text-white bg-purple-600 border border-transparent rounded-md hover:bg-purple-700"
                        >
                            Créer
                        </button>
                    </div>
                </form>
            </Modal>

            {/* Edit Modal */}
            <Modal isOpen={isEditModalOpen} onClose={handleCloseModals} title="Modifier un utilisateur">
                <form onSubmit={handleUpdate} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Prénom</label>
                            <input
                                required
                                type="text"
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 border p-2"
                                value={formData.first_name || ''}
                                onChange={e => setFormData({ ...formData, first_name: e.target.value })}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Nom</label>
                            <input
                                required
                                type="text"
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 border p-2"
                                value={formData.last_name || ''}
                                onChange={e => setFormData({ ...formData, last_name: e.target.value })}
                            />
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Login</label>
                        <input
                            required
                            type="text"
                            disabled
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 border p-2 bg-gray-100 cursor-not-allowed"
                            value={formData.login || ''}
                            onChange={e => setFormData({ ...formData, login: e.target.value })}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Email</label>
                        <input
                            required
                            type="email"
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 border p-2"
                            value={formData.email || ''}
                            onChange={e => setFormData({ ...formData, email: e.target.value })}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Mot de passe (Laisser vide pour ne pas changer)</label>
                        <input
                            type="password"
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 border p-2"
                            placeholder="Nouveau mot de passe"
                            value={formData.password || ''}
                            onChange={e => setFormData({ ...formData, password: e.target.value })}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Rôle</label>
                        <select
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 border p-2 bg-white"
                            value={formData.role}
                            onChange={e => setFormData({ ...formData, role: e.target.value as any })}
                        >
                            <option value="VIEWER">Viewer</option>
                            <option value="COMMERCIAL">Commercial</option>
                            <option value="OPERATOR">Operator</option>
                            <option value="ADMIN">Admin</option>
                            {currentUser?.role === 'SUPER_ADMIN' && <option value="SUPER_ADMIN">Super Admin</option>}
                        </select>
                    </div>
                    <div className="flex justify-end pt-4">
                        <button
                            type="button"
                            onClick={handleCloseModals}
                            className="mr-3 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                        >
                            Annuler
                        </button>
                        <button
                            type="submit"
                            className="px-4 py-2 text-sm font-medium text-white bg-purple-600 border border-transparent rounded-md hover:bg-purple-700"
                        >
                            Enregistrer
                        </button>
                    </div>
                </form>
            </Modal>
        </div>
    );
};

export default Users;
