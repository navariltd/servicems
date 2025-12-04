import frappe
from frappe.desk.form.assign_to import add


def complete_service_job_card(doc, method=None):
    incomplete_tasks = [task.task_name for task in doc.tasks if task.completed == 0]

    if not incomplete_tasks:
        doc.status = "Completed"


def update_task_status(doc, method=None):
    if not hasattr(doc, "_doc_before_save") or doc._doc_before_save is None:
        return

    incomplete = [task.task_name for task in doc.tasks if task.completed == 0]

    if doc.status == "Completed" and incomplete:
        doc.status = "Repairing"

    if doc._doc_before_save:
        old_task_names = {task.name for task in doc._doc_before_save.tasks}
        current_task_names = {task.name for task in doc.tasks}
        deleted_task_names = old_task_names - current_task_names

        for deleted_task_name in deleted_task_names:
            existing_task = frappe.db.get_value(
                "Task", {"job_card_task": deleted_task_name}, "name"
            )

            if existing_task:
                try:
                    frappe.delete_doc("Task", existing_task, force=1)
                except Exception as e:
                    frappe.log_error(f"Failed to delete task {existing_task}: {str(e)}")

    for task in doc.tasks:
        if not task.task_name:
            continue

        existing_task = frappe.db.get_value(
            "Task", {"job_card_task": task.name}, ["name", "status"], as_dict=True
        )

        if not existing_task:
            tasks_with_subject = frappe.get_all(
                "Task",
                filters={
                    "subject": task.task_name,
                },
                fields=["name", "status", "description"],
            )

            for t in tasks_with_subject:
                if t.description and doc.name in t.description:
                    existing_task = {"name": t.name, "status": t.status}
                    frappe.db.set_value("Task", t.name, "job_card_task", task.name)
                    break

        if existing_task:
            if task.completed and existing_task.get("status") != "Completed":
                frappe.db.set_value("Task", existing_task.get("name"), "status", "Completed")
            elif not task.completed and existing_task.get("status") == "Completed":
                frappe.db.set_value("Task", existing_task.get("name"), "status", "Open")

            if task.mechanic:
                existing_assignments = frappe.get_all(
                    "ToDo",
                    filters={
                        "reference_type": "Task",
                        "reference_name": existing_task.get("name"),
                        "allocated_to": task.mechanic,
                        "status": "Open",
                    },
                )

                if not existing_assignments:
                    try:
                        add(
                            {
                                "doctype": "Task",
                                "name": existing_task.get("name"),
                                "assign_to": [task.mechanic],
                                "description": f"Updated from Service Job Card: {doc.name}",
                            }
                        )
                    except Exception as e:
                        frappe.log_error(f"Failed to assign task: {str(e)}")
        else:
            task_doc = frappe.get_doc(
                {
                    "doctype": "Task",
                    "subject": task.task_name,
                    "status": "Completed" if task.completed else "Open",
                    "job_card_task": task.name,
                    "company": doc.company,
                    "description": f"Task for Service Job Card: {doc.name}\nTemplate: {task.template or 'N/A'}",
                }
            )

            task_doc.insert(ignore_permissions=True)

            if task.mechanic:
                try:
                    add(
                        {
                            "doctype": "Task",
                            "name": task_doc.name,
                            "assign_to": [task.mechanic],
                            "description": f"Assigned from Service Job Card: {doc.name}",
                        }
                    )
                except Exception as e:
                    frappe.log_error(f"Failed to assign new task: {str(e)}")
