import { ChartBar, Phone, Users, Settings, Bell, Sliders, HelpCircle, LogOut, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link, useLocation } from "wouter";

const navigationSections = [
  {
    title: "Analytics",
    items: [
      { name: "Overview", icon: ChartBar, href: "/overview" },
      { name: "Dashboard", icon: ChartBar, href: "/dashboard" },
      { name: "Analytics", icon: BarChart3, href: "/analytics" },
      { name: "Contacts", icon: Users, href: "/contacts" },
      { name: "Calls", icon: Phone, href: "/calls" },
    ],
  },
  {
    title: "Management", 
    items: [
      { name: "Automations", icon: Sliders, href: "/automations" },
      { name: "AI Assistant", icon: Settings, href: "/ai-assistant" },
      { name: "Automation Rules", icon: Sliders, href: "/automation-rules" },
      { name: "Response Templates", icon: Bell, href: "/response-templates" },
      { name: "AI Training", icon: HelpCircle, href: "/ai-training" },
    ],
  },
  {
    title: "Settings",
    items: [
      { name: "Settings", icon: Settings, href: "/settings" },
    ],
  },
];

export default function Sidebar() {
  const [location] = useLocation();
  // Assume selectedLocation is available from context or state
  const selectedLocation = typeof window !== 'undefined' && window.localStorage ? window.localStorage.getItem('automations_selected_location') || 'all' : 'all';

  return (
    <aside className="w-80 bg-slate-900 border-r border-slate-800 flex flex-col">
      {/* Logo Section */}
      <div className="p-6 border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <BarChart3 className="w-4 h-4 text-white" />
          </div>
          <h1 className="text-xl font-semibold text-white">StreamDash</h1>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 p-6 space-y-6">
        {navigationSections.map((section) => (
          <div key={section.title}>
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">
              {section.title}
            </h3>
            <ul className="space-y-1">
              {section.items.map((item) => {
                const Icon = item.icon;
                const isActive = location === item.href;
                // If Automations, add location_id as query param
                const href = item.name === "Automations"
                  ? `/automations?location_id=${encodeURIComponent(selectedLocation)}`
                  : item.href;
                return (
                  <li key={item.name}>
                    <Link href={href}>
                      <Button
                        variant={isActive ? "secondary" : "ghost"}
                        className={`w-full justify-start px-3 py-2 text-sm font-medium transition-colors ${
                          isActive
                            ? "text-white bg-blue-600/10 border border-blue-600/20 hover:bg-blue-600/20"
                            : "text-slate-300 hover:text-white hover:bg-slate-800"
                        }`}
                      >
                        <Icon className={`w-5 h-5 mr-3 ${isActive ? "text-blue-400" : "text-slate-400"}`} />
                        {item.name}
                      </Button>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* User Profile */}
      <div className="p-6 border-t border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">
            <span className="text-sm font-medium text-white">JD</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">John Doe</p>
            <p className="text-xs text-slate-400 truncate">john@company.com</p>
          </div>
          <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
            <LogOut className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </aside>
  );
}
