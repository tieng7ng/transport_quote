import { useState, useEffect, useCallback } from 'react';
import { Bell, X, AlertTriangle, ShieldAlert } from 'lucide-react';
import activityService, { type Alert } from '../../services/activityService';

const SEVERITY_COLORS = {
    critical: { bg: 'bg-red-50', border: 'border-red-200', icon: 'text-red-500', badge: 'bg-red-500' },
    medium: { bg: 'bg-orange-50', border: 'border-orange-200', icon: 'text-orange-400', badge: 'bg-orange-400' },
};

function AlertItem({ alert, onAction }: { alert: Alert; onAction: () => void }) {
    const colors = SEVERITY_COLORS[alert.severity as keyof typeof SEVERITY_COLORS] || SEVERITY_COLORS.medium;
    const d = alert.details;

    const description = alert.type === 'login_failures'
        ? `"${d.login}" a échoué ${d.failures} fois en 10 minutes. IP : ${d.ip_address}`
        : `"${d.user_login}" a effectué ${d.action_count} actions en 5 minutes`;

    const elapsed = (() => {
        const diff = Math.floor((Date.now() - new Date(alert.created_at).getTime()) / 60000);
        return diff < 1 ? 'à l\'instant' : `il y a ${diff} min`;
    })();

    const resolve = async (resolution: 'account_disabled' | 'ignored') => {
        try {
            await activityService.resolveAlert(alert.id, resolution);
            onAction();
        } catch (e) { console.error(e); }
    };

    return (
        <div className={`${colors.bg} ${colors.border} border rounded-lg p-3 text-sm`}>
            <div className="flex items-start justify-between gap-2">
                <div className="flex items-start gap-2">
                    <AlertTriangle className={`w-4 h-4 mt-0.5 shrink-0 ${colors.icon}`} />
                    <div>
                        <div className="font-semibold text-gray-800">
                            {alert.type === 'login_failures' ? '🔴 Échecs de connexion' : '🟠 Activité suspecte'}
                        </div>
                        <div className="text-gray-600 text-xs mt-0.5">{description}</div>
                    </div>
                </div>
                <span className="text-xs text-gray-400 whitespace-nowrap shrink-0">{elapsed}</span>
            </div>
            <div className="flex gap-2 mt-2">
                {alert.type === 'login_failures' && (
                    <button
                        onClick={() => resolve('account_disabled')}
                        className="text-xs px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700 transition"
                    >
                        Désactiver le compte
                    </button>
                )}
                <button
                    onClick={() => resolve('ignored')}
                    className="text-xs px-2 py-1 bg-white border border-gray-200 text-gray-600 rounded hover:bg-gray-50 transition"
                >
                    Ignorer
                </button>
            </div>
        </div>
    );
}

export default function AlertBadge() {
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [open, setOpen] = useState(false);

    const fetchAlerts = useCallback(async () => {
        try {
            const data = await activityService.getAlerts();
            setAlerts(data);
        } catch { /* silently fail */ }
    }, []);

    useEffect(() => {
        fetchAlerts();
        const interval = setInterval(fetchAlerts, 30_000); // rafraîchir toutes les 30s
        return () => clearInterval(interval);
    }, [fetchAlerts]);

    const unread = alerts.filter(a => !a.seen).length;

    const handleOpen = async () => {
        setOpen(true);
        // Mark unread as seen
        for (const a of alerts.filter(al => !al.seen)) {
            try { await activityService.markSeen(a.id); } catch { /* ignore */ }
        }
        setAlerts(prev => prev.map(a => ({ ...a, seen: true })));
    };

    const handleAction = () => {
        setOpen(false);
        fetchAlerts();
    };

    return (
        <div className="relative">
            <button
                onClick={open ? () => setOpen(false) : handleOpen}
                className="relative p-2 rounded-lg text-gray-500 hover:bg-gray-100 transition"
                title="Alertes de sécurité"
                id="alert-badge-btn"
            >
                <Bell className="w-5 h-5" />
                {unread > 0 && (
                    <span className="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center font-bold leading-none">
                        {unread > 9 ? '9+' : unread}
                    </span>
                )}
            </button>

            {open && (
                <>
                    {/* Backdrop */}
                    <div className="fixed inset-0 z-30" onClick={() => setOpen(false)} />

                    {/* Panel */}
                    <div className="absolute right-0 top-10 z-40 w-80 bg-white rounded-xl shadow-xl border border-gray-200 overflow-hidden">
                        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
                            <div className="flex items-center gap-2 font-semibold text-sm text-gray-800">
                                <ShieldAlert className="w-4 h-4 text-red-500" />
                                Alertes de sécurité
                            </div>
                            <button onClick={() => setOpen(false)} className="text-gray-400 hover:text-gray-600">
                                <X className="w-4 h-4" />
                            </button>
                        </div>

                        <div className="p-3 space-y-2 max-h-96 overflow-y-auto">
                            {alerts.length === 0 ? (
                                <div className="py-6 text-center text-sm text-gray-400">Aucune alerte en cours</div>
                            ) : (
                                alerts.map(alert => (
                                    <AlertItem key={alert.id} alert={alert} onAction={handleAction} />
                                ))
                            )}
                        </div>

                        {alerts.length > 0 && (
                            <div className="px-3 pb-3">
                                <button
                                    onClick={async () => {
                                        for (const a of alerts) {
                                            try { await activityService.markSeen(a.id); } catch { /* ignore */ }
                                        }
                                        setAlerts([]);
                                        setOpen(false);
                                    }}
                                    className="w-full text-xs text-gray-500 py-1.5 border border-gray-200 rounded-lg hover:bg-gray-50 transition"
                                >
                                    Tout marquer comme lu
                                </button>
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
}
