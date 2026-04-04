import React, { useState } from 'react';
import { Polyline, Polygon, Popup, useMapEvents } from 'react-leaflet';
import { Ruler, Square, Trash2 } from 'lucide-react';

interface MeasurementPoint {
  lat: number;
  lng: number;
}

interface Measurement {
  id: string;
  type: 'distance' | 'area';
  points: MeasurementPoint[];
  value: number;
  unit: string;
  label?: string;
}

interface MeasurementToolsProps {
  onMeasurementComplete?: (measurement: Measurement) => void;
}

export const MeasurementTools: React.FC<MeasurementToolsProps> = ({
  onMeasurementComplete
}) => {
  const [isActive, setIsActive] = useState(false);
  const [measurementType, setMeasurementType] = useState<'distance' | 'area'>('distance');
  const [currentPoints, setCurrentPoints] = useState<MeasurementPoint[]>([]);
  const [measurements, setMeasurements] = useState<Measurement[]>([]);
  const [isDrawing, setIsDrawing] = useState(false);

  // Calculate distance between two points using Haversine formula
  const calculateDistance = (point1: MeasurementPoint, point2: MeasurementPoint): number => {
    const R = 6371000; // Earth's radius in meters
    const lat1Rad = (point1.lat * Math.PI) / 180;
    const lat2Rad = (point2.lat * Math.PI) / 180;
    const deltaLatRad = ((point2.lat - point1.lat) * Math.PI) / 180;
    const deltaLngRad = ((point2.lng - point1.lng) * Math.PI) / 180;

    const a = Math.sin(deltaLatRad / 2) * Math.sin(deltaLatRad / 2) +
              Math.cos(lat1Rad) * Math.cos(lat2Rad) *
              Math.sin(deltaLngRad / 2) * Math.sin(deltaLngRad / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c;
  };

  // Calculate total distance for a polyline
  const calculateTotalDistance = (points: MeasurementPoint[]): number => {
    if (points.length < 2) return 0;
    
    let totalDistance = 0;
    for (let i = 0; i < points.length - 1; i++) {
      totalDistance += calculateDistance(points[i], points[i + 1]);
    }
    return totalDistance;
  };

  // Calculate area using Shoelace formula (approximate for small areas)
  const calculateArea = (points: MeasurementPoint[]): number => {
    if (points.length < 3) return 0;

    let area = 0;
    const n = points.length;
    
    for (let i = 0; i < n; i++) {
      const j = (i + 1) % n;
      area += points[i].lat * points[j].lng;
      area -= points[j].lat * points[i].lng;
    }
    
    area = Math.abs(area) / 2;
    
    // Convert to square meters (approximate)
    const metersPerDegree = 111320; // at equator
    return area * metersPerDegree * metersPerDegree;
  };

  // Format measurement value with appropriate units
  const formatMeasurement = (value: number, type: 'distance' | 'area'): { value: number; unit: string } => {
    if (type === 'distance') {
      if (value < 1000) {
        return { value: Math.round(value), unit: 'm' };
      } else if (value < 10000) {
        return { value: Math.round(value / 100) / 10, unit: 'km' };
      } else {
        return { value: Math.round(value / 1000), unit: 'km' };
      }
    } else {
      // Area
      if (value < 10000) {
        return { value: Math.round(value), unit: 'm²' };
      } else if (value < 1000000) {
        return { value: Math.round(value / 100) / 10, unit: 'ha' };
      } else {
        return { value: Math.round(value / 100000) / 10, unit: 'km²' };
      }
    }
  };

  useMapEvents({
    click: (e) => {
      if (!isActive || !isDrawing) return;

      const newPoint: MeasurementPoint = {
        lat: e.latlng.lat,
        lng: e.latlng.lng
      };

      setCurrentPoints(prev => [...prev, newPoint]);
    },
    dblclick: () => {
      if (!isActive || !isDrawing || currentPoints.length < 2) return;

      // Complete the measurement
      const finalPoints = [...currentPoints];
      let value: number;
      
      if (measurementType === 'distance') {
        value = calculateTotalDistance(finalPoints);
      } else {
        value = calculateArea(finalPoints);
      }

      const formatted = formatMeasurement(value, measurementType);
      const newMeasurement: Measurement = {
        id: Date.now().toString(),
        type: measurementType,
        points: finalPoints,
        value: formatted.value,
        unit: formatted.unit
      };

      setMeasurements(prev => [...prev, newMeasurement]);
      setCurrentPoints([]);
      setIsDrawing(false);
      
      if (onMeasurementComplete) {
        onMeasurementComplete(newMeasurement);
      }
    }
  });

  const startMeasurement = (type: 'distance' | 'area') => {
    setMeasurementType(type);
    setIsActive(true);
    setIsDrawing(true);
    setCurrentPoints([]);
  };

  const cancelMeasurement = () => {
    setIsActive(false);
    setIsDrawing(false);
    setCurrentPoints([]);
  };

  const clearAllMeasurements = () => {
    setMeasurements([]);
    cancelMeasurement();
  };

  const deleteMeasurement = (id: string) => {
    setMeasurements(prev => prev.filter(m => m.id !== id));
  };

  return (
    <>
      {/* Measurement Controls */}
      <div className="absolute top-20 right-4 z-[1000] bg-white rounded-lg shadow-lg p-3 min-w-[200px]">
        <div className="text-xs font-semibold text-text-secondary mb-2">Measurement Tools</div>
        
        <div className="space-y-2">
          <button
            onClick={() => startMeasurement('distance')}
            disabled={isDrawing}
            className={`w-full flex items-center gap-2 px-3 py-2 rounded text-sm transition-colors ${
              isActive && measurementType === 'distance'
                ? 'bg-primary text-white'
                : 'bg-neutral-100 hover:bg-neutral-200 text-text-primary'
            } ${isDrawing ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <Ruler size={16} />
            Measure Distance
          </button>
          
          <button
            onClick={() => startMeasurement('area')}
            disabled={isDrawing}
            className={`w-full flex items-center gap-2 px-3 py-2 rounded text-sm transition-colors ${
              isActive && measurementType === 'area'
                ? 'bg-primary text-white'
                : 'bg-neutral-100 hover:bg-neutral-200 text-text-primary'
            } ${isDrawing ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <Square size={16} />
            Measure Area
          </button>
          
          {isDrawing && (
            <button
              onClick={cancelMeasurement}
              className="w-full flex items-center gap-2 px-3 py-2 rounded text-sm bg-red-100 hover:bg-red-200 text-red-700"
            >
              <Trash2 size={16} />
              Cancel
            </button>
          )}
          
          {measurements.length > 0 && (
            <button
              onClick={clearAllMeasurements}
              className="w-full flex items-center gap-2 px-3 py-2 rounded text-sm bg-red-100 hover:bg-red-200 text-red-700"
            >
              <Trash2 size={16} />
              Clear All
            </button>
          )}
        </div>

        {isDrawing && (
          <div className="mt-3 pt-3 border-t border-neutral-200">
            <div className="text-xs text-text-secondary">
              {measurementType === 'distance' 
                ? 'Click to add points, double-click to finish'
                : 'Click to add vertices, double-click to close polygon'
              }
            </div>
            {currentPoints.length > 0 && (
              <div className="text-xs text-text-primary mt-1">
                Points: {currentPoints.length}
                {currentPoints.length > 1 && measurementType === 'distance' && (
                  <div>
                    Current: {formatMeasurement(calculateTotalDistance(currentPoints), 'distance').value} {formatMeasurement(calculateTotalDistance(currentPoints), 'distance').unit}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {measurements.length > 0 && (
          <div className="mt-3 pt-3 border-t border-neutral-200">
            <div className="text-xs font-semibold text-text-secondary mb-2">Measurements</div>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {measurements.map((measurement) => (
                <div key={measurement.id} className="flex items-center justify-between text-xs">
                  <span className="text-text-primary">
                    {measurement.type === 'distance' ? '📏' : '📐'} {measurement.value} {measurement.unit}
                  </span>
                  <button
                    onClick={() => deleteMeasurement(measurement.id)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Current measurement preview */}
      {isDrawing && currentPoints.length > 1 && (
        <>
          {measurementType === 'distance' ? (
            <Polyline
              positions={currentPoints.map(p => [p.lat, p.lng])}
              pathOptions={{
                color: '#3B82F6',
                weight: 3,
                dashArray: '5, 5',
                opacity: 0.8
              }}
            >
              <Popup>
                <div className="text-sm">
                  <div className="font-semibold">Distance Measurement</div>
                  <div>
                    {formatMeasurement(calculateTotalDistance(currentPoints), 'distance').value} {formatMeasurement(calculateTotalDistance(currentPoints), 'distance').unit}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Double-click to finish
                  </div>
                </div>
              </Popup>
            </Polyline>
          ) : (
            currentPoints.length > 2 && (
              <Polygon
                positions={currentPoints.map(p => [p.lat, p.lng])}
                pathOptions={{
                  color: '#10B981',
                  weight: 2,
                  fillColor: '#10B981',
                  fillOpacity: 0.2,
                  dashArray: '5, 5'
                }}
              >
                <Popup>
                  <div className="text-sm">
                    <div className="font-semibold">Area Measurement</div>
                    <div>
                      {formatMeasurement(calculateArea(currentPoints), 'area').value} {formatMeasurement(calculateArea(currentPoints), 'area').unit}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      Double-click to finish
                    </div>
                  </div>
                </Popup>
              </Polygon>
            )
          )}
        </>
      )}

      {/* Completed measurements */}
      {measurements.map((measurement) => (
        <React.Fragment key={measurement.id}>
          {measurement.type === 'distance' ? (
            <Polyline
              positions={measurement.points.map(p => [p.lat, p.lng])}
              pathOptions={{
                color: '#3B82F6',
                weight: 3,
                opacity: 0.8
              }}
            >
              <Popup>
                <div className="text-sm">
                  <div className="font-semibold">Distance</div>
                  <div>{measurement.value} {measurement.unit}</div>
                  <button
                    onClick={() => deleteMeasurement(measurement.id)}
                    className="mt-2 text-red-500 hover:text-red-700 text-xs"
                  >
                    Delete measurement
                  </button>
                </div>
              </Popup>
            </Polyline>
          ) : (
            <Polygon
              positions={measurement.points.map(p => [p.lat, p.lng])}
              pathOptions={{
                color: '#10B981',
                weight: 2,
                fillColor: '#10B981',
                fillOpacity: 0.2
              }}
            >
              <Popup>
                <div className="text-sm">
                  <div className="font-semibold">Area</div>
                  <div>{measurement.value} {measurement.unit}</div>
                  <button
                    onClick={() => deleteMeasurement(measurement.id)}
                    className="mt-2 text-red-500 hover:text-red-700 text-xs"
                  >
                    Delete measurement
                  </button>
                </div>
              </Popup>
            </Polygon>
          )}
        </React.Fragment>
      ))}
    </>
  );
};