import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import type { User, LoginRequest } from '../types/auth';
import authService from '../services/authService';
import { jwtDecode } from 'jwt-decode';

interface AuthState {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    error: string | null;
    mustChangePassword?: boolean;
}

interface AuthContextType extends AuthState {
    login: (credentials: LoginRequest) => Promise<void>;
    logout: () => void;
    hasRole: (...roles: string[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(localStorage.getItem('access_token'));
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [mustChangePassword, setMustChangePassword] = useState<boolean>(false);

    useEffect(() => {
        const initAuth = async () => {
            const storedToken = localStorage.getItem('access_token');
            if (storedToken) {
                try {
                    // Check if token is expired
                    const decoded: any = jwtDecode(storedToken);
                    const now = Date.now() / 1000;

                    if (decoded.exp < now) {
                        // Token expired
                    }

                    setToken(storedToken);
                    const currentUser = await authService.getCurrentUser();
                    setUser(currentUser);
                    if (currentUser.must_change_password) {
                        setMustChangePassword(true);
                    }
                } catch (err: any) {
                    console.error("Auth initialization error", err);

                    // Check for 403 Password change required
                    if (err.response?.status === 403 &&
                        (err.response?.data?.detail === "Password change required" ||
                            err.response?.headers?.["x-require-password-change"] === "true")) {
                        setMustChangePassword(true);
                        // We might want to keep the token so the user can change password
                        setToken(storedToken);
                    } else {
                        logout();
                    }
                }
            }
            setIsLoading(false);
        };

        initAuth();
    }, []);

    const login = async (credentials: LoginRequest) => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await authService.login(credentials);
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            setToken(data.access_token);

            // After login, we try to get user. If it fails due to password change, we catch it.
            try {
                const currentUser = await authService.getCurrentUser();
                setUser(currentUser);
                if (currentUser.must_change_password) {
                    setMustChangePassword(true);
                }
            } catch (err: any) {
                if (err.response?.status === 403 &&
                    (err.response?.data?.detail === "Password change required" ||
                        err.response?.headers?.["x-require-password-change"] === "true")) {
                    setMustChangePassword(true);
                } else {
                    throw err;
                }
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Login failed');
            throw err;
        } finally {
            setIsLoading(false);
        }
    };

    const logout = async () => {
        try {
            await authService.logout();
        } catch (error) {
            console.error("Logout API call failed", error);
        } finally {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            setUser(null);
            setToken(null);
            setMustChangePassword(false);
            window.location.href = '/login';
        }
    };

    const hasRole = (...roles: string[]) => {
        if (!user) return false;
        if (user.role === 'SUPER_ADMIN') return true;
        return roles.includes(user.role);
    };

    return (
        <AuthContext.Provider value={{
            user,
            token,
            isAuthenticated: !!user || mustChangePassword, // Allow partial auth for password change
            isLoading,
            error,
            login,
            logout,
            hasRole,
            mustChangePassword
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
