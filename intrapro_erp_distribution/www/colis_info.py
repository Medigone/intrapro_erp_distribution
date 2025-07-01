import frappe
from frappe import _

def get_context(context):
    """Récupère les informations du colis pour l'affichage public"""
    # Récupérer l'ID du colis depuis les paramètres de l'URL
    colis_id = frappe.form_dict.get('id')
    
    if not colis_id:
        frappe.throw(_('ID du colis non spécifié'), frappe.ValidationError)
    
    try:
        # Récupérer le document Colis
        colis = frappe.get_doc('Colis', colis_id)
        
        # Ajouter les informations du client si disponible
        if colis.client:
            client = frappe.get_doc('Customer', colis.client)
            colis.client_name = client.customer_name
        
        # Récupérer les noms des articles
        for item in colis.articles:
            if item.article:
                item_doc = frappe.get_doc('Item', item.article)
                item.article_name = item_doc.item_name
        
        # Ajouter le colis au contexte
        context.colis = colis
        
        # Définir le titre de la page
        context.title = _("Informations Colis {0}").format(colis.name)
        
    except frappe.DoesNotExistError:
        frappe.throw(_('Colis non trouvé'), frappe.DoesNotExistError)
    except Exception as e:
        frappe.throw(_('Erreur lors de la récupération des informations du colis: {0}').format(str(e)))
    
    return context