import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { customerQuoteService } from '../services/customerQuoteService';
import type { CustomerQuote } from '../types/customerQuote';
import { ArrowLeft, Printer, Send, Edit, FileText, Truck } from 'lucide-react';

export const CustomerQuoteDetail: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [quote, setQuote] = useState<CustomerQuote | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (id) {
            loadQuote(id);
        }
    }, [id]);

    const loadQuote = async (quoteId: string) => {
        try {
            const data = await customerQuoteService.getById(quoteId);
            setQuote(data);
        } catch (error) {
            console.error("Failed to load quote", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="p-8 text-center text-gray-500">Chargement...</div>;
    if (!quote) return <div className="p-8 text-center text-red-500">Devis introuvable</div>;

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
        <div className="max-w-5xl mx-auto p-8">
            {/* Header */}
            <div className="flex justify-between items-start mb-8">
                <div>
                    <Link to="/customer-quotes" className="text-gray-500 hover:text-gray-900 flex items-center mb-4 transition-colors">
                        <ArrowLeft className="w-4 h-4 mr-2" /> Retour à la liste
                    </Link>
                    <div className="flex items-center gap-4">
                        <h1 className="text-3xl font-bold text-gray-900">{quote.reference || 'Devis Brouillon'}</h1>
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(quote.status)}`}>
                            {quote.status}
                        </span>
                    </div>
                </div>
                <div className="flex gap-3">
                    <button className="flex items-center space-x-2 bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors">
                        <Printer className="w-4 h-4" />
                        <span>Imprimer</span>
                    </button>
                    <button className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors shadow-sm">
                        <Send className="w-4 h-4" />
                        <span>Envoyer</span>
                    </button>
                    <button
                        onClick={() => navigate(`/customer-quotes/${quote.id}/edit`)}
                        className="flex items-center space-x-2 bg-gray-900 text-white px-4 py-2 rounded-lg hover:bg-gray-800 transition-colors shadow-sm"
                    >
                        <Edit className="w-4 h-4" />
                        <span>Éditer</span>
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-3 gap-8">
                {/* Main Content */}
                <div className="col-span-2 space-y-6">

                    {/* Items List */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                        <div className="p-6 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
                            <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                                <FileText className="w-5 h-5 text-gray-500" />
                                Détail des prestations
                            </h3>
                            <span className="text-sm text-gray-500">{quote.items.length} lignes</span>
                        </div>
                        <div className="divide-y divide-gray-100">
                            {quote.items.map((item) => (
                                <div key={item.id} className="p-6 hover:bg-gray-50 transition-colors">
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-1">
                                                {item.item_type === 'TRANSPORT' ? (
                                                    <span className="bg-blue-100 text-blue-700 text-xs font-bold px-2 py-0.5 rounded">TRANSPORT</span>
                                                ) : (
                                                    <span className="bg-orange-100 text-orange-700 text-xs font-bold px-2 py-0.5 rounded">FRAIS</span>
                                                )}
                                                <h4 className="font-medium text-gray-900">{item.description}</h4>
                                            </div>

                                            {item.item_type === 'TRANSPORT' && (
                                                <div className="text-sm text-gray-500 mt-2 space-y-1 ml-1">
                                                    <div className="flex items-center gap-2">
                                                        <Truck className="w-3 h-3" />
                                                        <span>{item.transport_mode} - {item.partner_name}</span>
                                                    </div>
                                                    <div className="pl-5">
                                                        {item.origin_city}, {item.origin_country} &rarr; {item.dest_city}, {item.dest_country}
                                                    </div>
                                                    <div className="pl-5">
                                                        Poids: {item.weight} kg | Délai: {item.delivery_time}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                        <div className="text-right">
                                            <div className="text-lg font-bold text-gray-900">{item.sell_price.toFixed(2)} €</div>
                                            <div className="text-xs text-green-600 mt-1">
                                                Marge: {item.margin_percent}% ({item.margin_amount.toFixed(2)} €)
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Sidebar Summary */}
                <div className="col-span-1 space-y-6">
                    {/* Client Info */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">Client</h3>
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center text-gray-500 font-bold">
                                {(quote.customer_name?.[0] || '?')}
                            </div>
                            <div>
                                <div className="font-medium text-gray-900">{quote.customer_name || 'Client non renseigné'}</div>
                                <div className="text-sm text-gray-500">{quote.customer_company}</div>
                            </div>
                        </div>
                        <div className="text-sm text-gray-500 space-y-2 pt-4 border-t border-gray-100">
                            <div>Email: {quote.customer_email || '-'}</div>
                            <div>Validité: {quote.valid_until ? new Date(quote.valid_until).toLocaleDateString() : 'Illimitée'}</div>
                        </div>
                    </div>

                    {/* Totals */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">Récapitulatif</h3>
                        <div className="space-y-3 text-sm">
                            <div className="flex justify-between text-gray-600">
                                <span>Total Transport</span>
                                <span>{quote.transport_subtotal.toFixed(2)} €</span>
                            </div>
                            <div className="flex justify-between text-gray-600">
                                <span>Total Frais</span>
                                <span>{quote.fees_total.toFixed(2)} €</span>
                            </div>
                            <div className="pt-3 border-t border-gray-100 flex justify-between items-center">
                                <span className="text-base font-bold text-gray-900">Total HT</span>
                                <span className="text-xl font-bold text-blue-600">{quote.total.toFixed(2)} €</span>
                            </div>
                            <div className="pt-2 flex justify-between text-xs text-green-600">
                                <span>Marge Totale</span>
                                <span>{quote.total_margin.toFixed(2)} €</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
