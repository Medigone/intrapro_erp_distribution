frappe.pages['commande'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Commande',
		single_column: true
	});
	
	// Initialisation de la page
	frappe.require([
		'/assets/intrapro_erp_distribution/js/commande_ui.bundle.js'
	], function() {
		page.commande_view = new intrapro_erp_distribution.CommandeUI({
			wrapper: wrapper,
			page: page
		});
	});
}

frappe.pages['commande'].on_page_show = function(wrapper) {
	// Rafraîchir les données à chaque affichage de la page
	if (wrapper.commande_view) {
		wrapper.commande_view.refresh();
	}
}