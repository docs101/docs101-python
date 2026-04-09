"""Complete workflow: Create customer → Invoice → Position → Finalize → PDF."""

import os

from docs101 import Docs101Client

client = Docs101Client(api_key=os.environ["DOCS101_API_KEY"])

# Create customer
customer = client.customers.create(
    organization_name="Acme Corp",
    email="billing@acme.com",
    contact_type="B2B",
    vat_id="DE123456789",
    language="English",
)
customer_id = customer["id"]
print(f"Created customer {customer_id}")

# Add address
client.customers.create_address(
    customer_id,
    company="Acme Corp",
    address_line_1="Musterstraße 1",
    postal_code="10115",
    city="Berlin",
    country_code="DE",
    is_default=True,
)
print("Address added")

# Create invoice
invoice = client.invoices.create(
    customer_id=customer_id,
    benefit_period_start="2026-04-01",
    benefit_period_end="2026-04-30",
    invoice_format="ZUGFERD",
)
invoice_id = invoice["invoice_id"]
print(f"Created invoice {invoice_id}")

# Add position
client.invoices.add_position(
    invoice_id,
    title="Pro Plan — Monthly Subscription",
    quantity=1.0,
    unit_id="HUR",
    unit_net_amount=25.00,
    single_net_amount=25.00,
    tax_rate=0.19,
    tax_treatment_id="standard",
)
print("Position added")

# Validate
validation = client.invoices.validate(invoice_id)
assert validation["valid"], f"Validation failed: {validation['errors']}"
print("Validation passed")

# Finalize (starts async job, polls until done)
client.invoices.finalize(invoice_id)
print("Invoice finalized")

# Download PDF
pdf = client.invoices.get_pdf_url(invoice_id)
print(f"PDF ready: {pdf['filename']} — {pdf['url']}")

# Mark as sent
client.invoices.mark_as_sent(invoice_id)
print("Invoice marked as sent")
