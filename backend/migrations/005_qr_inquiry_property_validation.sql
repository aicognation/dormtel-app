-- 005_qr_inquiry_property_validation.sql
--
-- FIX-009 (2026-07-21): Property-level isolation for QR inquiries.
--
-- Root cause: When a QR inquiry was submitted via the public form (no auth),
-- the create_inquiry endpoint defaulted property_code to "DT01" regardless
-- of which property the QR campaign belonged to. This caused:
--   - DT01 staff seeing DT02's QR leads (data leak)
--   - DT02 staff unable to see their own QR leads (broken isolation)
--
-- The code fix (inquiries.py) now derives property_code from the campaign
-- when campaign_id is provided. This trigger is a defense-in-depth measure:
-- even if the code has a bug, the database will reject inquiries where
-- property_code doesn't match the campaign's property_code.
--
-- Idempotent: safe to run on every deploy.

-- Drop existing trigger/function if they exist (for re-runs)
DROP TRIGGER IF EXISTS trg_validate_inquiry_property ON pilot.inquiries;
DROP TRIGGER IF EXISTS trg_validate_inquiry_property ON demo.inquiries;
DROP FUNCTION IF EXISTS pilot.validate_inquiry_property();
DROP FUNCTION IF EXISTS demo.validate_inquiry_property();

-- Create validation function for pilot schema
CREATE OR REPLACE FUNCTION pilot.validate_inquiry_property()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.campaign_id IS NOT NULL THEN
        DECLARE
            campaign_prop VARCHAR(10);
        BEGIN
            SELECT property_code INTO campaign_prop
            FROM pilot.qr_campaigns
            WHERE id = NEW.campaign_id;

            IF campaign_prop IS NOT NULL AND NEW.property_code != campaign_prop THEN
                RAISE EXCEPTION 'Property mismatch: inquiry property_code (%) does not match campaign property_code (%)',
                    NEW.property_code, campaign_prop;
            END IF;
        END;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create validation function for demo schema
CREATE OR REPLACE FUNCTION demo.validate_inquiry_property()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.campaign_id IS NOT NULL THEN
        DECLARE
            campaign_prop VARCHAR(10);
        BEGIN
            SELECT property_code INTO campaign_prop
            FROM demo.qr_campaigns
            WHERE id = NEW.campaign_id;

            IF campaign_prop IS NOT NULL AND NEW.property_code != campaign_prop THEN
                RAISE EXCEPTION 'Property mismatch: inquiry property_code (%) does not match campaign property_code (%)',
                    NEW.property_code, campaign_prop;
            END IF;
        END;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach triggers
CREATE TRIGGER trg_validate_inquiry_property
BEFORE INSERT OR UPDATE ON pilot.inquiries
FOR EACH ROW EXECUTE FUNCTION pilot.validate_inquiry_property();

CREATE TRIGGER trg_validate_inquiry_property
BEFORE INSERT OR UPDATE ON demo.inquiries
FOR EACH ROW EXECUTE FUNCTION demo.validate_inquiry_property();
