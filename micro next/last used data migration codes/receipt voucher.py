import pandas as pd

# Load client input file
input_file = 'RECEIPT VOUCHERS - APRIL 2025 AND MAY 2025_with_ids.xlsx'  # Replace with your actual file
df = pd.read_excel(input_file)

def clean_currency(value):
    if isinstance(value, str):
        # Remove currency symbol, commas, and extra spaces
        return value.replace('₹', '').replace(',', '').strip()
    return value
# Clean the 'Amount' column
df['Amount'] = df['Amount'].apply(clean_currency)
# Helper function to format particulars with Ledger Id, excluding prefix if Ledger Id is #NA or missing
def format_particulars(row):
    ledger_id = str(row['Ledger Id']) if pd.notnull(row['Ledger Id']) else ''
    particulars = str(row['Ledger']) if pd.notnull(row['Ledger']) else ''
    
    if ledger_id.strip().upper() == '#NA' or ledger_id.strip() == '':
        return f"{particulars} - SC"
    else:
        return f"{ledger_id} - {particulars} - SC"

def format_particulars1(row):
    payment_ledger_id = str(row['Payment Ledger Ids']) if pd.notnull(row['Payment Ledger Ids']) else ''
    particulars = str(row['Payment Ledger']) if pd.notnull(row['Payment Ledger']) else ''
    
    if payment_ledger_id.strip().upper() == '#NA' or payment_ledger_id.strip() == '':
        return f"{particulars} - SC"
    else:
        return f"{payment_ledger_id} - {particulars} - SC"

# Prepare output list
output_rows = []

# Process each row individually instead of grouping
for idx, row in df.iterrows():
    # Skip rows where status is Deleted
    if pd.notnull(row['Status']) and str(row['Status']).strip().lower() == 'deleted':
        continue
    remarks = row['narration'] if 'narration' in df.columns and pd.notnull(row['narration']) else ''
    custom_remarks = '0' if pd.isna(remarks) or str(remarks).strip() == '' else '1'
    # Format Posting Date as yyyy-mm-dd
    posting_date = ''
    if pd.notnull(row['Date']):
        try:
            posting_date = pd.to_datetime(row['Date']).strftime('%Y-%m-%d')
        except Exception:
            posting_date = str(row['Date'])
    if pd.notnull(row['Customer Id']):
        output_row = {
        'ID': '',
        'Series': 'ACC-PAY-.YYYY.-',
        'Payment Type': 'Receive',
        'Posting Date': posting_date,
        'Company': 'Srinath Collective',
        'Account Paid From': 'Debtors - SC',
        'Account Currency (From)': 'INR',
        'Account Paid To': format_particulars1(row),
        'Account Currency (To)': 'INR',
        'Paid Amount': row['Amount'] if pd.notnull(row.get('Amount', None)) else 0,
        'Source Exchange Rate': 1,
        'Received Amount': row['Amount'] if pd.notnull(row.get('Amount', None)) else 0,
        'Target Exchange Rate': 1,
        'Cheque/Reference No': row['Transaction id'],
        'Custom Remarks': custom_remarks,
        'Remarks': remarks,
        'Party Type': 'Customer',
        'Party': row['Customer Id']
        }
        output_rows.append(output_row)
    elif pd.notnull(row['Vendor Id']):
        output_row = {
        'ID': '',
        'Series': 'ACC-PAY-.YYYY.-',
        'Payment Type': 'Receive',
        'Posting Date': posting_date,
        'Company': 'Srinath Collective',
        'Account Paid From': 'Creditors - SC',
        'Account Currency (From)': 'INR',
        'Account Paid To': format_particulars1(row),
        'Account Currency (To)': 'INR',
        'Paid Amount': row['Amount'] if pd.notnull(row.get('Amount', None)) else 0,
        'Source Exchange Rate': 1,
        'Received Amount': row['Amount'] if pd.notnull(row.get('Amount', None)) else 0,
        'Target Exchange Rate': 1,
        'Cheque/Reference No': row['Transaction id'],
        'Custom Remarks': custom_remarks,
        'Remarks': remarks,
        'Party Type': 'Supplier',
        'Party': row['Vendor Id']
        }
        output_rows.append(output_row)
    else:
        if pd.isnull(row['Ledger Id']) or str(row['Ledger Id']).strip() == '':
            with open('missing_ledger_ids.txt', 'a') as f:
                f.write(f"{row['Transaction id']}\n")
            print(f"Skipping row {idx} due to missing Ledger Id.")
            continue
        output_row = {
        'ID': '',
        'Series': 'ACC-PAY-.YYYY.-',
        'Payment Type': 'Internal Transfer',
        'Posting Date': posting_date,
        'Company': 'Srinath Collective',
        'Account Paid From': format_particulars(row),
        'Account Currency (From)': 'INR',
        'Account Paid To': format_particulars1(row),
        'Account Currency (To)': 'INR',
        'Paid Amount': row['Amount'] if pd.notnull(row.get('Amount', None)) else 0,
        'Source Exchange Rate': 1,
        'Received Amount': row['Amount'] if pd.notnull(row.get('Amount', None)) else 0,
        'Target Exchange Rate': 1,
        'Cheque/Reference No': row['Transaction id'],
        'Custom Remarks': custom_remarks,
        'Remarks': remarks
        }
        output_rows.append(output_row)

correct_account_map = [('SSWAL005475 - Mobile and Telephone Charges - SC','SSWAL005475 - MOBILE AND TELEPHONE CHARGES - SC'),
('SSWAL135913 - Shashikiran J M (Staff Adv) - SC','SSWAL135913 - SHASHIKIRAN J M (STAFF ADV) - SC')]


# Convert to DataFrame
output_df = pd.DataFrame(output_rows)

# Apply the correct account mappings to the output DataFrame
for original, corrected in correct_account_map:
    # Update Account Paid From column
    output_df['Account Paid From'] = output_df['Account Paid From'].replace(original, corrected)
    
    # Update Account Paid To column
    output_df['Account Paid To'] = output_df['Account Paid To'].replace(original, corrected)

# Save to Excel
output_file = 'output_receipt_voucher_delta.csv'
output_df.to_csv(output_file, index=False)
print(f"Successfully saved to: {output_file}")