import axios from 'axios';

// Hardcoded API base URL for all environments
export const API_BASE_URL = 'http://localhost:5173/';

// Create a shared axios instance
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

export interface ZillowProperty {
  id: number;
  zpid: string;
  street_address: string;
  city: string;
  state: string;
  zip_code?: string;
  zipcode?: string;
  price: number;
  bedrooms: number;
  bathrooms: number;
  living_area: number;
  home_status: string;
  home_type: string;
  hi_res_image_link?: string;
  hdp_url?: string;
  sent_by_current_user: boolean;
  sent_to_cyclsales_count: number;
  sent_to_cyclsales: boolean;
  listingAgent?: {
    id: number;
    name: string;
    business_name: string;
    phone: string;
    profile_url: string;
    email: string;
    license_number: string;
    license_state: string;
  };
}

export interface SearchParams {
  url: string;
  page?: number;
  listing_type?: 'by_agent' | 'by_owner' | 'new_construction';
}

export interface SearchResponse {
  success: boolean;
  properties: ZillowProperty[];
  total_results: number;
  page: number;
}

export interface ApiResponse {
  status: 'success' | 'error';
  data?: ZillowProperty[];
  message?: string;
}

export const zillowService = {
  async getProperties(): Promise<ZillowProperty[]> {
    try {
      console.log('Fetching properties from:', `/api/zillow/properties`);
      const response = await api.get<ZillowProperty[]>(`/api/zillow/properties`);
      console.log('API Response:', response.data);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error('Axios error details:', {
          message: error.message,
          status: error.response?.status,
          data: error.response?.data,
          config: error.config
        });
        throw new Error(`API Error: ${error.message}`);
      }
      console.error('Error fetching properties:', error);
      throw error;
    }
  },

  async searchProperties(params: SearchParams): Promise<SearchResponse> {
    try {
      const response = await api.get<SearchResponse>(`/api/zillow/search`, {
        params: {
          url: params.url,
          page: params.page || 1,
          listing_type: params.listing_type || 'by_agent'
        },
      });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error('Search error details:', {
          message: error.message,
          status: error.response?.status,
          data: error.response?.data,
        });
        throw new Error(`Search Error: ${error.message}`);
      }
      throw error;
    }
  },

  async sendToCyclSales(propertyIds: number[], locationId?: string): Promise<{ success: boolean; error?: string }> {
    try {
      console.log('zillowService.sendToCyclSales - Sending request with data:', { property_ids: propertyIds, locationId });
      const body: any = { property_ids: propertyIds };
      if (locationId) body.locationId = locationId;
      const response = await api.post<{ success: boolean; error?: string }>(
        `/api/zillow/send-to-cyclsales`,
        body
      );
      console.log('zillowService.sendToCyclSales - Response:', response.data);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error('Send to CyclSales error details:', {
          message: error.message,
          status: error.response?.status,
          data: error.response?.data,
        });
        throw new Error(`Send to CyclSales Error: ${error.message}`);
      }
      throw error;
    }
  },

  async getProperty(zpid: string): Promise<any> {
    try {
      const response = await api.get(`/api/zillow/property/${zpid}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(`Get Property Error: ${error.message}`);
      }
      throw error;
    }
  }
}; 