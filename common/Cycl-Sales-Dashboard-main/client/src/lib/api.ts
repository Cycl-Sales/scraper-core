import axios, { AxiosInstance, AxiosResponse } from 'axios';
import type { DashboardMetrics, Contact, Opportunity } from '@shared/schema';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8018';
const API_TIMEOUT = 10000; // 10 seconds

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
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
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
        params: { locationId: this.locationId }
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
  async getCallVolumeAnalytics(): Promise<any[]> {
    try {
      const response = await apiClient.get('/api/dashboard/analytics/call-volume', {
        params: { locationId: this.locationId }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching call volume analytics:', error);
      throw error;
    }
  }

  async getEngagementAnalytics(): Promise<any[]> {
    try {
      const response = await apiClient.get('/api/dashboard/analytics/engagement', {
        params: { locationId: this.locationId }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching engagement analytics:', error);
      throw error;
    }
  }

  async getPipelineAnalytics(): Promise<any[]> {
    try {
      const response = await apiClient.get('/api/dashboard/analytics/pipeline', {
        params: { locationId: this.locationId }
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
        params: { locationId }
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