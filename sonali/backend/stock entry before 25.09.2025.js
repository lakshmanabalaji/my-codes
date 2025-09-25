import frappe
import time

@frappe.whitelist()
def create_and_submit_stock_entry(item_code, weight):
    item_kg = find_kg_item(item_code)
    company = "Sonali Wires LLP"
    try:
        if item_kg:
            doc = frappe.get_doc({
                "doctype": "Stock Entry",
                "stock_entry_type": "Repack",
                "company": company,
                "items": [
                    {
                        "item_code": item_kg,
                        "qty": weight,
                        "s_warehouse": "Stores - S"
                    },
                    {
                        "item_code": item_code,
                        "qty": 1,
                        "t_warehouse": "Stores - S"
                    }
                ]
            })
            doc.insert(ignore_permissions=True)  # Insert into Draft state
            doc.submit()  # Submit the document

            # Fetch Generated Serial Number
            serial_nos = []
            attempts = 0
            while attempts < 5:
                serial_nos = frappe.db.get_list(
                    "Serial No",
                    filters={"item_code": item_code, "purchase_document_no": doc.name},
                    pluck="name"
                )
                if serial_nos:  # If serial number found, break the loop
                    break
                time.sleep(0.3)  # Wait for 0.3 seconds before retrying
                attempts += 1

            return {"name": doc.name, "status": "Submitted", "serial_numbers": serial_nos}
        else:
            return {"error": f"No KG item found for {item_code}"}
    except Exception as e:
        frappe.log_error(f"Stock Entry Error: {str(e)}")
        return {"error": str(e)}



@frappe.whitelist()
def find_kg_item(item_code):
    possible_kg_codes = [
        f"{item_code}-KG",
        f"{item_code} - KG"
    ]
    for code in possible_kg_codes:
        kg_item = frappe.db.get_value(
            "Item",
            {
                "item_code": ["like", f"%{code}%"],"disabled": 0,
            },
            "item_code"
        )
        if kg_item:
            return kg_item
    return None


@frappe.whitelist()
def create_and_submit_stock_entry_meter(item_code, length):
    meter_item = find_meter_item(item_code)
    try:
        if meter_item:
            doc = frappe.get_doc({
                "doctype": "Stock Entry",
                "stock_entry_type": "Repack",
                "items": [
                    {
                        "item_code": meter_item,
                        "qty": length,
                        "s_warehouse": "Stores - S"
                    },
                    {
                        "item_code": item_code,
                        "qty": 1,
                        "t_warehouse": "Stores - S"
                    }
                ]
            })
            doc.insert(ignore_permissions=True)  # Insert into Draft state
            doc.submit()  # Submit the document

            # Fetch Generated Serial Number
            serial_nos = []
            attempts = 0
            while attempts < 5:
                serial_nos = frappe.db.get_list(
                    "Serial No",
                    filters={"item_code": item_code, "purchase_document_no": doc.name},
                    pluck="name"
                )
                if serial_nos:  # If serial number found, break the loop
                    break
                time.sleep(0.3)  # Wait for 0.3 seconds before retrying
                attempts += 1

            return {"name": doc.name, "status": "Submitted", "serial_numbers": serial_nos}
        else:
            return {"error": f"No METER item found for {item_code}"}
    except Exception as e:
        frappe.log_error(f"Stock Entry Error: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def find_meter_item(item_code):
    possible_meter_codes = [
        f"{item_code}-METER",
        f"{item_code} - METER"
    ]
    for code in possible_meter_codes:
        meter_item = frappe.db.get_value(
            "Item",
            {
                "item_code": ["like", f"%{code}%"],
                "disabled": 0
            },
            "item_code"
        )
        if meter_item:
            actual_qty = frappe.db.get_value(
                "Bin",
                {
                    "item_code": meter_item,
                    "warehouse": "Stores - S"
                },
                "actual_qty"
            )
            if actual_qty and actual_qty > 0:
                return meter_item
    return {"error": f"No METER item with stock found for {item_code}"}