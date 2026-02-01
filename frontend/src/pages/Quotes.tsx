import React, { useEffect, useState } from 'react';
import type { Quote, Partner } from '../types';
import { QuoteService } from '../services/quoteService';
import { PartnerService } from '../services/partnerService';
import { Trash2, Search, Filter, Truck, Train, Plane, Ship } from 'lucide-react';

const transportIcons: Record<string, React.ElementType> = {
    ROAD: Truck,
    RAIL: Train,
    AIR: Plane,
    SEA: Ship,
};

const transportLabels: Record<string, string> = {
    ROAD: 'Route',
    RAIL: 'Rail',
    AIR: 'Aérien',
    SEA: 'Maritime',
};

export const Quotes: React.FC = () => {
    const [quotes, setQuotes] = useState<Quote[]>([]);
    const [partners, setPartners] = useState<Partner[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterPartner, setFilterPartner] = useState('');
    const [filterMode, setFilterMode] = useState('');

    const fetchData = async () => {
        setLoading(true);
        try {
            const [quotesData, partnersData] = await Promise.all([
                QuoteService.getAll({
                    partner_id: filterPartner || undefined,
                    transport_mode: filterMode || undefined,
                }),
                PartnerService.getAll(),
            ]);
            setQuotes(quotesData);
            setPartners(partnersData);
        } catch (error) {
            console.error("Failed to fetch data", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [filterPartner, filterMode]);

    const handleDelete = async (id: string) => {
        if (window.confirm("Supprimer ce tarif ?")) {
            try {
                await QuoteService.delete(id);
                fetchData();
            } catch (error) {
                console.error("Failed to delete quote", error);
                alert("Erreur lors de la suppression");
            }
        }
    };

    const getPartnerName = (partnerId: string) => {
        const partner = partners.find(p => p.id === partnerId);
        return partner ? partner.name : partnerId;
    };

    const filteredQuotes = quotes.filter(q =>
        q.origin_city.toLowerCase().includes(searchTerm.toLowerCase()) ||
        q.dest_city.toLowerCase().includes(searchTerm.toLowerCase()) ||
        q.origin_country.toLowerCase().includes(searchTerm.toLowerCase()) ||
        q.dest_country.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Tarifs</h1>
                    <p className="mt-1 text-sm text-gray-500">
                        {filteredQuotes.length} tarif(s) en base de donnees
                    </p>
                </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                {/* Filters */}
                <div className="p-4 border-b border-gray-100 bg-gray-50/50">
                    <div className="flex flex-wrap gap-4">
                        <div className="relative flex-1 min-w-[200px]">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                            <input
                                type="text"
                                placeholder="Rechercher par ville ou pays..."
                                className="pl-10 w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm py-2"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>
                        <div className="flex items-center gap-2">
                            <Filter className="w-4 h-4 text-gray-400" />
                            <select
                                className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm py-2"
                                value={filterPartner}
                                onChange={(e) => setFilterPartner(e.target.value)}
                            >
                                <option value="">Tous les partenaires</option>
                                {partners.map(p => (
                                    <option key={p.id} value={p.id}>{p.name}</option>
                                ))}
                            </select>
                            <select
                                className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm py-2"
                                value={filterMode}
                                onChange={(e) => setFilterMode(e.target.value)}
                            >
                                <option value="">Tous les modes</option>
                                <option value="ROAD">Route</option>
                                <option value="RAIL">Rail</option>
                                <option value="AIR">Aerien</option>
                                <option value="SEA">Maritime</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* Table */}
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Mode</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Origine</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Destination</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Poids (kg)</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Prix</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Delai</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Partenaire</th>
                                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {loading ? (
                                <tr>
                                    <td colSpan={8} className="px-6 py-8 text-center text-gray-500">
                                        Chargement des donnees...
                                    </td>
                                </tr>
                            ) : filteredQuotes.length > 0 ? (
                                filteredQuotes.slice(0, 100).map((quote) => {
                                    const ModeIcon = transportIcons[quote.transport_mode] || Truck;
                                    return (
                                        <tr key={quote.id} className="hover:bg-gray-50 transition-colors">
                                            <td className="px-4 py-3 whitespace-nowrap">
                                                <div className="flex items-center gap-2">
                                                    <ModeIcon className="w-4 h-4 text-gray-400" />
                                                    <span className="text-sm text-gray-600">
                                                        {transportLabels[quote.transport_mode] || quote.transport_mode}
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="px-4 py-3 whitespace-nowrap">
                                                <div className="text-sm font-medium text-gray-900">{quote.origin_city}</div>
                                                <div className="text-xs text-gray-500">{quote.origin_country}</div>
                                            </td>
                                            <td className="px-4 py-3 whitespace-nowrap">
                                                <div className="text-sm font-medium text-gray-900">{quote.dest_city}</div>
                                                <div className="text-xs text-gray-500">{quote.dest_country}</div>
                                            </td>
                                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                                                {quote.weight_min} - {quote.weight_max}
                                            </td>
                                            <td className="px-4 py-3 whitespace-nowrap">
                                                <span className="text-sm font-semibold text-green-600">
                                                    {Number(quote.cost).toFixed(2)} {quote.currency}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                                                {quote.delivery_time || '-'}
                                            </td>
                                            <td className="px-4 py-3 whitespace-nowrap">
                                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                                    {getPartnerName(quote.partner_id)}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 whitespace-nowrap text-right">
                                                <button
                                                    onClick={() => handleDelete(quote.id)}
                                                    className="text-gray-400 hover:text-red-600 transition-colors"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </td>
                                        </tr>
                                    );
                                })
                            ) : (
                                <tr>
                                    <td colSpan={8} className="px-6 py-8 text-center text-gray-500">
                                        Aucun tarif trouve
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination info */}
                {filteredQuotes.length > 100 && (
                    <div className="px-4 py-3 border-t border-gray-100 bg-gray-50/50 text-sm text-gray-500">
                        Affichage des 100 premiers resultats sur {filteredQuotes.length}
                    </div>
                )}
            </div>
        </div>
    );
};
