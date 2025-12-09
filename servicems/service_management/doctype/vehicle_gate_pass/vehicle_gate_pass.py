# Copyright (c) 2025, Aakvatech Limited and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now


class VehicleGatePass(Document):
	def on_submit(self):
		if self.service_job_card:
			frappe.db.set_value(
				"Service Job Card",
				self.service_job_card,
				{
					"status": "Closed",
					"completion_date": now(),
				},
			)
			frappe.db.set_value(
				"Vehicle Gate Pass",
				self.name,
				"completed_on",
				now(),
			)
