import { useState, useEffect } from "react";
import { MoreHorizontal } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip, LabelList } from "recharts";
import { Skeleton } from "@/components/ui/skeleton";

interface PipelineChartProps {
  data?: any[];
}

function CustomTooltip({ active, payload }: any) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-md px-4 py-2 text-blue-400 text-lg font-semibold shadow">
        Value: ${payload[0].value}
      </div>
    );
  }
  return null;
}

export default function PipelineChart({ data }: PipelineChartProps) {
  const [pipelineData, setPipelineData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (data) {
      setPipelineData(data);
      setIsLoading(false);
    } else {
      // Fallback to empty data if no data provided
      setPipelineData([]);
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
        <CardTitle className="text-lg font-semibold text-white">Pipeline Overview</CardTitle>
        <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
          <MoreHorizontal className="w-4 h-4" />
        </Button>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={256}>
          <LineChart data={pipelineData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis 
              dataKey="month"
              stroke="#94a3b8"
              fontSize={12}
            />
            <YAxis 
              stroke="#94a3b8"
              fontSize={12}
              tickFormatter={(value) => `$${value}`}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(59, 130, 246, 0.1)' }} />
            <Line 
              type="monotone"
              dataKey="value"
              stroke="#3b82f6"
              strokeWidth={3}
              dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: '#3b82f6', strokeWidth: 2 }}
            >
              <LabelList dataKey="value" position="top" fill="#3b82f6" fontSize={12} fontWeight={600} />
            </Line>
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
