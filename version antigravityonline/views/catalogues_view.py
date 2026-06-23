import os
import base64
import streamlit as st
import pandas as pd
from models.base_model import BaseModel
from services.stock_service import StockService
from utils.helpers import clean_numeric

class CataloguesView:
    @staticmethod
    def get_base64_image(path):
        if not path or pd.isna(path) or str(path).strip() in ["", "nan"] or not os.path.exists(str(path)):
            return None
        try:
            with open(str(path), "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                # Determine file extension to set appropriate MIME type
                ext = str(path).split('.')[-1].lower()
                mime = "image/png" if ext == "png" else "image/jpeg"
                return f"data:{mime};base64,{encoded_string}"
        except Exception:
            return None

    @staticmethod
    def render():
        st.title("📚 CATALOGUES VISUELS PRO")
        
        tab1, tab2, tab3 = st.tabs(["📦 Catalogue Stock", "🏭 Catalogue Production", "💰 Catalogue Ventes"])
        
        df_inv = BaseModel.load_df("inventory")
        df_prod = BaseModel.load_df("production")
        df_ventes = BaseModel.load_df("ventes")
        df_offres = BaseModel.load_df("offres")
        df_pertes = BaseModel.load_df("pertes")
        df_cat = BaseModel.load_df("categories")
        
        # Rebuild stock to ensure it's up to date
        StockService.rebuild_inventory()
        df_inv = BaseModel.load_df("inventory")

        # =====================================================
        # TAB 1 : CATALOGUE STOCK (Raw Materials & Perfumes)
        # =====================================================
        with tab1:
            st.subheader("📦 Stock Réel Actuel")
            
            if df_inv.empty:
                st.info("Aucun article en stock.")
            else:
                col_filt1, col_filt2, col_filt3 = st.columns(3)
                with col_filt1:
                    cat_filter = st.selectbox("📦 Catégorie", ["Tous"] + df_inv["Categorie"].unique().tolist())
                with col_filt2:
                    genre_filter = st.selectbox("🚻 Genre", ["Tous", "Homme", "Femme", "Mixte"])
                with col_filt3:
                    saison_filter = st.selectbox("🌤️ Saison", ["Toutes", "Été", "Hiver", "Toutes Saisons"])
                
                cats_to_render = df_inv["Categorie"].unique().tolist() if cat_filter == "Tous" else [cat_filter]
                
                # The category headers will be rendered in the main loop below
                with st.expander("✏️ Éditer les propriétés (Genre & Saison) d'un article"):
                    # Get all bases and finished perfumes
                    df_edit = df_inv[df_inv["Categorie"].isin(["Base Parfum", "Parfum Fini"])]
                    if not df_edit.empty:
                        # We only edit the Base Parfum, which propagates to Parfum Fini. So we show Base Parfum items.
                        df_bases = df_edit[df_edit["Categorie"] == "Base Parfum"]
                        items_to_edit = []
                        for _, row in df_bases.iterrows():
                            items_to_edit.append(f"{row['Nom']} | {row['Qualite']}")
                        
                        if items_to_edit:
                            col_e1, col_e2, col_e3, col_e4 = st.columns(4)
                            with col_e1:
                                item_sel = st.selectbox("Article à modifier", list(set(items_to_edit)), key="cat_edit_item")
                            with col_e2:
                                new_genre = st.selectbox("Nouveau Genre", ["Homme", "Femme", "Mixte"], key="cat_edit_genre")
                            with col_e3:
                                new_saison = st.selectbox("Nouvelle Saison", ["Été", "Hiver", "Toutes Saisons"], key="cat_edit_saison")
                            with col_e4:
                                pin_edit = st.text_input("PIN", type="password", key="cat_edit_pin")
                                st.markdown("<br>", unsafe_allow_html=True)
                                if st.button("Enregistrer", key="cat_edit_btn"):
                                    nom_e = item_sel.split(" | ")[0]
                                    qual_e = item_sel.split(" | ")[1] if " | " in item_sel else ""
                                    from controllers.achats_controller import AchatsController
                                    success, msg = AchatsController.update_item_properties(nom_e, qual_e, "Base Parfum", new_genre, new_saison, pin_edit)
                                    if success:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                        else:
                            st.info("Aucune Base Parfum à modifier.")
                            
                for current_cat in cats_to_render:
                    df_filtered = df_inv[df_inv["Categorie"] == current_cat]
                    if genre_filter != "Tous":
                        df_filtered = df_filtered[df_filtered["Genre"] == genre_filter]
                    if saison_filter != "Toutes":
                        df_filtered = df_filtered[df_filtered["Saison"] == saison_filter]
                    if df_filtered.empty:
                        continue
                        
                    if cat_filter == "Tous":
                        # Style the category header right before its items
                        st.markdown(f"<h3 style='margin-top: 20px; margin-bottom: 15px; color: #7b1fa2; border-bottom: 2px solid rgba(123, 31, 162, 0.2); padding-bottom: 5px;'>📑 {current_cat}</h3>", unsafe_allow_html=True)
                        
                    cols = st.columns(3)
                    for idx, (_, row) in enumerate(df_filtered.iterrows()):
                        col_idx = idx % 3
                        with cols[col_idx]:
                            # Load image as base64
                            img_path = row.get("Image_Path", "")
                            b64_img = CataloguesView.get_base64_image(img_path)
                            
                            if b64_img:
                                image_html = f"<img src='{b64_img}' style='max-width:100%; max-height:100%; object-fit:contain; border-radius:8px;' />"
                            else:
                                # Classy placeholder for perfume items
                                image_html = "<div style='font-size:64px; text-shadow: 0 0 10px rgba(123, 31, 162, 0.15);'>🧴</div>"

                            # Add visual distinction for Base vs Fini
                            overlay_html = ""
                            if row['Categorie'] == "Base Parfum":
                                overlay_html = "<div style='position:absolute; top:8px; right:8px; background:rgba(0,0,0,0.65); color:white; padding:4px 10px; border-radius:12px; font-size:10.5px; font-weight:800; backdrop-filter:blur(4px); box-shadow:0 2px 4px rgba(0,0,0,0.2); letter-spacing:0.5px;'>🧪 ESSENCE</div>"
                            elif row['Categorie'] == "Parfum Fini":
                                overlay_html = "<div style='position:absolute; top:8px; right:8px; background:rgba(212,175,55,0.85); color:#2b1f3d; padding:4px 10px; border-radius:12px; font-size:10.5px; font-weight:800; backdrop-filter:blur(4px); box-shadow:0 2px 4px rgba(0,0,0,0.2); letter-spacing:0.5px;'>✨ PRÊT À VENDRE</div>"
                            elif row['Categorie'] == "Macérat":
                                overlay_html = "<div style='position:absolute; top:8px; right:8px; background:rgba(123, 31, 162, 0.85); color:white; padding:4px 10px; border-radius:12px; font-size:10.5px; font-weight:800; backdrop-filter:blur(4px); box-shadow:0 2px 4px rgba(0,0,0,0.2); letter-spacing:0.5px;'>🏺 MACÉRAT (VRAC)</div>"

                            # Retrieve threshold for stock alerts
                            seuil = 50.0
                            if not df_cat.empty:
                                match_cat = df_cat[df_cat["Nom"] == row['Categorie']]
                                if not match_cat.empty:
                                    seuil = clean_numeric(match_cat.iloc[0]["Seuil_Alerte"])

                            # Define stock status pill
                            stock_qty = clean_numeric(row['Quantite_ML'])
                            if stock_qty <= 0:
                                status_pill = "<span style='font-size:11px; background: rgba(235, 51, 73, 0.1); color: #c0392b; border: 1px solid rgba(235, 51, 73, 0.25); padding: 2px 8px; border-radius: 20px; font-weight: 600;'>🔴 Rupture</span>"
                            elif stock_qty < seuil:
                                status_pill = f"<span style='font-size:11px; background: rgba(244, 164, 96, 0.1); color: #d35400; border: 1px solid rgba(244, 164, 96, 0.25); padding: 2px 8px; border-radius: 20px; font-weight: 600;'>⚠️ Stock Bas</span>"
                            else:
                                status_pill = f"<span style='font-size:11px; background: rgba(46, 204, 113, 0.1); color: #27ae60; border: 1px solid rgba(46, 204, 113, 0.25); padding: 2px 8px; border-radius: 20px; font-weight: 600;'>🟢 En Stock</span>"

                            # Quality badge
                            quality_badge = ""
                            if row["Qualite"] and str(row["Qualite"]).strip() not in ["", "nan"]:
                                quality_badge = f"<span style='font-size:11.5px; background: rgba(224, 192, 104, 0.18); color: #b89739; border: 1px solid rgba(224, 192, 104, 0.35); padding: 2px 8px; border-radius: 20px; font-weight: 600;'>⭐ {row['Qualite']}</span>"
                                
                            # Ignore Genre/Saison for non-perfume categories
                            ignore_genre_saison = str(row.get("Categorie", "")) in ["Alcool", "Flacon", "Emballage", "Bouchon", "Boite", "Matière Première", "Fixateur", "Colorant"]
                            
                            # Genre and Saison badges
                            genre_badge = ""
                            if not ignore_genre_saison and "Genre" in row and pd.notna(row["Genre"]):
                                g = str(row["Genre"]).strip()
                                icon = "👨" if g == "Homme" else "👩" if g == "Femme" else "🚻"
                                if g and g not in ["nan", "None", ""]: 
                                    genre_badge = f"<span style='font-size: 11px; background: rgba(52, 152, 219, 0.1); color: #2980b9; border: 1px solid rgba(52, 152, 219, 0.25); padding: 2px 8px; border-radius: 20px; font-weight: 600;'>{icon} {g}</span>"
                                
                            saison_badge = ""
                            if not ignore_genre_saison and "Saison" in row and pd.notna(row["Saison"]):
                                s = str(row["Saison"]).strip()
                                icon = "☀️" if s == "Été" else "❄️" if s == "Hiver" else "🍂"
                                if s and s not in ["nan", "None", ""]: 
                                    saison_badge = f"<span style='font-size: 11px; background: rgba(155, 89, 182, 0.1); color: #8e44ad; border: 1px solid rgba(155, 89, 182, 0.25); padding: 2px 8px; border-radius: 20px; font-weight: 600;'>{icon} {s}</span>"

                            # Retrieve color for the category
                            cat_color = "#7b1fa2"
                            if not df_cat.empty:
                                match_cat = df_cat[df_cat["Nom"] == row['Categorie']]
                                if not match_cat.empty:
                                    cat_color = match_cat.iloc[0].get("Couleur", "#7b1fa2")
                            
                            bg_color = f"{cat_color}18" # ~9% opacity
                            border_color = f"{cat_color}40" # ~25% opacity

                            unit_str = "ML"
                            if row['Categorie'] in ["Parfum Fini", "Flacon"]:
                                unit_str = "Pièces"
                                
                            qty_str = f"{int(stock_qty)} {unit_str}" if unit_str == "Pièces" else f"{stock_qty:.1f} {unit_str}"

                            # Card background based on genre
                            card_bg_color = "rgba(255, 255, 255, 0.65)" # default white translucent
                            if not ignore_genre_saison and "Genre" in row and pd.notna(row["Genre"]):
                                genre_val = str(row["Genre"]).strip()
                                if genre_val == "Homme":
                                    card_bg_color = "rgba(220, 240, 255, 0.6)" # More transparent Light Blue
                                elif genre_val == "Femme":
                                    card_bg_color = "rgba(255, 225, 240, 0.6)" # More transparent Light Pink
                                elif genre_val == "Mixte":
                                    card_bg_color = "rgba(245, 230, 255, 0.6)" # More transparent Light Purple

                            html_content = f"""
                            <div class="catalog-item" style="display: flex; flex-direction: column; justify-content: space-between; height: 470px; background-color: {card_bg_color};">
                                <div>
                                    <!-- Image Section -->
                                    <div style="width: 100%; height: 160px; overflow: hidden; border-radius: 8px; margin-bottom: 15px; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.02); border: 1px solid rgba(224, 192, 104, 0.2); position: relative;">
                                        {image_html}
                                        {overlay_html}
                                    </div>
                                    <!-- Header Info -->
                                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; gap: 8px; min-height: 46px;">
                                        <h4 style="margin: 0; font-size: 17px; font-weight: 700; color: #2b1f3d; line-height: 1.2;">{row['Nom']}</h4>
                                        <div style="white-space: nowrap; flex-shrink: 0;">{quality_badge}</div>
                                    </div>
                                    <!-- Badges & Details -->
                                    <div style="margin-bottom: 15px; display: flex; flex-wrap: wrap; gap: 6px;">
                                        <span style="font-size: 11px; background: {bg_color}; color: {cat_color}; border: 1px solid {border_color}; padding: 2px 8px; border-radius: 20px; font-weight: 600;">🏷️ {row['Categorie']}</span>
                                        {genre_badge}
                                        {saison_badge}
                                        {status_pill}
                                    </div>
                                </div>
                                <!-- Financials Grid -->
                                <div style="border-top: 1px solid rgba(224, 192, 104, 0.15); padding-top: 12px; margin-top: 10px;">
                                    <div style="display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 6px; font-size: 12.5px; line-height: 1.4;">
                                        <div style="color: rgba(43, 31, 61, 0.65);">📏 Qte Restante:</div>
                                        <div style="text-align: right; font-weight: 700; color: #2b1f3d;">{qty_str}</div>
                                        <div style="color: rgba(43, 31, 61, 0.65);">💰 CUMP:</div>
                                        <div style="text-align: right; font-weight: 700; color: #b89739;">{row['CUMP']:.2f} TND</div>
                                        <div style="color: rgba(43, 31, 61, 0.65); font-weight: 600;">📊 Valeur Stock:</div>
                                        <div style="text-align: right; font-weight: 800; color: #b89739;">{row['Valeur_Stock_Totale']:.2f} TND</div>
                                    </div>
                                </div>
                            </div>
                            """
                            # Remove all newlines to prevent Streamlit markdown parser from breaking HTML
                            html_content = html_content.replace('\n', '')
                            st.markdown(html_content, unsafe_allow_html=True)

                            if row['Categorie'] == "Parfum Fini" and stock_qty > 0:
                                if st.button("🛒 Vendre ce produit", key=f"sell_{idx}", use_container_width=True):
                                    st.session_state["sell_from_catalog"] = {"nom": row["Nom"], "qualite": row["Qualite"]}
                                    st.session_state["navigate_to"] = "💰 Terminal de Ventes"
                                    st.rerun()


        # =====================================================
        # TAB 2 : CATALOGUE PRODUCTION (Flows analysis)
        # =====================================================
        with tab2:
            st.subheader("🏭 Analyse de Production")
            
            if df_prod.empty:
                st.info("Aucune fabrication dans la base.")
            else:
                unique_parfums = df_prod["Nom_Parfum"].unique()
                cols = st.columns(3)
                for idx, name in enumerate(unique_parfums):
                    col_idx = idx % 3
                    with cols[col_idx]:
                        # Calculate details
                        qual_matches = df_prod[df_prod["Nom_Parfum"] == name]
                        qualite = qual_matches.iloc[0]["Qualite_Base"] if not qual_matches.empty else ""
                        
                        produced = clean_numeric(df_prod[df_prod["Nom_Parfum"] == name]["Quantite_Flacons"].sum())
                        sold = clean_numeric(df_ventes[df_ventes["Nom_Parfum"] == name]["Quantite"].sum())
                        offered = clean_numeric(df_offres[df_offres["Nom_Parfum"] == name]["Quantite"].sum())
                        lost = clean_numeric(df_pertes[df_pertes["Nom_Parfum"] == name]["Quantite"].sum())
                        
                        stock = StockService.get_stock(name, qualite, "Parfum Fini")
                        
                        quality_text = f"⭐ {qualite}" if qualite else "Standard"

                        html_content_prod = f"""
                        <div class="catalog-item" style="display: flex; flex-direction: column; justify-content: space-between; height: 280px;">
                            <div>
                                <h4 style="margin: 0 0 15px 0; font-size: 17px; font-weight: 700; color: #2b1f3d; display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; min-height: 46px;">
                                    <span style="line-height: 1.2;">🧴 {name}</span>
                                    <span style="font-size: 11px; background: rgba(224, 192, 104, 0.15); color: #b89739; border: 1px solid rgba(224, 192, 104, 0.25); padding: 2px 8px; border-radius: 20px; font-weight: 600; white-space: nowrap;">{quality_text}</span>
                                </h4>
                                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 13px; line-height: 1.4;">
                                    <div style="display: flex; justify-content: space-between;">
                                        <span style="color: rgba(43, 31, 61, 0.65);">🔨 Fabriqués:</span>
                                        <span style="font-weight: 700; color: #2b1f3d;">{produced:.0f} flacons</span>
                                    </div>
                                    <div style="display: flex; justify-content: space-between;">
                                        <span style="color: rgba(43, 31, 61, 0.65);">💰 Vendus:</span>
                                        <span style="font-weight: 700; color: #27ae60;">{sold:.0f} flacons</span>
                                    </div>
                                    <div style="display: flex; justify-content: space-between;">
                                        <span style="color: rgba(43, 31, 61, 0.65);">🎁 Offerts:</span>
                                        <span style="font-weight: 700; color: #8e44ad;">{offered:.0f} flacons</span>
                                    </div>
                                    <div style="display: flex; justify-content: space-between;">
                                        <span style="color: rgba(43, 31, 61, 0.65);">💔 Perdus:</span>
                                        <span style="font-weight: 700; color: #c0392b;">{lost:.0f} flacons</span>
                                    </div>
                                </div>
                            </div>
                            <div style="border-top: 1px solid rgba(224, 192, 104, 0.15); padding-top: 12px; margin-top: 15px; display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-weight: 600; color: rgba(43, 31, 61, 0.75); font-size: 13px;">🟢 Stock Restant:</span>
                                <span style="font-size: 16px; font-weight: 800; color: #b89739;">{stock:.0f} flacons</span>
                            </div>
                        </div>
                        """
                        html_content_prod = html_content_prod.replace('\n', '')
                        st.markdown(html_content_prod, unsafe_allow_html=True)

        # =====================================================
        # TAB 3 : CATALOGUE VENTES (Financial performance)
        # =====================================================
        with tab3:
            st.subheader("💰 Performance Financière des Ventes")
            
            if df_ventes.empty:
                st.info("Aucune vente enregistrée.")
            else:
                sales_perf = df_ventes.groupby("Nom_Parfum").agg({
                    "Quantite": "sum",
                    "CA_Reel": "sum",
                    "Marge": "sum"
                }).reset_index()
                
                cols = st.columns(3)
                for idx, row in sales_perf.iterrows():
                    col_idx = idx % 3
                    with cols[col_idx]:
                        html_content_ventes = f"""
                        <div class="catalog-item" style="display: flex; flex-direction: column; justify-content: space-between; height: 230px;">
                            <div>
                                <h4 style="margin: 0 0 15px 0; font-size: 17px; font-weight: 700; color: #2b1f3d; border-bottom: 1px solid rgba(224, 192, 104, 0.15); padding-bottom: 8px; min-height: 46px; line-height: 1.2;">
                                    🧴 {row['Nom_Parfum']}
                                </h4>
                                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 13px; line-height: 1.4;">
                                    <div style="display: flex; justify-content: space-between;">
                                        <span style="color: rgba(43, 31, 61, 0.65);">🛍️ Quantité Vendue:</span>
                                        <span style="font-weight: 700; color: #2b1f3d;">{row['Quantite']:.0f} flacons</span>
                                    </div>
                                    <div style="display: flex; justify-content: space-between;">
                                        <span style="color: rgba(43, 31, 61, 0.65);">💰 CA Réel:</span>
                                        <span style="font-weight: 800; color: #b89739;">{row['CA_Reel']:.2f} TND</span>
                                    </div>
                                </div>
                            </div>
                            <div style="background: rgba(46, 204, 113, 0.06); border: 1px solid rgba(46, 204, 113, 0.18); padding: 8px 12px; border-radius: 8px; margin-top: 15px; display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-weight: 700; color: #27ae60; font-size: 13.5px;">📈 Marges Réalisées:</span>
                                <span style="font-size: 16px; font-weight: 800; color: #27ae60;">{row['Marge']:.2f} TND</span>
                            </div>
                        </div>
                        """
                        html_content_ventes = html_content_ventes.replace('\n', '')
                        st.markdown(html_content_ventes, unsafe_allow_html=True)
