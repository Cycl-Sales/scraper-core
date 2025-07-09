import { useState, useEffect } from "react";
import { Link, useLocation } from "wouter";
import { ChevronDown, Settings, Users, BarChart3, Phone, LogOut, UserCircle, MapPin, Grid, Sun, Moon } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useTheme } from "../theme-context";

export default function TopNavigation() {
  const [selectedLocation, setSelectedLocation] = useState("all");
  const [activeNav, setActiveNav] = useState("Analytics");
  const { theme, setTheme } = useTheme();
  const [location] = useLocation();

  // Set active nav based on route
  useEffect(() => {
    if (location === "/overview") setActiveNav("Overview");
    // You can add more route checks for other navs if needed
  }, [location]);

  const navButtons = [
    { label: "Actions" },
    { label: "Overview" },
    { label: "Analytics" },
    { label: "Automations" },
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
          <Button
            variant="ghost"
            size="icon"
            className="text-slate-300 hover:text-white hover:bg-slate-800 border border-slate-700 rounded-lg"
          >
            <Settings className="h-5 w-5" />
          </Button>
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
      {/* Existing Navigation */}
      <nav className="w-full bg-slate-900 border-b border-slate-800 px-6 py-4">
        <div className="w-full flex items-center justify-between">
          {/* Left Section - Logo, Title, and Main Navigation */}
          <div className="flex items-center space-x-8">
            {/* Logo and Title */}
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-4 h-4 text-white" />
              </div>
              <span className="text-white font-semibold text-xl">Cycl Sales</span>
            </div>

            {/* Main Navigation Menu */}
            <div className="flex items-center space-x-6">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="text-white hover:text-blue-400 hover:bg-slate-800">
                    <BarChart3 className="w-4 h-4 mr-2" />
                    Dashboard
                    <ChevronDown className="w-4 h-4 ml-2" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="bg-slate-800 border-slate-700">
                  <Link href="/contacts">
                    <DropdownMenuItem className="text-slate-300 hover:text-white hover:bg-slate-700 cursor-pointer">
                      <Users className="w-4 h-4 mr-2" />
                      Contacts
                    </DropdownMenuItem>
                  </Link>
                  <Link href="/calls">
                    <DropdownMenuItem className="text-slate-300 hover:text-white hover:bg-slate-700 cursor-pointer">
                      <Phone className="w-4 h-4 mr-2" />
                      Calls
                    </DropdownMenuItem>
                  </Link>
                </DropdownMenuContent>
              </DropdownMenu>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="text-slate-300 hover:text-white hover:bg-slate-800">
                    <Settings className="w-4 h-4 mr-2" />
                    AI Settings
                    <ChevronDown className="w-4 h-4 ml-2" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="bg-slate-800 border-slate-700">
                  <Link href="/ai-assistant">
                    <DropdownMenuItem className="text-slate-300 hover:text-white hover:bg-slate-700 cursor-pointer">
                      AI Assistant Configuration
                    </DropdownMenuItem>
                  </Link>
                  <Link href="/automation-rules">
                    <DropdownMenuItem className="text-slate-300 hover:text-white hover:bg-slate-700 cursor-pointer">
                      Automation Rules
                    </DropdownMenuItem>
                  </Link>
                  <Link href="/response-templates">
                    <DropdownMenuItem className="text-slate-300 hover:text-white hover:bg-slate-700 cursor-pointer">
                      Response Templates
                    </DropdownMenuItem>
                  </Link>
                  <Link href="/ai-training">
                    <DropdownMenuItem className="text-slate-300 hover:text-white hover:bg-slate-700 cursor-pointer">
                      AI Training Data
                    </DropdownMenuItem>
                  </Link>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>

          {/* Right Section - Location Filter, Settings, Grid/Menu, Profile */}
          <div className="flex items-center space-x-4">
            {/* Location Filter */}
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-slate-400" />
              <Select value={selectedLocation} onValueChange={setSelectedLocation}>
                <SelectTrigger className="w-[140px] bg-slate-800 border-slate-700 text-slate-300">
                  <SelectValue placeholder="Location" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-700">
                  <SelectItem value="all" className="text-slate-300 hover:text-white hover:bg-slate-700">All Locations</SelectItem>
                  <SelectItem value="location_1" className="text-slate-300 hover:text-white hover:bg-slate-700">Main Office</SelectItem>
                  <SelectItem value="location_2" className="text-slate-300 hover:text-white hover:bg-slate-700">Branch Office</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Settings */}
            <Button variant="ghost" size="icon" className="text-slate-300 hover:text-white hover:bg-slate-800">
              <Settings className="h-5 w-5" />
            </Button>

            {/* Profile Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center space-x-2 text-slate-300 hover:text-white hover:bg-slate-800">
                  <Avatar className="h-8 w-8">
                    <AvatarImage src="/placeholder-avatar.png" alt="User" />
                    <AvatarFallback className="bg-slate-700 text-slate-300">
                      <UserCircle className="h-5 w-5" />
                    </AvatarFallback>
                  </Avatar>
                  <span className="hidden sm:block">John Doe</span>
                  <ChevronDown className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56 bg-slate-800 border-slate-700">
                <DropdownMenuLabel className="text-slate-300">My Account</DropdownMenuLabel>
                <DropdownMenuSeparator className="bg-slate-700" />
                <DropdownMenuItem className="text-slate-300 hover:text-white hover:bg-slate-700">
                  <UserCircle className="mr-2 h-4 w-4" />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem className="text-slate-300 hover:text-white hover:bg-slate-700">
                  <Settings className="mr-2 h-4 w-4" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-slate-700" />
                <DropdownMenuItem className="text-slate-300 hover:text-white hover:bg-slate-700">
                  <LogOut className="mr-2 h-4 w-4" />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </nav>
    </>
  );
}