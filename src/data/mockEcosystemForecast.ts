import { EcosystemForecast } from '@/types';

const generateForecast = (): EcosystemForecast[] => {
  const forecasts: EcosystemForecast[] = [];
  const startDate = new Date('2024-04-04');
  const baseCPUE = 18.5;
  
  for (let i = 0; i < 90; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);
    
    const seasonalFactor = 1 + 0.15 * Math.sin((i / 90) * Math.PI);
    const trendFactor = 1 + (i / 90) * 0.12;
    const noise = (Math.random() - 0.5) * 0.08;
    
    const predictedCPUE = baseCPUE * seasonalFactor * trendFactor * (1 + noise);
    const uncertainty = 1.5 + (i / 90) * 2.5;
    
    const ndviBase = 0.64;
    const ndviTrend = 0.04 * (i / 90);
    const ndviSeasonal = 0.03 * Math.sin((i / 90) * Math.PI);
    
    forecasts.push({
      date: date.toISOString().split('T')[0],
      predictedCPUE: parseFloat(predictedCPUE.toFixed(2)),
      lowerBound: parseFloat((predictedCPUE - uncertainty).toFixed(2)),
      upperBound: parseFloat((predictedCPUE + uncertainty).toFixed(2)),
      ndviValue: parseFloat((ndviBase + ndviTrend + ndviSeasonal).toFixed(4)),
    });
  }
  
  return forecasts;
};

export const mockEcosystemForecast: EcosystemForecast[] = generateForecast();
