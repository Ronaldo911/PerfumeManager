import streamlit as st
import pandas as pd
import plotly.express as px
from models.base_model import BaseModel
from services.stock_service import StockService
from utils.helpers import clean_numeric

class DashboardView:
    @staticmethod
    def render():
        st.title("📊 TABLEAU DE BORD")
        
        df_ventes = BaseModel.load_df("ventes")
        df_inv = BaseModel.load_df("inventory")
        df_credits = BaseModel.load_df("credits_history")
        df_purch = BaseModel.load_df("purchases")
        df_prod = BaseModel.load_df("production")
        
        # Recalculate stock values dynamically to avoid corruption
        StockService.rebuild_inventory()
        df_inv = BaseModel.load_df("inventory")
        
        # 1. Financial Indicators
        ca_reel = clean_numeric(df_ventes["CA_Reel"].sum()) if not df_ventes.empty and "CA_Reel" in df_ventes.columns else 0.0
        ca_encaisse = clean_numeric(df_ventes["Montant_Recu"].sum()) if not df_ventes.empty else 0.0
        investissements = clean_numeric(df_purch["Prix_Total"].sum()) if not df_purch.empty else 0.0
        
        valeur_stock_totale = clean_numeric(df_inv["Valeur_Stock_Totale"].sum()) if not df_inv.empty else 0.0
        valeur_stock_finis = clean_numeric(df_inv[df_inv["Categorie"].isin(["Parfum Fini", "Macérat"])]["Valeur_Stock_Totale"].sum()) if not df_inv.empty else 0.0
        valeur_stock_mp = valeur_stock_totale - valeur_stock_finis
        
        credits_en_cours = clean_numeric(df_credits[df_credits["Statut"] == "En cours"]["Montant_Restant"].sum()) if not df_credits.empty else 0.0
        
        # Calculate Total Cost of raw materials consumed
        # We can find this from production couts + sold items couts
        total_marge = clean_numeric(df_ventes["Marge"].sum()) if not df_ventes.empty else 0.0
        cout_ventes = clean_numeric(df_ventes["Cout_Revient"].sum()) if not df_ventes.empty and "Cout_Revient" in df_ventes.columns else 0.0
        total_quantite = clean_numeric(df_ventes["Quantite"].sum()) if not df_ventes.empty and "Quantite" in df_ventes.columns else 0.0
        prix_moyen = (ca_reel / total_quantite) if total_quantite > 0 else 0.0
        ca_avant = clean_numeric(df_ventes["CA_Avant"].sum()) if not df_ventes.empty and "CA_Avant" in df_ventes.columns else 0.0
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.markdown(f"""
            <div class='metric-card' style='border-color: rgba(224, 192, 104, 0.45) !important; background: rgba(224, 192, 104, 0.12) !important;'>
                <h3 style='margin:0;font-size:13px;color:#b89739;font-weight:600;'>💰 CA Réalisé</h3>
                <h2 style='margin:10px 0 0 0;font-size:23px;color:#2b1f3d;font-weight:800;'>{ca_reel:,.2f} <span style='font-size:14px;color:#b89739;'>TND</span></h2>
                <p style='margin:5px 0 0 0;font-size:11px;color:#7f8c8d;'>Encaissé : <b>{ca_encaisse:,.2f} TND</b></p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class='metric-card' style='border-color: rgba(123, 31, 162, 0.35) !important; background: rgba(123, 31, 162, 0.08) !important;'>
                <h3 style='margin:0;font-size:13px;color:#7b1fa2;font-weight:600;'>📥 Investissements</h3>
                <h2 style='margin:10px 0 0 0;font-size:23px;color:#2b1f3d;font-weight:800;'>{investissements:,.2f} <span style='font-size:14px;color:#7b1fa2;'>TND</span></h2>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class='metric-card' style='border-color: rgba(244, 164, 96, 0.35) !important; background: rgba(244, 164, 96, 0.08) !important;'>
                <h3 style='margin:0;font-size:13px;color:#e67e22;font-weight:600;'>📦 Valeur Stock</h3>
                <h2 style='margin:10px 0 0 0;font-size:23px;color:#2b1f3d;font-weight:800;'>{valeur_stock_totale:,.2f} <span style='font-size:14px;color:#e67e22;'>TND</span></h2>
                <p style='margin:5px 0 0 0;font-size:11px;color:#7f8c8d;'>Prod. Finis: <b>{valeur_stock_finis:,.2f} TND</b></p>
                <p style='margin:2px 0 0 0;font-size:11px;color:#7f8c8d;'>Mat. Prem.: <b>{valeur_stock_mp:,.2f} TND</b></p>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown(f"""
            <div class='metric-card' style='border-color: rgba(235, 51, 73, 0.35) !important; background: rgba(235, 51, 73, 0.07) !important;'>
                <h3 style='margin:0;font-size:13px;color:#eb3349;font-weight:600;'>💳 Crédits En Cours</h3>
                <h2 style='margin:10px 0 0 0;font-size:23px;color:#2b1f3d;font-weight:800;'>{credits_en_cours:,.2f} <span style='font-size:14px;color:#eb3349;'>TND</span></h2>
            </div>
            """, unsafe_allow_html=True)
            
        with col5:
            taux_marge = (total_marge / cout_ventes * 100) if cout_ventes > 0 else 0.0
            st.markdown(f"""
            <div class='metric-card' style='border-color: rgba(46, 204, 113, 0.35) !important; background: rgba(46, 204, 113, 0.08) !important;'>
                <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <h3 style='margin:0;font-size:13px;color:#2ecc71;font-weight:600;'>📈 Marge Totale</h3>
                    <span style='font-size:12px;color:#27ae60;font-weight:bold;background:rgba(46,204,113,0.2);padding:2px 6px;border-radius:10px;'>+{taux_marge:,.1f}%</span>
                </div>
                <h2 style='margin:10px 0 0 0;font-size:23px;color:#2b1f3d;font-weight:800;'>
                    {total_marge:,.2f} <span style='font-size:14px;color:#2ecc71;'>TND</span>
                </h2>
                <p style='margin:12px 0 0 0;font-size:11px;color:#7f8c8d;'>Coût Ventes: <b>{cout_ventes:,.2f} TND</b></p>
            </div>
            """, unsafe_allow_html=True)
            
        with col6:
            st.markdown(f"""
            <div class='metric-card' style='border-color: rgba(52, 152, 219, 0.35) !important; background: rgba(52, 152, 219, 0.08) !important;'>
                <h3 style='margin:0;font-size:13px;color:#2980b9;font-weight:600;'>🛍️ Volume Ventes</h3>
                <h2 style='margin:10px 0 0 0;font-size:23px;color:#2b1f3d;font-weight:800;'>{total_quantite:,.0f} <span style='font-size:14px;color:#2980b9;'>Flacons</span></h2>
                <p style='margin:5px 0 0 0;font-size:11px;color:#7f8c8d;'>Prix Moyen : <b>{prix_moyen:,.2f} TND</b></p>
                <p style='margin:2px 0 0 0;font-size:11px;color:#7f8c8d;'>CA Brut : <b>{ca_avant:,.2f} TND</b></p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Helper function to style Plotly charts in luxury light/gold theme
        def apply_luxury_chart_layout(fig):
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Plus Jakarta Sans", color="#2b1f3d"),
                xaxis=dict(
                    gridcolor="rgba(0, 0, 0, 0.04)",
                    linecolor="rgba(0, 0, 0, 0.08)",
                    tickfont=dict(family="Plus Jakarta Sans", color="#2b1f3d")
                ),
                yaxis=dict(
                    gridcolor="rgba(0, 0, 0, 0.04)",
                    linecolor="rgba(0, 0, 0, 0.08)",
                    tickfont=dict(family="Plus Jakarta Sans", color="#2b1f3d")
                ),
                margin=dict(l=40, r=20, t=20, b=40),
                legend=dict(
                    bgcolor="rgba(255, 255, 255, 0.9)",
                    bordercolor="rgba(224, 192, 104, 0.2)",
                    borderwidth=1,
                    font=dict(color="#2b1f3d")
                )
            )
            return fig

        # 2. Charts Section
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("<h3 style='font-size:18px;margin-bottom:15px;'>🏆 Top 10 Parfums (par CA)</h3>", unsafe_allow_html=True)
            if not df_ventes.empty:
                top_perfumes = df_ventes.groupby("Nom_Parfum")["CA_Reel"].sum().sort_values(ascending=False).head(10).reset_index()
                fig1 = px.bar(top_perfumes, x="CA_Reel", y="Nom_Parfum", orientation="h",
                               color="CA_Reel", color_continuous_scale=["#f3effa", "#7b1fa2", "#b89739"],
                               labels={"CA_Reel": "CA (TND)", "Nom_Parfum": "Parfum"})
                fig1.update_layout(yaxis={'categoryorder':'total ascending'})
                fig1 = apply_luxury_chart_layout(fig1)
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("Aucune vente enregistrée pour afficher le Top 10.")
                
        with col_chart2:
            st.markdown("<h3 style='font-size:18px;margin-bottom:15px;'>📂 Investissement par Catégorie</h3>", unsafe_allow_html=True)
            if not df_purch.empty:
                cat_purch = df_purch.groupby("Categorie")["Prix_Total"].sum().reset_index()
                
                # Build custom color map from categories database
                df_cat_colors = BaseModel.load_df("categories")
                color_map = {}
                if not df_cat_colors.empty:
                    for _, r in df_cat_colors.iterrows():
                        color_map[r["Nom"]] = r.get("Couleur", "#7b1fa2")
                        
                fig2 = px.pie(
                    cat_purch, 
                    values="Prix_Total", 
                    names="Categorie", 
                    hole=0.4,
                    color="Categorie",
                    color_discrete_map=color_map
                )
                fig2 = apply_luxury_chart_layout(fig2)
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Aucun achat enregistré pour afficher la répartition.")
                
        # 3. Marge vs CA Analysis
        st.markdown("<h3 style='font-size:18px;margin-top:20px;margin-bottom:15px;'>💎 Chiffre d'Affaires vs Marge par Produit</h3>", unsafe_allow_html=True)
        if not df_ventes.empty:
            marge_analysis = df_ventes.groupby("Nom_Parfum")[["CA_Reel", "Marge"]].sum().reset_index()
            fig3 = px.bar(marge_analysis, x="Nom_Parfum", y=["CA_Reel", "Marge"], barmode="group",
                          labels={"value": "TND", "Nom_Parfum": "Parfum", "variable": "Indicateur"},
                          color_discrete_map={"CA_Reel": "#b89739", "Marge": "#7b1fa2"})
            fig3 = apply_luxury_chart_layout(fig3)
            st.plotly_chart(fig3, use_container_width=True)
            
        # 4. Stock Alerts
        st.markdown("<h3 style='font-size:18px;margin-top:25px;margin-bottom:15px;'>⚠️ Alertes Stock Bas</h3>", unsafe_allow_html=True)
        df_cat = BaseModel.load_df("categories")
        if not df_inv.empty and not df_cat.empty:
            alerts = []
            for _, cat_row in df_cat.iterrows():
                cat_nom = cat_row["Nom"]
                seuil = clean_numeric(cat_row["Seuil_Alerte"])
                items_cat = df_inv[df_inv["Categorie"] == cat_nom]
                for _, item in items_cat.iterrows():
                    qty = clean_numeric(item["Quantite_ML"])
                    if qty < seuil:
                        alerts.append({
                            "Article": item["Nom"],
                            "Catégorie": cat_nom,
                            "Stock Actuel": f"{qty:.1f} ML",
                            "Seuil Alerte": f"{seuil:.1f} ML"
                        })
            if alerts:
                st.dataframe(pd.DataFrame(alerts), use_container_width=True)
            else:
                st.success("✅ Tous les niveaux de stock sont corrects!")
        else:
            st.info("Ajoutez des matières premières en stock et configurez les catégories pour voir les alertes.")
