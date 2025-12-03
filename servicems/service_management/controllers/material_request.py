import frappe


def update_sjc_status_to_awaiting_parts(doc, method=None):
    if doc.docstatus == 1 and doc.service_job_card:
        frappe.db.set_value("Service Job Card", doc.service_job_card, "status", "Awaiting Parts")
