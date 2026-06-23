import streamlit as st
import pandas as pd
from datetime import date
from models.base_model import BaseModel
from controllers.ventes_controller import VentesController
from services.stock_service import StockService
from services.costing_service import CostingService
from utils.helpers import clean_numeric, new_id

class VentesView:
    @staticmethod
    def render():
        st.title("💰 TERMINAL DE VENTES")
        
        tab1, tab2, tab3, tab4 = st.tabs(["🛒 Nouvelle Vente", "📜 Historique", "🗑️ Archives Suppressions", "🧺 Ventes Multiples"])
        
        df_inv = BaseModel.load_df("inventory")
        df_tailles = BaseModel.load_df("tailles")
        df_prix = BaseModel.load_df("prix_vente")
        
        # Parfums list
        parfums_stock = df_inv[df_inv["Categorie"] == "Parfum Fini"]
        parfums_list = [f"{r['Nom']} | {r['Qualite']}" for _, r in parfums_stock.iterrows()] if not parfums_stock.empty else []
        
        tailles_actives = df_tailles[df_tailles["Actif"] == True]["Taille"].tolist() if not df_tailles.empty else ["3 ML", "5 ML", "10 ML", "30 ML", "50 ML", "100 ML", "200 ML"]

        # =====================================================
        # TAB 1 : NOUVELLE VENTE
        # =====================================================
        with tab1:
            st.subheader("🛍️ Enregistrer une vente")
            
            if "sales_form_gen" not in st.session_state:
                st.session_state["sales_form_gen"] = 0
            gen = st.session_state["sales_form_gen"]

            k_taille = f"v_taille_{gen}"
            k_prix_unit = f"v_prix_unitaire_{gen}"
            k_qty = f"v_quantite_{gen}"
            k_remise = f"v_remise_{gen}"
            k_client = f"v_client_{gen}"
            k_montant_recu = f"v_montant_recu_{gen}"
            k_type_remise = f"v_type_remise_{gen}"
            k_type_vente = f"v_type_vente_{gen}"
            k_date = f"v_date_{gen}"
            k_parfum = f"v_parfum_{gen}"

            if "sell_from_catalog" in st.session_state:
                sfc = st.session_state.pop("sell_from_catalog")
                st.session_state[k_type_vente] = "Vente Stock"
                match_str = f"{sfc['nom']} | {sfc['qualite']}" if sfc['qualite'] and str(sfc['qualite']).strip() not in ["", "nan", "None"] else sfc['nom']
                try:
                    p_idx = parfums_list.index(match_str)
                    st.session_state[k_parfum] = parfums_list[p_idx]
                except ValueError:
                    matches = [p for p in parfums_list if sfc['nom'] in p]
                    if matches:
                        st.session_state[k_parfum] = matches[0]

            if k_taille not in st.session_state:
                default_taille = tailles_actives[0] if tailles_actives else "3 ML"
                st.session_state[k_taille] = default_taille
                
                # Fetch default price
                prix_default = 4.0
                match_p = df_prix[df_prix["Taille"] == default_taille]
                if not match_p.empty:
                    prix_default = clean_numeric(match_p.iloc[0]["Prix_TND"])
                st.session_state[k_prix_unit] = float(prix_default)

            if k_qty not in st.session_state:
                st.session_state[k_qty] = 1

            if k_remise not in st.session_state:
                st.session_state[k_remise] = 0.0

            col1, col2 = st.columns(2)
            with col1:
                date_vente = st.date_input("📅 Date de Vente", value=date.today(), key=k_date)
                
                df_clients = BaseModel.load_df("clients")
                clients_list = [f"{row['Code']} - {row['Nom']}" for _, row in df_clients.iterrows()] if not df_clients.empty else []
                client_sel = st.selectbox("👤 Client", ["Anonyme", "➕ Nouveau Client..."] + clients_list, key=k_client)
                
                nouveau_client_name = ""
                if client_sel == "➕ Nouveau Client...":
                    nouveau_client_name = st.text_input("Nom du nouveau client", key=f"v_new_client_{gen}")
                    
                type_vente = st.selectbox("🔧 Mode de Vente", ["Vente Stock", "Fabrication Directe"], key=k_type_vente)
                
                # Active list for raw materials if Direct Fab
                bases_disp = df_inv[df_inv["Categorie"] == "Base Parfum"]
                bases_list = [f"{r['Nom']} | {r['Qualite']}" for _, r in bases_disp.iterrows()] if not bases_disp.empty else []
                alcools_disp = df_inv[df_inv["Categorie"] == "Alcool"]
                alcool_list = alcools_disp["Nom"].tolist() if not alcools_disp.empty else []
                flacons_disp = df_inv[df_inv["Categorie"] == "Flacon"]
                flacons_list = flacons_disp["Nom"].tolist() if not flacons_disp.empty else []
                
            with col2:
                # Dynamic pricing logic callback
                def update_default_price():
                    selected_taille = st.session_state.get(k_taille)
                    match_p = df_prix[df_prix["Taille"] == selected_taille]
                    if not match_p.empty:
                        st.session_state[k_prix_unit] = float(clean_numeric(match_p.iloc[0]["Prix_TND"]))
                    else:
                        st.session_state[k_prix_unit] = 4.0

                taille = st.selectbox("📏 Taille", tailles_actives, key=k_taille, on_change=update_default_price)
                
                prix_unit = st.number_input("💰 Prix Unitaire (TND)", min_value=0.0, step=1.0, key=k_prix_unit)
                quantite = st.number_input("🔢 Quantité", min_value=1, step=1, key=k_qty)
                
            col_remise1, col_remise2 = st.columns(2)
            with col_remise1:
                type_remise = st.radio("🎁 Type Remise", ["TND", "%"], horizontal=True, key=k_type_remise)
            with col_remise2:
                remise = st.number_input("🎁 Valeur Remise", min_value=0.0, step=1.0, key=k_remise)
                
            # CA calculations
            ca_avant = prix_unit * quantite
            if type_remise == "TND":
                ca_reel = ca_avant - remise
            else:
                ca_reel = ca_avant * (1 - remise / 100)
            ca_reel = max(0.0, ca_reel)
            
            # Auto-fill montant_recu if the user has not overridden it
            if f"v_montant_recu_user_{gen}" not in st.session_state:
                st.session_state[k_montant_recu] = float(ca_reel)
            
            def on_montant_recu_change():
                st.session_state[f"v_montant_recu_user_{gen}"] = True

            montant_recu = st.number_input("💵 Montant Encaissé (TND)", min_value=0.0, key=k_montant_recu, on_change=on_montant_recu_change, step=1.0)
            
            st.markdown(f"**CA Avant Remise :** {ca_avant:.2f} TND | **CA Réel :** {ca_reel:.2f} TND")
            if montant_recu < ca_reel:
                st.warning(f"⚠️ Paiement partiel. Le reste ({ca_reel - montant_recu:.2f} TND) sera enregistré sous forme de Crédit client.")
                
            st.markdown("---")
            
            if type_vente == "Vente Stock":
                parfum_sel = st.selectbox("🧴 Sélectionner le Parfum Fini", parfums_list, key=k_parfum)
                if st.button("💾 ENREGISTRER LA VENTE"):
                    if not parfum_sel:
                        st.error("Sélectionnez un parfum.")
                    else:
                        nom_p = parfum_sel.split(" | ")[0]
                        qualite_p = parfum_sel.split(" | ")[1] if " | " in parfum_sel else ""
                        
                        final_client = client_sel if client_sel != "➕ Nouveau Client..." else "Anonyme"
                        if client_sel == "➕ Nouveau Client..." and nouveau_client_name.strip():
                            df_clients = BaseModel.load_df("clients")
                            new_code = f"CLI-{(len(df_clients) + 1):03d}"
                            final_client = f"{new_code} - {nouveau_client_name.strip()}"
                            new_c_dict = {"ID": new_id(), "Code": new_code, "Nom": nouveau_client_name.strip(), "Telephone": "", "Date_Ajout": date.today().strftime("%Y-%m-%d")}
                            df_clients = pd.concat([df_clients, pd.DataFrame([new_c_dict])], ignore_index=True)
                            st.session_state["clients"] = df_clients
                            BaseModel.save_df("clients")
                            
                        success, msg = VentesController.create_vente(
                            date_vente=date_vente,
                            client=final_client,
                            type_vente="Stock",
                            nom_parfum=nom_p,
                            qualite=qualite_p,
                            taille=taille,
                            qte=quantite,
                            prix_unit=prix_unit,
                            type_remise=type_remise,
                            remise=remise,
                            montant_recu=montant_recu
                        )
                        if success:
                            st.success(msg)
                            st.session_state["sales_form_gen"] += 1
                            st.rerun()
                        else:
                            st.error(msg)
            else:
                st.subheader("🏭 Formulaire de Fabrication Directe")
                if not bases_list or not alcool_list or not flacons_list:
                    st.warning("⚠️ Matières premières insuffisantes pour fabrication directe.")
                else:
                    col_fd1, col_fd2 = st.columns(2)
                    with col_fd1:
                        base_sel = st.selectbox("🧪 Base Parfumée", bases_list, key=f"fd_base_{gen}")
                        nom_base = base_sel.split(" | ")[0]
                        qualite_base = base_sel.split(" | ")[1] if " | " in base_sel else ""
                        
                        alcool_sel = st.selectbox("🍶 Alcool", alcool_list, key=f"fd_alc_{gen}")
                        
                    with col_fd2:
                        flacon_sel = st.selectbox("🧴 Flacon", flacons_list, key=f"fd_flac_{gen}")
                        ml_base = st.number_input("💧 ML Base par flacon", min_value=0.1, value=15.0, step=1.0, key=f"fd_ml_base_{gen}")
                        
                    if st.button("🚀 FABRIQUER ET VENDRE"):
                        final_client = client_sel if client_sel != "➕ Nouveau Client..." else "Anonyme"
                        if client_sel == "➕ Nouveau Client..." and nouveau_client_name.strip():
                            df_clients = BaseModel.load_df("clients")
                            new_code = f"CLI-{(len(df_clients) + 1):03d}"
                            final_client = f"{new_code} - {nouveau_client_name.strip()}"
                            new_c_dict = {"ID": new_id(), "Code": new_code, "Nom": nouveau_client_name.strip(), "Telephone": "", "Date_Ajout": date.today().strftime("%Y-%m-%d")}
                            df_clients = pd.concat([df_clients, pd.DataFrame([new_c_dict])], ignore_index=True)
                            st.session_state["clients"] = df_clients
                            BaseModel.save_df("clients")
                            
                        success, msg = VentesController.create_vente(
                            date_vente=date_vente,
                            client=final_client,
                            type_vente="Fabrication Directe",
                            nom_parfum=nom_base,
                            qualite=qualite_base,
                            taille=taille,
                            qte=quantite,
                            prix_unit=prix_unit,
                            type_remise=type_remise,
                            remise=remise,
                            montant_recu=montant_recu,
                            base_name=nom_base,
                            ml_base=ml_base,
                            alcohol_name=alcool_sel,
                            flacon_name=flacon_sel
                        )
                        if success:
                            st.success(msg)
                            st.session_state["sales_form_gen"] += 1
                            st.rerun()
                        else:
                            st.error(msg)

        # =====================================================
        # TAB 2 : HISTORIQUE & MODIFICATION
        # =====================================================
        with tab2:
            st.subheader("📜 Historique des Ventes")
            df_ventes = BaseModel.load_df("ventes")
            
            if df_ventes.empty:
                st.info("Aucune vente enregistrée.")
            else:
                df_clients_hist = BaseModel.load_df("clients")
                clients_list_hist = [f"{r['Code']} - {r['Nom']}" for _, r in df_clients_hist.iterrows()] if not df_clients_hist.empty else []
                client_options = ["Anonyme"] + clients_list_hist
                
                for idx, row in df_ventes.iterrows():
                    montant_recu = row.get("Montant_Recu", row["CA_Reel"])
                    if pd.isna(montant_recu):
                        montant_recu = row["CA_Reel"]
                    
                    if montant_recu >= row["CA_Reel"]:
                        badge = "✅ Au Comptant"
                    elif montant_recu <= 0:
                        badge = "💳 À Crédit"
                    else:
                        badge = f"💸 Partiel (Avance: {montant_recu} TND)"

                    with st.expander(f"🛍️ [{row['Type_Vente']}] {row['Nom_Parfum']} - {row['Date']} ({row['Quantite']} flacons x {row['Taille']} / CA: {row['CA_Reel']} TND) | {badge}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Client :** {row['Client']}")
                            st.write(f"**Qualité :** {row['Qualite']}")
                            st.write(f"**Remise :** {row['Remise']} {row['Type_Remise']}")
                            st.write(f"**Coût Revient :** {row['Cout_Revient']:.2f} TND")
                            st.write(f"**Marge :** {row['Marge']:.2f} TND")
                            st.write(f"**Montant Encaissé :** {montant_recu} TND")
                            
                        with col2:
                            st.write("**✏️ Modifier la Vente**")
                            
                            try:
                                c_idx = client_options.index(row["Client"])
                            except:
                                c_idx = 0
                            new_client = st.selectbox("Client", client_options, index=c_idx, key=f"client_v_edit_{idx}")
                            
                            try:
                                d_val = datetime.strptime(str(row["Date"]), "%Y-%m-%d").date()
                            except:
                                d_val = date.today()
                            new_date = st.date_input("Date", value=d_val, key=f"date_v_edit_{idx}")
                            
                            new_qty = st.number_input("Nouvelle Quantité", value=int(row["Quantite"]), key=f"qty_v_edit_{idx}")
                            new_pu = st.number_input("Nouveau Prix Unitaire", value=float(row["Prix_Unitaire"]), key=f"pu_v_edit_{idx}")
                            
                            col_r1, col_r2 = st.columns(2)
                            with col_r1:
                                t_r_idx = 0 if str(row["Type_Remise"]) == "TND" else 1
                                new_type_remise = st.radio("Type Remise", ["TND", "%"], index=t_r_idx, key=f"tr_v_edit_{idx}", horizontal=True)
                            with col_r2:
                                new_remise = st.number_input("Valeur Remise", value=float(row["Remise"]), key=f"remise_v_edit_{idx}")
                                
                            new_mr = st.number_input("Nouveau Montant Encaissé", value=float(montant_recu), key=f"mr_v_edit_{idx}")
                            pin_edit = st.text_input("🔒 Code PIN Modification", type="password", key=f"pin_v_edit_{idx}")
                            
                            col_act1, col_act2 = st.columns(2)
                            with col_act1:
                                if st.button("💾 Sauvegarder", key=f"btn_v_edit_{idx}"):
                                    success, msg = VentesController.update_vente(idx, new_date, new_client, new_qty, new_pu, new_type_remise, new_remise, new_mr, pin_edit)
                                    if success:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                            with col_act2:
                                if st.button("🗑️ Annuler Vente", key=f"btn_v_del_{idx}"):
                                    success, msg = VentesController.delete_vente(idx, pin_edit)
                                    if success:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)

        # =====================================================
        # TAB 3 : DELETIONS ARCHIVE
        # =====================================================
        with tab3:
            st.subheader("🗑️ Historique des suppressions de ventes")
            df_del_v = BaseModel.load_df("deletions_ventes")
            if df_del_v.empty:
                st.info("Aucune vente supprimée.")
            else:
                st.dataframe(df_del_v, use_container_width=True)

        # =====================================================
        # TAB 4 : PANIER MULTI-VENTES
        # =====================================================
        with tab4:
            st.subheader("🧺 Panier de Ventes Multiples")
            
            if "panier_ventes" not in st.session_state:
                st.session_state["panier_ventes"] = []
                
            col_p1, col_p2 = st.columns([2, 1])
            with col_p1:
                if st.session_state["panier_ventes"]:
                    df_panier = pd.DataFrame(st.session_state["panier_ventes"])
                    st.dataframe(df_panier, use_container_width=True)
                    
                    total_panier = sum([r["CA_Reel"] for r in st.session_state["panier_ventes"]])
                    st.metric("💰 Total Panier", f"{total_panier:.2f} TND")
                    
                    if st.button("🗑️ Vider le Panier"):
                        st.session_state["panier_ventes"] = []
                        st.rerun()
                else:
                    st.info("Le panier est vide.")
                    
            with col_p2:
                st.write("**➕ Ajouter au Panier**")
                p_selected = st.selectbox("Parfum fini", parfums_list, key="panier_pf")
                t_selected = st.selectbox("Taille flacon", tailles_actives, key="panier_taille")
                q_selected = st.number_input("Quantité", min_value=1, value=1, key="panier_qty")
                
                # Fetch price
                px_match = df_prix[df_prix["Taille"] == t_selected]
                px_default = clean_numeric(px_match.iloc[0]["Prix_TND"]) if not px_match.empty else 4.0
                
                prix_p = st.number_input("Prix", min_value=0.0, value=float(px_default), key="panier_prix")
                
                if st.button("➕ Ajouter"):
                    if p_selected:
                        nom_p = p_selected.split(" | ")[0]
                        qualite_p = p_selected.split(" | ")[1] if " | " in p_selected else ""
                        
                        ca_reel = prix_p * q_selected
                        st.session_state["panier_ventes"].append({
                            "Nom_Parfum": nom_p,
                            "Qualite": qualite_p,
                            "Taille": t_selected,
                            "Quantite": q_selected,
                            "Prix_Unitaire": prix_p,
                            "CA_Reel": ca_reel
                        })
                        st.rerun()
                        
            if st.session_state["panier_ventes"]:
                st.markdown("---")
                df_clients_p = BaseModel.load_df("clients")
                clients_list_p = [f"{row['Code']} - {row['Nom']}" for _, row in df_clients_p.iterrows()] if not df_clients_p.empty else []
                client_panier_sel = st.selectbox("👤 Client pour le panier", ["Anonyme", "➕ Nouveau Client..."] + clients_list_p, key="panier_client_sel")
                
                nouveau_client_panier = ""
                if client_panier_sel == "➕ Nouveau Client...":
                    nouveau_client_panier = st.text_input("Nom du nouveau client", key="panier_new_client")
                    
                recu_panier = st.number_input("Montant total encaissé pour le panier", min_value=0.0, value=float(total_panier))
                
                if st.button("💾 ENREGISTRER LE PANIER"):
                    final_client_p = client_panier_sel if client_panier_sel != "➕ Nouveau Client..." else "Anonyme"
                    if client_panier_sel == "➕ Nouveau Client..." and nouveau_client_panier.strip():
                        new_code = f"CLI-{(len(df_clients_p) + 1):03d}"
                        final_client_p = f"{new_code} - {nouveau_client_panier.strip()}"
                        new_c_dict = {"ID": new_id(), "Code": new_code, "Nom": nouveau_client_panier.strip(), "Telephone": "", "Date_Ajout": date.today().strftime("%Y-%m-%d")}
                        df_clients_p = pd.concat([df_clients_p, pd.DataFrame([new_c_dict])], ignore_index=True)
                        st.session_state["clients"] = df_clients_p
                        BaseModel.save_df("clients")

                    # Process each item in the basket
                    all_success = True
                    err_msg = ""
                    remaining_recu = recu_panier
                    for item in st.session_state["panier_ventes"]:
                        item_ca = float(item["CA_Reel"])
                        item_recu = min(item_ca, remaining_recu)
                        remaining_recu -= item_recu
                        remaining_recu = max(0.0, remaining_recu)
                        
                        success, msg = VentesController.create_vente(
                            date_vente=date.today(),
                            client=final_client_p,
                            type_vente="Stock",
                            nom_parfum=item["Nom_Parfum"],
                            qualite=item["Qualite"],
                            taille=item["Taille"],
                            qte=item["Quantite"],
                            prix_unit=item["Prix_Unitaire"],
                            type_remise="TND",
                            remise=0.0,
                            montant_recu=item_recu
                        )
                        if not success:
                            all_success = False
                            err_msg = msg
                            break
                            
                    if all_success:
                        st.success("✅ Panier enregistré avec succès!")
                        st.session_state["panier_ventes"] = []
                        st.rerun()
                    else:
                        st.error(f"Erreur lors de la validation : {err_msg}")
