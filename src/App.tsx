import { BrowserRouter, Routes, Route, Outlet } from 'react-router-dom';
import { Sidebar } from '@/components/layout/Sidebar';
import { DashboardPage } from '@/pages/DashboardPage';
import { MangroveMonitoringPage } from '@/pages/MangroveMonitoringPage';
import { AdvancedMapPage } from '@/pages/AdvancedMapPage';
import { FisheryAnalyticsPage } from '@/pages/FisheryAnalyticsPage';
import { RestorationPlanningPage } from '@/pages/RestorationPlanningPage';
import { AlertManagementPage } from '@/pages/AlertManagementPage';
import { ESGReportPage } from '@/pages/ESGReportPage';

const Layout = () => {
  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex-1 md:ml-64 flex flex-col">
        <Outlet />
      </div>
    </div>
  );
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="mangrove" element={<MangroveMonitoringPage />} />
          <Route path="advanced-map" element={<AdvancedMapPage />} />
          <Route path="fishery" element={<FisheryAnalyticsPage />} />
          <Route path="restoration" element={<RestorationPlanningPage />} />
          <Route path="alerts" element={<AlertManagementPage />} />
          <Route path="esg" element={<ESGReportPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
