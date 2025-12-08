# Copyright (c) 2025, Aakvatech Limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.query_builder import DocType


ServiceJobCard = DocType("Service Job Card")



def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)

	return columns, data

def get_columns():
    return [
		{
			"fieldname": "service_job_card",
			"label": "Service Job Card",
			"fieldtype": "Link",
			"options": "Service Job Card",
			"width": 200
		},
		{
			"fieldname": "service_item_name",
			"label": "Service Vehicle",
			"fieldtype": "Link",
			"options": "Service Vehicle",
			"width": 150
		},
		{
			"fieldname": "spares_cost",
			"label": "Spares Cost",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "total",
			"label": "Total",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "status",
			"label": "Status",
			"fieldtype": "Data",
			"width": 150
		},
	]


def get_data(filters):		
	query = (
		frappe.qb.from_(ServiceJobCard)
		.select(
			ServiceJobCard.name.as_("service_job_card"),
			ServiceJobCard.service_item_name,
			ServiceJobCard.spares_cost,
			ServiceJobCard.total,
			ServiceJobCard.status
		)
		.orderby(ServiceJobCard.total, order=frappe.qb.desc)
	)
	
	query = apply_query_filters(query, filters)

	data = query.run(as_dict=True)
 	
	return data


def apply_query_filters(query, filters={}):
	if not filters:
		return query

	if filters.get("company"):
		query = query.where(ServiceJobCard.company == filters["company"])
	if filters.get("from_date"):
		query = query.where(ServiceJobCard.creation >= filters["from_date"])
	if filters.get("to_date"):
		query = query.where(ServiceJobCard.creation <= filters["to_date"])
	if filters.get("service_item_name"):
		query = query.where(ServiceJobCard.service_item_name == filters["service_item_name"])
	if filters.get("status"):
		query = query.where(ServiceJobCard.status == filters["status"])
	return query
