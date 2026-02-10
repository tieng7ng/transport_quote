import api from './api';
import type { LoginRequest, RegisterRequest, TokenResponse, User } from '../types/auth';

const authService = {
    login: async (credentials: LoginRequest): Promise<TokenResponse> => {
        // OAuth2PasswordRequestForm expects form data
        const formData = new FormData();
        formData.append('username', credentials.username);
        formData.append('password', credentials.password);

        const response = await api.post<TokenResponse>('/auth/login', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        return response.data;
    },

    register: async (data: RegisterRequest): Promise<User> => {
        const response = await api.post<User>('/auth/register', data);
        return response.data;
    },

    getCurrentUser: async (): Promise<User> => {
        const response = await api.get<User>('/auth/me');
        return response.data;
    },

    logout: async (): Promise<void> => {
        // Try to notify backend but don't block if it fails
        try {
            await api.post('/auth/logout');
        } catch (e) {
            console.error('Logout error', e);
        }
    }
};

export default authService;
