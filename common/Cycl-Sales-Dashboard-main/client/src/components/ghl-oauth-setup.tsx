import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Loader2, CheckCircle, XCircle, ExternalLink } from 'lucide-react';
import { dashboardAPI } from '../lib/api';

interface GHLOAuthSetupProps {
  locationId: string;
  onConnectionChange?: (isConnected: boolean) => void;
}

export function GHLOAuthSetup({ locationId, onConnectionChange }: GHLOAuthSetupProps) {
  const [isConnected, setIsConnected] = useState<boolean | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  // Check OAuth status on component mount
  useEffect(() => {
    checkOAuthStatus();
  }, [locationId]);

  const checkOAuthStatus = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const status = await dashboardAPI.getOAuthStatus(locationId);
      setIsConnected(status.isConnected);
      setLastUpdated(status.lastUpdated || null);
      
      // Notify parent component
      onConnectionChange?.(status.isConnected);
      
    } catch (err: any) {
      console.error('Error checking OAuth status:', err);
      setError(err.message || 'Failed to check OAuth status');
      setIsConnected(false);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInstallApp = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Generate authorization URL
      const authData = await dashboardAPI.getOAuthAuthorizationUrl(locationId, 'install');
      
      // Redirect to GHL authorization page
      window.location.href = authData.authorizationUrl;
      
    } catch (err: any) {
      console.error('Error starting OAuth flow:', err);
      setError(err.message || 'Failed to start OAuth flow');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReconnect = () => {
    handleInstallApp();
  };

  const formatLastUpdated = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return 'Unknown';
    }
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <img 
            src="https://gohighlevel.com/wp-content/uploads/2021/03/logo.png" 
            alt="GHL" 
            className="h-6 w-auto"
          />
          GHL Connection
        </CardTitle>
        <CardDescription>
          Connect your GoHighLevel account to sync contacts and data
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Status Display */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Connection Status:</span>
          {isLoading ? (
            <div className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm text-muted-foreground">Checking...</span>
            </div>
          ) : isConnected ? (
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <Badge variant="default" className="bg-green-100 text-green-800">
                Connected
              </Badge>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <XCircle className="h-4 w-4 text-red-500" />
              <Badge variant="secondary" className="bg-red-100 text-red-800">
                Not Connected
              </Badge>
            </div>
          )}
        </div>

        {/* Last Updated */}
        {lastUpdated && (
          <div className="text-sm text-muted-foreground">
            Last updated: {formatLastUpdated(lastUpdated)}
          </div>
        )}

        {/* Error Display */}
        {error && (
          <Alert variant="destructive">
            <XCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2">
          {isConnected ? (
            <>
              <Button 
                variant="outline" 
                onClick={checkOAuthStatus}
                disabled={isLoading}
                className="flex-1"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : null}
                Refresh Status
              </Button>
              <Button 
                variant="outline" 
                onClick={handleReconnect}
                disabled={isLoading}
                className="flex-1"
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                Reconnect
              </Button>
            </>
          ) : (
            <Button 
              onClick={handleInstallApp}
              disabled={isLoading}
              className="w-full"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <ExternalLink className="h-4 w-4 mr-2" />
              )}
              Install GHL App
            </Button>
          )}
        </div>

        {/* Instructions */}
        {!isConnected && (
          <div className="text-xs text-muted-foreground space-y-1">
            <p>• Click "Install GHL App" to start the connection process</p>
            <p>• You'll be redirected to GoHighLevel to authorize the app</p>
            <p>• After authorization, you'll be redirected back here</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
} 