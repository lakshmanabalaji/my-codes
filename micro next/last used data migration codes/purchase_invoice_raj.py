import csv
import pandas as pd
import os
from datetime import datetime

# Desired headers to match ERPNext purchase invoice format
desired_headers = [
    "ID", "Supplier", "Date", "Credit To", "Company", "Supplier GSTIN", "Supplier Invoice No", 
    "Supplier Invoice Date", "Set Accepted Warehouse", "Ignore Pricing Rule", "Accepted Qty (Items)", 
    "UOM (Items)", "UOM Conversion Factor (Items)", "Accepted Warehouse (Items)", 
    "Discount on Price List Rate (%) (Items)", "Item (Items)", "Price List Rate (Items)", 
    "Account Head (Purchase Taxes and Charges)", "Add or Deduct (Purchase Taxes and Charges)", 
    "Type (Purchase Taxes and Charges)", "Tax Rate (Purchase Taxes and Charges)", 
    "Description (Purchase Taxes and Charges)", "Consider Tax or Charge for (Purchase Taxes and Charges)",
    "Type", "Test"
]

# Mapping input headers to output headers
header_mapping = {
    "Invoice No": "ID",
    "Vendor ID": "Supplier",
    "Price": "Price List Rate (Items)",
    "Variation Id": "Item (Items)",
    "Quantity": "Accepted Qty (Items)",
    "InvoiceDate": "Date",
    "Tax": "Tax Rate (Purchase Taxes and Charges)",
    "Invoice No": "Supplier Invoice No",
    "Discount": "Discount on Price List Rate (%) (Items)",
    "PurchaseType": "Type",
    "OverAllDiscount": "Test"
}

# File paths
input_file = "item Wise purchaseexport from April and May.csv"
output_file = "output_purchase invoice_delta.csv"

# Main processing function
def transform_csv():
    file_extension = os.path.splitext(input_file)[1].lower()

    if file_extension == '.xlsx':
        df = pd.read_excel(input_file)
    else:
        df = pd.read_csv(input_file, encoding='utf-8')

    input_data = df.to_dict('records')

    with open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=desired_headers)
        writer.writeheader()

        seen_ids = set()

        for row in input_data:
            row = {k: ('' if pd.isna(v) else str(v)) for k, v in row.items()}
            current_id = str(row.get("Invoice No", "")).strip()

            new_row = {desired: row.get(original, "") for original, desired in header_mapping.items()}

            # Set ID to Supplier Invoice No for output
            new_row["ID"] = new_row.get("Supplier Invoice No", "")

            if "Item (Items)" in new_row and new_row["Item (Items)"]:
                new_row["Item (Items)"] = new_row["Item (Items)"].lstrip("SSWIG0")

            if new_row.get("Discount on Price List Rate (%) (Items)") == "0.0" and new_row.get("Test"):
                new_row["Discount on Price List Rate (%) (Items)"] = new_row["Test"]

            if "Date" in new_row and new_row["Date"]:
                try:
                    try:
                        parsed_date = datetime.strptime(new_row["Date"], "%d-%b-%y")
                    except ValueError:
                        parsed_date = datetime.strptime(new_row["Date"], "%Y-%m-%d %H:%M:%S")
                    new_row["Date"] = parsed_date.strftime("%Y-%m-%d")
                    new_row["Supplier Invoice Date"] = new_row["Date"]
                except ValueError as e:
                    print(f"Date parsing failed for value: {new_row['Date']} - Error: {e}")

            if "Accepted Qty (Items)" in new_row and new_row["Accepted Qty (Items)"]:
                qty_clean = ''.join(c for c in new_row["Accepted Qty (Items)"] if c.isdigit() or c == ' ').strip()
                new_row["Accepted Qty (Items)"] = qty_clean.split()[0] if qty_clean.split() else "0"


            new_row.update({
                "Company": "Srinath Collective",
                "Credit To": "Creditors - SC",
                "Set Accepted Warehouse": "Centralised Warehouse",
                "Accepted Warehouse (Items)": "Stores - SC",
                "Ignore Pricing Rule": "1",
                "UOM Conversion Factor (Items)": "1",
                "Type (Purchase Taxes and Charges)": "On Net Total",
            })

            if current_id in seen_ids:
                for column in [
                    "ID", "Supplier", "Date", "Credit To", "Company", "Supplier GSTIN", 
                    "Supplier Invoice No", "Supplier Invoice Date", "Set Accepted Warehouse", 
                    "Ignore Pricing Rule", "Account Head (Purchase Taxes and Charges)", 
                    "Tax Rate (Purchase Taxes and Charges)", "Description (Purchase Taxes and Charges)", 
                    "Type (Purchase Taxes and Charges)", "Add or Deduct (Purchase Taxes and Charges)",
                    "Consider Tax or Charge for (Purchase Taxes and Charges)"
                ]:
                    new_row[column] = ""
            else:
                seen_ids.add(current_id)
                current_gst = new_row.get("Type", "")

                if current_gst == "Local":
                    row_sgst = new_row.copy()
                    row_sgst.update({
                        "Account Head (Purchase Taxes and Charges)": "Input Tax SGST - SC",
                        "Tax Rate (Purchase Taxes and Charges)": "9",
                        "Description (Purchase Taxes and Charges)": "SGST",
                        "Add or Deduct (Purchase Taxes and Charges)": "Add",
                        "Consider Tax or Charge for (Purchase Taxes and Charges)": "Total"
                    })
                    writer.writerow(row_sgst)

                    row_cgst = {
                        "Account Head (Purchase Taxes and Charges)": "Input Tax CGST - SC",
                        "Type (Purchase Taxes and Charges)": "On Net Total",
                        "Tax Rate (Purchase Taxes and Charges)": "9",
                        "Description (Purchase Taxes and Charges)": "CGST",
                        "Add or Deduct (Purchase Taxes and Charges)": "Add",
                        "Consider Tax or Charge for (Purchase Taxes and Charges)": "Total"
                    }

                    if "Type" in new_row:
                        del new_row["Type"]

                    writer.writerow(row_cgst)
                    continue

                elif current_gst == "Interstate":
                    row_igst = new_row.copy()
                    row_igst.update({
                        "Account Head (Purchase Taxes and Charges)": "Input Tax IGST - SC",
                        "Tax Rate (Purchase Taxes and Charges)": "18",
                        "Description (Purchase Taxes and Charges)": "IGST",
                        "Add or Deduct (Purchase Taxes and Charges)": "Add",
                        "Consider Tax or Charge for (Purchase Taxes and Charges)": "Total"
                    })

                    if "Type" in new_row:
                        del new_row["Type"]

                    writer.writerow(row_igst)
                    continue

                if "Type" in new_row:
                    del new_row["Type"]

            writer.writerow(new_row)

# Entry point
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    transform_csv()
    print(f"Transformed CSV file has been saved as {output_file}.")
