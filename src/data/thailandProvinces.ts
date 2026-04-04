// Thailand provinces boundaries (based on official GeoJSON data)
// Source: UNOCHA/กรมแผนที่ทหาร updated 6 November 2019
export interface Province {
  code: string;
  name: string;
  nameTh: string;
  region: string;
  coordinates: [number, number][];
}

// Import GeoJSON data and convert to our format
import thailandGeoJSON from '../../thailand.json';

const regionMapping: Record<string, string> = {
  'Amnat Charoen': 'northeast',
  'Ang Thong': 'central',
  'Bangkok Metropolis': 'central',
  'Bueng Kan': 'northeast',
  'Buri Ram': 'northeast',
  'Chachoengsao': 'central',
  'Chai Nat': 'central',
  'Chaiyaphum': 'northeast',
  'Chanthaburi': 'east',
  'Chiang Mai': 'north',
  'Chiang Rai': 'north',
  'Chon Buri': 'east',
  'Chumphon': 'south',
  'Kalasin': 'northeast',
  'Kamphaeng Phet': 'central',
  'Kanchanaburi': 'central',
  'Khon Kaen': 'northeast',
  'Krabi': 'south',
  'Lampang': 'north',
  'Lamphun': 'north',
  'Loei': 'northeast',
  'Lopburi': 'central',
  'Mae Hong Son': 'north',
  'Maha Sarakham': 'northeast',
  'Mukdahan': 'northeast',
  'Nakhon Nayok': 'central',
  'Nakhon Pathom': 'central',
  'Nakhon Phanom': 'northeast',
  'Nakhon Ratchasima': 'northeast',
  'Nakhon Sawan': 'central',
  'Nakhon Si Thammarat': 'south',
  'Nan': 'north',
  'Narathiwat': 'south',
  'Nong Bua Lam Phu': 'northeast',
  'Nong Khai': 'northeast',
  'Nonthaburi': 'central',
  'Pathum Thani': 'central',
  'Pattani': 'south',
  'Phang Nga': 'south',
  'Phatthalung': 'south',
  'Phayao': 'north',
  'Phetchabun': 'central',
  'Phetchaburi': 'central',
  'Phichit': 'central',
  'Phitsanulok': 'central',
  'Phra Nakhon Si Ayutthaya': 'central',
  'Phrae': 'north',
  'Phuket': 'south',
  'Prachin Buri': 'east',
  'Prachuap Khiri Khan': 'central',
  'Ranong': 'south',
  'Ratchaburi': 'central',
  'Rayong': 'east',
  'Roi Et': 'northeast',
  'Sa Kaeo': 'east',
  'Sakon Nakhon': 'northeast',
  'Samut Prakan': 'central',
  'Samut Sakhon': 'central',
  'Samut Songkhram': 'central',
  'Saraburi': 'central',
  'Satun': 'south',
  'Sing Buri': 'central',
  'Sisaket': 'northeast',
  'Songkhla': 'south',
  'Sukhothai': 'central',
  'Suphan Buri': 'central',
  'Surat Thani': 'south',
  'Surin': 'northeast',
  'Tak': 'north',
  'Trang': 'south',
  'Trat': 'east',
  'Ubon Ratchathani': 'northeast',
  'Udon Thani': 'northeast',
  'Uthai Thani': 'central',
  'Uttaradit': 'north',
  'Yala': 'south',
  'Yasothon': 'northeast'
};

export const thailandProvinces: Province[] = thailandGeoJSON.features.map((feature: any) => {
  const name = feature.properties.NAME_1;
  const nameTh = feature.properties.NL_NAME_1;
  const region = regionMapping[name] || 'central';
  
  // Convert coordinates from GeoJSON format (MultiPolygon or Polygon)
  let coordinates: [number, number][] = [];
  
  if (feature.geometry.type === 'Polygon') {
    // For Polygon, take the first ring (exterior boundary)
    coordinates = feature.geometry.coordinates[0].map((coord: number[]) => [coord[1], coord[0]] as [number, number]);
  } else if (feature.geometry.type === 'MultiPolygon') {
    // For MultiPolygon, take the first polygon's first ring
    coordinates = feature.geometry.coordinates[0][0].map((coord: number[]) => [coord[1], coord[0]] as [number, number]);
  }
  
  return {
    code: `TH${feature.properties.ID_1.toString().padStart(2, '0')}`,
    name,
    nameTh,
    region,
    coordinates
  };
});

// Get provinces by region
export const getProvincesByRegion = (region: string) => {
  return thailandProvinces.filter(province => province.region === region);
};

// Get all regions with colors
export const regions = [
  { key: 'north', name: 'Northern', nameTh: 'ภาคเหนือ', color: '#A855F7' },
  { key: 'central', name: 'Central', nameTh: 'ภาคกลาง', color: '#06B6D4' },
  { key: 'east', name: 'Eastern', nameTh: 'ภาคตะวันออก', color: '#10B981' },
  { key: 'northeast', name: 'Northeastern', nameTh: 'ภาคตะวันออกเฉียงเหนือ', color: '#F59E0B' },
  { key: 'south', name: 'Southern', nameTh: 'ภาคใต้', color: '#EF4444' },
];