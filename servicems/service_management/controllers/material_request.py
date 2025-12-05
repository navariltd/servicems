import frappe
from frappe import _


def update_sjc_status_to_awaiting_parts(doc, method=None):
    """Update the status of the linked Service Job Card to 'Awaiting Parts' when a Material Request is submitted."""
    if doc.service_job_card:
        frappe.db.set_value("Service Job Card", doc.service_job_card, "status", "Awaiting Parts")


def verify_service_job_card_items(doc, method=None):
    if not doc.service_job_card:
        return

    try:
        job_card = frappe.get_doc("Service Job Card", doc.service_job_card)
    except frappe.DoesNotExistError:
        frappe.throw(
            _("Service Job Card {0} does not exist").format(doc.service_job_card)
        )
        return

    job_card_parts = {}
    for part in job_card.parts:
        if part.item in job_card_parts:
            job_card_parts[part.item] += part.qty
        else:
            job_card_parts[part.item] = part.qty

    errors = []
    for idx, mr_item in enumerate(doc.items, start=1):
        item_code = mr_item.item_code
        requested_qty = mr_item.qty

        if item_code not in job_card_parts:
            errors.append(
                _("Row #{0}: Item {1} is not in Service Job Card {2}").format(
                    idx, frappe.bold(item_code), frappe.bold(doc.service_job_card)
                )
            )
            continue

        job_card_qty = job_card_parts[item_code]
        if requested_qty > job_card_qty:
            errors.append(
                _(
                    "Row #{0}: Requested quantity {1} for item {2} exceeds the quantity {3} in Service Job Card {4}"
                ).format(
                    idx,
                    frappe.bold(requested_qty),
                    frappe.bold(item_code),
                    frappe.bold(job_card_qty),
                    frappe.bold(doc.service_job_card),
                )
            )

    if errors:
        error_message = "<br>".join(errors)
        frappe.throw(
            _("Material Request validation failed:<br><br>{0}").format(error_message),
            title=_("Quantity Validation Error"),
        )


def update_sjc_status_to_repairing(doc, method=None):
    """Update the status of the linked Service Job Card to 'Repairing' when a Material Request is issued."""
    if doc.service_job_card and doc.status == "Issued":
        frappe.db.set_value("Service Job Card", doc.service_job_card, "status", "Repairing")
