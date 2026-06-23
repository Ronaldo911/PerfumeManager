import os
import pandas as pd
import streamlit as st
from datetime import datetime
from models.base_model import BaseModel
from services.stock_service import StockService
from controllers.security_controller import SecurityController
from utils.constants import IMG_DIR
from utils.helpers import clean_numeric, new_id

class AchatsController:
    @staticmethod
    def create_achat(date_achat, categorie, nom, qualite, genre, saison, quantite, prix_total, fournisseur, commentaire, uploaded_img):
        if not nom or quantite <= 0 or prix_total <= 0:
            return False, "Veuillez remplir tous les champs obligatoires (Nom, Quantité, Prix)."
            
        # Save image if provided
        img_path = ""
        if uploaded_img:
            img_filename = f"{new_id()}_{uploaded_img.name}"
            img_path = os.path.join(IMG_DIR, img_filename)
            try:
                with open(img_path, "wb") as f:
                    f.write(uploaded_img.getbuffer())
            except Exception as e:
                return False, f"Erreur lors de l'enregistrement de l'image : {e}"
                
        cump_achat = prix_total / quantite
        
        df_purch = BaseModel.load_df("purchases")
        achat_id = new_id()
        new_achat = {
            "ID": achat_id,
            "Date": date_achat.strftime("%Y-%m-%d") if hasattr(date_achat, "strftime") else str(date_achat),
            "Categorie": categorie,
            "Nom": nom,
            "Qualite": qualite,
            "Genre": genre,
            "Saison": saison,
            "Quantite_ML": quantite,
            "Prix_Total": prix_total,
            "CUMP_Achat": cump_achat,
            "Commentaire": commentaire,
            "Image_Path": img_path
        }
        df_purch = pd.concat([df_purch, pd.DataFrame([new_achat])], ignore_index=True)
        st.session_state["purchases"] = df_purch
        BaseModel.save_df("purchases")
        
        # Calculate stock before and after for movement log
        stock_before = StockService.get_stock(nom, qualite, categorie)
        StockService.rebuild_inventory()
        stock_after = StockService.get_stock(nom, qualite, categorie)
        
        # Log movement
        BaseModel.log_movement(
            m_type="ACHAT",
            ref_id=achat_id,
            article=nom,
            qte=quantite_ml,
            valeur=prix_total,
            stock_avant=stock_before,
            stock_apres=stock_after
        )
        
        return True, "Achat enregistré avec succès!"

    @staticmethod
    def update_achat(idx, date_achat, categorie, nom, qualite, quantite_ml, prix_total, commentaire, new_img, pin):
        if not SecurityController.verify_pin(pin):
            return False, "Code PIN incorrect."
            
        df_purch = BaseModel.load_df("purchases")
        if idx < 0 or idx >= len(df_purch):
            return False, "Achat introuvable."
            
        row = df_purch.iloc[idx].copy()
        
        # Log old movement inversion
        stock_before = StockService.get_stock(row["Nom"], row["Qualite"], row["Categorie"])
        
        # Save image if provided
        img_path = row["Image_Path"]
        if new_img:
            img_filename = f"{new_id()}_{new_img.name}"
            img_path = os.path.join(IMG_DIR, img_filename)
            with open(img_path, "wb") as f:
                f.write(new_img.getbuffer())
                
        cump_achat = prix_total / quantite_ml if quantite_ml > 0 else 0.0
        
        df_purch.at[idx, "Date"] = date_achat.strftime("%Y-%m-%d") if hasattr(date_achat, "strftime") else str(date_achat)
        df_purch.at[idx, "Categorie"] = categorie
        df_purch.at[idx, "Nom"] = nom
        df_purch.at[idx, "Qualite"] = qualite
        df_purch.at[idx, "Quantite_ML"] = quantite_ml
        df_purch.at[idx, "Prix_Total"] = prix_total
        df_purch.at[idx, "CUMP_Achat"] = cump_achat
        df_purch.at[idx, "Commentaire"] = commentaire
        df_purch.at[idx, "Image_Path"] = img_path
        
        st.session_state["purchases"] = df_purch
        BaseModel.save_df("purchases")
        
        # Rebuild and log movement
        StockService.rebuild_inventory()
        stock_after = StockService.get_stock(nom, qualite, categorie)
        
        BaseModel.log_movement(
            m_type="MODIF_ACHAT",
            ref_id=row["ID"],
            article=nom,
            qte=quantite_ml - clean_numeric(row["Quantite_ML"]),
            valeur=prix_total - clean_numeric(row["Prix_Total"]),
            stock_avant=stock_before,
            stock_apres=stock_after
        )
        
        return True, "Achat mis à jour avec succès."

    @staticmethod
    def delete_achat(idx, pin):
        if not SecurityController.verify_pin(pin):
            return False, "Code PIN incorrect."
            
        df_purch = BaseModel.load_df("purchases")
        if idx < 0 or idx >= len(df_purch):
            return False, "Achat introuvable."
            
        row = df_purch.iloc[idx].copy()
        
        df_del = BaseModel.load_df("deletions_purchases")
        del_record = row.to_dict()
        del_record["Date_Suppression"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df_del = pd.concat([df_del, pd.DataFrame([del_record])], ignore_index=True)
        BaseModel.save_df("deletions_purchases")
        
        # Log old movement inversion
        stock_before = StockService.get_stock(row["Nom"], row["Qualite"], row["Categorie"])
        
        df_purch = df_purch.drop(idx).reset_index(drop=True)
        st.session_state["purchases"] = df_purch
        BaseModel.save_df("purchases")
        
        StockService.rebuild_inventory()
        stock_after = StockService.get_stock(row["Nom"], row["Qualite"], row["Categorie"])
        
        # Log movement
        BaseModel.log_movement(
            m_type="SUPPRESSION_ACHAT",
            ref_id=row["ID"],
            article=row["Nom"],
            qte=row["Quantite_ML"],
            valeur=row["Prix_Total"],
            stock_avant=stock_before,
            stock_apres=stock_after
        )
        
        return True, "Achat supprimé avec succès."

    @staticmethod
    def update_item_properties(nom, qualite, categorie, new_genre, new_saison, pin):
        if not SecurityController.verify_pin(pin):
            return False, "Code PIN incorrect."
            
        df_purch = BaseModel.load_df("purchases")
        
        # Filter all occurrences of this item
        filt = (df_purch["Nom"] == nom) & (df_purch["Categorie"] == categorie)
        if qualite:
            purch_qual = df_purch["Qualite"].fillna("").astype(str).str.strip()
            filt = filt & (purch_qual == qualite)
            
        if not filt.any():
            return False, "Article introuvable dans l'historique d'achats."
            
        # Update Genre and Saison for all matching rows
        df_purch.loc[filt, "Genre"] = new_genre
        df_purch.loc[filt, "Saison"] = new_saison
        
        st.session_state["purchases"] = df_purch
        BaseModel.save_df("purchases")
        
        # Rebuild inventory to reflect changes in the catalog
        StockService.rebuild_inventory()
        
        return True, "Propriétés mises à jour avec succès !"
