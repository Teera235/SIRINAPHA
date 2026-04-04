import React, { useState } from 'react';
import { 
  Layers, 
  BarChart3, 
  Ruler, 
  Menu,
  Thermometer,
  Waves,
  Leaf,
  Factory,
  Fish,
  AlertTriangle
} from 'lucide-react';
import { BottomSheet, CollapsibleSection, TouchButton, useIsMobile } from '../common/MobileOptimized';

interface MobileMapControlsProps {
  showBasemapSelector: boolean;
  setShowBasemapSelector: (show: boolean) => void;
  showAnalyticsPanel: boolean;
  setShowAnalyticsPanel: (show: boolean) => void;
  showMeasurementTools: boolean;
  setShowMeasurementTools: (show: boolean) => void;
  showHeatmap: boolean;
  setShowHeatmap: (show: boolean) => void;
  heatmapType: 'biodiversity' | 'carbon' | 'fishery' | 'degradation';
  setHeatmapType: (type: 'biodiversity' | 'carbon' | 'fishery' | 'degradation') => void;
  showWeatherStations: boolean;
  setShowWeatherStations: (show: boolean) => void;
  showTideGauges: boolean;
  setShowTideGauges: (show: boolean) => void;
  baseMaps: any[];
  selectedBaseMap: number;
  setSelectedBaseMap: (index: number) => void;
}

export const MobileMapControls: React.FC<MobileMapControlsProps> = ({
  showBasemapSelector,
  setShowBasemapSelector,
  showAnalyticsPanel,
  setShowAnalyticsPanel,
  showMeasurementTools,
  setShowMeasurementTools,
  showHeatmap,
  setShowHeatmap,
  heatmapType,
  setHeatmapType,
  showWeatherStations,
  setShowWeatherStations,
  showTideGauges,
  setShowTideGauges,
  baseMaps,
  selectedBaseMap,
  setSelectedBaseMap
}) => {
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const isMobile = useIsMobile();

  const heatmapConfigs = {
    biodiversity: { name: 'ความหลากหลายทางชีวภาพ', icon: Leaf, color: '#10B981' },
    carbon: { name: 'การกักเก็บคาร์บอน', icon: Factory, color: '#059669' },
    fishery: { name: 'กิจกรรมการประมง', icon: Fish, color: '#0EA5E9' },
    degradation: { name: 'ความเสี่ยงการเสื่อมโทรม', icon: AlertTriangle, color: '#EF4444' }
  };

  if (!isMobile) return null;

  return (
    <>
      {/* Mobile Control Button - Larger and more accessible */}
      <div className="fixed bottom-6 right-6 z-[1000]">
        <TouchButton
          onClick={() => setShowMobileMenu(!showMobileMenu)}
          variant="primary"
          size="lg"
          className="w-14 h-14 rounded-full shadow-2xl"
        >
          <Menu size={24} />
        </TouchButton>
      </div>

      {/* Mobile Menu Bottom Sheet */}
      <BottomSheet
        isOpen={showMobileMenu}
        onClose={() => setShowMobileMenu(false)}
        title="Map Controls"
        maxHeight="80vh"
      >
        <div className="space-y-4">
          {/* Quick Actions - Improved touch targets */}
          <div className="grid grid-cols-3 gap-3">
            <TouchButton
              onClick={() => {
                setShowBasemapSelector(!showBasemapSelector);
                setShowMobileMenu(false);
              }}
              variant={showBasemapSelector ? 'primary' : 'secondary'}
              size="lg"
              className="flex-col gap-2"
            >
              <Layers size={24} />
              <span className="text-xs">Layers</span>
            </TouchButton>
            
            <TouchButton
              onClick={() => {
                setShowAnalyticsPanel(!showAnalyticsPanel);
                setShowMobileMenu(false);
              }}
              variant={showAnalyticsPanel ? 'primary' : 'secondary'}
              size="lg"
              className="flex-col gap-2"
            >
              <BarChart3 size={24} />
              <span className="text-xs">Analytics</span>
            </TouchButton>
            
            <TouchButton
              onClick={() => {
                setShowMeasurementTools(!showMeasurementTools);
                setShowMobileMenu(false);
              }}
              variant={showMeasurementTools ? 'primary' : 'secondary'}
              size="lg"
              className="flex-col gap-2"
            >
              <Ruler size={24} />
              <span className="text-xs">Measure</span>
            </TouchButton>
          </div>

          {/* Base Maps Section */}
          <CollapsibleSection 
            title="Base Maps" 
            icon={<Layers size={16} />}
            defaultOpen={false}
          >
            <div className="grid grid-cols-1 gap-2">
              {baseMaps.map((map, index) => (
                <TouchButton
                  key={map.name}
                  onClick={() => {
                    setSelectedBaseMap(index);
                    setShowMobileMenu(false);
                  }}
                  variant={selectedBaseMap === index ? 'primary' : 'outline'}
                  size="md"
                  className="justify-start"
                >
                  {map.name}
                </TouchButton>
              ))}
            </div>
          </CollapsibleSection>

          {/* Data Layers Section */}
          <CollapsibleSection 
            title="Data Layers" 
            icon={<BarChart3 size={16} />}
            defaultOpen={true}
          >
            <div className="space-y-4">
              {/* Heatmap Toggle */}
              <div className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg">
                <span className="font-medium text-text-primary">Heatmap Layer</span>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showHeatmap}
                    onChange={(e) => setShowHeatmap(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              {/* Heatmap Type Selection */}
              {showHeatmap && (
                <div className="space-y-2">
                  <div className="text-sm font-medium text-text-secondary mb-2">Select Heatmap Type:</div>
                  {Object.entries(heatmapConfigs).map(([key, config]) => {
                    const IconComponent = config.icon;
                    return (
                      <TouchButton
                        key={key}
                        onClick={() => setHeatmapType(key as any)}
                        variant={heatmapType === key ? 'primary' : 'outline'}
                        size="md"
                        className="justify-start gap-3"
                      >
                        <IconComponent size={20} style={{ color: heatmapType === key ? 'white' : config.color }} />
                        <span>{config.name}</span>
                      </TouchButton>
                    );
                  })}
                </div>
              )}

              {/* Environmental Monitoring */}
              <div className="space-y-2">
                <div className="text-sm font-medium text-text-secondary mb-2">Environmental Monitoring:</div>
                
                <div className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Thermometer size={16} className="text-orange-500" />
                    <span className="text-sm text-text-primary">Weather Stations</span>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={showWeatherStations}
                      onChange={(e) => setShowWeatherStations(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Waves size={16} className="text-blue-500" />
                    <span className="text-sm text-text-primary">Tide Gauges</span>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={showTideGauges}
                      onChange={(e) => setShowTideGauges(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>
            </div>
          </CollapsibleSection>

          {/* Measurement Tools Section */}
          {showMeasurementTools && (
            <CollapsibleSection 
              title="Measurement Tools" 
              icon={<Ruler size={16} />}
              defaultOpen={true}
            >
              <div className="space-y-3">
                <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="text-sm font-medium text-blue-800 mb-1">How to use:</div>
                  <div className="text-xs text-blue-600">
                    • Distance: Tap points on map, double-tap to finish<br/>
                    • Area: Tap to create polygon, double-tap to close
                  </div>
                </div>
                
                <TouchButton
                  onClick={() => setShowMobileMenu(false)}
                  variant="primary"
                  size="md"
                  className="w-full"
                >
                  Start Measuring on Map
                </TouchButton>
              </div>
            </CollapsibleSection>
          )}
        </div>
      </BottomSheet>
    </>
  );
};