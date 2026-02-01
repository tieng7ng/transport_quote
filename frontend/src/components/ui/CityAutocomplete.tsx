import React, { useState, useEffect, useRef } from 'react';
import { CityService } from '../../services/cityService';
import type { CitySuggestion } from '../../services/cityService';
import { MapPin } from 'lucide-react';

interface CityAutocompleteProps {
    value: string;
    onChange: (city: string, country?: string) => void;
    placeholder?: string;
    className?: string;
    country?: string; // Optional filter context
}

export const CityAutocomplete: React.FC<CityAutocompleteProps> = ({
    value,
    onChange,
    placeholder = "Ville",
    className,
    country
}) => {
    const [inputValue, setInputValue] = useState(value);
    const [suggestions, setSuggestions] = useState<CitySuggestion[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const [selectedIndex, setSelectedIndex] = useState(-1);
    const [loading, setLoading] = useState(false);
    const wrapperRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    // Sync input value with prop
    useEffect(() => {
        setInputValue(value);
    }, [value]);

    // Close on click outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [wrapperRef]);

    // Debounce search
    useEffect(() => {
        const timeoutId = setTimeout(async () => {
            if (inputValue.length >= 2 && isOpen) {
                setLoading(true);
                try {
                    const results = await CityService.suggest(inputValue);
                    // Filter by country if provided
                    const filtered = country
                        ? results.filter(city => city.country === country)
                        : results;
                    setSuggestions(filtered);
                } catch (error) {
                    console.error("City suggest error:", error);
                    setSuggestions([]);
                } finally {
                    setLoading(false);
                }
            } else {
                setSuggestions([]);
            }
        }, 300);

        return () => clearTimeout(timeoutId);
    }, [inputValue, country, isOpen]);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const val = e.target.value;
        setInputValue(val);
        onChange(val); // Propagate text change immediately
        setIsOpen(true);
        setSelectedIndex(-1);
    };

    const handleSelect = (suggestion: CitySuggestion) => {
        setInputValue(suggestion.city);
        onChange(suggestion.city, suggestion.country);
        setIsOpen(false);
        setSuggestions([]);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            setSelectedIndex(prev => (prev < suggestions.length - 1 ? prev + 1 : prev));
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setSelectedIndex(prev => (prev > 0 ? prev - 1 : -1));
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
                handleSelect(suggestions[selectedIndex]);
            } else {
                setIsOpen(false); // Close if just Enter without selection
            }
        } else if (e.key === 'Escape') {
            setIsOpen(false);
            inputRef.current?.blur();
        } else if (e.key === 'Tab') {
            if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
                // Select and allow default tab behavior (focus next)
                handleSelect(suggestions[selectedIndex]);
            } else {
                setIsOpen(false);
            }
        }
    };

    return (
        <div className="relative" ref={wrapperRef}>
            <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={handleInputChange}
                onFocus={() => setIsOpen(true)}
                onKeyDown={handleKeyDown}
                placeholder={placeholder}
                className={className || "w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"}
                autoComplete="off"
            />

            {isOpen && (suggestions.length > 0 || loading) && inputValue.length >= 2 && (
                <div className="absolute z-10 w-full bg-white mt-1 rounded-lg shadow-lg border border-gray-100 max-h-60 overflow-auto">
                    {loading && suggestions.length === 0 && (
                        <div className="p-3 text-sm text-gray-500 text-center">Chargement...</div>
                    )}

                    {suggestions.map((city, index) => (
                        <div
                            key={`${city.city}-${city.country}-${index}`}
                            onClick={() => handleSelect(city)}
                            className={`px-4 py-2 cursor-pointer text-sm flex justify-between items-center ${index === selectedIndex ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50 text-gray-700'
                                }`}
                        >
                            <div className="flex items-center gap-2">
                                <MapPin className="w-4 h-4 text-gray-400" />
                                <span>
                                    <span className="font-medium">{city.city}</span>
                                    <span className="text-gray-400 ml-1">({city.country})</span>
                                </span>
                            </div>
                            <span className="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded-full">
                                {city.count}
                            </span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};
