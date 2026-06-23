import os
import pandas as pd
import streamlit as st
from datetime import datetime
from utils.constants import FILES, DATA_DIR, IMG_DIR, BACKUP_DIR
from utils.helpers import clean_numeric, new_id

class BaseModel:
    @staticmethod
    @staticmethod
    def _get_connection():
        from streamlit_gsheets import GSheetsConnection
        return st.connection("gsheets", type=GSheetsConnection)

    @staticmethod
    def load_df(key):
        """Load data from Google Sheets to session state if not already loaded"""
        if key not in st.session_state:
            try:
                conn = BaseModel._get_connection()
                df = conn.read(worksheet=key, ttl=0)
                if df is None or df.empty:
                    df = pd.DataFrame()
                    # It's fine if the dataframe is empty, we just need it not to be None.
                    # We will apply columns cleaning next.
                    # Ensure numeric columns are clean and string columns are type-safe (not float64 NaN)
                    if key == "inventory":
                        for col in ["Quantite_ML", "CUMP", "Valeur_Stock_Totale"]:
                            if col in df.columns:
                                df[col] = df[col].apply(clean_numeric)
                        for col in ["ID", "Nom", "Categorie"]:
                            if col in df.columns:
                                df[col] = df[col].fillna("").astype(str)
                    elif key == "purchases":
                        for col in ["Quantite_ML", "Prix_Total", "CUMP_Achat"]:
                            if col in df.columns:
                                df[col] = df[col].apply(clean_numeric)
                        for col in ["ID", "Date", "Categorie", "Nom", "Qualite", "Commentaire", "Image_Path"]:
                            if col in df.columns:
                                df[col] = df[col].fillna("").astype(str)
                    elif key == "production":
                        for col in ["Quantite_Base_ML", "Quantite_Alcool_ML", "Quantite_Flacons",
                                    "Cout_Base", "Cout_Alcool", "Cout_Flacon", "Cout_Total", "Cout_Unitaire"]:
                            if col in df.columns:
                                df[col] = df[col].apply(clean_numeric)
                        for col in ["ID", "Date", "Nom_Base", "Qualite_Base", "Nom_Flacon", "Taille_Flacon", "Nom_Parfum", "Nom_Alcool", "Type_Production"]:
                            if col in df.columns:
                                df[col] = df[col].fillna("").astype(str)
                    elif key == "ventes":
                        for col in ["Quantite", "Prix_Unitaire", "Remise", "CA_Avant", "CA_Reel",
                                    "Montant_Recu", "Cout_Revient", "Marge"]:
                            if col in df.columns:
                                df[col] = df[col].apply(clean_numeric)
                        for col in ["ID", "Date", "Client", "Type_Vente", "Nom_Parfum", "Qualite", "Taille", "Type_Remise"]:
                            if col in df.columns:
                                df[col] = df[col].fillna("").astype(str)
                    elif key == "shop_config":
                        for col in ["Boutique_Nom", "Logo_Path", "Theme_Couleur", "Date_Creation"]:
                            if col in df.columns:
                                df[col] = df[col].fillna("").astype(str)
                    elif key == "categories":
                        for col in ["ID", "Nom", "Couleur", "Date_Ajout"]:
                            if col in df.columns:
                                df[col] = df[col].fillna("").astype(str)
                    elif key == "mouvements":
                        for col in ["Quantite", "Valeur", "Stock_Avant", "Stock_Apres"]:
                            if col in df.columns:
                                df[col] = df[col].apply(clean_numeric)
                        for col in ["ID", "Date", "Type", "Reference", "Article"]:
                            if col in df.columns:
                                df[col] = df[col].fillna("").astype(str)
                    elif key == "tailles":
                        for col in ["ID", "Taille"]:
                            if col in df.columns:
                                df[col] = df[col].fillna("").astype(str)
                    elif key == "prix_vente":
                        for col in ["ID", "Taille"]:
                            if col in df.columns:
                                df[col] = df[col].fillna("").astype(str)
                        if "Prix_TND" in df.columns:
                            df["Prix_TND"] = df["Prix_TND"].apply(clean_numeric)
                    elif key == "offres":
                        for col in ["ID", "Date", "Client", "Type_Vente", "Nom_Parfum", "Qualite", "Taille"]:
                            if col in df.columns:
                                df[col] = df[col].fillna("").astype(str)
                        for col in ["Quantite", "Cout_Revient"]:
                            if col in df.columns:
                                df[col] = df[col].apply(clean_numeric)
                    elif key == "pertes":
                        for col in ["ID", "Date", "Article", "Raison"]:
                            if col in df.columns:
                                df[col] = df[col].fillna("").astype(str)
                        for col in ["Quantite", "Cout"]:
                            if col in df.columns:
                                df[col] = df[col].apply(clean_numeric)
                    elif key == "credits_history":
                        for col in ["ID", "Date_Vente", "Client", "Nom_Parfum", "Taille"]:
                            if col in df.columns:
                                df[col] = df[col].fillna("").astype(str)
                        for col in ["Montant_Dette", "Montant_Paye", "Reste"]:
                            if col in df.columns:
                                df[col] = df[col].apply(clean_numeric)
                    elif key == "deletions_purchases":
                        for col in ["ID", "Date_Suppression", "Date_Achat", "Categorie", "Nom"]:
                            if col in df.columns:
                                df[col] = df[col].fillna("").astype(str)
                        for col in ["Quantite_ML", "Prix_Total"]:
                            if col in df.columns:
                                df[col] = df[col].apply(clean_numeric)
                    elif key == "deletions_production":
                        for col in ["ID", "Date_Suppression", "Date_Production", "Nom_Parfum"]:
                            if col in df.columns:
                                df[col] = df[col].fillna("").astype(str)
                        for col in ["Quantite_Flacons", "Cout_Total"]:
                            if col in df.columns:
                                df[col] = df[col].apply(clean_numeric)
                    elif key == "deletions_ventes":
                        for col in ["ID", "Date_Suppression", "Date_Vente", "Nom_Parfum"]:
                            if col in df.columns:
                                df[col] = df[col].fillna("").astype(str)
                        for col in ["Quantite", "CA_Reel"]:
                            if col in df.columns:
                                df[col] = df[col].apply(clean_numeric)
                    st.session_state[key] = df
            except Exception as e:
                st.error(f"Erreur Google Sheets pour '{key}': {e}")
                st.info("Vérifiez votre fichier .streamlit/secrets.toml et les noms de vos onglets Google Sheets.")
                st.session_state[key] = pd.DataFrame()
        return st.session_state[key]

    @staticmethod
    def save_df(key):
        if key in st.session_state:
            try:
                df = st.session_state[key]
                conn = BaseModel._get_connection()
                conn.update(worksheet=key, data=df)
                return True
            except Exception as e:
                st.error(f"Erreur lors de la sauvegarde sur Google Sheets pour '{key}': {e}")
                return False

    @staticmethod
    def log_movement(m_type, ref_id, article, qte, valeur, stock_avant, stock_apres):
        """Logs a movement to mouvements.csv"""
        df_mov = BaseModel.load_df("mouvements")
        new_mov = {
            "ID": new_id(),
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Type": m_type,
            "Reference": ref_id,
            "Article": article,
            "Quantite": qte,
            "Valeur": valeur,
            "Stock_Avant": stock_avant,
            "Stock_Apres": stock_apres
        }
        df_mov = pd.concat([df_mov, pd.DataFrame([new_mov])], ignore_index=True)
        st.session_state["mouvements"] = df_mov
        BaseModel.save_df("mouvements")

    @staticmethod
    def log_deletion(module, item_id, snapshot_json, pin):
        """Logs a deletion to deletions_log.csv or corresponding file"""
        # Determine specific delete log files for compatibility
        log_key = f"deletions_{module.lower()}"
        if log_key not in FILES:
            # Fallback to general deletions log if specific file key not found
            log_key = "deletions_log"
            if log_key not in FILES:
                FILES["deletions_log"] = os.path.join(DATA_DIR, "deletions_log.csv")
        
        df_del = BaseModel.load_df(log_key)
        
        if log_key == "deletions_purchases":
            archive = {
                "ID": item_id,
                "Date_Suppression": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Date_Achat": snapshot_json.get("Date", ""),
                "Categorie": snapshot_json.get("Categorie", ""),
                "Nom": snapshot_json.get("Nom", ""),
                "Quantite_ML": snapshot_json.get("Quantite_ML", 0),
                "Prix_Total": snapshot_json.get("Prix_Total", 0)
            }
        elif log_key == "deletions_production":
            archive = {
                "ID": item_id,
                "Date_Suppression": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Date_Production": snapshot_json.get("Date", ""),
                "Nom_Parfum": snapshot_json.get("Nom_Parfum", ""),
                "Quantite_Flacons": snapshot_json.get("Quantite_Flacons", 0),
                "Cout_Total": snapshot_json.get("Cout_Total", 0)
            }
        elif log_key == "deletions_ventes":
            archive = {
                "ID": item_id,
                "Date_Suppression": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Date_Vente": snapshot_json.get("Date", ""),
                "Nom_Parfum": snapshot_json.get("Nom_Parfum", ""),
                "Quantite": snapshot_json.get("Quantite", 0),
                "CA_Reel": snapshot_json.get("CA_Reel", 0)
            }
        else:
            archive = {
                "ID": item_id,
                "Date_Suppression": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Module": module,
                "Snapshot": str(snapshot_json),
                "PIN": pin
            }
            
        df_del = pd.concat([df_del, pd.DataFrame([archive])], ignore_index=True)
        st.session_state[log_key] = df_del
        BaseModel.save_df(log_key)
