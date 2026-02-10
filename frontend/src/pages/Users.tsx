import { useState, useEffect } from 'react';
import type { User, UserUpdate } from '../types/auth';
import userService from '../services/userService';
import { useAuth } from '../context/AuthContext';
import { Pencil, Trash2, Check, X, User as UserIcon } from 'lucide-react';

const Users = () => {
    const { user: currentUser } = useAuth();
    const [users, setUsers] = useState<User[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [editingUser, setEditingUser] = useState<User | null>(null);
    const [formData, setFormData] = useState<UserUpdate>({});

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

    const handleEdit = (user: User) => {
        setEditingUser(user);
        setFormData({
            first_name: user.first_name,
            last_name: user.last_name,
            role: user.role,
            is_active: user.is_active
        });
    };

    const handleCancelEdit = () => {
        setEditingUser(null);
        setFormData({});
    };

    const handleSave = async () => {
        if (!editingUser) return;
        try {
            await userService.update(editingUser.id, formData);
            setEditingUser(null);
            fetchUsers();
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Failed to update user');
        }
    };

    const handleDelete = async (id: string) => {
        if (!window.confirm('Are you sure you want to delete this user?')) return;
        try {
            await userService.delete(id);
            fetchUsers();
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Failed to delete user');
        }
    };

    const handleToggleActive = async (user: User) => {
        try {
            await userService.update(user.id, { is_active: !user.is_active });
            fetchUsers();
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Failed to update status');
        }
    }

    if (isLoading) return <div className="p-8 text-center text-slate-500">Loading users...</div>;
    if (error) return <div className="p-8 text-center text-red-500">{error}</div>;

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                    <UserIcon className="w-6 h-6" />
                    Utilisateurs
                </h1>
                <div className="text-sm text-slate-500">
                    {users.length} utilisateur(s)
                </div>
            </div>

            <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Utilisateur</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Statut</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {users.map((user) => (
                            <tr key={user.id} className={user.id === currentUser?.id ? "bg-indigo-50" : ""}>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    {editingUser?.id === user.id ? (
                                        <div className="flex gap-2">
                                            <input
                                                className="border rounded px-2 py-1 w-24"
                                                value={formData.first_name}
                                                onChange={e => setFormData({ ...formData, first_name: e.target.value })}
                                            />
                                            <input
                                                className="border rounded px-2 py-1 w-24"
                                                value={formData.last_name}
                                                onChange={e => setFormData({ ...formData, last_name: e.target.value })}
                                            />
                                        </div>
                                    ) : (
                                        <div className="flex flex-col">
                                            <span className="font-medium text-gray-900">{user.first_name} {user.last_name}</span>
                                            <span className="text-gray-500 text-sm">{user.email}</span>
                                        </div>
                                    )}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    {editingUser?.id === user.id ? (
                                        <select
                                            className="border rounded px-2 py-1"
                                            value={formData.role}
                                            onChange={e => setFormData({ ...formData, role: e.target.value as any })}
                                            disabled={currentUser?.role !== 'SUPER_ADMIN' && user.role === 'ADMIN'}
                                        >
                                            <option value="VIEWER">Viewer</option>
                                            <option value="COMMERCIAL">Commercial</option>
                                            <option value="OPERATOR">Operator</option>
                                            <option value="ADMIN">Admin</option>
                                            {currentUser?.role === 'SUPER_ADMIN' && <option value="SUPER_ADMIN">Super Admin</option>}
                                        </select>
                                    ) : (
                                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                                            ${user.role === 'SUPER_ADMIN' ? 'bg-purple-100 text-purple-800' :
                                                user.role === 'ADMIN' ? 'bg-red-100 text-red-800' :
                                                    user.role === 'COMMERCIAL' ? 'bg-blue-100 text-blue-800' :
                                                        user.role === 'OPERATOR' ? 'bg-green-100 text-green-800' :
                                                            'bg-gray-100 text-gray-800'}`}>
                                            {user.role}
                                        </span>
                                    )}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <button
                                        onClick={() => handleToggleActive(user)}
                                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full cursor-pointer
                                        ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
                                    >
                                        {user.is_active ? 'Actif' : 'Inactif'}
                                    </button>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                    {editingUser?.id === user.id ? (
                                        <div className="flex justify-end gap-2">
                                            <button onClick={handleSave} className="text-green-600 hover:text-green-900"><Check className="w-5 h-5" /></button>
                                            <button onClick={handleCancelEdit} className="text-gray-600 hover:text-gray-900"><X className="w-5 h-5" /></button>
                                        </div>
                                    ) : (
                                        <div className="flex justify-end gap-3">
                                            <button onClick={() => handleEdit(user)} className="text-indigo-600 hover:text-indigo-900"><Pencil className="w-5 h-5" /></button>
                                            {user.id !== currentUser?.id && (
                                                <button onClick={() => handleDelete(user.id)} className="text-red-600 hover:text-red-900"><Trash2 className="w-5 h-5" /></button>
                                            )}
                                        </div>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default Users;
