import { Calendar, Filter, Bell } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function DashboardHeader() {
  return (
    <header className="bg-slate-900 border-b border-slate-800 px-8 py-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">Dashboard Overview</h1>
          <p className="text-slate-400 mt-1">Track your business performance and key metrics</p>
        </div>
        <div className="flex items-center space-x-4">
          {/* Date Range Picker */}
          <div className="flex items-center space-x-2 px-4 py-2 bg-slate-800 rounded-lg border border-slate-700">
            <Calendar className="w-4 h-4 text-slate-400" />
            <span className="text-sm text-slate-300">May 12, 2025 - May 18, 2025</span>
          </div>
          
          {/* Filter Button */}
          <Button className="bg-blue-600 text-white hover:bg-blue-700">
            <Filter className="w-4 h-4 mr-2" />
            Filters
          </Button>
          
          {/* Notifications */}
          <div className="relative">
            <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
              <Bell className="w-5 h-5" />
            </Button>
            <Badge className="absolute -top-1 -right-1 w-5 h-5 p-0 bg-red-500 text-white text-xs flex items-center justify-center">
              3
            </Badge>
          </div>
        </div>
      </div>
    </header>
  );
}
