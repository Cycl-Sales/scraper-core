import TopNavigation from "@/components/top-navigation";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Switch } from "@/components/ui/switch";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { format } from "date-fns";
import { Calendar as CalendarIcon, HelpCircle, RefreshCw } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { DateRange } from "react-day-picker";
import { useLocation } from "wouter"; 

const columnHelpers: Record<string, string> = {
  "Location Name": "Name of the business location.",
  "Automation Group": "The automation template or group assigned to this location.",
  "Ad Accounts": "Statuses of the ad accounts",
  "Total Ad Spend": "Total ad spend over the total revenue (sum of opportunities marked as won). This includes all contacts, not just those generated directly by the advertising.",
  "Cost per Conversion": "Total ad spend over the total count of conversion events on all advertising campaigns",
  "New Contacts": "Total count of new contacts created over the selected period, excluding manually created contacts.",
  "Median AI Quality Grade": "Median grade of all the contact quality overall, determined with AI in your automations",
  "Touch Rate": "Percentage of contacts that were touched with any kind of manual outbound message or call",
  "Engagement Rate": "Percentage of contacts that answered the phone, messaged back, or called at any point",
  "Speed to Lead": "Median time it takes from when a contact is created to when the first manual outbound message or call is made",
  "Median AI Sales Grade": "Median grade of all the sales conversations overall, determined with AI in your automations",
  "Close Rate": "Percentage of contacts that have at least one opportunity marked as won",
  "Revenue per Contact": "Average revenue per contact",
  "Gross ROAS": "Total ad spend over the total revenue (sum of opportunities marked as won). This includes all contacts, not just those generated directly by the advertising.",
};

const columns = [
  { label: "Location Name" },
  { label: "Automation Group" },
  { label: "Ad Accounts" },
  { label: "Total Ad Spend" },
  { label: "Cost per Conversion" },
  { label: "New Contacts" },
  { label: "Median AI Quality Grade" },
  { label: "Touch Rate" },
  { label: "Engagement Rate" },
  { label: "Speed to Lead" },
  { label: "Median AI Sales Grade" },
  { label: "Close Rate" },
  { label: "Revenue per Contact" },
  { label: "Gross ROAS" },
];

// Helper to get outlined badge classes for grades
function getGradeBadgeClass(grade: string) {
  if (grade.includes("D")) return "border border-red-600 text-red-400 bg-transparent";
  if (grade.includes("C")) return "border border-yellow-500 text-yellow-400 bg-transparent";
  if (grade.includes("B")) return "border border-green-600 text-green-400 bg-transparent";
  return "border border-slate-600 text-slate-300 bg-transparent";
}

// DateRangePicker component
function DateRangePicker({ from, to, setRange }: { from: Date | undefined, to: Date | undefined, setRange: (range: DateRange | undefined) => void }) {
  const [open, setOpen] = useState(false);
  const formatRange = (from?: Date, to?: Date) =>
    from && to ? `${format(from, "MMM d, yyyy")} - ${format(to, "MMM d, yyyy")}` : "Select range";

  // Quick select helpers
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

export default function Overview() {
  const [activeTab, setActiveTab] = useState("locations");
  const [activeOnly, setActiveOnly] = useState(false);
  const [dateRange, setDateRange] = useState<DateRange>({ from: new Date("2025-05-12"), to: new Date("2025-05-18") });
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [fetchedLocations, setFetchedLocations] = useState<any[]>([]);
  const [syncStatus, setSyncStatus] = useState<string>("");
  const [refreshing, setRefreshing] = useState(false);
  const [, setLocation] = useLocation();
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    setLoading(true);
    fetch("/api/installed-locations")
      .then((res) => res.json())
      .then((data) => {
        setFetchedLocations(data.locations || []);
        if (data.sync_status === "background") {
          setSyncStatus(data.message || "Background sync in progress...");
          // Start polling
          if (!pollRef.current) {
            pollRef.current = setInterval(async () => {
              const statusResponse = await fetch("/api/installed-locations-sync-status");
              const statusData = await statusResponse.json();
              if (statusData.status === "completed") {
                setFetchedLocations(statusData.locations || []);
                setSyncStatus("Data updated successfully!");
                setTimeout(() => setSyncStatus(""), 3000);
                clearInterval(pollRef.current!);
                pollRef.current = null;
              } else if (statusData.status === "failed") {
                setSyncStatus(`Sync failed: ${statusData.error || "Unknown error"}`);
                setTimeout(() => setSyncStatus(""), 5000);
                clearInterval(pollRef.current!);
                pollRef.current = null;
              }
            }, 2000);
          }
        } else {
          setSyncStatus("");
        }
      })
      .catch(() => {
        setSyncStatus("");
      })
      .finally(() => setLoading(false));

  // Cleanup on unmount
  return () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };
}, []);

  // Function to refresh locations with fresh data
  const refreshLocations = async () => {
    setRefreshing(true);
    try {
      // Use the fresh endpoint for immediate sync
      const response = await fetch("/api/installed-locations-fresh");
      const data = await response.json();
      
      if (data.locations) {
        setFetchedLocations(data.locations || []);
        setSyncStatus("Data refreshed successfully");
        setTimeout(() => setSyncStatus(""), 3000);
      } else {
        console.error("Failed to refresh locations:", data.error);
        setSyncStatus("Failed to refresh data");
        setTimeout(() => setSyncStatus(""), 3000);
      }
    } catch (error) {
      console.error("Error refreshing locations:", error);
      setSyncStatus("Error refreshing data");
      setTimeout(() => setSyncStatus(""), 3000);
    } finally {
      setRefreshing(false);
    }
  };

  const totalPages = Math.ceil(fetchedLocations.length / rowsPerPage);
  const paginatedRows = fetchedLocations.slice((page - 1) * rowsPerPage, page * rowsPerPage);

  return (
    <div className="min-h-screen w-full bg-slate-950 text-slate-50 overflow-x-hidden">
      <TopNavigation />
      <main className="p-8 max-w-full">
        <div className="bg-slate-900 rounded-2xl p-6 shadow-lg max-w-full">
          {/* Tabs and Filters Row */}
          <div className="flex items-center justify-between mb-4 w-full">
            {/* Tabs */}
            <div className="flex bg-slate-800 rounded-md p-0.5 gap-0.5">
              <button
                className={`px-3 py-0.5 rounded-md font-medium transition-colors focus:outline-none text-xs h-7 ${
                  activeTab === "locations"
                    ? "bg-slate-900 text-white shadow"
                    : "text-slate-400 hover:text-white"
                }`}
                onClick={() => setActiveTab("locations")}
              >
                Locations
              </button>
              <button
                className={`px-3 py-0.5 rounded-md font-medium transition-colors focus:outline-none text-xs h-7 ${
                  activeTab === "users"
                    ? "bg-slate-900 text-white shadow"
                    : "text-slate-400 hover:text-white"
                }`}
                onClick={() => setActiveTab("users")}
              >
                Users
              </button>
            </div>
            {/* Filters */}
            <div className="flex flex-wrap gap-4 items-center">
              <div className="flex gap-2 items-center">
                <span className="text-slate-300 font-medium text-xs">Active Only</span>
                <Switch checked={activeOnly} onCheckedChange={setActiveOnly} />
              </div>
              <DateRangePicker from={dateRange.from} to={dateRange.to} setRange={(range) => setDateRange(range ?? { from: undefined, to: undefined })} />
              <Button 
                variant="outline" 
                className="flex gap-2 items-center bg-slate-800 text-slate-200 border-slate-700"
                onClick={refreshLocations}
                disabled={refreshing}
              >
                <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
                {refreshing ? 'Refreshing...' : 'Refresh'}
              </Button>
            </div>
          </div>

          {/* Sync Status Indicator */}
          {syncStatus && (
            <div className="flex items-center gap-2 px-3 py-2 bg-blue-900/50 border border-blue-700 rounded-md mb-4">
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
              <span className="text-blue-300 text-sm">{syncStatus}</span>
            </div>    
          )}

          {/* Table or Skeleton */}
          {loading ? (
            <div className="animate-pulse">
              <div className="h-8 bg-slate-800 rounded mb-2 w-full max-w-[1200px]" />
              {[...Array(10)].map((_, i) => (
                <div key={i} className="h-6 bg-slate-800 rounded mb-2 w-full max-w-[1200px]" />
              ))}
            </div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900 relative" style={{ isolation: 'isolate' }}>
              <table className="w-full min-w-[1200px] text-sm">
                  <thead>
                    <tr className="border-b border-slate-800">
                      {columns.map((col, idx) => (
                        <th
                          key={col.label}
                          className={`text-left py-3 px-4 font-medium text-slate-400 whitespace-nowrap ${idx === 0 ? 'sticky left-0 z-10 bg-slate-900' : ''} overflow-visible`}
                        >
                          <span className="inline-flex items-center gap-1">
                            {col.label}
                            {columnHelpers[col.label] && (
                              <Tooltip delayDuration={0}>
                                <TooltipTrigger asChild>
                                  <button className="inline-flex items-center justify-center w-4 h-4 text-slate-400 hover:text-blue-400 cursor-pointer bg-transparent border-none p-0">
                                    <HelpCircle className="w-4 h-4" />
                                  </button>
                                </TooltipTrigger>
                                <TooltipContent side="top" align="center" sideOffset={8} className="bg-slate-800 text-slate-100 text-xs px-3 py-2 rounded-lg shadow-lg max-w-xs w-max whitespace-pre-line break-words z-[9999]">
                                  {columnHelpers[col.label]}
                                </TooltipContent>
                              </Tooltip>
                            )}
                          </span>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedRows.map((row, i) => (
                      <tr key={i} className="border-b border-slate-800 hover:bg-slate-800/50">
                        <td className="py-3 px-4 text-white font-semibold whitespace-nowrap sticky left-0 z-10 bg-slate-900">
                          <button
                            className="text-blue-400 hover:underline hover:text-blue-300 transition cursor-pointer bg-transparent border-none p-0 m-0 font-semibold"
                            onClick={() => setLocation(`/analytics?location_id=${encodeURIComponent(row.location_id)}`)}
                          >
                            {row.location}
                          </button>
                        </td>
                        <td className="py-3 px-4 text-slate-400 whitespace-nowrap">
                          {row.automationGroup}
                        </td>
                        <td className="py-3 px-4 text-slate-300 whitespace-nowrap">{row.adAccounts}</td>
                        <td className="py-3 px-4 text-slate-300 whitespace-nowrap">{row.totalAdSpend}</td>
                        <td className="py-3 px-4 whitespace-nowrap">
                          <span className="bg-slate-800 text-blue-300 px-2 py-1 rounded-full font-semibold">
                            {row.costPerConversion}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-slate-300 whitespace-nowrap">
                          {row.newContacts}
                          <span className="ml-2 bg-blue-900 text-blue-300 px-2 py-0.5 rounded-full text-xs font-semibold">
                            {row.newContactsChange}
                          </span>
                        </td>
                        <td className="py-3 px-4 whitespace-nowrap">
                          <span className={`px-2 py-0.5 font-semibold rounded-md ${getGradeBadgeClass(row.medianAIQualityGrade)}`}>
                            Σ {row.medianAIQualityGrade}
                          </span>
                        </td>
                        <td className="py-3 px-4 whitespace-nowrap">
                          <span className="bg-slate-800 text-blue-300 px-2 py-1 rounded-full font-semibold">
                            {row.touchRate}
                          </span>
                          <span className="ml-2 bg-red-900 text-red-400 px-2 py-0.5 rounded-full text-xs font-semibold">
                            {row.touchRateChange}
                          </span>
                        </td>  
                        <td className="py-3 px-4 whitespace-nowrap">
                          {row.engagementRate}
                          <span className="ml-2 bg-green-900 text-green-400 px-2 py-0.5 rounded-full text-xs font-semibold">
                            {row.engagementRateChange}
                          </span>
                        </td>
                        <td className="py-3 px-4 whitespace-nowrap">
                          <span className="bg-slate-800 text-blue-300 px-2 py-1 rounded-full font-semibold">
                            {row.speedToLead}
                          </span>
                        </td>
                        <td className="py-3 px-4 whitespace-nowrap">
                          <span className={`px-2 py-0.5 rounded-md font-semibold ${getGradeBadgeClass(row.medianAISalesGrade)}`}>
                            Σ {row.medianAISalesGrade}
                          </span>
                        </td>
                        <td className="py-3 px-4 whitespace-nowrap">
                          <span className="bg-slate-800 text-blue-300 px-2 py-1 rounded-full font-semibold">
                            {row.closeRate}
                          </span>
                        </td>
                        <td className="py-3 px-4 whitespace-nowrap">
                          <span className="bg-slate-800 text-blue-300 px-2 py-1 rounded-full font-semibold">
                            {row.revenuePerContact}
                          </span>
                        </td>
                        <td className="py-3 px-4 whitespace-nowrap">
                          <span className="bg-slate-800 text-blue-300 px-2 py-1 rounded-full font-semibold">
                            {row.grossROAS}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
            </div>
          )}

          {/* Pagination and Rows per page */}
          <div className="flex items-center justify-between mt-4">
            <div className="flex items-center gap-2">
              <span className="text-slate-300">Rows per page:</span>
              <select
                value={rowsPerPage}
                onChange={e => {
                  setRowsPerPage(Number(e.target.value));
                  setPage(1);
                }}
                className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200"
              >
                {[10, 25, 50].map(n => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </div>
            <div className="text-slate-400">
              Showing {(page - 1) * rowsPerPage + 1}-{Math.min(page * rowsPerPage, fetchedLocations.length)} of {fetchedLocations.length} locations
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                className="border-slate-700 text-slate-300"
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
              >
                Previous
              </Button>
              <span className="text-slate-300 text-sm my-auto">Page {page} of {totalPages}</span>
              <Button
                variant="outline"
                className="border-slate-700 text-slate-300"
                disabled={page === totalPages}
                onClick={() => setPage(page + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}