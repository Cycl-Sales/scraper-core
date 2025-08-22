import React from 'react';
import { Building2 } from 'lucide-react';
import { useSubAccount } from '@/contexts/SubAccountContext';

export default function SubAccountHeader() {
  const { locationId } = useSubAccount();
  const accountName = localStorage.getItem('sub_account_name') || 'Sub Account';

  return (
    <div className="bg-slate-800 border-b border-slate-700 px-4 py-3 flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
          <Building2 className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="text-white font-semibold text-base">{accountName}</div>
          <div className="text-slate-400 text-sm">Location ID: {locationId}</div>
        </div>
      </div>
      
      <div className="flex items-center space-x-3">
        <div className="px-3 py-1 bg-blue-600/20 border border-blue-500/30 rounded-full">
          <span className="text-blue-300 text-xs font-medium">SUB-ACCOUNT</span>
        </div>
      </div>
    </div>
  );
}
