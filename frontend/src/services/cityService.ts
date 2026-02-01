import api from './api';

export interface CitySuggestion {
    city: string;
    country: string;
    count: number;
}

export const CityService = {
    suggest: async (query: string, limit: number = 10) => {
        if (!query || query.length < 2) return [];
        const response = await api.get<CitySuggestion[]>('/cities/suggest', {
            params: { q: query, limit }
        });
        return response.data;
    }
};
