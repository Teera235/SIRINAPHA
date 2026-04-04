# Setup Instructions

## Prerequisites

- Node.js 18+ installed
- npm or yarn package manager

## Installation Steps

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser and navigate to the URL shown in the terminal (typically http://localhost:5173)

## What to Expect

The dashboard will load with:
- 8 mangrove zones around Kung Krabaen Bay, Chanthaburi
- 36 months of NDVI historical data
- 50 catch logs from local fishers
- 12 degradation alerts
- 5 restoration sites
- 8 carbon credit records
- 90-day ecosystem forecast

## Navigation

Use the left sidebar to navigate between:
- Dashboard - Overview with KPIs and map
- Mangrove Monitoring - NDVI time series and zone details
- Fishery Analytics - FSI map and catch analysis
- Restoration Planning - Site management and carbon credits
- Alert Management - Degradation alert tracking
- ESG Report - Environmental, Social, and Governance metrics

## Features to Try

1. Click on mangrove zones on the map to see details
2. Sort and filter tables by clicking column headers
3. Hover over charts to see detailed tooltips
4. Acknowledge alerts in the Alert Management page
5. Download the ESG report (mock action)

## Build for Production

```bash
npm run build
```

The production build will be in the `dist` folder.

## Notes

- All data is mock data for demonstration purposes
- The map uses OpenStreetMap tiles (no API key required)
- Loading states simulate API calls with 800ms delay
