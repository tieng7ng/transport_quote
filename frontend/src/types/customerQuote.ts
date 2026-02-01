export type CustomerQuoteStatus = 'DRAFT' | 'READY' | 'SENT' | 'ACCEPTED' | 'REJECTED' | 'EXPIRED';
export type CustomerQuoteItemType = 'TRANSPORT' | 'FEE';

export interface CustomerQuoteItem {
    id: string;
    quote_id: string;
    item_type: CustomerQuoteItemType;
    description: string;
    position: number;

    // Pricing
    sell_price: number;
    margin_percent?: number;
    margin_amount: number;
    cost_price: number;

    // Snapshot (Transport only)
    partner_quote_id?: string;
    origin_city?: string;
    origin_country?: string;
    dest_city?: string;
    dest_country?: string;
    partner_name?: string;
    transport_mode?: string;
    delivery_time?: string;
    weight?: number;
    marketing_carrier?: string; // Added to fix build error

    created_at: string;
}

export interface CustomerQuote {
    id: string;
    reference: string;
    status: CustomerQuoteStatus;

    customer_name?: string;
    customer_email?: string;
    customer_company?: string;

    // Totals
    transport_subtotal: number;
    fees_total: number;
    total: number;
    total_margin: number;
    currency: string;

    valid_until?: string;
    created_at: string;
    updated_at?: string;
    sent_at?: string;

    items: CustomerQuoteItem[];
}

export interface CustomerQuoteItemCreate {
    item_type: CustomerQuoteItemType;
    description: string;
    sell_price: number;
    margin_percent?: number;
    margin_amount: number;
    cost_price?: number;

    // Transport specific
    partner_quote_id?: string;
    weight?: number;
}

export interface CustomerQuoteItemUpdate {
    sell_price?: number;
    margin_percent?: number;
    description?: string;
}

export interface CustomerQuoteCreate {
    customer_name?: string;
    customer_email?: string;
    customer_company?: string;
    valid_until?: string;
    currency?: string;
}
