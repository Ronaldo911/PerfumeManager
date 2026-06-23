import pandas as pd
import streamlit as st
from utils.helpers import clean_numeric

class CostingService:
    @staticmethod
    def get_cump_from_inventory(item_name, qualite="", categorie=None):
        """Retrieves CUMP from current inventory to avoid division by zero or recalculation errors"""
        df_inv = st.session_state.get("inventory", pd.DataFrame())
        if df_inv.empty:
            return 0.0
            
        filt = df_inv["Nom"] == item_name
        if qualite:
            filt = filt & (df_inv["Qualite"] == qualite)
        if categorie:
            filt = filt & (df_inv["Categorie"] == categorie)
            
        match = df_inv[filt]
        if not match.empty:
            return clean_numeric(match.iloc[0]["CUMP"])
        return 0.0

    @staticmethod
    def calculate_production_cost(ml_base, cump_base, ml_alcool, cump_alcool, cump_flacon):
        """Calculates production cost: (ml base * base CUMP) + (ml alcohol * alcohol CUMP) + flacon cost"""
        base_cost = ml_base * cump_base
        alcool_cost = ml_alcool * cump_alcool
        flacon_cost = cump_flacon
        return base_cost + alcool_cost + flacon_cost
