import api from './api';

export interface ActivityLog {
    id: string;
    user_login: string;
    user_role: string;
    action: string;
    resource: string | null;
    resource_id: string | null;
    details: Record<string, any>;
    ip_address: string | null;
    created_at: string;
}

export interface ActivityLogsResponse {
    total: number;
    page: number;
    page_size: number;
    pages: number;
    items: ActivityLog[];
}

export interface StatsOverview {
    period: { from: string; to: string };
    active_users: number;
    searches: number;
    quotes_created: number;
    quotes_sent: number;
    quotes_accepted: number;
    conversion_rate_pct: number;
}

export interface Alert {
    id: string;
    type: string;
    severity: string;
    details: Record<string, any>;
    seen: boolean;
    created_at: string;
}

const activityService = {
    // --- Activity Logs ---
    getLogs: async (params: {
        page?: number;
        page_size?: number;
        user_login?: string;
        action?: string;
        from?: string;
        to?: string;
    }): Promise<ActivityLogsResponse> => {
        const { data } = await api.get('/activity-logs', { params });
        return data;
    },

    exportCsv: (params: { user_login?: string; action?: string; from?: string; to?: string }): string => {
        const token = localStorage.getItem('access_token');
        const base = api.defaults.baseURL;
        const query = new URLSearchParams({ format: 'csv', ...params } as any).toString();
        return `${base}/activity-logs/export?${query}`;
    },

    // --- Stats ---
    getOverview: async (params?: { from?: string; to?: string }): Promise<StatsOverview> => {
        const { data } = await api.get('/stats/overview', { params });
        return data;
    },

    getDailyActivity: async (params?: { from?: string; to?: string }) => {
        const { data } = await api.get('/stats/activity', { params });
        return data;
    },

    getSearchStats: async (params?: { from?: string; to?: string }) => {
        const { data } = await api.get('/stats/searches', { params });
        return data;
    },

    getQuoteStats: async (params?: { from?: string; to?: string }) => {
        const { data } = await api.get('/stats/quotes', { params });
        return data;
    },

    getSecurityStats: async (params?: { from?: string; to?: string }) => {
        const { data } = await api.get('/stats/security', { params });
        return data;
    },

    // --- Alerts ---
    getAlerts: async (): Promise<Alert[]> => {
        const { data } = await api.get('/alerts');
        return data;
    },

    markSeen: async (id: string) => {
        const { data } = await api.patch(`/alerts/${id}/seen`);
        return data;
    },

    resolveAlert: async (id: string, resolution: 'account_disabled' | 'ignored') => {
        const { data } = await api.patch(`/alerts/${id}/resolve`, { resolution });
        return data;
    },
};

export default activityService;
