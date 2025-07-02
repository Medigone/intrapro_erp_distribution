import frappe
from frappe import _

def get_context(context):
    """Récupère les informations du colis pour l'affichage public"""
    # Récupérer l'ID du colis depuis les paramètres de l'URL
    colis_id = frappe.form_dict.get('id')
    
    if not colis_id:
        frappe.throw(_('ID du colis non spécifié'), frappe.ValidationError)
    
    try:
        # Forcer la récupération des données fraîches depuis la base
        frappe.clear_cache()
        frappe.clear_document_cache('Colis', colis_id)
        
        # Récupérer le document Colis avec les données fraîches
        colis = frappe.get_doc('Colis', colis_id)
        
        # Recharger explicitement tous les articles pour avoir les données à jour
        for item in colis.articles:
            item.reload()
        
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
        # Au lieu de lever une exception, afficher une page d'erreur conviviale
        context.error = True
        context.error_title = _('Colis non trouvé')
        context.error_message = _('Le colis avec l\'ID "{0}" n\'existe pas ou a été supprimé.').format(colis_id)
        context.error_type = 'not_found'
        context.title = _('Erreur - Colis non trouvé')
        return context
        
    except Exception as e:
        # Gestion d'autres erreurs
        context.error = True
        context.error_title = _('Erreur système')
        context.error_message = _('Une erreur s\'est produite lors de la récupération des informations du colis: {0}').format(str(e))
        context.error_type = 'system_error'
        context.title = _('Erreur système')
        return context
    
    return context