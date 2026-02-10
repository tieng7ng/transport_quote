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

    update: async (id: string, data: UserUpdate) => {
        const response = await api.put<User>(`/users/${id}`, data);
        return response.data;
    },

    delete: async (id: string) => {
        const response = await api.delete(`/users/${id}`);
        return response.data;
    }
};

export default userService;
