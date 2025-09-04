import { useState, useEffect } from "react";
import { MoreHorizontal, ChevronDown } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip, LabelList } from "recharts";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface CallVolumeChartProps {
  data?: any[];
  rawData?: any[]; // Raw call data for different views
  loading?: boolean; // Loading state
}

type ChartView = "location" | "user" | "direction";

function CustomTooltip({ active, payload, label }: any) {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-slate-800 border border-slate-600 rounded-lg p-3 shadow-lg min-w-[200px]">
        <p className="text-white font-medium mb-2">{label}</p>
        <div className="space-y-1 text-sm">
          <p className="text-blue-400">
            <span className="text-slate-300">Calls:</span> {payload[0].value}
          </p>
          <p className="text-green-400">
            <span className="text-slate-300">Total Duration:</span> {data.totalDuration?.toFixed(1)}s
          </p>
          <p className="text-yellow-400">
            <span className="text-slate-300">Avg Duration:</span> {data.avgDuration?.toFixed(1)}s
          </p>
        </div>
      </div>
    );
  }
  return null;
}

export default function CallVolumeChart({ data, rawData, loading = false }: CallVolumeChartProps) {
  const [callData, setCallData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [chartView, setChartView] = useState<ChartView>("location");

  // Process raw data based on selected view
  const processDataForView = (rawCallData: any[], view: ChartView) => {
    if (!rawCallData || rawCallData.length === 0) return [];

    const groupedData: { [key: string]: { count: number; totalDuration: number } } = {};

    rawCallData.forEach(call => {
      let key = '';
      switch (view) {
        case 'location':
          const source = call.contact_id?.source;
          if (source && source !== false && source !== 'false' && source.trim() !== '') {
            // Normalize source names to prevent duplicates
            key = source.toString().trim();
            // Group similar sources together
            if (key.toLowerCase().includes('unknown') || key.toLowerCase().includes('false')) {
              key = 'Unknown Source';
            }
          } else {
            key = 'Unknown Source';
          }
          break;
        case 'user':
          key = call.user_id && call.user_id !== 'None' ? call.user_id : 'Unknown User';
          break;
        case 'direction':
          key = call.direction || 'Unknown Direction';
          break;
      }

      // Ensure key is a string and not empty
      key = key.toString().trim() || 'Unknown';

      if (!groupedData[key]) {
        groupedData[key] = { count: 0, totalDuration: 0 };
      }
      groupedData[key].count += 1;
      groupedData[key].totalDuration += call.meta?.call_duration || 0;
    });

    // Sort by volume (descending) and limit to top 10 for better readability
    const sortedEntries = Object.entries(groupedData)
      .sort(([,a], [,b]) => b.count - a.count)
      .slice(0, 10);

    return sortedEntries.map(([key, value]) => ({
      location: key,
      volume: value.count,
      totalDuration: value.totalDuration,
      avgDuration: value.totalDuration / value.count
    }));
  };

  useEffect(() => {
    console.log('CallVolumeChart - Loading:', loading, 'RawData:', rawData, 'Data:', data);
    
    if (loading) {
      setIsLoading(true);
      return;
    }
    
    if (rawData) {
      console.log('Processing raw data for chart view:', chartView);
      const processedData = processDataForView(rawData, chartView);
      console.log('Processed data:', processedData);
      setCallData(processedData);
      setIsLoading(false);
    } else if (data) {
      setCallData(data);
      setIsLoading(false);
    } else {
      setCallData([]);
      setIsLoading(false);
    }
  }, [data, rawData, chartView, loading]);

  if (isLoading) {
    return (
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <Skeleton className="h-6 w-48 bg-slate-700" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-64 w-full bg-slate-700" />
        </CardContent>
      </Card>
    );
  }

  // Show empty state if no data
  if (!callData || callData.length === 0) {
    return (
      <Card className="bg-slate-800 border-slate-700 h-100" >
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-lg font-semibold text-white">Call Volume by Location</CardTitle>
          <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
            <MoreHorizontal className="w-4 h-4" />
          </Button>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64 text-slate-400">
            <div className="text-center">
              <div className="text-lg font-medium mb-2">No Data Available</div>
              <div className="text-sm">Call volume data will appear here once contacts are synced</div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const getChartTitle = () => {
    switch (chartView) {
      case 'location': return 'Call Volume by Location';
      case 'user': return 'Call Volume by User';
      case 'direction': return 'Call Volume by Direction';
      default: return 'Call Volume by Location';
    }
  };

  return (
    <Card className="bg-slate-800 border-slate-700 h-full flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="flex items-center gap-3">
          <CardTitle className="text-lg font-semibold text-white">{getChartTitle()}</CardTitle>
          <Select value={chartView} onValueChange={(value: ChartView) => setChartView(value)}>
            <SelectTrigger className="w-[200px] bg-slate-700 border-slate-600 text-white">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-slate-800 border-slate-700">
              <SelectItem value="location" className="text-white hover:bg-slate-700">Call Volume by Location</SelectItem>
              <SelectItem value="user" className="text-white hover:bg-slate-700">Call Volume by User</SelectItem>
              <SelectItem value="direction" className="text-white hover:bg-slate-700">Call Volume by Direction</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
          <MoreHorizontal className="w-4 h-4" />
        </Button>
      </CardHeader>
      <CardContent className="flex-1 min-h-0">
        <div className="h-full min-h-[300px] max-h-[500px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={callData} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis 
                dataKey="location"
                stroke="#94a3b8"
                fontSize={10}
                angle={-45}
                textAnchor="end"
                height={100}
                interval={0}
              />
              <YAxis 
                stroke="#94a3b8"
                fontSize={12}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(59, 130, 246, 0.1)' }} />
              <Bar 
                dataKey="volume"
                fill="#3b82f6"
                radius={[6, 6, 0, 0]}
              >
                <LabelList dataKey="volume" position="top" fill="#3b82f6" fontSize={12} fontWeight={700} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
