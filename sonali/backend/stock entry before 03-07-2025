import frappe
import time

@frappe.whitelist()
def create_and_submit_stock_entry(item_code, weight):
    item_kg = find_kg_item(item_code)
    try:
        if item_kg:
            doc = frappe.get_doc({
                "doctype": "Stock Entry",
                "stock_entry_type": "Repack",
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
    """
    Finds the corresponding KG item for the given item_code in the Item doctype.
    Example: 'SWW 0.8/1.1' -> Searches for 'SWW 0.8/1.1-KG' or 'SWW 0.8/1.1 - KG' in Items.
    Returns the KG item code if found, otherwise returns an error message.
    """
    possible_kg_codes = [
        f"{item_code}-KG",
        f"{item_code} - KG"
    ]

    kg_item = frappe.db.get_value("Item", {"item_code": ["in", possible_kg_codes]}, "item_code")

    if kg_item:
        return kg_item
    else:
        return {"error": f"No KG item found for {item_code}"}


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

    meter_item = frappe.db.get_value("Item", {"item_code": ["in", possible_meter_codes]}, "item_code")

    if meter_item:
        return meter_item
    else:
        return {"error": f"No METER item found for {item_code}"}