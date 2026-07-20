-- Deposits tenant-table migration (idempotent)
-- Root cause of the "Create Reservation" 500: deposits existed ONLY in the public
-- schema with an FK to public.residents, but tenant residents live in demo/pilot.
-- Any reservation WITH deposits violated deposits_resident_id_fkey and crashed.
-- Fix: create per-tenant deposits tables (they shadow public.deposits via
-- search_path "<schema>, public") with FKs to the correct tenant residents table,
-- and retire the unsatisfiable FK on the legacy public table.

CREATE TABLE IF NOT EXISTS demo.deposits (
    id UUID PRIMARY KEY,
    resident_id UUID NOT NULL REFERENCES demo.residents(id) ON DELETE CASCADE,
    deposit_type deposit_type NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    receipt_number VARCHAR(100),
    payment_date DATE DEFAULT NOW(),
    status deposit_status NOT NULL DEFAULT 'paid',
    refunded_amount NUMERIC(10, 2),
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pilot.deposits (
    id UUID PRIMARY KEY,
    resident_id UUID NOT NULL REFERENCES pilot.residents(id) ON DELETE CASCADE,
    deposit_type deposit_type NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    receipt_number VARCHAR(100),
    payment_date DATE DEFAULT NOW(),
    status deposit_status NOT NULL DEFAULT 'paid',
    refunded_amount NUMERIC(10, 2),
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_demo_deposits_resident_id ON demo.deposits(resident_id);
CREATE INDEX IF NOT EXISTS ix_pilot_deposits_resident_id ON pilot.deposits(resident_id);

-- Retire the unsatisfiable cross-schema FK on the legacy public table (0 rows;
-- the table is now shadowed by the tenant copies and never written to).
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint c
        JOIN pg_namespace n ON n.oid = c.connamespace
        WHERE c.conname = 'deposits_resident_id_fkey' AND n.nspname = 'public'
    ) THEN
        ALTER TABLE public.deposits DROP CONSTRAINT deposits_resident_id_fkey;
    END IF;
END $$;
