import React, { useState, useEffect } from 'react';
import { MapContainer as LeafletMap, TileLayer, Polygon, CircleMarker, Popup, Tooltip, Marker } from 'react-leaflet';
import { MangroveZone, DegradationAlert } from '@/types';
import { getHealthColor, getHealthFillColor, getSeverityColor } from '@/utils/colorScales';
import { formatArea, formatNDVI } from '@/utils/formatters';
import { thailandBoundary } from '@/data/thailandBoundary';
import { thailandProvinces, regions } from '@/data/thailandProvinces';
import { 
  getHeatmapData, 
  heatmapConfigs, 
  weatherStations, 
  tideGauges,
  HeatmapPoint
} from '@/data/mockHeatmapData';
import { MeasurementTools } from './MeasurementTools';
import { MobileMapControls } from './MobileMapControls';
import { useIsMobile, useViewportHeight, BottomSheet, MobileCard } from '../common/MobileOptimized';
import { 
  Layers, 
  Thermometer, 
  Waves, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  BarChart3,
  Clock,
  Ruler
} from 'lucide-react';
import 'leaflet/dist/leaflet.css';

interface AdvancedMapContainerProps {
  zones: MangroveZone[];
  alerts?: DegradationAlert[];
  center?: [number, number];
  zoom?: number;
  onZoneClick?: (zoneId: string) => void;
  showThailandBoundary?: boolean;
  showProvinceBoundaries?: boolean;
}

const baseMaps = [
  {
    name: 'OpenStreetMap',
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  },
  {
    name: 'Satellite',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: '&copy; Esri',
  },
  {
    name: 'Terrain',
    url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
    attribution: '&copy; <a href="https://opentopomap.org">OpenTopoMap</a>',
  },
  {
    name: 'Light',
    url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
  },
  {
    name: 'Dark',
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
  },
];

export const AdvancedMapContainer: React.FC<AdvancedMapContainerProps> = ({
  zones,
  alerts = [],
  center = [12.57, 101.90],
  zoom = 11,
  onZoneClick,
  showThailandBoundary = true,
  showProvinceBoundaries = true,
}) => {
  const [selectedBaseMap, setSelectedBaseMap] = useState(0);
  const [showBasemapSelector, setShowBasemapSelector] = useState(false);
  const [showThailand, setShowThailand] = useState(showThailandBoundary);
  const [showProvinces, setShowProvinces] = useState(showProvinceBoundaries);
  const [visibleRegions, setVisibleRegions] = useState<string[]>(['north', 'central', 'east', 'northeast', 'south']);
  
  // Advanced layer controls
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [heatmapType, setHeatmapType] = useState<'biodiversity' | 'carbon' | 'fishery' | 'degradation'>('biodiversity');
  const [showWeatherStations, setShowWeatherStations] = useState(false);
  const [showTideGauges, setShowTideGauges] = useState(false);
  const [showAnalyticsPanel, setShowAnalyticsPanel] = useState(false);
  const [showMeasurementTools, setShowMeasurementTools] = useState(false);
  const [selectedTimeRange, setSelectedTimeRange] = useState('24h');
  
  // Mobile optimizations
  const isMobile = useIsMobile();
  const viewportHeight = useViewportHeight();
  
  // Real-time data simulation
  const [currentTime, setCurrentTime] = useState(new Date());
  
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000); // Update every minute
    
    return () => clearInterval(timer);
  }, []);

  const toggleRegion = (regionKey: string) => {
    setVisibleRegions(prev => 
      prev.includes(regionKey) 
        ? prev.filter(r => r !== regionKey)
        : [...prev, regionKey]
    );
  };

  const getRegionColor = (regionKey: string) => {
    const region = regions.find(r => r.key === regionKey);
    return region?.color || '#9CA3AF';
  };

  const getHeatmapColor = (point: HeatmapPoint) => {
    const config = heatmapConfigs[point.type];
    const opacity = point.intensity;
    return `${config.color}${Math.round(opacity * 255).toString(16).padStart(2, '0')}`;
  };

  const getTrendIcon = (trend: 'rising' | 'falling' | 'stable') => {
    switch (trend) {
      case 'rising':
        return <TrendingUp size={12} className="text-green-600" />;
      case 'falling':
        return <TrendingDown size={12} className="text-red-600" />;
      default:
        return <Minus size={12} className="text-gray-600" />;
    }
  };

  const formatTime = (timeString: string) => {
    return new Date(timeString).toLocaleTimeString('th-TH', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="h-full w-full rounded-lg overflow-hidden shadow-sm relative">
      <LeafletMap
        center={center}
        zoom={isMobile ? Math.max(zoom - 1, 8) : zoom}
        style={{ 
          height: '100%', 
          width: '100%',
          minHeight: isMobile ? `${Math.min(viewportHeight * 0.6, 500)}px` : 'auto'
        }}
        scrollWheelZoom={true}
        touchZoom={isMobile}
        doubleClickZoom={!isMobile}
        dragging={true}
        zoomControl={!isMobile}
      >
        <TileLayer
          attribution={baseMaps[selectedBaseMap].attribution}
          url={baseMaps[selectedBaseMap].url}
        />

        {/* Thailand Boundary */}
        {showThailand && (
          <Polygon
            positions={thailandBoundary}
            pathOptions={{
              fillColor: 'transparent',
              fillOpacity: 0,
              color: '#1E5F8C',
              weight: 3,
              dashArray: '8, 4',
            }}
          >
            <Tooltip permanent={zoom <= 6} direction="center">
              <span className="text-sm font-semibold text-primary">ประเทศไทย</span>
            </Tooltip>
          </Polygon>
        )}

        {/* Province Boundaries by Region */}
        {showProvinces && thailandProvinces.map((province) => {
          if (!visibleRegions.includes(province.region)) return null;
          
          return (
            <Polygon
              key={province.name}
              positions={province.coordinates}
              pathOptions={{
                fillColor: getRegionColor(province.region),
                fillOpacity: 0.4,
                color: '#FFFFFF',
                weight: 1.5,
                opacity: 0.9,
              }}
            >
              <Tooltip>
                <div className="text-xs">
                  <div className="font-semibold text-text-primary">{province.nameTh}</div>
                  <div className="text-text-secondary">{province.name}</div>
                  <div className="text-text-secondary text-xs">ภูมิภาค: {regions.find(r => r.key === province.region)?.nameTh}</div>
                </div>
              </Tooltip>
            </Polygon>
          );
        })}

        {/* Heatmap Layer */}
        {showHeatmap && getHeatmapData(heatmapType).map((point, index) => (
          <CircleMarker
            key={`heatmap-${index}`}
            center={[point.lat, point.lng]}
            radius={8 + (point.intensity * 12)}
            pathOptions={{
              fillColor: getHeatmapColor(point),
              fillOpacity: 0.6,
              color: heatmapConfigs[point.type].color,
              weight: 1,
              opacity: 0.8,
            }}
          >
            <Tooltip>
              <div className="text-xs">
                <div className="font-semibold">{heatmapConfigs[point.type].name}</div>
                <div>ค่า: {point.value} {heatmapConfigs[point.type].unit}</div>
                <div>ความเข้มข้น: {(point.intensity * 100).toFixed(0)}%</div>
                <div className="text-gray-500 text-xs mt-1">
                  อัปเดต: {formatTime(point.timestamp)}
                </div>
              </div>
            </Tooltip>
          </CircleMarker>
        ))}

        {/* Weather Stations */}
        {showWeatherStations && weatherStations.map((station) => (
          <Marker
            key={station.id}
            position={station.position}
          >
            <Popup maxWidth={isMobile ? 250 : 300}>
              <div className={`text-sm ${isMobile ? 'min-w-[200px]' : 'min-w-[200px]'}`}>
                <div className="font-semibold mb-2 flex items-center gap-2">
                  <Thermometer size={16} className="text-orange-500" />
                  {station.name}
                </div>
                <div className={`${isMobile ? 'grid grid-cols-2 gap-2' : 'space-y-1'}`}>
                  <div className="flex justify-between">
                    <span>อุณหภูมิ:</span>
                    <span className="font-medium">{station.temperature}°C</span>
                  </div>
                  <div className="flex justify-between">
                    <span>ความชื้น:</span>
                    <span className="font-medium">{station.humidity}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>ความเร็วลม:</span>
                    <span className="font-medium">{station.windSpeed} km/h</span>
                  </div>
                  <div className="flex justify-between">
                    <span>ปริมาณฝน:</span>
                    <span className="font-medium">{station.rainfall} mm</span>
                  </div>
                </div>
                <div className="text-xs text-gray-500 mt-2 border-t pt-2">
                  อัปเดตล่าสุด: {formatTime(station.lastUpdate)}
                </div>
              </div>
            </Popup>
            <Tooltip>
              <div className="text-xs">
                <div className="font-semibold">{station.name}</div>
                <div>{station.temperature}°C | {station.humidity}%</div>
              </div>
            </Tooltip>
          </Marker>
        ))}

        {/* Tide Gauges */}
        {showTideGauges && tideGauges.map((gauge) => (
          <Marker
            key={gauge.id}
            position={gauge.position}
          >
            <Popup maxWidth={isMobile ? 200 : 250}>
              <div className={`text-sm ${isMobile ? 'min-w-[160px]' : 'min-w-[180px]'}`}>
                <div className="font-semibold mb-2 flex items-center gap-2">
                  <Waves size={16} className="text-blue-500" />
                  {gauge.name}
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between items-center">
                    <span>ระดับน้ำปัจจุบัน:</span>
                    <div className="flex items-center gap-1">
                      <span className="font-medium">{gauge.currentLevel} ม.</span>
                      {getTrendIcon(gauge.trend)}
                    </div>
                  </div>
                  <div className="flex justify-between">
                    <span>น้ำขึ้นสูงสุด:</span>
                    <span className="font-medium">{gauge.nextHigh}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>น้ำลงต่ำสุด:</span>
                    <span className="font-medium">{gauge.nextLow}</span>
                  </div>
                </div>
              </div>
            </Popup>
            <Tooltip>
              <div className="text-xs">
                <div className="font-semibold">{gauge.name}</div>
                <div className="flex items-center gap-1">
                  {gauge.currentLevel} ม. {getTrendIcon(gauge.trend)}
                </div>
              </div>
            </Tooltip>
          </Marker>
        ))}

        {/* Mangrove Zones */}
        {zones.map((zone) => (
          <Polygon
            key={zone.zoneId}
            positions={zone.coordinates}
            pathOptions={{
              fillColor: getHealthFillColor(zone.healthStatus),
              fillOpacity: 0.6,
              color: getHealthColor(zone.healthStatus),
              weight: 2,
            }}
            eventHandlers={{
              click: () => onZoneClick?.(zone.zoneId),
            }}
          >
            <Tooltip>
              <div className="text-sm">
                <div className="font-semibold">{zone.zoneName}</div>
                <div>NDVI: {formatNDVI(zone.currentNDVI)}</div>
                <div>Status: {zone.healthStatus}</div>
                <div>Area: {formatArea(zone.areaRai)}</div>
              </div>
            </Tooltip>
            <Popup>
              <div className="text-sm">
                <div className="font-semibold mb-2">{zone.zoneName}</div>
                <div>NDVI: {formatNDVI(zone.currentNDVI)}</div>
                <div>Area: {formatArea(zone.areaRai)}</div>
                <button
                  onClick={() => onZoneClick?.(zone.zoneId)}
                  className="mt-2 text-primary hover:underline text-xs"
                >
                  View Details
                </button>
              </div>
            </Popup>
          </Polygon>
        ))}

        {/* Alert Markers */}
        {alerts.map((alert) => (
          <CircleMarker
            key={alert.alertId}
            center={alert.centroid}
            radius={alert.severity === 'critical' ? 12 : alert.severity === 'high' ? 10 : 8}
            pathOptions={{
              fillColor: getSeverityColor(alert.severity),
              fillOpacity: 0.7,
              color: getSeverityColor(alert.severity),
              weight: 2,
            }}
            className="animate-pulse"
          >
            <Popup>
              <div className="text-sm">
                <div className="font-semibold">{alert.zoneName}</div>
                <div>Type: {alert.alertType}</div>
                <div>Severity: {alert.severity}</div>
                <div>Delta NDVI: {alert.deltaNDVI.toFixed(2)}</div>
              </div>
            </Popup>
          </CircleMarker>
        ))}

        {/* Measurement Tools */}
        {showMeasurementTools && (
          <MeasurementTools
            onMeasurementComplete={(measurement) => {
              console.log('Measurement completed:', measurement);
            }}
          />
        )}
      </LeafletMap>

      {/* Desktop Controls */}
      <div className="hidden md:flex absolute top-4 right-4 z-[1000] flex-col gap-2">
        <button
          onClick={() => setShowBasemapSelector(!showBasemapSelector)}
          className="bg-white p-2 rounded-lg shadow-lg hover:bg-neutral-50 transition-colors"
          title="Map Controls"
        >
          <Layers size={20} className="text-text-primary" />
        </button>
        
        <button
          onClick={() => setShowAnalyticsPanel(!showAnalyticsPanel)}
          className="bg-white p-2 rounded-lg shadow-lg hover:bg-neutral-50 transition-colors"
          title="Analytics Panel"
        >
          <BarChart3 size={20} className="text-text-primary" />
        </button>
        
        <button
          onClick={() => setShowMeasurementTools(!showMeasurementTools)}
          className={`p-2 rounded-lg shadow-lg transition-colors ${
            showMeasurementTools 
              ? 'bg-primary text-white' 
              : 'bg-white hover:bg-neutral-50 text-text-primary'
          }`}
          title="Measurement Tools"
        >
          <Ruler size={20} />
        </button>
        
        {showBasemapSelector && (
          <div className="bg-white rounded-lg shadow-lg p-3 min-w-[250px] max-h-[500px] overflow-y-auto">
            <div className="text-xs font-semibold text-text-secondary px-1 py-1 mb-2">Base Map</div>
            {baseMaps.map((map, index) => (
              <button
                key={map.name}
                onClick={() => {
                  setSelectedBaseMap(index);
                }}
                className={`w-full text-left px-3 py-2 rounded text-sm transition-colors mb-1 ${
                  selectedBaseMap === index
                    ? 'bg-primary text-white'
                    : 'hover:bg-neutral-100 text-text-primary'
                }`}
              >
                {map.name}
              </button>
            ))}
            
            <div className="border-t border-neutral-200 mt-3 pt-3">
              <div className="text-xs font-semibold text-text-secondary px-1 py-1 mb-2">Boundaries</div>
              <label className="flex items-center gap-2 px-3 py-2 hover:bg-neutral-100 rounded cursor-pointer">
                <input
                  type="checkbox"
                  checked={showThailand}
                  onChange={(e) => setShowThailand(e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm text-text-primary">Thailand Border</span>
              </label>
              <label className="flex items-center gap-2 px-3 py-2 hover:bg-neutral-100 rounded cursor-pointer">
                <input
                  type="checkbox"
                  checked={showProvinces}
                  onChange={(e) => setShowProvinces(e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm text-text-primary">Provinces</span>
              </label>
            </div>

            {showProvinces && (
              <div className="border-t border-neutral-200 mt-3 pt-3">
                <div className="text-xs font-semibold text-text-secondary px-1 py-1 mb-2">Regions</div>
                {regions.map((region) => (
                  <label
                    key={region.key}
                    className="flex items-center gap-2 px-3 py-2 hover:bg-neutral-100 rounded cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={visibleRegions.includes(region.key)}
                      onChange={() => toggleRegion(region.key)}
                      className="rounded"
                    />
                    <div
                      className="w-3 h-3 rounded"
                      style={{ backgroundColor: region.color }}
                    />
                    <span className="text-sm text-text-primary">{region.nameTh}</span>
                  </label>
                ))}
              </div>
            )}

            <div className="border-t border-neutral-200 mt-3 pt-3">
              <div className="text-xs font-semibold text-text-secondary px-1 py-1 mb-2">Data Layers</div>
              
              <label className="flex items-center gap-2 px-3 py-2 hover:bg-neutral-100 rounded cursor-pointer">
                <input
                  type="checkbox"
                  checked={showHeatmap}
                  onChange={(e) => setShowHeatmap(e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm text-text-primary">Heatmap Layer</span>
              </label>

              {showHeatmap && (
                <div className="ml-6 mt-2 space-y-1">
                  {Object.entries(heatmapConfigs).map(([key, config]) => (
                    <label
                      key={key}
                      className="flex items-center gap-2 px-2 py-1 hover:bg-neutral-50 rounded cursor-pointer"
                    >
                      <input
                        type="radio"
                        name="heatmapType"
                        checked={heatmapType === key}
                        onChange={() => setHeatmapType(key as any)}
                        className="rounded"
                      />
                      <div
                        className="w-2 h-2 rounded"
                        style={{ backgroundColor: config.color }}
                      />
                      <span className="text-xs text-text-primary">{config.name}</span>
                    </label>
                  ))}
                </div>
              )}

              <label className="flex items-center gap-2 px-3 py-2 hover:bg-neutral-100 rounded cursor-pointer">
                <input
                  type="checkbox"
                  checked={showWeatherStations}
                  onChange={(e) => setShowWeatherStations(e.target.checked)}
                  className="rounded"
                />
                <Thermometer size={14} className="text-orange-500" />
                <span className="text-sm text-text-primary">Weather Stations</span>
              </label>

              <label className="flex items-center gap-2 px-3 py-2 hover:bg-neutral-100 rounded cursor-pointer">
                <input
                  type="checkbox"
                  checked={showTideGauges}
                  onChange={(e) => setShowTideGauges(e.target.checked)}
                  className="rounded"
                />
                <Waves size={14} className="text-blue-500" />
                <span className="text-sm text-text-primary">Tide Gauges</span>
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Mobile Controls */}
      <MobileMapControls
        showBasemapSelector={showBasemapSelector}
        setShowBasemapSelector={setShowBasemapSelector}
        showAnalyticsPanel={showAnalyticsPanel}
        setShowAnalyticsPanel={setShowAnalyticsPanel}
        showMeasurementTools={showMeasurementTools}
        setShowMeasurementTools={setShowMeasurementTools}
        showHeatmap={showHeatmap}
        setShowHeatmap={setShowHeatmap}
        heatmapType={heatmapType}
        setHeatmapType={setHeatmapType}
        showWeatherStations={showWeatherStations}
        setShowWeatherStations={setShowWeatherStations}
        showTideGauges={showTideGauges}
        setShowTideGauges={setShowTideGauges}
        baseMaps={baseMaps}
        selectedBaseMap={selectedBaseMap}
        setSelectedBaseMap={setSelectedBaseMap}
      />

      {/* Analytics Panel - Responsive */}
      {showAnalyticsPanel && (
        <div className={`absolute z-[1000] bg-white rounded-lg shadow-lg p-4 overflow-y-auto ${
          // Desktop positioning
          'hidden md:block top-4 left-4 min-w-[300px] max-h-[400px]'
        }`}>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-text-primary">Real-time Analytics</h3>
            <div className="flex items-center gap-1 text-xs text-text-secondary">
              <Clock size={12} />
              {currentTime.toLocaleTimeString('th-TH')}
            </div>
          </div>

          <div className="space-y-3">
            <div className="text-xs font-semibold text-text-secondary mb-2">Time Range</div>
            <div className="flex gap-1">
              {['1h', '6h', '24h', '7d'].map((range) => (
                <button
                  key={range}
                  onClick={() => setSelectedTimeRange(range)}
                  className={`px-2 py-1 text-xs rounded transition-colors ${
                    selectedTimeRange === range
                      ? 'bg-primary text-white'
                      : 'bg-neutral-100 text-text-primary hover:bg-neutral-200'
                  }`}
                >
                  {range}
                </button>
              ))}
            </div>

            {showHeatmap && (
              <div className="border-t pt-3">
                <div className="text-xs font-semibold text-text-secondary mb-2">
                  {heatmapConfigs[heatmapType].name}
                </div>
                <div className="text-xs text-text-secondary mb-2">
                  {heatmapConfigs[heatmapType].description}
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span>จำนวนจุดข้อมูล:</span>
                    <span className="font-medium">{getHeatmapData(heatmapType).length}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span>ค่าเฉลี่ย:</span>
                    <span className="font-medium">
                      {(getHeatmapData(heatmapType).reduce((sum, p) => sum + p.value, 0) / getHeatmapData(heatmapType).length).toFixed(1)} {heatmapConfigs[heatmapType].unit}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span>ค่าสูงสุด:</span>
                    <span className="font-medium">
                      {Math.max(...getHeatmapData(heatmapType).map(p => p.value))} {heatmapConfigs[heatmapType].unit}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {showWeatherStations && (
              <div className="border-t pt-3">
                <div className="text-xs font-semibold text-text-secondary mb-2">Weather Summary</div>
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span>Avg Temperature:</span>
                    <span className="font-medium">
                      {(weatherStations.reduce((sum, s) => sum + s.temperature, 0) / weatherStations.length).toFixed(1)}°C
                    </span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span>Avg Humidity:</span>
                    <span className="font-medium">
                      {(weatherStations.reduce((sum, s) => sum + s.humidity, 0) / weatherStations.length).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Mobile Analytics Panel */}
      {showAnalyticsPanel && isMobile && (
        <BottomSheet
          isOpen={showAnalyticsPanel}
          onClose={() => setShowAnalyticsPanel(false)}
          title="Real-time Analytics"
          maxHeight="60vh"
        >
          <div className="space-y-4">
            {/* Time Range Selection */}
            <div>
              <div className="text-sm font-semibold text-text-secondary mb-2">Time Range</div>
              <div className="grid grid-cols-4 gap-2">
                {['1h', '6h', '24h', '7d'].map((range) => (
                  <button
                    key={range}
                    onClick={() => setSelectedTimeRange(range)}
                    className={`px-3 py-2 text-sm rounded-lg transition-colors ${
                      selectedTimeRange === range
                        ? 'bg-primary text-white'
                        : 'bg-neutral-100 text-text-primary hover:bg-neutral-200'
                    }`}
                  >
                    {range}
                  </button>
                ))}
              </div>
            </div>

            {showHeatmap && (
              <MobileCard>
                <div className="text-sm font-semibold text-text-secondary mb-2">
                  {heatmapConfigs[heatmapType].name}
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="text-center p-3 bg-neutral-50 rounded-lg">
                    <div className="text-xs text-text-secondary">จุดข้อมูล</div>
                    <div className="text-lg font-bold text-text-primary">{getHeatmapData(heatmapType).length}</div>
                  </div>
                  <div className="text-center p-3 bg-neutral-50 rounded-lg">
                    <div className="text-xs text-text-secondary">ค่าเฉลี่ย</div>
                    <div className="text-lg font-bold text-text-primary">
                      {(getHeatmapData(heatmapType).reduce((sum, p) => sum + p.value, 0) / getHeatmapData(heatmapType).length).toFixed(1)}
                    </div>
                  </div>
                  <div className="text-center p-3 bg-neutral-50 rounded-lg">
                    <div className="text-xs text-text-secondary">ค่าต่ำสุด</div>
                    <div className="text-lg font-bold text-text-primary">
                      {Math.min(...getHeatmapData(heatmapType).map(p => p.value))}
                    </div>
                  </div>
                  <div className="text-center p-3 bg-neutral-50 rounded-lg">
                    <div className="text-xs text-text-secondary">ค่าสูงสุด</div>
                    <div className="text-lg font-bold text-text-primary">
                      {Math.max(...getHeatmapData(heatmapType).map(p => p.value))}
                    </div>
                  </div>
                </div>
              </MobileCard>
            )}

            {showWeatherStations && (
              <MobileCard>
                <div className="text-sm font-semibold text-text-secondary mb-2">Weather Summary</div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="text-center p-3 bg-orange-50 rounded-lg">
                    <div className="text-xs text-orange-600">อุณหภูมิเฉลี่ย</div>
                    <div className="text-lg font-bold text-orange-800">
                      {(weatherStations.reduce((sum, s) => sum + s.temperature, 0) / weatherStations.length).toFixed(1)}°C
                    </div>
                  </div>
                  <div className="text-center p-3 bg-blue-50 rounded-lg">
                    <div className="text-xs text-blue-600">ความชื้นเฉลี่ย</div>
                    <div className="text-lg font-bold text-blue-800">
                      {(weatherStations.reduce((sum, s) => sum + s.humidity, 0) / weatherStations.length).toFixed(0)}%
                    </div>
                  </div>
                </div>
              </MobileCard>
            )}

            {/* Data Quality */}
            <MobileCard>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-text-primary">Data Quality</div>
                  <div className="text-xs text-text-secondary">Last updated: {currentTime.toLocaleTimeString('th-TH')}</div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-green-600 font-medium">Excellent</span>
                </div>
              </div>
            </MobileCard>
          </div>
        </BottomSheet>
      )}

      {/* Enhanced Legend - Desktop */}
      <div className="hidden md:block absolute bottom-4 left-4 z-[1000] bg-white rounded-lg shadow-lg p-3 max-w-[250px]">
        <div className="text-xs font-semibold text-text-primary mb-2">Map Legend</div>
        
        <div className="space-y-2">
          <div>
            <div className="text-xs font-medium text-text-primary mb-1">Health Status</div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded" style={{ backgroundColor: '#2D7A4F' }} />
                <span className="text-xs text-text-secondary">Healthy</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded" style={{ backgroundColor: '#D69E2E' }} />
                <span className="text-xs text-text-secondary">Stressed</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded" style={{ backgroundColor: '#C53030' }} />
                <span className="text-xs text-text-secondary">Degraded</span>
              </div>
            </div>
          </div>

          {showHeatmap && (
            <div className="border-t pt-2">
              <div className="text-xs font-medium text-text-primary mb-1">
                {heatmapConfigs[heatmapType].name}
              </div>
              <div className="flex items-center gap-1">
                <span className="text-xs text-text-secondary">Low</span>
                <div className="flex-1 h-2 rounded" style={{
                  background: `linear-gradient(to right, ${heatmapConfigs[heatmapType].color}40, ${heatmapConfigs[heatmapType].color})`
                }} />
                <span className="text-xs text-text-secondary">High</span>
              </div>
            </div>
          )}

          {alerts && alerts.length > 0 && (
            <div className="border-t pt-2">
              <div className="text-xs font-medium text-text-primary mb-1">Alert Severity</div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full animate-pulse" style={{ backgroundColor: '#C53030' }} />
                  <span className="text-xs text-text-secondary">Critical</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full animate-pulse" style={{ backgroundColor: '#C05621' }} />
                  <span className="text-xs text-text-secondary">High</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full animate-pulse" style={{ backgroundColor: '#D69E2E' }} />
                  <span className="text-xs text-text-secondary">Medium</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Mobile Legend - Compact */}
      <div className="md:hidden absolute bottom-4 left-4 right-4 z-[1000] bg-white rounded-lg shadow-lg p-3">
        <div className="flex items-center justify-between mb-2">
          <div className="text-xs font-semibold text-text-primary">Legend</div>
          <div className="flex gap-1">
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded" style={{ backgroundColor: '#2D7A4F' }} />
              <span className="text-xs text-text-secondary">Healthy</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded" style={{ backgroundColor: '#D69E2E' }} />
              <span className="text-xs text-text-secondary">Stressed</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded" style={{ backgroundColor: '#C53030' }} />
              <span className="text-xs text-text-secondary">Degraded</span>
            </div>
          </div>
        </div>
        
        {showHeatmap && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-text-secondary">{heatmapConfigs[heatmapType].name}:</span>
            <div className="flex items-center gap-1 flex-1">
              <span className="text-xs text-text-secondary">Low</span>
              <div className="flex-1 h-1 rounded" style={{
                background: `linear-gradient(to right, ${heatmapConfigs[heatmapType].color}40, ${heatmapConfigs[heatmapType].color})`
              }} />
              <span className="text-xs text-text-secondary">High</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};