import os
import json
import zipfile
import io
import shutil
import streamlit as st
import pandas as pd
from datetime import datetime
from models.base_model import BaseModel
from controllers.security_controller import SecurityController
from utils.constants import FILES, DATA_DIR, IMG_DIR, BACKUP_DIR, DEFAULT_PIN, RESET_PIN
from utils.helpers import new_id, clean_numeric

class SettingsView:
    @staticmethod
    def render():
        st.title("⚙️ PARAMÈTRES DU SYSTÈME")
        
        tab1, tab2, tab2_5, tab3, tab4 = st.tabs(["🏪 Boutique Settings", "📐 Tailles & Prix", "🎨 Catégories & Couleurs", "📤 Backup & Restore", "💣 Zone de Danger"])
        
        df_shop = BaseModel.load_df("shop_config")
        df_tailles = BaseModel.load_df("tailles")
        df_prix = BaseModel.load_df("prix_vente")

        # =====================================================
        # TAB 1 : CONFIGURATION BOUTIQUE
        # =====================================================
        with tab1:
            st.subheader("🏪 Paramètres de la boutique")
            if not df_shop.empty:
                nom_actuel = df_shop.iloc[0]["Boutique_Nom"]
                logo_actuel = df_shop.iloc[0]["Logo_Path"]
                
                col1, col2 = st.columns(2)
                with col1:
                    new_nom = st.text_input("Nom de la Boutique", value=nom_actuel)
                    uploaded_logo = st.file_uploader("Nouveau Logo", type=["png", "jpg", "jpeg"])
                    
                with col2:
                    if logo_actuel and os.path.exists(str(logo_actuel)):
                        st.image(str(logo_actuel), width=200)
                    else:
                        st.info("Aucun logo configuré.")
                        
                if st.button("Enregistrer les modifications"):
                    df_shop["Logo_Path"] = df_shop["Logo_Path"].astype(object)
                    df_shop.at[0, "Boutique_Nom"] = new_nom
                    if uploaded_logo:
                        logo_filename = f"logo_{new_id()}.{uploaded_logo.name.split('.')[-1]}"
                        logo_path = os.path.join(IMG_DIR, logo_filename)
                        with open(logo_path, "wb") as f:
                            f.write(uploaded_logo.getbuffer())
                        df_shop.at[0, "Logo_Path"] = logo_path
                    st.session_state["shop_config"] = df_shop
                    BaseModel.save_df("shop_config")
                    st.success("Configuration mise à jour !")
                    st.rerun()

        # =====================================================
        # TAB 2 : TAILLES & PRIX
        # =====================================================
        with tab2:
            st.subheader("📐 Gestion des tailles et prix par défaut")
            
            # Show current
            if not df_tailles.empty and not df_prix.empty:
                df_merged = pd.merge(df_tailles, df_prix, on="Taille", how="left")
                st.dataframe(df_merged[["Taille", "Actif", "Prix_TND"]], use_container_width=True)
                
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**➕ Ajouter une Taille**")
                new_taille = st.text_input("Taille (ex: 50 ML)", placeholder="50 ML")
                new_prix = st.number_input("Prix de vente par défaut (TND)", min_value=0.0, value=25.0)
                pin_add = st.text_input("PIN de sécurité", type="password", key="pin_add_t")
                if st.button("Ajouter la taille"):
                    if pin_add == DEFAULT_PIN and new_taille:
                        # Add size
                        new_t = {"ID": new_id(), "Taille": new_taille, "Ordre": len(df_tailles) + 1, "Actif": True}
                        df_tailles = pd.concat([df_tailles, pd.DataFrame([new_t])], ignore_index=True)
                        st.session_state["tailles"] = df_tailles
                        BaseModel.save_df("tailles")
                        
                        # Add price
                        new_p = {"ID": new_id(), "Taille": new_taille, "Prix_TND": new_prix}
                        df_prix = pd.concat([df_prix, pd.DataFrame([new_p])], ignore_index=True)
                        st.session_state["prix_vente"] = df_prix
                        BaseModel.save_df("prix_vente")
                        st.success("Taille et prix par défaut ajoutés !")
                        st.rerun()
                    else:
                        st.error("PIN incorrect ou champ vide.")
                        
            with col2:
                st.write("**🗑️ Supprimer une Taille**")
                taille_del = st.selectbox("Taille à supprimer", df_tailles["Taille"].tolist() if not df_tailles.empty else [])
                pin_del = st.text_input("PIN de sécurité", type="password", key="pin_del_t")
                if st.button("Supprimer la taille"):
                    if pin_del == DEFAULT_PIN:
                        df_tailles = df_tailles[df_tailles["Taille"] != taille_del].reset_index(drop=True)
                        st.session_state["tailles"] = df_tailles
                        BaseModel.save_df("tailles")
                        
                        df_prix = df_prix[df_prix["Taille"] != taille_del].reset_index(drop=True)
                        st.session_state["prix_vente"] = df_prix
                        BaseModel.save_df("prix_vente")
                        st.success("Taille supprimée !")
                        st.rerun()
                    else:
                        st.error("PIN incorrect.")

        # =====================================================
        # TAB 2.5 : CATEGORIES & COULEURS
        # =====================================================
        with tab2_5:
            st.subheader("🎨 Gestion des Catégories et Couleurs")
            
            df_cat = BaseModel.load_df("categories")
            if df_cat.empty:
                st.info("Aucune catégorie disponible.")
            else:
                st.markdown("**Catégories actuelles :**")
                
                formatted_cats = []
                for idx, row in df_cat.iterrows():
                    color = row.get("Couleur", "#7b1fa2")
                    formatted_cats.append({
                        "Nom": row["Nom"],
                        "Seuil d'Alerte (ML)": row["Seuil_Alerte"],
                        "Couleur Hex": color
                    })
                st.dataframe(pd.DataFrame(formatted_cats), use_container_width=True)
                
                st.markdown("---")
                col_c1, col_c2 = st.columns(2)
                
                with col_c1:
                    st.markdown("**✏️ Modifier une Catégorie / Couleur**")
                    cat_select = st.selectbox("Sélectionner la catégorie", df_cat["Nom"].tolist())
                    
                    if cat_select:
                        cat_row = df_cat[df_cat["Nom"] == cat_select].iloc[0]
                        current_color = cat_row.get("Couleur", "#7b1fa2")
                        current_seuil = float(cat_row["Seuil_Alerte"])
                        
                        new_seuil = st.number_input(f"Seuil d'Alerte pour {cat_select} (ML)", min_value=0.0, value=current_seuil, step=10.0, key="edit_seuil_cat")
                        new_color = st.color_picker(f"Couleur pour {cat_select}", value=current_color, key="edit_color_cat")
                        
                        pin_edit_cat = st.text_input("PIN de sécurité", type="password", key="pin_edit_cat")
                        
                        if st.button("💾 Sauvegarder la catégorie", key="btn_save_cat"):
                            if pin_edit_cat == DEFAULT_PIN:
                                idx_cat = df_cat[df_cat["Nom"] == cat_select].index[0]
                                df_cat.at[idx_cat, "Seuil_Alerte"] = new_seuil
                                df_cat.at[idx_cat, "Couleur"] = new_color
                                st.session_state["categories"] = df_cat
                                BaseModel.save_df("categories")
                                st.success("Catégorie mise à jour avec succès !")
                                st.rerun()
                            else:
                                st.error("PIN de sécurité incorrect.")
                                
                with col_c2:
                    st.markdown("**➕ Ajouter une nouvelle Catégorie**")
                    new_cat_name = st.text_input("Nom de la catégorie", placeholder="ex: Accessoire", key="new_cat_name")
                    new_cat_seuil = st.number_input("Seuil d'Alerte (ML)", min_value=0.0, value=50.0, step=10.0, key="new_cat_seuil")
                    new_cat_color = st.color_picker("Couleur de la catégorie", value="#7b1fa2", key="new_cat_color")
                    
                    pin_add_cat = st.text_input("PIN de sécurité", type="password", key="pin_add_cat")
                    
                    if st.button("➕ Ajouter la catégorie", key="btn_add_cat"):
                        if pin_add_cat == DEFAULT_PIN:
                            if new_cat_name:
                                if new_cat_name in df_cat["Nom"].tolist():
                                    st.error("Cette catégorie existe déjà.")
                                else:
                                    new_row = {
                                        "ID": new_id(),
                                        "Nom": new_cat_name,
                                        "Seuil_Alerte": new_cat_seuil,
                                        "Couleur": new_cat_color,
                                        "Date_Ajout": datetime.now().strftime("%Y-%m-%d")
                                    }
                                    df_cat = pd.concat([df_cat, pd.DataFrame([new_row])], ignore_index=True)
                                    st.session_state["categories"] = df_cat
                                    BaseModel.save_df("categories")
                                    st.success(f"Catégorie '{new_cat_name}' ajoutée !")
                                    st.rerun()
                            else:
                                st.error("Le nom de la catégorie ne peut pas être vide.")
                        else:
                            st.error("PIN de sécurité incorrect.")

        # =====================================================
        # TAB 3 : BACKUP & RESTORE
        # =====================================================
        with tab3:
            st.subheader("📥 Télécharger une sauvegarde de la base")
            
            # Create backup zip on-the-fly and let user download it
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for file_key, filepath in FILES.items():
                    if os.path.exists(filepath):
                        zip_file.write(filepath, os.path.basename(filepath))
            zip_buffer.seek(0)
            
            st.download_button(
                label="⬇️ Télécharger la sauvegarde (.zip)",
                data=zip_buffer,
                file_name=f"parfum_manager_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                mime="application/zip"
            )
            
            st.markdown("---")
            st.subheader("📤 Restaurer une sauvegarde")
            uploaded_zip = st.file_uploader("Sélectionner une archive sauvegarde (.zip)", type=["zip"])
            if uploaded_zip:
                if st.button("🔄 Restaurer les données"):
                    try:
                        with zipfile.ZipFile(uploaded_zip, "r") as zip_ref:
                            zip_ref.extractall(DATA_DIR)
                        st.success("Base de données restaurée avec succès ! Veuillez actualiser la page.")
                        # Clear state to force reload
                        for key in list(st.session_state.keys()):
                            del st.session_state[key]
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur de restauration : {e}")

        # =====================================================
        # TAB 4 : ZONE DE DANGER (RESET TOTAL)
        # =====================================================
        with tab4:
            st.subheader("💣 Réinitialisation Totale de l'application")
            st.warning("⚠️ Attention ! Cette action effacera définitivement toutes les données (achats, ventes, productions, etc.).")
            
            pin_reset = st.text_input("Saisir le PIN de réinitialisation (9999)", type="password")
            
            if st.button("💣 Lancer le Reset"):
                if pin_reset == RESET_PIN:
                    # 1. Automatic backup
                    backup_name = f"auto_backup_before_reset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                    backup_path = os.path.join(BACKUP_DIR, backup_name)
                    
                    with zipfile.ZipFile(backup_path, 'w') as zipf:
                        for file in FILES.values():
                            if os.path.exists(file):
                                zipf.write(file, os.path.basename(file))
                                
                    # 2. Offer for auto-download
                    with open(backup_path, "rb") as f:
                        st.download_button("📥 Télécharger la sauvegarde forcée avant effacement", f, file_name=backup_name)
                        
                    # 3. Clean files
                    for file_key, filepath in FILES.items():
                        if os.path.exists(filepath):
                            try:
                                os.remove(filepath)
                            except:
                                pass
                                
                    # Clear session state
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                        
                    st.success("Application réinitialisée ! Veuillez recharger l'application Streamlit.")
                    st.rerun()
                else:
                    st.error("PIN de réinitialisation incorrect.")
