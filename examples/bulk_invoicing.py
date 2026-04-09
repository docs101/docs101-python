"""Bulk invoicing: Read customers + positions from CSV and create invoices."""

import csv
import os
import sys

from docs101 import Docs101Client, LimitExceededError

client = Docs101Client(api_key=os.environ["DOCS101_API_KEY"])

csv_path = sys.argv[1] if len(sys.argv) > 1 else "invoices.csv"

# Expected CSV columns:
# customer_id, title, quantity, unit_id, unit_net_amount, tax_rate

with open(csv_path, newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Group rows by customer_id
invoices_by_customer = {}
for row in rows:
    cid = int(row["customer_id"])
    invoices_by_customer.setdefault(cid, []).append(row)

for customer_id, positions in invoices_by_customer.items():
    try:
        # Create invoice
        invoice = client.invoices.create(
            customer_id=customer_id,
            invoice_format="ZUGFERD",
        )
        invoice_id = invoice["invoice_id"]
        print(f"Invoice {invoice_id} created for customer {customer_id}")

        # Add positions
        for pos in positions:
            amount = float(pos["unit_net_amount"])
            client.invoices.add_position(
                invoice_id,
                title=pos["title"],
                quantity=float(pos["quantity"]),
                unit_id=pos["unit_id"],
                unit_net_amount=amount,
                single_net_amount=amount,
                tax_rate=float(pos.get("tax_rate", 0.19)),
                tax_treatment_id="standard",
            )

        # Validate and finalize
        validation = client.invoices.validate(invoice_id)
        if not validation["valid"]:
            print(f"  Validation failed: {validation['errors']}")
            continue

        client.invoices.finalize(invoice_id)
        print(f"  Invoice {invoice_id} finalized")

    except LimitExceededError as e:
        print(f"Monthly limit reached ({e.used}/{e.limit}). Resets: {e.reset_date}")
        print("Stopping bulk process.")
        break
    except Exception as e:
        print(f"  Error for customer {customer_id}: {e}")
        continue

print("Done.")
