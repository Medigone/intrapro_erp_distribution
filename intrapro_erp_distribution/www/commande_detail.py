import frappe

def get_context(context):
    sales_order_name = frappe.form_dict.name

    doc = frappe.get_doc("Sales Order", sales_order_name)

    # Sécurité : vérifier que l'utilisateur est lié au client
    customer = frappe.db.get_value(
        "Portal User", {"parenttype": "Customer", "user": frappe.session.user}, "parent"
    )
    if not customer or doc.customer != customer:
        frappe.throw("Accès non autorisé.")

    context.order = doc
