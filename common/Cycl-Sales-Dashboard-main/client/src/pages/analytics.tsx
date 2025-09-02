import { useState, useEffect } from "react";
import TopNavigation from "@/components/top-navigation";
import AnalyticsContactsTable from "@/components/analytics-contacts-table";
import { Button } from "@/components/ui/button";
import { Calendar as CalendarIcon, Filter, Share2, User, Users, ChevronDown, RefreshCw } from "lucide-react";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { format } from "date-fns";
import type { DateRange } from "react-day-picker";
import { CYCLSALES_APP_ID, PROD_BASE_URL } from "@/lib/constants";
import { useSubAccount } from "@/contexts/SubAccountContext";

// Filter options
const aiStatusOptions = [
  "Valid Lead",
  "Wants to Stay - Retention Path",
  "Unqualified",
  "Not Contacted",
  "❄️ Cold Lead - No Recent Activity",
  "🔥 Hot Lead - Highly Engaged",
  "❌ API Error",
  "❌ Analysis Failed",
  "❌ No API Key",
  "❌ Invalid API Key",
  "❌ Data Too Large"
];

const aiQualityOptions = [
  "Lead Grade A",
  "Lead Grade B", 
  "Lead Grade C",
  "No Grade"
];

const aiSalesOptions = [
  "Sales Grade A",
  "Sales Grade B",
  "Sales Grade C", 
  "Sales Grade D",
  "No Grade"
];

const crmTasksOptions = [
  "1 Overdue",
  "2 Upcoming", 
  "No Tasks"
];

const categoryOptions = ["Integration", "Manual", "Automated", "Referral"];
const channelOptions = ["Integration", "Manual", "Automated", "Referral"];
const touchSummaryOptions = ["no_touches", "SMS", "PHONE CALL", "EMAIL", "OPPORTUNITY", "FACEBOOK", "WHATSAPP", "WEBCHAT", "REVIEW", "APPOINTMENT", "ACTIVITY"];



// Removed unused useQuery helper

// DateRangePicker (reuse from overview)
function DateRangePicker({ from, to, setRange }: { from: Date | undefined, to: Date | undefined, setRange: (range: DateRange | undefined) => void }) {
  const [open, setOpen] = useState(false);
  const formatRange = (from?: Date, to?: Date) =>
    from && to ? `${format(from, "MMM d, yyyy")} - ${format(to, "MMM d, yyyy")}` : "Select range";
  const trailingDays = (days: number) => {
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - (days - 1));
    setRange({ from: start, to: end });
    setOpen(false);
  };
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" className="bg-slate-900 border-slate-700 text-slate-200 font-medium flex gap-2 items-center min-w-[260px] justify-start">
          <CalendarIcon className="w-4 h-4 text-slate-400" />
          <span>{formatRange(from, to)}</span>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0 bg-slate-900 border-slate-700">
        <div className="flex flex-col gap-2">
          <Calendar
            mode="range"
            selected={{ from, to }}
            onSelect={setRange}
            numberOfMonths={2}
            className="bg-slate-900 text-slate-100"
          />
          <div className="flex gap-2 px-4 pb-2">
            <Button variant="outline" size="sm" className="flex-1" onClick={() => trailingDays(7)}>
              Trailing 7 days
            </Button>
            <Button variant="outline" size="sm" className="flex-1" onClick={() => trailingDays(30)}>
              Trailing 30 days
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}

export default function Analytics() {
  const query = new URLSearchParams(window.location.search);
  const { locationId: contextLocationId, isSubAccount } = useSubAccount();
  const locationId = isSubAccount ? contextLocationId : (query.get("location_id") || "");
  const [locationName, setLocationName] = useState<string>("");
  const [locationNameLoading, setLocationNameLoading] = useState(false);
  const [dateRange, setDateRange] = useState<DateRange>({ from: new Date("2025-05-12"), to: new Date("2025-05-18") });
  const [activeTab, setActiveTab] = useState("contacts");
  const [users, setUsers] = useState<any[]>([]);
  const [selectedUser, setSelectedUser] = useState<string>("");
  const [selectedUserExternalId, setSelectedUserExternalId] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [contactsLoading] = useState(false);
  const [syncStatus, setSyncStatus] = useState<string>("");
  const [refreshing, setRefreshing] = useState(false);
  
  // Agency-specific state for location selection
  const [availableLocations, setAvailableLocations] = useState<any[]>([]);
  const [locationsLoading, setLocationsLoading] = useState(false);
  const [locationSelectorOpen, setLocationSelectorOpen] = useState(false);
  
  // Filter state
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [activeFilters, setActiveFilters] = useState({
    aiStatus: [] as string[],
    aiQualityGrade: [] as string[],
    aiSalesGrade: [] as string[],
    crmTasks: [] as string[],
    category: [] as string[],
    channel: [] as string[],
    touchSummary: [] as string[],
  });

  // Fetch available locations for agency users
  useEffect(() => {
    if (!isSubAccount) {
      setLocationsLoading(true);
      fetch(`${PROD_BASE_URL}/api/installed-locations`)
        .then((res) => res.json())
        .then((data) => {
          setAvailableLocations(data.locations || []);
        })
        .catch((err) => {
          console.error("Failed to fetch locations:", err);
        })
        .finally(() => {
          setLocationsLoading(false);
        });
    }
  }, [isSubAccount]);

  // Helper functions for filters
  const toggleFilter = (filterType: keyof typeof activeFilters, value: string) => {
    setActiveFilters(prev => ({
      ...prev,
      [filterType]: prev[filterType].includes(value) 
        ? prev[filterType].filter(v => v !== value)
        : [...prev[filterType], value]
    }));
  };

  const clearAllFilters = () => {
    setActiveFilters({
      aiStatus: [],
      aiQualityGrade: [],
      aiSalesGrade: [],
      crmTasks: [],
      category: [],
      channel: [],
      touchSummary: [],
    });
  };

  const getActiveFiltersCount = () => {
    return Object.values(activeFilters).reduce((total, filters) => total + filters.length, 0);
  };

  useEffect(() => { 
    if (locationId) {
      setLocationNameLoading(true);
              fetch(`${PROD_BASE_URL}/api/location-name?location_id=${encodeURIComponent(locationId)}&appId=${CYCLSALES_APP_ID}`)
        .then(res => res.json())
        .then(data => {
          if (data.success && data.name) {
            setLocationName(data.name);
          } else {
            setLocationName("");
          }
        })
        .catch(() => setLocationName(""))
        .finally(() => setLocationNameLoading(false));

      // First, trigger the fetch from GHL API for users
      setLoading(true);
              fetch(`${PROD_BASE_URL}/api/get-location-users?location_id=${encodeURIComponent(locationId)}&appId=${CYCLSALES_APP_ID}`)
        .then(res => res.json())
        .then(data => { 
          // Then fetch users from our database
          return fetch(`${PROD_BASE_URL}/api/location-users?location_id=${encodeURIComponent(locationId)}&appId=${CYCLSALES_APP_ID}`);
        })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            setUsers(data.users || []);
          }
        })
        .catch(err => {
          console.error("Failed to fetch users:", err);
        })
        .finally(() => {
          setLoading(false);
        });

      // Contacts table handles its own data fetching
    } else {
      setLocationName("");
    }
  }, [locationId]);

  // Function to refresh contacts with fresh data
  const refreshContacts = async () => {
    if (!locationId) return;
    
    setRefreshing(true);
    try {
      // Trigger backend refresh; table fetches independently
      const response = await fetch(`${PROD_BASE_URL}/api/location-contacts-optimized?location_id=${encodeURIComponent(locationId)}&page=1&limit=10&appId=${CYCLSALES_APP_ID}`);
      const data = await response.json();
      if (data.success) {
        setSyncStatus("Data refreshed successfully");
        setTimeout(() => setSyncStatus(""), 3000);
      } else {
        console.error("Failed to refresh contacts:", data.error);
        setSyncStatus("Failed to refresh data");
        setTimeout(() => setSyncStatus(""), 3000);
      }
    } catch (error) {
      console.error("Error refreshing contacts:", error);
      setSyncStatus("Error refreshing data");
      setTimeout(() => setSyncStatus(""), 3000);
    } finally {
      setRefreshing(false);
    }
  };

  // Function to sync all contacts from GHL API
  const syncAllContacts = async () => {
    if (!locationId) return;
    
    setRefreshing(true);
    setSyncStatus("Starting full GHL sync...");
    
    try {
      const response = await fetch(`${PROD_BASE_URL}/api/sync-location-contacts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          location_id: locationId,
          appId: CYCLSALES_APP_ID
        })
      });
      
      const data = await response.json();
      if (data.success) {
        setSyncStatus("Full GHL sync started successfully. This may take several minutes.");
        setTimeout(() => setSyncStatus(""), 10000);
        
        // Wait a bit then refresh the contacts table to show updated counts
        setTimeout(async () => {
          try {
            const refreshResponse = await fetch(`${PROD_BASE_URL}/api/location-contacts-optimized?location_id=${encodeURIComponent(locationId)}&page=1&limit=10&appId=${CYCLSALES_APP_ID}`);
            const refreshData = await refreshResponse.json();
            if (refreshData.success) {
              setSyncStatus("Sync completed! Refreshed contact data.");
              setTimeout(() => setSyncStatus(""), 5000);
            }
          } catch (refreshError) {
            console.error("Error refreshing after sync:", refreshError);
          }
        }, 5000);
      } else {
        console.error("Failed to start sync:", data.error);
        setSyncStatus("Failed to start sync: " + (data.error || "Unknown error"));
        setTimeout(() => setSyncStatus(""), 5000);
      }
    } catch (error) {
      console.error("Error starting sync:", error);
      setSyncStatus("Error starting sync: " + (error instanceof Error ? error.message : String(error)));
      setTimeout(() => setSyncStatus(""), 5000);
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-slate-950 text-slate-50 overflow-x-hidden">
      {!isSubAccount && <TopNavigation />}
      <main className="p-8 max-w-full">
        {/* Top Filters Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900 rounded-2xl p-6 shadow-lg mb-6">
          <div className="flex flex-wrap gap-2 items-center">
            {/* Location selector - conditional based on user type */}
            {!isSubAccount ? (
              // Agency users get a location selector
              <Popover open={locationSelectorOpen} onOpenChange={setLocationSelectorOpen}>
                <PopoverTrigger asChild>
                  <Button variant="secondary" className="bg-blue-900 text-blue-300 font-semibold flex gap-2 items-center min-w-[200px] justify-between">
                    <Users className="w-4 h-4" />
                    <span>{locationNameLoading ? "Loading..." : (locationName || locationId || "Select location")}</span>
                    <ChevronDown className="w-4 h-4" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0 bg-slate-900 border-slate-700">
                  <div className="p-2">
                    {locationsLoading ? (
                      <div className="text-slate-400 text-sm p-2">Loading locations...</div>
                    ) : availableLocations.length > 0 ? (
                      <div className="max-h-60 overflow-y-auto">
                        {availableLocations.map((location) => (
                          <button
                            key={location.location_id}
                            className="w-full text-left px-3 py-2 text-sm text-slate-200 hover:bg-slate-800 rounded-md flex flex-col"
                            onClick={() => {
                              window.location.href = `/analytics?location_id=${encodeURIComponent(location.location_id)}`;
                              setLocationSelectorOpen(false);
                            }}
                          >
                            <span className="font-medium">{location.location}</span>
                            <span className="text-xs text-slate-400">{location.automationGroup}</span>
                          </button>
                        ))}
                      </div>
                    ) : (
                      <div className="text-slate-400 text-sm p-2">No locations found</div>
                    )}
                  </div>
                </PopoverContent>
              </Popover>
            ) : (
              // Sub-account users get a non-clickable display
              <Button variant="secondary" className="bg-blue-900 text-blue-300 font-semibold flex gap-2 items-center">
                <Users className="w-4 h-4" />
                {locationNameLoading ? "Loading..." : (locationName || locationId)}
              </Button>
            )}
            {/* User selector */}
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" className="bg-slate-800 text-slate-200 flex gap-2 items-center min-w-[200px] justify-between">
                  <User className="w-4 h-4" />
                  <span>{selectedUser || "Choose user"}</span>
                  <ChevronDown className="w-4 h-4" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0 bg-slate-900 border-slate-700">
                <div className="p-2">
                  {loading ? (
                    <div className="text-slate-400 text-sm p-2">Loading users...</div>
                  ) : users.length > 0 ? (
                    <div className="max-h-60 overflow-y-auto">
                      {users.map((user) => (
                        <button
                          key={user.id}
                          className="w-full text-left px-3 py-2 text-sm text-slate-200 hover:bg-slate-800 rounded-md flex flex-col"
                          onClick={() => {
                            const displayName = user.name || `${user.first_name} ${user.last_name}`;
                            setSelectedUser(displayName);
                            setSelectedUserExternalId(user.external_id || "");
                            console.log(`Selected user: ${displayName} with external_id: ${user.external_id}`);
                          }}
                        >
                          <span className="font-medium">{user.name || `${user.first_name} ${user.last_name}`}</span>
                          <span className="text-xs text-slate-400">{user.email}</span>
                          {/* {user.role && <span className="text-xs text-blue-400">{user.role}</span>} */}
                        </button>
                      ))}
                    </div>
                  ) : (
                    <div className="text-slate-400 text-sm p-2">No users found</div>
                  )}
                  {selectedUser && (
                    <div className="border-t border-slate-700 pt-2 mt-2">
                      <button
                        className="w-full text-left px-3 py-2 text-sm text-red-400 hover:bg-slate-800 rounded-md"
                        onClick={() => {
                          setSelectedUser("");
                          setSelectedUserExternalId("");
                          console.log("Cleared user selection");
                        }}
                      >
                        Clear Selection
                      </button>
                    </div>
                  )}
                </div>
              </PopoverContent>
            </Popover>

            {/* More Filters */}
            <Popover open={filtersOpen} onOpenChange={setFiltersOpen}>
              <PopoverTrigger asChild>
                <Button variant="outline" className="bg-slate-800 text-slate-200 flex gap-2 items-center">
                  <Filter className="w-4 h-4" />
                  More Filters
                  {getActiveFiltersCount() > 0 && (
                    <span className="ml-1 bg-blue-600 text-white text-xs px-1.5 py-0.5 rounded-full">
                      {getActiveFiltersCount()}
                    </span>
                  )}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-96 p-4 bg-slate-900 border-slate-700" align="start">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-white">Filters</h3>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={clearAllFilters}
                      className="text-slate-400 hover:text-white"
                    >
                      Clear All
                    </Button>
                  </div>
                  
                  {/* AI Status Filter */}
                  <div>
                    <h4 className="text-sm font-medium text-slate-300 mb-2">AI Status</h4>
                    <div className="space-y-1">
                      {aiStatusOptions.map((option) => (
                        <label key={option} className="flex items-center space-x-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={activeFilters.aiStatus.includes(option)}
                            onChange={() => toggleFilter('aiStatus', option)}
                            className="rounded border-slate-600 bg-slate-800 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="text-sm text-slate-200">{option}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* AI Quality Grade Filter */}
                  <div>
                    <h4 className="text-sm font-medium text-slate-300 mb-2">AI Quality Grade</h4>
                    <div className="space-y-1">
                      {aiQualityOptions.map((option) => (
                        <label key={option} className="flex items-center space-x-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={activeFilters.aiQualityGrade.includes(option)}
                            onChange={() => toggleFilter('aiQualityGrade', option)}
                            className="rounded border-slate-600 bg-slate-800 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="text-sm text-slate-200">{option}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* AI Sales Grade Filter */}
                  <div>
                    <h4 className="text-sm font-medium text-slate-300 mb-2">AI Sales Grade</h4>
                    <div className="space-y-1">
                      {aiSalesOptions.map((option) => (
                        <label key={option} className="flex items-center space-x-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={activeFilters.aiSalesGrade.includes(option)}
                            onChange={() => toggleFilter('aiSalesGrade', option)}
                            className="rounded border-slate-600 bg-slate-800 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="text-sm text-slate-200">{option}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* CRM Tasks Filter */}
                  <div>
                    <h4 className="text-sm font-medium text-slate-300 mb-2">CRM Tasks</h4>
                    <div className="space-y-1">
                      {crmTasksOptions.map((option) => (
                        <label key={option} className="flex items-center space-x-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={activeFilters.crmTasks.includes(option)}
                            onChange={() => toggleFilter('crmTasks', option)}
                            className="rounded border-slate-600 bg-slate-800 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="text-sm text-slate-200">{option}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Category Filter */}
                  <div>
                    <h4 className="text-sm font-medium text-slate-300 mb-2">Category</h4>
                    <div className="space-y-1">
                      {categoryOptions.map((option) => (
                        <label key={option} className="flex items-center space-x-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={activeFilters.category.includes(option)}
                            onChange={() => toggleFilter('category', option)}
                            className="rounded border-slate-600 bg-slate-800 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="text-sm text-slate-200">{option}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Channel Filter */}
                  <div>
                    <h4 className="text-sm font-medium text-slate-300 mb-2">Channel</h4>
                    <div className="space-y-1">
                      {channelOptions.map((option) => (
                        <label key={option} className="flex items-center space-x-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={activeFilters.channel.includes(option)}
                            onChange={() => toggleFilter('channel', option)}
                            className="rounded border-slate-600 bg-slate-800 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="text-sm text-slate-200">{option}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Touch Summary Filter */}
                  <div>
                    <h4 className="text-sm font-medium text-slate-300 mb-2">Touch Summary</h4>
                    <div className="space-y-1">
                      {touchSummaryOptions.map((option) => (
                        <label key={option} className="flex items-center space-x-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={activeFilters.touchSummary.includes(option)}
                            onChange={() => toggleFilter('touchSummary', option)}
                            className="rounded border-slate-600 bg-slate-800 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="text-sm text-slate-200">{option}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
              </PopoverContent>
            </Popover>
          </div>
          <div className="flex flex-wrap gap-2 items-center">
            {/* Tab switch */}
            <div className="flex bg-slate-800 rounded-md p-0.5 gap-0.5">
              <button
                className={`px-3 py-0.5 rounded-md font-medium transition-colors focus:outline-none text-xs h-7 ${activeTab === "contacts" ? "bg-slate-900 text-white shadow" : "text-slate-400 hover:text-white"}`}
                onClick={() => setActiveTab("contacts")}
              >
                Contacts
              </button>
              <button
                className={`px-3 py-0.5 rounded-md font-medium transition-colors focus:outline-none text-xs h-7 ${activeTab === "calls" ? "bg-slate-900 text-white shadow" : "text-slate-400 hover:text-white"}`}
                onClick={() => setActiveTab("calls")}
              >
                Calls
              </button>
            </div>
            {/* Date range picker */}
            <DateRangePicker from={dateRange.from} to={dateRange.to} setRange={(range) => setDateRange(range ?? { from: undefined, to: undefined })} />
            {/* Share button */}
            <Button variant="outline" className="bg-blue-900 text-blue-300 border-blue-700 flex gap-2 items-center">
              <Share2 className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* KPI Cards Row */}
        {/* <KPICards metrics={undefined} /> */}

        {/* Funnel and Speed to Lead Section */}
        {/* <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6"> 
          <div className="lg:col-span-2 bg-slate-900 rounded-2xl p-6 shadow-lg flex flex-col">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-200 font-semibold">Template: Generic Default</span>
            </div>
            <div className="flex-1 flex items-center justify-center"> 
              <div className="w-full h-64 flex items-center justify-center">
                <span className="text-blue-500 text-6xl">&#x25B2;</span> 
              </div>
            </div>
          </div> 
          <div className="bg-slate-900 rounded-2xl p-6 shadow-lg flex flex-col">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-200 font-semibold">Speed to Lead Distribution</span> 
            </div>
            <div className="flex-1 flex items-center justify-center">
              <span className="text-slate-400 text-3xl">¯\\_(ツ)_/¯<br />No data available.</span>
            </div>
          </div>
        </div> */}

        {/* Contacts Table Section */}
        <div className="bg-slate-900 rounded-2xl p-6 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <span className="text-lg font-semibold text-white">Contacts</span>
              {syncStatus && (
                <div className="flex items-center gap-2 px-3 py-1 bg-blue-900/50 border border-blue-700 rounded-md">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                  <span className="text-blue-300 text-sm">{syncStatus}</span>
                </div>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button 
                variant="outline" 
                className="flex gap-2 items-center bg-slate-800 text-slate-200 border-slate-700"
                onClick={refreshContacts}
                disabled={refreshing}
              >
                <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
                {refreshing ? 'Refreshing...' : 'Refresh'}
              </Button>
              <Button 
                variant="outline" 
                className="flex gap-2 items-center bg-blue-800 text-blue-200 border-blue-700 hover:bg-blue-700"
                onClick={syncAllContacts}
                disabled={refreshing}
              >
                <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
                {refreshing ? 'Syncing...' : 'Sync All Contacts'}
              </Button>
              <Button variant="outline" className="flex gap-2 items-center bg-slate-800 text-slate-200 border-slate-700">
                <Filter className="w-4 h-4" />
                Customize Columns
              </Button>
              <Button 
                variant="outline" 
                className="flex gap-2 items-center bg-yellow-800 text-yellow-200 border-yellow-700 hover:bg-yellow-700"
                onClick={() => {
                  console.log('Debug info:');
                  console.log('  - selectedUser:', selectedUser);
                  console.log('  - selectedUserExternalId:', selectedUserExternalId);
                  console.log('  - locationId:', locationId);
                  console.log('  - users count:', users.length);
                  console.log('  - users:', users);
                }}
                title="Debug user filtering"
              >
                🐛 Debug
              </Button>
            </div>
          </div>
          <AnalyticsContactsTable 
            loading={contactsLoading} 
            locationId={locationId || ""} 
            selectedUser={selectedUserExternalId || selectedUser} 
            activeFilters={activeFilters} 
          />
          {/* Debug info */}
          {selectedUser && (
            <div className="mt-4 p-3 bg-slate-800 rounded-lg text-xs text-slate-300">
              <div><strong>Debug Info:</strong></div>
              <div>Selected User: {selectedUser}</div>
              <div>External ID: {selectedUserExternalId || 'None'}</div>
              <div>Sent to Table: {selectedUserExternalId || selectedUser}</div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
} 