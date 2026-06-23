import pandas as pd
import streamlit as st
from datetime import datetime
from models.base_model import BaseModel
from services.stock_service import StockService
from services.costing_service import CostingService
from controllers.security_controller import SecurityController
from controllers.production_controller import ProductionController
from utils.helpers import clean_numeric, new_id

class VentesController:
    @staticmethod
    def create_vente(date_vente, client, type_vente, nom_parfum, qualite, taille, qte, prix_unit, type_remise, remise, montant_recu,
                     base_name=None, ml_base=None, alcohol_name=None, flacon_name=None):
                     
        # 1. Handle Direct Fabrication first if applicable
        if type_vente == "Fabrication Directe":
            if not base_name or not alcohol_name or not flacon_name or ml_base <= 0:
                return False, "Veuillez remplir tous les champs de fabrication directe."
                
            success, msg = ProductionController.create_production(
                date_prod=date_vente,
                base_name=base_name,
                qualite_base=qualite,
                ml_base=ml_base,
                alcool_name=alcohol_name,
                flacon_name=flacon_name,
                taille_flacon=taille,
                qty_flacons=qte
            )
            if not success:
                return False, f"Échec de la fabrication directe : {msg}"

        # 2. Check finished goods stock
        perfume_stock = StockService.get_stock(nom_parfum, qualite, "Parfum Fini")
        if perfume_stock < qte:
            return False, f"Stock de parfum fini insuffisant ({perfume_stock:.0f} disponibles)."

        # 3. Calculations
        ca_avant = prix_unit * qte
        if type_remise == "TND":
            ca_reel = ca_avant - remise
        else:
            ca_reel = ca_avant * (1 - remise / 100)
            
        ca_reel = max(0.0, ca_reel)
        
        # Coût de revient from inventory
        cump_pf = CostingService.get_cump_from_inventory(nom_parfum, qualite, "Parfum Fini")
        cout_revient = cump_pf * qte
        marge = ca_reel - cout_revient
        
        # 4. Insert Vente Record
        df_ventes = BaseModel.load_df("ventes")
        vente_id = new_id()
        new_v = {
            "ID": vente_id,
            "Date": date_vente.strftime("%Y-%m-%d") if hasattr(date_vente, "strftime") else str(date_vente),
            "Client": client if client else "Anonyme",
            "Type_Vente": type_vente,
            "Nom_Parfum": nom_parfum,
            "Qualite": qualite,
            "Taille": taille,
            "Quantite": qte,
            "Prix_Unitaire": prix_unit,
            "Type_Remise": type_remise,
            "Remise": remise,
            "CA_Avant": ca_avant,
            "CA_Reel": ca_reel,
            "Montant_Recu": montant_recu,
            "Cout_Revient": cout_revient,
            "Marge": marge
        }
        df_ventes = pd.concat([df_ventes, pd.DataFrame([new_v])], ignore_index=True)
        st.session_state["ventes"] = df_ventes
        BaseModel.save_df("ventes")
        
        # 5. Handle Credit if not fully paid
        if montant_recu < ca_reel:
            montant_restant = ca_reel - montant_recu
            df_cred = BaseModel.load_df("credits_history")
            new_cred = {
                "ID": new_id(),
                "Date": date_vente.strftime("%Y-%m-%d") if hasattr(date_vente, "strftime") else str(date_vente),
                "Client": client if client else "Anonyme",
                "Montant_Initial": ca_reel,
                "Montant_Paye": montant_recu,
                "Montant_Restant": montant_restant,
                "Statut": "En cours",
                "Date_Maj": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Commentaire": f"Vente à crédit ID: {vente_id}"
            }
            df_cred = pd.concat([df_cred, pd.DataFrame([new_cred])], ignore_index=True)
            st.session_state["credits_history"] = df_cred
            BaseModel.save_df("credits_history")
            
        # Rebuild Stock
        StockService.rebuild_inventory()
        
        # Log movements
        BaseModel.log_movement(
            m_type="VENTE",
            ref_id=vente_id,
            article=f"{nom_parfum} {taille}",
            qte=-qte,
            valeur=-cout_revient,
            stock_avant=perfume_stock,
            stock_apres=perfume_stock - qte
        )
        
        return True, f"Vente validée ! Total: {ca_reel:.2f} TND"

    @staticmethod
    def update_vente(idx, new_date, new_client, new_qte, new_prix, new_type_remise, new_remise, new_montant_recu, pin):
        """Allows modifying sale quantities/prices/payments/client with PIN 4334"""
        if not SecurityController.verify_pin(pin):
            return False, "Code PIN incorrect."
            
        df_ventes = BaseModel.load_df("ventes")
        if idx < 0 or idx >= len(df_ventes):
            return False, "Vente introuvable."
            
        row = df_ventes.iloc[idx].copy()
        
        # Log changes and update
        old_qte = clean_numeric(row["Quantite"])
        diff_qte = new_qte - old_qte
        
        # Check stock if quantity increases
        perfume_stock = StockService.get_stock(row["Nom_Parfum"], row["Qualite"], "Parfum Fini")
        if diff_qte > 0 and perfume_stock < diff_qte:
            return False, "Stock insuffisant pour cette augmentation de quantité."
            
        # Recalculate CA
        ca_avant = new_prix * new_qte
        remise = clean_numeric(new_remise)
        if new_type_remise == "TND":
            ca_reel = ca_avant - remise
        else:
            ca_reel = ca_avant * (1 - remise / 100)
            
        ca_reel = max(0.0, ca_reel)
        
        cump_pf = CostingService.get_cump_from_inventory(row["Nom_Parfum"], row["Qualite"], "Parfum Fini")
        cout_revient = cump_pf * new_qte
        marge = ca_reel - cout_revient
        
        # Update row
        df_ventes.at[idx, "Date"] = new_date.strftime("%Y-%m-%d") if hasattr(new_date, "strftime") else str(new_date)
        df_ventes.at[idx, "Client"] = new_client
        df_ventes.at[idx, "Type_Remise"] = new_type_remise
        df_ventes.at[idx, "Remise"] = new_remise
        df_ventes.at[idx, "Quantite"] = new_qte
        df_ventes.at[idx, "Prix_Unitaire"] = new_prix
        df_ventes.at[idx, "CA_Avant"] = ca_avant
        df_ventes.at[idx, "CA_Reel"] = ca_reel
        df_ventes.at[idx, "Cout_Revient"] = cout_revient
        df_ventes.at[idx, "Marge"] = marge
        df_ventes.at[idx, "Montant_Recu"] = new_montant_recu
        
        st.session_state["ventes"] = df_ventes
        BaseModel.save_df("ventes")
        
        # Sync Credit
        df_cred = BaseModel.load_df("credits_history")
        credit_comment = f"Vente à crédit ID: {row['ID']}"
        credit_idx = df_cred[df_cred["Commentaire"].astype(str).str.contains(credit_comment, na=False)].index
        
        if new_montant_recu < ca_reel:
            montant_restant = ca_reel - new_montant_recu
            if not credit_idx.empty:
                c_idx = credit_idx[0]
                df_cred.at[c_idx, "Date"] = df_ventes.at[idx, "Date"]
                df_cred.at[c_idx, "Client"] = new_client
                df_cred.at[c_idx, "Montant_Initial"] = ca_reel
                df_cred.at[c_idx, "Montant_Paye"] = new_montant_recu
                df_cred.at[c_idx, "Montant_Restant"] = montant_restant
                df_cred.at[c_idx, "Statut"] = "En cours"
                df_cred.at[c_idx, "Date_Maj"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                new_cred = {
                    "ID": new_id(),
                    "Date": df_ventes.at[idx, "Date"],
                    "Client": new_client,
                    "Montant_Initial": ca_reel,
                    "Montant_Paye": new_montant_recu,
                    "Montant_Restant": montant_restant,
                    "Statut": "En cours",
                    "Date_Maj": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Commentaire": credit_comment
                }
                df_cred = pd.concat([df_cred, pd.DataFrame([new_cred])], ignore_index=True)
        else:
            if not credit_idx.empty:
                c_idx = credit_idx[0]
                df_cred.at[c_idx, "Date"] = df_ventes.at[idx, "Date"]
                df_cred.at[c_idx, "Client"] = new_client
                df_cred.at[c_idx, "Montant_Initial"] = ca_reel
                df_cred.at[c_idx, "Montant_Paye"] = ca_reel
                df_cred.at[c_idx, "Montant_Restant"] = 0.0
                df_cred.at[c_idx, "Statut"] = "Soldé"
                df_cred.at[c_idx, "Date_Maj"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
        st.session_state["credits_history"] = df_cred
        BaseModel.save_df("credits_history")
        
        # Rebuild Stock
        StockService.rebuild_inventory()
        
        # Log movement
        BaseModel.log_movement(
            m_type="MODIF_VENTE",
            ref_id=row["ID"],
            article=f"{row['Nom_Parfum']} {row['Taille']}",
            qte=-diff_qte,
            valeur=cout_revient - clean_numeric(row["Cout_Revient"]),
            stock_avant=perfume_stock,
            stock_apres=perfume_stock - diff_qte
        )
        
        return True, "Vente mise à jour avec succès."

    @staticmethod
    def delete_vente(idx, pin):
        if not SecurityController.verify_pin(pin):
            return False, "Code PIN incorrect."
            
        df_ventes = BaseModel.load_df("ventes")
        if idx < 0 or idx >= len(df_ventes):
            return False, "Vente introuvable."
            
        row = df_ventes.iloc[idx].copy()
        
        # Log deletion snapshot
        BaseModel.log_deletion("Ventes", row["ID"], row.to_dict(), pin)
        
        # Delete row
        df_ventes = df_ventes.drop(idx).reset_index(drop=True)
        st.session_state["ventes"] = df_ventes
        BaseModel.save_df("ventes")
        
        # Rebuild stock and log movements
        perfume_stock = StockService.get_stock(row["Nom_Parfum"], row["Qualite"], "Parfum Fini")
        StockService.rebuild_inventory()
        stock_after = StockService.get_stock(row["Nom_Parfum"], row["Qualite"], "Parfum Fini")
        
        BaseModel.log_movement(
            m_type="SUPPR_VENTE",
            ref_id=row["ID"],
            article=f"{row['Nom_Parfum']} {row['Taille']}",
            qte=clean_numeric(row["Quantite"]),
            valeur=clean_numeric(row["Cout_Revient"]),
            stock_avant=perfume_stock,
            stock_apres=stock_after
        )
        
        return True, "Vente supprimée et stock restitué."
