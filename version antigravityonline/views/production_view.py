import streamlit as st
import pandas as pd
from datetime import date
from models.base_model import BaseModel
from controllers.production_controller import ProductionController
from services.stock_service import StockService
from services.costing_service import CostingService
from utils.helpers import clean_numeric

class ProductionView:
    @staticmethod
    def render():
        st.title("🏭 FABRICATION DE PARFUMS")
        
        if "panier_production" not in st.session_state:
            st.session_state["panier_production"] = []
            
        tab1, tab2, tab3, tab4 = st.tabs(["🏗️ Lancer Fabrication", "🧺 Production Multiple", "📜 Journal de Production", "🗑️ Archives Suppressions"])        
        df_inv = BaseModel.load_df("inventory")
        df_tailles = BaseModel.load_df("tailles")
        tailles_actives = df_tailles[df_tailles["Actif"] == True]["Taille"].tolist() if not df_tailles.empty else ["3 ML", "5 ML", "10 ML", "30 ML", "50 ML", "100 ML", "200 ML"]
        
        bases_disp = df_inv[df_inv["Categorie"] == "Base Parfum"]
        bases_list = [f"{r['Nom']} | {r['Qualite']}" for _, r in bases_disp.iterrows()] if not bases_disp.empty else []
        
        alcools_disp = df_inv[df_inv["Categorie"] == "Alcool"]
        alcools_list = alcools_disp["Nom"].tolist() if not alcools_disp.empty else []
        
        flacons_disp = df_inv[df_inv["Categorie"] == "Flacon"]
        flacons_list = flacons_disp["Nom"].tolist() if not flacons_disp.empty else []

        # =====================================================
        # TAB 1 : FORMULAIRE DE FABRICATION
        # =====================================================
        with tab1:
            st.subheader("🏗️ Lancer une nouvelle opération")
            
            if "prod_form_gen" not in st.session_state:
                st.session_state["prod_form_gen"] = 0
            gen = st.session_state["prod_form_gen"]
            
            macerats_disp = df_inv[df_inv["Categorie"] == "Macérat"]
            macerats_list = [f"{r['Nom']} | {r['Qualite']}" for _, r in macerats_disp.iterrows()] if not macerats_disp.empty else []
            
            prod_type = st.radio("Type d'opération", ["📦 Fabrication Complète (Directe)", "🧪 Mise en Macération (Vrac)", "🧴 Mise en Bouteille (Depuis Vrac)"], horizontal=True, key=f"p_type_{gen}")
            st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px; opacity: 0.3;'>", unsafe_allow_html=True)
            
            if prod_type == "📦 Fabrication Complète (Directe)":
                if not bases_list or not alcools_list or not flacons_list:
                    st.warning("⚠️ Stock insuffisant de matières premières. Assurez-vous d'avoir enregistré des Achats de bases, d'alcool et de flacons.")
                else:
                    k_ml_base = f"p_ml_base_{gen}"
                    k_qty_flac = f"p_qty_flac_{gen}"
                    
                    if k_ml_base not in st.session_state:
                        st.session_state[k_ml_base] = 15.0
                    if k_qty_flac not in st.session_state:
                        st.session_state[k_qty_flac] = 1

                    col1, col2 = st.columns(2)
                    
                    with col1:
                        date_prod = st.date_input("📅 Date de Fabrication", value=date.today(), key=f"p_date_{gen}")
                        base_sel = st.selectbox("🧪 Base Parfumée", bases_list, key=f"p_base_{gen}")
                        
                        nom_base = base_sel.split(" | ")[0]
                        qualite_base = base_sel.split(" | ")[1] if " | " in base_sel else ""
                        nom_parfum_final = f"{nom_base} {qualite_base}".strip()
                        st.info(f"Produit fini généré : **{nom_parfum_final}**")
                        
                        alcool_sel = st.selectbox("🍶 Alcool", alcools_list, key=f"p_alc_{gen}")
                        flacon_sel = st.selectbox("🧴 Flacon à utiliser", flacons_list, key=f"p_flac_{gen}")
                        
                    with col2:
                        taille_flacon = st.selectbox("📏 Taille Flacon à fabriquer", tailles_actives, key=f"p_taille_{gen}")
                        
                        try:
                            taille_ml = float(taille_flacon.split()[0])
                        except:
                            taille_ml = 50.0
                            
                        ml_base = st.number_input("💧 Quantité Base par flacon (ML)", min_value=0.1, step=1.0, key=k_ml_base)
                        ml_alcool = max(0.0, taille_ml - ml_base)
                        st.metric("🍶 Alcool requis par flacon (Calculé)", f"{ml_alcool:.1f} ML")
                        
                        qty_flacons = st.number_input("🔢 Nombre de flacons à fabriquer", min_value=1, step=1, key=k_qty_flac)

                    if st.button("🔨 FABRIQUER", key=f"p_btn_{gen}"):
                        success, msg = ProductionController.create_production(date_prod, nom_base, qualite_base, ml_base, alcool_sel, flacon_sel, taille_flacon, qty_flacons)
                        if success:
                            st.success(msg)
                            st.session_state["prod_form_gen"] += 1
                            st.rerun()
                        else:
                            st.error(msg)
                            
            elif prod_type == "🧪 Mise en Macération (Vrac)":
                if not bases_list or not alcools_list:
                    st.warning("⚠️ Stock insuffisant de bases ou d'alcool.")
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                        date_prod = st.date_input("📅 Date de Macération", value=date.today(), key=f"pm_date_{gen}")
                        base_sel = st.selectbox("🧪 Base Parfumée", bases_list, key=f"pm_base_{gen}")
                        nom_base = base_sel.split(" | ")[0]
                        qualite_base = base_sel.split(" | ")[1] if " | " in base_sel else ""
                        alcool_sel = st.selectbox("🍶 Alcool", alcools_list, key=f"pm_alc_{gen}")
                        
                    with col2:
                        ml_base = st.number_input("💧 Volume Total Base (ML)", min_value=1.0, value=150.0, step=10.0, key=f"pm_v_base_{gen}")
                        ml_alcool = st.number_input("🍶 Volume Total Alcool (ML)", min_value=1.0, value=350.0, step=10.0, key=f"pm_v_alc_{gen}")
                        st.info(f"Volume Total du Macérat : **{ml_base + ml_alcool:.1f} ML**")
                        
                    if st.button("🏺 METTRE EN MACÉRATION", key=f"pm_btn_{gen}"):
                        success, msg = ProductionController.create_maceration(date_prod, nom_base, qualite_base, ml_base, alcool_sel, ml_alcool)
                        if success:
                            st.success(msg)
                            st.session_state["prod_form_gen"] += 1
                            st.rerun()
                        else:
                            st.error(msg)
                            
            elif prod_type == "🧴 Mise en Bouteille (Depuis Vrac)":
                if not macerats_list or not flacons_list:
                    st.warning("⚠️ Aucun Macérat disponible ou stock de flacons vide.")
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                        date_prod = st.date_input("📅 Date d'Embouteillage", value=date.today(), key=f"pb_date_{gen}")
                        mac_sel = st.selectbox("🏺 Macérat à utiliser", macerats_list, key=f"pb_mac_{gen}")
                        nom_base = mac_sel.split(" | ")[0]
                        qualite_base = mac_sel.split(" | ")[1] if " | " in mac_sel else ""
                        flacon_sel = st.selectbox("🧴 Flacon à utiliser", flacons_list, key=f"pb_flac_{gen}")
                        
                    with col2:
                        taille_flacon = st.selectbox("📏 Taille Flacon", tailles_actives, key=f"pb_taille_{gen}")
                        qty_flacons = st.number_input("🔢 Nombre de flacons à remplir", min_value=1, step=1, key=f"pb_qty_{gen}")
                        try:
                            taille_ml = float(taille_flacon.split()[0])
                        except:
                            taille_ml = 50.0
                        st.info(f"Volume de Macérat requis : **{taille_ml * qty_flacons:.1f} ML**")
                        
                    if st.button("🍾 METTRE EN BOUTEILLE", key=f"pb_btn_{gen}"):
                        success, msg = ProductionController.bottle_macerat(date_prod, nom_base, qualite_base, flacon_sel, taille_flacon, qty_flacons)
                        if success:
                            st.success(msg)
                            st.session_state["prod_form_gen"] += 1
                            st.rerun()
                        else:
                            st.error(msg)
                        
            st.markdown("---")
            st.subheader("📤 Importation Excel Fabrications")
            uploaded_fab_excel = st.file_uploader("📁 Sélectionner fichier Excel (.xlsx)", type=["xlsx"], key="fab_excel_importer")
            if uploaded_fab_excel:
                try:
                    df_imp_fab = pd.read_excel(uploaded_fab_excel)
                    
                    # Normalize column names: strip whitespace and BOM characters
                    df_imp_fab.columns = (
                        df_imp_fab.columns
                        .str.strip()
                        .str.replace('\ufeff', '', regex=False)
                        .str.replace('\xa0', '', regex=False)
                    )
                    
                    st.markdown(f"**Aperçu ({len(df_imp_fab)} lignes) :** `colonnes détectées : {list(df_imp_fab.columns)}`")
                    st.dataframe(df_imp_fab, use_container_width=True)
                    
                    required_cols = ["Date", "Nom_Base", "Qualite_Base", "ML_Base", "Nom_Alcool", "Nom_Flacon", "Taille_Flacon", "Quantite_Flacons"]
                    missing = [c for c in required_cols if c not in df_imp_fab.columns]
                    if missing:
                        st.error(f"❌ Colonnes manquantes : {missing}")
                        st.info("Colonnes attendues : Date, Nom_Base, Qualite_Base, ML_Base, Nom_Alcool, Nom_Flacon, Taille_Flacon, Quantite_Flacons")
                    else:
                        st.success(f"✅ Fichier valide — {len(df_imp_fab)} fabrications prêtes.")
                        if st.button("🚀 Importer les fabrications", key="btn_import_fab"):
                            imported = 0
                            errors = 0
                            for i, row in df_imp_fab.iterrows():
                                try:
                                    d_val = pd.to_datetime(row["Date"]).date()
                                except:
                                    d_val = date.today()
                                success, msg = ProductionController.create_production(
                                    date_prod=d_val,
                                    base_name=str(row["Nom_Base"]).strip(),
                                    qualite_base=str(row["Qualite_Base"]).strip(),
                                    ml_base=clean_numeric(row["ML_Base"]),
                                    alcool_name=str(row["Nom_Alcool"]).strip(),
                                    flacon_name=str(row["Nom_Flacon"]).strip(),
                                    taille_flacon=str(row["Taille_Flacon"]).strip(),
                                    qty_flacons=int(clean_numeric(row["Quantite_Flacons"]))
                                )
                                if success:
                                    imported += 1
                                else:
                                    errors += 1
                                    st.warning(f"Ligne {i+2} ignorée : {msg}")
                            if imported > 0:
                                st.success(f"✅ {imported} productions enregistrées!")
                            if errors > 0:
                                st.error(f"⚠️ {errors} lignes n'ont pas pu être importées.")
                            if imported > 0:
                                st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur de lecture du fichier : {e}")

        # =====================================================
        # TAB 2 : PRODUCTION MULTIPLE (PANIER)
        # =====================================================
        with tab2:
            st.subheader("🧺 Panier de Production Multiple")
            
            if not bases_list or not alcools_list or not flacons_list:
                st.warning("⚠️ Stock insuffisant de matières premières.")
            else:
                with st.expander("➕ Ajouter une fabrication au panier", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        p_base_sel = st.selectbox("🧪 Base Parfumée", bases_list, key="pm_base")
                        p_nom_base = p_base_sel.split(" | ")[0]
                        p_qualite_base = p_base_sel.split(" | ")[1] if " | " in p_base_sel else ""
                        p_alcool_sel = st.selectbox("🍶 Alcool", alcools_list, key="pm_alc")
                        p_flacon_sel = st.selectbox("🧴 Flacon", flacons_list, key="pm_flac")
                    with col2:
                        p_taille_flacon = st.selectbox("📏 Taille Flacon", tailles_actives, key="pm_taille")
                        p_ml_base = st.number_input("💧 Quantité Base par flacon (ML)", min_value=0.1, step=1.0, value=15.0, key="pm_ml_base")
                        p_qty_flacons = st.number_input("🔢 Nombre de flacons", min_value=1, step=1, value=1, key="pm_qty_flac")
                        
                    if st.button("🛒 Ajouter au Panier", key="pm_add_btn"):
                        item = {
                            "nom_base": p_nom_base,
                            "qualite_base": p_qualite_base,
                            "alcool_name": p_alcool_sel,
                            "flacon_name": p_flacon_sel,
                            "taille_flacon": p_taille_flacon,
                            "ml_base": p_ml_base,
                            "qty_flacons": p_qty_flacons
                        }
                        st.session_state["panier_production"].append(item)
                        st.rerun()

            st.markdown("---")
            if len(st.session_state["panier_production"]) == 0:
                st.info("🛒 Le panier de production est vide.")
            else:
                st.markdown("### 📋 Contenu du Panier")
                
                for i, item in enumerate(st.session_state["panier_production"]):
                    col_info, col_del = st.columns([0.9, 0.1])
                    with col_info:
                        nom_complet = f"{item['nom_base']} {item['qualite_base']}".strip()
                        st.markdown(f"**{i+1}. 🧴 {nom_complet}** — {item['qty_flacons']} flacons de {item['taille_flacon']} (Base: {item['ml_base']} ML/flacon, Alcool: {item['alcool_name']})")
                    with col_del:
                        if st.button("❌", key=f"pm_del_{i}"):
                            st.session_state["panier_production"].pop(i)
                            st.rerun()
                
                st.markdown("---")
                st.markdown("### ✅ Validation Globale")
                col_date, col_btn = st.columns([0.4, 0.6])
                with col_date:
                    date_prod_globale = st.date_input("📅 Date de Production", value=date.today(), key="pm_date_globale")
                with col_btn:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🚀 VALIDER TOUTE LA PRODUCTION", use_container_width=True):
                        succes_count = 0
                        erreurs_count = 0
                        for idx, prod_item in enumerate(st.session_state["panier_production"]):
                            success, msg = ProductionController.create_production(
                                date_prod=date_prod_globale,
                                base_name=prod_item["nom_base"],
                                qualite_base=prod_item["qualite_base"],
                                ml_base=prod_item["ml_base"],
                                alcool_name=prod_item["alcool_name"],
                                flacon_name=prod_item["flacon_name"],
                                taille_flacon=prod_item["taille_flacon"],
                                qty_flacons=prod_item["qty_flacons"]
                            )
                            if success:
                                succes_count += 1
                            else:
                                erreurs_count += 1
                                st.error(f"Erreur à l'article {idx+1} ({prod_item['nom_base']}) : {msg}")
                        
                        if succes_count > 0:
                            st.success(f"✅ {succes_count} fabrications enregistrées avec succès !")
                            st.session_state["panier_production"] = []
                            import time
                            time.sleep(1.5)
                            st.rerun()

        # =====================================================
        # TAB 3 : JOURNAL DE PRODUCTION
        # =====================================================
        with tab3:
            st.subheader("📜 Journal des Fabrications")
            df_prod = BaseModel.load_df("production")
            
            if df_prod.empty:
                st.info("Aucune fabrication enregistrée.")
            else:
                for idx, row in df_prod.iterrows():
                    with st.expander(f"🏭 {row['Nom_Parfum']} - {row['Date']} ({row['Quantite_Flacons']} Flacons x {row['Taille_Flacon']}) - Type: {row.get('Type_Production', 'Fini')}"):
                        st.write("### 📊 Détails des Coûts")
                        qty_f = clean_numeric(row.get('Quantite_Flacons', 0))
                        
                        if row.get('Type_Production', 'Fini') == "Macération" or qty_f == 0:
                            v_base = clean_numeric(row.get('Quantite_Base_ML', 0))
                            v_alc = clean_numeric(row.get('Quantite_Alcool_ML', 0))
                            v_tot = v_base + v_alc
                            
                            c_tot = clean_numeric(row.get('Cout_Total', 0))
                            cb = clean_numeric(row.get('Cout_Base', 0))
                            ca = clean_numeric(row.get('Cout_Alcool', 0))
                            
                            c1, c2, c3 = st.columns(3)
                            c1.metric("Volume Total", f"{v_tot:.1f} ML")
                            c2.metric("Coût Total", f"{c_tot:.2f} TND")
                            c3.metric("Coût Unitaire au ML", f"{(c_tot/v_tot):.3f} TND" if v_tot > 0 else "0.000 TND")
                            
                            st.write("**Répartition du Coût Total :**")
                            st.write(f"- 🧪 Base Parfum : {cb:.2f} TND")
                            st.write(f"- 🍶 Alcool : {ca:.2f} TND")
                        else:
                            c_tot = clean_numeric(row.get('Cout_Total', 0))
                            c_unit = clean_numeric(row.get('Cout_Unitaire', 0))
                            cb = clean_numeric(row.get('Cout_Base', 0)) / qty_f
                            ca = clean_numeric(row.get('Cout_Alcool', 0)) / qty_f
                            cf = clean_numeric(row.get('Cout_Flacon', 0)) / qty_f
                            
                            c1, c2, c3 = st.columns(3)
                            c1.metric("Quantité", f"{int(qty_f)} Flacons")
                            c2.metric("Coût Total", f"{c_tot:.2f} TND")
                            c3.metric("Coût Unitaire / Flacon", f"{c_unit:.2f} TND")
                            
                            col_u, col_t = st.columns(2)
                            with col_u:
                                st.write("**Répartition du Coût Unitaire :**")
                                if ca > 0:
                                    st.write(f"- 🧪 Base Parfum : {cb:.2f} TND")
                                    st.write(f"- 🍶 Alcool : {ca:.2f} TND")
                                    st.write(f"- 🧴 Flacon : {cf:.2f} TND")
                                else:
                                    st.write(f"- 🏺 Macérat (Vrac) : {cb:.2f} TND")
                                    st.write(f"- 🧴 Flacon : {cf:.2f} TND")
                            with col_t:
                                st.write("**Répartition du Coût Total :**")
                                cb_tot = cb * qty_f
                                ca_tot = ca * qty_f
                                cf_tot = cf * qty_f
                                if ca > 0:
                                    st.write(f"- 🧪 Base Parfum : {cb_tot:.2f} TND")
                                    st.write(f"- 🍶 Alcool : {ca_tot:.2f} TND")
                                    st.write(f"- 🧴 Flacon : {cf_tot:.2f} TND")
                                else:
                                    st.write(f"- 🏺 Macérat (Vrac) : {cb_tot:.2f} TND")
                                    st.write(f"- 🧴 Flacon : {cf_tot:.2f} TND")
                        
                        st.markdown("---")
                        
                        st.write("**✏️ Édition Avancée**")
                        
                        e_type = st.radio("Type d'opération", ["📦 Fabrication Complète (Directe)", "🧪 Mise en Macération (Vrac)", "🧴 Mise en Bouteille (Depuis Vrac)"], index=["Fini", "Macération", "Mise en Flacon"].index(row.get("Type_Production", "Fini")) if row.get("Type_Production", "Fini") in ["Fini", "Macération", "Mise en Flacon"] else 0, key=f"e_type_{idx}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            try:
                                d_val = pd.to_datetime(row['Date']).date()
                            except:
                                d_val = date.today()
                            e_date = st.date_input("Date", value=d_val, key=f"e_date_{idx}")
                            
                            old_base_name = row['Nom_Base']
                            old_qual_base = row['Qualite_Base']
                            old_base_str = f"{old_base_name} | {old_qual_base}" if old_qual_base and pd.notna(old_qual_base) else old_base_name
                            try:
                                b_idx = bases_list.index(old_base_str)
                            except:
                                b_idx = 0
                            
                            e_base = st.selectbox("Base", bases_list, index=b_idx, key=f"e_base_{idx}")
                            nom_base = e_base.split(" | ")[0]
                            qualite_base = e_base.split(" | ")[1] if " | " in e_base else ""
                            
                            old_alc = row.get("Nom_Alcool", "")
                            try:
                                a_idx = alcools_list.index(old_alc)
                            except:
                                a_idx = 0
                                
                            e_alc = st.selectbox("Alcool", alcools_list, index=a_idx, key=f"e_alc_{idx}")
                            
                        with col2:
                            old_flac = row.get("Nom_Flacon", "")
                            try:
                                f_idx = flacons_list.index(old_flac)
                            except:
                                f_idx = 0
                            e_flac = st.selectbox("Flacon", flacons_list, index=f_idx, key=f"e_flac_{idx}")
                            
                            old_taille = row.get("Taille_Flacon", "50 ML")
                            try:
                                t_idx = tailles_actives.index(old_taille)
                            except:
                                t_idx = 0
                            e_taille = st.selectbox("Taille Flacon", tailles_actives, index=t_idx, key=f"e_taille_{idx}")
                            
                            if e_type == "📦 Fabrication Complète (Directe)":
                                try:
                                    oq = int(row.get("Quantite_Flacons", 1))
                                except:
                                    oq = 1
                                e_ml_base = st.number_input("Base par flacon (ML)", min_value=0.1, value=float(clean_numeric(row.get("Quantite_Base_ML", 15.0)) / oq) if oq > 0 else 15.0, step=1.0, key=f"e_v_base_{idx}")
                                try:
                                    t_ml = float(e_taille.split()[0])
                                except:
                                    t_ml = 50.0
                                e_ml_alcool = max(0.0, t_ml - e_ml_base)
                                st.write(f"Alcool par flacon: {e_ml_alcool:.1f} ML")
                                e_qty = st.number_input("Nombre de flacons", min_value=1, value=oq if oq > 0 else 1, step=1, key=f"e_qty_{idx}")
                            elif e_type == "🧪 Mise en Macération (Vrac)":
                                e_ml_base = st.number_input("Volume Total Base (ML)", min_value=1.0, value=clean_numeric(row.get("Quantite_Base_ML", 150.0)), step=10.0, key=f"e_m_base_{idx}")
                                e_ml_alcool = st.number_input("Volume Total Alcool (ML)", min_value=1.0, value=clean_numeric(row.get("Quantite_Alcool_ML", 350.0)), step=10.0, key=f"e_m_alc_{idx}")
                                e_qty = 0
                            elif e_type == "🧴 Mise en Bouteille (Depuis Vrac)":
                                try:
                                    oq = int(row.get("Quantite_Flacons", 1))
                                except:
                                    oq = 1
                                e_qty = st.number_input("Nombre de flacons à remplir", min_value=1, value=oq if oq > 0 else 1, step=1, key=f"e_b_qty_{idx}")
                                e_ml_base = 0.0
                                e_ml_alcool = 0.0

                        pin_edit = st.text_input("🔒 Code PIN Modification", type="password", key=f"pin_prod_edit_{idx}")
                        
                        col_actions1, col_actions2 = st.columns(2)
                        with col_actions1:
                            if st.button("💾 Enregistrer Modification", key=f"btn_prod_edit_{idx}"):
                                success, msg = ProductionController.edit_production_full(
                                    idx=idx, pin=pin_edit, new_type=e_type, date_prod=e_date,
                                    base_name=nom_base, qualite_base=qualite_base,
                                    ml_base=e_ml_base, alcool_name=e_alc, ml_alcool=e_ml_alcool,
                                    flacon_name=e_flac, taille_flacon=e_taille, qty_flacons=e_qty
                                )
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                        with col_actions2:
                            if st.button("🗑️ Annuler Production", key=f"btn_prod_del_{idx}"):
                                success, msg = ProductionController.delete_production(idx, pin_edit)
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

        # =====================================================
        # TAB 4 : DELETIONS ARCHIVE
        # =====================================================
        with tab4:
            st.subheader("🗑️ Historique des suppressions de productions")
            df_del_prod = BaseModel.load_df("deletions_production")
            if df_del_prod.empty:
                st.info("Aucune production supprimée.")
            else:
                st.dataframe(df_del_prod, use_container_width=True)
