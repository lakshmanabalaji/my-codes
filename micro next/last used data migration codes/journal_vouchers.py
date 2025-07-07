import pandas as pd

# Load the input file
input_path = "updated_file.csv"
df = pd.read_csv(input_path)

# Drop unnecessary columns if they exist
columns_to_drop = ["Created Time", "Updated Time", "Created User", "Updated User"]
df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])

# Rename columns (exclude accountid and particulars so we can use both)
column_mapping = {
    "Voucher Id": "ID",
    "Voucher Type": "Entry Type",
    "Voucher Number": "Bill No",
    "Date": "Posting Date",
    "Narration": "User Remark",
    "Reference NO.": "Reference Number",
    "SubType": "Party Type (Accounting Entries)",
    "Doc No.": "Party (Accounting Entries)",
    "Credit": "Credit (Accounting Entries)",
    "Debit": "Debit (Accounting Entries)"
}
df = df.rename(columns=column_mapping)

# Add static columns
df["ID (Accounting Entries)"] = None
df["Company"] = "Srinath Collective"
df["Entry Type"] = "Journal Entry"
df["Series"] = "ACC-JV-.YYYY.-"
df["Company GSTIN"] = "29AAIFS5015M1ZS"

# Apply party/account logic
def apply_party_account_logic(row):
    if pd.notna(row.get("Customer ID")):
        party_type = "Customer"
        party = row["Customer ID"]
        account = "Debtors - SC"
    elif pd.notna(row.get("Vendor ID")):
        party_type = "Supplier"
        party = row["Vendor ID"]
        account = "Creditors - SC"
    elif pd.notna(row.get("Ledger ID")) and pd.notna(row.get("Particulars")):
        party_type = None
        party = None
        account = f"{row['Ledger ID']} - {row['Particulars']} - SC"
    else:
        party_type = None
        party = None
        account = None

    return pd.Series([party_type, party, account])

# Assign computed fields
df[["Party Type (Accounting Entries)", "Party (Accounting Entries)", "Account (Accounting Entries)"]] = df.apply(apply_party_account_logic, axis=1)

# Format Posting Date
df["Posting Date"] = pd.to_datetime(df["Posting Date"]).dt.strftime('%Y-%m-%d')

# Final column order
column_order = [
    "ID", "Entry Type", "Series", "Company", "Company GSTIN", "Posting Date",
    "User Remark", "Reference Number", "Bill No",
    "ID (Accounting Entries)", "Account (Accounting Entries)",
    "Party Type (Accounting Entries)", "Party (Accounting Entries)",
    "Credit (Accounting Entries)", "Debit (Accounting Entries)"
]

# Group by Bill No and format for Frappe import
final_rows = []
grouped = df.groupby("Bill No", sort=False)

for _, group in grouped:
    first_row = True
    for _, row in group.iterrows():
        row_data = row[column_order].copy()
        if not first_row:
            row_data["ID"] = ""
            row_data["Entry Type"] = ""
            row_data["Series"] = ""
            row_data["Company"] = ""
            row_data["Posting Date"] = ""
            row_data["User Remark"] = ""
            row_data["Reference Number"] = ""
            row_data["Bill No"] = ""
            row_data["Company GSTIN"] = ""
        final_rows.append(row_data)
        first_row = False

# Save final output
final_df = pd.DataFrame(final_rows, columns=column_order)
output_path = "Journal Vouchers delta Output final.xlsx"
final_df.to_excel(output_path, index=False)

print(f"File saved as: {output_path}")
