import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'https://transportquote.duckdns.org/transport/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor: Attach token
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Response interceptor: Handle 401
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            try {
                const refreshToken = localStorage.getItem('refresh_token');
                if (refreshToken) {
                    // Eviter dépendance circulaire si possible, ou appeler endpoint directement
                    const { data } = await axios.post(
                        `${originalRequest.baseURL}/auth/refresh`,
                        { refresh_token: refreshToken }
                    );

                    localStorage.setItem('access_token', data.access_token);
                    if (data.refresh_token) {
                        localStorage.setItem('refresh_token', data.refresh_token);
                    }

                    api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`;
                    originalRequest.headers['Authorization'] = `Bearer ${data.access_token}`;

                    return api(originalRequest);
                }
            } catch (refreshError) {
                // Refresh failed -> Logout
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export default api;
