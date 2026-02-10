import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Users, UploadCloud, Box, Search, ShoppingCart, UserCog } from 'lucide-react';
import { useCustomerQuote } from '../../context/CustomerQuoteContext';
import RoleGate from '../auth/RoleGate';
import { useAuth } from '../../context/AuthContext';

export const Sidebar: React.FC = () => {
    const { openSearchForConsultation } = useCustomerQuote();
    const { user } = useAuth();

    const initials = user ? `${user.first_name.charAt(0)}${user.last_name.charAt(0)}`.toUpperCase() : '';

    return (
        <div className="flex flex-col w-64 bg-slate-900 border-r border-slate-800 text-white transition-all duration-300">
            <div className="flex items-center justify-center h-20 border-b border-slate-800/50 bg-gradient-to-r from-slate-900 to-slate-800">
                <div className="flex items-center gap-3">
                    <div className="bg-blue-600 p-2 rounded-lg shadow-lg shadow-blue-500/20">
                        <Box className="w-6 h-6 text-white" />
                    </div>
                    <span className="text-xl font-bold tracking-tight">TQ Admin</span>
                </div>
            </div>

            <nav className="flex-1 px-4 py-6 space-y-2">
                <div className="px-4 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Menu
                </div>

                <SidebarLink to="/" icon={LayoutDashboard} label="Dashboard" />
                <RoleGate allowedRoles={['ADMIN', 'OPERATOR']}>
                    <SidebarLink to="/partners" icon={Users} label="Partenaires" />
                    <SidebarLink to="/imports" icon={UploadCloud} label="Imports" />
                </RoleGate>

                <RoleGate allowedRoles={['ADMIN', 'SUPER_ADMIN']}>
                    <SidebarLink to="/users" icon={UserCog} label="Utilisateurs" />
                </RoleGate>

                <div className="px-4 mt-6 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Client
                </div>

                <button
                    onClick={openSearchForConsultation}
                    className="w-full flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 text-slate-400 hover:bg-slate-800 hover:text-white hover:pl-5 group"
                >
                    <Search className="mr-3 h-5 w-5 transition-transform group-hover:scale-110" />
                    Recherche
                </button>

                <SidebarLink to="/customer-quotes" icon={ShoppingCart} label="Mes Devis" />
            </nav>

            {user && (
                <div className="p-4 border-t border-slate-800">
                    <div className="flex items-center gap-3 px-2">
                        <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-xs font-bold">
                            {initials}
                        </div>
                        <div className="flex flex-col overflow-hidden">
                            <span className="text-sm font-medium truncate">{user.first_name} {user.last_name}</span>
                            <span className="text-xs text-slate-500 truncate">{user.email}</span>
                        </div>
                    </div>
                </div>
            )}
        </div >
    );
};

interface SidebarLinkProps {
    to: string;
    icon: React.ElementType;
    label: string;
}

const SidebarLink: React.FC<SidebarLinkProps> = ({ to, icon: Icon, label }) => (
    <NavLink
        to={to}
        className={({ isActive }) =>
            `flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 group ${isActive
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/20'
                : 'text-slate-400 hover:bg-slate-800 hover:text-white hover:pl-5'
            }`
        }
    >
        <Icon className="mr-3 h-5 w-5 transition-transform group-hover:scale-110" />
        {label}
    </NavLink>
);
