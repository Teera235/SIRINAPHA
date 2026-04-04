import { CatchLog } from '@/types';

const fisherNames = [
  'Somchai Thongchai', 'Niran Pattana', 'Wichai Saengchai', 'Apinya Rattana',
  'Surasak Boonmee', 'Prasert Chaiwong', 'Manop Srisuk', 'Chalerm Pongpan',
  'Anan Thepsiri', 'Boonlert Kaewkam'
];

const gearTypes = ['Gill Net', 'Crab Trap', 'Cast Net', 'Long Line', 'Hand Line'];

const species = [
  'Pla Kapong Khao',
  'Kung Kula Dam',
  'Pu Ma',
  'Pla Kraphong Daeng',
  'Pla Muek'
];

const generateCatchLog = (index: number): CatchLog => {
  const daysAgo = Math.floor(Math.random() * 180);
  const date = new Date();
  date.setDate(date.getDate() - daysAgo);
  
  const totalWeight = 5 + Math.random() * 40;
  const fuelCost = 400 + Math.random() * 800;
  const revenue = totalWeight * (80 + Math.random() * 60);
  
  const numSpecies = 2 + Math.floor(Math.random() * 3);
  const composition = [];
  let remainingWeight = totalWeight;
  
  for (let i = 0; i < numSpecies - 1; i++) {
    const weight = remainingWeight * (0.2 + Math.random() * 0.4);
    composition.push({
      species: species[i % species.length],
      weightKg: parseFloat(weight.toFixed(2))
    });
    remainingWeight -= weight;
  }
  composition.push({
    species: species[(numSpecies - 1) % species.length],
    weightKg: parseFloat(remainingWeight.toFixed(2))
  });
  
  return {
    logId: `catch-${String(index + 1).padStart(3, '0')}`,
    fisherName: fisherNames[index % fisherNames.length],
    tripDate: date.toISOString().split('T')[0],
    fishingLocation: [
      12.50 + Math.random() * 0.10,
      101.88 + Math.random() * 0.05
    ] as [number, number],
    totalWeightKg: parseFloat(totalWeight.toFixed(2)),
    fuelCostBaht: Math.round(fuelCost),
    estimatedRevenueBaht: Math.round(revenue),
    gearType: gearTypes[Math.floor(Math.random() * gearTypes.length)],
    speciesComposition: composition,
    usedFSIRecommendation: Math.random() > 0.4,
  };
};

export const mockCatchLogs: CatchLog[] = Array.from({ length: 50 }, (_, i) => generateCatchLog(i));
