import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search as SearchIcon, Truck, Package, Calendar, MapPin, X, Train, Plane, Ship, ArrowLeft } from 'lucide-react';
import { QuoteService } from '../services/quoteService';
import { CityAutocomplete } from './ui/CityAutocomplete';
import { useCustomerQuote } from '../context/CustomerQuoteContext';
import type { SearchCriteria } from '../types';

const TRANSPORT_MODE_LABELS: Record<string, { label: string; icon: React.ReactNode; description: string }> = {
    ROAD: { label: 'Route', icon: <Truck className="w-8 h-8" />, description: 'Transport routier standard' },
    RAIL: { label: 'Rail', icon: <Train className="w-8 h-8" />, description: 'Transport ferroviaire' },
    AIR: { label: 'Aérien', icon: <Plane className="w-8 h-8" />, description: 'Fret aérien express' },
    SEA: { label: 'Maritime', icon: <Ship className="w-8 h-8" />, description: 'Fret maritime' }
};

const TRANSPORT_MODE_LABELS_SMALL: Record<string, { label: string; icon: React.ReactNode }> = {
    ROAD: { label: 'Route', icon: <Truck className="w-4 h-4" /> },
    RAIL: { label: 'Rail', icon: <Train className="w-4 h-4" /> },
    AIR: { label: 'Aérien', icon: <Plane className="w-4 h-4" /> },
    SEA: { label: 'Maritime', icon: <Ship className="w-4 h-4" /> }
};

export const SearchModal: React.FC = () => {
    const navigate = useNavigate();
    const { isSearchModalOpen, closeSearchModal, selectedTransportMode, setSelectedTransportMode, searchMode } = useCustomerQuote();
    const [loading, setLoading] = useState(false);
    const [step, setStep] = useState<'mode' | 'form'>('mode');

    // Initial state
    const [formData, setFormData] = useState<SearchCriteria>({
        origin_country: 'FR',
        origin_postal_code: '',
        origin_city: '',
        dest_country: 'FR',
        dest_postal_code: '',
        dest_city: '',
        weight: 0,
        volume: 0,
        transport_mode: undefined,
        shipping_date: new Date().toISOString().split('T')[0]
    });

    // Reset step and sync transport mode when modal opens
    useEffect(() => {
        if (isSearchModalOpen) {
            if (searchMode === 'quote' && selectedTransportMode) {
                // In quote mode, we skip mode selection if already selected
                setStep('form');
                setFormData(prev => ({ ...prev, transport_mode: selectedTransportMode }));
            } else {
                // In consultation mode or if no mode selected, start at mode selection
                setStep('mode');
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isSearchModalOpen]); // Only run when opening/closing, not when mode changes internally

    if (!isSearchModalOpen) return null;

    const handleModeSelect = (mode: 'ROAD' | 'RAIL' | 'AIR' | 'SEA') => {
        setSelectedTransportMode(mode);
        setFormData(prev => ({ ...prev, transport_mode: mode }));
        setStep('form');
    };

    const handleBackToMode = () => {
        setStep('mode');
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFormData((prev: SearchCriteria) => ({
            ...prev,
            [name]: name === 'weight' || name === 'volume' ? parseFloat(value) : value
        }));
    };

    const validateForm = (data: SearchCriteria): boolean => {
        if (!data.origin_postal_code && !data.origin_city) {
            alert("Veuillez renseigner au moins une Ville OU un Département pour l'Origine.");
            return false;
        }
        if (!data.dest_postal_code && !data.dest_city) {
            alert("Veuillez renseigner au moins une Ville OU un Département pour la Destination.");
            return false;
        }
        return true;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!validateForm(formData)) return;

        setLoading(true);
        try {
            const payload = { ...formData };
            if (!payload.transport_mode) delete payload.transport_mode;
            if (!payload.origin_city) delete payload.origin_city;
            if (!payload.dest_city) delete payload.dest_city;
            if (!payload.origin_postal_code) delete payload.origin_postal_code;
            if (!payload.dest_postal_code) delete payload.dest_postal_code;
            if (!payload.volume) delete payload.volume;

            const results = await QuoteService.search(payload);

            closeSearchModal();
            navigate('/results', { state: { results, criteria: formData } });
        } catch (error) {
            console.error("Search failed", error);
            // @ts-expect-error - loose types
            const msg = error.response?.data?.detail?.[0]?.msg || error.response?.data?.detail || "Erreur lors de la recherche";
            alert(msg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[60] overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            {/* Backdrop */}
            <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                <div
                    className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
                    aria-hidden="true"
                    onClick={closeSearchModal}
                ></div>

                <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

                <div className="inline-block align-bottom bg-white rounded-xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">

                    {/* Step 1: Mode Selection */}
                    {step === 'mode' && (
                        <div className="bg-white px-4 pt-5 pb-4 sm:p-8">
                            <div className="flex justify-between items-start mb-8">
                                <h3 className="text-2xl font-bold text-gray-900">
                                    Quel type de transport recherchez-vous ?
                                </h3>
                                <button onClick={closeSearchModal} className="text-gray-400 hover:text-gray-500 p-1">
                                    <X className="h-6 w-6" />
                                </button>
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                {Object.entries(TRANSPORT_MODE_LABELS).map(([key, { label, icon, description }]) => {
                                    const isDisabled = key !== 'ROAD';
                                    return (
                                        <button
                                            key={key}
                                            disabled={isDisabled}
                                            onClick={() => !isDisabled && handleModeSelect(key as any)}
                                            className={`flex flex-col items-center p-6 border-2 rounded-xl transition-all group text-center
                                                ${isDisabled
                                                    ? 'border-gray-100 bg-gray-100 opacity-60 cursor-not-allowed'
                                                    : 'border-gray-100 hover:border-blue-500 hover:bg-blue-50 cursor-pointer'
                                                }`}
                                        >
                                            <div className={`mb-3 p-3 rounded-full transition-colors
                                                ${isDisabled
                                                    ? 'bg-gray-200 text-gray-400'
                                                    : 'bg-gray-50 group-hover:bg-white text-gray-600 group-hover:text-blue-600'
                                                }`}>
                                                {icon}
                                            </div>
                                            <div className={`font-bold text-lg mb-1 ${isDisabled ? 'text-gray-500' : 'text-gray-900'}`}>{label}</div>
                                            <div className={`text-sm ${isDisabled ? 'text-gray-400' : 'text-gray-500'}`}>{description}</div>
                                        </button>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    {/* Step 2: Search Form */}
                    {step === 'form' && (
                        <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                            <div className="flex justify-between items-center mb-6">
                                <div>
                                    <h3 className="text-xl leading-6 font-medium text-gray-900" id="modal-title">
                                        Rechercher un transport
                                    </h3>
                                    {selectedTransportMode && TRANSPORT_MODE_LABELS_SMALL[selectedTransportMode] && (
                                        <div className="flex items-center gap-2 mt-1 text-sm text-gray-600">
                                            <span className="text-indigo-600">{TRANSPORT_MODE_LABELS_SMALL[selectedTransportMode].icon}</span>
                                            <span>Mode : {TRANSPORT_MODE_LABELS_SMALL[selectedTransportMode].label}</span>
                                            {searchMode === 'consultation' && (
                                                <button
                                                    onClick={handleBackToMode}
                                                    className="text-blue-600 hover:text-blue-800 text-xs font-medium ml-2 underline"
                                                >
                                                    (Changer)
                                                </button>
                                            )}
                                        </div>
                                    )}
                                </div>
                                <button onClick={closeSearchModal} className="text-gray-400 hover:text-gray-500">
                                    <X className="h-6 w-6" />
                                </button>
                            </div>

                            <form onSubmit={handleSubmit} className="space-y-6">
                                {/* Route Section */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    {/* Origin */}
                                    <div className="bg-gray-50 p-4 rounded-lg space-y-3">
                                        <h4 className="font-semibold text-gray-700 flex items-center gap-2">
                                            <MapPin className="text-blue-600 w-4 h-4" /> Origine
                                        </h4>
                                        <div className="grid grid-cols-2 gap-3">
                                            <div>
                                                <label className="block text-xs font-medium text-gray-500 mb-1">Pays</label>
                                                <select
                                                    name="origin_country"
                                                    value={formData.origin_country}
                                                    onChange={handleChange}
                                                    className="w-full text-sm rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                                >
                                                    <option value="FR">France</option>
                                                    <option value="DE">Allemagne</option>
                                                    <option value="IT">Italie</option>
                                                    <option value="ES">Espagne</option>
                                                    <option value="BE">Belgique</option>
                                                </select>
                                            </div>
                                            <div>
                                                <label className="block text-xs font-medium text-gray-500 mb-1">Département</label>
                                                <input
                                                    type="text"
                                                    name="origin_postal_code"
                                                    value={formData.origin_postal_code}
                                                    onChange={handleChange}
                                                    className="w-full text-sm rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                                    placeholder="75"
                                                    maxLength={3}
                                                />
                                            </div>
                                            <div className="col-span-2">
                                                <label className="block text-xs font-medium text-gray-500 mb-1">Ville</label>
                                                <CityAutocomplete
                                                    value={formData.origin_city || ''}
                                                    onChange={(city, country) => {
                                                        setFormData(prev => ({
                                                            ...prev,
                                                            origin_city: city,
                                                            origin_country: country || prev.origin_country
                                                        }));
                                                    }}
                                                    country={formData.origin_country}
                                                    placeholder="Ex: Paris"
                                                />
                                            </div>
                                        </div>
                                    </div>

                                    {/* Destination */}
                                    <div className="bg-gray-50 p-4 rounded-lg space-y-3">
                                        <h4 className="font-semibold text-gray-700 flex items-center gap-2">
                                            <MapPin className="text-green-600 w-4 h-4" /> Destination
                                        </h4>
                                        <div className="grid grid-cols-2 gap-3">
                                            <div>
                                                <label className="block text-xs font-medium text-gray-500 mb-1">Pays</label>
                                                <select
                                                    name="dest_country"
                                                    value={formData.dest_country}
                                                    onChange={handleChange}
                                                    className="w-full text-sm rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                                >
                                                    <option value="FR">France</option>
                                                    <option value="DE">Allemagne</option>
                                                    <option value="IT">Italie</option>
                                                    <option value="ES">Espagne</option>
                                                    <option value="BE">Belgique</option>
                                                </select>
                                            </div>
                                            <div>
                                                <label className="block text-xs font-medium text-gray-500 mb-1">Département</label>
                                                <input
                                                    type="text"
                                                    name="dest_postal_code"
                                                    value={formData.dest_postal_code}
                                                    onChange={handleChange}
                                                    className="w-full text-sm rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                                    placeholder="69"
                                                    maxLength={3}
                                                />
                                            </div>
                                            <div className="col-span-2">
                                                <label className="block text-xs font-medium text-gray-500 mb-1">Ville</label>
                                                <CityAutocomplete
                                                    value={formData.dest_city || ''}
                                                    onChange={(city, country) => {
                                                        setFormData(prev => ({
                                                            ...prev,
                                                            dest_city: city,
                                                            dest_country: country || prev.dest_country
                                                        }));
                                                    }}
                                                    country={formData.dest_country}
                                                    placeholder="Ex: Lyon"
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Details Section */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="space-y-3">
                                        <h4 className="font-semibold text-gray-700 flex items-center gap-2">
                                            <Package className="text-orange-600 w-4 h-4" /> Marchandise
                                        </h4>
                                        <div>
                                            <label className="block text-xs font-medium text-gray-500 mb-1">Poids (kg) *</label>
                                            <input
                                                type="number"
                                                name="weight"
                                                value={formData.weight}
                                                onChange={handleChange}
                                                required
                                                min="1"
                                                className="w-full text-sm rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-xs font-medium text-gray-500 mb-1">Volume (m3)</label>
                                            <input
                                                type="number"
                                                name="volume"
                                                value={formData.volume}
                                                onChange={handleChange}
                                                step="0.01"
                                                className="w-full text-sm rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                            />
                                        </div>
                                    </div>

                                    <div className="space-y-3">
                                        <h4 className="font-semibold text-gray-700 flex items-center gap-2">
                                            <Calendar className="text-purple-600 w-4 h-4" /> Date expédition
                                        </h4>
                                        <div>
                                            <label className="block text-xs font-medium text-gray-500 mb-1">Date *</label>
                                            <input
                                                type="date"
                                                name="shipping_date"
                                                value={formData.shipping_date}
                                                onChange={handleChange}
                                                required
                                                className="w-full text-sm rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                                    <button
                                        type="submit"
                                        disabled={loading}
                                        className="w-full inline-flex justify-center items-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:col-start-2 sm:text-sm disabled:opacity-50 gap-2"
                                    >
                                        {loading ? 'Recherche...' : (
                                            <>
                                                <SearchIcon className="w-4 h-4" /> Rechercher les offres
                                            </>
                                        )}
                                    </button>

                                    {searchMode === 'consultation' ? (
                                        <button
                                            type="button"
                                            onClick={handleBackToMode}
                                            className="mt-3 w-full inline-flex justify-center items-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:col-start-1 sm:text-sm gap-2"
                                        >
                                            <ArrowLeft className="w-4 h-4" /> Retour au choix du mode
                                        </button>
                                    ) : (
                                        <button
                                            type="button"
                                            onClick={closeSearchModal}
                                            className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:col-start-1 sm:text-sm"
                                        >
                                            Annuler
                                        </button>
                                    )}
                                </div>
                            </form>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
