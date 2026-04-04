import React, { useState } from 'react';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { AdvancedMapContainer } from '@/components/map/AdvancedMapContainer';
import { mockMangroveZones } from '@/data/mockMangroveZones';
import { mockAlerts } from '@/data/mockAlerts';
import { 
  getHeatmapData, 
  heatmapConfigs, 
  weatherStations, 
  tideGauges 
} from '@/data/mockHeatmapData';
import { useIsMobile, MobileCard, TouchButton } from '@/components/common/MobileOptimized';
import { 
  Map, 
  Layers, 
  BarChart3, 
  Thermometer, 
  Waves, 
  Leaf, 
  Factory,
  Fish,
  AlertTriangle,
  Info
} from 'lucide-react';

export const AdvancedMapPage: React.FC = () => {
  const [selectedDataLayer, setSelectedDataLayer] = useState<'biodiversity' | 'carbon' | 'fishery' | 'degradation'>('biodiversity');
  const [showStatistics, setShowStatistics] = useState(true);
  const isMobile = useIsMobile();

  const currentHeatmapData = getHeatmapData(selectedDataLayer);
  const currentConfig = heatmapConfigs[selectedDataLayer];

  const calculateStatistics = () => {
    if (currentHeatmapData.length === 0) return null;
    
    const values = currentHeatmapData.map(p => p.value);
    const sum = values.reduce((a, b) => a + b, 0);
    const avg = sum / values.length;
    const min = Math.min(...values);
    const max = Math.max(...values);
    const median = values.sort((a, b) => a - b)[Math.floor(values.length / 2)];
    
    return { avg, min, max, median, count: values.length };
  };

  const stats = calculateStatistics();

  const getLayerIcon = (type: string) => {
    switch (type) {
      case 'biodiversity':
        return <Leaf size={16} className="text-green-600" />;
      case 'carbon':
        return <Factory size={16} className="text-emerald-600" />;
      case 'fishery':
        return <Fish size={16} className="text-blue-600" />;
      case 'degradation':
        return <AlertTriangle size={16} className="text-red-600" />;
      default:
        return <BarChart3 size={16} />;
    }
  };

  return (
    <PageWrapper title="Advanced Map Analytics">
      <div className="space-y-6">
        {/* Header Controls - Mobile Responsive */}
        <div className="bg-surface rounded-lg p-4 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
              <div className="flex items-center gap-2">
                <Map size={20} className="text-primary" />
                <h2 className="text-lg font-semibold text-text-primary">Interactive Map Viewer</h2>
              </div>
              <div className="text-sm text-text-secondary">
                Real-time environmental monitoring and analysis
              </div>
            </div>
            <div className="flex items-center gap-2">
              <TouchButton
                onClick={() => setShowStatistics(!showStatistics)}
                variant={showStatistics ? 'primary' : 'secondary'}
                size={isMobile ? 'md' : 'sm'}
                className="flex items-center gap-2"
              >
                <BarChart3 size={16} />
                {!isMobile && 'Statistics'}
              </TouchButton>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Data Layer Selection - Mobile: Full width, Desktop: 1 column */}
          <div className="lg:col-span-1 space-y-4">
            <MobileCard>
              <h3 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2">
                <Layers size={16} />
                Data Layers
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-2">
                {Object.entries(heatmapConfigs).map(([key, config]) => (
                  <TouchButton
                    key={key}
                    onClick={() => setSelectedDataLayer(key as any)}
                    variant={selectedDataLayer === key ? 'primary' : 'outline'}
                    size="md"
                    className="justify-start p-3"
                  >
                    <div className="flex items-center gap-2 w-full">
                      {getLayerIcon(key)}
                      <div className="text-left">
                        <div className="font-medium text-sm">{config.name}</div>
                        {!isMobile && (
                          <div className="text-xs opacity-80 mt-1">
                            {config.description}
                          </div>
                        )}
                      </div>
                    </div>
                  </TouchButton>
                ))}
              </div>
            </MobileCard>

            {/* Environmental Monitoring - Hide on mobile, show on tablet+ */}
            {!isMobile && (
              <MobileCard>
                <h3 className="text-sm font-semibold text-text-primary mb-3">Environmental Monitoring</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Thermometer size={14} className="text-orange-500" />
                      <span className="text-sm text-text-primary">Weather Stations</span>
                    </div>
                    <span className="text-xs text-text-secondary">{weatherStations.length} active</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Waves size={14} className="text-blue-500" />
                      <span className="text-sm text-text-primary">Tide Gauges</span>
                    </div>
                    <span className="text-xs text-text-secondary">{tideGauges.length} active</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <AlertTriangle size={14} className="text-red-500" />
                      <span className="text-sm text-text-primary">Active Alerts</span>
                    </div>
                    <span className="text-xs text-text-secondary">
                      {mockAlerts.filter(a => !a.isAcknowledged).length} alerts
                    </span>
                  </div>
                </div>
              </MobileCard>
            )}

            {/* Current Layer Statistics - Responsive */}
            {showStatistics && stats && (
              <MobileCard>
                <h3 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2">
                  <BarChart3 size={16} />
                  <span className="hidden sm:inline">{currentConfig.name}</span>
                  <span className="sm:hidden">Statistics</span>
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  <div className="text-center p-3 bg-neutral-50 rounded-lg">
                    <div className="text-xs text-text-secondary">จุดข้อมูล</div>
                    <div className="text-lg font-bold text-text-primary">{stats.count}</div>
                  </div>
                  <div className="text-center p-3 bg-neutral-50 rounded-lg">
                    <div className="text-xs text-text-secondary">ค่าเฉลี่ย</div>
                    <div className="text-lg font-bold text-text-primary">
                      {stats.avg.toFixed(1)}
                      {!isMobile && <span className="text-sm font-normal ml-1">{currentConfig.unit}</span>}
                    </div>
                  </div>
                  <div className="text-center p-3 bg-neutral-50 rounded-lg">
                    <div className="text-xs text-text-secondary">ค่ามัธยฐาน</div>
                    <div className="text-lg font-bold text-text-primary">
                      {stats.median.toFixed(1)}
                      {!isMobile && <span className="text-sm font-normal ml-1">{currentConfig.unit}</span>}
                    </div>
                  </div>
                  <div className="text-center p-3 bg-neutral-50 rounded-lg">
                    <div className="text-xs text-text-secondary">ช่วงค่า</div>
                    <div className="text-lg font-bold text-text-primary">
                      {stats.min.toFixed(1)}-{stats.max.toFixed(1)}
                    </div>
                  </div>
                </div>
                
                {/* Data Quality Indicator */}
                <div className="mt-3 pt-3 border-t border-neutral-200">
                  <div className="flex items-center gap-2 text-xs">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-text-secondary">Data Quality: Excellent</span>
                  </div>
                  <div className="text-xs text-text-secondary mt-1">
                    Last updated: {new Date().toLocaleTimeString('th-TH')}
                  </div>
                </div>
              </MobileCard>
            )}

            {/* Layer Information - Hide on mobile */}
            {!isMobile && (
              <MobileCard>
                <h3 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2">
                  <Info size={16} />
                  Layer Information
                </h3>
                <div className="space-y-2 text-xs text-text-secondary">
                  <div>
                    <span className="font-medium">Data Source:</span> Satellite imagery and field sensors
                  </div>
                  <div>
                    <span className="font-medium">Resolution:</span> 10m spatial resolution
                  </div>
                  <div>
                    <span className="font-medium">Update Frequency:</span> Daily
                  </div>
                  <div>
                    <span className="font-medium">Coverage:</span> Kung Krabaen Bay area
                  </div>
                </div>
              </MobileCard>
            )}
          </div>

          {/* Main Map - Responsive height */}
          <div className="lg:col-span-3">
            <div className="bg-surface rounded-lg shadow-sm overflow-hidden" style={{ 
              height: window.innerWidth < 768 ? '60vh' : '800px' 
            }}>
              <AdvancedMapContainer
                zones={mockMangroveZones}
                alerts={mockAlerts.filter(a => !a.isAcknowledged)}
                center={[12.57, 101.90]}
                zoom={window.innerWidth < 768 ? 10 : 12}
                showThailandBoundary={true}
                showProvinceBoundaries={true}
              />
            </div>
          </div>
        </div>

        {/* Quick Stats Cards - Responsive Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-surface rounded-lg p-4 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <Leaf size={20} className="text-green-600" />
              </div>
              <div>
                <div className="text-sm text-text-secondary">Healthy Zones</div>
                <div className="text-xl font-bold text-text-primary">
                  {mockMangroveZones.filter(z => z.healthStatus === 'healthy').length}
                </div>
              </div>
            </div>
          </div>

          <div className="bg-surface rounded-lg p-4 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                <AlertTriangle size={20} className="text-yellow-600" />
              </div>
              <div>
                <div className="text-sm text-text-secondary">Stressed Zones</div>
                <div className="text-xl font-bold text-text-primary">
                  {mockMangroveZones.filter(z => z.healthStatus === 'stressed').length}
                </div>
              </div>
            </div>
          </div>

          <div className="bg-surface rounded-lg p-4 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                <AlertTriangle size={20} className="text-red-600" />
              </div>
              <div>
                <div className="text-sm text-text-secondary">Degraded Zones</div>
                <div className="text-xl font-bold text-text-primary">
                  {mockMangroveZones.filter(z => z.healthStatus === 'degraded').length}
                </div>
              </div>
            </div>
          </div>

          <div className="bg-surface rounded-lg p-4 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <BarChart3 size={20} className="text-blue-600" />
              </div>
              <div>
                <div className="text-sm text-text-secondary">Total Area</div>
                <div className="text-xl font-bold text-text-primary">
                  {mockMangroveZones.reduce((sum, z) => sum + z.areaRai, 0).toFixed(0)} <span className="text-sm font-normal">rai</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </PageWrapper>
  );
};