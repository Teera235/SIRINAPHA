import React, { useState } from 'react';
import { Bell, ChevronDown } from 'lucide-react';
import { mockAlerts } from '@/data/mockAlerts';

interface TopBarProps {
  title: string;
}

export const TopBar: React.FC<TopBarProps> = ({ title }) => {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const unacknowledgedCount = mockAlerts.filter(a => !a.isAcknowledged).length;

  return (
    <div className="h-16 bg-surface border-b border-neutral-200 flex items-center justify-between px-6">
      <div>
        <h1 className="text-2xl font-semibold text-text-primary">{title}</h1>
        <div className="text-xs text-text-secondary mt-0.5">
          Last updated: April 4, 2024 08:30 ICT
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button className="relative p-2 hover:bg-neutral-100 rounded-lg transition-colors">
          <Bell size={20} className="text-text-secondary" />
          {unacknowledgedCount > 0 && (
            <span className="absolute top-1 right-1 w-5 h-5 bg-danger text-white text-xs rounded-full flex items-center justify-center">
              {unacknowledgedCount}
            </span>
          )}
        </button>

        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 p-2 hover:bg-neutral-100 rounded-lg transition-colors"
          >
            <div className="w-8 h-8 bg-primary text-white rounded-full flex items-center justify-center text-sm font-medium">
              SK
            </div>
            <ChevronDown size={16} className="text-text-secondary" />
          </button>

          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-48 bg-surface border border-neutral-200 rounded-lg shadow-lg py-1 z-50">
              <button className="w-full text-left px-4 py-2 text-sm text-text-primary hover:bg-neutral-100">
                Profile
              </button>
              <button className="w-full text-left px-4 py-2 text-sm text-text-primary hover:bg-neutral-100">
                Settings
              </button>
              <hr className="my-1 border-neutral-200" />
              <button className="w-full text-left px-4 py-2 text-sm text-danger hover:bg-neutral-100">
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
