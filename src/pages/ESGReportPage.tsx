import React, { useState } from 'react';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { Button } from '@/components/common/Button';
import { mockMangroveZones } from '@/data/mockMangroveZones';
import { mockCarbonCredits } from '@/data/mockCarbonCredits';
import { mockCatchLogs } from '@/data/mockCatchLogs';
import { mockAlerts } from '@/data/mockAlerts';
import { formatNumber } from '@/utils/formatters';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Download, CheckCircle } from 'lucide-react';

export const ESGReportPage: React.FC = () => {
  const [showToast, setShowToast] = useState(false);

  const totalArea = mockMangroveZones.reduce((sum, z) => sum + z.areaRai, 0);
  const healthyArea = mockMangroveZones.filter(z => z.healthStatus === 'healthy').reduce((sum, z) => sum + z.areaRai, 0);
  const totalCarbon = mockCarbonCredits.reduce((sum, c) => sum + c.co2EquivalentTon, 0);
  const activeFishers = new Set(mockCatchLogs.map(l => l.fisherName)).size;
  const totalCatch = mockCatchLogs.reduce((sum, l) => sum + l.totalWeightKg, 0);
  const acknowledgedRate = (mockAlerts.filter(a => a.isAcknowledged).length / mockAlerts.length * 100).toFixed(1);
  const recentObservations = mockMangroveZones.filter(z => {
    const daysDiff = (new Date().getTime() - new Date(z.lastObservationDate).getTime()) / (1000 * 60 * 60 * 24);
    return daysDiff <= 7;
  }).length;
  const transparencyScore = (recentObservations / mockMangroveZones.length * 100).toFixed(1);

  const carbonOverTime = [
    { month: 'Jan', carbon: 820 },
    { month: 'Feb', carbon: 945 },
    { month: 'Mar', carbon: 1120 },
    { month: 'Apr', carbon: 1285 },
    { month: 'May', carbon: 1450 },
    { month: 'Jun', carbon: 1620 },
  ];

  const sdgData = [
    {
      number: 1,
      name: 'No Poverty',
      description: 'Supporting fisher livelihoods through improved catch predictions and reduced operational costs.',
    },
    {
      number: 2,
      name: 'Zero Hunger',
      description: 'Enhancing food security by optimizing artisanal fishery productivity in coastal communities.',
    },
    {
      number: 13,
      name: 'Climate Action',
      description: 'Protecting and restoring mangrove forests as critical blue carbon sinks for climate mitigation.',
    },
    {
      number: 14,
      name: 'Life Below Water',
      description: 'Monitoring and preserving coastal ecosystems that support marine biodiversity and fishery health.',
    },
  ];

  const handleDownload = () => {
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
  };

  return (
    <PageWrapper title="ESG Report">
      <div className="space-y-8">
        <div className="bg-surface rounded-lg p-6 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-text-primary">Environmental, Social & Governance Report</h2>
              <p className="text-sm text-text-secondary mt-1">SIRINAPHA: Baan-Pla Link Platform Impact Assessment</p>
            </div>
            <Button onClick={handleDownload}>
              <Download size={18} className="mr-2" />
              Download ESG Report
            </Button>
          </div>
        </div>

        <div className="bg-surface rounded-lg p-6 shadow-sm">
          <h3 className="text-xl font-semibold text-text-primary mb-6 flex items-center gap-2">
            <span className="w-8 h-8 bg-success/20 text-success rounded-full flex items-center justify-center text-sm font-bold">E</span>
            Environmental Impact
          </h3>
          
          <div className="grid grid-cols-4 gap-6 mb-6">
            <div className="p-4 bg-neutral-50 rounded-lg">
              <div className="text-sm text-text-secondary mb-1">Mangrove Area Protected</div>
              <div className="text-2xl font-bold text-success">{formatNumber(totalArea, 2)} rai</div>
              <div className="text-xs text-success mt-1">+2.3% YoY</div>
            </div>
            <div className="p-4 bg-neutral-50 rounded-lg">
              <div className="text-sm text-text-secondary mb-1">Healthy Forest Coverage</div>
              <div className="text-2xl font-bold text-success">{((healthyArea / totalArea) * 100).toFixed(1)}%</div>
              <div className="text-xs text-text-secondary mt-1">{formatNumber(healthyArea, 2)} rai</div>
            </div>
            <div className="p-4 bg-neutral-50 rounded-lg">
              <div className="text-sm text-text-secondary mb-1">Carbon Sequestered</div>
              <div className="text-2xl font-bold text-success">{formatNumber(totalCarbon, 1)} tCO2</div>
              <div className="text-xs text-success mt-1">+18.5% YoY</div>
            </div>
            <div className="p-4 bg-neutral-50 rounded-lg">
              <div className="text-sm text-text-secondary mb-1">Biodiversity Indicator</div>
              <div className="text-2xl font-bold text-success">142 species</div>
              <div className="text-xs text-text-secondary mt-1">Estimated support</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-semibold text-text-primary mb-3">Cumulative Carbon Sequestration</h4>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={carbonOverTime}>
                  <defs>
                    <linearGradient id="carbonGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2D7A4F" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#2D7A4F" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis dataKey="month" tick={{ fontSize: 12 }} stroke="#6B7280" />
                  <YAxis tick={{ fontSize: 12 }} stroke="#6B7280" />
                  <Tooltip />
                  <Area type="monotone" dataKey="carbon" stroke="#2D7A4F" fillOpacity={1} fill="url(#carbonGradient)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-text-primary mb-3">Blue Carbon Comparison</h4>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-text-secondary">Mangrove Forest (1 rai)</span>
                    <span className="text-sm font-medium text-text-primary">4.2 tCO2/yr</span>
                  </div>
                  <div className="w-full bg-neutral-200 rounded-full h-3">
                    <div className="bg-success h-3 rounded-full" style={{ width: '100%' }} />
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-text-secondary">Terrestrial Forest (1 rai)</span>
                    <span className="text-sm font-medium text-text-primary">1.8 tCO2/yr</span>
                  </div>
                  <div className="w-full bg-neutral-200 rounded-full h-3">
                    <div className="bg-primary h-3 rounded-full" style={{ width: '43%' }} />
                  </div>
                </div>
                <div className="mt-4 p-3 bg-success/10 rounded-lg text-sm text-success">
                  Mangroves sequester 2.3x more CO2 than terrestrial forests per unit area
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-surface rounded-lg p-6 shadow-sm">
          <h3 className="text-xl font-semibold text-text-primary mb-6 flex items-center gap-2">
            <span className="w-8 h-8 bg-primary/20 text-primary rounded-full flex items-center justify-center text-sm font-bold">S</span>
            Social Impact
          </h3>
          
          <div className="grid grid-cols-4 gap-6 mb-6">
            <div className="p-4 bg-neutral-50 rounded-lg">
              <div className="text-sm text-text-secondary mb-1">Fisher Livelihoods Supported</div>
              <div className="text-2xl font-bold text-primary">{activeFishers}</div>
              <div className="text-xs text-text-secondary mt-1">Active fishers</div>
            </div>
            <div className="p-4 bg-neutral-50 rounded-lg">
              <div className="text-sm text-text-secondary mb-1">Income Improvement</div>
              <div className="text-2xl font-bold text-primary">+24.3%</div>
              <div className="text-xs text-text-secondary mt-1">Since platform adoption</div>
            </div>
            <div className="p-4 bg-neutral-50 rounded-lg">
              <div className="text-sm text-text-secondary mb-1">Training Sessions</div>
              <div className="text-2xl font-bold text-primary">12</div>
              <div className="text-xs text-text-secondary mt-1">340 participants</div>
            </div>
            <div className="p-4 bg-neutral-50 rounded-lg">
              <div className="text-sm text-text-secondary mb-1">Food Security Contribution</div>
              <div className="text-2xl font-bold text-primary">{formatNumber(totalCatch, 0)} kg</div>
              <div className="text-xs text-text-secondary mt-1">Total catch volume</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div className="p-4 bg-neutral-50 rounded-lg">
              <div className="text-sm font-semibold text-text-primary mb-2">Community Engagement</div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-text-secondary">Catch logs submitted</span>
                  <span className="font-medium text-text-primary">{mockCatchLogs.length}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-text-secondary">FSI recommendations followed</span>
                  <span className="font-medium text-text-primary">
                    {mockCatchLogs.filter(l => l.usedFSIRecommendation).length} ({((mockCatchLogs.filter(l => l.usedFSIRecommendation).length / mockCatchLogs.length) * 100).toFixed(0)}%)
                  </span>
                </div>
              </div>
            </div>
            <div className="p-4 bg-neutral-50 rounded-lg">
              <div className="text-sm font-semibold text-text-primary mb-2">Economic Impact</div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-text-secondary">Total revenue generated</span>
                  <span className="font-medium text-text-primary">
                    {formatNumber(mockCatchLogs.reduce((sum, l) => sum + l.estimatedRevenueBaht, 0))} Baht
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-text-secondary">Avg fuel cost savings</span>
                  <span className="font-medium text-success">-12.8%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-surface rounded-lg p-6 shadow-sm">
          <h3 className="text-xl font-semibold text-text-primary mb-6 flex items-center gap-2">
            <span className="w-8 h-8 bg-warning/20 text-warning rounded-full flex items-center justify-center text-sm font-bold">G</span>
            Governance & Transparency
          </h3>
          
          <div className="grid grid-cols-4 gap-6 mb-6">
            <div className="p-4 bg-neutral-50 rounded-lg">
              <div className="text-sm text-text-secondary mb-1">Data Transparency Score</div>
              <div className="text-2xl font-bold text-warning">{transparencyScore}%</div>
              <div className="text-xs text-text-secondary mt-1">Recent observations</div>
            </div>
            <div className="p-4 bg-neutral-50 rounded-lg">
              <div className="text-sm text-text-secondary mb-1">Alert Response Rate</div>
              <div className="text-2xl font-bold text-warning">{acknowledgedRate}%</div>
              <div className="text-xs text-text-secondary mt-1">Within 48 hours</div>
            </div>
            <div className="p-4 bg-neutral-50 rounded-lg">
              <div className="text-sm text-text-secondary mb-1">Platform Uptime</div>
              <div className="text-2xl font-bold text-warning">99.7%</div>
              <div className="text-xs text-text-secondary mt-1">Last 90 days</div>
            </div>
            <div className="p-4 bg-neutral-50 rounded-lg">
              <div className="text-sm text-text-secondary mb-1">Data Sources</div>
              <div className="text-2xl font-bold text-warning">5</div>
              <div className="text-xs text-text-secondary mt-1">Satellite & ocean data</div>
            </div>
          </div>

          <div className="p-4 bg-neutral-50 rounded-lg">
            <div className="text-sm font-semibold text-text-primary mb-3">Data Sources & Update Frequencies</div>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-sm">
                <div className="font-medium text-text-primary">Sentinel-2 MSI</div>
                <div className="text-text-secondary">NDVI monitoring, 5-day revisit</div>
              </div>
              <div className="text-sm">
                <div className="font-medium text-text-primary">MODIS Aqua</div>
                <div className="text-text-secondary">SST & Chlorophyll-a, daily</div>
              </div>
              <div className="text-sm">
                <div className="font-medium text-text-primary">Copernicus Marine</div>
                <div className="text-text-secondary">Ocean currents, daily</div>
              </div>
              <div className="text-sm">
                <div className="font-medium text-text-primary">Fisher Community Logs</div>
                <div className="text-text-secondary">Catch data, real-time</div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-surface rounded-lg p-6 shadow-sm">
          <h3 className="text-xl font-semibold text-text-primary mb-6">UN Sustainable Development Goals Alignment</h3>
          <div className="grid grid-cols-2 gap-6">
            {sdgData.map(sdg => (
              <div key={sdg.number} className="p-4 border-2 border-primary/20 rounded-lg">
                <div className="flex items-start gap-4">
                  <div className="w-16 h-16 bg-primary text-white rounded-lg flex items-center justify-center flex-shrink-0">
                    <div className="text-center">
                      <div className="text-2xl font-bold">{sdg.number}</div>
                    </div>
                  </div>
                  <div>
                    <div className="font-semibold text-text-primary mb-1">{sdg.name}</div>
                    <div className="text-sm text-text-secondary">{sdg.description}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {showToast && (
        <div className="fixed bottom-6 right-6 bg-success text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-2 z-50">
          <CheckCircle size={20} />
          <span>Report generation initiated</span>
        </div>
      )}
    </PageWrapper>
  );
};
