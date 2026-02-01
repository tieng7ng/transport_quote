import React from 'react';
import { useCustomerQuote } from '../../context/CustomerQuoteContext';
import { X, Trash2, ShoppingCart, FileText, Truck, Plus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const QuoteSidebar: React.FC = () => {
    const {
        isSidebarOpen,
        closeSidebar,
        currentQuote,
        removeItem,
        clearQuote,
        openSearchModal
    } = useCustomerQuote();

    const navigate = useNavigate();

    // If needed to override specific styles or check mobile, we can do it here.
    if (!isSidebarOpen) return null;

    const handleCheckout = () => {
        if (currentQuote) {
            navigate(`/customer-quotes/${currentQuote.id}/edit`);
            closeSidebar();
        }
    };

    const handleSearch = () => {
        openSearchModal();
        // On mobile we might want to close sidebar, but on desktop it's fine to keep it
    };

    return (
        <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-2xl transform transition-transform duration-300 ease-in-out z-50 flex flex-col font-sans border-l border-gray-200">
            {/* Header */}
            <div className="p-4 bg-gray-900 text-white flex justify-between items-center shadow-md">
                <div className="flex items-center space-x-2">
                    <ShoppingCart className="h-5 w-5" />
                    <h2 className="text-lg font-semibold">Mon Devis</h2>
                </div>
                <button onClick={closeSidebar} className="p-1 hover:bg-gray-800 rounded-full transition-colors">
                    <X className="h-5 w-5" />
                </button>
            </div>

            {/* Body - List Items */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
                {!currentQuote || currentQuote.items.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-gray-400 space-y-4">
                        <ShoppingCart className="w-12 h-12 opacity-20" />
                        <p className="text-center font-medium">Votre devis est vide</p>
                        <button
                            onClick={handleSearch}
                            className="text-blue-600 font-medium hover:underline text-sm"
                        >
                            Ajouter un trajet
                        </button>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {/* Transport Items */}
                        {currentQuote.items.filter(i => i.item_type === 'TRANSPORT').map((item) => (
                            <div key={item.id} className="bg-white p-3 rounded-lg shadow-sm border border-gray-100 relative group">
                                <button
                                    onClick={() => removeItem(item.id)}
                                    className="absolute top-2 right-2 text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all p-1"
                                    title="Retirer"
                                >
                                    <Trash2 className="h-4 w-4" />
                                </button>
                                <div className="pr-6">
                                    <div className="flex items-center space-x-2 mb-1">
                                        <Truck className="h-3 w-3 text-blue-500" />
                                        <span className="text-xs font-bold text-gray-500">TRANSPORT</span>
                                    </div>
                                    <div className="text-sm font-medium text-gray-900">
                                        {item.origin_city} → {item.dest_city}
                                    </div>
                                    <div className="text-xs text-gray-500 mt-1">
                                        {item.partner_name} • {item.transport_mode} • {item.weight} kg
                                    </div>

                                    <div className="mt-2 text-right">
                                        <div className="font-bold text-gray-900">{item.sell_price.toFixed(2)} €</div>
                                    </div>
                                </div>
                            </div>
                        ))}

                        {/* Fee Items */}
                        {currentQuote.items.filter(i => i.item_type === 'FEE').map((item) => (
                            <div key={item.id} className="bg-white p-3 rounded-lg shadow-sm border border-gray-100 relative group">
                                <button
                                    onClick={() => removeItem(item.id)}
                                    className="absolute top-2 right-2 text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all p-1"
                                >
                                    <Trash2 className="h-4 w-4" />
                                </button>
                                <div className="pr-6">
                                    <div className="flex items-center space-x-2 mb-1">
                                        <FileText className="h-3 w-3 text-orange-500" />
                                        <span className="text-xs font-bold text-gray-500">FRAIS</span>
                                    </div>
                                    <div className="text-sm font-medium text-gray-900">{item.description}</div>
                                    <div className="mt-2 text-right">
                                        <div className="font-bold text-gray-900">{item.sell_price.toFixed(2)} €</div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Footer - Totals & Actions */}
            <div className="p-4 bg-white border-t border-gray-200 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]">
                {currentQuote && currentQuote.items.length > 0 && (
                    <div className="space-y-1 mb-4 text-sm">
                        <div className="flex justify-between text-gray-600">
                            <span>Total HT</span>
                            <span className="font-bold text-gray-900">{currentQuote.total.toFixed(2)} €</span>
                        </div>
                        <div className="flex justify-between text-xs text-green-600">
                            <span>Marge estimée</span>
                            <span>{currentQuote.total_margin.toFixed(2)} €</span>
                        </div>
                    </div>
                )}

                <div className="space-y-3">
                    <button
                        onClick={handleSearch}
                        className="w-full flex items-center justify-center gap-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-2 px-4 rounded-lg transition-colors border border-gray-200"
                    >
                        <Plus className="w-4 h-4" />
                        <span>Ajouter un trajet</span>
                    </button>

                    {currentQuote && currentQuote.items.length > 0 && (
                        <div className="grid grid-cols-2 gap-3">
                            <button
                                onClick={clearQuote}
                                className="px-4 py-2 text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-md transition-colors border border-red-100"
                            >
                                Vider
                            </button>
                            <button
                                onClick={handleCheckout}
                                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md shadow-sm transition-all flex justify-center items-center space-x-2"
                            >
                                <span>Finaliser</span>
                                <FileText className="h-4 w-4" />
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

