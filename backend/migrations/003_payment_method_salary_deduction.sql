-- Migration 003: extend payment_method enum with 'salary_deduction'
--
-- Why: the admin UI (frontend/src/utils/constants.js PAYMENT_METHODS) offers
-- "Salary Deduction" as a payment method, but the PG enum only had
-- {gcash, maya, bank_transfer, cash}. Recording a salary-deduction payment
-- failed with: invalid input value for enum payment_method -> HTTP 500.
--
-- Notes:
--   * PG enum types live in the public schema and are shared by demo + pilot.
--   * ALTER TYPE ... ADD VALUE IF NOT EXISTS is idempotent (PG 12+).
--   * models.py Payment.method Enum is updated in lockstep (same commit).

ALTER TYPE payment_method ADD VALUE IF NOT EXISTS 'salary_deduction';
