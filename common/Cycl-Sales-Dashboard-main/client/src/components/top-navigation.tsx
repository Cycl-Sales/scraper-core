import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import { BarChart3, Grid, Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation } from "wouter";
import { useTheme } from "../theme-context";

export default function TopNavigation() {
  const [activeNav, setActiveNav] = useState("Analytics");
  const { theme, setTheme } = useTheme();
  const [location] = useLocation();

  // Set active nav based on route
  useEffect(() => {
    if (location === "/overview") setActiveNav("Overview");
    else if (["/automations", "/ai-assistant", "/automation-rules", "/response-templates", "/ai-training"].includes(location)) setActiveNav("Automations");
    // You can add more route checks for other navs if needed
  }, [location]);

  // Use selectedLocation from localStorage if available
  const selectedLocation = typeof window !== 'undefined' && window.localStorage ? window.localStorage.getItem('automations_selected_location') || 'all' : 'all';
  const navButtons = [
    { label: "Actions" },
    { label: "Overview" },
    { label: "Analytics" },
    { label: "Automations", href: `/automations?location_id=${encodeURIComponent(selectedLocation)}` },
  ];

  // Minimal top navbar (from screenshot)
  // Only logo/title on left, nav buttons and icons on right
  return (
    <>
      {/* Minimal Top Navbar - Switchable Buttons & Bordered Icons */}
      <nav className="w-full bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between">
        {/* Left: Logo and Title */}
        <div className="flex items-center space-x-3 min-w-[200px]">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <BarChart3 className="w-4 h-4 text-white" />
          </div>
          <span className="text-white font-semibold text-xl">Cycl Sales</span>
        </div>
        {/* Right: Nav Buttons and Icon Buttons */}
        <div className="flex items-center space-x-2 min-w-[80px] justify-end">
          <div className="flex items-center bg-slate-800 rounded-lg px-1 py-1 gap-1">
            {navButtons.map((btn) => (
              btn.label === "Overview" ? (
                <Link key={btn.label} href="/overview">
                  <button
                    onClick={() => setActiveNav(btn.label)}
                    className={`px-5 py-1 rounded-lg text-sm transition-colors focus:outline-none ${
                      activeNav === btn.label
                        ? "text-white bg-slate-900 font-semibold"
                        : "text-slate-300 hover:text-white bg-transparent"
                    }`}
                  >
                    {btn.label}
                  </button>
                </Link>
              ) : btn.href ? (
                <Link key={btn.label} href={btn.href}>
                  <button
                    onClick={() => setActiveNav(btn.label)}
                    className={`px-5 py-1 rounded-lg text-sm transition-colors focus:outline-none ${
                      activeNav === btn.label
                        ? "text-white bg-slate-900 font-semibold"
                        : "text-slate-300 hover:text-white bg-transparent"
                    }`}
                  >
                    {btn.label}
                  </button>
                </Link>
              ) : (
                <button
                  key={btn.label}
                  onClick={() => setActiveNav(btn.label)}
                  className={`px-5 py-1 rounded-lg text-sm transition-colors focus:outline-none ${
                    activeNav === btn.label
                      ? "text-white bg-slate-900 font-semibold"
                      : "text-slate-300 hover:text-white bg-transparent"
                  }`}
                >
                  {btn.label}
                </button>
              )
            ))}
          </div>
          {/* <Button
            variant="ghost"
            size="icon"
            className="text-slate-300 hover:text-white hover:bg-slate-800 border border-slate-700 rounded-lg"
          >
            <Settings className="h-5 w-5" />
          </Button> */}
          {/* Grid/Menu Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="text-slate-300 hover:text-white hover:bg-slate-800 border border-slate-700 rounded-lg"
              >
                <Grid className="h-5 w-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-44 bg-slate-900 border-slate-700">
              <DropdownMenuItem
                className="text-slate-300 hover:text-white hover:bg-slate-800 cursor-pointer"
                onClick={() => setTheme("system")}
              >
                <Grid className="h-4 w-4 mr-2" />
                System
                {theme === "system" && <span className="ml-auto">✓</span>}
              </DropdownMenuItem>
              <DropdownMenuItem
                className="text-slate-300 hover:text-white hover:bg-slate-800 cursor-pointer"
                onClick={() => setTheme("light")}
              >
                <Sun className="h-4 w-4 mr-2" />
                Light
                {theme === "light" && <span className="ml-auto">✓</span>}
              </DropdownMenuItem>
              <DropdownMenuItem
                className="text-slate-300 hover:text-white hover:bg-slate-800 cursor-pointer"
                onClick={() => setTheme("dark")}
              >
                <Moon className="h-4 w-4 mr-2" />
                Dark
                {theme === "dark" && <span className="ml-auto">✓</span>}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </nav> 
    </>
  );
}