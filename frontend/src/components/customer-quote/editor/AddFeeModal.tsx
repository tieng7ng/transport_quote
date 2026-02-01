import React, { useState } from 'react';
import { useCustomerQuote } from '../../../context/CustomerQuoteContext';
import { X } from 'lucide-react';

interface Props {
    isOpen: boolean;
    onClose: () => void;
}

export const AddFeeModal: React.FC<Props> = ({ isOpen, onClose }) => {
    const { addFee } = useCustomerQuote();
    const [description, setDescription] = useState('');
    const [price, setPrice] = useState('0');

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (description && price) {
            await addFee(description, parseFloat(price));
            onClose();
            setDescription('');
            setPrice('0');
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center backdrop-blur-sm">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden">
                <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                    <h3 className="font-bold text-gray-800">Ajouter un coût annexe</h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
                        <X className="w-5 h-5" />
                    </button>
                </div>
                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                        <input 
                            type="text" 
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="Ex: Frais de dossier, Douane..."
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                            autoFocus
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Montant (€)</label>
                        <input 
                            type="number" 
                            step="0.01"
                            value={price}
                            onChange={(e) => setPrice(e.target.value)}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                            required
                        />
                    </div>
                    <div className="pt-2 flex justify-end gap-3">
                        <button 
                            type="button" 
                            onClick={onClose}
                            className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg font-medium"
                        >
                            Annuler
                        </button>
                        <button 
                            type="submit"
                            className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 shadow-sm"
                        >
                            Ajouter
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};
