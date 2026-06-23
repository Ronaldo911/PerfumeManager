import pandas as pd
import streamlit as st
from datetime import datetime
from models.base_model import BaseModel
from services.stock_service import StockService
from services.costing_service import CostingService
from controllers.security_controller import SecurityController
from utils.helpers import clean_numeric, new_id

class OffresPertesController:
    @staticmethod
    def create_offre(date_offre, nom_parfum, qualite, taille, qte, raison, commentaire):
        if not nom_parfum or qte <= 0:
            return False, "Nom du parfum et quantité requis."
            
        perfume_stock = StockService.get_stock(nom_parfum, qualite, "Parfum Fini")
        if perfume_stock < qte:
            return False, f"Stock insuffisant pour offrir ({perfume_stock:.0f} disponibles)."
            
        cump_pf = CostingService.get_cump_from_inventory(nom_parfum, qualite, "Parfum Fini")
        valeur = cump_pf * qte
        
        df_offres = BaseModel.load_df("offres")
        o_id = new_id()
        new_offre = {
            "ID": o_id,
            "Date": date_offre.strftime("%Y-%m-%d") if hasattr(date_offre, "strftime") else str(date_offre),
            "Nom_Parfum": nom_parfum,
            "Qualite": qualite,
            "Taille": taille,
            "Quantite": qte,
            "Raison": raison,
            "Commentaire": commentaire
        }
        df_offres = pd.concat([df_offres, pd.DataFrame([new_offre])], ignore_index=True)
        st.session_state["offres"] = df_offres
        BaseModel.save_df("offres")
        
        # Rebuild Stock
        StockService.rebuild_inventory()
        
        # Log movements
        BaseModel.log_movement(
            m_type="OFFRE",
            ref_id=o_id,
            article=f"{nom_parfum} {taille}",
            qte=-qte,
            valeur=-valeur,
            stock_avant=perfume_stock,
            stock_apres=perfume_stock - qte
        )
        return True, f"Offre enregistrée : {qte} flacons offerts."

    @staticmethod
    def create_perte(date_perte, nom_parfum, qualite, taille, qte, type_perte, commentaire):
        if not nom_parfum or qte <= 0:
            return False, "Nom du parfum et quantité requis."
            
        perfume_stock = StockService.get_stock(nom_parfum, qualite, "Parfum Fini")
        if perfume_stock < qte:
            return False, f"Stock insuffisant pour déclarer une perte ({perfume_stock:.0f} disponibles)."
            
        cump_pf = CostingService.get_cump_from_inventory(nom_parfum, qualite, "Parfum Fini")
        valeur = cump_pf * qte
        
        df_pertes = BaseModel.load_df("pertes")
        p_id = new_id()
        new_perte = {
            "ID": p_id,
            "Date": date_perte.strftime("%Y-%m-%d") if hasattr(date_perte, "strftime") else str(date_perte),
            "Nom_Parfum": nom_parfum,
            "Qualite": qualite,
            "Taille": taille,
            "Quantite": qte,
            "Type_Perte": type_perte,
            "Commentaire": commentaire
        }
        df_pertes = pd.concat([df_pertes, pd.DataFrame([new_perte])], ignore_index=True)
        st.session_state["pertes"] = df_pertes
        BaseModel.save_df("pertes")
        
        # Rebuild Stock
        StockService.rebuild_inventory()
        
        # Log movements
        BaseModel.log_movement(
            m_type="PERTE",
            ref_id=p_id,
            article=f"{nom_parfum} {taille}",
            qte=-qte,
            valeur=-valeur,
            stock_avant=perfume_stock,
            stock_apres=perfume_stock - qte
        )
        return True, f"Perte enregistrée : {qte} flacons perdus."
