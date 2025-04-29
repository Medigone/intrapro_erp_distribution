(() => {
  // ../intrapro_erp_distribution/intrapro_erp_distribution/public/js/commande_ui.bundle.js
  frappe.provide("intrapro_erp_distribution");
  intrapro_erp_distribution.CommandeUI = class CommandeUI {
    constructor(opts) {
      $.extend(this, opts);
      this.make();
    }
    make() {
      this.prepare_dom();
      this.setup_header();
      this.setup_history_section();
      this.setup_new_order_section();
      this.bind_events();
      this.refresh();
    }
    prepare_dom() {
      this.$wrapper = $(this.wrapper).find(".layout-main-section");
      this.$wrapper.empty();
      this.$wrapper.append(`
			<div class="commande-container">
				<div class="history-section section-margin"></div>
				<div class="new-order-section section-margin"></div>
			</div>
		`);
      $("<style>").text(`
			.commande-container {
				display: flex;
				flex-direction: column;
				gap: 20px;
			}
			.section-margin {
				margin-bottom: 15px;
			}
			.section-title {
				font-size: 16px;
				font-weight: bold;
				margin-bottom: 10px;
				padding-bottom: 8px;
				border-bottom: 1px solid #d1d8dd;
			}
			.order-list {
				border: 1px solid #d1d8dd;
				border-radius: 4px;
			}
			.order-item {
				padding: 10px;
				border-bottom: 1px solid #d1d8dd;
				cursor: pointer;
			}
			.order-item:last-child {
				border-bottom: none;
			}
			.order-item:hover {
				background-color: #f7fafc;
			}
			.order-details {
				display: flex;
				justify-content: space-between;
			}
			.btn-new-order {
				margin-top: 10px;
			}
			.filter-section {
				display: flex;
				gap: 10px;
				margin-bottom: 15px;
			}
		`).appendTo(this.$wrapper);
    }
    setup_header() {
      let $historySection = this.$wrapper.find(".history-section");
      $historySection.append(`
			<h3 class="section-title">Historique des Commandes</h3>
			<div class="filter-section">
				<input type="text" class="form-control search-input" placeholder="Rechercher une commande...">
				<select class="form-control status-filter">
					<option value="">Tous les statuts</option>
					<option value="En attente">En attente</option>
					<option value="Confirm\xE9e">Confirm\xE9e</option>
					<option value="Exp\xE9di\xE9e">Exp\xE9di\xE9e</option>
					<option value="Livr\xE9e">Livr\xE9e</option>
					<option value="Annul\xE9e">Annul\xE9e</option>
				</select>
				<select class="form-control date-filter">
					<option value="all">Toutes les dates</option>
					<option value="today">Aujourd'hui</option>
					<option value="week">Cette semaine</option>
					<option value="month">Ce mois</option>
					<option value="year">Cette ann\xE9e</option>
				</select>
			</div>
		`);
    }
    setup_history_section() {
      let $historySection = this.$wrapper.find(".history-section");
      $historySection.append(`
			<div class="order-list"></div>
		`);
    }
    setup_new_order_section() {
      let $newOrderSection = this.$wrapper.find(".new-order-section");
      $newOrderSection.append(`
			<h3 class="section-title">Nouvelle Commande</h3>
			<p>Cr\xE9ez une nouvelle commande en cliquant sur le bouton ci-dessous :</p>
			<button class="btn btn-primary btn-new-order">Cr\xE9er une Nouvelle Commande</button>
		`);
    }
    bind_events() {
      let me = this;
      this.$wrapper.find(".btn-new-order").on("click", function() {
        frappe.new_doc("Sales Order", {
          customer: frappe.user_info().user_fullname
        });
      });
      this.$wrapper.find(".search-input").on("input", function() {
        me.refresh();
      });
      this.$wrapper.find(".status-filter, .date-filter").on("change", function() {
        me.refresh();
      });
    }
    refresh() {
      let me = this;
      let searchText = this.$wrapper.find(".search-input").val();
      let statusFilter = this.$wrapper.find(".status-filter").val();
      let dateFilter = this.$wrapper.find(".date-filter").val();
      let filters = [
        ["customer", "=", frappe.user_info().user_fullname]
      ];
      if (statusFilter) {
        filters.push(["status", "=", statusFilter]);
      }
      if (dateFilter && dateFilter !== "all") {
        let dateObj = new Date();
        let startDate = "";
        if (dateFilter === "today") {
          startDate = frappe.datetime.get_today();
        } else if (dateFilter === "week") {
          dateObj.setDate(dateObj.getDate() - dateObj.getDay());
          startDate = frappe.datetime.obj_to_str(dateObj);
        } else if (dateFilter === "month") {
          dateObj.setDate(1);
          startDate = frappe.datetime.obj_to_str(dateObj);
        } else if (dateFilter === "year") {
          dateObj.setMonth(0, 1);
          startDate = frappe.datetime.obj_to_str(dateObj);
        }
        filters.push(["transaction_date", ">=", startDate]);
      }
      frappe.call({
        method: "frappe.client.get_list",
        args: {
          doctype: "Sales Order",
          filters,
          fields: ["name", "transaction_date", "status", "grand_total", "currency"],
          order_by: "transaction_date desc"
        },
        callback: function(r) {
          me.render_order_list(r.message, searchText);
        }
      });
    }
    render_order_list(orders, searchText) {
      let $orderList = this.$wrapper.find(".order-list");
      $orderList.empty();
      if (!orders || orders.length === 0) {
        $orderList.append(`
				<div class="text-muted text-center p-4">
					Aucune commande trouv\xE9e
				</div>
			`);
        return;
      }
      if (searchText) {
        searchText = searchText.toLowerCase();
        orders = orders.filter(
          (order) => order.name.toLowerCase().includes(searchText)
        );
      }
      orders.forEach((order) => {
        let formattedDate = frappe.datetime.str_to_user(order.transaction_date);
        let formattedAmount = format_currency(order.grand_total, order.currency);
        let $orderItem = $(`
				<div class="order-item" data-name="${order.name}">
					<div class="order-details">
						<div>
							<strong>${order.name}</strong>
							<div class="text-muted">${formattedDate}</div>
						</div>
						<div>
							<span class="status-indicator ${this.get_status_color(order.status)}">
								${order.status}
							</span>
							<div class="text-right">${formattedAmount}</div>
						</div>
					</div>
				</div>
			`);
        $orderItem.on("click", function() {
          frappe.set_route("Form", "Sales Order", $(this).attr("data-name"));
        });
        $orderList.append($orderItem);
      });
    }
    get_status_color(status) {
      const statusColors = {
        "En attente": "orange",
        "Confirm\xE9e": "blue",
        "Exp\xE9di\xE9e": "purple",
        "Livr\xE9e": "green",
        "Annul\xE9e": "red",
        "Draft": "orange",
        "On Hold": "orange",
        "To Deliver and Bill": "blue",
        "To Bill": "blue",
        "To Deliver": "blue",
        "Completed": "green",
        "Cancelled": "red",
        "Closed": "grey"
      };
      return statusColors[status] || "grey";
    }
  };
})();
//# sourceMappingURL=commande_ui.bundle.XXQAJSYY.js.map
