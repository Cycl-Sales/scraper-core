import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Shield, Building2 } from 'lucide-react';
import { useSubAccount } from '@/contexts/SubAccountContext';

export default function SubAccountAuth() {
  const { authenticateSubAccount, isLoading, error } = useSubAccount();
  const [locationId, setLocationId] = useState('');
  const [isAuthenticating, setIsAuthenticating] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!locationId.trim()) return;

    setIsAuthenticating(true);
    try {
      await authenticateSubAccount(locationId.trim());
    } catch (err) {
      console.error('Authentication error:', err);
    } finally {
      setIsAuthenticating(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-slate-800 border-slate-700">
        <CardHeader className="text-center">
          <div className="mx-auto w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center mb-4">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <CardTitle className="text-white text-xl">Sub-Account Access</CardTitle>
          <CardDescription className="text-slate-400">
            Enter your location ID to access your account dashboard
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="locationId" className="text-sm font-medium text-slate-300">
                Location ID
              </label>
              <Input
                id="locationId"
                type="text"
                placeholder="Enter your location ID"
                value={locationId}
                onChange={(e) => setLocationId(e.target.value)}
                className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-400"
                disabled={isAuthenticating}
              />
            </div>
            
            {error && (
              <Alert className="bg-red-900/20 border-red-800">
                <AlertDescription className="text-red-300">
                  {error}
                </AlertDescription>
              </Alert>
            )}

            <Button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white"
              disabled={!locationId.trim() || isAuthenticating}
            >
              {isAuthenticating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Authenticating...
                </>
              ) : (
                <>
                  <Building2 className="w-4 h-4 mr-2" />
                  Access Dashboard
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
