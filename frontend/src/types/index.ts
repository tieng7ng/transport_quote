export interface Partner {
    id: string;
    code: string;
    name: string;
    email: string;
    rating: number;
    is_active: boolean;
    created_at: string;
}

export interface ImportJob {
    id: string;
    partner_id: string;
    filename: string;
    file_type: string;
    status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
    total_rows: number;
    success_count: number;
    error_count: number;
    errors: any[];
    created_at: string;
}

export interface PartnerCreate {
    code: string;
    name: string;
    email: string | null;
}

export interface Quote {
    id: string;
    partner_id: string;
    transport_mode: 'ROAD' | 'RAIL' | 'AIR' | 'SEA';
    origin_city: string;
    origin_country: string;
    origin_postal_code?: string;
    dest_city: string;
    dest_country: string;
    dest_postal_code?: string;
    weight_min: number;
    weight_max: number;
    cost: string | number;
    currency: string;
    delivery_time: string | null;
    valid_from: string | null;
    valid_until: string | null;
    created_at: string;
    partner: Partner;
}

export interface Partner {
    id: string;
    code: string;
    name: string;
    email: string;
    rating: number;
    is_active: boolean;
    created_at: string;
}

export interface DashboardStats {
    partners_count: number;
    quotes_count: number;
    recent_imports: number;
}

export interface SearchCriteria {
    origin_country: string;
    origin_postal_code?: string;
    origin_city?: string;
    dest_country: string;
    dest_postal_code?: string;
    dest_city?: string;
    weight: number;
    volume?: number;
    transport_mode?: 'ROAD' | 'RAIL' | 'AIR' | 'SEA';
    shipping_date?: string;
}
