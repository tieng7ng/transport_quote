import api from './api';

export interface CitySuggestion {
    city: string;
    country: string;
    count: number;
    zip?: string;
}

export interface CountriesResponse {
    origin_countries: string[];
    dest_countries: string[];
}

export const CityService = {
    suggest: async (query: string, limit: number = 10) => {
        if (!query || query.length < 2) return [];
        const response = await api.get<CitySuggestion[]>('/cities/suggest', {
            params: { q: query, limit }
        });
        return response.data;
    },
    getCountries: async () => {
        const response = await api.get<CountriesResponse>('/cities/countries');
        return response.data;
    }
};
