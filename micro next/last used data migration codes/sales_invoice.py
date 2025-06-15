import csv
import pandas as pd
from datetime import datetime

# Update the desired headers to match the new order
desired_headers = [
    "ID", "Company", "Date", "Currency", "Exchange Rate", "Price List", "Price List Currency", "Price List Exchange Rate", "Debit To", "Customer", "Ignore Pricing Rule", "Cost Center (Items)", "Income Account (Items)", "Price List Rate (Items)", "UOM (Items)", "UOM Conversion Factor (Items)", "Discount (%) on Price List Rate with Margin (Items)", "Item (Items)", "SGST Rate (Items)", "CGST Rate (Items)", "Quantity (Items)", "Account Head (Sales Taxes and Charges)","Amount (Sales Taxes and Charges)", "Type (Sales Taxes and Charges)", "Tax Rate (Sales Taxes and Charges)", "Description (Sales Taxes and Charges)", "GST Tax Type (Sales Taxes and Charges)", "Sales Person (Sales Contributions and Incentives)", "Contribution (%) (Sales Contributions and Incentives)"
]

# Mapping of input file headers to desired headers
header_mapping = {
    "Invoice No": "ID",
    "Customer Id": "Customer",
    "Selling Price": "Price List Rate (Items)",
    "Discount (%)": "Discount (%) on Price List Rate with Margin (Items)",
    "Variation id": "Item (Items)",
    "Quantity": "Quantity (Items)",
    "Sales Person": "Sales Person (Sales Contributions and Incentives)",
    "Unit": "UOM (Items)",
    "Date": "Date",
    "Tax": "SGST Rate (Items)",
}

# Input and output file paths
input_file_unorder = "sales.csv"
output_file = "outputSI.csv"
charges_file = "Sales Register.xlsx"  # Assuming this is the file with charge values

# Read the charges Excel file to create a lookup dictionary
def get_charge_values():
    try:
        charges_df = pd.read_excel(charges_file)
        # Create a dictionary mapping Invoice No to Charge Value
        charge_lookup = dict(zip(charges_df['Invoice Number'], charges_df['Charge Value']))
        return charge_lookup
    except Exception as e:
        print(f"Error reading charges file: {e}")
        return {}

# Read the CSV
df = pd.read_csv(input_file_unorder)

# Sort by Voucher No, Date, Item Name
# (Adjust columns based on your actual CSV — for example 'Date', 'Item Name', etc.)
df_sorted = df.sort_values(by=['Invoice No'])

# Save the sorted file
output_path = 'fixed_input.csv'
df_sorted.to_csv(output_path, index=False)
input_file = output_path

# Read the input CSV and write to the output CSV with desired headers
def transform_csv():
    # Get charge values from the additional Excel sheet
    charge_lookup = get_charge_values()
    
    with open(input_file, mode='r', newline='', encoding='utf-8') as infile, \
         open(output_file, mode='w', newline='', encoding='utf-8') as outfile:

        reader = csv.DictReader(infile)
        # Ensure the writer uses the updated headers
        writer = csv.DictWriter(outfile, fieldnames=desired_headers)

        # Write the desired headers to the output file
        writer.writeheader()

        # Load sales person names from sales_person.txt
        with open('sales_person.txt', 'r', encoding='utf-8') as sp_file:
            sales_persons = set(line.strip() for line in sp_file if line.strip())

        # Track seen IDs to handle duplicates
        seen_ids = set()

        for row in reader:
            new_row = {desired: row.get(original, "") for original, desired in header_mapping.items()}

            # Convert date format from dd-mm-yyyy to yyyy-mm-dd
            if "Date" in new_row and new_row["Date"]:
                try:
                    parsed_date = datetime.strptime(new_row["Date"], "%d-%b-%y")
                    new_row["Date"] = parsed_date.strftime("%Y-%m-%d")
                except ValueError as e:
                    print(f"Date parsing failed for value: {new_row['Date']} - Error: {e}")
            
            # Modify the Item (Items) column to remove the prefix and keep only the numeric part
            if "Item (Items)" in new_row and new_row["Item (Items)"]:
                new_row["Item (Items)"] = new_row["Item (Items)"].lstrip("SSWIG0")

            #Modify SGST Rate (Items) and CGST Rate (Items) to take value from tax column on input csv and divide by 2
            if "SGST Rate (Items)" in new_row and new_row["SGST Rate (Items)"]:
                new_row["SGST Rate (Items)"] = str(float(new_row["SGST Rate (Items)"]) / 2)
                new_row["CGST Rate (Items)"] = new_row["SGST Rate (Items)"]

            # Modify the Quantity (Items) column to keep only the numeric part before any text appears
            if "Quantity (Items)" in new_row and new_row["Quantity (Items)"]:
                new_row["Quantity (Items)"] = ''.join(c for c in new_row["Quantity (Items)"] if c.isdigit() or c == ' ').split()[0]

            if "UOM (Items)" in new_row:
                new_row["UOM (Items)"] = "Pcs"

            # Check and update Sales Person (Sales Contributions and Incentives)
            if "Sales Person (Sales Contributions and Incentives)" in new_row:
                sales_person = new_row["Sales Person (Sales Contributions and Incentives)"]
                if sales_person not in sales_persons:
                    new_row["Sales Person (Sales Contributions and Incentives)"] = "Micronxt"

            # Add constant values
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
            })

            # Handle duplicate IDs
            current_id = new_row.get("ID", "")
            if current_id in seen_ids:
                for column in [
                    "ID", "Company", "Date", "Currency", "Exchange Rate", "Price List", "Price List Currency", 
                    "Price List Exchange Rate", "Debit To", "Customer", "Ignore Pricing Rule", "Cost Center (Items)", 
                    "Income Account (Items)", "Account Head (Sales Taxes and Charges)", "Type (Sales Taxes and Charges)", 
                    "Tax Rate (Sales Taxes and Charges)", "Description (Sales Taxes and Charges)", 
                    "GST Tax Type (Sales Taxes and Charges)", "Sales Person (Sales Contributions and Incentives)", 
                    "Contribution (%) (Sales Contributions and Incentives)","Amount (Sales Taxes and Charges)"
                ]:
                    new_row[column] = ""
            else:
                seen_ids.add(current_id)
                    # Add a row for SGST with all columns populated
                row_sgst = new_row.copy()
                row_sgst.update({
                    "Account Head (Sales Taxes and Charges)": "Output Tax SGST - SC",
                    "Type (Sales Taxes and Charges)": "On Net Total",
                    "Tax Rate (Sales Taxes and Charges)": "9",
                    "Description (Sales Taxes and Charges)": "SGST",
                    "GST Tax Type (Sales Taxes and Charges)": "sgst"
                })
                writer.writerow(row_sgst)
                # Add a row for CGST with only the specified columns populated
                row_cgst = {
                    "Account Head (Sales Taxes and Charges)": "Output Tax CGST - SC",
                    "Type (Sales Taxes and Charges)": "On Net Total",
                    "Tax Rate (Sales Taxes and Charges)": "9",
                    "Description (Sales Taxes and Charges)": "CGST",
                    "GST Tax Type (Sales Taxes and Charges)": "cgst"
                }
                writer.writerow(row_cgst)
                charge_value = charge_lookup.get(current_id, None)
                row_additional = {field: "" for field in desired_headers}
                if charge_value is not None and not pd.isna(charge_value) and charge_value != 0 and str(charge_value).strip():
                    row_additional.update({
                        "Price List Rate (Items)": str(charge_value),
                        "UOM (Items)": "Nos",
                        "UOM Conversion Factor (Items)": "1",
                        "Discount (%) on Price List Rate with Margin (Items)": "0",
                        "Item (Items)": "Sales-Expense",
                        "SGST Rate (Items)": "9",
                        "CGST Rate (Items)": "9",
                        "Quantity (Items)": "1"
                    })
                    writer.writerow(row_additional)

                

                continue  # Skip writing the original row to avoid duplication

            writer.writerow(new_row)

if __name__ == "__main__":
    transform_csv()
    print(f"Transformed CSV file has been saved as {output_file}.")
