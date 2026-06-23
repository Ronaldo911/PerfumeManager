import streamlit as st
import pandas as pd
from datetime import date
from models.base_model import BaseModel
from controllers.credits_controller import CreditsController
from utils.helpers import clean_numeric

class CreditsView:
    @staticmethod
    def render():
        st.title("💳 GESTION DES CRÉDITS CLIENTS")
        
        tab1, tab2, tab3 = st.tabs(["👥 Suivi par Client", "💳 Détails des Crédits", "📜 Archives & Historique"])
        
        df_credits = BaseModel.load_df("credits_history")
        df_ventes = BaseModel.load_df("ventes")
        
        # =====================================================
        # TAB 1 : SUIVI PAR CLIENT
        # =====================================================
        with tab1:
            st.subheader("👥 Dette Totale par Client")
            credits_actifs = df_credits[df_credits["Statut"] == "En cours"]
            
            if credits_actifs.empty:
                st.success("🎉 Aucun crédit en cours ! Tous les clients ont payé.")
            else:
                # Group by client
                df_grouped = credits_actifs.groupby("Client")["Montant_Restant"].sum().reset_index()
                df_grouped = df_grouped.sort_values(by="Montant_Restant", ascending=False)
                
                for _, grp_row in df_grouped.iterrows():
                    client_name = grp_row["Client"]
                    total_debt = grp_row["Montant_Restant"]
                    
                    with st.expander(f"👤 {client_name} — Dette Totale : {total_debt:.2f} TND"):
                        client_credits = credits_actifs[credits_actifs["Client"] == client_name].copy()
                        client_credits["Parfum"] = ""
                        for i, r in client_credits.iterrows():
                            vid = ""
                            if "Vente à crédit ID:" in str(r['Commentaire']):
                                vid = str(r['Commentaire']).split("Vente à crédit ID: ")[-1].strip()
                            if vid:
                                vm = df_ventes[df_ventes["ID"] == vid]
                                if not vm.empty:
                                    client_credits.at[i, "Parfum"] = f"{vm.iloc[0]['Nom_Parfum']} ({vm.iloc[0]['Taille']})"
                                    
                        st.write(f"**Nombre de crédits en cours :** {len(client_credits)}")
                        st.dataframe(client_credits[["Date", "Parfum", "Montant_Initial", "Montant_Paye", "Montant_Restant", "Commentaire"]], use_container_width=True)
                        st.info("Pour encaisser un de ces crédits, veuillez vous rendre dans l'onglet 'Détails des Crédits'.")

        # =====================================================
        # TAB 2 : SUIVI & ENCAISSEMENT INDIVIDUEL
        # =====================================================
        with tab2:
            st.subheader("💳 Liste des Crédits Actifs (Tickets)")
            
            if credits_actifs.empty:
                st.success("🎉 Aucun crédit en cours ! Tous les clients ont payé.")
            else:
                for idx, row in credits_actifs.iterrows():
                    vente_id = ""
                    if "Vente à crédit ID:" in str(row['Commentaire']):
                        vente_id = str(row['Commentaire']).split("Vente à crédit ID: ")[-1].strip()
                    
                    parfum_str = ""
                    nom_parfum_seul = "Inconnu"
                    if vente_id:
                        v_match = df_ventes[df_ventes["ID"] == vente_id]
                        if not v_match.empty:
                            nom_parfum_seul = f"{v_match.iloc[0]['Nom_Parfum']} ({v_match.iloc[0]['Taille']})"
                            parfum_str = f" | 🧪 {nom_parfum_seul}"

                    with st.expander(f"🎫 {row['Client']} — Reste : {row['Montant_Restant']:.2f} TND (sur {row['Montant_Initial']:.2f} TND) - {row['Date']}{parfum_str}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Client :** {row['Client']}")
                            st.write(f"**Parfum :** {nom_parfum_seul}")
                            st.write(f"**Montant Initial :** {row['Montant_Initial']:.2f} TND")
                            st.write(f"**Montant Déjà Payé :** {row['Montant_Paye']:.2f} TND")
                            st.write(f"**Montant Restant :** {row['Montant_Restant']:.2f} TND")
                            st.write(f"**Date Dernière MAJ :** {row['Date_Maj']}")
                            st.write(f"**Commentaires :** {row['Commentaire']}")
                            
                        with col2:
                            st.write("**💰 Encaisser ou Perte**")
                            amount_paid = st.number_input("Montant (TND)", min_value=0.1, max_value=float(row["Montant_Restant"]), value=float(row["Montant_Restant"]), step=1.0, key=f"pay_amount_{row['ID']}")
                            
                            action = st.radio("Opération", ["Paiement", "Perte"], horizontal=True, key=f"act_type_{row['ID']}")
                            
                            pin = st.text_input("🔒 Code PIN (4334)", type="password", key=f"pin_cred_{row['ID']}")
                            
                            col_b1, col_b2 = st.columns(2)
                            with col_b1:
                                if st.button("💾 Valider", key=f"btn_pay_{row['ID']}"):
                                    success, msg = CreditsController.solder_credit(row["ID"], amount_paid, action, pin)
                                    if success:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                            with col_b2:
                                if st.button("🔄 Annuler Crédit (Rétablir)", key=f"btn_canc_{row['ID']}"):
                                    success, msg = CreditsController.cancel_credit(row["ID"], pin)
                                    if success:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                                        
        # =====================================================
        # TAB 3 : ARCHIVES / HISTORIQUE
        # =====================================================
        with tab3:
            st.subheader("📜 Archives de tous les crédits")
            
            if df_credits.empty:
                st.info("Aucun historique de crédit.")
            else:
                # Filter selection
                statut_filter = st.selectbox("Filtrer par statut", ["Tous", "En cours", "Soldé", "Perdu"])
                
                df_filtered = df_credits
                if statut_filter != "Tous":
                    df_filtered = df_credits[df_credits["Statut"] == statut_filter]
                    
                st.dataframe(df_filtered, use_container_width=True)
