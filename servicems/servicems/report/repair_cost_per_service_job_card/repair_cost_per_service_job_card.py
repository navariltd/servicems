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
			"fieldname": "service_charges",
			"label": "Service Charges",
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
		{
			"fieldname": "completion_date",
			"label": "Completion Date",
			"fieldtype": "Datetime",
			"width": 180
		}
	]


def get_data(filters):		
	query = (
		frappe.qb.from_(ServiceJobCard)
		.select(
			ServiceJobCard.name.as_("service_job_card"),
			ServiceJobCard.service_item_name,
			ServiceJobCard.spares_cost,
			ServiceJobCard.service_charges,
			ServiceJobCard.total,
			ServiceJobCard.status,
			ServiceJobCard.completion_date,
		)
		.orderby(ServiceJobCard.total, order=frappe.qb.desc)
	)
	
	query = apply_query_filters(query, filters)

	data = query.run(as_dict=True)
 	
	return data


def apply_query_filters(query, filters={}):
	if not filters:
		return query

	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	
	if from_date:
		from_date = f"{from_date} 00:00:00"
	if to_date:
		to_date = f"{to_date} 23:59:59"

	if filters.get("company"):
		query = query.where(ServiceJobCard.company == filters["company"])
	if filters.get("from_date"):
		query = query.where(ServiceJobCard.creation >= from_date)
	if filters.get("to_date"):
		query = query.where(ServiceJobCard.creation <= to_date)
	if filters.get("service_item_name"):
		query = query.where(ServiceJobCard.service_item_name == filters["service_item_name"])
	if filters.get("status"):
		query = query.where(ServiceJobCard.status == filters["status"])
	return query
