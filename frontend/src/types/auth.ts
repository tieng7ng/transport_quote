export interface User {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    role: 'SUPER_ADMIN' | 'ADMIN' | 'COMMERCIAL' | 'OPERATOR' | 'VIEWER';
    is_active: boolean;
    must_change_password?: boolean;
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
    refresh_token: string;
}

export interface LoginRequest {
    username: string;  // OAuth2 expects 'username', which is email in our case
    password: string;
}

export interface RegisterRequest {
    email: string;
    first_name: string;
    last_name: string;
    password?: string; // Optional if generated or set later
}

export interface UserUpdate {
    first_name?: string;
    last_name?: string;
    email?: string;
    role?: 'SUPER_ADMIN' | 'ADMIN' | 'COMMERCIAL' | 'OPERATOR' | 'VIEWER';
    is_active?: boolean;
    password?: string;
}
