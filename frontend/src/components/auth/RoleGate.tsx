import React from 'react';
import { useAuth } from '../../context/AuthContext';

interface Props {
    children: React.ReactNode;
    allowedRoles: string[];
}

const RoleGate = ({ children, allowedRoles }: Props) => {
    const { user } = useAuth();

    if (!user) return null;

    if (user.role === 'SUPER_ADMIN' || allowedRoles.includes(user.role)) {
        return <>{children}</>;
    }

    return null;
};

export default RoleGate;
