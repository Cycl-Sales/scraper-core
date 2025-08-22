import React from 'react';
import { useSubAccount } from '@/contexts/SubAccountContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Building2, Shield, Users, Settings } from 'lucide-react';

export default function SubAccountTest() {
  const { 
    locationId, 
    isSubAccount, 
    isAuthenticated, 
    isLoading, 
    error
  } = useSubAccount();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-white">Loading sub-account status...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white mb-2">Sub-Account Access Test</h1>
          <p className="text-slate-400">Verify sub-account functionality and access control</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Authentication Status */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Authentication Status
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-slate-300">Sub-Account Mode:</span>
                <Badge variant={isSubAccount ? "default" : "secondary"}>
                  {isSubAccount ? "Active" : "Inactive"}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-300">Authenticated:</span>
                <Badge variant={isAuthenticated ? "default" : "destructive"}>
                  {isAuthenticated ? "Yes" : "No"}
                </Badge>
              </div>
              {error && (
                <div className="flex items-center justify-between">
                  <span className="text-slate-300">Error:</span>
                  <span className="text-red-400 text-sm">{error}</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Account Information */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Building2 className="w-5 h-5" />
                Account Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-slate-300">Location ID:</span>
                <span className="text-white font-mono text-sm">
                  {locationId || "Not set"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-300">Account Name:</span>
                <span className="text-white">
                  {localStorage.getItem('sub_account_name') || "Not available"}
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Access Control */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Users className="w-5 h-5" />
                Access Control
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <h4 className="text-slate-300 font-medium">Available Pages:</h4>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-green-400 border-green-400">
                      ✓ Analytics
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-green-400 border-green-400">
                      ✓ Automations
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-green-400 border-green-400">
                      ✓ Call Details
                    </Badge>
                  </div>
                </div>
              </div>
              <div className="space-y-2">
                <h4 className="text-slate-300 font-medium">Restricted Pages:</h4>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-red-400 border-red-400">
                      ✗ Overview
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-red-400 border-red-400">
                      ✗ Dashboard
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-red-400 border-red-400">
                      ✗ Settings
                    </Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Test Actions */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Settings className="w-5 h-5" />
                Test Actions
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Button 
                  onClick={() => window.location.href = `/analytics?location_id=${locationId}`}
                  className="w-full"
                  disabled={!isAuthenticated}
                >
                  Test Analytics Page
                </Button>
                <Button 
                  onClick={() => window.location.href = `/automations?location_id=${locationId}`}
                  className="w-full"
                  disabled={!isAuthenticated}
                >
                  Test Automations Page
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* URL Examples */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Test URL Examples</CardTitle>
            <CardDescription className="text-slate-400">
              Use these URLs to test sub-account functionality
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <h4 className="text-slate-300 font-medium">Analytics:</h4>
              <code className="block bg-slate-700 p-3 rounded text-sm text-green-400 break-all">
                http://localhost:3000/analytics?location_id=GMCTanHIR07xDE3kvnpo
              </code>
            </div>
            <div className="space-y-2">
              <h4 className="text-slate-300 font-medium">Automations:</h4>
              <code className="block bg-slate-700 p-3 rounded text-sm text-green-400 break-all">
                http://localhost:3000/automations?location_id=GMCTanHIR07xDE3kvnpo
              </code>
            </div>
            <div className="space-y-2">
              <h4 className="text-slate-300 font-medium">Call Details:</h4>
              <code className="block bg-slate-700 p-3 rounded text-sm text-green-400 break-all">
                http://localhost:3000/call-details?contact_id=34450&contact=Lori%20Barber&date=2025-08-18T19%3A21%3A06.114000&tags=name%20via%20lookup%2Csent%20quick%20message%2Cunqualified%2Cgoogle-call%2Cnew%20lead%20no%20answer%20campaign%2Cai%20follow%20up%20bot%2Cai%20off
              </code>
            </div>
          </CardContent>
        </Card>

        {/* Key Differences */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Key Differences: Agency vs Sub-Account</CardTitle>
            <CardDescription className="text-slate-400">
              How the interface changes between agency and sub-account views
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <h4 className="text-slate-300 font-medium">Agency View:</h4>
                <ul className="text-sm text-slate-400 space-y-1">
                  <li>• Full navigation (Overview, Analytics, Automations)</li>
                  <li>• "Select Locations" dropdown available</li>
                  <li>• Can switch between multiple locations</li>
                  <li>• Access to all pages and features</li>
                  <li>• No "SUB-ACCOUNT" badge</li>
                </ul>
              </div>
              <div className="space-y-2">
                <h4 className="text-slate-300 font-medium">Sub-Account View:</h4>
                <ul className="text-sm text-slate-400 space-y-1">
                  <li>• Limited navigation (Analytics, Automations only)</li>
                  <li>• "Current Location" display (no dropdown)</li>
                  <li>• Locked to single location</li>
                  <li>• Restricted access to specific pages</li>
                  <li>• "SUB-ACCOUNT" badge visible</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
