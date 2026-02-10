import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

interface Props {
    allowedRoles?: string[];
}

const ProtectedRoute = ({ allowedRoles }: Props) => {
    const { isAuthenticated, isLoading, user } = useAuth();

    if (isLoading) {
        // Or a proper loading spinner
        return <div className="flex justify-center items-center h-screen">Loading...</div>;
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    if (allowedRoles && user && !allowedRoles.includes(user.role) && user.role !== 'SUPER_ADMIN') {
        return <Navigate to="/" replace />; // Or 403 page
    }

    return <Outlet />;
};

export default ProtectedRoute;
