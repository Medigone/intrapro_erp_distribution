# apps/intrapro_erp_distribution/intrapro_erp_distribution/www/commande_detail/[name].py

import frappe
from frappe import _

def get_context(context):
    name = frappe.form_dict.name
    if not name:
        frappe.throw(_("Nom de la commande manquant."))

    doc = frappe.get_doc("Sales Order", name)

    customer = frappe.db.get_value("Portal User", {
        "parenttype": "Customer",
        "user": frappe.session.user
    }, "parent")

    if not customer or doc.customer != customer:
        frappe.throw(_("Accès non autorisé."))

    context.order = doc
    return context
