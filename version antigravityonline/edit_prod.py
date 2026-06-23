    @staticmethod
    def edit_production_full(idx, pin, new_type, date_prod, base_name, qualite_base, ml_base, alcool_name, ml_alcool, flacon_name, taille_flacon, qty_flacons):
        if not SecurityController.verify_pin(pin):
            return False, ""Code PIN incorrect.""
            
        df_prod = BaseModel.load_df(""production"")
        if idx < 0 or idx >= len(df_prod):
            return False, ""Production introuvable.""
            
        old_row = df_prod.iloc[idx].copy()
        old_type = old_row.get(""Type_Production"", ""Fini"")
        old_qty_flacons = clean_numeric(old_row.get(""Quantite_Flacons"", 0))
        
        old_base_cons = clean_numeric(old_row.get(""Quantite_Base_ML"", 0))
        old_alcool_cons = clean_numeric(old_row.get(""Quantite_Alcool_ML"", 0))
        old_flacon_cons = old_qty_flacons if old_type in [""Fini"", ""Mise en Flacon""] else 0
        old_macerat_cons = 0.0
        
        if old_type == ""Mise en Flacon"":
            try:
                t_ml = float(str(old_row.get(""Taille_Flacon"", """")).split()[0])
            except:
                t_ml = 50.0
            old_macerat_cons = t_ml * old_qty_flacons

        base_stock = StockService.get_stock(base_name, qualite_base, ""Base Parfum"")
        if old_row[""Nom_Base""] == base_name and old_row[""Qualite_Base""] == qualite_base and old_type != ""Mise en Flacon"":
            base_stock += old_base_cons
            
        alcool_stock = StockService.get_stock(alcool_name, """", ""Alcool"")
        if old_row.get(""Nom_Alcool"") == alcool_name and old_type != ""Mise en Flacon"":
            alcool_stock += old_alcool_cons
            
        flacon_stock = StockService.get_stock(flacon_name, """", ""Flacon"")
        if old_row.get(""Nom_Flacon"") == flacon_name and old_type in [""Fini"", ""Mise en Flacon""]:
            flacon_stock += old_flacon_cons
            
        macerat_stock = StockService.get_stock(base_name, qualite_base, ""Macérat"")
        if old_type == ""Mise en Flacon"" and old_row[""Nom_Base""] == base_name and old_row[""Qualite_Base""] == qualite_base:
            macerat_stock += old_macerat_cons
            
        if new_type == ""?? Fabrication Complète (Directe)"":
            try:
                t_ml = float(str(taille_flacon).split()[0])
            except:
                t_ml = 50.0
            
            new_base_cons = ml_base * qty_flacons
            new_alcool_cons = ml_alcool * qty_flacons
            new_flacon_cons = qty_flacons
            
            if base_stock < new_base_cons:
                return False, f""Stock de Base insuffisant (Requis: {new_base_cons:.1f} ML, Dispo: {base_stock:.1f} ML).""
            if alcool_stock < new_alcool_cons:
                return False, f""Stock d'Alcool insuffisant (Requis: {new_alcool_cons:.1f} ML, Dispo: {alcool_stock:.1f} ML).""
            if flacon_stock < new_flacon_cons:
                return False, ""Stock de Flacons insuffisant.""
                
            cump_base = CostingService.get_cump_from_inventory(base_name, qualite_base)
            cump_alcool = CostingService.get_cump_from_inventory(alcool_name)
            cump_flacon = CostingService.get_cump_from_inventory(flacon_name)
            
            cout_base = new_base_cons * cump_base
            cout_alcool = new_alcool_cons * cump_alcool
            cout_flacon = new_flacon_cons * cump_flacon
            cout_total = cout_base + cout_alcool + cout_flacon
            cout_unitaire = cout_total / new_flacon_cons if new_flacon_cons > 0 else 0.0
            
            updates = {
                ""Date"": date_prod.strftime(""%Y-%m-%d"") if hasattr(date_prod, ""strftime"") else str(date_prod),
                ""Nom_Base"": base_name,
                ""Qualite_Base"": qualite_base,
                ""Quantite_Base_ML"": new_base_cons,
                ""Quantite_Alcool_ML"": new_alcool_cons,
                ""Nom_Flacon"": flacon_name,
                ""Taille_Flacon"": taille_flacon,
                ""Quantite_Flacons"": new_flacon_cons,
                ""Nom_Parfum"": base_name,
                ""Cout_Base"": cout_base,
                ""Cout_Alcool"": cout_alcool,
                ""Cout_Flacon"": cout_flacon,
                ""Cout_Total"": cout_total,
                ""Cout_Unitaire"": cout_unitaire,
                ""Nom_Alcool"": alcool_name,
                ""Type_Production"": ""Fini""
            }

        elif new_type == ""?? Mise en Macération (Vrac)"":
            new_base_cons = ml_base
            new_alcool_cons = ml_alcool
            volume_total = new_base_cons + new_alcool_cons
            
            if base_stock < new_base_cons:
                return False, f""Stock de Base insuffisant (Requis: {new_base_cons:.1f} ML, Dispo: {base_stock:.1f} ML).""
            if alcool_stock < new_alcool_cons:
                return False, f""Stock d'Alcool insuffisant (Requis: {new_alcool_cons:.1f} ML, Dispo: {alcool_stock:.1f} ML).""
                
            cump_base = CostingService.get_cump_from_inventory(base_name, qualite_base)
            cump_alcool = CostingService.get_cump_from_inventory(alcool_name)
            
            cout_base = new_base_cons * cump_base
            cout_alcool = new_alcool_cons * cump_alcool
            cout_total = cout_base + cout_alcool
            cout_unitaire = cout_total / volume_total if volume_total > 0 else 0.0
            
            updates = {
                ""Date"": date_prod.strftime(""%Y-%m-%d"") if hasattr(date_prod, ""strftime"") else str(date_prod),
                ""Nom_Base"": base_name,
                ""Qualite_Base"": qualite_base,
                ""Quantite_Base_ML"": new_base_cons,
                ""Quantite_Alcool_ML"": new_alcool_cons,
                ""Nom_Flacon"": ""Aucun"",
                ""Taille_Flacon"": ""Vrac"",
                ""Quantite_Flacons"": 0,
                ""Nom_Parfum"": base_name,
                ""Cout_Base"": cout_base,
                ""Cout_Alcool"": cout_alcool,
                ""Cout_Flacon"": 0.0,
                ""Cout_Total"": cout_total,
                ""Cout_Unitaire"": cout_unitaire,
                ""Nom_Alcool"": alcool_name,
                ""Type_Production"": ""Macération""
            }
            
        elif new_type == ""?? Mise en Bouteille (Depuis Vrac)"":
            try:
                t_ml = float(str(taille_flacon).split()[0])
            except:
                t_ml = 50.0
                
            macerat_needed = t_ml * qty_flacons
            new_flacon_cons = qty_flacons
            
            if macerat_stock < macerat_needed:
                return False, f""Stock de Macérat insuffisant (Requis: {macerat_needed:.1f} ML, Dispo: {macerat_stock:.1f} ML).""
            if flacon_stock < new_flacon_cons:
                return False, ""Stock de Flacons insuffisant.""
                
            cump_macerat = CostingService.get_cump_from_inventory(base_name, qualite_base, ""Macérat"")
            cump_flacon = CostingService.get_cump_from_inventory(flacon_name)
            
            cout_macerat = macerat_needed * cump_macerat
            cout_flacon = cump_flacon * new_flacon_cons
            cout_total = cout_macerat + cout_flacon
            cout_unitaire = cout_total / new_flacon_cons if new_flacon_cons > 0 else 0.0
            
            updates = {
                ""Date"": date_prod.strftime(""%Y-%m-%d"") if hasattr(date_prod, ""strftime"") else str(date_prod),
                ""Nom_Base"": base_name,
                ""Qualite_Base"": qualite_base,
                ""Quantite_Base_ML"": 0.0,
                ""Quantite_Alcool_ML"": 0.0,
                ""Nom_Flacon"": flacon_name,
                ""Taille_Flacon"": taille_flacon,
                ""Quantite_Flacons"": new_flacon_cons,
                ""Nom_Parfum"": base_name,
                ""Cout_Base"": cout_macerat,
                ""Cout_Alcool"": 0.0,
                ""Cout_Flacon"": cout_flacon,
                ""Cout_Total"": cout_total,
                ""Cout_Unitaire"": cout_unitaire,
                ""Nom_Alcool"": """",
                ""Type_Production"": ""Mise en Flacon""
            }
            
        for k, v in updates.items():
            df_prod.at[idx, k] = v
            
        st.session_state[""production""] = df_prod
        BaseModel.save_df(""production"")
        StockService.rebuild_inventory()
        BaseModel.log_movement(""MODIF_PROD"", old_row[""ID""], ""Correction de Type"", 0, updates[""Cout_Total""] - clean_numeric(old_row[""Cout_Total""]), 0, 0)
        return True, ""Production modifiée avec succès.""
