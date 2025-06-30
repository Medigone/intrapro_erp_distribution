import frappe
from frappe import _
from frappe.utils import nowdate


def create_delivery_note_from_sales_order(doc, method):
    """
    Crée automatiquement une Delivery Note à partir d'une Sales Order lors de sa soumission.
    
    Args:
        doc (object): Document Sales Order soumis
        method (str): Méthode de hook appelée (on_submit)
    
    Returns:
        object: Document Delivery Note créé
    """
    try:
        # Vérifier si la Sales Order a des articles à livrer
        if not doc.items:
            frappe.msgprint(_("Aucun article à livrer dans cette commande"))
            return
            
        # Créer une nouvelle Delivery Note
        delivery_note = frappe.new_doc("Delivery Note")
        
        # Copier les champs principaux de la Sales Order
        delivery_note.customer = doc.customer
        delivery_note.customer_name = doc.customer_name
        delivery_note.posting_date = nowdate()
        delivery_note.company = doc.company
        delivery_note.currency = doc.currency
        delivery_note.selling_price_list = doc.selling_price_list
        delivery_note.conversion_rate = doc.conversion_rate
        delivery_note.sales_order = doc.name
        
        # Copier le champ personnalisé custom_type
        if hasattr(doc, 'custom_type'):
            delivery_note.custom_type = doc.custom_type
        
        # Copier les informations d'adresse
        if doc.shipping_address_name:
            delivery_note.shipping_address_name = doc.shipping_address_name
        
        if doc.customer_address:
            delivery_note.customer_address = doc.customer_address
        
        # Copier les articles de la Sales Order
        for item in doc.items:
            delivery_item = delivery_note.append("items", {})
            delivery_item.item_code = item.item_code
            delivery_item.item_name = item.item_name
            delivery_item.description = item.description
            delivery_item.qty = item.qty
            delivery_item.uom = item.uom
            delivery_item.stock_uom = item.stock_uom
            delivery_item.rate = item.rate
            delivery_item.amount = item.amount
            delivery_item.warehouse = item.warehouse
            delivery_item.against_sales_order = doc.name
            delivery_item.so_detail = item.name
        
        # Ajouter les taxes si présentes
        if doc.taxes_and_charges and doc.taxes:
            delivery_note.taxes_and_charges = doc.taxes_and_charges
            for tax in doc.taxes:
                delivery_tax = delivery_note.append("taxes", {})
                delivery_tax.charge_type = tax.charge_type
                delivery_tax.account_head = tax.account_head
                delivery_tax.description = tax.description
                delivery_tax.rate = tax.rate
                delivery_tax.tax_amount = tax.tax_amount
                delivery_tax.total = tax.total
        
        # Sauvegarder comme brouillon
        delivery_note.flags.ignore_permissions = True
        delivery_note.insert()
        
        # Informer l'utilisateur
        custom_type_msg = ""
        if hasattr(doc, 'custom_type') and doc.custom_type:
            custom_type_msg = _(" de type '{0}'").format(doc.custom_type)
            
        frappe.msgprint(
            _("Bon de livraison {0} créé{1}").format(
                "<a href='/app/delivery-note/{0}'>{0}</a>".format(delivery_note.name),
                custom_type_msg
            )
        )
        
        return delivery_note
        
    except Exception as e:
        frappe.log_error(f"Erreur lors de la création du bon de livraison: {str(e)}", 
                        "Sales Order to Delivery Note")
        frappe.msgprint(_("Erreur lors de la création du bon de livraison. Veuillez vérifier les logs."))


def cancel_linked_delivery_notes(doc, method):
    """
    Annule ou supprime automatiquement les bons de livraison liés à une Sales Order lorsque celle-ci est annulée.
    
    Args:
        doc (object): Document Sales Order annulé
        method (str): Méthode de hook appelée (on_cancel)
    """
    try:
        # Rechercher tous les bons de livraison liés à cette commande (soumis)
        submitted_delivery_notes = frappe.get_all(
            "Delivery Note",
            filters={
                "against_sales_order": doc.name,  # Utilisation du champ correct
                "docstatus": 1  # Documents soumis
            },
            pluck="name"
        )
        
        # Rechercher tous les bons de livraison liés à cette commande (brouillons)
        draft_delivery_notes = frappe.get_all(
            "Delivery Note",
            filters={
                "against_sales_order": doc.name,  # Utilisation du champ correct
                "docstatus": 0  # Documents en brouillon
            },
            pluck="name"
        )
        
        # Si aucun bon de livraison n'est trouvé, essayer avec un autre champ possible
        if not submitted_delivery_notes and not draft_delivery_notes:
            # Essayer avec le champ 'sales_order' s'il existe
            submitted_delivery_notes = frappe.db.sql("""
                SELECT name FROM `tabDelivery Note` 
                WHERE sales_order = %s AND docstatus = 1
            """, (doc.name,), as_dict=0)
            submitted_delivery_notes = [d[0] for d in submitted_delivery_notes] if submitted_delivery_notes else []
            
            draft_delivery_notes = frappe.db.sql("""
                SELECT name FROM `tabDelivery Note` 
                WHERE sales_order = %s AND docstatus = 0
            """, (doc.name,), as_dict=0)
            draft_delivery_notes = [d[0] for d in draft_delivery_notes] if draft_delivery_notes else []
        
        # Si toujours aucun bon de livraison n'est trouvé, essayer avec les items
        if not submitted_delivery_notes and not draft_delivery_notes:
            # Rechercher dans les items des bons de livraison
            submitted_delivery_notes = frappe.db.sql("""
                SELECT DISTINCT parent FROM `tabDelivery Note Item` 
                WHERE against_sales_order = %s AND docstatus = 1
            """, (doc.name,), as_dict=0)
            submitted_delivery_notes = [d[0] for d in submitted_delivery_notes] if submitted_delivery_notes else []
            
            draft_delivery_notes = frappe.db.sql("""
                SELECT DISTINCT parent FROM `tabDelivery Note Item` 
                WHERE against_sales_order = %s AND docstatus = 0
            """, (doc.name,), as_dict=0)
            draft_delivery_notes = [d[0] for d in draft_delivery_notes] if draft_delivery_notes else []
        
        cancelled_notes = []
        deleted_notes = []
        
        # Traiter les bons de livraison soumis (à annuler)
        for dn in submitted_delivery_notes:
            try:
                # Récupérer le document complet
                delivery_note = frappe.get_doc("Delivery Note", dn)
                
                # Annuler le bon de livraison
                delivery_note.flags.ignore_permissions = True
                delivery_note.cancel()
                
                cancelled_notes.append(dn)
            except Exception as e:
                frappe.log_error(
                    f"Erreur lors de l'annulation du bon de livraison {dn}: {str(e)}",
                    "Cancel Delivery Note"
                )
        
        # Traiter les bons de livraison en brouillon (à supprimer)
        for dn in draft_delivery_notes:
            try:
                # Récupérer le document complet
                delivery_note = frappe.get_doc("Delivery Note", dn)
                
                # Supprimer le bon de livraison en brouillon
                delivery_note.flags.ignore_permissions = True
                frappe.delete_doc("Delivery Note", dn, force=1)
                
                deleted_notes.append(dn)
            except Exception as e:
                frappe.log_error(
                    f"Erreur lors de la suppression du bon de livraison en brouillon {dn}: {str(e)}",
                    "Delete Draft Delivery Note"
                )
        
        # Informer l'utilisateur des bons de livraison annulés
        if cancelled_notes:
            if len(cancelled_notes) == 1:
                frappe.msgprint(
                    _("Le bon de livraison {0} a été automatiquement annulé").format(
                        "<a href='/app/delivery-note/{0}'>{0}</a>".format(cancelled_notes[0])
                    )
                )
            else:
                note_links = ", ".join([f"<a href='/app/delivery-note/{dn}'>{dn}</a>" for dn in cancelled_notes])
                frappe.msgprint(
                    _("Les bons de livraison suivants ont été automatiquement annulés: {0}").format(note_links)
                )
        
        # Informer l'utilisateur des bons de livraison supprimés
        if deleted_notes:
            if len(deleted_notes) == 1:
                frappe.msgprint(_("Le bon de livraison en brouillon {0} a été automatiquement supprimé").format(deleted_notes[0]))
            else:
                frappe.msgprint(_("Les bons de livraison en brouillon suivants ont été automatiquement supprimés: {0}").format(", ".join(deleted_notes)))
    
    except Exception as e:
        frappe.log_error(
            f"Erreur lors de l'annulation des bons de livraison liés à la commande {doc.name}: {str(e)}",
            "Sales Order Cancel Hook"
        )
        frappe.msgprint(_("Erreur lors de l'annulation des bons de livraison liés. Veuillez vérifier les logs."))