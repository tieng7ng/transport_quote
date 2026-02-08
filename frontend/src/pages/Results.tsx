import React, { useMemo } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { useCustomerQuote } from '../context/CustomerQuoteContext';
import { Truck, Calendar, MapPin, Package, Clock, PlusCircle, CheckCircle, Trash2, Search } from 'lucide-react';
import { PriceBreakdownPanel } from '../components/ui/PriceBreakdown';
import type { Quote, SearchCriteria } from '../types';

const getCountryName = (code: string) => {
    try {
        return new Intl.DisplayNames(['fr'], { type: 'region' }).of(code);
    } catch {
        return code;
    }
};

const formatLocation = (countryCode: string, postalCode?: string, city?: string) => {
    const country = getCountryName(countryCode);
    const parts = [];
    if (city) parts.push(city);
    if (postalCode) parts.push(postalCode);
    parts.push(country);
    return parts.join(', '); // Ex: Lyon, 69000, France
};

interface LocationState {
    results: Quote[];
    criteria: SearchCriteria;
}


export const Results: React.FC = () => {
    const location = useLocation();
    const state = location.state as LocationState;
    const { results = [], criteria } = state || {};
    const { addItem, currentQuote, removeItem, openSidebar, searchMode, openSearchForConsultation } = useCustomerQuote();

    const quoteItemsMap = useMemo(() => {
        const map = new Map<string, string>(); // partner_quote_id -> item_id
        if (currentQuote) {
            currentQuote.items.forEach(item => {
                if (item.partner_quote_id) {
                    map.set(item.partner_quote_id, item.id);
                }
            });
        }
        return map;
    }, [currentQuote]);


    const handleAdd = async (quoteId: string, weight: number) => {
        await addItem(quoteId, weight);
        openSidebar(); // Open sidebar to show it happened
    };

    if (!state) {
        return (
            <div className="p-8 text-center text-gray-500">
                <p>Aucun résultat à afficher. Veuillez effectuer une recherche.</p>
                <button
                    onClick={openSearchForConsultation}
                    className="text-blue-600 hover:underline mt-4 inline-flex items-center gap-2"
                >
                    <Search className="w-4 h-4" /> Nouvelle recherche
                </button>
            </div>
        );
    }

    const isQuoteMode = searchMode === 'quote';

    return (
        <div className="max-w-full mx-auto p-6">
            {/* Active Quote Banner */}
            {isQuoteMode && currentQuote && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="bg-blue-100 p-2 rounded-full">
                            <Package className="w-5 h-5 text-blue-600" />
                        </div>
                        <div>
                            <p className="text-sm text-blue-800 font-medium">Devis en cours : {currentQuote.reference}</p>
                            <p className="text-xs text-blue-600">{currentQuote.customer_name || 'Client non assigné'}</p>
                        </div>
                    </div>
                    <Link to={`/customer-quotes/${currentQuote.id}/edit`} className="text-sm font-medium text-blue-700 hover:text-blue-900 hover:underline">
                        Retourner au devis →
                    </Link>
                </div>
            )}

            <div className="mb-8">
                <button
                    onClick={openSearchForConsultation}
                    className="inline-flex items-center text-gray-500 hover:text-gray-900 mb-4 transition-colors"
                >
                    <Search className="w-4 h-4 mr-2" /> Nouvelle recherche
                </button>
                <div className="flex justify-between items-end">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">
                            {results.length} offre(s) correspondante(s)
                            {!isQuoteMode && <span className="ml-2 text-sm font-normal text-gray-500">(Mode Consultation)</span>}
                        </h1>
                        <p className="mt-2 text-gray-600 flex items-center gap-2 text-sm">
                            <MapPin className="w-4 h-4" />
                            <span className="font-medium">
                                {formatLocation(criteria.origin_country, criteria.origin_postal_code, criteria.origin_city)}
                            </span>
                            <span className="text-gray-400">→</span>
                            <MapPin className="w-4 h-4" />
                            <span className="font-medium">
                                {formatLocation(criteria.dest_country, criteria.dest_postal_code, criteria.dest_city)}
                            </span>
                            <span className="mx-2">|</span>
                            <Package className="w-4 h-4" /> {criteria.weight} kg
                        </p>
                    </div>
                </div>
            </div>

            <div className="space-y-4">
                {results.map((quote) => {
                    const existingItemId = quoteItemsMap.get(quote.id);
                    const isAdded = !!existingItemId;

                    return (
                        <div key={quote.id} className={`bg-white rounded-xl shadow-sm border ${isAdded ? 'border-green-500 ring-1 ring-green-500' : 'border-gray-100'} p-6 hover:shadow-md transition-all relative overflow-hidden group`}>
                            {isAdded && (
                                <div className="absolute top-0 right-0 bg-green-500 text-white text-xs px-2 py-1 rounded-bl-lg font-bold flex items-center gap-1">
                                    <CheckCircle className="w-3 h-3" /> Ajouté
                                </div>
                            )}

                            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">

                                {/* Transporteur Info */}
                                <div className="flex items-start gap-4">
                                    <div className={`p-3 rounded-lg ${isAdded ? 'bg-green-50 text-green-600' : 'bg-blue-50 text-blue-600'}`}>
                                        <Truck className="w-6 h-6" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-gray-900 text-lg">{quote.partner?.name || 'Transporteur Inconnu'}</h3>
                                        <div className="flex flex-wrap gap-2 mt-1">
                                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                                {quote.transport_mode}
                                            </span>
                                            {quote.weight_min !== null && quote.weight_max !== null && (
                                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700">
                                                    {quote.weight_min} - {quote.weight_max} kg
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {/* Details */}
                                <div className="flex flex-wrap gap-6 text-sm text-gray-600">
                                    <div className="flex items-center gap-2">
                                        <MapPin className="w-4 h-4 text-gray-400" />
                                        <span>dest: <span className="font-semibold text-gray-900">
                                            {quote.dest_city === 'ALL' ? `Dept ${quote.dest_postal_code}` : quote.dest_city}
                                        </span></span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Clock className="w-4 h-4 text-gray-400" />
                                        <span>transit: <span className="font-semibold text-gray-900">{quote.delivery_time || '-'}</span></span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Calendar className="w-4 h-4 text-gray-400" />
                                        <span>validité: <span className="font-semibold text-gray-900">{quote.valid_until || 'illimitée'}</span></span>
                                    </div>
                                </div>

                                {/* Prix & Action */}
                                <div className="flex items-center gap-6 w-full md:w-auto mt-4 md:mt-0 pt-4 md:pt-0 border-t md:border-0 border-gray-100">
                                    <div className="text-right">
                                        <p className="text-xs text-gray-500 mb-1">Prix estimé</p>
                                        <p className="text-2xl font-bold text-gray-900">{quote.cost} {quote.currency}</p>
                                        {quote.price_breakdown && (
                                            <PriceBreakdownPanel breakdown={quote.price_breakdown} currency={quote.currency} />
                                        )}
                                    </div>

                                    {/* Only show actions in Quote Mode */}
                                    {isQuoteMode ? (
                                        isAdded ? (
                                            <button
                                                onClick={() => removeItem(existingItemId!)}
                                                className="bg-red-50 text-red-600 px-6 py-3 rounded-lg font-medium hover:bg-red-100 transition-colors flex items-center gap-2"
                                            >
                                                <Trash2 className="w-5 h-5" />
                                                Retirer
                                            </button>
                                        ) : (
                                            <button
                                                onClick={() => handleAdd(quote.id, criteria.weight)}
                                                className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors shadow-lg shadow-blue-500/20 flex items-center gap-2"
                                            >
                                                <PlusCircle className="w-5 h-5" />
                                                Ajouter au devis
                                            </button>
                                        )
                                    ) : (
                                        <div className="text-xs text-gray-400 italic px-4">
                                            Mode consultation
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};
