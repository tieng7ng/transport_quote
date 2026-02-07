import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search as SearchIcon, Truck, Package, Calendar, MapPin } from 'lucide-react';
import { QuoteService } from '../services/quoteService';
import { CityService } from '../services/cityService';
import { CityAutocomplete } from '../components/ui/CityAutocomplete';
import { COUNTRY_NAMES } from '../constants/countries';
import type { SearchCriteria } from '../types';

export const Search: React.FC = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [countries, setCountries] = useState<{ origin_countries: string[]; dest_countries: string[] }>({
        origin_countries: [], dest_countries: []
    });

    useEffect(() => {
        CityService.getCountries().then(setCountries).catch(console.error);
    }, []);

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

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFormData((prev: SearchCriteria) => ({
            ...prev,
            [name]: name === 'weight' || name === 'volume' ? parseFloat(value) : value
        }));
    };

    const validateForm = (data: SearchCriteria): boolean => {
        // Origin Validation
        if (!data.origin_postal_code && !data.origin_city) {
            alert("Veuillez renseigner au moins une Ville OU un Département pour l'Origine.");
            return false;
        }
        // Destination Validation
        if (!data.dest_postal_code && !data.dest_city) {
            alert("Veuillez renseigner au moins une Ville OU un Département pour la Destination.");
            return false;
        }
        return true;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!validateForm(formData)) {
            return;
        }

        setLoading(true);
        try {
            // Clean up payload: remove empty strings or undefined values
            const payload = { ...formData };
            if (!payload.transport_mode) {
                delete payload.transport_mode;
            }
            // Explicitly keep fields even if empty strings because backend now handles them as optional
            // but we want to send them if user typed something.
            // However, our initial state has empty strings. 
            // Better to remove empty strings to let backend Optional[str] = None take over (or handle empty str).
            if (!payload.origin_city) delete payload.origin_city;
            if (!payload.dest_city) delete payload.dest_city;
            if (!payload.origin_postal_code) delete payload.origin_postal_code;
            if (!payload.dest_postal_code) delete payload.dest_postal_code;
            if (!payload.volume) delete payload.volume;

            const results = await QuoteService.search(payload);
            navigate('/results', { state: { results, criteria: formData } });
        } catch (error) {
            console.error("Search failed", error);
            // Show backend error message if available
            // @ts-expect-error - jspdf types are loose
            const msg = error.response?.data?.detail?.[0]?.msg || error.response?.data?.detail || "Erreur lors de la recherche";
            alert(msg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto p-6">
            <div className="mb-8 text-center">
                <h1 className="text-3xl font-bold text-gray-900">Trouver un tarif</h1>
                <p className="mt-2 text-gray-600">Recherchez les meilleurs tarifs de transport pour vos expéditions.</p>
            </div>

            <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
                <div className="p-8 space-y-8">

                    {/* Route Section */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* Origin */}
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                                <MapPin className="text-blue-600 w-5 h-5" /> Origine
                            </h3>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Pays</label>
                                    <select
                                        name="origin_country"
                                        value={formData.origin_country}
                                        onChange={handleChange}
                                        className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                    >
                                        {countries.origin_countries.map(code => (
                                            <option key={code} value={code}>{COUNTRY_NAMES[code] || code}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Département</label>
                                    <input
                                        type="text"
                                        name="origin_postal_code"
                                        value={formData.origin_postal_code}
                                        onChange={handleChange}
                                        maxLength={3}
                                        className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                        placeholder="75"
                                    />
                                </div>
                                <div className="col-span-2">
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Ville</label>
                                    <CityAutocomplete
                                        value={formData.origin_city || ''}
                                        onChange={(city, country) => {
                                            setFormData(prev => ({
                                                ...prev,
                                                origin_city: city,
                                                // Optional: auto-select country if provided
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
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                                <MapPin className="text-green-600 w-5 h-5" /> Destination
                            </h3>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Pays</label>
                                    <select
                                        name="dest_country"
                                        value={formData.dest_country}
                                        onChange={handleChange}
                                        className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                    >
                                        {countries.dest_countries.map(code => (
                                            <option key={code} value={code}>{COUNTRY_NAMES[code] || code}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Département</label>
                                    <input
                                        type="text"
                                        name="dest_postal_code"
                                        value={formData.dest_postal_code}
                                        onChange={handleChange}
                                        maxLength={3}
                                        className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                        placeholder="69"
                                    />
                                </div>
                                <div className="col-span-2">
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Ville</label>
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

                    <div className="border-t border-gray-100 pt-8"></div>

                    {/* Details Section */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                                <Package className="text-orange-600 w-5 h-5" /> Marchandise
                            </h3>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Poids (kg)</label>
                                <input
                                    type="number"
                                    name="weight"
                                    value={formData.weight}
                                    onChange={handleChange}
                                    required
                                    min="1"
                                    className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Volume (m3)</label>
                                <input
                                    type="number"
                                    name="volume"
                                    value={formData.volume}
                                    onChange={handleChange}
                                    step="0.01"
                                    className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                />
                            </div>
                        </div>

                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                                <Truck className="text-indigo-600 w-5 h-5" /> Transport
                            </h3>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Mode</label>
                                <select
                                    name="transport_mode"
                                    value={formData.transport_mode || ''}
                                    onChange={handleChange}
                                    className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                >
                                    <option value="">Tous les modes</option>
                                    <option value="ROAD">Route</option>
                                    <option value="RAIL">Rail</option>
                                    <option value="AIR">Aérien</option>
                                    <option value="SEA">Maritime</option>
                                </select>
                            </div>
                        </div>

                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                                <Calendar className="text-purple-600 w-5 h-5" /> Date expédition
                            </h3>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                                <input
                                    type="date"
                                    name="shipping_date"
                                    value={formData.shipping_date}
                                    onChange={handleChange}
                                    required
                                    className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                />
                            </div>
                        </div>
                    </div>
                </div>

                <div className="bg-gray-50 px-8 py-5 flex justify-end">
                    <button
                        type="submit"
                        disabled={loading}
                        className="flex items-center gap-2 bg-blue-600 text-white px-8 py-3 rounded-xl font-semibold hover:bg-blue-700 transition-colors shadow-lg shadow-blue-500/30 disabled:opacity-50"
                    >
                        {loading ? 'Recherche en cours...' : (
                            <>
                                <SearchIcon className="w-5 h-5" /> Rechercher les offres
                            </>
                        )}
                    </button>
                </div>
            </form>
        </div>
    );
};
