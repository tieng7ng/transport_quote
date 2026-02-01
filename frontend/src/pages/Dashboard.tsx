import React, { useEffect, useState } from 'react';
import { PartnerService } from '../services/partnerService';
import { QuoteService } from '../services/quoteService';
import { Users, FileText, Activity, TrendingUp, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Dashboard: React.FC = () => {
    const [stats, setStats] = useState({
        partnersCount: 0,
        quotesCount: 0,
        successRate: 100
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const [partners, quotesCount] = await Promise.all([
                    PartnerService.getAll(),
                    QuoteService.getCount()
                ]);
                setStats({
                    partnersCount: partners.length,
                    quotesCount: quotesCount,
                    successRate: 100
                });
            } catch (e) {
                console.error("Failed to fetch dashboard stats", e);
            } finally {
                setLoading(false);
            }
        };
        fetchStats();
    }, []);

    return (
        <div className="p-6">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-slate-800">Tableau de bord</h1>
                <p className="text-slate-500 mt-1">Bienvenue sur votre interface d'administration Transport Quote.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <StatCard
                    title="Partenaires Actifs"
                    value={loading ? '...' : stats.partnersCount}
                    icon={Users}
                    trend="Actifs"
                    color="bg-blue-600"
                    link="/partners"
                />
                <StatCard
                    title="Tarifs en Base"
                    value={loading ? '...' : stats.quotesCount.toLocaleString()}
                    icon={FileText}
                    trend="Total"
                    color="bg-emerald-600"
                    link="/quotes"
                />
                <StatCard
                    title="Taux de Succes Import"
                    value={`${stats.successRate}%`}
                    icon={Activity}
                    trend="Stable"
                    color="bg-violet-600"
                    link="/imports"
                />
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                <Link to="/imports" className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 hover:shadow-md transition-shadow group">
                    <div className="flex items-center justify-between">
                        <div>
                            <h3 className="text-lg font-bold text-slate-800">Importer des Tarifs</h3>
                            <p className="text-slate-500 text-sm mt-1">Uploadez un fichier Excel ou CSV</p>
                        </div>
                        <ArrowRight className="w-5 h-5 text-slate-400 group-hover:text-blue-600 group-hover:translate-x-1 transition-all" />
                    </div>
                </Link>
                <Link to="/partners" className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 hover:shadow-md transition-shadow group">
                    <div className="flex items-center justify-between">
                        <div>
                            <h3 className="text-lg font-bold text-slate-800">Gerer les Partenaires</h3>
                            <p className="text-slate-500 text-sm mt-1">Ajouter ou modifier un transporteur</p>
                        </div>
                        <ArrowRight className="w-5 h-5 text-slate-400 group-hover:text-blue-600 group-hover:translate-x-1 transition-all" />
                    </div>
                </Link>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-bold text-slate-800">Activite Recente</h3>
                    <Link to="/imports" className="text-sm text-blue-600 font-medium hover:text-blue-700">Voir les imports</Link>
                </div>
                <div className="border rounded-xl p-8 py-12 text-center bg-slate-50/50 border-dashed border-slate-200">
                    <TrendingUp className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                    <h4 className="text-slate-900 font-medium">Pret a commencer</h4>
                    <p className="text-slate-500 text-sm mt-1">Importez vos premiers tarifs pour voir l'activite ici.</p>
                </div>
            </div>
        </div>
    );
};

interface StatCardProps {
    title: string;
    value: string | number;
    icon: React.ElementType;
    trend: string;
    color: string;
    link?: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon: Icon, trend, color, link }) => {
    const content = (
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow relative overflow-hidden group cursor-pointer">
            <div className={`absolute top-0 right-0 w-24 h-24 ${color} opacity-5 rounded-bl-full -mr-4 -mt-4 transition-transform group-hover:scale-110`}></div>

            <div className="flex items-start justify-between">
                <div>
                    <p className="text-slate-500 text-sm font-medium uppercase tracking-wide">{title}</p>
                    <h3 className="text-3xl font-extrabold text-slate-800 mt-2">{value}</h3>
                </div>
                <div className={`p-3 rounded-xl ${color} bg-opacity-10 text-white`}>
                    <Icon className={`w-6 h-6 ${color.replace('bg-', 'text-')}`} />
                </div>
            </div>

            <div className="mt-4 flex items-center text-sm text-emerald-600 font-medium bg-emerald-50 w-fit px-2 py-1 rounded-full">
                <TrendingUp className="w-3 h-3 mr-1" />
                {trend}
            </div>
        </div>
    );

    return link ? <Link to={link}>{content}</Link> : content;
};
