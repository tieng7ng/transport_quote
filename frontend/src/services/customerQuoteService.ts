import api from './api';
import type {
    CustomerQuote,
    CustomerQuoteCreate,
    CustomerQuoteItem,
    CustomerQuoteItemCreate,
    CustomerQuoteItemUpdate
} from '../types/customerQuote';

const BASE_URL = '/customer-quotes';

export const customerQuoteService = {
    // --- Quotes ---

    getAll: async (skip = 0, limit = 100): Promise<CustomerQuote[]> => {
        const response = await api.get<CustomerQuote[]>(BASE_URL, {
            params: { skip, limit }
        });
        return response.data;
    },

    getById: async (id: string): Promise<CustomerQuote> => {
        const response = await api.get<CustomerQuote>(`${BASE_URL}/${id}`);
        return response.data;
    },

    create: async (data: CustomerQuoteCreate): Promise<CustomerQuote> => {
        const response = await api.post<CustomerQuote>(BASE_URL, data);
        return response.data;
    },

    update: async (id: string, data: Partial<CustomerQuoteCreate>): Promise<CustomerQuote> => {
        const response = await api.put<CustomerQuote>(`${BASE_URL}/${id}`, data);
        return response.data;
    },

    delete: async (id: string): Promise<void> => {
        await api.delete(`${BASE_URL}/${id}`);
    },

    // --- Items ---

    addTransportItem: async (quoteId: string, partnerQuoteId: string, weight: number): Promise<CustomerQuoteItem> => {
        const payload: CustomerQuoteItemCreate = {
            item_type: 'TRANSPORT',
            description: 'Transport', // Sera écrasé par le backend
            sell_price: 0, // Sera calculé
            margin_amount: 0,
            partner_quote_id: partnerQuoteId,
            weight: weight
        };
        const response = await api.post<CustomerQuoteItem>(`${BASE_URL}/${quoteId}/items`, payload);
        return response.data;
    },

    addFeeItem: async (quoteId: string, description: string, price: number): Promise<CustomerQuoteItem> => {
        const payload: CustomerQuoteItemCreate = {
            item_type: 'FEE',
            description: description,
            sell_price: price,
            margin_amount: price, // Marge 100% pour frais
        };
        const response = await api.post<CustomerQuoteItem>(`${BASE_URL}/${quoteId}/fees`, payload);
        return response.data;
    },

    updateItem: async (quoteId: string, itemId: string, data: CustomerQuoteItemUpdate): Promise<CustomerQuoteItem> => {
        const response = await api.put<CustomerQuoteItem>(`${BASE_URL}/${quoteId}/items/${itemId}`, data);
        return response.data;
    },

    removeItem: async (quoteId: string, itemId: string): Promise<void> => {
        await api.delete(`${BASE_URL}/${quoteId}/items/${itemId}`);
    }
};
