import React from 'react';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { KPICard } from '@/components/dashboard/KPICard';
import { AlertFeed } from '@/components/dashboard/AlertFeed';
import { MapContainer } from '@/components/map/MapContainer';
import { NDVITimeSeriesChart } from '@/components/charts/NDVITimeSeriesChart';
import { useIsMobile, MobileCard } from '@/components/common/MobileOptimized';
import { TreePine, ShieldCheck, AlertTriangle, Bell } from 'lucide-react';
import { mockMangroveZones } from '@/data/mockMangroveZones';
import { mockAlerts } from '@/data/mockAlerts';
import { mockNDVIHistory } from '@/data/mockNDVIHistory';
import { mockCatchLogs } from '@/data/mockCatchLogs';
import { formatNumber, formatArea } from '@/utils/formatters';
import { BarChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export const DashboardPage: React.FC = () => {
  const isMobile = useIsMobile();
  
  const totalArea = mockMangroveZones.reduce((sum, zone) => sum + zone.areaRai, 0);
  const healthyArea = mockMangroveZones
    .filter(z => z.healthStatus === 'healthy')
    .reduce((sum, zone) => sum + zone.areaRai, 0);
  const atRiskArea = mockMangroveZones
    .filter(z => z.healthStatus === 'stressed' || z.healthStatus === 'degraded')
    .reduce((sum, zone) => sum + zone.areaRai, 0);
  const unacknowledgedAlerts = mockAlerts.filter(a => !a.isAcknowledged);
  const criticalAlerts = unacknowledgedAlerts.filter(a => a.severity === 'critical');
  const provinces = new Set(mockMangroveZones.map(z => z.province)).size;

  const last12Months = mockNDVIHistory.slice(-12);

  const catchByMonth = mockCatchLogs.reduce((acc, log) => {
    const month = log.tripDate.substring(0, 7);
    if (!acc[month]) {
      acc[month] = { month, weight: 0, revenue: 0 };
    }
    acc[month].weight += log.totalWeightKg;
    acc[month].revenue += log.estimatedRevenueBaht;
    return acc;
  }, {} as Record<string, { month: string; weight: number; revenue: number }>);

  const catchData = Object.values(catchByMonth)
    .sort((a, b) => a.month.localeCompare(b.month))
    .slice(-6)
    .map(d => ({
      month: d.month.substring(5),
      weight: Math.round(d.weight),
      revenue: Math.round(d.revenue),
    }));

  return (
    <PageWrapper title="Dashboard">
      <div className="space-y-6">
        {/* KPI Cards - Responsive Grid */}
        <div className={`grid gap-4 ${isMobile ? 'grid-cols-2' : 'grid-cols-4'}`}>
          <KPICard
            title="Total Mangrove Area"
            value={formatArea(totalArea)}
            subtitle={`${provinces} provinces`}
            icon={TreePine}
            color="#2D7A4F"
            trend={{ value: 2.3, isPositive: true }}
          />
          <KPICard
            title="Healthy Forest"
            value={formatArea(healthyArea)}
            subtitle={`${((healthyArea / totalArea) * 100).toFixed(1)}% of total`}
            icon={ShieldCheck}
            color="#38A169"
            progressBar={{ value: (healthyArea / totalArea) * 100, color: '#38A169' }}
          />
          <KPICard
            title="Degraded / At-Risk"
            value={formatArea(atRiskArea)}
            subtitle={`${((atRiskArea / totalArea) * 100).toFixed(1)}% of total`}
            icon={AlertTriangle}
            color="#C05621"
            trend={{ value: 5.2, isPositive: false }}
          />
          <KPICard
            title="Active Alerts"
            value={formatNumber(unacknowledgedAlerts.length)}
            subtitle={criticalAlerts.length > 0 ? `${criticalAlerts.length} Critical` : 'No critical alerts'}
            icon={Bell}
            color={criticalAlerts.length > 0 ? '#C53030' : '#D69E2E'}
          />
        </div>

        {/* Main Content - Responsive Layout */}
        <div className={`grid gap-6 ${isMobile ? 'grid-cols-1' : 'grid-cols-3'}`}>
          {/* Map Section */}
          <div className={isMobile ? 'order-2' : 'col-span-2'}>
            <MobileCard className="h-[400px] md:h-[500px]">
              <h3 className="text-lg font-semibold text-text-primary mb-4">Mangrove Zones</h3>
              <div className="h-[calc(100%-3rem)]">
                <MapContainer
                  zones={mockMangroveZones}
                  alerts={unacknowledgedAlerts}
                />
              </div>
            </MobileCard>
          </div>

          {/* Alert Feed */}
          <div className={isMobile ? 'order-1' : ''}>
            <AlertFeed alerts={mockAlerts.slice(0, isMobile ? 5 : 8)} />
          </div>
        </div>

        {/* Charts Section - Responsive Layout */}
        <div className={`grid gap-6 ${isMobile ? 'grid-cols-1' : 'grid-cols-2'}`}>
          {/* NDVI Chart */}
          <div className={isMobile ? 'order-1' : ''}>
            <NDVITimeSeriesChart
              data={last12Months}
              title="NDVI Trend — All Zones (12 Months)"
            />
          </div>

          {/* Catch Data Chart */}
          <div className={isMobile ? 'order-2' : ''}>
            <MobileCard>
              <h3 className="text-lg font-semibold text-text-primary mb-4">
                Monthly Catch Volume & Revenue
              </h3>
              <ResponsiveContainer width="100%" height={isMobile ? 250 : 300}>
                <BarChart data={catchData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis 
                    dataKey="month" 
                    tick={{ fontSize: isMobile ? 10 : 12 }} 
                    stroke="#6B7280" 
                  />
                  <YAxis
                    yAxisId="left"
                    tick={{ fontSize: isMobile ? 10 : 12 }}
                    stroke="#6B7280"
                    label={!isMobile ? { value: 'Weight (kg)', angle: -90, position: 'insideLeft' } : undefined}
                  />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    tick={{ fontSize: isMobile ? 10 : 12 }}
                    stroke="#6B7280"
                    label={!isMobile ? { value: 'Revenue (Baht)', angle: 90, position: 'insideRight' } : undefined}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#FFFFFF',
                      border: '1px solid #E5E7EB',
                      borderRadius: '8px',
                      fontSize: isMobile ? '12px' : '14px'
                    }}
                  />
                  {!isMobile && <Legend />}
                  <Bar yAxisId="left" dataKey="weight" fill="#2B7BBF" name="Catch (kg)" />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="revenue"
                    stroke="#2D7A4F"
                    strokeWidth={2}
                    name="Revenue (Baht)"
                    dot={{ r: isMobile ? 3 : 4 }}
                  />
                </BarChart>
              </ResponsiveContainer>
            </MobileCard>
          </div>
        </div>
      </div>
    </PageWrapper>
  );
};
