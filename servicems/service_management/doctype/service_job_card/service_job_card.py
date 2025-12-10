# Copyright (c) 2021, Aakvatech Limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.desk.form.assign_to import add
from frappe.utils import nowdate, nowtime, cint
from frappe.website.website_generator import WebsiteGenerator
import json


class ServiceJobCard(WebsiteGenerator):
    def after_insert(self):
        price_list = frappe.get_single_value("Service Settings", "price_list")
        cost_center = frappe.get_single_value("Service Settings", "cost_center")
        if self.service_booking:
            frappe.db.set_value(
                "Service Booking",
                self.service_booking,
                {
                    "status": "In Progress",
                    "job_card": self.name,
                },
            )

        self._create_task_documents()

        if self.price_list:
            self._update_parts_rates_from_price_list()

    def _update_parts_rates_from_price_list(self):
        """Update rates for all parts in the parts table based on the specified price_list"""
        if not self.parts:
            return

        updated_count = 0
        for part in self.parts:
            if not part.item:
                continue

            rate = get_item_price(part.item, self.price_list, self.company)

            if rate and rate > 0:
                frappe.db.set_value("Job Card Items Supplied", part.name, "rate", rate)
                part.rate = rate
                updated_count += 1

        if updated_count > 0:
            self.set_totals()
            self.db_update()

            frappe.msgprint(
                _("Updated rates for {0} item(s) from Price List {1}").format(
                    updated_count, frappe.bold(self.price_list)
                ),
                alert=True,
                indicator="blue",
            )

    def validate(self):
        self.price_list = frappe.db.get_single_value("Service Settings", "price_list")
        self.cost_center = frappe.db.get_single_value("Service Settings", "cost_center")

        self.update_tables()
        self.set_parts_rate()
        self.set_totals()
        self.vaildate_complete()

    def update_tables(self):
        for template in self.services:
            if template.bypass_billable and template.applied:
                continue

            service_template = frappe.get_doc("Service Template", template.service)

            if not template.bypass_billable:
                template.is_billable = service_template.is_billable

            if not template.applied:
                if service_template.tasks:
                    self.create_tasks_from_job_card(service_template)

                if service_template.parts:
                    for part in service_template.parts:
                        self.append(
                            "parts",
                            {
                                "item": part.item,
                                "qty": part.qty,
                                "rate": get_item_price(
                                    part.item,
                                    self.get_price_list(service_template.price_list),
                                    self.company,
                                ),
                                "is_billable": part.is_billable,
                            },
                        )

                template.applied = 1

    def create_tasks_from_job_card(self, service_template):
        """Only populate the tasks child table - don't create Task documents yet"""
        if service_template.tasks:
            for task in service_template.tasks:
                self.append(
                    "tasks",
                    {
                        "task_name": task.task_name,
                        "template": service_template.name,
                    },
                )

    def _create_task_documents(self):
        """Create Task documents for each task in the job card"""
        for task in self.tasks:
            if not task.task_name:
                continue

            # Check if Task already exists
            existing_task = frappe.db.exists("Task", {"job_card_task": task.name})
            if existing_task:
                continue

            task_doc = frappe.get_doc(
                {
                    "doctype": "Task",
                    "subject": task.task_name,
                    "status": "Completed" if task.completed else "Open",
                    "service_job_card": self.name,
                    "job_card_task": task.name,
                    "company": self.company,
                    "description": f"Task for Service Job Card: {self.name}\nTemplate: {task.template or 'N/A'}",
                }
            )

            task_doc.insert(ignore_permissions=True)

            # Assign task to mechanic if specified
            if task.mechanic:
                try:
                    add(
                        {
                            "doctype": "Task",
                            "name": task_doc.name,
                            "assign_to": [task.mechanic],
                            "description": f"Assigned from Service Job Card: {self.name}",
                        }
                    )
                except Exception as e:
                    frappe.log_error(
                        f"Failed to assign task {task_doc.name}: {str(e)}",
                        "Task Assignment Error",
                    )

            frappe.msgprint(
                _("Task {0} created for {1}").format(
                    '<a href="/app/task/{0}">{0}</a>'.format(task_doc.name),
                    task.task_name,
                ),
                alert=True,
                indicator="green",
            )

    def set_totals(self):
        self.service_charges = 0
        self.spares_cost = 0
        self.total = 0

        if self.services:
            for service in self.services:
                if not service.rate or service.rate == 0:
                    service.rate = get_item_price(
                        service.item,
                        self.get_price_list(service.price_list),
                        self.company,
                    )
                if service.is_billable:
                    self.service_charges += service.rate
        if self.parts:
            for part in self.parts:
                if part.is_billable:
                    self.spares_cost += part.rate * part.qty
        if self.supplied_parts:
            for supplied_part in self.supplied_parts:
                if supplied_part.is_billable:
                    self.spares_cost += supplied_part.rate * supplied_part.qty

        self.total = self.service_charges + self.spares_cost

    def set_parts_rate(self):
        price_list = self.get_price_list()
        for item in self.parts:
            if item.rate:
                continue

            item.rate = get_item_price(item.item, price_list, self.company)

    @frappe.whitelist()
    def create_parts_entry(self, type):
        is_allowed = frappe.get_single_value(
            "Service Settings", "use_spares_instead_of_item"
        )

        if not is_allowed:
            frappe.throw(
                _(
                    "Please enable 'Use Spares Instead of Item' in Service Settings to create Parts Entry."
                )
            )
            return

        if not self.parts:
            frappe.throw(_("Add Parts and Consumable Supplied first."))

        supplied_items = []
        items = []
        for item_row in self.parts:
            if (
                item_row.service_parts_entry
                or item_row.use_existing_spares
                or not item_row.qty
            ):
                continue

            item_dict = frappe._dict(
                {
                    "item_code": item_row.item,
                    "qty": item_row.qty,
                    "basic_rate": item_row.rate,
                }
            )

            items.append(item_dict)
            supplied_items.append(item_row.name)

        if not len(items):
            frappe.throw(_("Items not available to create Parts Entry."))

        service_parts_entry = frappe.get_doc(
            dict(
                doctype="Service Parts Entry",
                posting_date=nowdate(),
                posting_time=nowtime(),
                company=self.company,
                service_job_card=self.name,
                items=items,
            ),
        )

        frappe.flags.ignore_account_permission = True
        service_parts_entry.insert(ignore_permissions=True)
        service_parts_entry.submit()

        if not service_parts_entry.get("name"):
            return

        frappe.msgprint(
            _("Service Parts Entry {0} Created").format(
                '<a href="/app/service-parts-entry/{0}">{0}</a>'.format(
                    service_parts_entry.name
                )
            ),
            alert=True,
            indicator="green",
        )

        self.update_supplied_parts_details(supplied_items, service_parts_entry.name)

        if type == "call":
            self.save()

    def update_supplied_parts_details(self, supplied_items, parts_entry_no):
        for row in self.parts:
            if row.name not in supplied_items:
                continue

            row.service_parts_entry = parts_entry_no

            self.append(
                "supplied_parts",
                {
                    "item": row.item,
                    "qty": row.qty,
                    "rate": row.rate,
                    "is_billable": row.is_billable,
                },
            )

    @frappe.whitelist()
    def create_stock_entry(self, type):
        if self.parts and len(self.parts) > 0:
            workshop = frappe.get_doc("Service Workshop", self.workshop)
            stock_entry_type = (
                frappe.get_single_value("Service Settings", "default_stock_enty_type")
                or "Material Transfer"
            )

            items = []
            for item in self.parts:
                if item.qty > 0:
                    items.append(
                        {
                            "s_warehouse": workshop.parts_warehouse,
                            "t_warehouse": workshop.workshop_warehouse,
                            "item_code": item.item,
                            "qty": item.qty,
                            "uom": frappe.get_value("Item", item.item, "stock_uom"),
                        }
                    )

            if len(items) == 0:
                return

            doc = frappe.get_doc(
                dict(
                    doctype="Stock Entry",
                    posting_date=nowdate(),
                    posting_time=nowtime(),
                    stock_entry_type=stock_entry_type,
                    purpose=stock_entry_type,
                    company=self.company,
                    service_job_card=self.name,
                    from_warehouse=workshop.parts_warehouse,
                    to_warehouse=workshop.workshop_warehouse,
                    items=items,
                ),
            )
            frappe.flags.ignore_account_permission = True
            doc.insert(ignore_permissions=True)
            doc.submit()
            frappe.msgprint(_("Stock Entry Created {0}").format(doc.name), alert=True)

            if doc.get("name"):
                left_parts = []
                for row in self.parts:
                    if row.qty > 0:
                        new_row = self.append("supplied_parts", {})
                        new_row.item = row.item
                        new_row.qty = row.qty
                        new_row.rate = row.rate
                        new_row.is_billable = row.is_billable
                        new_row.stock_entry = doc.name
                    else:
                        left_parts.append(row)
                self.parts = left_parts
                if type == "call":
                    self.save()

    def move_parts_to_supplied(self):
        stock_entry_type = (
            frappe.get_single_value("Service Settings", "default_stock_enty_type")
            or "Material Transfer"
        )
        workshop = frappe.get_doc("Service Workshop", self.workshop)

        items = []
        for item in self.parts:
            if item.qty > 0:
                items.append(
                    {
                        "s_warehouse": workshop.parts_warehouse,
                        "t_warehouse": workshop.workshop_warehouse,
                        "item_code": item.item,
                        "qty": item.qty,
                        "uom": frappe.get_value("Item", item.item, "stock_uom"),
                    }
                )

        stock_entry = frappe.db.get_value(
            "Stock Entry",
            {
                "service_job_card": self.name,
                "docstatus": 1,
                "stock_entry_type": stock_entry_type,
                "from_warehouse": workshop.parts_warehouse,
                "to_warehouse": workshop.workshop_warehouse,
            },
            "name",
        )

        left_parts = []
        for row in self.parts:
            if row.qty > 0:
                new_row = self.append("supplied_parts", {})
                new_row.item = row.item
                new_row.qty = row.qty
                new_row.rate = row.rate
                new_row.is_billable = row.is_billable
                new_row.stock_entry = stock_entry
            else:
                left_parts.append(row)
        self.parts = left_parts

    def create_invoice(self):
        create_sales_invoice = frappe.get_single_value(
            "Service Settings", "create_sjc_sales_invoice"
        )

        if self.status != "Completed" or not create_sales_invoice:
            return
        items = []
        workshop = frappe.get_doc("Service Workshop", self.workshop)
        if self.services and len(self.services) > 0:
            for item in self.services:
                if not item.is_billable:
                    continue

                items.append(
                    {
                        "item_code": item.item,
                        "qty": 1,
                        "uom": frappe.get_value("Item", item.item, "stock_uom"),
                        "warehouse": workshop.workshop_warehouse,
                        "rate": item.rate if item.is_billable else 0,
                    }
                )
        if self.supplied_parts and len(self.supplied_parts) > 0:
            for item in self.supplied_parts:
                if not item.is_billable or item.is_return or item.qty == 0:
                    continue

                items.append(
                    {
                        "item_code": item.item,
                        "qty": item.qty,
                        "uom": frappe.get_value("Item", item.item, "stock_uom"),
                        "warehouse": workshop.workshop_warehouse,
                        "rate": item.rate if item.is_billable else 0,
                    }
                )
            taxes = frappe.get_value(
                "Sales Taxes and Charges Template",
                {"company": self.company, "is_default": 1},
                ["name", "tax_category"],
                as_dict=1,
            )

            if len(items) == 0:
                return
            date = nowdate()
            doc = frappe.get_doc(
                dict(
                    doctype="Sales Invoice",
                    customer=self.customer,
                    posting_date=date,
                    due_date=date,
                    update_stock=1,
                    service_job_card=self.name,
                    company=self.company,
                    ignore_pricing_rule=1,
                    set_warehouse=workshop.workshop_warehouse,
                    items=items,
                    taxes_and_charges=taxes.name,
                    tax_category=taxes.tax_category,
                ),
            )
            frappe.flags.ignore_account_permission = True
            doc.set_taxes()
            doc.set_missing_values(for_validate=True)
            doc.flags.ignore_mandatory = True
            doc.calculate_taxes_and_totals()
            doc.insert(ignore_permissions=True)
            self.invoice = doc.name
            frappe.msgprint(_("Sales Invoice Created {0}").format(doc.name), alert=True)

    def _validate_and_get_warehouse(self):
        warehouse = frappe.get_value(
            "Service Workshop", self.workshop, "workshop_warehouse"
        )

        if not warehouse:
            frappe.throw(
                _("Please set Workshop Warehouse in Service Workshop {0}").format(
                    self.workshop
                )
            )

        item_codes = [part.item for part in self.parts if part.qty > 0]
        if not item_codes:
            frappe.msgprint(
                _(
                    "No parts with quantity greater than zero to create Material Request"
                ),
                alert=True,
            )
            return None, None

        return warehouse, item_codes

    def _prepare_material_request_items(self, warehouse, item_codes):
        item_uoms = {
            item.name: item.stock_uom
            for item in frappe.get_all(
                "Item",
                filters={"name": ["in", item_codes]},
                fields=["name", "stock_uom"],
            )
        }

        items = []
        for part in self.parts:
            if part.qty > 0:
                uom = item_uoms.get(part.item)
                if not uom:
                    frappe.log_error(
                        f"Missing UOM for item {part.item} on SJC {self.name}",
                        "MR Creation Warning",
                    )

                items.append(
                    {
                        "item_code": part.item,
                        "qty": part.qty,
                        "uom": uom,
                        "schedule_date": nowdate(),
                        "warehouse": warehouse,
                    }
                )

        if len(items) == 0:
            frappe.msgprint(_("No items to create Material Request"), alert=True)
            return []

        return items

    @frappe.whitelist()
    def create_material_request(self):
        warehouse, item_codes = self._validate_and_get_warehouse()
        if not warehouse or not item_codes:
            return

        issued_quantities = self._get_issued_quantities()

        items = self._prepare_material_request_items_with_validation(
            warehouse, item_codes, issued_quantities
        )

        if not items:
            return

        material_request_type = (
            frappe.get_single_value(
                "Service Settings", "default_sjc_material_request_type"
            )
            or "Material Transfer"
        )

        doc = frappe.get_doc(
            dict(
                doctype="Material Request",
                material_request_type=material_request_type,
                posting_date=nowdate(),
                company=self.company,
                service_job_card=self.name,
                items=items,
                set_warehouse=warehouse,
            ),
        )

        doc.insert(ignore_permissions=True)
        if (
            frappe.get_single_value(
                "Service Settings", "auto_submit_sjc_material_request"
            )
            == 1
        ):
            doc.submit()

        frappe.msgprint(
            _("Material Request Created: {0}").format(
                '<a href="/app/material-request/{0}">{0}</a>'.format(doc.name)
            ),
            alert=True,
            indicator="green",
        )

    def _get_issued_quantities(self):
        """
        Get total issued quantities from all Material Requests linked to this job card
        Returns a dict with item_code as key and total issued qty as value
        """
        issued_quantities = {}

        material_requests = frappe.get_all(
            "Material Request",
            filters={
                "service_job_card": self.name,
                "docstatus": 1,
            },
            fields=["name"],
        )

        if not material_requests:
            return issued_quantities

        for mr in material_requests:
            mr_items = frappe.get_all(
                "Material Request Item",
                filters={"parent": mr.name},
                fields=["item_code", "qty"],
            )

            for item in mr_items:
                if item.item_code in issued_quantities:
                    issued_quantities[item.item_code] += item.qty
                else:
                    issued_quantities[item.item_code] = item.qty

        return issued_quantities

    def _calculate_remaining_quantities(self, issued_quantities):
        """
        Calculate remaining quantities for each part based on already issued quantities
        Returns list of dicts with part info and remaining quantities, plus validation errors
        """
        parts_info = []
        validation_errors = []

        for part in self.parts:
            if part.qty <= 0:
                continue

            item_code = part.item
            required_qty = part.qty
            already_issued = issued_quantities.get(item_code, 0)
            remaining_qty = required_qty - already_issued

            if remaining_qty <= 0:
                validation_errors.append(
                    _(
                        "Row #{0}: Item {1} - Required quantity ({2}) has already been fully issued ({3})"
                    ).format(
                        part.idx,
                        frappe.bold(item_code),
                        frappe.bold(required_qty),
                        frappe.bold(already_issued),
                    )
                )
                continue

            if remaining_qty < required_qty:
                frappe.msgprint(
                    _(
                        "Row #{0}: Item {1} - Only {2} units remaining to request (Required: {3}, Already Issued: {4})"
                    ).format(
                        part.idx,
                        frappe.bold(item_code),
                        frappe.bold(remaining_qty),
                        frappe.bold(required_qty),
                        frappe.bold(already_issued),
                    ),
                    alert=True,
                    indicator="orange",
                )

            parts_info.append(
                {
                    "item_code": item_code,
                    "remaining_qty": remaining_qty,
                }
            )

        return parts_info, validation_errors

    def _prepare_material_request_items_with_validation(
        self, warehouse, item_codes, issued_quantities
    ):
        parts_info, validation_errors = self._calculate_remaining_quantities(
            issued_quantities
        )

        if validation_errors:
            for error in validation_errors:
                frappe.msgprint(error, alert=True, indicator="red")

        if not parts_info:
            frappe.msgprint(
                _(
                    "No items available to create Material Request. All required items have been issued."
                ),
                alert=True,
                indicator="orange",
            )
            return []

        item_uoms = {
            item.name: item.stock_uom
            for item in frappe.get_all(
                "Item",
                filters={"name": ["in", item_codes]},
                fields=["name", "stock_uom"],
            )
        }

        items = []
        for part_info in parts_info:
            item_code = part_info["item_code"]
            uom = item_uoms.get(item_code)

            if not uom:
                frappe.log_error(
                    f"Missing UOM for item {item_code} on SJC {self.name}",
                    "MR Creation Warning",
                )

            items.append(
                {
                    "item_code": item_code,
                    "qty": part_info["remaining_qty"],
                    "uom": uom,
                    "schedule_date": nowdate(),
                    "warehouse": warehouse,
                }
            )

        return items

    def vaildate_complete(self):
        if self.status != "Completed":
            return

        for task in self.tasks:
            if not task.completed:
                frappe.throw(_("Row #{0}: The Tasks is not Completed").format(task.idx))

    def get_price_list(self, template_price_list=None):
        price_list = frappe.get_value("Customer", self.customer, "default_price_list")

        if not price_list and template_price_list:
            price_list = template_price_list

        if not price_list:
            price_list = frappe.get_value(
                "Service Settings", "Service Settings", "price_list"
            )
        return price_list or ""

    @frappe.whitelist()
    def reopen_job_card(self):
        """Reopen a closed job card by setting status back to Repairing"""
        if self.status != "Closed":
            frappe.throw(
                _(
                    "Service Job Card can only be reopened when status is 'Closed'. Current status: {0}"
                ).format(self.status)
            )

        if self.docstatus != 0:
            frappe.throw(_("Only draft Service Job Cards can be reopened"))

        if self.invoice:
            invoice_status = frappe.db.get_value(
                "Sales Invoice", self.invoice, "docstatus"
            )
            if invoice_status == 1:
                frappe.throw(
                    _(
                        "Cannot reopen Job Card. Please cancel the linked Sales Invoice {0} first."
                    ).format(self.invoice)
                )

        self.status = "Initiated"
        self.save()

        frappe.msgprint(
            _("Service Job Card {0} has been reopened").format(self.name),
            alert=True,
            indicator="blue",
        )

        return True

    @frappe.whitelist()
    def create_vehicle_inspection(self):
        inspection = frappe.get_doc(
            {
                "doctype": "Service Vehicle Inspection",
                "driver_name": self.driver_name or "",
                "vehicle_plate_number": self.service_item_name or "",
                "date": nowdate(),
                "service_job_card": self.name,
                "mileage": self.odometer_reading or "",
            }
        )

        inspection.insert(ignore_permissions=True)

        frappe.msgprint(
            _("Vehicle Inspection {0} created").format(
                '<a href="/app/service-vehicle-inspection/{0}">{0}</a>'.format(
                    inspection.name
                )
            ),
            alert=True,
            indicator="green",
        )

        return inspection.name


def get_item_price(item_code, price_list, company):
    company_currency = frappe.get_value("Company", company, "default_currency")
    item_prices_data = frappe.db.get_value(
        "Item Price",
        filters={
            "price_list": price_list,
            "item_code": item_code,
            "currency": company_currency,
        },
        fieldname=["item_code", "price_list_rate", "currency"],
        as_dict=True,
        order_by="valid_from desc",
    )

    return item_prices_data.price_list_rate if item_prices_data else 0


@frappe.whitelist()
def get_selected_items(items):
    selected_items = json.loads(items)

    if selected_items:
        doc = frappe.get_doc(
            selected_items[0]["parenttype"], selected_items[0]["parent"]
        )
        source_doc = frappe.get_doc("Stock Entry", selected_items[0]["stock_entry"])

        new_doc = frappe.new_doc("Stock Entry")
        new_doc.company = source_doc.company
        new_doc.stock_entry_type = source_doc.stock_entry_type
        new_doc.purpose = source_doc.purpose
        new_doc.posting_date = nowdate()
        new_doc.posting_time = nowtime()
        new_doc.from_warehouse = source_doc.to_warehouse
        new_doc.to_warehouse = source_doc.from_warehouse
        new_doc.is_return = 1
        new_doc.service_job_card = doc.name

        for item in selected_items:
            if not item.get("qty_to_return"):
                frappe.throw(
                    _(
                        '<h4 class="text-center" style="background-color: yellow; font-weight: bold;">\
                    Can not process stock entry for empty quantity to return<h4>'
                    )
                )

            for entry in source_doc.items:
                if item.get("item") == entry.item_code:
                    new_doc.append(
                        "items",
                        {
                            "s_warehouse": entry.t_warehouse,
                            "t_warehouse": entry.s_warehouse,
                            "item_code": item.get("item"),
                            "item_name": entry.item_name,
                            "description": entry.description,
                            "item_group": entry.item_group,
                            "qty": item.get("qty_to_return"),
                            "transfer_qty": item.get("qty_to_return"),
                            "uom": entry.uom,
                            "stock_uom": entry.stock_uom,
                            "conversion_factor": entry.conversion_factor,
                            "expense_account": entry.expense_account,
                            "basic_rate": item.get("rate"),
                            "basic_amount": item.get("rate"),
                            "amount": item.get("rate"),
                            "cost_center": entry.cost_center,
                        },
                    )

        new_doc.save(ignore_permissions=True)
        new_doc.submit()
        if new_doc.get("name"):
            updated_supplied_parts(doc, selected_items, new_doc.get("name"))
            frappe.msgprint(
                "Stock Entry: {0} Created Successfully".format(
                    frappe.bold(new_doc.name)
                )
            )
        else:
            frappe.throw("Stock Entry was not created, try again")


def updated_supplied_parts(doc, selected_items, name):
    for row in doc.supplied_parts:
        if not row.is_billable:
            continue
        for d in selected_items:
            if row.item == d["item"]:
                row.qty_returned = d.get("qty_to_return")
                row.qty = cint(d.get("qty")) - cint(d.get("qty_to_return"))
                row.return_stock_enty = name
                if (cint(d.get("qty")) - cint(d.get("qty_to_return"))) == 0:
                    row.is_billable = 0
                    row.is_return = 1
    doc.save()
    doc.reload()


@frappe.whitelist()
def get_all_supplied_parts(job_card):
    return frappe.get_all(
        "Supplied Parts",
        filters={"parent": job_card, "is_billable": 1, "is_return": 0},
        fields=[
            "idx",
            "item",
            "item_name",
            "qty",
            "rate",
            "stock_entry",
            "parent",
            "parenttype",
        ],
        order_by="idx ASC",
        page_length=100,
    )
