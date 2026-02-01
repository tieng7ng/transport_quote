import api from './api';
import type { Quote } from '../types';

export const QuoteService = {
    getAll: async (params?: { partner_id?: string; transport_mode?: string }) => {
        const response = await api.get<Quote[]>('/quotes/', { params });
        return response.data;
    },

    getById: async (id: string) => {
        const response = await api.get<Quote>(`/quotes/${id}`);
        return response.data;
    },

    delete: async (id: string) => {
        await api.delete(`/quotes/${id}`);
    },

    getCount: async (params?: { partner_id?: string }) => {
        const response = await api.get<number>('/quotes/count', { params });
        return response.data;
    },

    search: async (criteria: any) => {
        const response = await api.post<Quote[]>('/match/', criteria);
        return response.data;
    }
};
