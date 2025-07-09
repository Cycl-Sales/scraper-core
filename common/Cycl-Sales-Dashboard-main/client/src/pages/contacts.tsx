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
import type { DashboardMetrics } from "@shared/schema";
import { Calendar, Filter, Search } from "lucide-react";
import { useEffect, useState } from "react";

export default function Contacts() {
  const [activeView, setActiveView] = useState<"metrics" | "table">("metrics");
  const [selectedLocation, setSelectedLocation] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [dateRange, setDateRange] = useState<string>("last_30_days");
  const [metrics, setMetrics] = useState<DashboardMetrics | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(true);

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
          <div>
            <TableLoadingSkeleton rows={8} />
          </div>
        )}
      </main>
    </div>
  );
}