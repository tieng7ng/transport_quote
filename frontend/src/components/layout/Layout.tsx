import React from 'react';
import { Sidebar } from './Sidebar';
import { QuoteSidebar } from '../customer-quote/QuoteSidebar';
import { SearchModal } from '../SearchModal';
import { Outlet, useLocation } from 'react-router-dom';
import { Bell } from 'lucide-react';

const pageTitles: Record<string, string> = {
    '/': 'Tableau de bord',
    '/partners': 'Gestion des Partenaires',
    '/quotes': 'Gestion des Tarifs',
    '/imports': 'Importation des Tarifs',
};

export const Layout: React.FC = () => {
    const location = useLocation();
    const pageTitle = pageTitles[location.pathname] || 'Transport Quote';

    return (
        <div className="flex h-screen bg-slate-50 font-sans">
            <Sidebar />
            <div className="flex-1 flex flex-col overflow-hidden relative">
                <header className="bg-white/80 backdrop-blur-md border-b border-slate-200 z-10 px-8 py-5 flex items-center justify-between sticky top-0">
                    <h2 className="text-xl font-bold text-slate-800 tracking-tight">{pageTitle}</h2>
                    <div className="flex items-center gap-4">
                        <button className="p-2 rounded-full hover:bg-slate-100 text-slate-500 transition-colors relative">
                            <Bell className="w-5 h-5" />
                            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
                        </button>
                    </div>
                </header>
                <main className="flex-1 overflow-x-hidden overflow-y-auto scroll-smooth">
                    <Outlet />
                </main>
            </div>
            <QuoteSidebar />
            <SearchModal />
        </div>
    );
};
