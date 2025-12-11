import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "fieldname": "service_item_name",
            "label": _("Service Vehicle"),
            "fieldtype": "Link",
            "options": "Service Vehicle",
            "width": 150,
        },
        {
            "fieldname": "service_booking",
            "label": _("Service Booking"),
            "fieldtype": "Link",
            "options": "Service Booking",
            "width": 150,
        },
        {
            "fieldname": "service_job_card",
            "label": _("Service Job Card"),
            "fieldtype": "Link",
            "options": "Service Job Card",
            "width": 150,
        },
        {
            "fieldname": "completion_date",
            "label": _("Completion Date"),
            "fieldtype": "Datetime",
            "width": 160,
        },
        {"fieldname": "type", "label": _("Type"), "fieldtype": "Data", "width": 100},
        {
            "fieldname": "description",
            "label": _("Description/Item"),
            "fieldtype": "Data",
            "width": 250,
        },
        {"fieldname": "qty", "label": _("Quantity"), "fieldtype": "Int", "width": 100},
        {
            "fieldname": "rate",
            "label": _("Rate"),
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "fieldname": "amount",
            "label": _("Amount"),
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "fieldname": "is_billable",
            "label": _("Billable"),
            "fieldtype": "Check",
            "width": 80,
        },
    ]


def get_data(filters):
    """Fetch service job cards and their related faults and supplied parts"""
    if not filters:
        filters = {}

    service_job_cards = get_service_job_cards(filters)
    if not service_job_cards:
        return []

    data = []
    current_vehicle = None

    for sjc in service_job_cards:
        if current_vehicle != sjc.service_item_name:
            current_vehicle = sjc.service_item_name
            data.append(build_vehicle_group(sjc.service_item_name))

        data.append(build_job_card_header(sjc))

        faults = get_faults(sjc.name)

        if faults:
            data.extend(build_fault_rows(sjc, faults))

        supplied_parts = get_supplied_parts(sjc.name)
        print(
            f"Supplied Parts for {sjc.name}: {supplied_parts if supplied_parts else 'No supplied parts fetched!'}"
        )
        if supplied_parts:
            data.extend(build_spare_part_rows(sjc, supplied_parts))

        if sjc != service_job_cards[-1]:
            data.append({})

    return data


def get_service_job_cards(filters):
    """Fetch Service Job Cards matching the filters"""
    conditions = build_conditions(filters)
    conditions_str = " AND ".join(conditions)

    return frappe.db.sql(
        f"""SELECT
			sjc.name,
			sjc.service_item_name,
			sjc.service_booking,
			sjc.completion_date,
			sjc.customer,
			sjc.status
		FROM
			`tabService Job Card` sjc
		WHERE
			{conditions_str}
		AND
			sjc.completion_date IS NOT NULL
		ORDER BY
			sjc.service_item_name, sjc.completion_date DESC
		""",
        filters,
        as_dict=True,
    )


def build_conditions(filters):
    """Build SQL conditions based on filters"""
    conditions = ["sjc.docstatus = 1"]

    if filters.get("company"):
        conditions.append("sjc.company = %(company)s")
    if filters.get("service_item_name"):
        conditions.append("sjc.service_item_name = %(service_item_name)s")
    if filters.get("service_job_card"):
        conditions.append("sjc.name = %(service_job_card)s")
    if filters.get("service_booking"):
        conditions.append("sjc.service_booking = %(service_booking)s")

    return conditions


def get_faults(job_card_name):
    """Fetch faults for a specific Service Job Card"""
    return frappe.db.sql(
        """SELECT
			description
		FROM
			`tabFaults`
		WHERE
			parent = %s
		ORDER BY
			idx
		""",
        job_card_name,
        as_dict=True,
    )


def get_supplied_parts(job_card_name):
    """Fetch supplied parts for a specific Service Job Card"""
    return frappe.db.sql(
        """SELECT
			sp.item,
			sp.spare,
			sp.qty,
			sp.rate,
			sp.is_billable
		FROM
        	`tabJob Card Items Supplied` sp
		WHERE
			sp.parent = %s
		ORDER BY
			sp.idx
		""",
        job_card_name,
        as_dict=True,
    )


def build_vehicle_group(vehicle_name):
    """Build vehicle group header row"""
    return {"service_item_name": vehicle_name, "indent": 0, "is_group": 1}


def build_job_card_header(sjc):
    """Build Service Job Card header row"""
    return {
        "service_item_name": "",
        "service_job_card": sjc.name,
        "service_booking": sjc.service_booking,
        "completion_date": sjc.completion_date,
        "indent": 1,
        "is_group": 1,
    }


def build_fault_rows(sjc, faults):
    """Build rows for faults"""
    rows = []
    for fault in faults:
        rows.append(
            {
                "service_item_name": "",
                "service_job_card": sjc.name,
                "type": "Fault",
                "description": fault.description,
                "indent": 2,
            }
        )
    return rows


def build_spare_part_rows(sjc, supplied_parts):
    """Build rows for supplied parts"""
    rows = []
    for part in supplied_parts:
        description = part.item_name or part.item or part.spare
        amount = (part.qty or 0) * (part.rate or 0)

        rows.append(
            {
                "service_item_name": "",
                "service_job_card": "",
                "type": "Spare Part",
                "description": description,
                "qty": part.qty,
                "rate": part.rate,
                "amount": amount,
                "is_billable": part.is_billable,
                "indent": 2,
            }
        )
    return rows
