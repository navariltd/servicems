# import frappe


def complete_service_job_card(doc, method=None):
    incomplete_tasks = [task.task_name for task in doc.tasks if task.completed == 0]
    
    if not incomplete_tasks:
        doc.status = "Completed"
