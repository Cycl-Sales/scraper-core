import CallVolumeChart from "@/components/charts/call-volume-chart";
import EngagementChart from "@/components/charts/engagement-chart";
import PipelineChart from "@/components/charts/pipeline-chart";
import StatusChart from "@/components/charts/status-chart";
import ContactsTable from "@/components/contacts-table";
import KPICards from "@/components/kpi-cards";
import LoadingAnimation, { LoadingSkeleton } from "@/components/loading-animation";
import TopNavigation from "@/components/top-navigation";
import { useCallVolumeAnalytics, useDashboardMetrics, useEngagementAnalytics, usePipelineAnalytics } from "@/hooks/use-api";
import { useToast } from "@/hooks/use-toast";
import { useEffect, useState } from "react";

export default function Dashboard() {
  const { toast } = useToast();
  
  // API hooks
  const { 
    data: metrics, 
    loading: metricsLoading, 
    error: metricsError, 
    execute: loadMetrics 
  } = useDashboardMetrics();
  
  const { 
    data: callVolumeData, 
    loading: callVolumeLoading, 
    error: callVolumeError, 
    execute: loadCallVolume 
  } = useCallVolumeAnalytics();
  
  const { 
    data: engagementData, 
    loading: engagementLoading, 
    error: engagementError, 
    execute: loadEngagement 
  } = useEngagementAnalytics();
  
  const { 
    data: pipelineData, 
    loading: pipelineLoading, 
    error: pipelineError, 
    execute: loadPipeline 
  } = usePipelineAnalytics();

  const [isInitialLoading, setIsInitialLoading] = useState(true);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setIsInitialLoading(true);
        // Load all dashboard data in parallel
        await Promise.all([
          loadMetrics(),
          loadCallVolume(),
          loadEngagement(),
          loadPipeline()
        ]);
      } catch (error) {
        console.error("Failed to load dashboard data:", error);
        toast({
          title: "Error",
          description: "Failed to load dashboard data. Please try again.",
          variant: "destructive",
        });
      } finally {
        setIsInitialLoading(false);
      }
    };
    loadDashboardData();
    // Only run once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Handle API errors
  useEffect(() => {
    if (metricsError) {
      toast({
        title: "Error",
        description: `Failed to load metrics: ${metricsError.message}`,
        variant: "destructive",
      });
    }
  }, [metricsError, toast]);

  useEffect(() => {
    if (callVolumeError) {
      toast({
        title: "Error",
        description: `Failed to load call volume data: ${callVolumeError.message}`,
        variant: "destructive",
      });
    }
  }, [callVolumeError, toast]);

  useEffect(() => {
    if (engagementError) {
      toast({
        title: "Error",
        description: `Failed to load engagement data: ${engagementError.message}`,
        variant: "destructive",
      });
    }
  }, [engagementError, toast]);

  useEffect(() => {
    if (pipelineError) {
      toast({
        title: "Error",
        description: `Failed to load pipeline data: ${pipelineError.message}`,
        variant: "destructive",
      });
    }
  }, [pipelineError, toast]);

  const isLoading = isInitialLoading || metricsLoading || callVolumeLoading || engagementLoading || pipelineLoading;

  if (isLoading) {
    return (
      <div className="min-h-screen w-full bg-slate-950 text-slate-50 overflow-x-hidden">
        <TopNavigation />
        <main className="p-8 max-w-full">
          <LoadingAnimation size="lg" message="Loading your dashboard data..." />
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
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-slate-950 text-slate-50 overflow-x-hidden">
      <TopNavigation />
      <main className="p-8 max-w-full">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Dashboard Overview</h1>
          <p className="text-slate-400">Track your business performance with real-time data</p>
        </div>

        <KPICards metrics={metrics || undefined} />
        
        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8 items-stretch">
          <div className="lg:col-span-2 flex flex-col">
            <CallVolumeChart data={callVolumeData || undefined} />
          </div>
          <div className="lg:col-span-1 flex flex-col">
            <EngagementChart data={engagementData || undefined} />
          </div>
        </div>

        {/* Pipeline Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          <div className="lg:col-span-2">
            <PipelineChart data={pipelineData || undefined} />
          </div>
          <StatusChart />
        </div>

        {/* Data Table */}
        <ContactsTable />
      </main>
    </div>
  );
}
