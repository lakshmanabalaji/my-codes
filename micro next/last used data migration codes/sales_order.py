import csv
import pandas as pd
import re
from datetime import datetime

# Desired headers for the output CSV
desired_headers = [
    "ID", "Customer", "Order Type", "Date", "Company", "Currency", "Exchange Rate", "Price List", "Price List Currency", 
    "Price List Exchange Rate", "Ignore Pricing Rule", "Item Code (Items)", "Quantity (Items)", "Price List Rate (Items)", 
    "UOM (Items)", "UOM Conversion Factor (Items)", "CGST Rate (Items)", "SGST Rate (Items)", 
    "Discount (%) on Price List Rate with Margin (Items)", "Amount (Sales Taxes and Charges)", 
    "Account Head (Sales Taxes and Charges)", "Description (Sales Taxes and Charges)", "Type (Sales Taxes and Charges)", 
    "GST Tax Type (Sales Taxes and Charges)", "Tax Rate (Sales Taxes and Charges)", "Sales Person (Sales Team)", 
    "Contribution (%) (Sales Team)", "Delivery Date"
]

# Mapping from input Excel columns to desired output headers
header_mapping = {
    "Order ID": "ID",
    "Customer ID": "Customer",
    "Price": "Price List Rate (Items)",
    "Variation Id": "Item Code (Items)",
    "Quantity": "Quantity (Items)",
    "Sales Person": "Sales Person (Sales Team)",
    "Date": "Date",
    "Tax": "SGST Rate (Items)",
    "Delivery Date": "Delivery Date",
    "Discount Price": "Discount Price",
}

# File paths
input_file = "ITEM WISE SALES ORDERS EXPORT.xlsx"
output_file = "output_june_sales_order_delta.csv"

# Reusable date parser
def format_date(date_input):
    if pd.isna(date_input):
        return ""
    try:
        # If already datetime
        if isinstance(date_input, datetime):
            return date_input.strftime("%d-%m-%Y")
        # Clean HTML or extra strings
        cleaned = re.sub(r'<.*?>', '', str(date_input)).strip()
        for fmt in ("%d %b, %Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(cleaned, fmt).strftime("%d-%m-%Y")
            except ValueError:
                continue
        return cleaned
    except:
        return ""

# Main transformation function
def transform_excel():
    df = pd.read_excel(input_file)
    df.columns = df.columns.str.strip()

    with open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=desired_headers)
        writer.writeheader()

        with open('sales_person.txt', 'r', encoding='utf-8') as sp_file:
            sales_persons = set(line.strip() for line in sp_file if line.strip())

        seen_ids = set()

        for row in df.to_dict(orient="records"):
            new_row = {desired: row.get(original, "") for original, desired in header_mapping.items()}

            # Format both dates
            if "Date" in new_row and new_row["Date"]:
                new_row["Date"] = format_date(new_row["Date"])
            if "Delivery Date" in new_row and new_row["Delivery Date"]:
                new_row["Delivery Date"] = format_date(new_row["Delivery Date"])

            # Clean item code
            if "Item Code (Items)" in new_row and new_row["Item Code (Items)"]:
                item_code = str(new_row["Item Code (Items)"])
                new_row["Item Code (Items)"] = item_code.lstrip("SSWIG0") if item_code.startswith("SSWIG0") else item_code

            # Split SGST into SGST + CGST
            if "SGST Rate (Items)" in new_row and new_row["SGST Rate (Items)"]:
                try:
                    sgst = float(new_row["SGST Rate (Items)"]) / 2
                    new_row["SGST Rate (Items)"] = str(sgst)
                    new_row["CGST Rate (Items)"] = str(sgst)
                except:
                    new_row["SGST Rate (Items)"] = ""
                    new_row["CGST Rate (Items)"] = ""

            # Clean quantity
            if "Quantity (Items)" in new_row and new_row["Quantity (Items)"]:
                new_row["Quantity (Items)"] = ''.join(c for c in str(new_row["Quantity (Items)"]) if c.isdigit() or c == ' ').split()[0]

            # Calculate discount
            if "Price List Rate (Items)" in new_row and "Discount Price" in new_row:
                try:
                    price = float(new_row["Price List Rate (Items)"]) * float(new_row["Quantity (Items)"])
                    discount_price = float(new_row["Discount Price"])
                    if price > 0 and discount_price < price:
                        discount_percent = (discount_price * 100) / price
                        new_row["Discount (%) on Price List Rate with Margin (Items)"] = str(round(discount_percent, 2))
                except:
                    pass

            # Remove helper discount column
            if "Discount Price" in new_row:
                del new_row["Discount Price"]

            # Validate Sales Person
            if new_row.get("Sales Person (Sales Team)") not in sales_persons:
                new_row["Sales Person (Sales Team)"] = "Micronxt"

            # Add default values
            new_row.update({
                "Company": "Srinath Collective",
                "Currency": "INR",
                "Exchange Rate": "1",
                "Price List": "Standard Selling",
                "Price List Currency": "INR",
                "Price List Exchange Rate": "1",
                "Ignore Pricing Rule": "1",
                "UOM Conversion Factor (Items)": "1",
                "Type (Sales Taxes and Charges)": "On Net Total",
                "Contribution (%) (Sales Team)": "100",
            })

            current_id = new_row.get("ID", "")
            if current_id in seen_ids:
                for column in [
                    "ID", "Company", "Date", "Currency", "Exchange Rate", "Price List", "Price List Currency",
                    "Price List Exchange Rate", "Customer", "Ignore Pricing Rule", "Account Head (Sales Taxes and Charges)",
                    "Tax Rate (Sales Taxes and Charges)", "Description (Sales Taxes and Charges)", "Type (Sales Taxes and Charges)",
                    "GST Tax Type (Sales Taxes and Charges)", "Sales Person (Sales Team)", "Contribution (%) (Sales Team)", "Delivery Date"
                ]:
                    new_row[column] = ""
            else:
                seen_ids.add(current_id)

                # SGST row
                row_sgst = new_row.copy()
                row_sgst.update({
                    "Account Head (Sales Taxes and Charges)": "Output Tax SGST - SC",
                    "Tax Rate (Sales Taxes and Charges)": "9",
                    "Description (Sales Taxes and Charges)": "SGST",
                    "GST Tax Type (Sales Taxes and Charges)": "sgst"
                })
                writer.writerow(row_sgst)

                # CGST row
                row_cgst = {
                    "Account Head (Sales Taxes and Charges)": "Output Tax CGST - SC",
                    "Type (Sales Taxes and Charges)": "On Net Total",
                    "Tax Rate (Sales Taxes and Charges)": "9",
                    "Description (Sales Taxes and Charges)": "CGST",
                    "GST Tax Type (Sales Taxes and Charges)": "cgst"
                }
                writer.writerow(row_cgst)

                continue  # Skip duplicate write of base row

            writer.writerow(new_row)

if __name__ == "__main__":
    transform_excel()
    print(f"Transformed CSV file has been saved as {output_file}.")
