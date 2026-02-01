import React, { useEffect, useState } from 'react';
import type { Partner } from '../types';
import { PartnerService } from '../services/partnerService';
import { QuoteService } from '../services/quoteService';
import { Trash2, Plus, Edit2, Search, FileMinus } from 'lucide-react';

export const Partners: React.FC = () => {
    const [partners, setPartners] = useState<Partner[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    // Form state
    const [showModal, setShowModal] = useState(false);
    const [editingPartner, setEditingPartner] = useState<Partner | null>(null);
    const [formData, setFormData] = useState({ name: '', code: '', email: '' });

    const fetchPartners = async () => {
        try {
            const data = await PartnerService.getAll();
            setPartners(data);
        } catch (error) {
            console.error("Failed to fetch partners", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchPartners();
    }, []);

    // Delete Quotes Modal State
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [partnerToDeleteQuotes, setPartnerToDeleteQuotes] = useState<Partner | null>(null);
    const [quoteCount, setQuoteCount] = useState<number | null>(null);
    const [confirmCode, setConfirmCode] = useState('');

    const handleDelete = async (id: string) => {
        if (window.confirm("Êtes-vous sûr de vouloir supprimer ce partenaire ?")) {
            try {
                await PartnerService.delete(id);
                fetchPartners();
            } catch (error) {
                console.error("Failed to delete partner", error);
                alert("Erreur lors de la suppression");
            }
        }
    };

    const handleDeleteQuotesClick = async (partner: Partner) => {
        setPartnerToDeleteQuotes(partner);
        setQuoteCount(null);
        setShowDeleteModal(true);
        setConfirmCode('');

        // Fetch count
        try {
            const count = await QuoteService.getCount({ partner_id: partner.id });
            setQuoteCount(count);
        } catch (e) {
            console.error("Failed to fetch quote count", e);
            setQuoteCount(0); // Should probably show error state
        }
    };

    const confirmDeleteQuotes = async () => {
        if (!partnerToDeleteQuotes) return;
        if (confirmCode !== partnerToDeleteQuotes.code) {
            alert("Le code partenaire est incorrect.");
            return;
        }

        try {
            const result = await PartnerService.deleteQuotes(partnerToDeleteQuotes.id);
            alert(`Succès : ${result.count} tarifs supprimés.`);
            setShowDeleteModal(false);
            setPartnerToDeleteQuotes(null);
        } catch (error) {
            console.error("Failed to delete quotes", error);
            alert("Erreur lors de la suppression des tarifs");
        }
    };

    const handleEdit = (partner: Partner) => {
        setEditingPartner(partner);
        setFormData({ name: partner.name, code: partner.code, email: partner.email || '' });
        setShowModal(true);
    };

    const handleCreate = () => {
        setEditingPartner(null);
        setFormData({ name: '', code: '', email: '' });
        setShowModal(true);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            if (editingPartner) {
                await PartnerService.update(editingPartner.id, formData);
            } else {
                await PartnerService.create(formData);
            }
            setShowModal(false);
            fetchPartners();
        } catch (error) {
            console.error("Failed to save partner", error);
            alert("Erreur lors de l'enregistrement");
        }
    };

    const filteredPartners = partners.filter(p =>
        p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.code.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Partenaires</h1>
                    <p className="mt-1 text-sm text-gray-500">Gérez vos partenaires de transport et leurs configurations.</p>
                </div>
                <button
                    onClick={handleCreate}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 shadow-sm"
                >
                    <Plus className="w-5 h-5" />
                    Nouveau Partenaire
                </button>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="p-4 border-b border-gray-100 bg-gray-50/50">
                    <div className="relative max-w-sm">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                        <input
                            type="text"
                            placeholder="Rechercher un partenaire..."
                            className="pl-10 w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm py-2"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Code</th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Nom</th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Email</th>
                                <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {loading ? (
                                <tr><td colSpan={4} className="px-6 py-8 text-center text-gray-500">Chargement des données...</td></tr>
                            ) : filteredPartners.length > 0 ? (
                                filteredPartners.map((partner) => (
                                    <tr key={partner.id} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-blue-600">{partner.code}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{partner.name}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{partner.email || '-'}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                            <div className="flex justify-end gap-3">
                                                <button onClick={() => handleEdit(partner)} className="text-gray-400 hover:text-blue-600 transition-colors">
                                                    <Edit2 className="w-5 h-5" />
                                                </button>
                                                <button onClick={() => handleDelete(partner.id)} className="text-gray-400 hover:text-red-600 transition-colors" title="Supprimer le partenaire">
                                                    <Trash2 className="w-5 h-5" />
                                                </button>
                                                <button onClick={() => handleDeleteQuotesClick(partner)} className="text-gray-400 hover:text-orange-600 transition-colors" title="Supprimer tous les tarifs">
                                                    <FileMinus className="w-5 h-5" />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr><td colSpan={4} className="px-6 py-8 text-center text-gray-500">Aucun partenaire trouvé</td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Modal Create/Edit */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-xl shadow-xl w-full max-w-md transform transition-all">
                        <div className="p-6 border-b border-gray-100">
                            <h2 className="text-xl font-bold text-gray-900">
                                {editingPartner ? 'Modifier le Partenaire' : 'Ajouter un Partenaire'}
                            </h2>
                        </div>
                        <form onSubmit={handleSubmit} className="p-6">
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Code</label>
                                    <input
                                        required
                                        type="text"
                                        className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                        value={formData.code}
                                        onChange={e => setFormData({ ...formData, code: e.target.value })}
                                        placeholder="Ex: DHLE"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Nom</label>
                                    <input
                                        required
                                        type="text"
                                        className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                        value={formData.name}
                                        onChange={e => setFormData({ ...formData, name: e.target.value })}
                                        placeholder="Ex: DHL Express"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Email (optionnel)</label>
                                    <input
                                        type="email"
                                        className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                        value={formData.email}
                                        onChange={e => setFormData({ ...formData, email: e.target.value })}
                                        placeholder="contact@example.com"
                                    />
                                </div>
                            </div>
                            <div className="mt-8 flex justify-end gap-3">
                                <button
                                    type="button"
                                    onClick={() => setShowModal(false)}
                                    className="px-4 py-2 text-gray-700 hover:bg-gray-50 rounded-lg border border-gray-300 transition-colors"
                                >
                                    Annuler
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 shadow-sm transition-colors"
                                >
                                    {editingPartner ? 'Enregistrer' : 'Créer'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Modal Delete Quotes */}
            {showDeleteModal && partnerToDeleteQuotes && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-xl shadow-xl w-full max-w-lg transform transition-all border-t-8 border-red-500">
                        <div className="p-6">
                            <h2 className="text-xl font-bold text-gray-900 border-b pb-4 mb-4">Supprimer les tarifs</h2>

                            <div className="bg-red-50 text-red-800 p-4 rounded-lg mb-6 flex items-start">
                                <span className="text-2xl mr-3">⚠️</span>
                                <div>
                                    <p className="font-bold">Attention : Cette action est irréversible !</p>
                                    <p className="mt-1 text-sm">Vous êtes sur le point de supprimer tous les tarifs du partenaire <span className="font-bold">"{partnerToDeleteQuotes.name}"</span>.</p>
                                </div>
                            </div>

                            <p className="mb-4 text-center">
                                Nombre de tarifs concernés : <span className="font-bold">{quoteCount !== null ? quoteCount.toLocaleString() : 'Chargement...'}</span>
                            </p>

                            <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Pour confirmer, tapez le code du partenaire : <span className="font-bold font-mono text-gray-900">{partnerToDeleteQuotes.code}</span>
                                </label>
                                <input
                                    type="text"
                                    className="w-full rounded-lg border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 font-mono"
                                    value={confirmCode}
                                    onChange={e => setConfirmCode(e.target.value)}
                                    placeholder="Code partenaire"
                                />
                            </div>

                            <div className="flex justify-between items-center mt-8">
                                <button
                                    onClick={() => setShowDeleteModal(false)}
                                    className="px-6 py-2 text-gray-700 hover:bg-gray-100 rounded-lg border border-gray-300 transition-colors"
                                >
                                    Annuler
                                </button>
                                <button
                                    onClick={confirmDeleteQuotes}
                                    disabled={confirmCode !== partnerToDeleteQuotes.code}
                                    className={`px-6 py-2 text-white rounded-lg shadow-sm transition-colors ${confirmCode === partnerToDeleteQuotes.code
                                        ? 'bg-red-600 hover:bg-red-700'
                                        : 'bg-red-300 cursor-not-allowed'
                                        }`}
                                >
                                    Supprimer
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
