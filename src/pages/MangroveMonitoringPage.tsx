import React, { useState } from 'react';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { Badge } from '@/components/common/Badge';
import { mockMangroveZones } from '@/data/mockMangroveZones';
import { mockNDVIHistory } from '@/data/mockNDVIHistory';
import { mockAlerts } from '@/data/mockAlerts';
import { formatArea, formatNDVI } from '@/utils/formatters';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea } from 'recharts';
import { AdvancedMapContainer } from '@/components/map/AdvancedMapContainer';
import { ArrowUp, ArrowDown } from 'lucide-react';

export const MangroveMonitoringPage: React.FC = () => {
  const [selectedZoneId, setSelectedZoneId] = useState(mockMangroveZones[0].zoneId);
  const [sortColumn, setSortColumn] = useState<string>('zoneName');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [filterStatus, setFilterStatus] = useState<string>('all');

  const selectedZone = mockMangroveZones.find(z => z.zoneId === selectedZoneId);

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  const filteredZones = mockMangroveZones.filter(zone => 
    filterStatus === 'all' || zone.healthStatus === filterStatus
  );

  const sortedZones = [...filteredZones].sort((a, b) => {
    let aVal: any = a[sortColumn as keyof typeof a];
    let bVal: any = b[sortColumn as keyof typeof b];
    
    if (typeof aVal === 'string') {
      return sortDirection === 'asc' 
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal);
    }
    
    return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
  });

  const getHealthBadgeVariant = (status: string) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'stressed': return 'warning';
      case 'degraded': return 'danger';
      default: return 'default';
    }
  };

  return (
    <PageWrapper title="Mangrove Monitoring">
      <div className="space-y-6">
        <div className="bg-surface rounded-lg p-4 shadow-sm">
          <div className="flex items-center gap-4 mb-4">
            <label className="text-sm font-medium text-text-primary">Select Zone:</label>
            <select
              value={selectedZoneId}
              onChange={(e) => setSelectedZoneId(e.target.value)}
              className="px-4 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {mockMangroveZones.map(zone => (
                <option key={zone.zoneId} value={zone.zoneId}>
                  {zone.zoneName} - {zone.healthStatus}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-5 gap-6">
          <div className="col-span-3">
            <div className="bg-surface rounded-lg p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-text-primary mb-4">
                NDVI Time Series (36 Months)
              </h3>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={mockNDVIHistory}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 11 }}
                    stroke="#6B7280"
                    interval={5}
                  />
                  <YAxis
                    domain={[0, 1]}
                    tick={{ fontSize: 12 }}
                    stroke="#6B7280"
                    label={{ value: 'NDVI', angle: -90, position: 'insideLeft' }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#FFFFFF',
                      border: '1px solid #E5E7EB',
                      borderRadius: '8px',
                    }}
                    formatter={(value: number) => value.toFixed(4)}
                  />
                  <ReferenceArea y1={0.5} y2={1.0} fill="#2D7A4F" fillOpacity={0.1} label="Healthy" />
                  <ReferenceArea y1={0.3} y2={0.5} fill="#D69E2E" fillOpacity={0.1} label="Stressed" />
                  <ReferenceArea y1={0} y2={0.3} fill="#C53030" fillOpacity={0.1} label="Degraded" />
                  <Line
                    type="monotone"
                    dataKey="meanNDVI"
                    stroke="#2B7BBF"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="minNDVI"
                    stroke="#2B7BBF"
                    strokeWidth={1}
                    strokeDasharray="3 3"
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="maxNDVI"
                    stroke="#2B7BBF"
                    strokeWidth={1}
                    strokeDasharray="3 3"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="col-span-2 space-y-6">
            {selectedZone && (
              <>
                <div className="bg-surface rounded-lg p-6 shadow-sm">
                  <h3 className="text-lg font-semibold text-text-primary mb-4">Zone Details</h3>
                  <div className="space-y-3">
                    <div>
                      <div className="text-sm text-text-secondary">Zone Name</div>
                      <div className="font-medium text-text-primary">{selectedZone.zoneName}</div>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <div className="text-sm text-text-secondary">Province</div>
                        <div className="font-medium text-text-primary">{selectedZone.province}</div>
                      </div>
                      <div>
                        <div className="text-sm text-text-secondary">District</div>
                        <div className="font-medium text-text-primary">{selectedZone.district}</div>
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-text-secondary">Area</div>
                      <div className="font-medium text-text-primary">{formatArea(selectedZone.areaRai)}</div>
                    </div>
                    <div>
                      <div className="text-sm text-text-secondary mb-1">Current NDVI</div>
                      <div className="flex items-center gap-2">
                        <div className="text-2xl font-bold text-text-primary">
                          {formatNDVI(selectedZone.currentNDVI)}
                        </div>
                        <Badge variant={getHealthBadgeVariant(selectedZone.healthStatus)}>
                          {selectedZone.healthStatus}
                        </Badge>
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-text-secondary">Previous NDVI</div>
                      <div className="flex items-center gap-2">
                        <div className="font-medium text-text-primary">
                          {formatNDVI(selectedZone.previousNDVI)}
                        </div>
                        <div className={`flex items-center text-sm ${selectedZone.deltaNDVI >= 0 ? 'text-success' : 'text-danger'}`}>
                          {selectedZone.deltaNDVI >= 0 ? <ArrowUp size={16} /> : <ArrowDown size={16} />}
                          {Math.abs(selectedZone.deltaNDVI).toFixed(4)}
                        </div>
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-text-secondary">Last Observation</div>
                      <div className="font-medium text-text-primary">{selectedZone.lastObservationDate}</div>
                    </div>
                    <div>
                      <div className="text-sm text-text-secondary">Satellite Source</div>
                      <div className="font-medium text-text-primary">Sentinel-2 MSI</div>
                    </div>
                  </div>
                </div>

                <div className="bg-surface rounded-lg p-4 shadow-sm h-64">
                  <h3 className="text-sm font-semibold text-text-primary mb-2">Zone Location</h3>
                  <div className="h-[calc(100%-2rem)]">
                    <AdvancedMapContainer
                      zones={[selectedZone]}
                      center={selectedZone.centroid}
                      zoom={13}
                    />
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        <div className="bg-surface rounded-lg p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-text-primary">All Zones Summary</h3>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="all">All Status</option>
              <option value="healthy">Healthy</option>
              <option value="stressed">Stressed</option>
              <option value="degraded">Degraded</option>
            </select>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-200">
                  <th
                    className="text-left py-3 px-4 text-sm font-semibold text-text-primary cursor-pointer hover:bg-neutral-50"
                    onClick={() => handleSort('zoneName')}
                  >
                    Zone Name {sortColumn === 'zoneName' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    className="text-left py-3 px-4 text-sm font-semibold text-text-primary cursor-pointer hover:bg-neutral-50"
                    onClick={() => handleSort('province')}
                  >
                    Province {sortColumn === 'province' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    className="text-right py-3 px-4 text-sm font-semibold text-text-primary cursor-pointer hover:bg-neutral-50"
                    onClick={() => handleSort('areaRai')}
                  >
                    Area (rai) {sortColumn === 'areaRai' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    className="text-right py-3 px-4 text-sm font-semibold text-text-primary cursor-pointer hover:bg-neutral-50"
                    onClick={() => handleSort('currentNDVI')}
                  >
                    Current NDVI {sortColumn === 'currentNDVI' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-text-primary">
                    Health Status
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-text-primary">
                    Delta NDVI
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-text-primary">
                    Last Observation
                  </th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-text-primary">
                    Alerts
                  </th>
                </tr>
              </thead>
              <tbody>
                {sortedZones.map((zone, index) => {
                  const zoneAlerts = mockAlerts.filter(a => a.zoneId === zone.zoneId && !a.isAcknowledged);
                  return (
                    <tr
                      key={zone.zoneId}
                      className={`border-b border-neutral-100 hover:bg-neutral-50 cursor-pointer ${
                        index % 2 === 0 ? 'bg-white' : 'bg-neutral-50/50'
                      }`}
                      onClick={() => setSelectedZoneId(zone.zoneId)}
                    >
                      <td className="py-3 px-4 text-sm text-text-primary">{zone.zoneName}</td>
                      <td className="py-3 px-4 text-sm text-text-secondary">{zone.province}</td>
                      <td className="py-3 px-4 text-sm text-text-primary text-right">
                        {zone.areaRai.toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-sm text-text-primary text-right">
                        {formatNDVI(zone.currentNDVI)}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <Badge variant={getHealthBadgeVariant(zone.healthStatus)} size="sm">
                          {zone.healthStatus}
                        </Badge>
                      </td>
                      <td className={`py-3 px-4 text-sm text-right ${zone.deltaNDVI >= 0 ? 'text-success' : 'text-danger'}`}>
                        {zone.deltaNDVI >= 0 ? '+' : ''}{zone.deltaNDVI.toFixed(4)}
                      </td>
                      <td className="py-3 px-4 text-sm text-text-secondary">{zone.lastObservationDate}</td>
                      <td className="py-3 px-4 text-center">
                        {zoneAlerts.length > 0 && (
                          <Badge variant="danger" size="sm">{zoneAlerts.length}</Badge>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </PageWrapper>
  );
};
