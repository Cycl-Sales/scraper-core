import axios from 'axios';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ? import.meta.env.VITE_API_BASE_URL + '/api/zillow' : '/api/zillow');

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
      console.log('Fetching properties from:', `${API_BASE_URL}/properties`);
      const response = await axios.get<ZillowProperty[]>(`${API_BASE_URL}/properties`, {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        timeout: 10000, // 10 second timeout
      });
      
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
      const response = await axios.get<SearchResponse>(`${API_BASE_URL}/search`, {
        params: {
          url: params.url,
          page: params.page || 1,
          listing_type: params.listing_type || 'by_agent'
        },
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        timeout: 10000,
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
      const response = await axios.post<{ success: boolean; error?: string }>(
        `${API_BASE_URL}/send-to-cyclsales`,
        body,
        {
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
          timeout: 10000,
        }
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
  }
}; 