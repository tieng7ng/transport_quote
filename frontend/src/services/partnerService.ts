import api from './api';
import type { Partner, PartnerCreate } from '../types';

export const PartnerService = {
    getAll: async () => {
        const response = await api.get<Partner[]>('/partners/');
        return response.data;
    },

    create: async (data: PartnerCreate) => {
        const response = await api.post<Partner>('/partners/', data);
        return response.data;
    },

    update: async (id: string, data: PartnerCreate) => {
        const response = await api.put<Partner>(`/partners/${id}`, data);
        return response.data;
    },

    delete: async (id: string) => {
        await api.delete(`/partners/${id}`);
    },

    deleteQuotes: async (id: string) => {
        const response = await api.delete<{ message: string, count: number }>(`/partners/${id}/quotes`);
        return response.data;
    }
};
