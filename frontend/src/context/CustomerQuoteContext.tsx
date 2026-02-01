import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { CustomerQuote } from '../types/customerQuote';
import { customerQuoteService } from '../services/customerQuoteService';

interface CustomerQuoteContextType {
    // État
    currentQuote: CustomerQuote | null;
    loading: boolean;
    error: string | null;

    // Actions
    createQuote: () => Promise<CustomerQuote>;
    loadQuote: (id: string) => Promise<void>;
    updateQuote: (data: { customer_name?: string; customer_company?: string; customer_email?: string; valid_until?: string }) => Promise<void>;

    // Manipulations Items
    addItem: (partnerQuoteId: string, weight: number) => Promise<void>;
    removeItem: (itemId: string) => Promise<void>;
    updateItemMargin: (itemId: string, marginPercent: number) => Promise<void>;
    updateItemPrice: (itemId: string, sellPrice: number) => Promise<void>;

    // Manipulations Frais
    addFee: (description: string, price: number) => Promise<void>;

    clearQuote: () => void;
    refreshQuote: () => Promise<void>;

    // UI
    isSidebarOpen: boolean;
    toggleSidebar: () => void;
    openSidebar: () => void;
    closeSidebar: () => void;

    // Search mode
    searchMode: 'consultation' | 'quote' | null;
    openSearchForConsultation: () => void;
    openSearchForQuote: (mode: 'ROAD' | 'RAIL' | 'AIR' | 'SEA') => void;

    isSearchModalOpen: boolean;
    openSearchModal: () => void;
    closeSearchModal: () => void;
    openSearchModalWithMode: (mode: 'ROAD' | 'RAIL' | 'AIR' | 'SEA') => void; // @deprecated use openSearchForQuote

    // Transport mode selection
    selectedTransportMode: 'ROAD' | 'RAIL' | 'AIR' | 'SEA' | undefined;
    setSelectedTransportMode: (mode: 'ROAD' | 'RAIL' | 'AIR' | 'SEA' | undefined) => void;

    // Computed
    transportSubtotal: number;
    feesTotal: number;
    total: number;
    totalMargin: number;
}

const CustomerQuoteContext = createContext<CustomerQuoteContextType | undefined>(undefined);

const STORAGE_KEY = 'current_quote_id';

export const CustomerQuoteProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [currentQuote, setCurrentQuote] = useState<CustomerQuote | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [isSearchModalOpen, setIsSearchModalOpen] = useState(false);
    const [selectedTransportMode, setSelectedTransportMode] = useState<'ROAD' | 'RAIL' | 'AIR' | 'SEA' | undefined>(undefined);
    const [searchMode, setSearchMode] = useState<'consultation' | 'quote' | null>(null);

    // Initialisation : tenter de récupérer le devis du localStorage
    useEffect(() => {
        const savedId = localStorage.getItem(STORAGE_KEY);
        if (savedId) {
            loadQuote(savedId).catch(() => {
                // Si échec (ex: devis supprimé côté serveur), on nettoie
                localStorage.removeItem(STORAGE_KEY);
            });
        }
    }, []);

    // Persistance : Sauver l'ID quand currentQuote change
    useEffect(() => {
        if (currentQuote?.id) {
            localStorage.setItem(STORAGE_KEY, currentQuote.id);
        } else {
            // Ne pas supprimer tout de suite si null, sauf si c'est explicitement clearQuote()
            // Mais ici c'est simple : si null, rien à sauver.
        }
    }, [currentQuote]);

    const refreshQuote = async () => {
        if (!currentQuote) return;
        try {
            const updated = await customerQuoteService.getById(currentQuote.id);
            setCurrentQuote(updated);
        } catch (err) {
            console.error("Failed to refresh quote", err);
        }
    };

    const createQuote = async () => {
        setLoading(true);
        try {
            const newQuote = await customerQuoteService.create({});
            setCurrentQuote(newQuote);
            localStorage.setItem(STORAGE_KEY, newQuote.id);
            setIsSidebarOpen(true);
            return newQuote;
        } catch (err) {
            setError("Erreur lors de la création du devis");
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const loadQuote = async (id: string) => {
        setLoading(true);
        try {
            const quote = await customerQuoteService.getById(id);
            setCurrentQuote(quote);
            localStorage.setItem(STORAGE_KEY, quote.id);
        } catch (err) {
            console.error("Impossible de charger le devis", err);
        } finally {
            setLoading(false);
        }
    };

    const updateQuote = async (data: { customer_name?: string; customer_company?: string; customer_email?: string; valid_until?: string }) => {
        if (!currentQuote) return;
        try {
            const updated = await customerQuoteService.update(currentQuote.id, data);
            setCurrentQuote(updated);
        } catch (err) {
            console.error("Erreur mise à jour devis", err);
            setError("Erreur mise à jour devis");
            throw err;
        }
    };

    const addItem = async (partnerQuoteId: string, weight: number) => {
        let targetQuoteId = currentQuote?.id;

        // Si pas de devis en cours, on en crée un
        if (!targetQuoteId) {
            try {
                const newQ = await customerQuoteService.create({});
                setCurrentQuote(newQ);
                targetQuoteId = newQ.id;
                localStorage.setItem(STORAGE_KEY, newQ.id); // Persist immediately
                setIsSidebarOpen(true);
            } catch (e) {
                console.error("Failed to auto-create quote", e);
                setError("Erreur création devis automatique");
                return;
            }
        }

        try {
            await customerQuoteService.addTransportItem(targetQuoteId, partnerQuoteId, weight);
            // Recharger pour avoir les totaux à jour
            const updated = await customerQuoteService.getById(targetQuoteId);
            setCurrentQuote(updated);
            setIsSidebarOpen(true);
        } catch (err) {
            console.error(err);
            setError("Erreur lors de l'ajout de l'item");
        }
    };

    const removeItem = async (itemId: string) => {
        if (!currentQuote) return;
        try {
            await customerQuoteService.removeItem(currentQuote.id, itemId);
            await refreshQuote();
        } catch {
            setError("Erreur suppression item");
        }
    };

    const updateItemMargin = async (itemId: string, marginPercent: number) => {
        if (!currentQuote) return;
        try {
            await customerQuoteService.updateItem(currentQuote.id, itemId, { margin_percent: marginPercent });
            await refreshQuote();
        } catch {
            setError("Erreur MAJ marge");
        }
    };

    const updateItemPrice = async (itemId: string, sellPrice: number) => {
        if (!currentQuote) return;
        try {
            await customerQuoteService.updateItem(currentQuote.id, itemId, { sell_price: sellPrice });
            await refreshQuote();
        } catch {
            setError("Erreur MAJ prix");
        }
    };

    const addFee = async (description: string, price: number) => {
        let targetQuoteId = currentQuote?.id;
        if (!targetQuoteId) {
            try {
                const newQ = await customerQuoteService.create({});
                setCurrentQuote(newQ);
                targetQuoteId = newQ.id;
                localStorage.setItem(STORAGE_KEY, newQ.id);
                setIsSidebarOpen(true);
            } catch (e) {
                console.error("Failed to auto-create quote", e);
                return;
            }
        }

        try {
            await customerQuoteService.addFeeItem(targetQuoteId, description, price);
            const updated = await customerQuoteService.getById(targetQuoteId);
            setCurrentQuote(updated);
        } catch {
            setError("Erreur ajout frais");
        }
    };

    const clearQuote = () => {
        setCurrentQuote(null);
        setIsSidebarOpen(false);
        localStorage.removeItem(STORAGE_KEY);
    };

    const toggleSidebar = () => setIsSidebarOpen(prev => !prev);
    const openSidebar = () => setIsSidebarOpen(true);
    const closeSidebar = () => setIsSidebarOpen(false);

    const openSearchForConsultation = () => {
        setSearchMode('consultation');
        setSelectedTransportMode(undefined);
        setIsSearchModalOpen(true);
    };

    const openSearchForQuote = (mode: 'ROAD' | 'RAIL' | 'AIR' | 'SEA') => {
        setSearchMode('quote');
        setSelectedTransportMode(mode);
        setIsSearchModalOpen(true);
    };

    // Deprecated wrapper
    const openSearchModalWithMode = (mode: 'ROAD' | 'RAIL' | 'AIR' | 'SEA') => {
        openSearchForQuote(mode);
    };

    const openSearchModal = () => {
        // Default to consultation if no mode
        if (!searchMode) setSearchMode('consultation');
        setIsSearchModalOpen(true);
    };
    const closeSearchModal = () => {
        setIsSearchModalOpen(false);
        // Reset searchMode on close? Maybe not to keep context if accidental close
        // But for clarity, let's keep it or reset it? 
        // Let's keep it for now.
    };

    return (
        <CustomerQuoteContext.Provider value={{
            currentQuote,
            loading,
            error,
            createQuote,
            loadQuote,
            updateQuote,
            addItem,
            removeItem,
            updateItemMargin,
            updateItemPrice,
            addFee,
            clearQuote,
            refreshQuote,
            isSidebarOpen,
            toggleSidebar,
            openSidebar,
            closeSidebar,
            // Search
            searchMode,
            openSearchForConsultation,
            openSearchForQuote,
            isSearchModalOpen,
            openSearchModal,
            closeSearchModal,
            selectedTransportMode,
            setSelectedTransportMode,
            openSearchModalWithMode,
            // Computed helpers for easier access
            transportSubtotal: currentQuote?.transport_subtotal || 0,
            feesTotal: currentQuote?.fees_total || 0,
            total: currentQuote?.total || 0,
            totalMargin: currentQuote?.total_margin || 0,
        }}>
            {children}
        </CustomerQuoteContext.Provider>
    );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useCustomerQuote = () => {
    const context = useContext(CustomerQuoteContext);
    if (context === undefined) {
        throw new Error('useCustomerQuote must be used within a CustomerQuoteProvider');
    }
    return context;
};
