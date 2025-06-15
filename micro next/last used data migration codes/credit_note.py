import csv
import pandas as pd
from datetime import datetime

# Desired output headers (removed "Credit Id + Return Date")
desired_headers = [
    "ID", "Company", "Date", "Currency", "Exchange Rate", "Price List", "Price List Currency",
    "Price List Exchange Rate", "Debit To", "Customer", "Ignore Pricing Rule", "is_return", "update_outstanding_for_self", "Cost Center (Items)",
    "Income Account (Items)", "Price List Rate (Items)", "UOM (Items)", "UOM Conversion Factor (Items)",
    "Discount (%) on Price List Rate with Margin (Items)", "Discount Amount (Items)", "Item (Items)", "SGST Rate (Items)",
    "CGST Rate (Items)", "Quantity (Items)", "Account Head (Sales Taxes and Charges)",
    "Amount (Sales Taxes and Charges)", "Type (Sales Taxes and Charges)",
    "Tax Rate (Sales Taxes and Charges)", "Description (Sales Taxes and Charges)",
    "GST Tax Type (Sales Taxes and Charges)", "Sales Person (Sales Contributions and Incentives)",
    "Contribution (%) (Sales Contributions and Incentives)", "Item Tax Template (Items)"
]

# Mapping input file headers to the desired headers
header_mapping = {
    "KEY ID": "ID",
    "Customer ID": "Customer",
    "Price": "Price List Rate (Items)",
    "Discount (%)": "Discount (%) on Price List Rate with Margin (Items)",
    "Discount Price": "Discount Amount (Items)",
    "Variation Id": "Item (Items)",
    "Quantity": "Quantity (Items)",
    "Sales Person": "Sales Person (Sales Contributions and Incentives)",
    "Unit": "UOM (Items)",
    "Invoice Date": "Date",
    "Tax": "SGST Rate (Items)",
}

# File paths
input_file_unorder = "Item wise Credit note april and may.xlsx"
output_file = "output11 delta.csv"

# Preprocess: Read and sort input file
df = pd.read_excel(input_file_unorder, dtype=str)

# Normalize and check column names
df.columns = df.columns.str.strip().str.upper()
print("Normalized Columns:", df.columns.tolist())

if 'KEY ID' not in df.columns:
    raise KeyError("'KEY ID' column not found in the input file. Please check your Excel sheet headers.")

df_sorted = df.sort_values(by=['KEY ID'])

output_path = 'fixed_input.csv'
df_sorted.to_csv(output_path, index=False)
input_file = output_path

tax_template_mapping = {
    "0": "Nil-Rated - SC",
    "5": "GST 5% - SC",
    "12": "GST 12% - SC",
    "28": "GST 28% - SC"
}

def transform_csv():
    def safe_float(val):
        """Convert a string to float safely, defaulting to 0.0 if empty or invalid."""
        val = ''.join(filter(lambda x: x.isdigit() or x == '.', str(val)))
        return float(val) if val else 0.0

    with open(input_file, mode='r', newline='', encoding='utf-8') as infile, \
         open(output_file, mode='w', newline='', encoding='utf-8') as outfile:

        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=desired_headers)
        writer.writeheader()

        seen_keys = set()

        for row in reader:
            new_row = {}
            for original, desired in header_mapping.items():
                value = row.get(original.upper(), "")
                if desired == "ID" and value:
                    value = value[6:]
                new_row[desired] = value

            if "Date" in new_row and new_row["Date"]:
                date_str = new_row["Date"].split()[0]
                for fmt in ("%d-%b-%y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
                    try:
                        parsed_date = datetime.strptime(date_str, fmt)
                        new_row["Date"] = parsed_date.strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        continue
                else:
                    print(f"Date parsing failed for value: {new_row['Date']}")

            if "Item (Items)" in new_row and new_row["Item (Items)"]:
                new_row["Item (Items)"] = ''.join(filter(str.isdigit, new_row["Item (Items)"]))

            tax_val = (row.get("TAX") or "").strip()
            new_row["Item Tax Template (Items)"] = tax_template_mapping.get(tax_val, "")

            if "SGST Rate (Items)" in new_row and new_row["SGST Rate (Items)"]:
                try:
                    rate = float(new_row["SGST Rate (Items)"]) / 2
                    new_row["SGST Rate (Items)"] = str(rate)
                    new_row["CGST Rate (Items)"] = str(rate)
                except ValueError:
                    new_row["SGST Rate (Items)"] = ""
                    new_row["CGST Rate (Items)"] = ""

                new_row["Quantity (Items)"] = "-" + new_row["Quantity (Items)"]

            price_str = new_row.get("Price List Rate (Items)") or "0"
            discount_str = new_row.get("Discount Amount (Items)") or "0"
            qty_str = new_row.get("Quantity (Items)") or "0"

            try:
                price = safe_float(price_str)
                discount_amt = safe_float(discount_str)
                qty = safe_float(qty_str)

                if price > 0 and discount_amt > 0 and qty > 0:
                    discount_per_unit = discount_amt / qty
                    discount_percent = (discount_per_unit / price) * 100
                    new_row["Discount (%) on Price List Rate with Margin (Items)"] = f"{discount_percent:.2f}"
                else:
                    new_row["Discount (%) on Price List Rate with Margin (Items)"] = ""

                # Optional debug print if data is missing
                if not price_str.strip() or not discount_str.strip() or not qty_str.strip():
                    print(f"Missing data in row ID {new_row.get('ID')}: price='{price_str}', discount='{discount_str}', qty='{qty_str}'")
            except Exception as e:
                print(f"Failed to calculate discount for row ID {new_row.get('ID')}: {e}")
                new_row["Discount (%) on Price List Rate with Margin (Items)"] = ""

            # Default values
            new_row["UOM (Items)"] = "Pcs"
            new_row["Sales Person (Sales Contributions and Incentives)"] = "Micronxt"

            new_row.update({
                "Company": "Srinath Collective",
                "Currency": "INR",
                "Exchange Rate": "1",
                "Price List": "Standard Selling",
                "Price List Currency": "INR",
                "Price List Exchange Rate": "1",
                "Debit To": "Debtors - SC",
                "Ignore Pricing Rule": "1",
                "Cost Center (Items)": "Main - SC",
                "Income Account (Items)": "Sales - SC",
                "UOM Conversion Factor (Items)": "1",
                "Type (Sales Taxes and Charges)": "On Net Total",
                "Contribution (%) (Sales Contributions and Incentives)": "100",
                "is_return": "1",
                "update_outstanding_for_self": "1"
            })

            key_id = (row.get("KEY ID") or row.get("Key Id") or "").strip()
            if key_id in seen_keys:
                for column in [
                    "ID", "Company", "Date", "Currency", "Exchange Rate", "Price List", "Price List Currency",
                    "Price List Exchange Rate", "Debit To", "Customer", "Ignore Pricing Rule", "Cost Center (Items)",
                    "Income Account (Items)", "Account Head (Sales Taxes and Charges)", "Type (Sales Taxes and Charges)",
                    "Tax Rate (Sales Taxes and Charges)", "Description (Sales Taxes and Charges)",
                    "GST Tax Type (Sales Taxes and Charges)", "Sales Person (Sales Contributions and Incentives)",
                    "Contribution (%) (Sales Contributions and Incentives)", "Amount (Sales Taxes and Charges)",
                    "is_return", "update_outstanding_for_self"
                ]:
                    new_row[column] = ""
            else:
                seen_keys.add(key_id)

                row_sgst = new_row.copy()
                row_sgst.update({
                    "Account Head (Sales Taxes and Charges)": "Output Tax SGST - SC",
                    "Type (Sales Taxes and Charges)": "On Net Total",
                    "Tax Rate (Sales Taxes and Charges)": "9",
                    "Description (Sales Taxes and Charges)": "SGST",
                    "GST Tax Type (Sales Taxes and Charges)": "sgst"
                })
                writer.writerow(row_sgst)

                row_cgst = {
                    "Account Head (Sales Taxes and Charges)": "Output Tax CGST - SC",
                    "Type (Sales Taxes and Charges)": "On Net Total",
                    "Tax Rate (Sales Taxes and Charges)": "9",
                    "Description (Sales Taxes and Charges)": "CGST",
                    "GST Tax Type (Sales Taxes and Charges)": "cgst"
                }
                for col in desired_headers:
                    row_cgst.setdefault(col, "")
                writer.writerow(row_cgst)
                continue

            writer.writerow(new_row)


if __name__ == "__main__":
    transform_csv()
    print(f"Transformed CSV file has been saved as {output_file}.")
