import React, { useState } from 'react';
import { ChevronRight, ChevronDown } from 'lucide-react';
import type { PriceBreakdown as PriceBreakdownType } from '../../types';

const PRICING_LABELS: Record<string, string> = {
    PER_100KG: 'Prix au 100 kg',
    PER_KG: 'Prix au kg',
    LUMPSUM: 'Forfait par envoi',
};

interface Props {
    breakdown: PriceBreakdownType;
    currency: string;
}

export const PriceBreakdownPanel: React.FC<Props> = ({ breakdown, currency }) => {
    const [open, setOpen] = useState(false);
    const cur = currency === 'EUR' ? '€' : currency;

    return (
        <div className="mt-1">
            <button
                onClick={() => setOpen(!open)}
                className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1 transition-colors"
            >
                {open ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                {open ? 'Masquer le détail' : 'Voir le détail'}
            </button>

            {open && (
                <div className="mt-2 bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm text-gray-700 min-w-[260px]">
                    <p className="font-semibold text-gray-900 mb-3">Détail du calcul</p>

                    <table className="w-full">
                        <tbody>
                            <Row label="Tarification" value={`${breakdown.pricing_type} (${PRICING_LABELS[breakdown.pricing_type] || breakdown.pricing_type})`} />

                            {breakdown.pricing_type === 'LUMPSUM' ? (
                                <>
                                    <Row label="Forfait" value={`${breakdown.unit_price.toFixed(2)} ${cur}`} />
                                    <Row label="Poids demandé" value={`${breakdown.actual_weight} kg`} />
                                </>
                            ) : (
                                <>
                                    <Row
                                        label="Prix unitaire"
                                        value={`${breakdown.unit_price.toFixed(2)} ${cur} / ${breakdown.pricing_type === 'PER_100KG' ? '100 kg' : 'kg'}`}
                                    />
                                    <Row label="Poids demandé" value={`${breakdown.actual_weight} kg`} />
                                    {breakdown.billable_weight !== breakdown.actual_weight && (
                                        <Row label="Poids facturé" value={`${breakdown.billable_weight} kg (arrondi au 100 kg supérieur)`} />
                                    )}
                                </>
                            )}
                        </tbody>
                    </table>

                    <hr className="my-2 border-gray-300" />

                    <table className="w-full">
                        <tbody>
                            <Row label="Calcul" value={breakdown.formula} bold />
                            <Row label="Total" value={`${breakdown.total.toFixed(2)} ${cur}`} bold />
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

const Row: React.FC<{ label: string; value: string; bold?: boolean }> = ({ label, value, bold }) => (
    <tr>
        <td className="pr-4 py-0.5 text-gray-500 whitespace-nowrap align-top">{label}</td>
        <td className={`py-0.5 ${bold ? 'font-semibold text-gray-900' : ''}`}>{value}</td>
    </tr>
);
