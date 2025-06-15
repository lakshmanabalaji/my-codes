import pandas as pd

# Load client input file
input_file = 'PAYMENT VOUCHERS - APRIL 2025 & MAY 2025_with_ids_pymnt.xlsx'  # Replace with your actual file
output_file = 'output_payment_vouchers_delta.csv'
df = pd.read_excel(input_file)

# Clean and normalize data
# Add Date column conversion for output Posting Date

def clean_currency(value):
    if isinstance(value, str):
        # Remove currency symbol, commas, and extra spaces
        return value.replace('₹', '').replace(',', '').strip()
    return value
# Clean the 'Amount' column
df['Amount'] = df['Amount'].apply(clean_currency)
# Convert Date column to datetime for formatting
if 'Date' in df.columns:
    # Specify the input format to match '15 Apr, 2025'
    df['Date'] = pd.to_datetime(df['Date'], format='%d %b, %Y', errors='coerce')

# Helper function to format particulars with Ledger ID, excluding prefix if Ledger ID is #NA or missing
def format_particulars(row):
    ledger_id = str(row['Ledger ID']) if pd.notnull(row['Ledger ID']) else ''
    particulars = str(row['Ledger']) if pd.notnull(row['Ledger']) else ''
    
    if ledger_id.strip().upper() == '#NA' or ledger_id.strip() == '':
        return f"{particulars} - SC"
    else:
        return f"{ledger_id} - {particulars} - SC"

def format_particulars1(row):
    payment_ledger_id = str(row['Payment Ledger Id']) if pd.notnull(row['Payment Ledger Id']) else ''
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
    # Format Posting Date as dd-mm-yyyy
    posting_date = row['Date'].strftime('%d-%m-%Y') if pd.notnull(row['Date']) else ''
    remarks = row['narration'] if 'narration' in df.columns and pd.notnull(row['narration']) else ''
    custom_remarks = '0' if pd.isna(remarks) or str(remarks).strip() == '' else '1'
    #Add a condition to check if the Customer ID is not null
    if pd.notnull(row['Customer Id']):
        output_row = {
        'ID': '',
        'Series': 'ACC-PAY-.YYYY.-',
        'Payment Type': 'Pay',
        'Posting Date': posting_date,
        'Company': 'Srinath Collective',
        'Account Paid From': format_particulars1(row),
        'Account Currency (From)': 'INR',
        'Account Paid To': 'Debtors - SC',
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
        'Payment Type': 'Pay',
        'Posting Date': posting_date,
        'Company': 'Srinath Collective',
        'Account Paid From': format_particulars1(row),
        'Account Currency (From)': 'INR',
        'Account Paid To': 'Creditors - SC',
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
        if pd.isnull(row['Ledger ID']) or str(row['Ledger ID']).strip() == '':
            # enter this Ledger ID in a txt file
            with open('missing_ledger_ids.txt', 'a') as f:
                f.write(f"{row['Transaction id']}\n")
            print(f"Skipping row {idx} due to missing Ledger ID.")
            continue
        output_row = {
        'ID': '',
        'Series': 'ACC-PAY-.YYYY.-',
        'Payment Type': 'Internal Transfer',
        'Posting Date': posting_date,
        'Company': 'Srinath Collective',
        'Account Paid From': format_particulars1(row),
        'Account Currency (From)': 'INR',
        'Account Paid To': format_particulars(row),
        'Account Currency (To)': 'INR',
        'Paid Amount': row['Amount'] if pd.notnull(row.get('Amount', None)) else 0,
        'Source Exchange Rate': 1,
        'Received Amount': row['Amount'] if pd.notnull(row.get('Amount', None)) else 0,
        'Target Exchange Rate': 1,
        'Cheque/Reference No': row['Transaction id'],
        'Custom Remarks': custom_remarks,
        'Remarks': remarks,
        }
        output_rows.append(output_row)
    

# Convert to DataFrame
output_df = pd.DataFrame(output_rows)

correct_account_map = [
    ('SSWAL005898 - Salaries Payable - SC', 'SSWAL005898 - SALARIES PAYABLE - SC'),
    ('SSWAL005902 - Office Expenses - SC', 'SSWAL005902 - OFFICE EXPENSES - SC'),
    ('SSWAL006124 - INDUMATHI P - (STAFF ADVANCE) - SC', 'SSWAL006124 - 42-INDUMATHI P - (STAFF ADVANCE) - SC'),
    ('SSWAL006140 - Petrol / Diesel - SC', 'SSWAL006140 - PETROL / DIESEL - SC'),
    ('SSWAL134836 - Loading / Unloading Charges Payable - SC', 'SSWAL134836 - LOADING / UNLOADING CHARGES PAYABLE - SC'),
    ('SSWAL135747 - Salary on Hold - SC', 'SSWAL135747 - SALARY ON HOLD - SC'),
    ('SSWAL135795 - SARASWATHI (STAFF ADV) - SC', 'SSWAL135795 - 70-SARASWATHI (STAFF ADV) - SC'),
    ('SSWAL135879 - SHANKAR K (STAFF ADV) - SC', 'SSWAL135879 - 27-SHANKAR K (STAFF ADV) - SC'),
    ('SSWAL139724 - KIRAN KUMAR V - STAFF ADVANCE - SC', 'SSWAL139724 - 05-KIRAN KUMAR V - STAFF ADVANCE - SC'),
    ('SSWAL139727 - RAVI KUMAR M H - STAFF ADVANCE - SC', 'SSWAL139727 - 34-RAVI KUMAR M H - STAFF ADVANCE - SC'),
    ('SSWAL144841 - SHIVAGAMI - STAFF ADVANCE - SC', 'SSWAL144841 - 69-SHIVAGAMI - STAFF ADVANCE - SC'),
    ('SSWAL144843 - SRINIVAS MURTHY - STAFF ADVANCE - SC', 'SSWAL144843 - 78-SRINIVAS MURTHY - STAFF ADVANCE - SC'),
    ('SSWAL151538 - KARIYAPPA - STAFF ADVANCE - SC', 'SSWAL151538 - 14-KARIYAPPA - STAFF ADVANCE - SC'),
    ('SSWAL151814 - UMESH N C (STAFF ADVANCE) - SC', 'SSWAL151814 - 114-UMESH N C (STAFF ADVANCE) - SC'),
    ('SSWAL152181 - MANOJ (STAFF ADVANCE) - SC', 'SSWAL152181 - 121-MANOJ (STAFF ADVANCE) - SC'),
    ('SSWAL153894 - SURESH B ( STAFF ADVANCE) - SC', 'SSWAL153894 - 90-SURESH B ( STAFF ADVANCE) - SC'),
    ('SSWAL154811 - MANUKUMAR - STAFF ADVANCE - SC','SSWAL154811 - 76-MANUKUMAR - STAFF ADVANCE - SC'),
    ('SSWAL155009 - KIRAN KUMAR - STAFF ADVANCE - SC','SSWAL155009 - 93-KIRAN KUMAR - STAFF ADVANCE - SC'),
    ('SSWAL155018 - JAGADISH R - STAFF ADVANCE - SC','SSWAL155018 - 44-JAGADISH R - STAFF ADVANCE - SC'),
    ('SSWAL155917 - NAVEEN S - STAFF ADVANCE - SC','SSWAL155917 - 106 - NAVEEN S - STAFF ADVANCE - SC'),
    ('SSWAL156538 - KUMAR SWAMY R - SC','SSWAL156538 - 143-KUMAR SWAMY R - SC'),
    ('SSWAL159544 - APPAIAH V ( STAFF ADVANCE) - SC','SSWAL159544 - 142-APPAIAH V ( STAFF ADVANCE) - SC'),
    ('STANDARD CHARTERED BANK - BILL DISCOUNT - SC','SSWAL165842 - STANDARD CHARTERED BANK (OD) - BILL DISCOUNT - SC')
]

# Apply the correct account mappings to the output DataFrame
for original, corrected in correct_account_map:
    # Update Account Paid From column
    output_df['Account Paid From'] = output_df['Account Paid From'].replace(original, corrected)
    
    # Update Account Paid To column
    output_df['Account Paid To'] = output_df['Account Paid To'].replace(original, corrected)


# Save to Excel
output_df.to_csv(output_file, index=False)

print(f"Successfully saved to: {output_file}")