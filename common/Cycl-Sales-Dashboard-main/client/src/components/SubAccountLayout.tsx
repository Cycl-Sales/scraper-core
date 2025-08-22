import React from 'react';
import SubAccountHeader from './SubAccountHeader';
import SubAccountNavigation from './SubAccountNavigation';

interface SubAccountLayoutProps {
  children: React.ReactNode;
}

export default function SubAccountLayout({ children }: SubAccountLayoutProps) {
  return (
    <div className="min-h-screen bg-slate-900">
      <SubAccountHeader />
      <SubAccountNavigation />
      <main className="p-6">
        {children}
      </main>
    </div>
  );
}
