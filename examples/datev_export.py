"""DATEV export: Configure → Export → Download."""

import os

from docs101 import Docs101Client

client = Docs101Client(api_key=os.environ["DOCS101_API_KEY"])

# Configure DATEV (only needed once)
client.exports.configure_datev(
    consultant_number=1234567,
    client_number=12345,
    chart_of_accounts="SKR03",
    fiscal_year_start_month=1,
)
print("DATEV configured")

# Start export (polls automatically until finished)
result = client.exports.create_datev(
    start_date="2026-01-01",
    end_date="2026-03-31",
    include_master_data=True,
    include_documents=True,
    only_new=True,
)

print(f"Export complete: {result['total_invoice_count']} invoices")

if result.get("is_split"):
    print(f"Export was split: {result.get('split_reason')}")

# Download all parts
for download_id in result["download_ids"]:
    url_info = client.downloads.get_url(download_id)
    print(f"Download: {url_info['url']}")
