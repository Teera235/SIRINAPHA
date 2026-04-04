import React, { useState } from 'react';
import { MapContainer as LeafletMap, TileLayer, Polygon, CircleMarker, Popup, Tooltip } from 'react-leaflet';
import { MangroveZone, DegradationAlert } from '@/types';
import { getHealthColor, getHealthFillColor, getSeverityColor } from '@/utils/colorScales';
import { formatArea, formatNDVI } from '@/utils/formatters';
import { thailandBoundary } from '@/data/thailandBoundary';
import { thailandProvinces, regions } from '@/data/thailandProvinces';
import { Layers } from 'lucide-react';
import 'leaflet/dist/leaflet.css';

interface MapContainerProps {
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
];

export const MapContainer: React.FC<MapContainerProps> = ({
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

  return (
    <div className="h-full w-full rounded-lg overflow-hidden shadow-sm relative">
      <LeafletMap
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
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
      </LeafletMap>

      {/* Layer Control */}
      <div className="absolute top-4 right-4 z-[1000] flex flex-col gap-2">
        <button
          onClick={() => setShowBasemapSelector(!showBasemapSelector)}
          className="bg-white p-2 rounded-lg shadow-lg hover:bg-neutral-50 transition-colors"
          title="Map Controls"
        >
          <Layers size={20} className="text-text-primary" />
        </button>
        
        {showBasemapSelector && (
          <div className="bg-white rounded-lg shadow-lg p-3 min-w-[200px] max-h-[400px] overflow-y-auto">
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
          </div>
        )}
      </div>

      {/* Map Legend */}
      <div className="absolute bottom-4 left-4 z-[1000] bg-white rounded-lg shadow-lg p-3">
        <div className="text-xs font-semibold text-text-primary mb-2">Health Status</div>
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
        {alerts && alerts.length > 0 && (
          <>
            <div className="text-xs font-semibold text-text-primary mt-3 mb-2">Alert Severity</div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#C53030' }} />
                <span className="text-xs text-text-secondary">Critical</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#C05621' }} />
                <span className="text-xs text-text-secondary">High</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#D69E2E' }} />
                <span className="text-xs text-text-secondary">Medium</span>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
