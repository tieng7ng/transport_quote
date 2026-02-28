import { useState, useEffect } from 'react';
import { BarChart2, TrendingUp, TrendingDown, Search, FileText, Shield } from 'lucide-react';
import activityService, { type StatsOverview } from '../services/activityService';

const PERIOD_OPTIONS = [
    { label: '7 jours', days: 7 },
    { label: '30 jours', days: 30 },
    { label: '90 jours', days: 90 },
];

function pad(n: number) { return String(n).padStart(2, '0'); }

function getDateRange(days: number) {
    const to = new Date();
    const from = new Date();
    from.setDate(to.getDate() - days);
    const fmt = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
    return { from: fmt(from), to: fmt(to) };
}

function KpiCard({ title, value, icon: Icon, color }: {
    title: string; value: string | number; icon: any; color: string;
}) {
    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 flex items-center gap-4">
            <div className={`p-3 rounded-xl ${color}`}>
                <Icon className="w-6 h-6 text-white" />
            </div>
            <div>
                <div className="text-xs text-gray-400 font-medium uppercase tracking-wide">{title}</div>
                <div className="text-2xl font-bold text-gray-800">{value}</div>
            </div>
        </div>
    );
}

function SimpleBar({ label, value, max }: { label: string; value: number; max: number }) {
    const pct = max > 0 ? (value / max) * 100 : 0;
    return (
        <div className="flex items-center gap-3">
            <div className="w-28 text-xs text-gray-600 truncate shrink-0">{label}</div>
            <div className="flex-1 bg-gray-100 rounded-full h-2">
                <div className="bg-indigo-500 h-2 rounded-full transition-all" style={{ width: `${pct}%` }} />
            </div>
            <div className="text-xs text-gray-500 w-10 text-right">{value}</div>
        </div>
    );
}

export default function Statistics() {
    const [periodDays, setPeriodDays] = useState(30);
    const [overview, setOverview] = useState<StatsOverview | null>(null);
    const [searchStats, setSearchStats] = useState<any>(null);
    const [quoteStats, setQuoteStats] = useState<any>(null);
    const [securityStats, setSecurityStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const params = getDateRange(periodDays);
        setLoading(true);
        Promise.all([
            activityService.getOverview(params),
            activityService.getSearchStats(params),
            activityService.getQuoteStats(params),
            activityService.getSecurityStats(params),
        ]).then(([ov, sr, qr, sc]) => {
            setOverview(ov);
            setSearchStats(sr);
            setQuoteStats(qr);
            setSecurityStats(sc);
        }).catch(console.error).finally(() => setLoading(false));
    }, [periodDays]);

    return (
        <div className="p-6 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                    <BarChart2 className="w-6 h-6 text-indigo-600" />
                    Statistiques & Indicateurs
                </h1>
                <div className="flex gap-2">
                    {PERIOD_OPTIONS.map(opt => (
                        <button
                            key={opt.days}
                            onClick={() => setPeriodDays(opt.days)}
                            className={`px-3 py-1.5 text-sm rounded-lg border transition ${periodDays === opt.days
                                ? 'bg-indigo-600 text-white border-indigo-600'
                                : 'bg-white text-gray-500 border-gray-200 hover:bg-gray-50'
                                }`}
                        >
                            {opt.label}
                        </button>
                    ))}
                </div>
            </div>

            {loading ? (
                <div className="py-20 text-center text-gray-400">Chargement des statistiques...</div>
            ) : (
                <>
                    {/* KPIs */}
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                        <KpiCard title="Utilisateurs actifs" value={overview?.active_users ?? 0} icon={TrendingUp} color="bg-indigo-500" />
                        <KpiCard title="Recherches" value={overview?.searches ?? 0} icon={Search} color="bg-blue-500" />
                        <KpiCard title="Devis créés" value={overview?.quotes_created ?? 0} icon={FileText} color="bg-emerald-500" />
                        <KpiCard title="Taux de conversion" value={`${overview?.conversion_rate_pct ?? 0}%`} icon={TrendingUp} color="bg-purple-500" />
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        {/* Top routes recherchées */}
                        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                            <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
                                <Search className="w-4 h-4 text-blue-500" /> Top routes recherchées
                            </h2>
                            {searchStats?.top_routes?.length > 0 ? (
                                <div className="space-y-3">
                                    {searchStats.top_routes.slice(0, 8).map((r: any, i: number) => (
                                        <SimpleBar
                                            key={i}
                                            label={`${r.origin} → ${r.destination}`}
                                            value={r.search_count}
                                            max={searchStats.top_routes[0].search_count}
                                        />
                                    ))}
                                </div>
                            ) : (
                                <div className="text-sm text-gray-400 py-4 text-center">Aucune donnée</div>
                            )}
                            {searchStats && (
                                <div className="mt-4 pt-4 border-t border-gray-50 flex justify-between text-xs text-gray-400">
                                    <span>{searchStats.total_searches} recherches</span>
                                    <span className="text-red-400">{searchStats.no_results_rate_pct}% sans résultat</span>
                                </div>
                            )}
                        </div>

                        {/* Entonnoir devis */}
                        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                            <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
                                <FileText className="w-4 h-4 text-emerald-500" /> Activité par commercial
                            </h2>
                            {quoteStats?.by_user?.length > 0 ? (
                                <div className="space-y-3">
                                    {quoteStats.by_user.slice(0, 8).map((u: any, i: number) => (
                                        <div key={i} className="flex items-center gap-3">
                                            <div className="w-28 text-xs font-medium text-gray-700 truncate">{u.user_login}</div>
                                            <div className="flex gap-2 flex-1">
                                                <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">{u.created} créés</span>
                                                <span className="text-xs bg-green-50 text-green-600 px-2 py-0.5 rounded-full">{u.sent} envoyés</span>
                                                <span className="text-xs bg-purple-50 text-purple-600 px-2 py-0.5 rounded-full">{u.accepted} acceptés</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-sm text-gray-400 py-4 text-center">Aucune donnée</div>
                            )}
                        </div>

                        {/* Modes de transport */}
                        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                            <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
                                <BarChart2 className="w-4 h-4 text-indigo-500" /> Modes de transport
                            </h2>
                            {searchStats?.by_transport_mode?.length > 0 ? (
                                <div className="space-y-3">
                                    {searchStats.by_transport_mode.map((m: any, i: number) => (
                                        <SimpleBar
                                            key={i}
                                            label={m.mode || 'Inconnu'}
                                            value={m.count}
                                            max={searchStats.by_transport_mode[0].count}
                                        />
                                    ))}
                                </div>
                            ) : (
                                <div className="text-sm text-gray-400 py-4 text-center">Aucune donnée</div>
                            )}
                        </div>

                        {/* Sécurité */}
                        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                            <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
                                <Shield className="w-4 h-4 text-red-500" /> Tentatives de connexion échouées
                            </h2>
                            {securityStats?.login_failures?.length > 0 ? (
                                <div className="space-y-2">
                                    {securityStats.login_failures.map((f: any, i: number) => (
                                        <div key={i} className="flex items-center justify-between bg-red-50 rounded-lg px-3 py-2 text-xs">
                                            <span className="font-medium text-red-700">{f.login || '?'}</span>
                                            <span className="text-red-500 font-mono">{f.ip_address}</span>
                                            <span className="bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-bold">{f.failures}×</span>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-sm text-gray-400 py-4 text-center flex items-center justify-center gap-2">
                                    <TrendingDown className="w-4 h-4 text-green-400" />
                                    Aucun échec détecté — tout va bien !
                                </div>
                            )}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
