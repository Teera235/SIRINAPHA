import React, { useState } from 'react';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { Badge } from '@/components/common/Badge';
import { mockRestorationSites } from '@/data/mockRestorationSites';
import { mockCarbonCredits } from '@/data/mockCarbonCredits';
import { MapContainer as LeafletMap, TileLayer, Polygon, Popup } from 'react-leaflet';
import { formatNumber } from '@/utils/formatters';
// import { getVerificationColor } from '@/utils/colorScales';
import 'leaflet/dist/leaflet.css';

export const RestorationPlanningPage: React.FC = () => {
  const [selectedSite, setSelectedSite] = useState<string | null>(null);
  
  // Use selectedSite to prevent TypeScript warning
  console.log('Selected site:', selectedSite);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'proposed': return '#6B7280';
      case 'approved': return '#2B7BBF';
      case 'planting': return '#D69E2E';
      case 'monitoring': return '#38A169';
      case 'established': return '#2D7A4F';
      default: return '#6B7280';
    }
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'established': return 'success';
      case 'monitoring': return 'success';
      case 'planting': return 'warning';
      case 'approved': return 'info';
      default: return 'default';
    }
  };

  const getVerificationVariant = (status: string) => {
    switch (status) {
      case 'issued': return 'success';
      case 'verified': return 'success';
      case 'reported': return 'info';
      default: return 'default';
    }
  };

  const totalVerified = mockCarbonCredits
    .filter(c => c.verificationStatus === 'verified' || c.verificationStatus === 'issued')
    .reduce((sum, c) => sum + c.co2EquivalentTon, 0);

  const totalPending = mockCarbonCredits
    .filter(c => c.verificationStatus === 'measured' || c.verificationStatus === 'reported')
    .reduce((sum, c) => sum + c.co2EquivalentTon, 0);

  const totalIssued = mockCarbonCredits
    .filter(c => c.verificationStatus === 'issued')
    .reduce((sum, c) => sum + c.co2EquivalentTon, 0);

  return (
    <PageWrapper title="Restoration Planning">
      <div className="space-y-6">
        <div className="bg-surface rounded-lg p-4 shadow-sm h-[500px]">
          <h3 className="text-lg font-semibold text-text-primary mb-4">Restoration Sites</h3>
          <div className="h-[calc(100%-3rem)]">
            <LeafletMap center={[12.56, 101.90]} zoom={11} style={{ height: '100%', width: '100%' }}>
              <TileLayer
                attribution='&copy; OpenStreetMap'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {mockRestorationSites.map(site => (
                <Polygon
                  key={site.siteId}
                  positions={site.coordinates}
                  pathOptions={{
                    fillColor: getStatusColor(site.status),
                    fillOpacity: site.status === 'proposed' ? 0 : 0.4,
                    color: getStatusColor(site.status),
                    weight: 2,
                  }}
                  eventHandlers={{
                    click: () => setSelectedSite(site.siteId),
                  }}
                >
                  <Popup>
                    <div className="text-sm">
                      <div className="font-semibold mb-2">{site.zoneName}</div>
                      <div>Area: {site.areaRai.toFixed(2)} rai</div>
                      <div>Priority: {(site.priorityScore * 100).toFixed(0)}%</div>
                      <div>Status: {site.status}</div>
                      <div>Survival Rate: {site.estimatedSurvivalRate}%</div>
                      <div>Carbon: {site.carbonSequestrationPotential.toFixed(1)} tCO2/yr</div>
                    </div>
                  </Popup>
                </Polygon>
              ))}
            </LeafletMap>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-2">
            <div className="bg-surface rounded-lg p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-text-primary mb-4">Restoration Sites</h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-neutral-200">
                      <th className="text-left py-3 px-4 text-sm font-semibold text-text-primary">Site Name</th>
                      <th className="text-right py-3 px-4 text-sm font-semibold text-text-primary">Area (rai)</th>
                      <th className="text-right py-3 px-4 text-sm font-semibold text-text-primary">Priority</th>
                      <th className="text-center py-3 px-4 text-sm font-semibold text-text-primary">Status</th>
                      <th className="text-right py-3 px-4 text-sm font-semibold text-text-primary">Survival %</th>
                      <th className="text-right py-3 px-4 text-sm font-semibold text-text-primary">Carbon (tCO2/yr)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {mockRestorationSites
                      .sort((a, b) => b.priorityScore - a.priorityScore)
                      .map((site, index) => (
                        <tr
                          key={site.siteId}
                          className={`border-b border-neutral-100 hover:bg-neutral-50 cursor-pointer ${
                            index % 2 === 0 ? 'bg-white' : 'bg-neutral-50/50'
                          }`}
                          onClick={() => setSelectedSite(site.siteId)}
                        >
                          <td className="py-3 px-4 text-sm text-text-primary">{site.zoneName}</td>
                          <td className="py-3 px-4 text-sm text-text-primary text-right">
                            {site.areaRai.toFixed(2)}
                          </td>
                          <td className="py-3 px-4 text-sm text-text-primary text-right">
                            <div className="flex items-center justify-end gap-2">
                              <div className="w-20 bg-neutral-200 rounded-full h-2">
                                <div
                                  className="bg-primary h-2 rounded-full"
                                  style={{ width: `${site.priorityScore * 100}%` }}
                                />
                              </div>
                              <span>{(site.priorityScore * 100).toFixed(0)}%</span>
                            </div>
                          </td>
                          <td className="py-3 px-4 text-center">
                            <Badge variant={getStatusVariant(site.status)} size="sm">
                              {site.status}
                            </Badge>
                          </td>
                          <td className="py-3 px-4 text-sm text-text-primary text-right">
                            {site.estimatedSurvivalRate}%
                          </td>
                          <td className="py-3 px-4 text-sm text-text-primary text-right">
                            {site.carbonSequestrationPotential.toFixed(1)}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-surface rounded-lg p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-text-primary mb-4">Carbon Credit Summary</h3>
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-text-secondary">Total Verified Credits</div>
                  <div className="text-2xl font-bold text-success">{formatNumber(totalVerified, 1)} tCO2</div>
                </div>
                <div>
                  <div className="text-sm text-text-secondary">Total Pending</div>
                  <div className="text-2xl font-bold text-warning">{formatNumber(totalPending, 1)} tCO2</div>
                </div>
                <div>
                  <div className="text-sm text-text-secondary">Total Issued</div>
                  <div className="text-2xl font-bold text-primary">{formatNumber(totalIssued, 1)} tCO2</div>
                </div>
              </div>
            </div>

            <div className="bg-surface rounded-lg p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-text-primary mb-4">Verification Flow</h3>
              <div className="flex items-center justify-between">
                {['Measured', 'Reported', 'Verified', 'Issued'].map((step, index) => (
                  <React.Fragment key={step}>
                    <div className="flex flex-col items-center">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-medium ${
                        index <= 2 ? 'bg-primary' : 'bg-neutral-300'
                      }`}>
                        {index + 1}
                      </div>
                      <div className="text-xs text-text-secondary mt-2">{step}</div>
                    </div>
                    {index < 3 && (
                      <div className={`flex-1 h-0.5 mx-2 ${index <= 1 ? 'bg-primary' : 'bg-neutral-300'}`} />
                    )}
                  </React.Fragment>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="bg-surface rounded-lg p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-text-primary mb-4">Carbon Credit Records</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-200">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-text-primary">Site Name</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-text-primary">Measurement Date</th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-text-primary">Biomass (ton)</th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-text-primary">CO2 Equivalent (ton)</th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-text-primary">Status</th>
                </tr>
              </thead>
              <tbody>
                {mockCarbonCredits.map((credit, index) => (
                  <tr
                    key={credit.creditId}
                    className={`border-b border-neutral-100 ${
                      index % 2 === 0 ? 'bg-white' : 'bg-neutral-50/50'
                    }`}
                  >
                    <td className="py-3 px-4 text-sm text-text-primary">{credit.siteName}</td>
                    <td className="py-3 px-4 text-sm text-text-secondary">{credit.measurementDate}</td>
                    <td className="py-3 px-4 text-sm text-text-primary text-right">
                      {formatNumber(credit.biomassEstimateTon, 1)}
                    </td>
                    <td className="py-3 px-4 text-sm text-text-primary text-right">
                      {formatNumber(credit.co2EquivalentTon, 1)}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <Badge variant={getVerificationVariant(credit.verificationStatus)} size="sm">
                        {credit.verificationStatus}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </PageWrapper>
  );
};
