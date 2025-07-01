# Copyright (c) 2025, IntraPro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import qrcode
import io
import base64


class Colis(Document):
	def validate(self):
		# Générer le QR code à chaque sauvegarde
		self.generate_qr_code()
	
	@frappe.whitelist()
	def generate_qr_code(self):
		"""Génère un QR code pour le document Colis et le stocke directement comme pièce jointe"""
		if not self.name or self.name == "new-colis":
			return
		
		# Construire l'URL complète vers la page publique d'information du colis
		site_url = frappe.utils.get_url()
		public_url = f"{site_url}/colis_info?id={self.name}"
		
		# URL vers l'application Frappe (pour les utilisateurs authentifiés)
		app_url = f"{site_url}/app/colis/{self.name}"
		
		# Préparer les données à encoder dans le QR code
		# Format JSON pour inclure plus d'informations
		qr_data = {
			"id": self.name,
			"url": public_url,  # URL publique pour accès direct
			"app_url": app_url,  # URL de l'application pour les utilisateurs authentifiés
			"client": self.client if self.client else "",
			"date": str(self.date) if self.date else "",
			"status": self.status if self.status else ""
		}
		
		# Pour les scanners QR simples qui ne supportent que les URL, utiliser directement l'URL publique
		data = public_url
		
		# Créer le QR code avec des paramètres optimisés pour réduire la taille
		# Augmenter légèrement la version pour accommoder plus de données
		qr = qrcode.QRCode(
			version=4,  # Version plus élevée pour plus de données
			error_correction=qrcode.constants.ERROR_CORRECT_M,
			box_size=6,
			border=2,
		)
		qr.add_data(data)
		qr.make(fit=True)
		
		# Créer l'image
		img = qr.make_image(fill_color="black", back_color="white")
		
		# Préparer le buffer pour l'image
		buffer = io.BytesIO()
		img.save(buffer, format="PNG", optimize=True)  # Optimiser l'image PNG
		buffer.seek(0)
		
		# Nom du fichier QR code
		file_name = f"qr_code_{self.name}.png"
		
		# Supprimer les anciennes pièces jointes de QR code si elles existent
		existing_files = frappe.get_all(
			"File",
			filters={
				"attached_to_doctype": "Colis",
				"attached_to_name": self.name,
				"file_name": ["like", "qr_code_%"]
			},
			fields=["name"]
		)
		
		for file in existing_files:
			try:
				frappe.delete_doc("File", file.name)
			except Exception as e:
				frappe.log_error(f"Erreur lors de la suppression du fichier QR code: {e}")
		
		# Sauvegarder comme pièce jointe
		file_doc = frappe.get_doc({
			"doctype": "File",
			"file_name": file_name,
			"attached_to_doctype": "Colis",
			"attached_to_name": self.name,
			"content": buffer.getvalue(),
			"is_private": 0
		})
		
		# Insérer le nouveau fichier et récupérer l'URL
		file_url = file_doc.insert().file_url
		
		# Mettre à jour le champ image
		self.image = file_url
		
		# Ne plus utiliser le champ qr_code pour éviter l'erreur "Valeur trop grande"
		self.qr_code = None


@frappe.whitelist()
def get_item_from_barcode(barcode):
	"""Récupère les informations d'un article à partir de son code-barres
	
	Args:
		barcode (str): Le code-barres à rechercher
	
	Returns:
		dict: Les informations de l'article (name, item_name) ou None si non trouvé
	"""
	# Sauvegarder les permissions actuelles
	original_flags = {}
	if hasattr(frappe.local, 'flags'):
		original_flags = dict(frappe.local.flags)
	
	try:
		# Désactiver la vérification des permissions
		frappe.flags.ignore_permissions = True
		
		# Rechercher le code-barres dans Item Barcode
		parent = frappe.db.get_value("Item Barcode", {"barcode": barcode}, "parent")
		
		if parent:
			# Récupérer les détails de l'article
			item = frappe.db.get_value("Item", parent, ["name", "item_name"], as_dict=True)
			return item
		
		return None
	finally:
		# Restaurer les permissions originales
		if original_flags:
			frappe.local.flags = frappe._dict(original_flags)
		else:
			frappe.flags.ignore_permissions = False


@frappe.whitelist()
def download_qr_code(docname):
	"""Télécharge le QR code existant d'un colis ou en génère un nouveau si nécessaire
	
	Args:
		docname (str): Le nom du document Colis
	
	Returns:
		Response: Réponse HTTP avec le fichier QR code
	"""
	# Récupérer le document Colis
	doc = frappe.get_doc("Colis", docname)
	
	# Vérifier si une image QR code existe déjà
	if doc.image:
		# Récupérer le fichier existant
		file_path = frappe.get_site_path() + doc.image
		try:
			with open(file_path, 'rb') as f:
				content = f.read()
			
			# Renvoyer le fichier existant pour téléchargement
			frappe.response['filecontent'] = content
			frappe.response['filename'] = f"qr_code_{doc.name}.png"
			frappe.response['type'] = 'download'
			return
		except Exception:
			# Si le fichier n'est pas accessible, générer un nouveau QR code
			pass
	
	# Générer un nouveau QR code avec l'URL publique
	site_url = frappe.utils.get_url()
	public_url = f"{site_url}/colis_info?id={doc.name}"
	
	# Créer le QR code avec les mêmes paramètres optimisés que dans generate_qr_code
	qr = qrcode.QRCode(
		version=4,  # Version plus élevée pour plus de données
		error_correction=qrcode.constants.ERROR_CORRECT_M,
		box_size=6,
		border=2,
	)
	qr.add_data(public_url)  # Utiliser l'URL publique directement
	qr.make(fit=True)
	
	# Créer l'image
	img = qr.make_image(fill_color="black", back_color="white")
	
	# Préparer le buffer pour le téléchargement
	buffer = io.BytesIO()
	img.save(buffer, format="PNG", optimize=True)  # Optimiser l'image PNG
	buffer.seek(0)
	
	# Renvoyer le fichier pour téléchargement
	frappe.response['filecontent'] = buffer.getvalue()
	frappe.response['filename'] = f"qr_code_{doc.name}.png"
	frappe.response['type'] = 'download'
