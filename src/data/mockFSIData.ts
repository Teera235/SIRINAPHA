import { FSIPoint } from '@/types';

const generateFSIGrid = (): FSIPoint[] => {
  const points: FSIPoint[] = [];
  const latStart = 12.50;
  const latEnd = 12.60;
  const lngStart = 101.88;
  const lngEnd = 101.93;
  const gridSize = 0.01;
  
  for (let lat = latStart; lat <= latEnd; lat += gridSize) {
    for (let lng = lngStart; lng <= lngEnd; lng += gridSize) {
      const distanceToMangrove = Math.min(
        Math.sqrt(Math.pow(lat - 12.5798, 2) + Math.pow(lng - 101.8985, 2)),
        Math.sqrt(Math.pow(lat - 12.5638, 2) + Math.pow(lng - 101.9125, 2))
      );
      
      const proximityBonus = Math.max(0, 0.4 - distanceToMangrove * 10);
      const baseFSI = 0.3 + Math.random() * 0.4;
      const fsiScore = Math.min(0.95, baseFSI + proximityBonus + (Math.random() - 0.5) * 0.2);
      
      const sst = 0.20 + Math.random() * 0.15;
      const chlorophyllA = 0.15 + Math.random() * 0.20;
      const ndviProximity = proximityBonus + 0.15 + Math.random() * 0.10;
      const seasonality = 0.25 + Math.random() * 0.15;
      
      const total = sst + chlorophyllA + ndviProximity + seasonality;
      
      points.push({
        lat: parseFloat(lat.toFixed(4)),
        lng: parseFloat(lng.toFixed(4)),
        fsiScore: parseFloat(fsiScore.toFixed(3)),
        confidence: parseFloat((0.65 + Math.random() * 0.30).toFixed(2)),
        predictionDate: '2024-04-04',
        contributingFactors: {
          sst: parseFloat((sst / total).toFixed(3)),
          chlorophyllA: parseFloat((chlorophyllA / total).toFixed(3)),
          ndviProximity: parseFloat((ndviProximity / total).toFixed(3)),
          seasonality: parseFloat((seasonality / total).toFixed(3)),
        },
      });
    }
  }
  
  return points;
};

export const mockFSIData: FSIPoint[] = generateFSIGrid();
