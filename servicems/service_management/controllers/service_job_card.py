import frappe
from frappe.desk.form.assign_to import add


def complete_service_job_card(doc, method=None):
    incomplete_tasks = [task.task_name for task in doc.tasks if task.completed == 0]

    if not incomplete_tasks:
        doc.status = "Completed"


def update_task_status(doc, method=None):
    if not hasattr(doc, "_doc_before_save") or doc._doc_before_save is None:
        return

    _update_job_card_status(doc)
    _handle_deleted_tasks(doc)

    for task in doc.tasks:
        if task.task_name:
            _sync_task(doc, task)


def _update_job_card_status(doc):
    incomplete = [task.task_name for task in doc.tasks if task.completed == 0]

    if doc.status == "Completed" and incomplete:
        doc.status = "Repairing"
    
    if doc.status != "Completed" and not incomplete:
        doc.status = "Completed"


def _handle_deleted_tasks(doc):
    if not doc._doc_before_save:
        return

    old_task_names = {task.name for task in doc._doc_before_save.tasks}
    current_task_names = {task.name for task in doc.tasks}
    deleted_task_names = old_task_names - current_task_names

    for deleted_task_name in deleted_task_names:
        _delete_task_document(deleted_task_name)


def _delete_task_document(job_card_task_name):
    existing_task = frappe.db.get_value(
        "Task", {"job_card_task": job_card_task_name}, "name"
    )

    if existing_task:
        try:
            frappe.delete_doc("Task", existing_task, force=1)
        except Exception as e:
            frappe.log_error(f"Failed to delete task {existing_task}: {str(e)}")


def _sync_task(doc, task):
    existing_task = _find_existing_task(doc, task)

    if existing_task:
        _update_existing_task(doc, task, existing_task)
    else:
        _create_new_task(doc, task)


def _find_existing_task(doc, task):
    existing_task = frappe.db.get_value(
        "Task", {"job_card_task": task.name}, ["name", "status"], as_dict=True
    )

    if not existing_task:
        existing_task = _find_task_by_description(doc, task)

    return existing_task


def _find_task_by_description(doc, task):
    tasks_with_subject = frappe.get_all(
        "Task",
        filters={"subject": task.task_name},
        fields=["name", "status", "description"],
    )

    for t in tasks_with_subject:
        if t.description and doc.name in t.description:
            frappe.db.set_value("Task", t.name, "job_card_task", task.name)
            return {"name": t.name, "status": t.status}

    return None


def _update_existing_task(doc, task, existing_task):
    task_name = existing_task.get("name")

    _update_task_completion_status(task, existing_task)

    if task.mechanic:
        _assign_mechanic_to_task(doc, task, task_name)


def _update_task_completion_status(task, existing_task):
    task_name = existing_task.get("name")
    current_status = existing_task.get("status")

    if task.completed and current_status != "Completed":
        frappe.db.set_value("Task", task_name, "status", "Completed")
    elif not task.completed and current_status == "Completed":
        frappe.db.set_value("Task", task_name, "status", "Open")


def _assign_mechanic_to_task(doc, task, task_name):
    existing_assignments = frappe.get_all(
        "ToDo",
        filters={
            "reference_type": "Task",
            "reference_name": task_name,
            "allocated_to": task.mechanic,
            "status": "Open",
        },
    )

    if not existing_assignments:
        try:
            add(
                {
                    "doctype": "Task",
                    "name": task_name,
                    "assign_to": [task.mechanic],
                    "description": f"Updated from Service Job Card: {doc.name}",
                }
            )
        except Exception as e:
            frappe.log_error(f"Failed to assign task: {str(e)}")


def _create_new_task(doc, task):
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
