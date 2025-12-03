import frappe


def update_sjc_status_to_awaiting_parts(doc, method=None):
    """Update the status of the linked Service Job Card to 'Awaiting Parts' when a Material Request is submitted."""
    if doc.docstatus == 1 and doc.service_job_card:
        frappe.db.set_value("Service Job Card", doc.service_job_card, "status", "Awaiting Parts")
