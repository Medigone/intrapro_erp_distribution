// Copyright (c) 2025, IntraPro and contributors
// For license information, please see license.txt

frappe.ui.form.on("Colis", {
	refresh(frm) {
		// Ajouter un bouton pour scanner les articles
		frm.add_custom_button(__('Scanner Article'), function() {
			// Initialiser le scanner
			const scanner = new frappe.ui.Scanner({
				dialog: true, // Ouvrir le scanner dans une boîte de dialogue
				multiple: true, // Permettre de scanner plusieurs articles
				on_scan(data) {
					// Traiter le code-barres scanné
					traiter_article_scanne(frm, data.decodedText);
				}
			});
		}, __('Actions'));
	},
});

/**
 * Traite un article scanné et l'ajoute à la table enfant 'articles'
 * @param {Object} frm - L'objet formulaire Frappe
 * @param {String} code_barre - Le code-barres scanné
 */
function traiter_article_scanne(frm, code_barre) {
	// Vérifier si le code-barres correspond à un article existant
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'Item',
			filters: {
				barcode: code_barre
			},
			fields: ['name', 'item_name']
		},
		callback: function(r) {
			if (r.message && r.message.length > 0) {
				const article = r.message[0];
				
				// Vérifier si l'article est déjà dans la table
				let existe = false;
				let row_idx = null;
				
				$.each(frm.doc.articles || [], function(i, row) {
					if (row.article === article.name) {
						existe = true;
						row_idx = i;
						return false; // Sortir de la boucle
					}
				});
				
				if (existe) {
					// Incrémenter la quantité si l'article existe déjà
					frm.doc.articles[row_idx].quantite += 1;
				} else {
					// Ajouter un nouvel article à la table
					const child = frm.add_child('articles');
					child.article = article.name;
					child.quantite = 1;
				}
				
				// Rafraîchir la table
				frm.refresh_field('articles');
				
				// Afficher un message de confirmation
				frappe.show_alert({
					message: __('Article {0} ajouté', [article.item_name || article.name]),
					indicator: 'green'
				}, 3);
			} else {
				// Aucun article trouvé avec ce code-barres
				frappe.show_alert({
					message: __('Aucun article trouvé avec le code-barres: {0}', [code_barre]),
					indicator: 'red'
				}, 3);
			}
		}
	});
}
