// Copyright (c) 2025, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.query_reports["Vehicle Repair History"] = {
  filters: [
    {
      fieldname: "company",
      label: __("Company"),
      fieldtype: "Link",
      options: "Company",
      default: frappe.defaults.get_user_default("Company"),
      reqd: 1,
    },
    {
      fieldname: "service_item_name",
      label: __("Service Vehicle"),
      fieldtype: "Link",
      options: "Service Vehicle",
    },
    {
      fieldname: "service_job_card",
      label: __("Service Job Card"),
      fieldtype: "Link",
      options: "Service Job Card",
      get_query: function () {
        let service_item_name =
          frappe.query_report.get_filter_value("service_item_name");
        if (service_item_name) {
          return {
            filters: {
              service_item_name: service_item_name,
			  status: "Completed",
            },
          };
        }
      },
    },
    {
      fieldname: "service_booking",
      label: __("Service Booking"),
      fieldtype: "Link",
      options: "Service Booking",
	  get_query: function () {
		let service_item_name = frappe.query_report.get_filter_value("service_item_name");
		if (service_item_name) {
			return {
				filters: {
					service_vehicle: service_item_name,
					status: "Completed",
				},
			};
		}
	  }
    },
  ],
};
