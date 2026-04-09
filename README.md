# docs101

[![PyPI](https://img.shields.io/pypi/v/docs101)](https://pypi.org/project/docs101/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/docs101)](https://pypi.org/project/docs101/)

Python client for the [docs101](https://docs101.com) invoicing API — create customers, generate EU-compliant invoices, and export to DATEV.

## Installation

```bash
pip install docs101
```

## Quick Start

```python
from docs101 import Docs101Client

client = Docs101Client(api_key="ak_live_YOUR_KEY_HERE")

# Create a customer
customer = client.customers.create(
    organization_name="Acme Corp",
    email="billing@acme.com",
    contact_type="B2B",
    vat_id="DE123456789",
    language="English",
)
customer_id = customer["id"]

# Add an address
client.customers.create_address(
    customer_id,
    address_line_1="Musterstraße 1",
    postal_code="10115",
    city="Berlin",
    country_code="DE",
    is_default=True,
)

# Create an invoice
invoice = client.invoices.create(
    customer_id=customer_id,
    benefit_period_start="2026-04-01",
    benefit_period_end="2026-04-30",
    invoice_format="ZUGFERD",
)
invoice_id = invoice["invoice_id"]

# Add a position
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

# Validate and finalize
validation = client.invoices.validate(invoice_id)
assert validation["valid"], f"Validation failed: {validation['errors']}"

client.invoices.finalize(invoice_id)

# Get PDF
pdf = client.invoices.get_pdf_url(invoice_id)
print(f"PDF ready: {pdf['filename']} — {pdf['url']}")
```

## Features

- **Typed exceptions** — `AuthenticationError`, `ValidationError`, `NotFoundError`, `LimitExceededError`, and more
- **Async job polling** — `finalize()` and `create_datev()` automatically poll until the job completes
- **DATEV export** — Configure DATEV settings and trigger exports with automatic download handling
- **ZUGFeRD, Peppol, FatturaPA, Facturae** — Full support for EU e-invoicing formats
- **Type hints** — Full type annotations with `py.typed` marker (PEP 561)

## Usage

### Customers

```python
# List all customers
customers = client.customers.list()

# Get a single customer
customer = client.customers.get(42)

# Update a customer
client.customers.update(42, email="new@acme.com")

# Manage addresses
addresses = client.customers.list_addresses(42)
client.customers.create_address(42, address_line_1="New St 1", city="Munich", country_code="DE")
client.customers.update_address(42, 1, city="Hamburg")
client.customers.delete_address(42, 1)
```

### Invoices

```python
# List invoices (paginated)
invoices = client.invoices.list(page=1, limit=25)

# Create, add positions, validate, finalize
invoice = client.invoices.create(customer_id=42, invoice_format="ZUGFERD")
invoice_id = invoice["invoice_id"]

client.invoices.add_position(invoice_id,
    title="Consulting", quantity=10, unit_id="HUR",
    unit_net_amount=150.00, single_net_amount=150.00,
    tax_rate=0.19, tax_treatment_id="standard",
)

client.invoices.validate(invoice_id)
client.invoices.finalize(invoice_id)

# Download links
pdf = client.invoices.get_pdf_url(invoice_id)
xml = client.invoices.get_xml_url(invoice_id)

# Status management
client.invoices.mark_as_sent(invoice_id)
client.invoices.mark_as_paid(invoice_id,
    paid_date="2026-04-15",
    payment_method="BANK_TRANSFER",
)

# Duplicate or cancel
new = client.invoices.duplicate(invoice_id)
client.invoices.cancel(invoice_id)
```

### DATEV Export

```python
# Configure DATEV
client.exports.configure_datev(
    consultant_number=1234567,
    client_number=12345,
    chart_of_accounts="SKR03",
)

# Run export (polls automatically)
result = client.exports.create_datev(
    start_date="2026-01-01",
    end_date="2026-03-31",
)

# Download all parts
for download_id in result["download_ids"]:
    url_info = client.downloads.get_url(download_id)
    print(f"Download: {url_info['url']}")
```

### Templates

```python
templates = client.templates.list()
template = client.templates.get(1)
```

### Error Handling

```python
from docs101 import (
    Docs101Error,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    LimitExceededError,
    VatOverrideRequiredError,
    JobFailedError,
    Docs101TimeoutError,
)

try:
    client.invoices.finalize(invoice_id)
except LimitExceededError as e:
    print(f"Limit reached: {e.used}/{e.limit}, resets {e.reset_date}")
except VatOverrideRequiredError:
    client.invoices.finalize(invoice_id, vat_override_confirmed=True)
except JobFailedError as e:
    print(f"Job failed: {e.error_message}")
except Docs101TimeoutError:
    print("Job timed out — check status manually")
```

## Examples

See the [`examples/`](examples/) directory for complete, runnable scripts:

- [`create_invoice.py`](examples/create_invoice.py) — Full workflow: customer → invoice → PDF
- [`bulk_invoicing.py`](examples/bulk_invoicing.py) — Bulk invoicing from CSV
- [`datev_export.py`](examples/datev_export.py) — DATEV export + download

## API Documentation

- [API Integration Guide](https://docs101.com/help/developers/api-integration-guide)
- [Invoice Workflow API Tutorial](https://docs101.com/help/developers/invoice-workflow-api)
- [Swagger / OpenAPI](https://docs101.com/api/v1/swagger/)
- [Developer Hub](https://docs101.com/help/developers/)

## Contributing

1. Clone the repo
2. Create a virtual environment: `python -m venv .venv && source .venv/bin/activate`
3. Install dev dependencies: `pip install -e ".[dev]"`
4. Run tests: `pytest tests/ -v`

## License

[MIT](LICENSE)
