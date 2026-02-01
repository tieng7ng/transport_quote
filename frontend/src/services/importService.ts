import api from './api';
import type { ImportJob } from '../types';

export const ImportService = {
    upload: async (partnerId: string, file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('partner_id', partnerId);

        // Note: Content-Type multipart/form-data is handled automatically by browser/axios when passing FormData
        const response = await api.post<ImportJob>('/imports/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    getJob: async (id: string) => {
        const response = await api.get<ImportJob>(`/imports/${id}`);
        return response.data;
    }
};
