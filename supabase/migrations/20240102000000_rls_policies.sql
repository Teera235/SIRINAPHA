-- ============================================================================
-- SIRINAPHA: Baan-Pla Link — Row Level Security (RLS) Policies
-- ============================================================================
-- Implements role-based data access filtering:
-- - Community_Rep sees only data for their responsible_area_ids
-- - Corporate_Partner sees ESG/Blue Carbon data filtered by membership_tier
-- - Fisherman sees FSI data for their registered fishing_area_ids
-- Requirements: 7.4, 7.5
-- ============================================================================

-- ---------------------------------------------------------------------------
-- Enable RLS on all relevant tables
-- ---------------------------------------------------------------------------
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE fsi_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE fsi_component_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE ndvi_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE mangrove_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE carbon_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE catch_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE yield_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE delivery_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE fishing_areas ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_fishing_areas ENABLE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------------------
-- Helper function: get the current user's type from the users table
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_user_type()
RETURNS TEXT AS $$
  SELECT user_type FROM users WHERE id = auth.uid();
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- ---------------------------------------------------------------------------
-- Helper function: get the current user's membership tier
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_membership_tier()
RETURNS TEXT AS $$
  SELECT membership_tier FROM users WHERE id = auth.uid();
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- ---------------------------------------------------------------------------
-- Helper function: get area IDs associated with the current user
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_user_area_ids()
RETURNS SETOF UUID AS $$
  SELECT area_id FROM user_fishing_areas WHERE user_id = auth.uid();
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- ============================================================================
-- USERS table policies
-- ============================================================================

-- Users can read their own profile
CREATE POLICY users_select_own ON users
  FOR SELECT USING (id = auth.uid());

-- Users can update their own profile
CREATE POLICY users_update_own ON users
  FOR UPDATE USING (id = auth.uid());

-- ============================================================================
-- FISHING_AREAS table policies
-- ============================================================================

-- All authenticated users can read fishing areas
CREATE POLICY fishing_areas_select ON fishing_areas
  FOR SELECT USING (auth.uid() IS NOT NULL);

-- ============================================================================
-- USER_FISHING_AREAS junction table policies
-- ============================================================================

-- Users can read their own area associations
CREATE POLICY user_fishing_areas_select_own ON user_fishing_areas
  FOR SELECT USING (user_id = auth.uid());

-- ============================================================================
-- FSI_RESULTS table policies (Req 7.4, 7.5)
-- ============================================================================

-- Fisherman: can only see FSI data for their registered fishing_area_ids
-- Community_Rep: can only see FSI data for their responsible_area_ids
-- Corporate_Partner: can see all FSI data (filtered by tier at app level)
CREATE POLICY fsi_results_select ON fsi_results
  FOR SELECT USING (
    CASE get_user_type()
      WHEN 'Fisherman' THEN area_id IN (SELECT get_user_area_ids())
      WHEN 'Community_Rep' THEN area_id IN (SELECT get_user_area_ids())
      WHEN 'Corporate_Partner' THEN true
      ELSE false
    END
  );

-- ============================================================================
-- FSI_COMPONENT_SCORES table policies
-- ============================================================================

-- Access follows the parent fsi_results row
CREATE POLICY fsi_component_scores_select ON fsi_component_scores
  FOR SELECT USING (
    fsi_result_id IN (
      SELECT id FROM fsi_results WHERE
        CASE get_user_type()
          WHEN 'Fisherman' THEN area_id IN (SELECT get_user_area_ids())
          WHEN 'Community_Rep' THEN area_id IN (SELECT get_user_area_ids())
          WHEN 'Corporate_Partner' THEN true
          ELSE false
        END
    )
  );

-- ============================================================================
-- NDVI_RECORDS table policies (Req 7.4)
-- ============================================================================

-- Community_Rep: only their responsible areas
-- Corporate_Partner: all (ESG data)
-- Fisherman: their fishing areas
CREATE POLICY ndvi_records_select ON ndvi_records
  FOR SELECT USING (
    CASE get_user_type()
      WHEN 'Fisherman' THEN area_id IN (SELECT get_user_area_ids())
      WHEN 'Community_Rep' THEN area_id IN (SELECT get_user_area_ids())
      WHEN 'Corporate_Partner' THEN true
      ELSE false
    END
  );

-- ============================================================================
-- MANGROVE_ALERTS table policies (Req 7.4)
-- ============================================================================

-- Community_Rep: only their responsible areas
-- Corporate_Partner: all alerts
-- Fisherman: their fishing areas
CREATE POLICY mangrove_alerts_select ON mangrove_alerts
  FOR SELECT USING (
    CASE get_user_type()
      WHEN 'Fisherman' THEN area_id IN (SELECT get_user_area_ids())
      WHEN 'Community_Rep' THEN area_id IN (SELECT get_user_area_ids())
      WHEN 'Corporate_Partner' THEN true
      ELSE false
    END
  );

-- ============================================================================
-- CARBON_REPORTS table policies (Req 7.5)
-- ============================================================================

-- Corporate_Partner only — filtered by membership tier at the app level.
-- Silver tier: basic carbon reports
-- Gold tier: all carbon reports + detailed breakdowns
-- Community_Rep can also view carbon reports for their areas.
CREATE POLICY carbon_reports_select ON carbon_reports
  FOR SELECT USING (
    CASE get_user_type()
      WHEN 'Corporate_Partner' THEN true
      WHEN 'Community_Rep' THEN true
      ELSE false
    END
  );

-- ============================================================================
-- YIELD_PREDICTIONS table policies
-- ============================================================================

-- Fisherman and Community_Rep: only their areas
-- Corporate_Partner: all
CREATE POLICY yield_predictions_select ON yield_predictions
  FOR SELECT USING (
    CASE get_user_type()
      WHEN 'Fisherman' THEN area_id IN (SELECT get_user_area_ids())
      WHEN 'Community_Rep' THEN area_id IN (SELECT get_user_area_ids())
      WHEN 'Corporate_Partner' THEN true
      ELSE false
    END
  );

-- ============================================================================
-- CATCH_REPORTS table policies
-- ============================================================================

-- Fisherman: can read/write their own catch reports
-- Community_Rep: can read catch reports for their areas
-- Corporate_Partner: can read all catch reports
CREATE POLICY catch_reports_select ON catch_reports
  FOR SELECT USING (
    CASE get_user_type()
      WHEN 'Fisherman' THEN user_id = auth.uid()
      WHEN 'Community_Rep' THEN area_id IN (SELECT get_user_area_ids())
      WHEN 'Corporate_Partner' THEN true
      ELSE false
    END
  );

CREATE POLICY catch_reports_insert ON catch_reports
  FOR INSERT WITH CHECK (
    user_id = auth.uid() AND get_user_type() = 'Fisherman'
  );

-- ============================================================================
-- DELIVERY_LOGS table policies
-- ============================================================================

-- Users can only see their own delivery logs
CREATE POLICY delivery_logs_select_own ON delivery_logs
  FOR SELECT USING (user_id = auth.uid());

-- ============================================================================
-- Service role bypass note:
-- The service role key (used by server-side admin operations and Lambda
-- functions) bypasses all RLS policies automatically.
-- ============================================================================
