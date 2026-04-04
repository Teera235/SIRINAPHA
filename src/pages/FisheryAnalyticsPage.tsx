import React from 'react';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { mockFSIData } from '@/data/mockFSIData';
import { mockCatchLogs } from '@/data/mockCatchLogs';
import { mockEcosystemForecast } from '@/data/mockEcosystemForecast';
import { mockMangroveZones } from '@/data/mockMangroveZones';
import { MapContainer as LeafletMap, TileLayer, CircleMarker, Polygon, Popup } from 'react-leaflet';
import { LineChart, Line, PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { getFSIColor, getHealthFillColor, getHealthColor } from '@/utils/colorScales';
import 'leaflet/dist/leaflet.css';

export const FisheryAnalyticsPage: React.FC = () => {
  const speciesData = mockCatchLogs.reduce((acc, log) => {
    log.speciesComposition.forEach(sp => {
      if (!acc[sp.species]) acc[sp.species] = 0;
      acc[sp.species] += sp.weightKg;
    });
    return acc;
  }, {} as Record<string, number>);

  const pieData = Object.entries(speciesData)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([name, value]) => ({ name, value: Math.round(value) }));

  const totalWeight = pieData.reduce((sum, d) => sum + d.value, 0);

  const COLORS = ['#2D7A4F', '#2B7BBF', '#D69E2E', '#C05621', '#4A5568'];

  const withFSI = mockCatchLogs.filter(l => l.usedFSIRecommendation);
  const withoutFSI = mockCatchLogs.filter(l => !l.usedFSIRecommendation);
  
  const avgFuelWithFSI = withFSI.reduce((sum, l) => sum + l.fuelCostBaht, 0) / withFSI.length;
  const avgFuelWithoutFSI = withoutFSI.reduce((sum, l) => sum + l.fuelCostBaht, 0) / withoutFSI.length;

  const fuelData = [
    { category: 'With FSI', cost: Math.round(avgFuelWithFSI) },
    { category: 'Without FSI', cost: Math.round(avgFuelWithoutFSI) },
  ];

  const cpueByMonth = mockCatchLogs.reduce((acc, log) => {
    const month = log.tripDate.substring(0, 7);
    if (!acc[month]) acc[month] = { trips: 0, weight: 0 };
    acc[month].trips++;
    acc[month].weight += log.totalWeightKg;
    return acc;
  }, {} as Record<string, { trips: number; weight: number }>);

  const cpueData = Object.entries(cpueByMonth)
    .sort((a, b) => a[0].localeCompare(b[0]))
    .slice(-6)
    .map(([month, data]) => ({
      month: month.substring(5),
      cpue: parseFloat((data.weight / data.trips).toFixed(2)),
    }));

  const forecastData = mockEcosystemForecast.map(f => ({
    date: f.date.substring(5),
    cpue: f.predictedCPUE,
    lower: f.lowerBound,
    upper: f.upperBound,
  }));

  const improvementPct = ((forecastData[forecastData.length - 1].cpue - forecastData[0].cpue) / forecastData[0].cpue * 100).toFixed(1);

  return (
    <PageWrapper title="Fishery Analytics">
      <div className="space-y-6">
        <div className="bg-surface rounded-lg p-4 shadow-sm h-[500px]">
          <h3 className="text-lg font-semibold text-text-primary mb-4">
            Fishery Suitability Index (FSI) Map
          </h3>
          <div className="h-[calc(100%-3rem)]">
            <LeafletMap center={[12.54, 101.90]} zoom={11} style={{ height: '100%', width: '100%' }}>
              <TileLayer
                attribution='&copy; OpenStreetMap'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {mockMangroveZones.map(zone => (
                <Polygon
                  key={zone.zoneId}
                  positions={zone.coordinates}
                  pathOptions={{
                    fillColor: getHealthFillColor(zone.healthStatus),
                    fillOpacity: 0.2,
                    color: getHealthColor(zone.healthStatus),
                    weight: 1,
                  }}
                />
              ))}
              {mockFSIData.filter((_, i) => i % 3 === 0).map((point, idx) => (
                <CircleMarker
                  key={idx}
                  center={[point.lat, point.lng]}
                  radius={4 + point.confidence * 3}
                  pathOptions={{
                    fillColor: getFSIColor(point.fsiScore),
                    fillOpacity: 0.7,
                    color: getFSIColor(point.fsiScore),
                    weight: 1,
                  }}
                >
                  <Popup>
                    <div className="text-sm">
                      <div>FSI Score: {point.fsiScore.toFixed(3)}</div>
                      <div>Confidence: {(point.confidence * 100).toFixed(0)}%</div>
                      <div className="mt-2 text-xs">
                        <div>SST: {(point.contributingFactors.sst * 100).toFixed(0)}%</div>
                        <div>Chl-a: {(point.contributingFactors.chlorophyllA * 100).toFixed(0)}%</div>
                        <div>NDVI Prox: {(point.contributingFactors.ndviProximity * 100).toFixed(0)}%</div>
                        <div>Season: {(point.contributingFactors.seasonality * 100).toFixed(0)}%</div>
                      </div>
                    </div>
                  </Popup>
                </CircleMarker>
              ))}
            </LeafletMap>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6">
          <div className="bg-surface rounded-lg p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-text-primary mb-4">CPUE Trend (6 Months)</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={cpueData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} stroke="#6B7280" />
                <YAxis tick={{ fontSize: 12 }} stroke="#6B7280" />
                <Tooltip />
                <Line type="monotone" dataKey="cpue" stroke="#2B7BBF" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-surface rounded-lg p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Species Composition</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey="value"
                  label={(entry) => `${entry.name}: ${((entry.value / totalWeight) * 100).toFixed(1)}%`}
                  labelLine={{ stroke: '#6B7280', strokeWidth: 1 }}
                >
                  {pieData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => `${value} kg`} />
              </PieChart>
            </ResponsiveContainer>
            <div className="text-center text-sm text-text-secondary mt-2">
              Total: {totalWeight} kg
            </div>
          </div>

          <div className="bg-surface rounded-lg p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Fuel Cost Analysis</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={fuelData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="category" tick={{ fontSize: 12 }} stroke="#6B7280" />
                <YAxis tick={{ fontSize: 12 }} stroke="#6B7280" label={{ value: 'Baht', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Bar dataKey="cost" fill="#2B7BBF">
                  {fuelData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={index === 0 ? '#2D7A4F' : '#C05621'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="text-center text-sm text-success mt-2">
              {((1 - avgFuelWithFSI / avgFuelWithoutFSI) * 100).toFixed(1)}% savings with FSI
            </div>
          </div>
        </div>

        <div className="bg-surface rounded-lg p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-text-primary">90-Day CPUE Forecast</h3>
            <div className="px-3 py-1 bg-primary/10 text-primary text-xs rounded-full">
              Model v2.1.3
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={forecastData}>
              <defs>
                <linearGradient id="cpueGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2B7BBF" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#2B7BBF" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#6B7280" interval={14} />
              <YAxis tick={{ fontSize: 12 }} stroke="#6B7280" label={{ value: 'CPUE (kg/trip)', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Area type="monotone" dataKey="upper" stroke="none" fill="#2B7BBF" fillOpacity={0.1} />
              <Area type="monotone" dataKey="lower" stroke="none" fill="#FFFFFF" fillOpacity={1} />
              <Line type="monotone" dataKey="cpue" stroke="#2B7BBF" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
          <div className="mt-4 p-4 bg-neutral-50 rounded-lg text-sm text-text-secondary">
            Model projects a {improvementPct}% increase in catch productivity over the next 90 days, 
            correlated with improving mangrove health in adjacent zones.
          </div>
        </div>
      </div>
    </PageWrapper>
  );
};
