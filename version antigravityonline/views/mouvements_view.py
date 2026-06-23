import streamlit as st
import pandas as pd
from models.base_model import BaseModel
from services.stock_service import StockService

class MouvementsView:
    @staticmethod
    def render():
        st.title("🔄 TRAÇABILITÉ DES MOUVEMENTS")
        
        df_mov = BaseModel.load_df("mouvements")
        
        if df_mov.empty:
            st.info("Aucun mouvement enregistré.")
        else:
            st.subheader("🔍 Filtrer les mouvements")
            
            # Simple filters
            col1, col2 = st.columns(2)
            with col1:
                search_art = st.text_input("Rechercher un article", "")
            with col2:
                type_filter = st.selectbox("Filtrer par type", ["Tous", "ACHAT", "PROD_CONSO", "PROD_ENTREE", "VENTE", "OFFRE", "PERTE"])
                
            df_filtered = df_mov
            if search_art:
                df_filtered = df_filtered[df_filtered["Article"].str.contains(search_art, case=False, na=False)]
            if type_filter != "Tous":
                df_filtered = df_filtered[df_filtered["Type"] == type_filter]
                
            st.dataframe(df_filtered.sort_values("Date", ascending=False), use_container_width=True)
