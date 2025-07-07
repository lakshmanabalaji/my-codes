import pandas as pd

# File paths
input_file = "ITEM WISE PURCHASE ORDER REPORT APRIL TO DATE_with_ids.xlsx - Main FIle.csv"
output_file = "purchase_order_grouped_final.csv"

# Read input CSV
df = pd.read_csv(input_file)

# Define header mapping
header_mapping = {
    "Purchase Order Id": "ID",
    "Vendor ID": "Supplier",
    "Vendor": "Supplier Name",  # Optional
    "Date": "Date",
    "Variation Id": "Item Code (Items)",
    "Warehouse Name": "Warehouse",
    "Purchase person": "Purchase Person (Purchase Team)",
    "Received Qty": "quantity (Items)",
    "Quantity": "total Quantity (Items)",
    "Total Amount": "Amount (INR)",
    "Status": "Status"
}

# Rename columns
df = df.rename(columns=header_mapping)

# Add constant fields
df["Company"] = "Srinath Collective"
df["Currency"] = "INR"
df["type (Purchase Taxes and Charges)"] = "On Net Total"

# Function to expand each row
def expand_rows(row):
    base = row.copy()
    sgst = row.copy()
    cgst = row.copy()

    # Main row - no tax
    base["Account Head (Purchase Taxes and Charges)"] = ""
    base["Tax Rate (Purchase Taxes and Charges)"] = ""
    base["Description (Purchase Taxes and Charges)"] = ""
    base["GST Tax Type (Purchase Taxes and Charges)"] = ""

    # SGST row
    sgst["Account Head (Purchase Taxes and Charges)"] = "Input Tax SGST - SC"
    sgst["Tax Rate (Purchase Taxes and Charges)"] = "9"
    sgst["Description (Purchase Taxes and Charges)"] = "SGST"
    sgst["GST Tax Type (Purchase Taxes and Charges)"] = "sgst"

    # CGST row
    cgst["Account Head (Purchase Taxes and Charges)"] = "Input Tax CGST - SC"
    cgst["Tax Rate (Purchase Taxes and Charges)"] = "9"
    cgst["Description (Purchase Taxes and Charges)"] = "CGST"
    cgst["GST Tax Type (Purchase Taxes and Charges)"] = "cgst"

    return pd.DataFrame([base, sgst, cgst])

# Expand all rows
expanded_df = pd.concat([expand_rows(row) for _, row in df.iterrows()], ignore_index=True)

# Sort by ID and Item Code
expanded_df.sort_values(by=["ID", "Item Code (Items)"], inplace=True)

# Remove repeating values
expanded_df["ID"] = expanded_df["ID"].mask(expanded_df["ID"].duplicated())
expanded_df["Item Code (Items)"] = expanded_df["Item Code (Items)"].mask(expanded_df["Item Code (Items)"].duplicated(keep=False))

# Reorder final columns
final_columns = [
    "ID",
    "Supplier",
    "Date",
    "Warehouse",
    "Purchase Person (Purchase Team)",
    "quantity (Items)",
    "total Quantity (Items)",
    "Amount (INR)",
    "Item Code (Items)",
    "Company",
    "Currency",
    "type (Purchase Taxes and Charges)",
    "Account Head (Purchase Taxes and Charges)",
    "Tax Rate (Purchase Taxes and Charges)",
    "Description (Purchase Taxes and Charges)",
    "GST Tax Type (Purchase Taxes and Charges)",
    "Status"
]

# Keep only existing columns
final_columns = [col for col in final_columns if col in expanded_df.columns]
final_df = expanded_df[final_columns]

# Save to CSV
final_df.to_csv(output_file, index=False)
print("✅ Grouped output saved to:", output_file)
