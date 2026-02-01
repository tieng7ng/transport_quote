import React, { useState, useEffect } from 'react';
import { X, User } from 'lucide-react';

interface EditCustomerModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (data: CustomerFormData) => Promise<void>;
    initialData: CustomerFormData;
}

export interface CustomerFormData {
    customer_name: string;
    customer_company: string;
    customer_email: string;
    valid_until: string;
}

export const EditCustomerModal: React.FC<EditCustomerModalProps> = ({
    isOpen,
    onClose,
    onSave,
    initialData
}) => {
    const [formData, setFormData] = useState<CustomerFormData>(initialData);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (isOpen) {
            setFormData(initialData);
        }
    }, [isOpen, initialData]);

    if (!isOpen) return null;

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            await onSave(formData);
            onClose();
        } catch (error) {
            console.error('Failed to save customer info', error);
            alert('Erreur lors de la sauvegarde');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[70] overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            {/* Backdrop */}
            <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                <div
                    className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
                    aria-hidden="true"
                    onClick={onClose}
                ></div>

                <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

                <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                    <form onSubmit={handleSubmit}>
                        <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                            <div className="flex justify-between items-center mb-6">
                                <h3 className="text-lg leading-6 font-medium text-gray-900 flex items-center gap-2" id="modal-title">
                                    <User className="w-5 h-5 text-blue-600" />
                                    Modifier les informations client
                                </h3>
                                <button
                                    type="button"
                                    onClick={onClose}
                                    className="text-gray-400 hover:text-gray-500"
                                >
                                    <X className="h-6 w-6" />
                                </button>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <label htmlFor="customer_name" className="block text-sm font-medium text-gray-700 mb-1">
                                        Nom du contact *
                                    </label>
                                    <input
                                        type="text"
                                        id="customer_name"
                                        name="customer_name"
                                        value={formData.customer_name}
                                        onChange={handleChange}
                                        className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                        placeholder="Ex: Jean Dupont"
                                        required
                                    />
                                </div>

                                <div>
                                    <label htmlFor="customer_company" className="block text-sm font-medium text-gray-700 mb-1">
                                        Société
                                    </label>
                                    <input
                                        type="text"
                                        id="customer_company"
                                        name="customer_company"
                                        value={formData.customer_company}
                                        onChange={handleChange}
                                        className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                        placeholder="Ex: SARL ABC"
                                    />
                                </div>

                                <div>
                                    <label htmlFor="customer_email" className="block text-sm font-medium text-gray-700 mb-1">
                                        Email
                                    </label>
                                    <input
                                        type="email"
                                        id="customer_email"
                                        name="customer_email"
                                        value={formData.customer_email}
                                        onChange={handleChange}
                                        className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                        placeholder="Ex: contact@abc.fr"
                                    />
                                </div>

                                <div>
                                    <label htmlFor="valid_until" className="block text-sm font-medium text-gray-700 mb-1">
                                        Date de validité
                                    </label>
                                    <input
                                        type="date"
                                        id="valid_until"
                                        name="valid_until"
                                        value={formData.valid_until}
                                        onChange={handleChange}
                                        className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse gap-3">
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full inline-flex justify-center rounded-lg border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:w-auto sm:text-sm disabled:opacity-50"
                            >
                                {loading ? 'Enregistrement...' : 'Enregistrer'}
                            </button>
                            <button
                                type="button"
                                onClick={onClose}
                                className="mt-3 w-full inline-flex justify-center rounded-lg border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:w-auto sm:text-sm"
                            >
                                Annuler
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};
