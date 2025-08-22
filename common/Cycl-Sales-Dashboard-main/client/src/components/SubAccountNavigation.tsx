import React from 'react';
import { Link, useLocation } from 'wouter';
import { BarChart3, Settings, Zap } from 'lucide-react';
import { useSubAccount } from '@/contexts/SubAccountContext';

export default function SubAccountNavigation() {
  const [location] = useLocation();
  const { locationId } = useSubAccount();
  const [activeNav, setActiveNav] = React.useState('Analytics');

  // Set active nav based on route
  React.useEffect(() => {
    if (location.includes('/analytics')) setActiveNav('Analytics');
    else if (location.includes('/automations')) setActiveNav('Automations');
    else if (location.includes('/call-details')) setActiveNav('Call Details');
  }, [location]);

  const navButtons = [
    { 
      label: 'Analytics', 
      href: `/analytics?location_id=${encodeURIComponent(locationId || '')}`,
      icon: BarChart3
    },
    { 
      label: 'Automations', 
      href: `/automations?location_id=${encodeURIComponent(locationId || '')}`,
      icon: Zap
    },
  ];

  return (
    <nav className="w-full bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between">
      {/* Left: Logo and Title */}
      <div className="flex items-center space-x-3 min-w-[200px]">
        <Link href={`/analytics?location_id=${encodeURIComponent(locationId || '')}`}>
          <div className="flex items-center space-x-3 cursor-pointer hover:opacity-80 transition-opacity">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-4 h-4 text-white" />
            </div>
            <div>
              <span className="text-white font-semibold text-xl">Cycl Sales</span>
              <div className="text-xs text-slate-400">Sub-Account View</div>
            </div>
          </div>
        </Link>
      </div>
      
      {/* Right: Nav Buttons */}
      <div className="flex items-center space-x-2 min-w-[80px] justify-end">
        <div className="flex items-center bg-slate-800 rounded-lg px-1 py-1 gap-1">
          {navButtons.map((btn) => {
            const IconComponent = btn.icon;
            return (
              <Link key={btn.label} href={btn.href}>
                <button
                  onClick={() => setActiveNav(btn.label)}
                  className={`px-5 py-1 rounded-lg text-sm transition-colors focus:outline-none flex items-center space-x-2 ${
                    activeNav === btn.label
                      ? "text-white bg-slate-900 font-semibold"
                      : "text-slate-300 hover:text-white bg-transparent"
                  }`}
                >
                  <IconComponent className="w-4 h-4" />
                  <span>{btn.label}</span>
                </button>
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
