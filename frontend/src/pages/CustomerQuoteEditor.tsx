import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useCustomerQuote } from '../context/CustomerQuoteContext';
import { ArrowLeft, Plus, Save, Calculator, User, Edit, Truck, Train, Plane, Ship } from 'lucide-react';
import { QuoteItemEditor } from '../components/customer-quote/editor/QuoteItemEditor';
import { AddFeeModal } from '../components/customer-quote/editor/AddFeeModal';
import { EditCustomerModal } from '../components/customer-quote/editor/EditCustomerModal';
import type { CustomerFormData } from '../components/customer-quote/editor/EditCustomerModal';

export const CustomerQuoteEditor: React.FC = () => {
    const { id } = useParams<{ id: string }>();

    // On utilise le context pour charger et manipuler ce devis
    // Attention : Le context gère "currentQuote", qui est généralement le panier en cours.
    // Ici on édite un devis spécifique. Il faut charger ce devis DANS le context pour bénéficier des méthodes d'update.
    const {
        currentQuote,
        loadQuote,
        updateQuote,
        loading,
        transportSubtotal,
        total,
        totalMargin,
        openSearchForQuote
    } = useCustomerQuote();

    const [isFeeModalOpen, setIsFeeModalOpen] = useState(false);
    const [isCustomerModalOpen, setIsCustomerModalOpen] = useState(false);
    const [selectedMode, setSelectedMode] = useState<'ROAD' | 'RAIL' | 'AIR' | 'SEA'>('ROAD');

    const transportModes: Array<{ value: 'ROAD' | 'RAIL' | 'AIR' | 'SEA'; label: string; icon: React.ReactNode }> = [
        { value: 'ROAD', label: 'Route', icon: <Truck className="w-4 h-4" /> },
        { value: 'RAIL', label: 'Rail', icon: <Train className="w-4 h-4" /> },
        { value: 'AIR', label: 'Aérien', icon: <Plane className="w-4 h-4" /> },
        { value: 'SEA', label: 'Maritime', icon: <Ship className="w-4 h-4" /> }
    ];

    const handleAddTransport = () => {
        openSearchForQuote(selectedMode);
    };

    const handleSaveCustomer = async (data: CustomerFormData) => {
        await updateQuote(data);
    };

    const getCustomerFormData = (): CustomerFormData => ({
        customer_name: currentQuote?.customer_name || '',
        customer_company: currentQuote?.customer_company || '',
        customer_email: currentQuote?.customer_email || '',
        valid_until: currentQuote?.valid_until?.split('T')[0] || ''
    });

    useEffect(() => {
        if (id && (!currentQuote || currentQuote.id !== id)) {
            loadQuote(id);
        }
    }, [id]);

    if (loading) return <div className="p-12 text-center text-gray-500">Chargement de l'éditeur...</div>;
    if (!currentQuote) return <div className="p-12 text-center text-red-500">Impossible de charger le devis.</div>;

    return (
        <div className="flex flex-col h-[calc(100vh-64px)] bg-gray-50">
            {/* Top Bar */}
            <div className="bg-white border-b border-gray-200 px-8 py-4 flex justify-between items-center shadow-sm z-10">
                <div className="flex items-center gap-4">
                    <Link to={`/customer-quotes/${currentQuote.id}`} className="p-2 hover:bg-gray-100 rounded-full text-gray-500 transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <div>
                        <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                            Éditeur de Devis <span className="text-gray-400 font-normal">| {currentQuote.reference}</span>
                        </h1>
                        <p className="text-sm text-gray-500">{currentQuote.customer_name || 'Sans client'} - {currentQuote.status}</p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <div className="text-right mr-6">
                        <div className="text-xs text-gray-500">Marge Totale</div>
                        <div className="text-green-600 font-bold">{totalMargin.toFixed(2)} €</div>
                    </div>
                    <div className="text-right mr-6 border-l pl-6">
                        <div className="text-xs text-gray-500">Total HT</div>
                        <div className="text-2xl font-bold text-gray-900">{total.toFixed(2)} €</div>
                    </div>

                    <button className="flex items-center space-x-2 bg-gray-900 text-white px-5 py-2.5 rounded-lg hover:bg-gray-800 transition-colors shadow-lg shadow-gray-900/10">
                        <Save className="w-4 h-4" />
                        <span>Enregistrer</span>
                    </button>
                </div>
            </div>

            {/* Workspace */}
            <div className="flex-1 overflow-y-auto p-8 max-w-5xl mx-auto w-full">

                {/* Customer Section */}
                <div className="mb-8">
                    <div className="flex justify-between items-end mb-4">
                        <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                            <User className="w-5 h-5 text-purple-600" />
                            Informations Client
                        </h2>
                        <button
                            onClick={() => setIsCustomerModalOpen(true)}
                            className="text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 px-3 py-1 rounded-lg transition-colors flex items-center gap-1"
                        >
                            <Edit className="w-4 h-4" />
                            Modifier
                        </button>
                    </div>

                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                            <div>
                                <div className="text-xs font-medium text-gray-500 mb-1">Nom du contact</div>
                                <div className="text-gray-900 font-medium">
                                    {currentQuote.customer_name || <span className="text-gray-400 italic">Non renseigné</span>}
                                </div>
                            </div>
                            <div>
                                <div className="text-xs font-medium text-gray-500 mb-1">Société</div>
                                <div className="text-gray-900">
                                    {currentQuote.customer_company || <span className="text-gray-400 italic">-</span>}
                                </div>
                            </div>
                            <div>
                                <div className="text-xs font-medium text-gray-500 mb-1">Email</div>
                                <div className="text-gray-900">
                                    {currentQuote.customer_email || <span className="text-gray-400 italic">-</span>}
                                </div>
                            </div>
                            <div>
                                <div className="text-xs font-medium text-gray-500 mb-1">Validité</div>
                                <div className="text-gray-900">
                                    {currentQuote.valid_until
                                        ? new Date(currentQuote.valid_until).toLocaleDateString()
                                        : <span className="text-gray-400 italic">Illimitée</span>
                                    }
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Transport Section */}
                <div className="mb-8">
                    <div className="flex justify-between items-end mb-4">
                        <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                            <Calculator className="w-5 h-5 text-blue-600" />
                            Prestations Transport
                        </h2>
                        <div className="text-sm font-medium text-gray-600">
                            Sous-total: {transportSubtotal.toFixed(2)} €
                        </div>
                    </div>

                    {currentQuote.items.filter(i => i.item_type === 'TRANSPORT').length === 0 ? (
                        <div className="text-center p-8 border-2 border-dashed border-gray-200 rounded-xl text-gray-400">
                            Aucune ligne de transport. Ajoutez des tarifs depuis la recherche.
                            {currentQuote.status === 'DRAFT' && (
                                <div className="mt-4 bg-white border border-gray-200 rounded-xl p-4">
                                    <div className="flex justify-center gap-2 mb-3">
                                        {transportModes.map(mode => (
                                            <button
                                                key={mode.value}
                                                onClick={() => setSelectedMode(mode.value)}
                                                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-all text-sm ${selectedMode === mode.value
                                                        ? 'bg-blue-50 border-blue-500 text-blue-700'
                                                        : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                                                    }`}
                                            >
                                                {mode.icon}
                                                <span className="font-medium">{mode.label}</span>
                                            </button>
                                        ))}
                                    </div>
                                    <button
                                        onClick={handleAddTransport}
                                        className="w-full py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm"
                                    >
                                        + Ajouter un transport
                                    </button>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {currentQuote.items.filter(i => i.item_type === 'TRANSPORT').map(item => (
                                <QuoteItemEditor key={item.id} item={item} />
                            ))}

                            {/* Transport Mode Selector + Add button */}
                            {currentQuote.status === 'DRAFT' && (
                                <div className="mt-2 bg-gray-50 border border-gray-200 rounded-xl p-4">
                                    <div className="flex justify-center gap-2 mb-3">
                                        {transportModes.map(mode => (
                                            <button
                                                key={mode.value}
                                                onClick={() => setSelectedMode(mode.value)}
                                                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-all text-sm ${selectedMode === mode.value
                                                        ? 'bg-blue-50 border-blue-500 text-blue-700'
                                                        : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                                                    }`}
                                            >
                                                {mode.icon}
                                                <span className="font-medium">{mode.label}</span>
                                            </button>
                                        ))}
                                    </div>
                                    <button
                                        onClick={handleAddTransport}
                                        className="w-full py-2.5 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-blue-400 hover:text-blue-600 hover:bg-white transition-colors font-medium text-sm"
                                    >
                                        + Ajouter un transport
                                    </button>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Fee Section */}
                <div className="mb-8">
                    <div className="flex justify-between items-end mb-4">
                        <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                            <Plus className="w-5 h-5 text-orange-600" />
                            Frais Annexes
                        </h2>
                        <button
                            onClick={() => setIsFeeModalOpen(true)}
                            className="text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 px-3 py-1 rounded-lg transition-colors"
                        >
                            + Ajouter un coût
                        </button>
                    </div>

                    {currentQuote.items.filter(i => i.item_type === 'FEE').length === 0 ? (
                        <div className="text-center p-6 bg-gray-50 rounded-xl text-sm text-gray-400">
                            Aucun frais additionnel.
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {currentQuote.items.filter(i => i.item_type === 'FEE').map(item => (
                                <QuoteItemEditor key={item.id} item={item} />
                            ))}
                        </div>
                    )}
                </div>

            </div>

            <AddFeeModal isOpen={isFeeModalOpen} onClose={() => setIsFeeModalOpen(false)} />
            <EditCustomerModal
                isOpen={isCustomerModalOpen}
                onClose={() => setIsCustomerModalOpen(false)}
                onSave={handleSaveCustomer}
                initialData={getCustomerFormData()}
            />
        </div>
    );
};
