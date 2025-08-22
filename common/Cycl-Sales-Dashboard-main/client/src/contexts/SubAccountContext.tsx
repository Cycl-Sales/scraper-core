import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface SubAccountContextType {
  locationId: string | null;
  isSubAccount: boolean;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  authenticateSubAccount: (locationId: string) => Promise<boolean>;
  logout: () => void;
}

const SubAccountContext = createContext<SubAccountContextType | undefined>(undefined);

interface SubAccountProviderProps {
  children: ReactNode;
}

export function SubAccountProvider({ children }: SubAccountProviderProps) {
  const [locationId, setLocationId] = useState<string | null>(null);
  const [isSubAccount, setIsSubAccount] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Check for location_id in URL on mount
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const urlLocationId = urlParams.get('location_id');
    
    if (urlLocationId) {
      authenticateSubAccount(urlLocationId);
    } else {
      setIsLoading(false);
    }
  }, []);

  const authenticateSubAccount = async (locationId: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Validate the location_id by making a test API call
      const response = await fetch(`/api/location-name?location_id=${encodeURIComponent(locationId)}&appId=6867d1537079188afca5013c`);
      const data = await response.json();
      
      if (data.success && data.name) {
        setLocationId(locationId);
        setIsSubAccount(true);
        setIsAuthenticated(true);
        
        // Store in localStorage for persistence
        localStorage.setItem('sub_account_location_id', locationId);
        localStorage.setItem('sub_account_name', data.name);
        
        setIsLoading(false);
        return true;
      } else {
        throw new Error('Invalid location ID');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
      setIsAuthenticated(false);
      setIsLoading(false);
      return false;
    }
  };

  const logout = () => {
    setLocationId(null);
    setIsSubAccount(false);
    setIsAuthenticated(false);
    setError(null);
    
    // Clear localStorage
    localStorage.removeItem('sub_account_location_id');
    localStorage.removeItem('sub_account_name');
    
    // Redirect to overview
    window.location.href = '/overview';
  };

  const value: SubAccountContextType = {
    locationId,
    isSubAccount,
    isAuthenticated,
    isLoading,
    error,
    authenticateSubAccount,
    logout,
  };

  return (
    <SubAccountContext.Provider value={value}>
      {children}
    </SubAccountContext.Provider>
  );
}

export function useSubAccount() {
  const context = useContext(SubAccountContext);
  if (context === undefined) {
    throw new Error('useSubAccount must be used within a SubAccountProvider');
  }
  return context;
}
