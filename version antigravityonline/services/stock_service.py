import pandas as pd
import streamlit as st
from datetime import datetime
from models.base_model import BaseModel
from utils.helpers import clean_numeric

class StockService:
    @staticmethod
    def get_stock(item_name, qualite="", categorie=""):
        """Dynamically calculates real stock from all operations to avoid physical sync issues"""
        # Ensure all dataframes are loaded
        df_purch = BaseModel.load_df("purchases")
        df_prod = BaseModel.load_df("production")
        df_ventes = BaseModel.load_df("ventes")
        df_offres = BaseModel.load_df("offres")
        df_pertes = BaseModel.load_df("pertes")
        
        # 1. Total Purchases
        purch_qty = 0.0
        if not df_purch.empty:
            purch_qual = df_purch["Qualite"].fillna("").astype(str).str.strip()
            filt = (df_purch["Nom"] == item_name) & (purch_qual == qualite)
            purch_qty = clean_numeric(df_purch[filt]["Quantite_ML"].sum())

        # 2. Total Production Consumption (For raw materials)
        prod_cons = 0.0
        if not df_prod.empty:
            prod_qual = df_prod["Qualite_Base"].fillna("").astype(str).str.strip()
            # Base Parfum consumption
            if "Nom_Base" in df_prod.columns:
                base_cons = clean_numeric(df_prod[(df_prod["Nom_Base"] == item_name) & (prod_qual == qualite)]["Quantite_Base_ML"].sum())
            else:
                base_cons = 0.0
            # Alcool consumption
            if "Nom_Alcool" in df_prod.columns:
                alcool_cons = clean_numeric(df_prod[df_prod["Nom_Alcool"] == item_name]["Quantite_Alcool_ML"].sum())
            else:
                alcool_cons = 0.0
            # Flacon consumption
            if "Nom_Flacon" in df_prod.columns:
                flacon_cons = clean_numeric(df_prod[df_prod["Nom_Flacon"] == item_name]["Quantite_Flacons"].sum())
            else:
                flacon_cons = 0.0
            prod_cons = base_cons + alcool_cons + flacon_cons

        # 3. Total Production Input (For manufactured perfumes)
        prod_in = 0.0
        if not df_prod.empty:
            prod_qual = df_prod["Qualite_Base"].fillna("").astype(str).str.strip()
            prod_in = clean_numeric(df_prod[(df_prod["Nom_Parfum"] == item_name) & (prod_qual == qualite)]["Quantite_Flacons"].sum())

        # 4. Total Sales
        sales_qty = 0.0
        if not df_ventes.empty:
            # Ventes can be stock sales or direct fab (both deduct from finished goods stock or are directly fabbed)
            # Standard vente deductions
            ventes_qual = df_ventes["Qualite"].fillna("").astype(str).str.strip()
            sales_qty = clean_numeric(df_ventes[(df_ventes["Nom_Parfum"] == item_name) & (ventes_qual == qualite)]["Quantite"].sum())

        # 5. Total Offers
        offres_qty = 0.0
        if not df_offres.empty:
            offres_qual = df_offres["Qualite"].fillna("").astype(str).str.strip()
            offres_qty = clean_numeric(df_offres[(df_offres["Nom_Parfum"] == item_name) & (offres_qual == qualite)]["Quantite"].sum())

        # 6. Total Losses
        losses_qty = 0.0
        if not df_pertes.empty:
            pertes_qual = df_pertes["Qualite"].fillna("").astype(str).str.strip()
            losses_qty = clean_numeric(df_pertes[(df_pertes["Nom_Parfum"] == item_name) & (pertes_qual == qualite)]["Quantite"].sum())

        # Logic separation: Parfums vs Raw Materials
        if categorie == "Parfum Fini":
            return prod_in - sales_qty - offres_qty - losses_qty
        elif categorie == "Macérat":
            if not df_prod.empty:
                type_prod = df_prod.get("Type_Production", pd.Series(["Fini"] * len(df_prod)))
                prod_qual = df_prod["Qualite_Base"].fillna("").astype(str).str.strip()
                
                # Volume produced (Mise en macération)
                macerat_df = df_prod[(df_prod["Nom_Parfum"] == item_name) & (prod_qual == qualite) & (type_prod == "Macération")]
                macerat_produit = clean_numeric(macerat_df["Quantite_Base_ML"].sum()) + clean_numeric(macerat_df["Quantite_Alcool_ML"].sum())
                
                # Volume consumed (Mise en Flacon)
                bottling_df = df_prod[(df_prod["Nom_Parfum"] == item_name) & (prod_qual == qualite) & (type_prod == "Mise en Flacon")]
                macerat_consomme = 0.0
                for _, row in bottling_df.iterrows():
                    try:
                        t = float(str(row["Taille_Flacon"]).split()[0])
                        macerat_consomme += t * clean_numeric(row["Quantite_Flacons"])
                    except:
                        pass
                
                return macerat_produit - macerat_consomme
            return 0.0
        else:
            return purch_qty - prod_cons

    @staticmethod
    def rebuild_inventory():
        """Rebuilds the inventory dataframe dynamically based on all transactions"""
        df_purch = BaseModel.load_df("purchases")
        df_prod = BaseModel.load_df("production")
        
        # We find all unique items in purchases — iterate using row values directly
        raw_items = set()
        if not df_purch.empty:
            for _, row in df_purch.iterrows():
                nom = str(row["Nom"]).strip() if pd.notna(row["Nom"]) else ""
                qualite = str(row["Qualite"]).strip() if pd.notna(row.get("Qualite", "")) else ""
                cat = str(row["Categorie"]).strip() if pd.notna(row["Categorie"]) else ""
                if nom:
                    raw_items.add((nom, qualite, cat))
                
        perfumes = set()
        macerats = set()
        if not df_prod.empty:
            type_prod = df_prod.get("Type_Production", pd.Series(["Fini"] * len(df_prod)))
            for _, row in df_prod.iterrows():
                nom = str(row["Nom_Parfum"]).strip() if pd.notna(row.get("Nom_Parfum", "")) else ""
                qualite = str(row["Qualite_Base"]).strip() if pd.notna(row.get("Qualite_Base", "")) else ""
                if nom:
                    if row.get("Type_Production", "Fini") == "Macération":
                        macerats.add((nom, qualite, "Macérat"))
                    else:
                        perfumes.add((nom, qualite, "Parfum Fini"))
                
        all_unique = list(raw_items | perfumes | macerats)
        
        new_inv_rows = []
        for nom, qualite, cat in all_unique:
            nom = str(nom).strip()
            qualite = str(qualite).strip() if qualite and qualite != "nan" else ""
            cat = str(cat).strip()
            
            if not nom:
                continue
                
            qty = StockService.get_stock(nom, qualite, cat)
            
            # Find CUMP
            cump = 0.0
            if cat == "Parfum Fini":
                # Average unitaire cost from production
                if not df_prod.empty:
                    prod_qual = df_prod["Qualite_Base"].fillna("").astype(str).str.strip()
                    type_prod = df_prod.get("Type_Production", pd.Series(["Fini"] * len(df_prod)))
                    matches = df_prod[(df_prod["Nom_Parfum"] == nom) & (prod_qual == qualite) & (type_prod != "Macération")]
                    if not matches.empty:
                        total_cost = clean_numeric(matches["Cout_Total"].sum())
                        total_qty = clean_numeric(matches["Quantite_Flacons"].sum())
                        if total_qty > 0:
                            cump = total_cost / total_qty
            elif cat == "Macérat":
                if not df_prod.empty:
                    prod_qual = df_prod["Qualite_Base"].fillna("").astype(str).str.strip()
                    type_prod = df_prod.get("Type_Production", pd.Series(["Fini"] * len(df_prod)))
                    matches = df_prod[(df_prod["Nom_Parfum"] == nom) & (prod_qual == qualite) & (type_prod == "Macération")]
                    if not matches.empty:
                        total_cost = clean_numeric(matches["Cout_Total"].sum())
                        total_vol = clean_numeric(matches["Quantite_Base_ML"].sum()) + clean_numeric(matches["Quantite_Alcool_ML"].sum())
                        if total_vol > 0:
                            cump = total_cost / total_vol
            else:
                # CUMP from purchases — Weighted average
                if not df_purch.empty:
                    purch_qual = df_purch["Qualite"].fillna("").astype(str).str.strip()
                    matches = df_purch[(df_purch["Nom"] == nom) & (purch_qual == qualite)]
                    if not matches.empty:
                        total_val = clean_numeric(matches["Prix_Total"].sum())
                        total_qty = clean_numeric(matches["Quantite_ML"].sum())
                        cump = total_val / total_qty if total_qty > 0 else 0.0
                    
            valeur_stock = qty * cump
            
            # Find image path from purchases
            img_path = ""
            if not df_purch.empty:
                img_match = df_purch[df_purch["Nom"] == nom]
                if not img_match.empty:
                    ip = img_match.iloc[0].get("Image_Path", "")
                    img_path = str(ip) if pd.notna(ip) else ""
            # Also check production for perfume images
            if not img_path and cat == "Parfum Fini" and not df_prod.empty:
                prod_match = df_prod[df_prod["Nom_Parfum"] == nom]
                if not prod_match.empty:
                    ip = prod_match.iloc[0].get("Image_Path", "")
                    img_path = str(ip) if pd.notna(ip) else ""
                    
            # Extract Genre and Saison from purchases (works for Base Parfum, and we can inherit for Parfum Fini)
            genre = "Mixte"
            saison = "Toutes Saisons"
            if not df_purch.empty:
                # If Parfum Fini, we look for the Base Parfum with the same name
                search_cat = "Base Parfum" if cat == "Parfum Fini" else cat
                gs_match = df_purch[(df_purch["Nom"] == nom) & (df_purch["Categorie"] == search_cat)]
                if not gs_match.empty:
                    val_g = gs_match.iloc[-1].get("Genre", "")
                    val_s = gs_match.iloc[-1].get("Saison", "")
                    if pd.notna(val_g) and str(val_g).strip(): genre = str(val_g).strip()
                    if pd.notna(val_s) and str(val_s).strip(): saison = str(val_s).strip()

            nom_key = nom[:3].upper() if nom else "UNK"
            qual_key = qualite[:3].upper() if qualite else "NA"
            cat_key = cat[:3].upper() if cat else "GEN"
            
            new_inv_rows.append({
                "ID": f"INV-{nom_key}-{qual_key}",
                "Code": f"{cat_key}-{nom_key}",
                "Categorie": cat,
                "Nom": nom,
                "Qualite": qualite,
                "Genre": genre,
                "Saison": saison,
                "Quantite_ML": qty,
                "CUMP": cump,
                "Valeur_Stock_Totale": valeur_stock,
                "Date_Derniere_MAJ": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Image_Path": img_path
            })
            
        st.session_state["inventory"] = pd.DataFrame(new_inv_rows)
        BaseModel.save_df("inventory")
