import pandas as pd
import streamlit as st
from datetime import datetime
from models.base_model import BaseModel
from services.stock_service import StockService
from services.costing_service import CostingService
from controllers.security_controller import SecurityController
from utils.helpers import clean_numeric, new_id

class ProductionController:
    @staticmethod
    def create_production(date_prod, base_name, qualite_base, ml_base, alcool_name, flacon_name, taille_flacon, qty_flacons):
        df_inv = BaseModel.load_df("inventory")
        
        # Verify materials exist in stock
        base_item = df_inv[(df_inv["Nom"] == base_name) & (df_inv["Qualite"] == qualite_base)]
        alcool_item = df_inv[df_inv["Nom"] == alcool_name]
        flacon_item = df_inv[df_inv["Nom"] == flacon_name]
        
        if base_item.empty or alcool_item.empty or flacon_item.empty:
            return False, "Matières premières introuvables en stock."
            
        # Parse bottle size
        try:
            taille_ml = float(taille_flacon.split()[0])
        except:
            taille_ml = 50.0
            
        ml_alcool = (taille_ml - ml_base)
        base_needed = ml_base * qty_flacons
        alcool_needed = ml_alcool * qty_flacons
        
        # Check actual stocks using StockService
        base_stock = StockService.get_stock(base_name, qualite_base, "Base Parfum")
        alcool_stock = StockService.get_stock(alcool_name, "", "Alcool")
        flacon_stock = StockService.get_stock(flacon_name, "", "Flacon")
        
        if base_stock < base_needed:
            return False, f"Stock de Base insuffisant (Requis: {base_needed:.1f} ML, Dispo: {base_stock:.1f} ML)."
        if alcool_stock < alcool_needed:
            return False, f"Stock d'Alcool insuffisant (Requis: {alcool_needed:.1f} ML, Dispo: {alcool_stock:.1f} ML)."
        if flacon_stock < qty_flacons:
            return False, f"Stock de Flacons insuffisant (Requis: {qty_flacons}, Dispo: {flacon_stock})."
            
        # Calculate costs
        cump_base = CostingService.get_cump_from_inventory(base_name, qualite_base, "Base Parfum")
        cump_alcool = CostingService.get_cump_from_inventory(alcool_name, categorie="Alcool")
        cump_flacon = CostingService.get_cump_from_inventory(flacon_name, categorie="Flacon")
        
        # Calculate costs
        cout_base = ml_base * cump_base * qty_flacons
        cout_alcool = ml_alcool * cump_alcool * qty_flacons
        cout_flacon = cump_flacon * qty_flacons
        cout_total = cout_base + cout_alcool + cout_flacon
        cout_unitaire = cout_total / qty_flacons if qty_flacons > 0 else 0.0
        
        # Insert production record
        df_prod = BaseModel.load_df("production")
        prod_id = new_id()
        nom_parfum = base_name # Name of the perfume is the name of the base + quality (handled in view or concatenated)
        
        new_prod = {
            "ID": prod_id,
            "Date": date_prod.strftime("%Y-%m-%d") if hasattr(date_prod, "strftime") else str(date_prod),
            "Nom_Base": base_name,
            "Qualite_Base": qualite_base,
            "Quantite_Base_ML": base_needed,
            "Quantite_Alcool_ML": alcool_needed,
            "Nom_Flacon": flacon_name,
            "Taille_Flacon": taille_flacon,
            "Quantite_Flacons": qty_flacons,
            "Nom_Parfum": nom_parfum,
            "Cout_Base": cout_base,
            "Cout_Alcool": cout_alcool,
            "Cout_Flacon": cout_flacon,
            "Cout_Total": cout_total,
            "Cout_Unitaire": cout_unitaire,
            "Nom_Alcool": alcool_name # Keep track of alcohol used
        }
        df_prod = pd.concat([df_prod, pd.DataFrame([new_prod])], ignore_index=True)
        st.session_state["production"] = df_prod
        BaseModel.save_df("production")
        
        # Log movements before and after
        # Base Parfum
        BaseModel.log_movement("PROD_CONSO", prod_id, base_name, -base_needed, -cout_base, base_stock, base_stock - base_needed)
        # Alcool
        BaseModel.log_movement("PROD_CONSO", prod_id, alcool_name, -alcool_needed, -cout_alcool, alcool_stock, alcool_stock - alcool_needed)
        # Flacon
        BaseModel.log_movement("PROD_CONSO", prod_id, flacon_name, -qty_flacons, -cout_flacon, flacon_stock, flacon_stock - qty_flacons)
        
        # Rebuild inventory to make sure perfume finished good stock is updated
        StockService.rebuild_inventory()
        
        # Perfume stock
        perfume_stock = StockService.get_stock(nom_parfum, qualite_base, "Parfum Fini")
        BaseModel.log_movement("PROD_ENTREE", prod_id, f"{nom_parfum} {taille_flacon}", qty_flacons, cout_total, perfume_stock - qty_flacons, perfume_stock)
        
        return True, f"Production réussie : {qty_flacons} flacons fabriqués."

    @staticmethod
    def update_production(idx, new_qte, pin):
        """Allows modifying production quantity with PIN code"""
        if not SecurityController.verify_pin(pin):
            return False, "Code PIN incorrect."
            
        df_prod = BaseModel.load_df("production")
        if idx < 0 or idx >= len(df_prod):
            return False, "Production introuvable."
            
        row = df_prod.iloc[idx].copy()
        old_qte = clean_numeric(row["Quantite_Flacons"])
        
        # If no changes
        if new_qte == old_qte:
            return True, "Aucune modification apportée."
            
        # Re-verify stock before updating
        # We need the difference
        diff_qte = new_qte - old_qte
        
        try:
            taille_ml = float(row["Taille_Flacon"].split()[0])
        except:
            taille_ml = 50.0
            
        ml_base_one = clean_numeric(row["Quantite_Base_ML"]) / old_qte
        ml_alcool_one = clean_numeric(row["Quantite_Alcool_ML"]) / old_qte
        
        base_diff = ml_base_one * diff_qte
        alcool_diff = ml_alcool_one * diff_qte
        
        if diff_qte > 0:
            # Check stock
            base_stock = StockService.get_stock(row["Nom_Base"], row["Qualite_Base"], "Base Parfum")
            alcool_name = row.get("Nom_Alcool", "Alcool")
            alcool_stock = StockService.get_stock(alcool_name, "", "Alcool")
            flacon_stock = StockService.get_stock(row["Nom_Flacon"], "", "Flacon")
            
            if base_stock < base_diff:
                return False, "Stock de Base insuffisant pour cette augmentation."
            if alcool_stock < alcool_diff:
                return False, "Stock d'Alcool insuffisant pour cette augmentation."
            if flacon_stock < diff_qte:
                return False, "Stock de Flacons insuffisant."
                
        # Calculate new costs
        cump_base = CostingService.get_cump_from_inventory(row["Nom_Base"], row["Qualite_Base"], "Base Parfum")
        alcool_name = row.get("Nom_Alcool", "Alcool")
        cump_alcool = CostingService.get_cump_from_inventory(alcool_name, categorie="Alcool")
        cump_flacon = CostingService.get_cump_from_inventory(row["Nom_Flacon"], categorie="Flacon")
        
        cout_base = ml_base_one * cump_base * new_qte
        cout_alcool = ml_alcool_one * cump_alcool * new_qte
        cout_flacon = cump_flacon * new_qte
        cout_total = cout_base + cout_alcool + cout_flacon
        cout_unitaire = cout_total / new_qte
        
        # Update row
        df_prod.at[idx, "Quantite_Flacons"] = new_qte
        df_prod.at[idx, "Quantite_Base_ML"] = ml_base_one * new_qte
        df_prod.at[idx, "Quantite_Alcool_ML"] = ml_alcool_one * new_qte
        df_prod.at[idx, "Cout_Base"] = cout_base
        df_prod.at[idx, "Cout_Alcool"] = cout_alcool
        df_prod.at[idx, "Cout_Flacon"] = cout_flacon
        df_prod.at[idx, "Cout_Total"] = cout_total
        df_prod.at[idx, "Cout_Unitaire"] = cout_unitaire
        
        st.session_state["production"] = df_prod
        BaseModel.save_df("production")
        
        # Log movements
        # Rebuild stock
        StockService.rebuild_inventory()
        
        # Log modification movement
        BaseModel.log_movement("MODIF_PROD", row["ID"], row["Nom_Parfum"], diff_qte, cout_total - clean_numeric(row["Cout_Total"]), 0, 0)
        
        return True, "Production mise à jour avec succès."

    @staticmethod
    def delete_production(idx, pin):
        if not SecurityController.verify_pin(pin):
            return False, "Code PIN incorrect."
            
        df_prod = BaseModel.load_df("production")
        if idx < 0 or idx >= len(df_prod):
            return False, "Production introuvable."
            
        row = df_prod.iloc[idx].copy()
        
        # Deletion snapshot
        BaseModel.log_deletion("Production", row["ID"], row.to_dict(), pin)
        
        # Delete row
        df_prod = df_prod.drop(idx).reset_index(drop=True)
        st.session_state["production"] = df_prod
        BaseModel.save_df("production")
        
        # Rebuild Stock
        StockService.rebuild_inventory()
        
        # Log movements
        BaseModel.log_movement(
            m_type="SUPPR_PROD",
            ref_id=row["ID"],
            article=row["Nom_Parfum"],
            qte=-clean_numeric(row["Quantite_Flacons"]),
            valeur=-clean_numeric(row["Cout_Total"]),
            stock_avant=0,
            stock_apres=0
        )
        
        return True, "Production annulée et archivée."

    @staticmethod
    def create_maceration(date_prod, base_name, qualite_base, ml_base, alcool_name, ml_alcool):
        df_inv = BaseModel.load_df("inventory")
        
        base_stock = StockService.get_stock(base_name, qualite_base, "Base Parfum")
        alcool_stock = StockService.get_stock(alcool_name, "", "Alcool")
        
        if base_stock < ml_base:
            return False, f"Stock de Base insuffisant (Requis: {ml_base:.1f} ML, Dispo: {base_stock:.1f} ML)."
        if alcool_stock < ml_alcool:
            return False, f"Stock d'Alcool insuffisant (Requis: {ml_alcool:.1f} ML, Dispo: {alcool_stock:.1f} ML)."
            
        # Get Costs
        cump_base = CostingService.get_cump_from_inventory(base_name, qualite_base, "Base Parfum")
        cump_alcool = CostingService.get_cump_from_inventory(alcool_name, categorie="Alcool")
        
        cout_base = ml_base * cump_base
        cout_alcool = ml_alcool * cump_alcool
        cout_total = cout_base + cout_alcool
        volume_total = ml_base + ml_alcool
        cout_unitaire = cout_total / volume_total if volume_total > 0 else 0.0
        
        df_prod = BaseModel.load_df("production")
        prod_id = new_id()
        nom_parfum = base_name # Le macérat porte le nom de la base
        
        new_prod = {
            "ID": prod_id,
            "Date": date_prod.strftime("%Y-%m-%d") if hasattr(date_prod, "strftime") else str(date_prod),
            "Nom_Base": base_name,
            "Qualite_Base": qualite_base,
            "Quantite_Base_ML": ml_base,
            "Quantite_Alcool_ML": ml_alcool,
            "Nom_Flacon": "Aucun",
            "Taille_Flacon": "Vrac",
            "Quantite_Flacons": 0,
            "Nom_Parfum": nom_parfum,
            "Cout_Base": cout_base,
            "Cout_Alcool": cout_alcool,
            "Cout_Flacon": 0.0,
            "Cout_Total": cout_total,
            "Cout_Unitaire": cout_unitaire,
            "Nom_Alcool": alcool_name,
            "Type_Production": "Macération"
        }
        df_prod = pd.concat([df_prod, pd.DataFrame([new_prod])], ignore_index=True)
        st.session_state["production"] = df_prod
        BaseModel.save_df("production")
        
        StockService.rebuild_inventory()
        
        BaseModel.log_movement("PROD_CONSO", prod_id, base_name, -ml_base, -cout_base, base_stock, base_stock - ml_base)
        BaseModel.log_movement("PROD_CONSO", prod_id, alcool_name, -ml_alcool, -cout_alcool, alcool_stock, alcool_stock - ml_alcool)
        
        macerat_stock = StockService.get_stock(nom_parfum, qualite_base, "Macérat")
        BaseModel.log_movement("PROD_ENTREE", prod_id, f"Macérat {nom_parfum}", volume_total, cout_total, macerat_stock - volume_total, macerat_stock)
        
        return True, f"Mise en macération réussie : {volume_total:.1f} ML de {nom_parfum} préparés."

    @staticmethod
    def bottle_macerat(date_prod, base_name, qualite_base, flacon_name, taille_flacon, qty_flacons):
        try:
            taille_ml = float(taille_flacon.split()[0])
        except:
            taille_ml = 50.0
            
        macerat_needed = taille_ml * qty_flacons
        macerat_stock = StockService.get_stock(base_name, qualite_base, "Macérat")
        flacon_stock = StockService.get_stock(flacon_name, "", "Flacon")
        
        if macerat_stock < macerat_needed:
            return False, f"Stock de Macérat insuffisant (Requis: {macerat_needed:.1f} ML, Dispo: {macerat_stock:.1f} ML)."
        if flacon_stock < qty_flacons:
            return False, f"Stock de Flacons insuffisant (Requis: {qty_flacons}, Dispo: {flacon_stock})."
            
        # Get Costs
        cump_macerat = CostingService.get_cump_from_inventory(base_name, qualite_base, "Macérat")
        cump_flacon = CostingService.get_cump_from_inventory(flacon_name, categorie="Flacon")
        
        cout_macerat = macerat_needed * cump_macerat
        cout_flacon = cump_flacon * qty_flacons
        cout_total = cout_macerat + cout_flacon
        cout_unitaire = cout_total / qty_flacons if qty_flacons > 0 else 0.0
        
        df_prod = BaseModel.load_df("production")
        prod_id = new_id()
        nom_parfum = base_name
        
        new_prod = {
            "ID": prod_id,
            "Date": date_prod.strftime("%Y-%m-%d") if hasattr(date_prod, "strftime") else str(date_prod),
            "Nom_Base": base_name,
            "Qualite_Base": qualite_base,
            "Quantite_Base_ML": 0.0,
            "Quantite_Alcool_ML": 0.0,
            "Nom_Flacon": flacon_name,
            "Taille_Flacon": taille_flacon,
            "Quantite_Flacons": qty_flacons,
            "Nom_Parfum": nom_parfum,
            "Cout_Base": cout_macerat, # We store macerat cost here
            "Cout_Alcool": 0.0,
            "Cout_Flacon": cout_flacon,
            "Cout_Total": cout_total,
            "Cout_Unitaire": cout_unitaire,
            "Nom_Alcool": "",
            "Type_Production": "Mise en Flacon"
        }
        df_prod = pd.concat([df_prod, pd.DataFrame([new_prod])], ignore_index=True)
        st.session_state["production"] = df_prod
        BaseModel.save_df("production")
        StockService.rebuild_inventory()
        
        BaseModel.log_movement("PROD_CONSO", prod_id, f"Macérat {nom_parfum}", -macerat_needed, -cout_macerat, macerat_stock, macerat_stock - macerat_needed)
        BaseModel.log_movement("PROD_CONSO", prod_id, flacon_name, -qty_flacons, -cout_flacon, flacon_stock, flacon_stock - qty_flacons)
        
        perfume_stock = StockService.get_stock(nom_parfum, qualite_base, "Parfum Fini")
        BaseModel.log_movement("PROD_ENTREE", prod_id, f"{nom_parfum} {taille_flacon}", qty_flacons, cout_total, perfume_stock - qty_flacons, perfume_stock)
        
        return True, f"Mise en bouteille réussie : {qty_flacons} flacons de {taille_flacon}."

    @staticmethod
    def edit_production_full(idx, pin, new_type, date_prod, base_name, qualite_base, ml_base, alcool_name, ml_alcool, flacon_name, taille_flacon, qty_flacons):
        if not SecurityController.verify_pin(pin):
            return False, "Code PIN incorrect."
            
        df_prod = BaseModel.load_df("production")
        if idx < 0 or idx >= len(df_prod):
            return False, "Production introuvable."
            
        old_row = df_prod.iloc[idx].copy()
        old_type = old_row.get("Type_Production", "Fini")
        old_qty_flacons = clean_numeric(old_row.get("Quantite_Flacons", 0))
        
        old_base_cons = clean_numeric(old_row.get("Quantite_Base_ML", 0))
        old_alcool_cons = clean_numeric(old_row.get("Quantite_Alcool_ML", 0))
        old_flacon_cons = old_qty_flacons if old_type in ["Fini", "Mise en Flacon"] else 0
        old_macerat_cons = 0.0
        
        if old_type == "Mise en Flacon":
            try:
                t_ml = float(str(old_row.get("Taille_Flacon", "")).split()[0])
            except:
                t_ml = 50.0
            old_macerat_cons = t_ml * old_qty_flacons

        base_stock = StockService.get_stock(base_name, qualite_base, "Base Parfum")
        if old_row["Nom_Base"] == base_name and old_row["Qualite_Base"] == qualite_base and old_type != "Mise en Flacon":
            base_stock += old_base_cons
            
        alcool_stock = StockService.get_stock(alcool_name, "", "Alcool")
        if old_row.get("Nom_Alcool") == alcool_name and old_type != "Mise en Flacon":
            alcool_stock += old_alcool_cons
            
        flacon_stock = StockService.get_stock(flacon_name, "", "Flacon")
        if old_row.get("Nom_Flacon") == flacon_name and old_type in ["Fini", "Mise en Flacon"]:
            flacon_stock += old_flacon_cons
            
        macerat_stock = StockService.get_stock(base_name, qualite_base, "Macérat")
        if old_type == "Mise en Flacon" and old_row["Nom_Base"] == base_name and old_row["Qualite_Base"] == qualite_base:
            macerat_stock += old_macerat_cons
            
        if new_type == "📦 Fabrication Complète (Directe)":
            try:
                t_ml = float(str(taille_flacon).split()[0])
            except:
                t_ml = 50.0
            
            new_base_cons = ml_base * qty_flacons
            new_alcool_cons = ml_alcool * qty_flacons
            new_flacon_cons = qty_flacons
            
            if base_stock < new_base_cons:
                return False, f"Stock de Base insuffisant (Requis: {new_base_cons:.1f} ML, Dispo: {base_stock:.1f} ML)."
            if alcool_stock < new_alcool_cons:
                return False, f"Stock d'Alcool insuffisant (Requis: {new_alcool_cons:.1f} ML, Dispo: {alcool_stock:.1f} ML)."
            if flacon_stock < new_flacon_cons:
                return False, "Stock de Flacons insuffisant."
            # Calculate costs for Directe
            cump_base = CostingService.get_cump_from_inventory(base_name, qualite_base, "Base Parfum")
            cump_alcool = CostingService.get_cump_from_inventory(alcool_name, categorie="Alcool")
            cump_flacon = CostingService.get_cump_from_inventory(flacon_name, categorie="Flacon")
            
            cout_base = new_base_cons * cump_base
            cout_alcool = new_alcool_cons * cump_alcool
            cout_flacon = new_flacon_cons * cump_flacon
            cout_total = cout_base + cout_alcool + cout_flacon
            cout_unitaire = cout_total / new_flacon_cons if new_flacon_cons > 0 else 0.0
            
            updates = {
                "Date": date_prod.strftime("%Y-%m-%d") if hasattr(date_prod, "strftime") else str(date_prod),
                "Nom_Base": base_name,
                "Qualite_Base": qualite_base,
                "Quantite_Base_ML": new_base_cons,
                "Quantite_Alcool_ML": new_alcool_cons,
                "Nom_Flacon": flacon_name,
                "Taille_Flacon": taille_flacon,
                "Quantite_Flacons": new_flacon_cons,
                "Nom_Parfum": base_name,
                "Cout_Base": cout_base,
                "Cout_Alcool": cout_alcool,
                "Cout_Flacon": cout_flacon,
                "Cout_Total": cout_total,
                "Cout_Unitaire": cout_unitaire,
                "Nom_Alcool": alcool_name,
                "Type_Production": "Fini"
            }

        elif new_type == "🧪 Mise en Macération (Vrac)":
            new_base_cons = ml_base
            new_alcool_cons = ml_alcool
            volume_total = new_base_cons + new_alcool_cons
            
            if base_stock < new_base_cons:
                return False, f"Stock de Base insuffisant (Requis: {new_base_cons:.1f} ML, Dispo: {base_stock:.1f} ML)."
            if alcool_stock < new_alcool_cons:
                return False, f"Stock d'Alcool insuffisant (Requis: {new_alcool_cons:.1f} ML, Dispo: {alcool_stock:.1f} ML)."
                
            cump_base = CostingService.get_cump_from_inventory(base_name, qualite_base)
            cump_alcool = CostingService.get_cump_from_inventory(alcool_name)
            
            cout_base = new_base_cons * cump_base
            cout_alcool = new_alcool_cons * cump_alcool
            cout_total = cout_base + cout_alcool
            cout_unitaire = cout_total / volume_total if volume_total > 0 else 0.0
            
            updates = {
                "Date": date_prod.strftime("%Y-%m-%d") if hasattr(date_prod, "strftime") else str(date_prod),
                "Nom_Base": base_name,
                "Qualite_Base": qualite_base,
                "Quantite_Base_ML": new_base_cons,
                "Quantite_Alcool_ML": new_alcool_cons,
                "Nom_Flacon": "Aucun",
                "Taille_Flacon": "Vrac",
                "Quantite_Flacons": 0,
                "Nom_Parfum": base_name,
                "Cout_Base": cout_base,
                "Cout_Alcool": cout_alcool,
                "Cout_Flacon": 0.0,
                "Cout_Total": cout_total,
                "Cout_Unitaire": cout_unitaire,
                "Nom_Alcool": alcool_name,
                "Type_Production": "Macération"
            }
            
        elif new_type == "🧴 Mise en Bouteille (Depuis Vrac)":
            try:
                t_ml = float(str(taille_flacon).split()[0])
            except:
                t_ml = 50.0
                
            macerat_needed = t_ml * qty_flacons
            new_flacon_cons = qty_flacons
            
            if macerat_stock < macerat_needed:
                return False, f"Stock de Macérat insuffisant (Requis: {macerat_needed:.1f} ML, Dispo: {macerat_stock:.1f} ML)."
            if flacon_stock < new_flacon_cons:
                return False, "Stock de Flacons insuffisant."
            # Calculate costs for Mise en Flacon
            cump_macerat = CostingService.get_cump_from_inventory(base_name, qualite_base, "Macérat")
            cump_flacon = CostingService.get_cump_from_inventory(flacon_name, categorie="Flacon")
            
            cout_macerat = macerat_needed * cump_macerat
            cout_flacon = cump_flacon * new_flacon_cons
            cout_total = cout_macerat + cout_flacon
            cout_unitaire = cout_total / new_flacon_cons if new_flacon_cons > 0 else 0.0
            
            updates = {
                "Date": date_prod.strftime("%Y-%m-%d") if hasattr(date_prod, "strftime") else str(date_prod),
                "Nom_Base": base_name,
                "Qualite_Base": qualite_base,
                "Quantite_Base_ML": 0.0,
                "Quantite_Alcool_ML": 0.0,
                "Nom_Flacon": flacon_name,
                "Taille_Flacon": taille_flacon,
                "Quantite_Flacons": new_flacon_cons,
                "Nom_Parfum": base_name,
                "Cout_Base": cout_macerat,
                "Cout_Alcool": 0.0,
                "Cout_Flacon": cout_flacon,
                "Cout_Total": cout_total,
                "Cout_Unitaire": cout_unitaire,
                "Nom_Alcool": "",
                "Type_Production": "Mise en Flacon"
            }
            
        for k, v in updates.items():
            df_prod.at[idx, k] = v
            
        st.session_state["production"] = df_prod
        BaseModel.save_df("production")
        StockService.rebuild_inventory()
        BaseModel.log_movement("MODIF_PROD", old_row["ID"], "Correction de Type", 0, updates["Cout_Total"] - clean_numeric(old_row["Cout_Total"]), 0, 0)
        return True, "Production modifiée avec succès."
