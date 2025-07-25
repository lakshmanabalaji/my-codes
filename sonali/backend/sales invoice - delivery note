import frappe

@frappe.whitelist()
def get_delivery_note_weights(sales_invoice):
    # ✅ Ensure the Sales Invoice exists
    if not frappe.db.exists("Sales Invoice", sales_invoice):
        return {"error": f"Sales Invoice {sales_invoice} not found"}

    sales_invoice_doc = frappe.get_doc("Sales Invoice", sales_invoice)

    # ✅ Prevent modification of Submitted Sales Invoice
    if sales_invoice_doc.docstatus != 0:
        return {"error": "Cannot update a submitted Sales Invoice"}

    # ✅ Get linked Delivery Notes
    delivery_notes = list(set(item.delivery_note for item in sales_invoice_doc.items if item.delivery_note))
    if not delivery_notes:
        return {"error": "No Delivery Notes linked"}

    # ✅ Fetch weight and quantity data from Delivery Note Items
    dn_items = frappe.get_all(
        "Delivery Note Item",
        filters={"parent": ["in", delivery_notes]},
        fields=["item_code", "qty", "custom_weight", "custom_length", "parent as delivery_note"]
    )

    # ✅ Group items by Delivery Note + Item Code
    grouped_items = {}
    for dn_item in dn_items:
        key = (dn_item["delivery_note"], dn_item["item_code"])
        qty = float(dn_item.get("qty") or 0)
        weight = float(dn_item.get("custom_weight") or 0)
        length = float(dn_item.get("custom_length") or 0)

        if key in grouped_items:
            grouped_items[key]["qty"] += qty
            grouped_items[key]["total_weight"] += weight
            grouped_items[key]["total_length"] += length
        else:
            grouped_items[key] = {
                "delivery_note": dn_item["delivery_note"],
                "item_code": dn_item["item_code"],
                "qty": qty,
                "total_weight": weight,
                "total_length": length
            }

    # Now let's update the items of the Sales Invoice based on the grouped data
    updated_items = []

    for key, grouped_item in grouped_items.items():
        # Check if the item already exists in the Sales Invoice
        existing_item = next(
            (item for item in sales_invoice_doc.items if item.item_code == grouped_item["item_code"] and item.delivery_note == grouped_item["delivery_note"]),
            None
        )

        if existing_item:
            # Update the existing item with new values
            existing_item.qty = grouped_item["qty"]  # Set the quantity to the new quantity
            existing_item.custom_weight_in_kg = round(grouped_item["total_weight"], 3)
            existing_item.custom_length_in_meter = round(grouped_item["total_length"], 3)  # Ensure custom_length_in_meter is set
        else:
            # Add a new item if it doesn't exist
            new_item = sales_invoice_doc.append("items", {})
            new_item.item_code = grouped_item["item_code"]
            new_item.custom_weight_in_kg = round(grouped_item["total_weight"], 3)
            new_item.custom_length_in_meter = round(grouped_item["total_length"], 3)  # Set custom_length_in_meter for new item
            new_item.qty = grouped_item["qty"]
            new_item.delivery_note = grouped_item["delivery_note"]
            new_item.rate = 0  # User will enter manually

        updated_items.append({
            "delivery_note": grouped_item["delivery_note"],
            "item_code": grouped_item["item_code"],
            "custom_weight_in_kg": grouped_item["total_weight"],
            "custom_length_in_meter": grouped_item["total_length"],
            "qty": grouped_item["qty"],
            "rate": 0
        })

    # Save the updated Sales Invoice document
    # sales_invoice_doc.save()

    return {"updated_items": updated_items}
