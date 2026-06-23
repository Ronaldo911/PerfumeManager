import re

with open('views/production_view.py', 'r', encoding='utf-8') as f:
    content = f.read()

replacement = """                for idx, row in df_prod.iterrows():
                    with st.expander(f"?? {row['Nom_Parfum']} - {row['Date']} ({row['Quantite_Flacons']} Flacons x {row['Taille_Flacon']}) - Type: {row.get('Type_Production', 'Fini')}"):
                        st.write("**?? Édition Avancée**")
                        
                        e_type = st.radio("Type d'opération", ["?? Fabrication Complète (Directe)", "?? Mise en Macération (Vrac)", "?? Mise en Bouteille (Depuis Vrac)"], key=f"e_type_{idx}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            try:
                                d_val = pd.to_datetime(row['Date']).date()
                            except:
                                d_val = date.today()
                            e_date = st.date_input("Date", value=d_val, key=f"e_date_{idx}")
                            
                            # Base and Alcool defaults
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
                            # Flacon defaults
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
                            
                            if e_type == "?? Fabrication Complète (Directe)":
                                e_ml_base = st.number_input("Base par flacon (ML)", min_value=0.1, value=15.0, step=1.0, key=f"e_v_base_{idx}")
                                try:
                                    t_ml = float(e_taille.split()[0])
                                except:
                                    t_ml = 50.0
                                e_ml_alcool = max(0.0, t_ml - e_ml_base)
                                st.write(f"Alcool par flacon: {e_ml_alcool:.1f} ML")
                                e_qty = st.number_input("Nombre de flacons", min_value=1, value=int(row.get("Quantite_Flacons", 1)) if int(row.get("Quantite_Flacons", 1)) > 0 else 1, step=1, key=f"e_qty_{idx}")
                            elif e_type == "?? Mise en Macération (Vrac)":
                                e_ml_base = st.number_input("Volume Total Base (ML)", min_value=1.0, value=clean_numeric(row.get("Quantite_Base_ML", 150.0)), step=10.0, key=f"e_m_base_{idx}")
                                e_ml_alcool = st.number_input("Volume Total Alcool (ML)", min_value=1.0, value=clean_numeric(row.get("Quantite_Alcool_ML", 350.0)), step=10.0, key=f"e_m_alc_{idx}")
                                e_qty = 0
                            elif e_type == "?? Mise en Bouteille (Depuis Vrac)":
                                e_qty = st.number_input("Nombre de flacons à remplir", min_value=1, value=int(row.get("Quantite_Flacons", 1)) if int(row.get("Quantite_Flacons", 1)) > 0 else 1, step=1, key=f"e_b_qty_{idx}")
                                e_ml_base = 0.0
                                e_ml_alcool = 0.0

                        pin_edit = st.text_input("?? Code PIN Modification", type="password", key=f"pin_prod_edit_{idx}")
                        
                        col_actions1, col_actions2 = st.columns(2)
                        with col_actions1:
                            if st.button("?? Enregistrer Modification", key=f"btn_prod_edit_{idx}"):
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
                            if st.button("??? Annuler Production", key=f"btn_prod_del_{idx}"):
                                success, msg = ProductionController.delete_production(idx, pin_edit)
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)"""

# Find the loop to replace
pattern = re.compile(r"                for idx, row in df_prod\.iterrows\(\):.*?st\.error\(msg\)", re.DOTALL)
new_content = pattern.sub(replacement, content)

with open('views/production_view.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
