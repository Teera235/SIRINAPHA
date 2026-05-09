"""Shared configuration constants for all Lambda functions."""

import os

# --- Supabase ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# --- AWS ---
AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-1")
SAGEMAKER_ENDPOINT = os.environ.get("SAGEMAKER_ENDPOINT", "")
SNS_ADMIN_TOPIC_ARN = os.environ.get("SNS_ADMIN_TOPIC_ARN", "")

# --- Target Regions (Bounding Boxes) ---
# Mahachai (Samut Sakhon) region
MAHACHAI_BBOX = {
    "lat_min": 13.4,
    "lat_max": 13.6,
    "lon_min": 100.2,
    "lon_max": 100.5,
}

# Ranong region
RANONG_BBOX = {
    "lat_min": 9.8,
    "lat_max": 10.1,
    "lon_min": 98.4,
    "lon_max": 98.7,
}

TARGET_REGIONS = {
    "mahachai": MAHACHAI_BBOX,
    "ranong": RANONG_BBOX,
}

# --- Data Pipeline ---
RETRY_MAX_ATTEMPTS = 3
RETRY_DELAY_MINUTES = 5

# --- NOAA ERDDAP ---
NOAA_ERDDAP_BASE_URL = "https://coastwatch.pfeg.noaa.gov/erddap"
NOAA_OISST_DATASET_ID = "ncdc_oisst_v2_avhrr_by_time_zlev_lat_lon"

# --- NASA Earthdata ---
NASA_MODIS_COLLECTION = "MODISA_L3m_CHL_NRT"

# --- GEBCO Bathymetry ---
GEBCO_FILE_PATH = os.environ.get("GEBCO_FILE_PATH", "data/gebco_bathymetry.nc")

# --- Copernicus Data Space ---
COPERNICUS_API_URL = os.environ.get("COPERNICUS_API_URL", "")
COPERNICUS_CLIENT_ID = os.environ.get("COPERNICUS_CLIENT_ID", "")
COPERNICUS_CLIENT_SECRET = os.environ.get("COPERNICUS_CLIENT_SECRET", "")
