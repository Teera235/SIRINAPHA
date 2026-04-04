import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  TreePine, 
  Fish, 
  Sprout, 
  AlertTriangle, 
  FileBarChart,
  ChevronLeft,
  ChevronRight,
  Map
} from 'lucide-react';

const menuItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/mangrove', label: 'Mangrove Monitoring', icon: TreePine },
  { path: '/advanced-map', label: 'Advanced Map', icon: Map },
  { path: '/fishery', label: 'Fishery Analytics', icon: Fish },
  { path: '/restoration', label: 'Restoration Planning', icon: Sprout },
  { path: '/alerts', label: 'Alert Management', icon: AlertTriangle },
  { path: '/esg', label: 'ESG Report', icon: FileBarChart },
];

export const Sidebar: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  // Close mobile menu when route changes
  React.useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="md:hidden fixed top-4 left-4 z-[1001] bg-primary text-white p-2 rounded-lg shadow-lg"
      >
        {mobileOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
      </button>

      {/* Mobile Overlay */}
      {mobileOpen && (
        <div 
          className="md:hidden fixed inset-0 bg-black bg-opacity-50 z-[999]"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed left-0 top-0 h-screen bg-surface border-r border-neutral-200 transition-all duration-300 flex flex-col z-[1000] ${
          // Mobile: slide in/out, Desktop: normal collapse behavior
          mobileOpen 
            ? 'translate-x-0 w-64 md:w-64' 
            : '-translate-x-full md:translate-x-0'
        } ${
          collapsed ? 'md:w-16' : 'md:w-64'
        }`}
      >
        <div className="flex items-center justify-between p-4 border-b border-neutral-200">
          {(!collapsed || mobileOpen) && (
            <div>
              <div className="text-xl font-bold text-primary">SIRINAPHA</div>
              <div className="text-xs text-text-secondary">Baan-Pla Link</div>
            </div>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="hidden md:block p-1 hover:bg-neutral-100 rounded"
          >
            {collapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
          </button>
        </div>

        <nav className="flex-1 p-2 overflow-y-auto">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2.5 mb-1 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-primary text-white'
                    : 'text-text-secondary hover:bg-neutral-100 hover:text-text-primary'
                }`}
                title={collapsed && !mobileOpen ? item.label : undefined}
                onClick={() => setMobileOpen(false)}
              >
                <Icon size={20} />
                {(!collapsed || mobileOpen) && <span className="text-sm font-medium">{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {(!collapsed || mobileOpen) && (
          <div className="p-4 border-t border-neutral-200 text-xs text-text-secondary">
            <div>Satellite & AI Platform</div>
            <div className="mt-1">Coastal Ecosystem Monitoring</div>
          </div>
        )}
      </div>
    </>
  );
};
