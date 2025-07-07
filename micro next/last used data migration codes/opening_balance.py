import pandas as pd

# Load input Excel file
input_file = 'CHART OF ACCOUNTS_31-03-2025_FINAL_with customer and vendor id.xlsx'
df = pd.read_excel(input_file)

# Clean and convert Opening Balance to float
def clean_balance(val):
    if pd.isna(val):
        return 0
    val = str(val).replace('₹', '').replace(',', '').strip()
    try:
        return float(val)
    except ValueError:
        return 0

df['Opening Balance'] = df['Opening Balance'].apply(clean_balance)

# Drop rows where Opening Balance is 0
df = df[df['Opening Balance'] != 0].reset_index(drop=True)

# Prepare output DataFrame
output = pd.DataFrame()

# Static columns
output['ID'] = [''] * len(df)
output['Entry Type'] = ['Opening Entry'] + [''] * (len(df) - 1)
output['Company'] = ['Srinath Collective'] + [''] * (len(df) - 1)
output['Posting Date'] = ['2025-05-30'] + [''] * (len(df) - 1)
output['Is Opening'] = ['Yes'] + [''] * (len(df) - 1)
output['ID (Accounting Entries)'] = [''] * len(df)

# Account mapping
def map_account(row):
    group = str(row['Account group']).strip().lower()
    account_prefix = str(row.get('Account', '')).strip()
    
    if group == 'sundry debtors':
        return 'Debtors - SC'
    elif group == 'sundry creditors':
        return 'Creditors - SC'
    
    vendor_name = str(row.get('Vendor Name', '')).strip()
    customer_name = str(row.get('Customer Name', '')).strip()

    if vendor_name and vendor_name.lower() != 'nan':
        return f"{account_prefix} - {vendor_name} - SC"
    elif customer_name and customer_name.lower() != 'nan':
        return f"{account_prefix} - {customer_name} - SC"
    else:
        return "Unknown Party - SC"


# Party Type mapping from account group
def map_party_type(account_group):
    group = str(account_group).strip().lower()
    if group == 'sundry debtors':
        return 'Customer'
    elif group == 'sundry creditors':
        return 'Supplier'
    else:
        return ''

# Party ID mapping
def map_party(row):
    customer_id = row.get('CUSTOMER ID', '')
    vendor_id = row.get('VENDOR ID', '')
    if pd.notna(customer_id) and str(customer_id).strip():
        return str(customer_id).strip()
    elif pd.notna(vendor_id) and str(vendor_id).strip():
        return str(vendor_id).strip()
    else:
        return ''

# Apply mappings
output['Account (Accounting Entries)'] = df.apply(map_account, axis=1)
output['Party Type (Accounting Entries)'] = df['Account group'].apply(map_party_type)
output['Party (Accounting Entries)'] = df.apply(map_party, axis=1)

# Adjust party type if missing and can be inferred from prefix
def adjust_party_type(row):
    if row['Party Type (Accounting Entries)']:
        return row['Party Type (Accounting Entries)']
    party = row['Party (Accounting Entries)']
    if isinstance(party, str):
        if party.startswith('SSWVE'):
            return 'Supplier'
        elif party.startswith('SSWCU'):
            return 'Customer'
    return ''

output['Party Type (Accounting Entries)'] = output.apply(adjust_party_type, axis=1)

# Override account based on Party Type
def override_account(row):
    if row['Party Type (Accounting Entries)'] == 'Supplier':
        return 'Creditors - SC'
    elif row['Party Type (Accounting Entries)'] == 'Customer':
        return 'Debtors - SC'
    else:
        return row['Account (Accounting Entries)']

output['Account (Accounting Entries)'] = output.apply(override_account, axis=1)

# Credit/Debit based on balance sign
output['Debit (Accounting Entries)'] = df['Opening Balance'].apply(lambda x: x if x > 0 else 0)
output['Credit (Accounting Entries)'] = df['Opening Balance'].apply(lambda x: abs(x) if x < 0 else 0)

# Optional: flag missing names
output['Notes'] = output['Account (Accounting Entries)'].apply(
    lambda x: 'Missing Vendor/Customer Name' if 'Unknown Party' in x else ''
)

# Summary info
missing_name_count = (output['Notes'] == 'Missing Vendor/Customer Name').sum()
print(f"ℹ️ {missing_name_count} entries missing vendor/customer name")

# Save to Excel
output_file = 'opening_balances_output.xlsx'
output.to_excel(output_file, index=False)

print(f"✅ Output file saved as {output_file}")
