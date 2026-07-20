-- QR Campaign tracking migration (idempotent)
-- Creates the qr_campaigns table and adds campaign attribution columns to inquiries
-- in BOTH the demo and pilot schemas. Safe to re-run.

CREATE TABLE IF NOT EXISTS demo.qr_campaigns (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    property_code VARCHAR(10) NOT NULL DEFAULT 'DT01',
    start_date DATE,
    end_date DATE,
    notes TEXT,
    created_by UUID REFERENCES demo.staff(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pilot.qr_campaigns (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    property_code VARCHAR(10) NOT NULL DEFAULT 'DT01',
    start_date DATE,
    end_date DATE,
    notes TEXT,
    created_by UUID REFERENCES pilot.staff(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

ALTER TABLE demo.inquiries ADD COLUMN IF NOT EXISTS campaign_id UUID;
ALTER TABLE demo.inquiries ADD COLUMN IF NOT EXISTS campaign_title VARCHAR(255);
ALTER TABLE pilot.inquiries ADD COLUMN IF NOT EXISTS campaign_id UUID;
ALTER TABLE pilot.inquiries ADD COLUMN IF NOT EXISTS campaign_title VARCHAR(255);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        JOIN pg_namespace n ON n.oid = c.connamespace
        WHERE c.conname = 'inquiries_campaign_id_fkey' AND n.nspname = 'demo'
    ) THEN
        ALTER TABLE demo.inquiries
            ADD CONSTRAINT inquiries_campaign_id_fkey
            FOREIGN KEY (campaign_id) REFERENCES demo.qr_campaigns(id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        JOIN pg_namespace n ON n.oid = c.connamespace
        WHERE c.conname = 'inquiries_campaign_id_fkey' AND n.nspname = 'pilot'
    ) THEN
        ALTER TABLE pilot.inquiries
            ADD CONSTRAINT inquiries_campaign_id_fkey
            FOREIGN KEY (campaign_id) REFERENCES pilot.qr_campaigns(id) ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_demo_inquiries_campaign_id ON demo.inquiries(campaign_id);
CREATE INDEX IF NOT EXISTS ix_pilot_inquiries_campaign_id ON pilot.inquiries(campaign_id);
