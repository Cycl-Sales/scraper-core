import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { GHLOAuthSetup } from '../components/ghl-oauth-setup';
import { Separator } from '../components/ui/separator';

export default function SettingsPage() {
  const [locationId] = useState('demo-location');

  const handleGHLConnectionChange = () => {
    // no-op for now; integration status not displayed on this page
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Manage your account settings and integrations
        </p>
      </div>

      <Tabs defaultValue="integrations" className="space-y-4">
        <TabsList>
          <TabsTrigger value="integrations">Integrations</TabsTrigger>
          <TabsTrigger value="account">Account</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
        </TabsList>

        <TabsContent value="integrations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Integrations</CardTitle>
              <CardDescription>
                Connect your external services and platforms
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* GHL Integration */}
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold">GoHighLevel Integration</h3>
                  <p className="text-sm text-muted-foreground">
                    Connect your GoHighLevel account to sync contacts, opportunities, and analytics data.
                  </p>
                </div>
                
                <GHLOAuthSetup 
                  locationId={locationId}
                  onConnectionChange={handleGHLConnectionChange}
                />
              </div>

              <Separator />

              {/* Other Integrations */}
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold">Other Integrations</h3>
                  <p className="text-sm text-muted-foreground">
                    More integrations coming soon...
                  </p>
                </div>
                
                <div className="grid gap-4">
                  <Card className="opacity-50">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium">Zillow Integration</h4>
                          <p className="text-sm text-muted-foreground">
                            Sync property data and leads
                          </p>
                        </div>
                        <span className="text-sm text-muted-foreground">Coming Soon</span>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="opacity-50">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium">CRM Integration</h4>
                          <p className="text-sm text-muted-foreground">
                            Connect with popular CRM systems
                          </p>
                        </div>
                        <span className="text-sm text-muted-foreground">Coming Soon</span>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="account" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Account Settings</CardTitle>
              <CardDescription>
                Manage your account preferences and profile
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Account settings will be available soon...
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
              <CardDescription>
                Configure how you receive notifications
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Notification settings will be available soon...
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
} 