import React, { useEffect, useState } from 'react';
import type { ImportJob, Partner } from '../types';
import { ImportService } from '../services/importService';
import { PartnerService } from '../services/partnerService';
import { UploadCloud, FileSpreadsheet, CheckCircle, AlertCircle, Clock, Loader2, RefreshCw } from 'lucide-react';

export const Imports: React.FC = () => {
    // State
    const [partners, setPartners] = useState<Partner[]>([]);
    const [selectedPartner, setSelectedPartner] = useState('');
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

    // Recent job state
    const [lastJob, setLastJob] = useState<ImportJob | null>(null);

    useEffect(() => {
        PartnerService.getAll().then(setPartners).catch(console.error);
    }, []);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file || !selectedPartner) return;

        setUploading(true);
        setMessage(null);
        try {
            const job = await ImportService.upload(selectedPartner, file);
            setLastJob(job);
            setMessage({ type: 'success', text: 'Fichier uploadé avec succès. Traitement démarré.' });

            // Start polling
            pollStatus(job.id);

        } catch {
            setMessage({ type: 'error', text: "Erreur lors de l'upload du fichier." });
        } finally {
            setUploading(false);
        }
    };

    const pollStatus = async (jobId: string) => {
        const interval = setInterval(async () => {
            try {
                const updatedJob = await ImportService.getJob(jobId);
                setLastJob(updatedJob);
                if (updatedJob.status === 'COMPLETED' || updatedJob.status === 'FAILED') {
                    clearInterval(interval);
                }
            } catch {
                clearInterval(interval);
            }
        }, 2000);
    };

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-8">Importation des Tarifs</h1>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Upload Section */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                    <div className="p-6 border-b border-gray-100 bg-gray-50/50">
                        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                            <UploadCloud className="w-5 h-5 text-blue-600" />
                            Nouvel Import
                        </h2>
                        <p className="text-sm text-gray-500 mt-1">Sélectionnez un partenaire et un fichier tarifaire.</p>
                    </div>

                    <div className="p-6">
                        <form onSubmit={handleUpload} className="space-y-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">Partenaire</label>
                                <select
                                    className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 py-2.5"
                                    value={selectedPartner}
                                    onChange={e => setSelectedPartner(e.target.value)}
                                    required
                                >
                                    <option value="">-- Sélectionner un partenaire --</option>
                                    {partners.map(p => (
                                        <option key={p.id} value={p.id}>{p.name} ({p.code})</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">Fichier Excel / CSV</label>
                                <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-lg hover:border-blue-400 transition-colors bg-gray-50/50">
                                    <div className="space-y-2 text-center">
                                        <div className="mx-auto h-12 w-12 text-gray-400">
                                            {file ? <FileSpreadsheet className="w-full h-full text-green-600" /> : <UploadCloud className="w-full h-full" />}
                                        </div>
                                        <div className="flex text-sm text-gray-600 justify-center">
                                            <label className="relative cursor-pointer rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none">
                                                <span>{file ? ' Changer le fichier' : 'Sélectionner un fichier'}</span>
                                                <input type="file" className="sr-only" onChange={handleFileChange} accept=".csv, .xlsx, .xls" />
                                            </label>
                                        </div>
                                        <p className="text-xs text-gray-500">
                                            {file ? file.name : "XLSX, XLS ou CSV jusqu'à 10MB"}
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={uploading || !file || !selectedPartner}
                                className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all"
                            >
                                {uploading ? (
                                    <>
                                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                        Traitement en cours...
                                    </>
                                ) : 'Lancer l\'importation'}
                            </button>

                            {message && (
                                <div className={`p-4 rounded-lg flex items-start gap-3 ${message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                                    {message.type === 'success' ? <CheckCircle className="w-5 h-5 flex-shrink-0" /> : <AlertCircle className="w-5 h-5 flex-shrink-0" />}
                                    <span className="text-sm font-medium">{message.text}</span>
                                </div>
                            )}
                        </form>
                    </div>
                </div>

                {/* Status Section */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                    <div className="p-6 border-b border-gray-100 bg-gray-50/50 flex justify-between items-center">
                        <div>
                            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                                <Clock className="w-5 h-5 text-purple-600" />
                                Dernier Job
                            </h2>
                            <p className="text-sm text-gray-500 mt-1">État du dernier traitement d'import.</p>
                        </div>
                        {lastJob && (
                            <button onClick={() => pollStatus(lastJob.id)} className="p-2 hover:bg-gray-200 rounded-full transition-colors" title="Actualiser">
                                <RefreshCw className="w-4 h-4 text-gray-600" />
                            </button>
                        )}
                    </div>

                    <div className="p-6">
                        {lastJob ? (
                            <div className="space-y-6">
                                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                                    <span className="text-sm font-mono text-gray-500">#{lastJob.id.split('-')[0]}</span>
                                    <StatusBadge status={lastJob.status} />
                                </div>

                                <div className="grid grid-cols-3 gap-4 text-center">
                                    <div className="p-4 rounded-lg border border-gray-100 bg-white shadow-sm">
                                        <div className="text-2xl font-bold text-gray-900">{lastJob.total_rows}</div>
                                        <div className="text-xs font-medium text-gray-500 uppercase mt-1">Lignes</div>
                                    </div>
                                    <div className="p-4 rounded-lg border border-green-100 bg-green-50 shadow-sm">
                                        <div className="text-2xl font-bold text-green-600">{lastJob.success_count}</div>
                                        <div className="text-xs font-medium text-green-700 uppercase mt-1">Succès</div>
                                    </div>
                                    <div className="p-4 rounded-lg border border-red-100 bg-red-50 shadow-sm">
                                        <div className="text-2xl font-bold text-red-600">{lastJob.error_count}</div>
                                        <div className="text-xs font-medium text-red-700 uppercase mt-1">Erreurs</div>
                                    </div>
                                </div>

                                {lastJob.errors && lastJob.errors.length > 0 && (
                                    <div className="mt-6">
                                        <h4 className="font-medium text-sm text-red-700 mb-3 flex items-center gap-2">
                                            <AlertCircle className="w-4 h-4" />
                                            Erreurs détectées
                                        </h4>
                                        <div className="bg-gray-900 rounded-lg p-4 overflow-auto max-h-60 shadow-inner">
                                            <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap">
                                                {JSON.stringify(lastJob.errors, null, 2)}
                                            </pre>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="text-center py-12">
                                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4">
                                    <Clock className="w-8 h-8 text-gray-400" />
                                </div>
                                <h3 className="text-lg font-medium text-gray-900">Aucune activité récente</h3>
                                <p className="text-gray-500 mt-1">Lancez un import pour voir le statut ici.</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

const StatusBadge = ({ status }: { status: string }) => {
    const config = {
        PENDING: { color: 'bg-yellow-100 text-yellow-800', icon: Clock, label: 'En attente' },
        PROCESSING: { color: 'bg-blue-100 text-blue-800', icon: Loader2, label: 'En cours' },
        COMPLETED: { color: 'bg-green-100 text-green-800', icon: CheckCircle, label: 'Terminé' },
        FAILED: { color: 'bg-red-100 text-red-800', icon: AlertCircle, label: 'Échoué' },
    };

    const { color, icon: Icon, label } = config[status as keyof typeof config] || { color: 'bg-gray-100 text-gray-800', icon: Clock, label: status };

    return (
        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${color}`}>
            <Icon className={`w-3.5 h-3.5 ${status === 'PROCESSING' ? 'animate-spin' : ''}`} />
            {label}
        </span>
    );
};
