-- ============================================================================
-- SIRINAPHA: Baan-Pla Link — Initial Database Schema
-- ============================================================================
-- Enables PostGIS for geospatial queries and pgcrypto for PII encryption.
-- Creates all 15 tables, foreign keys, geospatial GIST indexes, and
-- time-series indexes as defined in the design document.
-- Requirements: 10.1, 10.2, 10.4, 10.6
-- ============================================================================

-- ---------------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "postgis";       -- geospatial queries (Req 10.6)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";      -- column-level PII encryption (Req 10.4)

-- ---------------------------------------------------------------------------
-- 1. users
-- ---------------------------------------------------------------------------
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_type       TEXT NOT NULL CHECK (user_type IN ('Fisherman', 'Community_Rep', 'Corporate_Partner')),
    display_name    TEXT NOT NULL,
    preferred_channel TEXT NOT NULL DEFAULT 'line' CHECK (preferred_channel IN ('line', 'sms')),
    -- PII fields encrypted with pgcrypto
    line_user_id    BYTEA,                      -- encrypted via pgp_sym_encrypt
    phone_number    BYTEA,                      -- encrypted via pgp_sym_encrypt
    company_name    TEXT,
    membership_tier TEXT CHECK (membership_tier IN ('Silver', 'Gold')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- 2. fishing_areas
-- ---------------------------------------------------------------------------
CREATE TABLE fishing_areas (
    id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name      TEXT NOT NULL,
    boundary  GEOGRAPHY(Polygon, 4326),
    region    TEXT NOT NULL
);

-- ---------------------------------------------------------------------------
-- 3. user_fishing_areas (junction table)
-- ---------------------------------------------------------------------------
CREATE TABLE user_fishing_areas (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    area_id UUID NOT NULL REFERENCES fishing_areas(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, area_id)
);

-- ---------------------------------------------------------------------------
-- 4. satellite_raw_data  (Req 10.1 — raw data separate from processed)
-- ---------------------------------------------------------------------------
CREATE TABLE satellite_raw_data (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source          TEXT NOT NULL,
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    data_timestamp  TIMESTAMPTZ NOT NULL,
    data            JSONB NOT NULL,
    status          TEXT NOT NULL DEFAULT 'valid' CHECK (status IN ('valid', 'invalid', 'partial')),
    coverage        GEOGRAPHY(Polygon, 4326)
);

-- ---------------------------------------------------------------------------
-- 5. ndvi_records  (Req 10.2 — time-series, 5-year retention)
-- ---------------------------------------------------------------------------
CREATE TABLE ndvi_records (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    area_id             UUID NOT NULL REFERENCES fishing_areas(id) ON DELETE CASCADE,
    ndvi_value          DOUBLE PRECISION NOT NULL,
    health_level        TEXT NOT NULL CHECK (health_level IN ('healthy', 'moderate', 'degraded', 'critical')),
    sentinel2_scene_id  TEXT,
    observed_at         TIMESTAMPTZ NOT NULL,
    location            GEOGRAPHY(Point, 4326) NOT NULL
);

-- ---------------------------------------------------------------------------
-- 6. sst_records  (Req 10.2 — time-series, 5-year retention)
-- ---------------------------------------------------------------------------
CREATE TABLE sst_records (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sst_celsius DOUBLE PRECISION NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    location    GEOGRAPHY(Point, 4326) NOT NULL
);

-- ---------------------------------------------------------------------------
-- 7. chl_a_records  (Req 10.2 — time-series, 5-year retention)
-- ---------------------------------------------------------------------------
CREATE TABLE chl_a_records (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chl_a_mg_m3   DOUBLE PRECISION NOT NULL,
    observed_at   TIMESTAMPTZ NOT NULL,
    location      GEOGRAPHY(Point, 4326) NOT NULL
);

-- ---------------------------------------------------------------------------
-- 8. fsi_results
-- ---------------------------------------------------------------------------
CREATE TABLE fsi_results (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    area_id       UUID NOT NULL REFERENCES fishing_areas(id) ON DELETE CASCADE,
    fsi_value     DOUBLE PRECISION NOT NULL CHECK (fsi_value >= 0.0 AND fsi_value <= 1.0),
    zone          TEXT NOT NULL CHECK (zone IN ('green', 'yellow', 'red')),
    is_complete   BOOLEAN NOT NULL DEFAULT true,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    location      GEOGRAPHY(Point, 4326) NOT NULL
);

-- ---------------------------------------------------------------------------
-- 9. fsi_component_scores
-- ---------------------------------------------------------------------------
CREATE TABLE fsi_component_scores (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fsi_result_id   UUID NOT NULL REFERENCES fsi_results(id) ON DELETE CASCADE,
    sst_score       DOUBLE PRECISION NOT NULL CHECK (sst_score >= 0.0 AND sst_score <= 1.0),
    chl_a_score     DOUBLE PRECISION NOT NULL CHECK (chl_a_score >= 0.0 AND chl_a_score <= 1.0),
    depth_score     DOUBLE PRECISION NOT NULL CHECK (depth_score >= 0.0 AND depth_score <= 1.0),
    lunar_score     DOUBLE PRECISION NOT NULL CHECK (lunar_score >= 0.0 AND lunar_score <= 1.0),
    ndvi_score      DOUBLE PRECISION NOT NULL CHECK (ndvi_score >= 0.0 AND ndvi_score <= 1.0),
    season_score    DOUBLE PRECISION NOT NULL CHECK (season_score >= 0.0 AND season_score <= 1.0)
);

-- ---------------------------------------------------------------------------
-- 10. yield_predictions
-- ---------------------------------------------------------------------------
CREATE TABLE yield_predictions (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    area_id               UUID NOT NULL REFERENCES fishing_areas(id) ON DELETE CASCADE,
    species_predictions   JSONB NOT NULL,
    forecast_7day         JSONB NOT NULL,
    forecast_30day        JSONB NOT NULL,
    confidence_lower      DOUBLE PRECISION NOT NULL,
    confidence_upper      DOUBLE PRECISION NOT NULL,
    model_version         TEXT NOT NULL,
    predicted_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_confidence_interval CHECK (confidence_lower <= confidence_upper)
);

-- ---------------------------------------------------------------------------
-- 11. mangrove_alerts
-- ---------------------------------------------------------------------------
CREATE TABLE mangrove_alerts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    area_id         UUID NOT NULL REFERENCES fishing_areas(id) ON DELETE CASCADE,
    alert_level     TEXT NOT NULL CHECK (alert_level IN ('warning', 'critical')),
    ndvi_current    DOUBLE PRECISION NOT NULL,
    ndvi_6month_avg DOUBLE PRECISION NOT NULL,
    change_percent  DOUBLE PRECISION NOT NULL,
    detected_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    geometry        GEOGRAPHY(Polygon, 4326),
    is_resolved     BOOLEAN NOT NULL DEFAULT false
);

-- ---------------------------------------------------------------------------
-- 12. restoration_sites
-- ---------------------------------------------------------------------------
CREATE TABLE restoration_sites (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    geometry                GEOGRAPHY(Polygon, 4326),
    area_rai                DOUBLE PRECISION NOT NULL,
    carbon_potential        DOUBLE PRECISION NOT NULL,
    expected_survival_rate  DOUBLE PRECISION NOT NULL CHECK (expected_survival_rate >= 0.0 AND expected_survival_rate <= 1.0),
    priority_rank           INTEGER NOT NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- 13. carbon_reports
-- ---------------------------------------------------------------------------
CREATE TABLE carbon_reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id         UUID NOT NULL REFERENCES restoration_sites(id) ON DELETE CASCADE,
    period_start    DATE NOT NULL,
    period_end      DATE NOT NULL,
    total_area_rai  DOUBLE PRECISION NOT NULL,
    avg_ndvi        DOUBLE PRECISION NOT NULL,
    total_co2_tons  DOUBLE PRECISION NOT NULL,
    revenue_sharing JSONB NOT NULL,
    generated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- 14. catch_reports
-- ---------------------------------------------------------------------------
CREATE TABLE catch_reports (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    area_id       UUID NOT NULL REFERENCES fishing_areas(id) ON DELETE CASCADE,
    species_catch JSONB NOT NULL,
    total_kg      DOUBLE PRECISION NOT NULL,
    catch_date    DATE NOT NULL,
    reported_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- 15. delivery_logs
-- ---------------------------------------------------------------------------
CREATE TABLE delivery_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel         TEXT NOT NULL CHECK (channel IN ('line', 'sms', 'web')),
    message_type    TEXT NOT NULL CHECK (message_type IN ('daily_fsi', 'alert', 'report')),
    status          TEXT NOT NULL CHECK (status IN ('pending', 'sent', 'failed', 'fallback_sms')),
    content_preview TEXT,
    sent_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ===========================================================================
-- Geospatial GIST Indexes  (Req 10.6 — geospatial queries)
-- ===========================================================================
CREATE INDEX idx_fsi_results_location   ON fsi_results   USING GIST (location);
CREATE INDEX idx_ndvi_records_location  ON ndvi_records   USING GIST (location);
CREATE INDEX idx_sst_records_location   ON sst_records    USING GIST (location);

-- ===========================================================================
-- Time-Series Indexes  (Req 10.2 — efficient historical queries)
-- ===========================================================================
CREATE INDEX idx_ndvi_records_time  ON ndvi_records  (area_id, observed_at DESC);
CREATE INDEX idx_fsi_results_time   ON fsi_results   (area_id, calculated_at DESC);

-- ===========================================================================
-- Additional useful indexes
-- ===========================================================================
CREATE INDEX idx_satellite_raw_data_source_time ON satellite_raw_data (source, fetched_at DESC);
CREATE INDEX idx_mangrove_alerts_area_detected  ON mangrove_alerts    (area_id, detected_at DESC);
CREATE INDEX idx_delivery_logs_user_sent        ON delivery_logs      (user_id, sent_at DESC);
CREATE INDEX idx_catch_reports_user_date        ON catch_reports      (user_id, catch_date DESC);
CREATE INDEX idx_users_user_type                ON users              (user_type);

-- ===========================================================================
-- Helper functions for PII encryption / decryption
-- ===========================================================================
-- Usage examples (application layer should pass the encryption key):
--   INSERT INTO users (line_user_id, phone_number, ...)
--     VALUES (pgp_sym_encrypt('U1234abc', 'encryption_key'),
--             pgp_sym_encrypt('+66812345678', 'encryption_key'), ...);
--
--   SELECT pgp_sym_decrypt(line_user_id, 'encryption_key') AS line_user_id,
--          pgp_sym_decrypt(phone_number, 'encryption_key') AS phone_number
--     FROM users WHERE id = '...';
