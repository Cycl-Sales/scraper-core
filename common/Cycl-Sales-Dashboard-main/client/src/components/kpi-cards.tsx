import { DollarSign, Users, Target, TrendingUp, ArrowUp, ArrowDown, BarChart3, PercentCircle, Timer, Award, Tag, UserCheck, Phone, UserPlus, User, TrendingDown } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useState } from "react";
import type { DashboardMetrics } from "@shared/schema";

interface KPICardsProps {
  metrics: DashboardMetrics | undefined;
}

export default function KPICards({ metrics }: KPICardsProps) {
  // Dropdown options from screenshot
  const kpiOptions = [
    "Lead Touch Rate (All Types)",
    "Engagement Rate (All Types)",
    "Contact Win Percentage",
    "Average Revenue Per Contact",
    "Average Time to Win",
    "Average Win Value",
    "Average Opportunity Value",
    "Engaged Contacts Without Touch",
    "Lead Touch Rate (Calls Only)",
    "Engagement Rate (Calls Only)",
    "Median Speed to Lead (All Types)",
    "Median Speed to Lead (Calls Only)",
    "Percent With Tag Filter",
    "Total New Contacts",
    "Total Valid Leads",
    "Median Lead Quality",
  ];

  // Map each KPI option to an icon
  const kpiOptionIcons: Record<string, any> = {
    "Lead Touch Rate (All Types)": BarChart3,
    "Engagement Rate (All Types)": TrendingUp,
    "Contact Win Percentage": PercentCircle,
    "Average Revenue Per Contact": DollarSign,
    "Average Time to Win": Timer,
    "Average Win Value": Award,
    "Average Opportunity Value": Award,
    "Engaged Contacts Without Touch": UserCheck,
    "Lead Touch Rate (Calls Only)": Phone,
    "Engagement Rate (Calls Only)": Phone,
    "Median Speed to Lead (All Types)": Timer,
    "Median Speed to Lead (Calls Only)": Timer,
    "Percent With Tag Filter": Tag,
    "Total New Contacts": UserPlus,
    "Total Valid Leads": User,
    "Median Lead Quality": TrendingDown,
  };

  // Each card manages its own selected value
  const [selectedOptions, setSelectedOptions] = useState([
    kpiOptions[0],
    kpiOptions[0],
    kpiOptions[0],
    kpiOptions[0],
  ]);

  const handleSelect = (cardIdx: number, value: string) => {
    setSelectedOptions((prev) => {
      const updated = [...prev];
      updated[cardIdx] = value;
      return updated;
    });
  };

  const cards = [
    {
      title: "Total Revenue",
      value: metrics ? `$${metrics.totalRevenue.toLocaleString()}` : "$0",
      change: "+12.5%",
      isPositive: true,
      icon: DollarSign,
      iconBg: "bg-green-500/10",
      iconColor: "text-green-500",
    },
    {
      title: "Total Contacts",
      value: metrics ? metrics.totalContacts.toLocaleString() : "0",
      change: "+8.2%",
      isPositive: true,
      icon: Users,
      iconBg: "bg-blue-500/10",
      iconColor: "text-blue-500",
    },
    {
      title: "Opportunities",
      value: metrics ? metrics.totalOpportunities.toLocaleString() : "0",
      change: "+15.3%",
      isPositive: true,
      icon: Target,
      iconBg: "bg-yellow-500/10",
      iconColor: "text-yellow-500",
    },
    {
      title: "Conversion Rate",
      value: metrics ? `${metrics.conversionRate.toFixed(1)}%` : "0%",
      change: "+5.7%",
      isPositive: true,
      icon: TrendingUp,
      iconBg: "bg-purple-500/10",
      iconColor: "text-purple-400",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {cards.map((card, idx) => {
        // Use the selected icon for this card
        const SelectedIcon = kpiOptionIcons[selectedOptions[idx]] || card.icon;
        return (
          <Card key={card.title} className="bg-slate-800 border-slate-700 hover:border-slate-600 transition-colors w-full">
            <CardContent className="p-6">
              {/* Dropdown label */}
              <Select
                value={selectedOptions[idx]}
                onValueChange={(val) => handleSelect(idx, val)}
              >
                <SelectTrigger className="w-full bg-slate-900 text-start border border-slate-700 text-slate-200 font-medium mb-1 text-sm py-1 px-2 min-h-0 h-9">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 text-start border-slate-700 text-slate-200 text-sm">
                  {kpiOptions.map((option) => {
                    const OptionIcon = kpiOptionIcons[option] || BarChart3;
                    return (
                      <SelectItem
                        key={option}
                        value={option}
                        className="text-slate-200 hover:bg-slate-800 cursor-pointer flex items-center gap-2 text-sm min-h-0 h-9"
                      >
                        <OptionIcon className="w-4 h-4 mr-2 inline-block" />
                        {option}
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
              {/* Icon centered above value+change */}
              <div className="flex justify-start my-3">
                <div className={`w-12 h-12 ${card.iconBg} rounded-lg flex items-center justify-center`}>
                  <SelectedIcon className={`${card.iconColor} w-6 h-6`} />
                </div>
              </div>
              {/* Value and change indicator on same line */}
              <div className="flex justify-center items-center mb-0 mt-0">
                <h3 className="text-2xl font-bold text-white mr-3">{card.value}</h3>
                <span className={`flex items-center px-2 py-0.5 rounded-md text-xs font-semibold ml-2 ${card.isPositive ? "bg-green-900 text-green-400" : "bg-red-900 text-red-400"}`}>
                  {card.isPositive ? (
                    <ArrowUp className="w-3 h-3 mr-1" />
                  ) : (
                    <ArrowDown className="w-3 h-3 mr-1" />
                  )}
                  {card.change}
                </span>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
