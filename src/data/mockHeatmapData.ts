// Mock data for heatmap visualization
export interface HeatmapPoint {
  lat: number;
  lng: number;
  intensity: number;
  type: 'biodiversity' | 'carbon' | 'fishery' | 'degradation';
  value: number;
  timestamp: string;
}

export interface WeatherStation {
  id: string;
  name: string;
  position: [number, number];
  temperature: number;
  humidity: number;
  windSpeed: number;
  rainfall: number;
  lastUpdate: string;
}

export interface TideGauge {
  id: string;
  name: string;
  position: [number, number];
  currentLevel: number;
  trend: 'rising' | 'falling' | 'stable';
  nextHigh: string;
  nextLow: string;
}

// Biodiversity hotspots around Kung Krabaen Bay
export const biodiversityHeatmap: HeatmapPoint[] = [
  { lat: 12.5720, lng: 101.9050, intensity: 0.9, type: 'biodiversity', value: 85, timestamp: '2024-04-05T10:00:00Z' },
  { lat: 12.5680, lng: 101.9020, intensity: 0.8, type: 'biodiversity', value: 78, timestamp: '2024-04-05T10:00:00Z' },
  { lat: 12.5750, lng: 101.9080, intensity: 0.7, type: 'biodiversity', value: 72, timestamp: '2024-04-05T10:00:00Z' },
  { lat: 12.5650, lng: 101.8980, intensity: 0.6, type: 'biodiversity', value: 65, timestamp: '2024-04-05T10:00:00Z' },
  { lat: 12.5800, lng: 101.9120, intensity: 0.8, type: 'biodiversity', value: 80, timestamp: '2024-04-05T10:00:00Z' },
  { lat: 12.5600, lng: 101.8950, intensity: 0.5, type: 'biodiversity', value: 58, timestamp: '2024-04-05T10:00:00Z' },
  { lat: 12.5780, lng: 101.9100, intensity: 0.9, type: 'biodiversity', value: 88, timestamp: '2024-04-05T10:00:00Z' },
  { lat: 12.5620, lng: 101.8970, intensity: 0.4, type: 'biodiversity', value: 45, timestamp: '2024-04-05T10:00:00Z' },
];

// Carbon sequestration data
export const carbonHeatmap: HeatmapPoint[] = [
  { lat: 12.5710, lng: 101.9040, intensity: 0.8, type: 'carbon', value: 12.5, timestamp: '2024-04-05T10:00:00Z' },
  { lat: 12.5670, lng: 101.9010, intensity: 0.7, type: 'carbon', value: 10.8, timestamp: '2024-04-05T10:00:00Z' },
  { lat: 12.5740, lng: 101.9070, intensity: 0.9, type: 'carbon', value: 14.2, timestamp: '2024-04-05T10:00:00Z' },
  { lat: 12.5640, lng: 101.8990, intensity: 0.6, type: 'carbon', value: 9.3, timestamp: '2024-04-05T10:00:00Z' },
  { lat: 12.5790, lng: 101.9110, intensity: 0.8, type: 'carbon', value: 13.1, timestamp: '2024-04-05T10:00:00Z' },
  { lat: 12.5590, lng: 101.8940, intensity: 0.5, type: 'carbon', value: 7.6, timestamp: '2024-04-05T10:00:00Z' },
];

// Fishery activity hotspots
export const fisheryHeatmap: HeatmapPoint[] = [
  { lat: 12.5700, lng: 101.9030, intensity: 0.7, type: 'fishery', value: 45, timestamp: '2024-04-05T10:00:00Z' },
  { lat: 12.5660, lng: 101.9000, intensity: 0.8, type: 'fishery', value: 52, timestamp: '2024-04-05T10:00:00Z' },
  { lat: 12.5730, lng: 101.9060, intensity: 0.6, type: 'fishery', value: 38, timestamp: '2024-04-05T10:00:00Z' },
  { lat: 12.5630, lng: 101.8980, intensity: 0.9, type: 'fishery', value: 61, timestamp: '2024-04-05T10:00:00Z' },
  { lat: 12.5770, lng: 101.9090, intensity: 0.5, type: 'fishery', value: 32, timestamp: '2024-04-05T10:00:00Z' },
];

// Environmental degradation risk areas
export const degradationHeatmap: HeatmapPoint[] = [
  { lat: 12.5690, lng: 101.9020, intensity: 0.6, type: 'degradation', value: 35, timestamp: '2024-04-05T10:00:00Z' },
  { lat: 12.5650, lng: 101.8990, intensity: 0.8, type: 'degradation', value: 48, timestamp: '2024-04-05T10:00:00Z' },
  { lat: 12.5720, lng: 101.9050, intensity: 0.4, type: 'degradation', value: 22, timestamp: '2024-04-05T10:00:00Z' },
  { lat: 12.5610, lng: 101.8960, intensity: 0.9, type: 'degradation', value: 55, timestamp: '2024-04-05T10:00:00Z' },
  { lat: 12.5760, lng: 101.9080, intensity: 0.3, type: 'degradation', value: 18, timestamp: '2024-04-05T10:00:00Z' },
];

// Weather monitoring stations
export const weatherStations: WeatherStation[] = [
  {
    id: 'WS001',
    name: 'Kung Krabaen Central',
    position: [12.5720, 101.9050],
    temperature: 28.5,
    humidity: 78,
    windSpeed: 12.3,
    rainfall: 2.4,
    lastUpdate: '2024-04-05T10:30:00Z'
  },
  {
    id: 'WS002',
    name: 'Chanthaburi Coast',
    position: [12.5650, 101.8980],
    temperature: 29.1,
    humidity: 82,
    windSpeed: 15.7,
    rainfall: 0.8,
    lastUpdate: '2024-04-05T10:30:00Z'
  },
  {
    id: 'WS003',
    name: 'Mangrove North',
    position: [12.5800, 101.9120],
    temperature: 27.8,
    humidity: 85,
    windSpeed: 8.9,
    rainfall: 4.1,
    lastUpdate: '2024-04-05T10:30:00Z'
  }
];

// Tide monitoring stations
export const tideGauges: TideGauge[] = [
  {
    id: 'TG001',
    name: 'Kung Krabaen Bay',
    position: [12.5700, 101.9030],
    currentLevel: 1.8,
    trend: 'rising',
    nextHigh: '14:25',
    nextLow: '20:45'
  },
  {
    id: 'TG002',
    name: 'Chanthaburi Port',
    position: [12.5630, 101.8970],
    currentLevel: 1.6,
    trend: 'falling',
    nextHigh: '14:30',
    nextLow: '20:50'
  }
];

// Get heatmap data by type
export const getHeatmapData = (type: 'biodiversity' | 'carbon' | 'fishery' | 'degradation') => {
  switch (type) {
    case 'biodiversity':
      return biodiversityHeatmap;
    case 'carbon':
      return carbonHeatmap;
    case 'fishery':
      return fisheryHeatmap;
    case 'degradation':
      return degradationHeatmap;
    default:
      return [];
  }
};

// Heatmap layer configurations
export const heatmapConfigs = {
  biodiversity: {
    name: 'ความหลากหลายทางชีวภาพ',
    nameEn: 'Biodiversity Index',
    color: '#10B981',
    unit: 'ดัชนี',
    description: 'ดัชนีความหลากหลายทางชีวภาพในพื้นที่ป่าชายเลน'
  },
  carbon: {
    name: 'การกักเก็บคาร์บอน',
    nameEn: 'Carbon Sequestration',
    color: '#059669',
    unit: 'ตัน CO₂/ไร่/ปี',
    description: 'อัตราการกักเก็บคาร์บอนของป่าชายเลน'
  },
  fishery: {
    name: 'กิจกรรมการประมง',
    nameEn: 'Fishery Activity',
    color: '#0EA5E9',
    unit: 'เรือ/วัน',
    description: 'ความหนาแน่นของกิจกรรมการประมงในพื้นที่'
  },
  degradation: {
    name: 'ความเสี่ยงการเสื่อมโทรม',
    nameEn: 'Degradation Risk',
    color: '#EF4444',
    unit: 'ระดับความเสี่ยง',
    description: 'ความเสี่ยงการเสื่อมโทรมของระบบนิเวศ'
  }
};