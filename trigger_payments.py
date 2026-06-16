"""
Trigger demo webhook payments on dormtel.quriosity.cloud
to populate today's DSR with revenue.
"""
import asyncio
import asyncpg
import httpx
import uuid
from datetime import datetime, timezone

API_BASE = "https://dormtel.quriosity.cloud/api/v1"
DB_URL = "postgresql://dormtel:dormtel_prod_2026@db:5432/dormtel"


async def get_billable_residents():
    """Get residents with distributed billings that haven't been paid yet."""
    conn = await asyncpg.connect(DB_URL)
    rows = await conn.fetch("""
        SELECT r.id as rid, r.full_name, b.billing_period, b.total_amount
        FROM residents r
        JOIN billings b ON b.resident_id = r.id
        WHERE b.status = 'distributed'
        ORDER BY r.full_name
        LIMIT 6
    """)
    await conn.close()
    return rows


async def trigger_webhook_payments():
    """Send webhook payments to simulate GCash/Maya transactions."""
    # Since we can't connect to DB from local, use the API directly
    # We'll construct reference_ids based on known resident data
    
    async with httpx.AsyncClient(timeout=30) as client:
        # First check current DSR
        resp = await client.get(f"{API_BASE}/payments/dsr")
        print(f"Current DSR: {resp.json()}")
        
        # Get unmatched payments to understand the state
        resp = await client.get(f"{API_BASE}/payments/unmatched")
        unmatched = resp.json()
        print(f"Unmatched payments: {len(unmatched) if isinstance(unmatched, list) else unmatched}")
        
        # Simulate 5 webhook payments with varied amounts
        payments = [
            {"amount": 8500.00, "sender": "MARIA SANTOS", "channel": "gcash"},
            {"amount": 7200.00, "sender": "JUAN DELA CRUZ", "channel": "maya"},
            {"amount": 6500.00, "sender": "ANA REYES", "channel": "gcash"},
            {"amount": 9100.00, "sender": "CARLOS GARCIA", "channel": "bank_transfer"},
            {"amount": 5500.00, "sender": "JENNY LIM", "channel": "gcash"},
        ]
        
        total = 0
        success = 0
        for i, p in enumerate(payments, 1):
            # Generate a unique reference for each payment
            ref_id = f"PAY-{uuid.uuid4().hex[:8].upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
            
            payload = {
                "amount": p["amount"],
                "reference_id": ref_id,
                "sender_name": p["sender"],
                "channel": p["channel"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            resp = await client.post(f"{API_BASE}/payments/webhook", json=payload)
            if resp.status_code in (200, 201):
                print(f"  [{i}] OK: {p['sender']} - P{p['amount']:,.2f} via {p['channel']}")
                total += p["amount"]
                success += 1
            else:
                print(f"  [{i}] FAILED ({resp.status_code}): {resp.text[:200]}")
        
        print(f"\nSent {success}/{len(payments)} payments, total: P{total:,.2f}")
        
        # Check updated DSR
        resp = await client.get(f"{API_BASE}/payments/dsr")
        print(f"Updated DSR: {resp.json()}")


if __name__ == "__main__":
    asyncio.run(trigger_webhook_payments())
