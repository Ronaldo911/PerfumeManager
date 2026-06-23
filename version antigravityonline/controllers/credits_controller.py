import pandas as pd
import streamlit as st
from datetime import datetime
from models.base_model import BaseModel
from controllers.security_controller import SecurityController
from utils.helpers import clean_numeric, new_id

class CreditsController:
    @staticmethod
    def solder_credit(credit_id, amount_paid, action_type, pin):
        """Processes partial payment, full payment, or registers credit amount as a loss (perte)"""
        if not SecurityController.verify_pin(pin):
            return False, "Code PIN incorrect."
            
        df_credits = BaseModel.load_df("credits_history")
        if credit_id not in df_credits["ID"].values:
            return False, "Crédit introuvable."
            
        idx = df_credits[df_credits["ID"] == credit_id].index[0]
        row = df_credits.loc[idx].copy()
        
        # Verify numbers
        montant_restant = clean_numeric(row["Montant_Restant"])
        
        if amount_paid > montant_restant:
            return False, "Le montant payé dépasse la dette restante."
            
        # Register action
        if action_type == "Paiement":
            nouveau_paye = clean_numeric(row["Montant_Paye"]) + amount_paid
            nouveau_restant = clean_numeric(row["Montant_Initial"]) - nouveau_paye
            df_credits.loc[idx, "Montant_Paye"] = nouveau_paye
            df_credits.loc[idx, "Montant_Restant"] = nouveau_restant
            df_credits.loc[idx, "Statut"] = "Soldé" if nouveau_restant <= 0 else "En cours"
            df_credits.loc[idx, "Date_Maj"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            df_credits.loc[idx, "Commentaire"] = f"Paiement partiel enregistré: {amount_paid} TND. PIN: {pin}"
            
            BaseModel.log_movement("CREDIT_PAY", credit_id, row["Client"], amount_paid, amount_paid, 0, 0)
            
        elif action_type == "Perte":
            # Declare rest of the credit as lost
            nouveau_restant = 0.0
            df_credits.loc[idx, "Montant_Restant"] = nouveau_restant
            df_credits.loc[idx, "Statut"] = "Perdu"
            df_credits.loc[idx, "Date_Maj"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            df_credits.loc[idx, "Commentaire"] = f"Perte de créance déclarée pour le reste: {montant_restant} TND. PIN: {pin}"
            
            BaseModel.log_movement("CREDIT_LOSS", credit_id, row["Client"], -montant_restant, -montant_restant, 0, 0)
            
        BaseModel.save_df("credits_history")
        return True, "Crédit mis à jour avec succès!"

    @staticmethod
    def cancel_credit(credit_id, pin):
        """Allows resetting a credit or cancelling a payment with PIN"""
        if not SecurityController.verify_pin(pin):
            return False, "Code PIN incorrect."
            
        df_credits = BaseModel.load_df("credits_history")
        if credit_id not in df_credits["ID"].values:
            return False, "Crédit introuvable."
            
        idx = df_credits[df_credits["ID"] == credit_id].index[0]
        row = df_credits.loc[idx].copy()
        
        # Reset paying metrics
        df_credits.loc[idx, "Montant_Paye"] = 0.0
        df_credits.loc[idx, "Montant_Restant"] = clean_numeric(row["Montant_Initial"])
        df_credits.loc[idx, "Statut"] = "En cours"
        df_credits.loc[idx, "Date_Maj"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df_credits.loc[idx, "Commentaire"] = f"Crédit réinitialisé. Paiements annulés par PIN: {pin}"
        
        BaseModel.save_df("credits_history")
        BaseModel.log_movement("CREDIT_CANCEL", credit_id, row["Client"], 0.0, 0.0, 0, 0)
        
        return True, "Paiements annulés et crédit restauré."
