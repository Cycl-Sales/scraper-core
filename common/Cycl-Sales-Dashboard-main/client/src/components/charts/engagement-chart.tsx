import { useState, useEffect } from "react";
import { MoreHorizontal } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface EngagementChartProps {
  data?: any[];
  rawData?: any[]; // Raw call data for different views
  loading?: boolean; // Loading state
}

type ChartView = "location" | "user" | "direction";

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

function CustomTooltip({ active, payload }: any) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-md px-4 py-2 text-blue-400 text-lg font-semibold shadow">
        {payload[0].name}: {payload[0].value}%
      </div>
    );
  }
  return null;
}

export default function EngagementChart({ data, rawData, loading = false }: EngagementChartProps) {
  const [engagementData, setEngagementData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [chartView, setChartView] = useState<ChartView>("location");

  // Process raw data based on selected view
  const processDataForView = (rawCallData: any[], view: ChartView) => {
    if (!rawCallData || rawCallData.length === 0) return [];

    const groupedData: { [key: string]: number } = {};

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

      groupedData[key] = (groupedData[key] || 0) + 1;
    });

    const total = Object.values(groupedData).reduce((sum, count) => sum + count, 0);

    // Sort by count (descending) and limit to top 8 for better readability
    const sortedEntries = Object.entries(groupedData)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 8);

    return sortedEntries.map(([key, count]) => ({
      name: key,
      percentage: total > 0 ? Math.round((count / total) * 100) : 0,
      count: count
    }));
  };

  useEffect(() => {
    console.log('EngagementChart - Loading:', loading, 'RawData:', rawData, 'Data:', data);
    
    if (loading) {
      setIsLoading(true);
      return;
    }
    
    if (rawData) {
      console.log('Processing raw data for engagement chart view:', chartView);
      const processedData = processDataForView(rawData, chartView);
      console.log('Processed engagement data:', processedData);
      setEngagementData(processedData);
      setIsLoading(false);
    } else if (data) {
      setEngagementData(data);
      setIsLoading(false);
    } else {
      setEngagementData([]);
      setIsLoading(false);
    }
  }, [data, rawData, chartView, loading]);

  if (isLoading) {
    return (
      <Card className="bg-slate-800 border-slate-700 h-full flex flex-col">
        <CardHeader>
          <Skeleton className="h-6 w-48 bg-slate-700" />
        </CardHeader>
        <CardContent className="flex-1">
          <Skeleton className="h-64 w-full bg-slate-700" />
        </CardContent>
      </Card>
    );
  }

  // Add error handling for invalid data
  if (!engagementData || engagementData.length === 0) {
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
                <SelectItem value="location" className="text-white hover:bg-slate-700">Engagement by Source</SelectItem>
                <SelectItem value="user" className="text-white hover:bg-slate-700">Engagement by User</SelectItem>
                <SelectItem value="direction" className="text-white hover:bg-slate-700">Engagement by Direction</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
            <MoreHorizontal className="w-4 h-4" />
          </Button>
        </CardHeader>
        <CardContent className="flex-1 flex items-center justify-center">
          <div className="text-slate-400 text-center">
            <div className="text-2xl mb-2">📊</div>
            <div>No engagement data available</div>
          </div>
        </CardContent>
      </Card>
    );
  }


  const getChartTitle = () => {
    switch (chartView) {
      case 'location': return 'Engagement by Source';
      case 'user': return 'Engagement by User';
      case 'direction': return 'Engagement by Direction';
      default: return 'Engagement by Source';
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
              <SelectItem value="location" className="text-white hover:bg-slate-700">Engagement by Source</SelectItem>
              <SelectItem value="user" className="text-white hover:bg-slate-700">Engagement by User</SelectItem>
              <SelectItem value="direction" className="text-white hover:bg-slate-700">Engagement by Direction</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
          <MoreHorizontal className="w-4 h-4" />
        </Button>
      </CardHeader>
      <CardContent className="flex-1">
        <ResponsiveContainer width="100%" height={400}>
          <PieChart>
            <Pie
              data={engagementData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ percent }) => percent > 0.05 ? `${Math.round(percent * 100)}%` : ''}
              outerRadius={80}
              fill="#8884d8"
              dataKey="percentage"
              minAngle={5}
            >
              {engagementData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              verticalAlign="bottom" 
              height={36}
              wrapperStyle={{
                fontSize: '12px',
                lineHeight: '14px',
                paddingTop: '10px'
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
