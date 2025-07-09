import { useState, useCallback } from 'react';
import { dashboardAPI, handleAPIError, APIError } from '@/lib/api';
import type { DashboardMetrics, Contact } from '@shared/schema';

// Generic hook for API calls
export function useApiCall<T, P extends any[]>(
  apiFunction: (...args: P) => Promise<T>
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<APIError | null>(null);

  const execute = useCallback(async (...args: P) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiFunction(...args);
      setData(result);
      return result;
    } catch (err) {
      const apiError = handleAPIError(err);
      setError(apiError);
      throw apiError;
    } finally {
      setLoading(false);
    }
  }, [apiFunction]);

  return {
    data,
    loading,
    error,
    execute,
    setData,
    setError,
  };
}

// Specific hooks for dashboard functionality
export function useDashboardMetrics() {
  return useApiCall(dashboardAPI.getDashboardMetrics.bind(dashboardAPI));
}

export function useContacts() {
  return useApiCall(dashboardAPI.getContacts.bind(dashboardAPI));
}

export function useContactDetail() {
  return useApiCall(dashboardAPI.getContactDetail.bind(dashboardAPI));
}

export function useCreateContact() {
  return useApiCall(dashboardAPI.createContact.bind(dashboardAPI));
}

export function useUpdateContact() {
  return useApiCall(dashboardAPI.updateContact.bind(dashboardAPI));
}

export function useCallVolumeAnalytics() {
  return useApiCall(dashboardAPI.getCallVolumeAnalytics.bind(dashboardAPI));
}

export function useEngagementAnalytics() {
  return useApiCall(dashboardAPI.getEngagementAnalytics.bind(dashboardAPI));
}

export function usePipelineAnalytics() {
  return useApiCall(dashboardAPI.getPipelineAnalytics.bind(dashboardAPI));
}

// Hook for managing location ID
export function useLocationId() {
  const [locationId, setLocationId] = useState(dashboardAPI.getLocationId());

  const updateLocationId = useCallback((newLocationId: string) => {
    dashboardAPI.setLocationId(newLocationId);
    setLocationId(newLocationId);
  }, []);

  return {
    locationId,
    updateLocationId,
  };
}

// Hook for API configuration
export function useApiConfig() {
  const [baseUrl, setBaseUrl] = useState(
    import.meta.env.VITE_API_BASE_URL || 'http://localhost:8018'
  );

  const updateBaseUrl = useCallback((newBaseUrl: string) => {
    setBaseUrl(newBaseUrl);
    // You might want to update the axios instance here
    console.log('API Base URL updated to:', newBaseUrl);
  }, []);

  return {
    baseUrl,
    updateBaseUrl,
  };
} 