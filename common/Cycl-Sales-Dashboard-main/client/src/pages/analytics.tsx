import { useState, useEffect } from "react";
import { useLocation } from "wouter";
import TopNavigation from "@/components/top-navigation";
import KPICards from "@/components/kpi-cards";
import AnalyticsContactsTable from "@/components/analytics-contacts-table";
import { Button } from "@/components/ui/button";
import { Calendar as CalendarIcon, Filter, Share2, User, Users, ChevronDown } from "lucide-react";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { format } from "date-fns";
import type { DateRange } from "react-day-picker";

function useQuery() {
  const [location] = useLocation();
  console.log("Current location from useLocation:", location);
  return new URLSearchParams(location.split('?')[1] || '');
}

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
  const locationId = query.get("location_id") || "";
  const [locationName, setLocationName] = useState<string>("");
  const [locationNameLoading, setLocationNameLoading] = useState(false);
  const [dateRange, setDateRange] = useState<DateRange>({ from: new Date("2025-05-12"), to: new Date("2025-05-18") });
  const [activeTab, setActiveTab] = useState("contacts");
  const [users, setUsers] = useState<any[]>([]);
  const [selectedUser, setSelectedUser] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [contacts, setContacts] = useState<any[]>([]);
  const [contactsLoading, setContactsLoading] = useState(false);

  useEffect(() => {
    console.log("locationId from query:", locationId);
    if (locationId) {
      setLocationNameLoading(true);
      fetch(`/api/location-name?location_id=${encodeURIComponent(locationId)}`)
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
      fetch(`/api/get-location-users?location_id=${encodeURIComponent(locationId)}`)
        .then(res => res.json())
        .then(data => {
          console.log("Triggered GHL user fetch:", data);
          // Then fetch users from our database
          return fetch(`/api/location-users?location_id=${encodeURIComponent(locationId)}`);
        })
        .then(res => res.json())
        .then(data => {
          console.log("Fetched users from database:", data);
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

      // Fetch contacts data
      setContactsLoading(true);
      fetch(`/api/get-location-contacts?location_id=${encodeURIComponent(locationId)}`)
        .then(res => res.json())
        .then(data => {
          console.log("Triggered GHL contacts fetch:", data);
          // Then fetch contacts from our database
          return fetch(`/api/location-contacts?location_id=${encodeURIComponent(locationId)}`);
        })
        .then(res => res.json())
        .then(data => {
          console.log("Fetched contacts from database:", data);
          if (data.success) {
            setContacts(data.contacts || []);
          }
        })
        .catch(err => {
          console.error("Failed to fetch contacts:", err);
        })
        .finally(() => {
          setContactsLoading(false);
        });
    } else {
      setLocationName("");
    }
  }, [locationId]);

  return (
    <div className="min-h-screen w-full bg-slate-950 text-slate-50 overflow-x-hidden">
      <TopNavigation />
      <main className="p-8 max-w-full">
        {/* Top Filters Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900 rounded-2xl p-6 shadow-lg mb-6">
          <div className="flex flex-wrap gap-2 items-center">
            {/* Location selector (pre-selected) */}
            <Button variant="secondary" className="bg-blue-900 text-blue-300 font-semibold flex gap-2 items-center">
              <Users className="w-4 h-4" />
              {locationNameLoading ? "Loading..." : (locationName || locationId)}
            </Button>
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
                          onClick={() => setSelectedUser(user.name || `${user.first_name} ${user.last_name}`)}
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
                </div>
              </PopoverContent>
            </Popover>
            {/* More Filters */}
            <Button variant="outline" className="bg-slate-800 text-slate-200 flex gap-2 items-center">
              <Filter className="w-4 h-4" />
              More Filters
            </Button>
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
        <KPICards metrics={undefined} />

        {/* Funnel and Speed to Lead Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Funnel Chart Placeholder */}
          <div className="lg:col-span-2 bg-slate-900 rounded-2xl p-6 shadow-lg flex flex-col">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-200 font-semibold">Template: Generic Default</span>
              {/* Dropdown for template selection can go here */}
            </div>
            <div className="flex-1 flex items-center justify-center">
              {/* Funnel Chart Placeholder */}
              <div className="w-full h-64 flex items-center justify-center">
                <span className="text-blue-500 text-6xl">&#x25B2;</span>
                {/* Replace with actual funnel chart */}
              </div>
            </div>
          </div>
          {/* Speed to Lead Distribution Placeholder */}
          <div className="bg-slate-900 rounded-2xl p-6 shadow-lg flex flex-col">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-200 font-semibold">Speed to Lead Distribution</span>
              {/* Dropdown for chart type can go here */}
            </div>
            <div className="flex-1 flex items-center justify-center">
              <span className="text-slate-400 text-3xl">¯\\_(ツ)_/¯<br />No data available.</span>
            </div>
          </div>
        </div>

        {/* Contacts Table Section */}
        <div className="bg-slate-900 rounded-2xl p-6 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <span className="text-lg font-semibold text-white">Contacts</span>
            <Button variant="outline" className="flex gap-2 items-center bg-slate-800 text-slate-200 border-slate-700">
              <Filter className="w-4 h-4" />
              Customize Columns
            </Button>
          </div>
          <AnalyticsContactsTable contacts={contacts} loading={contactsLoading} />
        </div>
      </main>
    </div>
  );
} 