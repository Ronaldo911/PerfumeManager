import streamlit as st
import pandas as pd
from datetime import date
from models.base_model import BaseModel
from controllers.offres_pertes_controller import OffresPertesController
from services.stock_service import StockService
from utils.helpers import clean_numeric

class OffresPertesView:
    @staticmethod
    def render():
        st.title("🎁 OFFRES ET PERTES")
        
        tab1, tab2, tab3 = st.tabs(["🎁 Offrir un parfum", "💔 Déclarer une Perte", "📜 Historique"])
        
        df_inv = BaseModel.load_df("inventory")
        parfums_stock = df_inv[df_inv["Categorie"] == "Parfum Fini"]
        parfums_list = [f"{r['Nom']} | {r['Qualite']}" for _, r in parfums_stock.iterrows()] if not parfums_stock.empty else []
        
        df_tailles = BaseModel.load_df("tailles")
        tailles_actives = df_tailles[df_tailles["Actif"] == True]["Taille"].tolist() if not df_tailles.empty else ["3 ML", "5 ML", "10 ML", "30 ML", "50 ML", "100 ML", "200 ML"]

        # =====================================================
        # TAB 1 : OFFRES GRATUITES
        # =====================================================
        with tab1:
            st.subheader("🎁 Offrir un Parfum gratuitement")
            
            if not parfums_list:
                st.warning("⚠️ Aucun parfum en stock à offrir.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    date_offre = st.date_input("📅 Date de l'Offre", value=date.today(), key="o_date")
                    parfum_sel = st.selectbox("🧴 Parfum", parfums_list, key="o_parfum")
                    nom_p = parfum_sel.split(" | ")[0]
                    qualite_p = parfum_sel.split(" | ")[1] if " | " in parfum_sel else ""
                    
                with col2:
                    taille = st.selectbox("📏 Taille", tailles_actives, key="o_taille")
                    qte = st.number_input("🔢 Quantité", min_value=1, value=1, step=1, key="o_qte")
                    raison = st.text_input("👤 Bénéficiaire / Raison", placeholder="Ami, Partenaire...", key="o_raison")
                    commentaire = st.text_area("📝 Commentaire", key="o_comm")
                    
                if st.button("🎁 Confirmer l'Offre"):
                    success, msg = OffresPertesController.create_offre(
                        date_offre=date_offre,
                        nom_parfum=nom_p,
                        qualite=qualite_p,
                        taille=taille,
                        qte=qte,
                        raison=raison,
                        commentaire=commentaire
                    )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        # =====================================================
        # TAB 2 : PERTES DE STOCK
        # =====================================================
        with tab2:
            st.subheader("💔 Déclarer une Perte de stock")
            
            if not parfums_list:
                st.warning("⚠️ Aucun parfum en stock.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    date_perte = st.date_input("📅 Date de la Perte", value=date.today(), key="p_date")
                    parfum_sel = st.selectbox("🧴 Parfum concerné", parfums_list, key="p_parfum")
                    nom_p = parfum_sel.split(" | ")[0]
                    qualite_p = parfum_sel.split(" | ")[1] if " | " in parfum_sel else ""
                    
                    type_perte = st.selectbox("🏷️ Type de perte", ["Casse", "Vol", "Péremption", "Défaut Qualité", "Autre"], key="p_type")
                    
                with col2:
                    taille = st.selectbox("📏 Taille", tailles_actives, key="p_taille")
                    qte = st.number_input("🔢 Quantité perdue", min_value=1, value=1, step=1, key="p_qte")
                    commentaire = st.text_area("📝 Motif / Commentaire", key="p_comm")
                    
                if st.button("💔 Confirmer la Perte"):
                    success, msg = OffresPertesController.create_perte(
                        date_perte=date_perte,
                        nom_parfum=nom_p,
                        qualite=qualite_p,
                        taille=taille,
                        qte=qte,
                        type_perte=type_perte,
                        commentaire=commentaire
                    )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        # =====================================================
        # TAB 3 : HISTORIQUES
        # =====================================================
        with tab3:
            st.subheader("📜 Historique des Offres & Pertes")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 🎁 Offres")
                df_offres = BaseModel.load_df("offres")
                if df_offres.empty:
                    st.info("Aucune offre enregistrée.")
                else:
                    st.dataframe(df_offres, use_container_width=True)
                    
            with col2:
                st.markdown("#### 💔 Pertes")
                df_pertes = BaseModel.load_df("pertes")
                if df_pertes.empty:
                    st.info("Aucune perte enregistrée.")
                else:
                    st.dataframe(df_pertes, use_container_width=True)
