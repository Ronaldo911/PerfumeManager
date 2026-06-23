import os
import streamlit as st
import pandas as pd
from datetime import date
from models.base_model import BaseModel
from controllers.achats_controller import AchatsController
from services.stock_service import StockService
from utils.helpers import clean_numeric

class AchatsView:
    @staticmethod
    def render():
        st.title("🛒 GESTION DES ACHATS & STOCK")
        
        tab1, tab2, tab3 = st.tabs(["➕ Nouvel Achat", "📜 Historique", "🗑️ Archives Suppressions"])
        
        df_cat = BaseModel.load_df("categories")
        categories_list = df_cat["Nom"].tolist() if not df_cat.empty else ["Base Parfum", "Alcool", "Flacon", "Fourniture", "Autre"]
        
        df_tailles = BaseModel.load_df("tailles")
        tailles_actives = df_tailles[df_tailles["Actif"] == True]["Taille"].tolist() if not df_tailles.empty else ["3 ML", "5 ML", "10 ML", "30 ML", "50 ML", "100 ML", "200 ML"]

        # =====================================================
        # TAB 1 : NOUVEL ACHAT
        # =====================================================
        with tab1:
            st.subheader("📝 Enregistrer un Achat")
            
            # ── Form-generation counter: incrementing this changes all widget keys,
            #    which forces Streamlit to create fresh empty widgets (correct reset).
            if "purch_form_gen" not in st.session_state:
                st.session_state["purch_form_gen"] = 0
            gen = st.session_state["purch_form_gen"]

            # Build unique keys for this generation
            f_nom   = f"pa_nom_{gen}"
            f_qty   = f"pa_qty_{gen}"
            f_prix_unit = f"pa_prix_unit_{gen}"
            f_prix  = f"pa_prix_{gen}"
            f_comm  = f"pa_comm_{gen}"
            f_img   = f"pa_img_{gen}"

            # Initialize states if not present
            if f_qty not in st.session_state:
                st.session_state[f_qty] = 0.0
            if f_prix_unit not in st.session_state:
                st.session_state[f_prix_unit] = 0.0
            if f_prix not in st.session_state:
                st.session_state[f_prix] = 0.0

            # Define automatic calculation callbacks
            def on_qty_change():
                qty = st.session_state.get(f_qty, 0.0)
                unit = st.session_state.get(f_prix_unit, 0.0)
                st.session_state[f_prix] = float(qty * unit)

            def on_unit_change():
                qty = st.session_state.get(f_qty, 0.0)
                unit = st.session_state.get(f_prix_unit, 0.0)
                st.session_state[f_prix] = float(qty * unit)

            def on_total_change():
                qty = st.session_state.get(f_qty, 0.0)
                total = st.session_state.get(f_prix, 0.0)
                if qty > 0:
                    st.session_state[f_prix_unit] = float(total / qty)
                else:
                    st.session_state[f_prix_unit] = 0.0

            col1, col2 = st.columns(2)
            with col1:
                date_achat = st.date_input("📅 Date d'Achat", value=date.today(), key=f"pa_date_{gen}")
                categorie  = st.selectbox("📦 Catégorie", categories_list, key=f"pa_cat_{gen}")

                nom_saisi = st.text_input("📝 Nom de l'article", key=f_nom)

                # Check category rule
                nom_final = nom_saisi
                if categorie == "Flacon":
                    tailles_options = tailles_actives + ["Autre (Saisir manuellement)..."]
                    taille_selectionnee = st.selectbox("🧪 Taille Flacon", tailles_options, key=f"pa_taille_{gen}")
                    
                    if taille_selectionnee == "Autre (Saisir manuellement)...":
                        taille_finale = st.text_input("Saisir la taille personnalisée (ex: 250 ML)", key=f"pa_taille_custom_{gen}")
                    else:
                        taille_finale = taille_selectionnee

                    if nom_saisi and taille_finale:
                        nom_final = f"{nom_saisi} {taille_finale}"
                        st.info(f"Nom final enregistré : **{nom_final}**")

                qualite = ""
                genre = "Mixte"
                saison = "Toutes Saisons"
                if categorie == "Base Parfum":
                    qualite = st.selectbox("⭐ Qualité", ["Top", "Identique", "Extra"], key=f"pa_qual_{gen}")
                    
                    col_gs1, col_gs2 = st.columns(2)
                    with col_gs1:
                        genre = st.selectbox("🚻 Genre", ["Homme", "Femme", "Mixte"], index=2, key=f"pa_genre_{gen}")
                    with col_gs2:
                        saison = st.selectbox("🌤️ Saison", ["Été", "Hiver", "Toutes Saisons"], index=2, key=f"pa_saison_{gen}")
            with col2:
                quantite    = st.number_input("📏 Quantité (ML ou Unités)", min_value=0.0, step=10.0, key=f_qty, on_change=on_qty_change)
                
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    prix_unit = st.number_input("💰 Prix Unitaire (TND)", min_value=0.0, step=0.1, key=f_prix_unit, on_change=on_unit_change)
                with col_p2:
                    prix_total  = st.number_input("💵 Prix Total (TND)",         min_value=0.0, step=1.0,  key=f_prix, on_change=on_total_change)
                
                commentaire = st.text_area("💬 Commentaire (facultatif)", key=f_comm)
                uploaded_img = st.file_uploader("🖼️ Image de l'article", type=["png", "jpg", "jpeg"], key=f_img)

                if st.button("💾 ENREGISTRER L'ACHAT", key=f"pa_btn_{gen}"):
                    # Determine final values
                    qty_val = st.session_state.get(f_qty, 0.0)
                    total_val = st.session_state.get(f_prix, 0.0)
                    
                    success, msg = AchatsController.create_achat(
                        date_achat=date_achat,
                        categorie=categorie,
                        nom=nom_final,
                        qualite=qualite,
                        genre=genre,
                        saison=saison,
                        quantite=qty_val,
                        prix_total=total_val,
                        fournisseur="", 
                        commentaire=commentaire,
                        uploaded_img=uploaded_img
                    )
                    if success:
                        st.success(msg)
                        # ✅ Bump the generation → all widget keys change → form resets
                        st.session_state["purch_form_gen"] += 1
                        st.rerun()
                    else:
                        st.error(msg)
                    
            st.markdown("---")
            st.subheader("📤 Importation Excel Rapide")
            
            st.info("""
            💡 **Guide de formatage du fichier Excel :**
            
            Votre fichier Excel **doit** contenir exactement les colonnes suivantes (l'ordre des colonnes n'a pas d'importance) :
            1. **`Date`** : Date de l'achat au format `AAAA-MM-JJ` (ex : `2026-06-22`).
            2. **`Categorie`** : Catégorie exacte de l'article (`Base Parfum`, `Alcool`, `Flacon`, `Fourniture` ou `Autre`).
            3. **`Nom`** : Le nom de l'article (ex : `Oud Royal`, `Alcool 90°`, `Flacon Standard`).
            4. **`Qualite`** : Qualité du produit (uniquement pour `Base Parfum` : `Top`, `Identique` ou `Extra`). Laisser vide pour les autres catégories.
            5. **`Quantite_ML`** : Nombre indiquant la quantité (en ML pour les liquides, ou nombre d'unités pour les flacons/fournitures).
            6. **`Prix_Total`** : Nombre indiquant le prix total payé en TND (ex : `150.0`).
            
            ⚠️ *Important : Les noms des colonnes doivent être saisis exactement comme indiqués ci-dessus (respecter les majuscules et le tiret bas `_`).*
            """)
            
            uploaded_excel = st.file_uploader("📁 Charger un fichier Excel (.xlsx)", type=["xlsx"], key="excel_importer")
            if uploaded_excel:
                try:
                    df_imp = pd.read_excel(uploaded_excel)
                    
                    # Normalize column names: strip whitespace, BOM characters, and normalize
                    df_imp.columns = (
                        df_imp.columns
                        .str.strip()
                        .str.replace('\ufeff', '', regex=False)  # Remove BOM
                        .str.replace('\xa0', '', regex=False)    # Remove non-breaking space
                    )
                    
                    st.markdown(f"**Aperçu du fichier ({len(df_imp)} lignes) :**")
                    st.dataframe(df_imp, use_container_width=True)
                    
                    st.markdown(f"**Colonnes détectées :** `{list(df_imp.columns)}`")
                    
                    required_cols = ["Date", "Categorie", "Nom", "Qualite", "Quantite_ML", "Prix_Total"]
                    missing = [c for c in required_cols if c not in df_imp.columns]
                    if missing:
                        st.error(f"❌ Colonnes manquantes : {missing}")
                        st.warning("Vérifiez que vos en-têtes correspondent exactement : **Date, Categorie, Nom, Qualite, Quantite_ML, Prix_Total**")
                    else:
                        st.success(f"✅ Fichier valide — {len(df_imp)} achats prêts à être importés.")
                        if st.button("🚀 Lancer l'importation", key="btn_import_excel"):
                            imported = 0
                            errors = 0
                            for i, row in df_imp.iterrows():
                                try:
                                    # Safe date parsing
                                    try:
                                        d_val = pd.to_datetime(row["Date"]).date()
                                    except:
                                        d_val = date.today()
                                        
                                    qualite_val = str(row["Qualite"]).strip() if pd.notna(row["Qualite"]) and str(row["Qualite"]).strip() not in ["", "nan"] else ""
                                    
                                    success, _ = AchatsController.create_achat(
                                        date_achat=d_val,
                                        categorie=str(row["Categorie"]).strip(),
                                        nom=str(row["Nom"]).strip(),
                                        qualite=qualite_val,
                                        quantite_ml=clean_numeric(row["Quantite_ML"]),
                                        prix_total=clean_numeric(row["Prix_Total"]),
                                        commentaire="Import Excel",
                                        uploaded_img=None
                                    )
                                    if success:
                                        imported += 1
                                    else:
                                        errors += 1
                                except Exception as row_err:
                                    errors += 1
                                    st.warning(f"Ligne {i+2} ignorée : {row_err}")
                                    
                            if imported > 0:
                                st.success(f"✅ {imported} achats importés avec succès!")
                            if errors > 0:
                                st.error(f"⚠️ {errors} lignes n'ont pas pu être importées.")
                            if imported > 0:
                                st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur de lecture du fichier : {e}")

        # =====================================================
        # TAB 2 : HISTORIQUE & MODIFICATION
        # =====================================================
        with tab2:
            st.subheader("📜 Historique des Achats")
            df_purch = BaseModel.load_df("purchases")
            
            if df_purch.empty:
                st.info("Aucun achat enregistré.")
            else:
                for idx, row in df_purch.iterrows():
                    with st.expander(f"📦 [{row['Categorie']}] {row['Nom']} - {row['Date']} ({row['Quantite_ML']} ML / {row['Prix_Total']} TND)"):
                        # Parse date safety
                        try:
                            current_date = pd.to_datetime(row["Date"]).date()
                        except:
                            current_date = date.today()

                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            st.write("**✏️ Informations de l'Achat**")
                            new_date = st.date_input("Date d'Achat", value=current_date, key=f"date_edit_{idx}")
                            
                            new_cat = st.selectbox(
                                "Catégorie", 
                                categories_list, 
                                index=categories_list.index(row["Categorie"]) if row["Categorie"] in categories_list else 0, 
                                key=f"cat_edit_{idx}"
                            )
                            
                            new_nom = st.text_input("Nom de l'article", value=row["Nom"], key=f"nom_edit_{idx}")
                            
                            # Qualite selection
                            qual_options = ["", "Top", "Identique", "Extra"]
                            current_qual = str(row["Qualite"]).strip() if pd.notna(row["Qualite"]) else ""
                            if current_qual not in qual_options:
                                qual_options.append(current_qual)
                            
                            new_qual = st.selectbox(
                                "Qualité", 
                                qual_options, 
                                index=qual_options.index(current_qual), 
                                key=f"qual_edit_{idx}"
                            )
                            
                            # Commentaire input
                            comm_val = str(row["Commentaire"]) if pd.notna(row["Commentaire"]) and str(row["Commentaire"]).strip() != "nan" else ""
                            new_comm = st.text_area("Commentaire", value=comm_val, key=f"comm_edit_{idx}")
                            
                        with col2:
                            st.write("**✏️ Prix & Quantités**")
                            new_qty = st.number_input("Quantité (ML ou Unités)", value=float(row["Quantite_ML"]), key=f"qty_edit_{idx}")
                            new_prix = st.number_input("Prix Total (TND)", value=float(row["Prix_Total"]), key=f"prix_edit_{idx}")
                            
                            # Show recalculated CUMP
                            cump_val = new_prix / new_qty if new_qty > 0 else 0.0
                            st.metric("CUMP Achat recalculé", f"{cump_val:.4f} TND/ML")
                            
                            new_img = st.file_uploader("Modifier l'image", type=["png","jpg","jpeg"], key=f"img_edit_{idx}")
                            
                        with col3:
                            st.write("**🖼️ Image actuelle**")
                            img_val = row.get("Image_Path", "")
                            if pd.notna(img_val) and str(img_val).strip() not in ["", "nan"] and os.path.exists(str(img_val)):
                                st.image(str(img_val), use_container_width=True)
                            else:
                                st.write("🖼️ _Pas d'image_")
                                
                        col_actions1, col_actions2 = st.columns(2)
                        with col_actions1:
                            pin_edit = st.text_input("🔒 Code PIN pour Sauvegarder", type="password", key=f"pin_edit_a_{idx}")
                            if st.button("💾 Sauvegarder", key=f"save_edit_a_{idx}"):
                                success, msg = AchatsController.update_achat(
                                    idx=idx,
                                    date_achat=new_date,
                                    categorie=new_cat,
                                    nom=new_nom,
                                    qualite=new_qual,
                                    quantite_ml=new_qty,
                                    prix_total=new_prix,
                                    commentaire=new_comm,
                                    new_img=new_img,
                                    pin=pin_edit
                                )
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                                    
                        with col_actions2:
                            pin_del = st.text_input("🔒 Code PIN pour Supprimer", type="password", key=f"pin_del_a_{idx}")
                            if st.button("🗑️ Supprimer l'achat", key=f"btn_del_a_{idx}"):
                                success, msg = AchatsController.delete_achat(idx, pin_del)
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

        # =====================================================
        # TAB 3 : DELETIONS ARCHIVE
        # =====================================================
        with tab3:
            st.subheader("🗑️ Historique des suppressions d'achats")
            df_del = BaseModel.load_df("deletions_purchases")
            if df_del.empty:
                st.info("Aucun achat supprimé.")
            else:
                st.dataframe(df_del, use_container_width=True)
