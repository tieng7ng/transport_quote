import { useState, useEffect, useCallback } from 'react';
import { ClipboardList, Download, ChevronLeft, ChevronRight, Search, X, ChevronDown, ChevronUp } from 'lucide-react';
import activityService, { type ActivityLog, type ActivityLogsResponse } from '../services/activityService';

const ACTION_LABELS: Record<string, string> = {
    'auth.login_success': 'Connexion réussie',
    'auth.login_failed': 'Échec de connexion',
    'auth.logout': 'Déconnexion',
    'auth.password_changed': 'Mot de passe modifié',
    'search.performed': 'Recherche effectuée',
    'quote.created': 'Devis créé',
    'quote.updated': 'Devis modifié',
    'quote.status_changed': 'Statut devis modifié',
    'quote.deleted': 'Devis supprimé',
    'import.started': 'Import démarré',
    'import.completed': 'Import terminé',
    'import.failed': 'Import échoué',
    'user.created': 'Utilisateur créé',
    'user.updated': 'Utilisateur modifié',
    'user.deactivated': 'Utilisateur désactivé',
    'partner.created': 'Partenaire créé',
    'partner.updated': 'Partenaire modifié',
};

const ACTION_COLORS: Record<string, string> = {
    'auth.login_failed': 'bg-red-100 text-red-700',
    'auth.logout': 'bg-gray-100 text-gray-600',
    'auth.login_success': 'bg-green-100 text-green-700',
    'search.performed': 'bg-blue-100 text-blue-700',
    'quote.deleted': 'bg-red-100 text-red-700',
    'import.failed': 'bg-red-100 text-red-700',
    'user.deactivated': 'bg-orange-100 text-orange-700',
};

function formatDate(iso: string) {
    const d = new Date(iso);
    return d.toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}

function DetailsCell({ details }: { details: Record<string, any> }) {
    const [open, setOpen] = useState(false);
    const entries = Object.entries(details).filter(([, v]) => v !== null && v !== undefined);
    if (!entries.length) return <span className="text-gray-400">—</span>;
    return (
        <div>
            <button onClick={() => setOpen(o => !o)} className="flex items-center gap-1 text-indigo-600 hover:text-indigo-800 text-xs font-medium">
                {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                {open ? 'Masquer' : 'Détails'}
            </button>
            {open && (
                <div className="mt-1 p-2 bg-gray-50 rounded text-xs text-gray-600 space-y-0.5 border border-gray-100">
                    {entries.map(([k, v]) => (
                        <div key={k}><span className="font-medium">{k}:</span> {String(v)}</div>
                    ))}
                </div>
            )}
        </div>
    );
}

const UNIQUE_ACTIONS = Object.keys(ACTION_LABELS);

export default function ActivityLogs() {
    const [data, setData] = useState<ActivityLogsResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [filters, setFilters] = useState({ user_login: '', action: '', from: '', to: '' });
    const [applied, setApplied] = useState(filters);

    const fetchLogs = useCallback(async () => {
        setLoading(true);
        try {
            const params: any = { page, page_size: 50 };
            if (applied.user_login) params.user_login = applied.user_login;
            if (applied.action) params.action = applied.action;
            if (applied.from) params.from = applied.from;
            if (applied.to) params.to = applied.to;
            const res = await activityService.getLogs(params);
            setData(res);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    }, [page, applied]);

    useEffect(() => { fetchLogs(); }, [fetchLogs]);

    const handleApply = () => { setPage(1); setApplied(filters); };
    const handleReset = () => {
        const empty = { user_login: '', action: '', from: '', to: '' };
        setFilters(empty); setApplied(empty); setPage(1);
    };

    const handleExport = () => {
        const params: any = {};
        if (applied.user_login) params.user_login = applied.user_login;
        if (applied.action) params.action = applied.action;
        if (applied.from) params.from = applied.from;
        if (applied.to) params.to = applied.to;
        window.open(activityService.exportCsv(params), '_blank');
    };

    return (
        <div className="p-6 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                    <ClipboardList className="w-6 h-6 text-indigo-600" />
                    Historique des activités
                </h1>
                <button
                    onClick={handleExport}
                    className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition text-sm"
                >
                    <Download className="w-4 h-4" />
                    Exporter CSV
                </button>
            </div>

            {/* Filters */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4 flex flex-wrap gap-3 items-end">
                <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Utilisateur</label>
                    <input
                        type="text"
                        placeholder="login..."
                        value={filters.user_login}
                        onChange={e => setFilters(f => ({ ...f, user_login: e.target.value }))}
                        className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 w-36"
                    />
                </div>
                <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Action</label>
                    <select
                        value={filters.action}
                        onChange={e => setFilters(f => ({ ...f, action: e.target.value }))}
                        className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 bg-white w-48"
                    >
                        <option value="">Toutes</option>
                        {UNIQUE_ACTIONS.map(a => <option key={a} value={a}>{ACTION_LABELS[a]}</option>)}
                    </select>
                </div>
                <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Du</label>
                    <input type="date" value={filters.from}
                        onChange={e => setFilters(f => ({ ...f, from: e.target.value }))}
                        className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                    />
                </div>
                <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Au</label>
                    <input type="date" value={filters.to}
                        onChange={e => setFilters(f => ({ ...f, to: e.target.value }))}
                        className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                    />
                </div>
                <div className="flex gap-2 ml-auto">
                    <button onClick={handleReset} className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50">
                        <X className="w-4 h-4" /> Réinitialiser
                    </button>
                    <button onClick={handleApply} className="flex items-center gap-1 px-4 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
                        <Search className="w-4 h-4" /> Filtrer
                    </button>
                </div>
            </div>

            {/* Table */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                {loading ? (
                    <div className="p-12 text-center text-gray-400">Chargement...</div>
                ) : (
                    <>
                        <table className="min-w-full divide-y divide-gray-100">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Date / Heure</th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Utilisateur</th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Action</th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Ressource</th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Détails</th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">IP</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50">
                                {data?.items.map((log: ActivityLog) => (
                                    <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{formatDate(log.created_at)}</td>
                                        <td className="px-4 py-3">
                                            <div className="text-sm font-medium text-gray-800">{log.user_login || '—'}</div>
                                            {log.user_role && <div className="text-xs text-gray-400">{log.user_role}</div>}
                                        </td>
                                        <td className="px-4 py-3">
                                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${ACTION_COLORS[log.action] || 'bg-indigo-50 text-indigo-700'}`}>
                                                {ACTION_LABELS[log.action] || log.action}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-xs text-gray-500">{log.resource || '—'}</td>
                                        <td className="px-4 py-3 max-w-xs"><DetailsCell details={log.details} /></td>
                                        <td className="px-4 py-3 text-xs text-gray-400 font-mono">{log.ip_address || '—'}</td>
                                    </tr>
                                ))}
                                {data?.items.length === 0 && (
                                    <tr><td colSpan={6} className="px-4 py-10 text-center text-gray-400 text-sm">Aucune activité trouvée</td></tr>
                                )}
                            </tbody>
                        </table>

                        {/* Pagination */}
                        {data && data.pages > 1 && (
                            <div className="px-4 py-3 border-t border-gray-100 flex items-center justify-between text-sm text-gray-500">
                                <span>Page {data.page}/{data.pages} — {data.total} résultats</span>
                                <div className="flex gap-2">
                                    <button
                                        disabled={page === 1}
                                        onClick={() => setPage(p => p - 1)}
                                        className="flex items-center gap-1 px-3 py-1 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                                    >
                                        <ChevronLeft className="w-4 h-4" /> Précédent
                                    </button>
                                    <button
                                        disabled={page >= data.pages}
                                        onClick={() => setPage(p => p + 1)}
                                        className="flex items-center gap-1 px-3 py-1 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                                    >
                                        Suivant <ChevronRight className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
