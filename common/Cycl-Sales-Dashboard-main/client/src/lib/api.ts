import axios, { AxiosInstance, AxiosResponse } from 'axios';
import type { DashboardMetrics, Contact } from '@shared/schema';
import { CYCLSALES_APP_ID, API_BASE_URL, API_TIMEOUT } from './constants';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => { 
    return config;
  },
  (error) => { 
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response: AxiosResponse) => { 
    return response;
  },
  (error) => { 
    return Promise.reject(error);
  }
);

// API Service Class
export class DashboardAPI {
  private static instance: DashboardAPI;
  private locationId: string = 'demo-location';

  private constructor() {}

  public static getInstance(): DashboardAPI {
    if (!DashboardAPI.instance) {
      DashboardAPI.instance = new DashboardAPI();
    }
    return DashboardAPI.instance;
  }

  public setLocationId(locationId: string): void {
    this.locationId = locationId;
  }

  public getLocationId(): string {
    return this.locationId;
  }

  // Dashboard Metrics
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    try {
      const response = await apiClient.get('/api/dashboard/metrics', {
        params: { 
          locationId: this.locationId,
          appId: CYCLSALES_APP_ID
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard metrics:', error);
      throw error;
    }
  }

  // Contacts
  async getContacts(limit: number = 50, offset: number = 0): Promise<Contact[]> {
    try {
      const response = await apiClient.get('/api/dashboard/contacts', {
        params: { 
          locationId: this.locationId,
          appId: CYCLSALES_APP_ID,
          limit,
          offset
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching contacts:', error);
      throw error;
    }
  }

  // Fast contacts endpoint for immediate data with background sync
  async getContactsFast(locationId: string): Promise<{ contacts: Contact[], sync_status?: string, message?: string }> {
    try {
      const response = await apiClient.get('/api/get-location-contacts-fast', {
        params: { 
          location_id: locationId,
          appId: CYCLSALES_APP_ID
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching contacts (fast):', error);
      throw error;
    }
  }

  // Original contacts endpoint for fresh data sync
  async getContactsFresh(locationId: string): Promise<{ success: boolean, message?: string, error?: string }> {
    try {
      const response = await apiClient.get('/api/get-location-contacts', {
        params: { 
          location_id: locationId,
          appId: CYCLSALES_APP_ID
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching contacts (fresh):', error);
      throw error;
    }
  }

  // Database contacts endpoint for cached data
  async getContactsFromDB(locationId: string): Promise<{ contacts: Contact[], success: boolean }> {
    try {
      const response = await apiClient.get('/api/location-contacts', {
        params: { 
          location_id: locationId,
          appId: CYCLSALES_APP_ID
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching contacts from DB:', error);
      throw error;
    }
  }

  async getContactDetail(contactId: string): Promise<Contact> {
    try {
      const response = await apiClient.get(`/api/dashboard/contacts/${contactId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching contact detail:', error);
      throw error;
    }
  }

  async createContact(contactData: Partial<Contact>): Promise<{ success: boolean; contactId: string }> {
    try {
      const response = await apiClient.post('/api/dashboard/contacts', {
        ...contactData,
        locationId: this.locationId
      });
      return response.data;
    } catch (error) {
      console.error('Error creating contact:', error);
      throw error;
    }
  }

  async updateContact(contactId: string, contactData: Partial<Contact>): Promise<{ success: boolean }> {
    try {
      const response = await apiClient.put(`/api/dashboard/contacts/${contactId}`, contactData);
      return response.data;
    } catch (error) {
      console.error('Error updating contact:', error);
      throw error;
    }
  }

  // Analytics
  async getCallVolumeAnalytics(startDate?: string, endDate?: string): Promise<any[]> {
    try {
      const params: any = { 
        locationId: this.locationId,
        appId: CYCLSALES_APP_ID
      };
      
      if (startDate) params.startDate = startDate;
      if (endDate) params.endDate = endDate;
      
      const response = await apiClient.get('/api/dashboard/analytics/call-volume', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching call volume analytics:', error);
      throw error;
    }
  }

  async getEngagementAnalytics(startDate?: string, endDate?: string): Promise<any[]> {
    try {
      const params: any = { 
        locationId: this.locationId,
        appId: CYCLSALES_APP_ID
      };
      
      if (startDate) params.startDate = startDate;
      if (endDate) params.endDate = endDate;
      
      const response = await apiClient.get('/api/dashboard/analytics/engagement', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching engagement analytics:', error);
      throw error;
    }
  }

  async getPipelineAnalytics(): Promise<any[]> {
    try {
      const response = await apiClient.get('/api/dashboard/analytics/pipeline', {
        params: { 
          locationId: this.locationId,
          appId: CYCLSALES_APP_ID
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching pipeline analytics:', error);
      throw error;
    }
  }

  // OAuth Endpoints
  async getOAuthAuthorizationUrl(locationId: string, state?: string): Promise<{ authorizationUrl: string }> {
    try {
      const response = await apiClient.get('/api/dashboard/oauth/authorize', {
        params: { 
          locationId,
          appId: CYCLSALES_APP_ID,
          state
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error getting OAuth authorization URL:', error);
      throw error;
    }
  }

  async getOAuthStatus(locationId: string): Promise<{ isConnected: boolean; lastUpdated?: string }> {
    try {
      const response = await apiClient.get('/api/dashboard/oauth/status', {
        params: { 
          locationId,
          appId: CYCLSALES_APP_ID
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error getting OAuth status:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const dashboardAPI = DashboardAPI.getInstance();

// Export types for API responses
export interface APIResponse<T> {
  data: T;
  success: boolean;
  error?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  limit: number;
  offset: number;
}

// Error handling utilities
export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export const handleAPIError = (error: any): APIError => {
  if (error.response) {
    return new APIError(
      error.response.data?.error || 'An error occurred',
      error.response.status,
      error.response.data?.code
    );
  } else if (error.request) {
    return new APIError('Network error - no response received', 0);
  } else {
    return new APIError(error.message || 'An unexpected error occurred', 0);
  }
}; 