import CallVolumeChart from "@/components/charts/call-volume-chart";
import EngagementChart from "@/components/charts/engagement-chart";
import PipelineChart from "@/components/charts/pipeline-chart";
import StatusChart from "@/components/charts/status-chart";
import KPICards from "@/components/kpi-cards";
import LoadingAnimation, { LoadingSkeleton, TableLoadingSkeleton } from "@/components/loading-animation";
import TopNavigation from "@/components/top-navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { mockAPI } from "@/lib/mockData";
import { CYCLSALES_APP_ID } from "@/lib/constants";
import type { DashboardMetrics } from "@shared/schema";
import { Calendar, Filter, Search, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

export default function Contacts() {
  const [activeView, setActiveView] = useState<"metrics" | "table">("metrics");
  const [selectedLocation, setSelectedLocation] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [dateRange, setDateRange] = useState<string>("last_30_days");
  const [metrics, setMetrics] = useState<DashboardMetrics | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(true);
  
  // Contact table state
  const [contactsData, setContactsData] = useState<any[]>([]);
  const [contactsLoading, setContactsLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [rowsPerPage] = useState(10);
  const [hasMore, setHasMore] = useState(false);
  const [, setDetailedDataLoading] = useState<Set<number>>(new Set());
  const [, setContactDetails] = useState<Map<number, any>>(new Map());

  useEffect(() => {
    const loadContactData = async () => {
      try {
        const dashboardMetrics = await mockAPI.getDashboardMetrics();
        setMetrics(dashboardMetrics);
      } catch (error) {
        console.error("Failed to load contact data:", error);
      } finally {
        setIsLoading(false);
      }
    };

    loadContactData();
  }, []);

  // Load contacts when table view is active
  useEffect(() => {
    if (activeView === "table" && selectedLocation !== "all") {
      loadContacts();
    }
  }, [activeView, selectedLocation, page, rowsPerPage]);

  const loadContacts = async () => {
    if (selectedLocation === "all") return;
    
    setContactsLoading(true);
    try {
      const response = await fetch(`/api/location-contacts-optimized?location_id=${selectedLocation}&page=${page}&limit=${rowsPerPage}&appId=${CYCLSALES_APP_ID}`);
      const data = await response.json();
      
      if (data.success) {
        setContactsData(data.contacts || []);
        setHasMore(data.has_more || false);
        
        // If background sync was started, start polling for updates
        if (data.background_sync_started && data.contacts_syncing > 0) {
          startPollingForDetails(data.contacts.map((c: any) => c.id));
        }
      } else {
        setContactsData([]);
        setHasMore(false);
      }
    } catch (error) {
      console.error("Failed to load contacts:", error);
      setContactsData([]);
    } finally {
      setContactsLoading(false);
    }
  };

  // Poll for contact sync status
  const startPollingForDetails = (contactIds: number[]) => {
    if (contactIds.length === 0) return;
    
    setDetailedDataLoading(prev => new Set(Array.from(prev).concat(contactIds)));
    
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/contact-sync-status?contact_ids=${contactIds.join(',')}&appId=${CYCLSALES_APP_ID}`);
        const data = await response.json();
        
        if (data.success) {
          setContactDetails(prev => {
            const newMap = new Map(prev);
            data.contacts.forEach((contact: any) => {
              if (contact.details_fetched) {
                newMap.set(contact.contact_id, contact);
              }
            });
            return newMap;
          });
          
          setContactsData(prev => {
            let hasChanges = false;
            const updatedContacts = prev.map(contact => {
              const details = data.contacts.find((c: any) => c.contact_id === contact.id);
              if (details && details.details_fetched && !contact.details_fetched) {
                hasChanges = true;
                return {
                  ...contact,
                  tasks: details.tasks || [],
                  tasks_count: details.tasks_count || 0,
                  conversations: details.conversations || [],
                  conversations_count: details.conversations_count || 0,
                  details_fetched: true,
                  has_tasks: details.tasks_count > 0,
                  has_conversations: details.conversations_count > 0,
                  loading_details: false,
                  touch_summary: details.touch_summary || contact.touch_summary,
                  last_touch_date: details.last_touch_date || contact.last_touch_date,
                  last_message: details.last_message || contact.last_message,
                };
              } else if (details && !details.details_fetched) {
                return {
                  ...contact,
                  loading_details: true,
                };
              }
              return contact;
            });
            
            return hasChanges ? updatedContacts : prev;
          });
          
          if (data.sync_status.all_ready) {
            clearInterval(pollInterval);
            setDetailedDataLoading(prev => {
              const newSet = new Set(Array.from(prev));
              contactIds.forEach(id => newSet.delete(id));
              return newSet;
            });
          }
        }
      } catch (error) {
        console.error("Error polling for contact sync status:", error);
      }
    }, 2000);
    
    return () => clearInterval(pollInterval);
  };

  const handleRefresh = () => {
    if (activeView === "table") {
      loadContacts();
    }
  };

  return (
    <div className="min-h-screen w-full bg-slate-950 text-slate-50 overflow-x-hidden">
      <TopNavigation />
      
      <main className="p-8 max-w-full">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Contacts Dashboard</h1>
          <p className="text-slate-400">Manage and analyze your contact data</p>
        </div>

        {/* Filters Section */}
        <div className="bg-slate-900 rounded-lg p-6 mb-8">
          <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
            {/* View Toggle */}
            <div className="flex gap-2">
              <Button
                variant={activeView === "metrics" ? "default" : "outline"}
                onClick={() => setActiveView("metrics")}
                className={activeView === "metrics" ? "bg-blue-600 hover:bg-blue-700 text-white" : "border-slate-600 text-slate-300 hover:bg-slate-800 hover:text-white"}
              >
                Metrics
              </Button>
              <Button
                variant={activeView === "table" ? "default" : "outline"}
                onClick={() => setActiveView("table")}
                className={activeView === "table" ? "bg-blue-600 hover:bg-blue-700 text-white" : "border-slate-600 text-slate-300 hover:bg-slate-800 hover:text-white"}
              >
                Table
              </Button>
            </div>

            {/* Filters */}
            <div className="flex flex-col sm:flex-row gap-4 w-full lg:w-auto">
              {/* Location Selector for Table View */}
              {activeView === "table" && (
                <Select value={selectedLocation} onValueChange={setSelectedLocation}>
                  <SelectTrigger className="w-48 bg-slate-800 border-slate-700">
                    <SelectValue placeholder="Select Location" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-700">
                    <SelectItem value="all">All Locations</SelectItem>
                    <SelectItem value="Ipg8nKDPLYKsbtodR6LN">Main Location</SelectItem>
                  </SelectContent>
                </Select>
              )}

              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  placeholder="Search contacts..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 w-64 bg-slate-800 border-slate-700"
                />
              </div>

              {/* Date Range */}
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-slate-400" />
                <Select value={dateRange} onValueChange={setDateRange}>
                  <SelectTrigger className="w-40 bg-slate-800 border-slate-700">
                    <SelectValue placeholder="Date Range" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-700">
                    <SelectItem value="last_7_days">Last 7 Days</SelectItem>
                    <SelectItem value="last_30_days">Last 30 Days</SelectItem>
                    <SelectItem value="last_90_days">Last 90 Days</SelectItem>
                    <SelectItem value="custom">Custom Range</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Refresh Button */}
              <Button 
                variant="outline" 
                className="border-slate-700 hover:bg-slate-800"
                onClick={handleRefresh}
                disabled={contactsLoading}
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${contactsLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>

              {/* Additional Filters */}
              <Button variant="outline" className="border-slate-700 hover:bg-slate-800">
                <Filter className="w-4 h-4 mr-2" />
                More Filters
              </Button>
            </div>
          </div>
        </div>

        {/* Content based on active view */}
        {activeView === "metrics" ? (
          isLoading ? (
            <div>
              <LoadingAnimation size="md" message="Loading contact metrics..." />
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8 mt-8">
                {[...Array(4)].map((_, i) => (
                  <LoadingSkeleton key={i} />
                ))}
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {[...Array(4)].map((_, i) => (
                  <LoadingSkeleton key={i} />
                ))}
              </div>
            </div>
          ) : (
            <div>
              <KPICards metrics={metrics} />
              
              {/* Charts Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                <CallVolumeChart />
                <EngagementChart />
              </div>

              {/* Pipeline Overview */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
                <div className="lg:col-span-2">
                  <PipelineChart />
                </div>
                <StatusChart />
              </div>
            </div>
          )
        ) : (
          <div className="bg-slate-900 rounded-lg p-6">
            {selectedLocation === "all" ? (
              <div className="text-center py-12">
                <p className="text-slate-400 mb-4">Please select a location to view contacts</p>
                <Select value={selectedLocation} onValueChange={setSelectedLocation}>
                  <SelectTrigger className="w-48 bg-slate-800 border-slate-700 mx-auto">
                    <SelectValue placeholder="Select Location" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-700">
                    <SelectItem value="Ipg8nKDPLYKsbtodR6LN">Main Location</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            ) : contactsLoading ? (
              <TableLoadingSkeleton rows={8} />
            ) : (
              <div>
                {/* Contact Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-700">
                        <th className="text-left p-3 font-medium">Name</th>
                        <th className="text-left p-3 font-medium">Email</th>
                        <th className="text-left p-3 font-medium">Touch Summary</th>
                        <th className="text-left p-3 font-medium">Tasks</th>
                        <th className="text-left p-3 font-medium">Conversations</th>
                        <th className="text-left p-3 font-medium">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {contactsData.map((contact) => (
                        <tr key={contact.id} className="border-b border-slate-800 hover:bg-slate-800">
                          <td className="p-3">
                            <div className="font-medium">{contact.name}</div>
                          </td>
                          <td className="p-3 text-slate-300">{contact.email}</td>
                          <td className="p-3">
                            {contact.loading_details ? (
                              <div className="flex items-center gap-2">
                                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                                <span className="text-slate-400">Loading...</span>
                              </div>
                            ) : (
                              <span className="text-slate-300">{contact.touch_summary || 'No touches'}</span>
                            )}
                          </td>
                          <td className="p-3">
                            {contact.loading_details ? (
                              <div className="flex items-center gap-2">
                                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                                <span className="text-slate-400">Loading...</span>
                              </div>
                            ) : (
                              <span className="text-slate-300">{contact.tasks_count || 0}</span>
                            )}
                          </td>
                          <td className="p-3">
                            {contact.loading_details ? (
                              <div className="flex items-center gap-2">
                                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                                <span className="text-slate-400">Loading...</span>
                              </div>
                            ) : (
                              <span className="text-slate-300">{contact.conversations_count || 0}</span>
                            )}
                          </td>
                          <td className="p-3">
                            <span className={`px-2 py-1 rounded-full text-xs ${
                              contact.ai_status === 'valid_lead' ? 'bg-green-900 text-green-300' :
                              contact.ai_status === 'retention_path' ? 'bg-blue-900 text-blue-300' :
                              'bg-slate-800 text-slate-400'
                            }`}>
                              {contact.ai_status === 'valid_lead' ? 'Valid Lead' :
                               contact.ai_status === 'retention_path' ? 'Retention Path' :
                               contact.ai_status || 'Unknown'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                
                {/* Pagination */}
                <div className="flex justify-between items-center mt-6">
                  <div className="text-slate-400">
                    Showing {((page - 1) * rowsPerPage) + 1} to {Math.min(page * rowsPerPage, contactsData.length)} of {contactsData.length} contacts
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="border-slate-700 hover:bg-slate-800"
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(p => p + 1)}
                      disabled={!hasMore}
                      className="border-slate-700 hover:bg-slate-800"
                    >
                      Next
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}