import React, { useState, useEffect } from 'react';
import type { CustomerQuoteItem } from '../../../types/customerQuote';
import { useCustomerQuote } from '../../../context/CustomerQuoteContext';
import { Trash2, RefreshCw } from 'lucide-react';

interface Props {
    item: CustomerQuoteItem;
}

export const QuoteItemEditor: React.FC<Props> = ({ item }) => {
    const { updateItemMargin, updateItemPrice, removeItem } = useCustomerQuote();

    // Local state for smooth editing without jitter before API sync
    const [margin, setMargin] = useState(item.margin_percent || 0);
    const [price, setPrice] = useState(item.sell_price || 0);
    const [description, setDescription] = useState(item.description);

    useEffect(() => {
        setMargin(item.margin_percent || 0);
        setPrice(item.sell_price || 0);
        setDescription(item.description);
    }, [item]);

    const handleMarginChange = async (newMargin: number) => {
        setMargin(newMargin);
        await updateItemMargin(item.id, newMargin);
    };

    const handlePriceChange = async (newPrice: number) => {
        setPrice(newPrice);
        await updateItemPrice(item.id, newPrice);
    };

    return (
        <div className="bg-white border boundary-gray-200 rounded-lg p-4 flex items-center justify-between gap-4 mb-3 shadow-sm hover:shadow-md transition-shadow">

            {/* Description & Info */}
            <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                    {item.item_type === 'TRANSPORT' ? (
                        <span className="bg-blue-100 text-blue-700 text-xs font-bold px-2 py-0.5 rounded">TRANSPORT</span>
                    ) : (
                        <span className="bg-orange-100 text-orange-700 text-xs font-bold px-2 py-0.5 rounded">FRAIS</span>
                    )}
                    <span className="font-medium text-gray-900">{description}</span>
                </div>
                {item.item_type === 'TRANSPORT' && (
                    <div className="text-xs text-gray-500 flex gap-3 mt-1">
                        <span>{item.transport_mode}</span>
                        <span>•</span>
                        <span>{item.weight} kg</span>
                        <span>•</span>
                        <span>Coût: {item.cost_price.toFixed(2)} €</span>
                    </div>
                )}
            </div>

            {/* Editor Controls */}
            <div className="flex items-center gap-6 bg-gray-50 p-2 rounded-lg border border-gray-100">

                {/* Marge Editor */}
                <div className="text-center">
                    <label className="block text-xs text-gray-400 mb-1 font-medium">Marge %</label>
                    <div className="relative">
                        <input
                            type="number"
                            step="0.1"
                            value={margin}
                            onChange={(e) => handleMarginChange(parseFloat(e.target.value) || 0)}
                            className="w-20 text-center font-bold text-gray-700 bg-white border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none text-sm py-1"
                        />
                        <span className="absolute right-1 top-1.5 text-xs text-gray-400">%</span>
                    </div>
                </div>

                <div className="text-gray-300">
                    <RefreshCw className="w-4 h-4" />
                </div>

                {/* Price Editor */}
                <div className="text-center">
                    <label className="block text-xs text-gray-400 mb-1 font-medium">Prix Vente</label>
                    <div className="relative">
                        <input
                            type="number"
                            step="0.01"
                            value={price}
                            onChange={(e) => handlePriceChange(parseFloat(e.target.value) || 0)}
                            className="w-24 text-center font-bold text-blue-600 bg-white border border-blue-200 rounded focus:ring-2 focus:ring-blue-500 outline-none text-sm py-1"
                        />
                        <span className="absolute right-2 top-1.5 text-xs text-gray-400">€</span>
                    </div>
                </div>
            </div>

            {/* Margin Amount Display */}
            <div className="text-right w-24">
                <div className="text-xs text-gray-400 mb-1">Marge €</div>
                <div className="font-medium text-green-600">+{item.margin_amount.toFixed(2)} €</div>
            </div>

            {/* Actions */}
            <button
                onClick={() => removeItem(item.id)}
                className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                title="Supprimer"
            >
                <Trash2 className="w-5 h-5" />
            </button>
        </div>
    );
};
