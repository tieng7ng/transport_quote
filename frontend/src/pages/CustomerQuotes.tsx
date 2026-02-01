import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, FileText, Calendar, Search as SearchIcon, Eye, Trash2 } from 'lucide-react';
import { customerQuoteService } from '../services/customerQuoteService';
import { useCustomerQuote } from '../context/CustomerQuoteContext';
import type { CustomerQuote } from '../types/customerQuote';

export const CustomerQuotes: React.FC = () => {
    const navigate = useNavigate();
    const { createQuote } = useCustomerQuote();
    const [quotes, setQuotes] = useState<CustomerQuote[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadQuotes();
    }, []);

    const handleCreateQuote = async () => {
        try {
            const newQuote = await createQuote();
            navigate(`/customer-quotes/${newQuote.id}/edit`);
        } catch (error) {
            console.error("Failed to create quote", error);
        }
    };

    const loadQuotes = async () => {
        try {
            const data = await customerQuoteService.getAll();
            setQuotes(data);
        } catch (error) {
            console.error("Failed to load quotes", error);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteQuote = async (quoteId: string, e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();

        if (!confirm('Êtes-vous sûr de vouloir supprimer ce devis brouillon ?')) {
            return;
        }

        try {
            await customerQuoteService.delete(quoteId);
            setQuotes(quotes.filter(q => q.id !== quoteId));
        } catch (error) {
            console.error("Failed to delete quote", error);
            alert('Erreur lors de la suppression du devis');
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'DRAFT': return 'bg-gray-100 text-gray-800';
            case 'READY': return 'bg-blue-100 text-blue-800';
            case 'SENT': return 'bg-yellow-100 text-yellow-800';
            case 'ACCEPTED': return 'bg-green-100 text-green-800';
            case 'REJECTED': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    return (
        <div className="p-8 max-w-7xl mx-auto">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Devis Clients</h1>
                    <p className="text-gray-500 mt-1">Gérez vos propositions commerciales</p>
                </div>
                <button
                    onClick={handleCreateQuote}
                    className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
                >
                    <Plus className="w-5 h-5" />
                    <span>Nouveau Devis</span>
                </button>
            </div>

            {/* Filters / Search Bar (Placeholder) */}
            <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm mb-6 flex items-center space-x-4">
                <div className="relative flex-1 max-w-md">
                    <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                    <input
                        type="text"
                        placeholder="Rechercher par référence, client..."
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    />
                </div>
            </div>

            {/* List */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                {loading ? (
                    <div className="p-8 text-center text-gray-500">Chargement...</div>
                ) : quotes.length === 0 ? (
                    <div className="p-12 text-center">
                        <div className="mx-auto w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                            <FileText className="w-8 h-8 text-gray-400" />
                        </div>
                        <h3 className="text-lg font-medium text-gray-900">Aucun devis</h3>
                        <p className="text-gray-500 mt-1 mb-6">Commencez par créer une nouvelle recherche pour générer un devis.</p>
                        <Link to="/search" className="text-blue-600 hover:text-blue-700 font-medium">
                            Aller à la recherche &rarr;
                        </Link>
                    </div>
                ) : (
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-gray-50 border-b border-gray-200">
                                <th className="px-6 py-4 font-semibold text-gray-600 text-sm">Référence</th>
                                <th className="px-6 py-4 font-semibold text-gray-600 text-sm">Client</th>
                                <th className="px-6 py-4 font-semibold text-gray-600 text-sm">Date</th>
                                <th className="px-6 py-4 font-semibold text-gray-600 text-sm text-right">Montant HT</th>
                                <th className="px-6 py-4 font-semibold text-gray-600 text-sm text-center">Statut</th>
                                <th className="px-6 py-4 font-semibold text-gray-600 text-sm"></th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {quotes.map((quote) => (
                                <tr key={quote.id} className="hover:bg-gray-50 transition-colors group">
                                    <td className="px-6 py-4">
                                        <div className="font-medium text-gray-900">{quote.reference || 'Brouillon'}</div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="text-gray-900">{quote.customer_name || '-'}</div>
                                        <div className="text-xs text-gray-500">{quote.customer_company}</div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center text-gray-500 text-sm">
                                            <Calendar className="w-4 h-4 mr-2" />
                                            {new Date(quote.created_at).toLocaleDateString()}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-right font-medium text-gray-900">
                                        {quote.total.toFixed(2)} €
                                    </td>
                                    <td className="px-6 py-4 text-center">
                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(quote.status)}`}>
                                            {quote.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <div className="flex items-center justify-end gap-2">
                                            <Link
                                                to={`/customer-quotes/${quote.id}`}
                                                className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                                                title="Voir le devis"
                                            >
                                                <Eye className="w-5 h-5" />
                                            </Link>
                                            {quote.status === 'DRAFT' && (
                                                <button
                                                    onClick={(e) => handleDeleteQuote(quote.id, e)}
                                                    className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                                    title="Supprimer le brouillon"
                                                >
                                                    <Trash2 className="w-5 h-5" />
                                                </button>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
};
