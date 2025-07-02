import frappe
from frappe import _

@frappe.whitelist()
def get_fresh_colis_data(colis_id):
    """Récupère les données fraîches du colis pour mise à jour AJAX"""
    try:
        # Forcer la récupération des données fraîches depuis la base
        frappe.clear_cache()
        frappe.clear_document_cache('Colis', colis_id)
        
        # Récupérer le document Colis avec les données fraîches
        colis = frappe.get_doc('Colis', colis_id)
        
        # Recharger explicitement tous les articles pour avoir les données à jour
        for item in colis.articles:
            item.reload()
        
        # Préparer les données des articles
        articles_data = []
        for item in colis.articles:
            article_data = {
                'name': item.name,
                'article': item.article,
                'article_name': item.article_name if hasattr(item, 'article_name') else '',
                'quantite_totale': item.quantite_totale or 0,
                'quantite_livree': item.quantite_livree or 0,
                'quantite_restante': item.quantite_restante or 0,
                'statut_article': item.statut_article or 'En attente'
            }
            
            # Récupérer le nom de l'article si pas déjà présent
            if item.article and not article_data['article_name']:
                try:
                    item_doc = frappe.get_doc('Item', item.article)
                    article_data['article_name'] = item_doc.item_name
                except:
                    article_data['article_name'] = item.article
            
            articles_data.append(article_data)
        
        return {
            'success': True,
            'colis': {
                'name': colis.name,
                'status': colis.status,
                'client': colis.client,
                'date': str(colis.date) if colis.date else '',
                'articles': articles_data
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Erreur lors de la récupération des données fraîches du colis: {e}")
        return {
            'success': False,
            'message': f'Erreur: {str(e)}'
        }

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