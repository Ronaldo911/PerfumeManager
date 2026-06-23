import os

DATA_DIR = "data"
IMG_DIR = os.path.join(DATA_DIR, "images")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")

DEFAULT_PIN = "4334"
RESET_PIN = "9999"

FILES = {
    "inventory": os.path.join(DATA_DIR, "inventory.csv"),
    "purchases": os.path.join(DATA_DIR, "purchases.csv"),
    "production": os.path.join(DATA_DIR, "production.csv"),
    "ventes": os.path.join(DATA_DIR, "ventes.csv"),
    "offres": os.path.join(DATA_DIR, "offres.csv"),
    "pertes": os.path.join(DATA_DIR, "pertes.csv"),
    "credits_history": os.path.join(DATA_DIR, "credits_history.csv"),
    "deletions_purchases": os.path.join(DATA_DIR, "deletions_purchases.csv"),
    "deletions_production": os.path.join(DATA_DIR, "deletions_production.csv"),
    "deletions_ventes": os.path.join(DATA_DIR, "deletions_ventes.csv"),
    "tailles": os.path.join(DATA_DIR, "tailles.csv"),
    "prix_vente": os.path.join(DATA_DIR, "prix_vente.csv"),
    "categories": os.path.join(DATA_DIR, "categories.csv"),
    "settings": os.path.join(DATA_DIR, "settings.csv"),
    "shop_config": os.path.join(DATA_DIR, "shop_config.csv"),
    "mouvements": os.path.join(DATA_DIR, "mouvements.csv"),
    "clients": os.path.join(DATA_DIR, "clients.csv")
}
