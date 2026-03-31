import frappe
import time
import re
from frappe.utils import flt
from erpnext.stock.serial_batch_bundle import get_serial_nos_from_bundle

@frappe.whitelist()
def create_and_submit_stock_entry(item_code, weight, batch_id=None):
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
                        "s_warehouse": "Stores - S",
                        "use_serial_batch_fields": 1,
                        "batch_no": batch_id   # ✅ force selected batch
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
            {"item_code": ["like", f"%{code}%"], "disabled": 0},
            "item_code"
        )
        if kg_item:
            return kg_item
    return None


@frappe.whitelist()
def create_and_submit_stock_entry_meter(item_code, length, batch_id=None):
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
                        "s_warehouse": "Stores - S",
                        "batch_no": batch_id   # ✅ force selected batch if provided
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
            {"item_code": ["like", f"%{code}%"], "disabled": 0},
            "item_code"
        )
        if meter_item:
            actual_qty = frappe.db.get_value(
                "Bin",
                {"item_code": meter_item, "warehouse": "Stores - S"},
                "actual_qty"
            )
            if actual_qty and actual_qty > 0:
                return meter_item
    return {"error": f"No METER item with stock found for {item_code}"}


@frappe.whitelist()
def get_batches_for_output_item(output_item_code=None, txt=None, searchfield=None, start=0, page_len=20, filters=None):
    """
    Given an output item like 'SWW 1.10/1.50', try to find the corresponding
    KG item (e.g. 'SWW 1.10/1.50 - KG' or 'SWW 1.10/1.50-KG') and return its batches.
    """
    if not output_item_code and filters:
        output_item_code = (filters or {}).get("output_item_code")

    if not output_item_code:
        return []

    output_item_code = output_item_code.strip()
    kg_item_code = None

    candidates = [
        f"{output_item_code} - KG",
        f"{output_item_code}-KG",
        f"{output_item_code} -Kg",
        f"{output_item_code}-Kg",
        f"{output_item_code} - kg",
        f"{output_item_code}- kg"
    ]

    for cand in candidates:
        kg_item = frappe.db.exists("Item", {"item_code": cand, "disabled": 0})
        if kg_item:
            kg_item_code = cand
            break
    else:
        for cand in candidates:
            kg_item = frappe.db.get_value("Item", {"item_code": ["like", f"%{cand}%"], "disabled": 0}, "item_code")
            if kg_item:
                kg_item_code = kg_item
                break
        else:
            if re.search(r"-\s*kg\b", output_item_code, flags=re.IGNORECASE):
                kg_item_code = output_item_code

    if not kg_item_code:
        return []

    batches = frappe.get_all(
        "Batch",
        filters={"item": kg_item_code, "disabled": 0 ,"batch_qty": [">", 0]},
        fields=["name"],
        order_by="creation desc",
        limit_page_length=page_len or 20
    )

    return [b.get("name") for b in batches] if batches else []



def update_serial_no_with_work_order(doc, method):
    """Hook: enqueue update after Stock Entry submit/update."""
    if doc.stock_entry_type == "Manufacture" and doc.work_order:
        enqueue_update_serials(doc.name)


def enqueue_update_serials(stock_entry_name: str):
    frappe.enqueue(
        "sonali.custom_functions.Stock_Entry.sync_serial_work_orders",
        stock_entry_name=stock_entry_name,
        queue="short",
        enqueue_after_commit=True,
        job_name=f"update-serial-wo-{stock_entry_name}",
    )


def sync_serial_work_orders(stock_entry_name: str) -> int:
    """Sync serial numbers for a given Stock Entry with its work order."""
    doc = frappe.get_doc("Stock Entry", stock_entry_name)
    if not (doc.stock_entry_type == "Manufacture" and doc.work_order):
        return 0

    work_order = doc.work_order
    serials = []

    for item in doc.items:
        if item.serial_and_batch_bundle:
            bundle = frappe.get_doc("Serial and Batch Bundle", item.serial_and_batch_bundle)
            serials.extend([e.serial_no for e in bundle.entries if e.serial_no])

        if item.serial_no and not item.serial_and_batch_bundle:
            serials.extend([s.strip() for s in item.serial_no.replace(',', '\n').split('\n') if s.strip()])

    for serial_no in serials:
        if frappe.db.exists("Serial No", serial_no):
            frappe.db.set_value("Serial No", serial_no, "work_order", work_order)

    frappe.db.commit()
    return len(serials)


@frappe.whitelist()
def update_serial_work_order_from_creation_doc(serial_doc, method=None):
    """
    When a Serial No is created, try to set its work_order from the Stock Entry
    that created it (creation_document_no). Safe to call on existing serials.
    """
    if getattr(serial_doc, "work_order", None):
        return

    creation_doc = getattr(serial_doc, "creation_document_no", None)
    if not creation_doc:
        return

    if frappe.db.exists("Stock Entry", creation_doc):
        se_work_order = frappe.db.get_value("Stock Entry", creation_doc, "work_order")
        if se_work_order:
            frappe.db.set_value("Serial No", serial_doc.name, "work_order", se_work_order)


@frappe.whitelist()
def scan_batch_with_qty(scan_value: str, qty: float):
    """Resolve a `batch|qty` scan into item details and the parsed quantity."""
    batch_no = (scan_value or "").strip()
    parsed_qty = flt(qty)

    if not batch_no:
        frappe.throw("Please scan a valid batch number.")

    if parsed_qty <= 0:
        frappe.throw("Quantity must be greater than zero for scanned batches.")

    batch_doc = frappe.db.get_value(
        "Batch",
        batch_no,
        ["name", "item", "disabled"],
        as_dict=True,
    )

    if not batch_doc:
        frappe.throw(f"Batch {batch_no} was not found.")

    if batch_doc.disabled:
        frappe.throw(f"Batch {batch_no} is disabled.")

    item_info = frappe.db.get_value(
        "Item",
        batch_doc.item,
        ["stock_uom", "has_batch_no", "has_serial_no", "disabled"],
        as_dict=True,
    )

    if not item_info or item_info.disabled:
        frappe.throw(f"Item {batch_doc.item} linked to batch {batch_no} is disabled or missing.")

    return {
        "item_code": batch_doc.item,
        "batch_no": batch_doc.name,
        "uom": item_info.stock_uom,
        "has_batch_no": item_info.has_batch_no,
        "has_serial_no": item_info.has_serial_no,
        "qty": parsed_qty,
    }

@frappe.whitelist()
def create_stock_entry_with_weights(
    serial_no,
    gross_weight,
    tare_weight,
    net_weight,
    grade=None,
    batch_id=None
):
    """
    Flow:
    1. Scan Serial No
    2. Get product_item
    3. Resolve KG item from product_item
    4. Create Stock Entry using KG item
    5. Create NEW Serial No for product_item
    """

    # =========================================================
    # 🔥 STEP 0: KG ITEM RESOLUTION FUNCTION (UNCHANGED)
    # =========================================================
    def resolve_kg_item_local(code):
        code = (code or "").strip()

        candidates = [
            f"{code} - KG",
            f"{code}-KG",
            f"{code} -Kg",
            f"{code}-Kg",
            f"{code} - kg",
            f"{code}- kg"
        ]

        for c in candidates:
            if frappe.db.exists("Item", {"item_code": c, "disabled": 0}):
                return c

        for c in candidates:
            item = frappe.db.get_value(
                "Item",
                {"item_code": ["like", f"%{c}%"], "disabled": 0},
                "item_code"
            )
            if item:
                return item

        return None


    # =========================================================
    # 🔥 STEP 1: VALIDATE SERIAL NO + WEIGHTS
    # =========================================================
    gross_weight = flt(gross_weight)
    tare_weight = flt(tare_weight)
    net_weight = flt(net_weight)

    if gross_weight <= 0:
        return {"error": "Gross Weight must be greater than 0"}

    if net_weight <= 0:
        return {"error": "Net Weight must be greater than 0"}
    if not frappe.db.exists("Serial No", serial_no):
        return {"error": f"Invalid Serial No: {serial_no}"}

    sn_doc = frappe.get_doc("Serial No", serial_no)

    product_item = sn_doc.get("product_item")

    if not product_item:
        return {"error": f"Product Item not set in Serial No: {serial_no}"}


    # =========================================================
    # 🔥 STEP 2: RESOLVE KG ITEM (🔥 YOUR LOGIC USED HERE)
    # =========================================================
    kg_item = resolve_kg_item_local(product_item)

    if not kg_item:
        return {"error": f"No KG item found for {product_item}"}

    kg_flags = frappe.db.get_value(
        "Item",
        kg_item,
        ["has_serial_no", "has_batch_no", "disabled"],
        as_dict=True,
    )

    if not kg_flags or kg_flags.disabled:
        return {"error": f"KG item {kg_item} is disabled or missing"}

    if kg_flags.has_serial_no:
        return {"error": f"KG item {kg_item} requires Serial No; cannot auto-assign"}

    if kg_flags.has_batch_no and not batch_id:
        batch_rows = frappe.get_all(
            "Batch",
            filters={"item": kg_item, "disabled": 0, "batch_qty": [">", 0]},
            fields=["name"],
            order_by="creation desc",
            limit_page_length=1,
        )
        if batch_rows:
            batch_id = batch_rows[0].name
        else:
            return {"error": f"No batch with stock found for {kg_item}"}


    # =========================================================
    # 🔥 STEP 3: CREATE REPACK STOCK ENTRY
    # =========================================================
    se_doc = frappe.get_doc({
        "doctype": "Stock Entry",
        "stock_entry_type": "Repack",
        "items": [
            {
                "item_code": kg_item,
                "qty": net_weight,
                "s_warehouse": "Stores - S",
                "use_serial_batch_fields": 1,
                "batch_no": batch_id,
            },
            {
                "item_code": product_item,
                "qty": 1,
                "t_warehouse": "Stores - S",
            },
        ],
    })

    se_doc.insert(ignore_permissions=True)
    se_doc.submit()

    # =========================================================
    # 🔥 STEP 4: FETCH & UPDATE NEW SERIAL NO WITH WEIGHTS
    # =========================================================
    # Poll for newly created serial number (auto-generated by Frappe)
    new_serial_no = None
    attempts = 0
    while attempts < 5:
        new_serials = frappe.db.get_list(
            "Serial No",
            filters={"item_code": product_item, "purchase_document_no": se_doc.name},
            pluck="name"
        )
        if new_serials:
            new_serial_no = new_serials[0]
            break
        time.sleep(0.3)
        attempts += 1

    # Update the new serial with weight information
    if new_serial_no:
        frappe.db.set_value("Serial No", new_serial_no, {
            "gross_weight": gross_weight,
            "tare_weight": tare_weight,
            "net_weight": net_weight,
        })

    frappe.db.commit()

    return {
        "status": "Success",
        "stock_entry": se_doc.name,
        "serial_no": new_serial_no,
        "product_item": product_item,
        "kg_item_used": kg_item,
    }


# =========================================================
# 🔥 STOCK ENTRY FUNCTION
# =========================================================
def create_material_receipt_stock_entry(item_code, qty, batch_id=None):

    try:
        warehouse = frappe.db.get_single_value("Stock Settings", "default_warehouse")

        if not warehouse:
            return {"error": "Default Warehouse not set"}

        se = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "to_warehouse": warehouse,
            "items": [
                {
                    "item_code": item_code,
                    "qty": qty,
                    "t_warehouse": warehouse,
                    "batch_no": batch_id
                }
            ]
        })

        se.insert(ignore_permissions=True)
        se.submit()

        return {
            "status": "Success",
            "name": se.name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Stock Entry Failed")
        return {"error": str(e)}


@frappe.whitelist()
def create_stock_entry_with_weights_legacy(item_code, qty, tare_weight, product_item=None, warehouse="Stores - S"):
    """
    Create Stock Entry + update tare_weight in Serial No
    """

    # ==============================
    # CREATE STOCK ENTRY
    # ==============================
    se = frappe.get_doc({
        "doctype": "Stock Entry",
        "stock_entry_type": "Material Receipt",
        "to_warehouse": warehouse,
        "items": [
            {
                "item_code": item_code,
                "qty": qty,
                "t_warehouse": warehouse
            }
        ]
    })

    se.insert(ignore_permissions=True)
    se.submit()

    # ==============================
    # GET SERIAL NUMBERS
    # ==============================
    serial_numbers = []

    for item in se.items:

        # New bundle system
        if item.serial_and_batch_bundle:
            serial_numbers.extend(get_serial_nos_from_bundle(item.serial_and_batch_bundle))

        # Old system
        if item.serial_no and not item.serial_and_batch_bundle:
            serial_numbers.extend(item.serial_no.split("\n"))

    serial_numbers = [sn for sn in serial_numbers if sn]

    # Fallback
    if not serial_numbers:
        serial_numbers = frappe.db.get_list(
            "Serial No",
            filters={
                "item_code": item_code,
                "purchase_document_no": se.name
            },
            pluck="name",
        )

    # ==============================
    # UPDATE TARE WEIGHT
    # ==============================
    for sn in serial_numbers:
        frappe.db.set_value("Serial No", sn, {
            "tare_weight": tare_weight , "product_item": product_item
        })

    frappe.db.commit()

    return {
        "status": "Success",
        "stock_entry": se.name,
        "serial_numbers": serial_numbers
    }

@frappe.whitelist()
def create_stock_entry_with_reel(item_code, qty, tare_weight, product_item=None, warehouse="Stores - S"):
    """
    Create Stock Entry + update tare_weight + product_item in Serial No
    """

    # ==============================
    # CREATE STOCK ENTRY
    # ==============================
    se = frappe.get_doc({
        "doctype": "Stock Entry",
        "stock_entry_type": "Material Receipt",
        "to_warehouse": warehouse,
        "items": [
            {
                "item_code": item_code,
                "qty": qty,
                "t_warehouse": warehouse
            }
        ]
    })

    se.insert(ignore_permissions=True)
    se.submit()

    # ==============================
    # GET SERIAL NUMBERS
    # ==============================
    serial_numbers = []

    for item in se.items:

        # ✅ NEW SERIAL BUNDLE SYSTEM
        if item.serial_and_batch_bundle:
            serial_numbers.extend(get_serial_nos_from_bundle(item.serial_and_batch_bundle))

        # ✅ OLD SYSTEM
        if item.serial_no and not item.serial_and_batch_bundle:
            serial_numbers.extend(item.serial_no.split("\n"))

    serial_numbers = [sn for sn in serial_numbers if sn]

    # ✅ FALLBACK
    if not serial_numbers:
        serial_numbers = frappe.db.get_list(
            "Serial No",
            filters={
                "item_code": item_code,
                "purchase_document_no": se.name
            },
            pluck="name",
        )

    # ==============================
    # UPDATE SERIAL NOS
    # ==============================
    for sn in serial_numbers:
        frappe.db.set_value("Serial No", sn, {
            "tare_weight": tare_weight,
            "product_item": product_item   # ✅ ADDED
        })

    frappe.db.commit()

    return {
        "status": "Success",
        "stock_entry": se.name,
        "serial_numbers": serial_numbers
    }    
