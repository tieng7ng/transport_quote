import api from './api';
import type { User, UserUpdate } from '../types/auth';

export const userService = {
    getAll: async () => {
        const response = await api.get<User[]>('/users/');
        return response.data;
    },

    getById: async (id: string) => {
        const response = await api.get<User>(`/users/${id}`);
        return response.data;
    },

    create: async (data: any) => {
        const response = await api.post<User>('/users/', data);
        return response.data;
    },

    update: async (id: string, data: UserUpdate) => {
        const response = await api.put<User>(`/users/${id}`, data);
        return response.data;
    },

    updateStatus: async (id: string, is_active: boolean) => {
        const response = await api.patch<User>(`/users/${id}/status`, { is_active });
        return response.data;
    },

    updateRole: async (id: string, role: string) => {
        const response = await api.patch<User>(`/users/${id}/role`, { role });
        return response.data;
    },

    delete: async (id: string) => {
        const response = await api.delete(`/users/${id}`);
        return response.data;
    }
};

export default userService;
