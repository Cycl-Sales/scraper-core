import { useState, useEffect } from "react";
import { MoreHorizontal } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { Skeleton } from "@/components/ui/skeleton";

interface EngagementChartProps {
  data?: any[];
}

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

export default function EngagementChart({ data }: EngagementChartProps) {
  const [engagementData, setEngagementData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (data) {
      setEngagementData(data);
      setIsLoading(false);
    } else {
      // Fallback to empty data if no data provided
      setEngagementData([]);
      setIsLoading(false);
    }
  }, [data]);

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

  return (
    <Card className="bg-slate-800 border-slate-700">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg font-semibold text-white">Engagement by Source</CardTitle>
        <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
          <MoreHorizontal className="w-4 h-4" />
        </Button>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={256}>
          <PieChart>
            <Pie
              data={engagementData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="percentage"
            >
              {Array.from({ length: engagementData.length }).map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
