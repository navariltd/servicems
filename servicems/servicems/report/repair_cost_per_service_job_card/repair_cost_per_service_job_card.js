// Copyright (c) 2025, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.query_reports["Repair Cost per Service Job Card"] = {
	"filters": [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "vehicle",
			label: __("Vehicle"),
			fieldtype: "Link",
			options: "Service Vehicle",
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: [
				{ "value": "", "label": __("") },
				{ "value": "Initiated", "label": __("Initiated") },
				{ "value": "Awaiting Parts", "label": __("Awaiting Parts") },
				{ "value": "Repairing", "label": __("Repairing") },
				{ "value": "Completed", "label": __("Completed") },
				{ "value": "Closed", "label": __("Closed") },
			],
			default: "Completed",
		}
	]
};
