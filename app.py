import xmlrpc.client
import streamlit as st
import streamlit.components.v1 as components
import re

# ================= CONFIGURACIÓN FIJA DE ODOO =================
URL = "https://pcpistons.odoo.com"
DB = "antrafs-manufacturas-main-18053459"
USERNAME = "echacin@pcpistons.com"
API_KEY = "9e19c999d117f347b274b0d6fa42c2d323d2e213" # <--- PEGA TU CLAVE DENTRO DE ESTAS COMILLAS
# ==============================================================

st.set_page_config(page_title="Estructura de Costos - PC Pistons", layout="centered")

st.markdown('''
    <style>
    .block-container { padding-top: 1rem !important; }
    
    @media print {
        .no-print, header, footer, .stSidebar, .stButton, .stAlert,
        [data-testid="stSidebar"], [data-testid="stHeader"], 
        [data-testid="stTextInput"], [data-testid="stAlert"], iframe { display: none !important; }
        
        @page { margin: 0mm; }
        
        .main .block-container, div[data-testid="stAppViewBlockContainer"] {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }
        
        body { 
            background-color: white !important; 
            margin: 0 !important; 
            padding: 5mm 15mm 5mm 15mm !important; 
        }
        
        .document-container { 
            border: none !important; 
            padding: 0 !important; 
            margin: 0 !important; 
            width: 100% !important; 
            max-width: 100% !important; 
            box-shadow: none !important; 
        }
        
        .signatures { margin-top: 80px !important; page-break-inside: avoid; }
        .doc-subtitle { margin-bottom: 10px !important; }
        
        table { page-break-inside: auto; margin-top: 10px !important; }
        tr { page-break-inside: avoid; page-break-after: auto; }
    }
    
    .document-container { background-color: white; color: black; font-family: "Courier New", Courier, monospace, Arial; padding: 30px 40px; margin: 0 auto; max-width: 800px; border: 1px solid #ddd; }
    .text-center { text-align: center; }
    .company-header { font-weight: bold; letter-spacing: 2px; border-bottom: 2px solid #000; padding-bottom: 4px; margin-bottom: 15px; margin-top: 0px; text-align: center; font-size: 16px; }
    .doc-title { font-weight: bold; font-size: 18px; margin-bottom: 4px; }
    .doc-subtitle { font-weight: bold; font-size: 15px; margin-bottom: 25px; }
    .row-flex { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px; }
    
    .table-cost { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; table-layout: fixed; }
    .table-cost td { padding: 4px 6px; border-bottom: 1px solid #eeeeee; }
    .col-label { width: 88%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .col-total { width: 12%; text-align: right; font-weight: bold; }
    
    .subtotal-row { font-weight: bold; border-top: 1px solid #000; border-bottom: 1px solid #000 !important; }
    .section-title { font-weight: bold; padding-top: 15px !important; border-bottom: none !important; }
    
    .signatures { display: flex; justify-content: space-between; margin-top: 130px; padding: 0 40px; }
    .signature-line { width: 40%; text-align: center; border-top: 1px solid #000; padding-top: 6px; font-size: 14px; }
    </style>
''', unsafe_allow_html=True)

@st.cache_data(ttl=300, show_spinner=False)
def fetch_pricelists(url, db, username, api_key):
    if not api_key or api_key == "TU_CLAVE_API_AQUI": return []
    try:
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        uid = common.authenticate(db, username, api_key, {})
        if not uid: return []
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        return models.execute_kw(db, uid, api_key, 'product.pricelist', 'search_read', [[]], {'fields': ['id', 'name']})
    except:
        return []

st.sidebar.markdown("### 🟢 Estado: En línea")
st.sidebar.markdown("---")
st.sidebar.header("💰 Precios y Tasa")

listas = fetch_pricelists(URL, DB, USERNAME, API_KEY)
opciones_listas = {p['name']: p['id'] for p in listas} if listas else {}
lista_seleccionada = st.sidebar.selectbox("Lista de Precios (Ventas)", options=["Ninguna"] + list(opciones_listas.keys()))

tasa_cambio = st.sidebar.number_input("Tasa de Cambio (Bs/$)", value=791.67, format="%.2f")

st.sidebar.markdown("---")
st.sidebar.header("✏️ Edición Manual")
usar_precio_manual = st.sidebar.checkbox("Ingresar precio manualmente")
precio_manual_bs = 0.0
if usar_precio_manual:
    precio_manual_bs = st.sidebar.number_input("Precio de Venta (Bs)", min_value=0.0, value=0.0, format="%.2f")

st.markdown('<div class="no-print"><h3>Generador de Hoja de Costos</h3></div>', unsafe_allow_html=True)
col_in1, col_in2 = st.columns([3, 1])
with col_in1:
    codigo_busqueda = st.text_input("Código del Pistón:", placeholder="Ej. EPV-4026R-STD-3", label_visibility="collapsed").strip().upper()
with col_in2:
    btn_buscar = st.button("🔍 Generar Hoja", use_container_width=True)

CAMPO_COSTO = 'x_studio_costo_reposicin_us' 

def fmt(n, decimals=2):
    if decimals == 4:
        return f"{n:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_row(name, total):
    total_str = fmt(total, decimals=4)
    return f"<tr><td class='col-label'>&nbsp;&nbsp;{name}</td><td class='col-total' style='font-weight: normal; padding-right: 40px;'>{total_str}</td></tr>"

def sort_key(item):
    name = item['name'].strip()
    if name.startswith('[') or name.startswith('('):
        return name[1:]
    return name

if btn_buscar and codigo_busqueda:
    if API_KEY == "TU_CLAVE_API_AQUI":
        st.error("⚠️ Faltan las credenciales. Por favor, edita el archivo app.py e ingresa tu Clave API en la línea 10.")
    else:
        try:
            common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
            uid = common.authenticate(DB, USERNAME, API_KEY, {})
            models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

            prod_ids = models.execute_kw(DB, uid, API_KEY, 'product.product', 'search', [[['default_code', '=', codigo_busqueda]]])
            
            if not prod_ids:
                st.error("No se encontró ningún producto EXACTO con ese código. Verifica que esté escrito igual que en Odoo.")
            else:
                prod_data = models.execute_kw(DB, uid, API_KEY, 'product.product', 'read', [prod_ids[0]], 
                                              {'fields': ['name', 'default_code', 'uom_id', 'product_tmpl_id']})[0]
                
                codigo_mostrar = prod_data.get('default_code', '')
                tmpl_id = prod_data.get('product_tmpl_id', [0])[0]
                target_description = prod_data.get('name', '').upper()

                ALL_MARKERS = ['0.25', '0.50', '0.75', '1.00', '010', '020', '030', '040', '060', '080', '0.20', '0.30', '0.40', '0.60', '0.80', 'STD']
                target_measures = []
                
                cb = codigo_busqueda.upper()
                for m in ALL_MARKERS:
                    if f"-{m}" in cb:
                        target_measures.append(m)
                        if m == '0.25': target_measures.append('010')
                        if m == '010': target_measures.append('0.25')
                        if m == '0.50': target_measures.append('020')
                        if m == '020': target_measures.append('0.50')
                        if m == '0.75': target_measures.append('030')
                        if m == '030': target_measures.append('0.75')
                        if m == '1.00': target_measures.append('040')
                        if m == '040': target_measures.append('1.00')
                        if m == '0.20': target_measures.append('020')
                        if m == '020': target_measures.append('0.20')
                        if m == '0.30': target_measures.append('030')
                        if m == '030': target_measures.append('0.30')
                        if m == '0.40': target_measures.append('040')
                        if m == '040': target_measures.append('0.40')
                        if m == '0.60': target_measures.append('060')
                        if m == '060': target_measures.append('0.60')
                        if m == '0.80': target_measures.append('080')
                        if m == '080': target_measures.append('0.80')
                        
                target_measures = list(set(target_measures))
                keywords_to_filter = ["MECANIZADO", "ANILLO", "CAMISA", "CASTING", "SEMIKIT"]

                comp_list, mod_list, moi_list, caf_list = [], [], [], []
                
                # VARIABLE PARA GUARDAR LA MEDIDA DE LA CAJA (LA EXTRAEREMOS DE LA BOM)
                caja_medida_extraida = None

                bom_ids = models.execute_kw(DB, uid, API_KEY, 'mrp.bom', 'search', [[['product_tmpl_id', '=', tmpl_id]]])
                
                if bom_ids:
                    bom_lines = models.execute_kw(DB, uid, API_KEY, 'mrp.bom.line', 'search_read', 
                                                  [[['bom_id', '=', bom_ids[0]]]], 
                                                  {'fields': ['product_id', 'product_qty']})
                    
                    for line in bom_lines:
                        comp_name = line['product_id'][1].upper()
                        qty = line['product_qty']
                        
                        # NUEVA LÓGICA: Si es una CAJA, extraemos su número de cilindros para corregir el UOM
                        if "CAJA" in comp_name and "CIL" in comp_name:
                            match = re.search(r'(\d+)\s*CIL', comp_name)
                            if match:
                                caja_medida_extraida = match.group(1)
                        
                        # FILTRO SELECTIVO DE MEDIDAS (Solo afecta a Mecanizado, Anillos, etc)
                        is_measure_sensitive = any(kw in comp_name for kw in keywords_to_filter)
                        
                        if is_measure_sensitive and target_measures:
                            tiene_alguna_medida = False
                            for m in ALL_MARKERS:
                                if re.search(r'(?:^|[^a-zA-Z0-9])' + re.escape(m) + r'(?:[^a-zA-Z0-9]|$)', comp_name):
                                    tiene_alguna_medida = True
                                    break
                            
                            if tiene_alguna_medida:
                                es_mi_medida = False
                                for m in target_measures:
                                    if re.search(r'(?:^|[^a-zA-Z0-9])' + re.escape(m) + r'(?:[^a-zA-Z0-9]|$)', comp_name):
                                        es_mi_medida = True
                                        break
                                
                                if not es_mi_medida:
                                    continue
                        
                        comp_id = line['product_id'][0]
                        comp_data = models.execute_kw(DB, uid, API_KEY, 'product.product', 'read', [comp_id], {'fields': [CAMPO_COSTO, 'standard_price']})[0]
                        
                        costo_unitario = comp_data.get(CAMPO_COSTO, 0.0)
                        if not isinstance(costo_unitario, (int, float)) or costo_unitario == 0.0:
                            costo_unitario = comp_data.get('standard_price', 0.0)
                            if not isinstance(costo_unitario, (int, float)):
                                costo_unitario = 0.0
                            
                        costo_linea = qty * costo_unitario
                        item_data = {'name': comp_name, 'total': costo_linea}

                        if "MOD-" in comp_name or "MANO DE OBRA DIR" in comp_name or "MECANIZADO" in comp_name or "CASTING" in comp_name:
                            mod_list.append(item_data)
                        elif "MOI-" in comp_name or "MANO DE OBRA IND" in comp_name:
                            moi_list.append(item_data)
                        elif "CAF-" in comp_name or "CARGA FABRIL" in comp_name:
                            caf_list.append(item_data)
                        else:
                            comp_list.append(item_data)

                # =========================================================================
                # DECISIÓN FINAL DEL NOMBRE DE UNIDAD / MEDIDA
                # Si logramos extraer la caja de los componentes, lo usamos. 
                # De lo contrario, tomamos el valor nativo crudo de Odoo como respaldo.
                if caja_medida_extraida:
                    uom_name = f"Caja {caja_medida_extraida}"
                else:
                    uom_raw = prod_data.get('uom_id', [0, ''])[1]
                    if "Pieza X" in uom_raw:
                        uom_raw = uom_raw.replace("Pieza X", "Caja")
                    uom_name = uom_raw
                # =========================================================================

                comp_list.sort(key=sort_key)
                mod_list.sort(key=sort_key)
                moi_list.sort(key=sort_key)
                caf_list.sort(key=sort_key)

                html_comp = "".join(format_row(i['name'], i['total']) for i in comp_list)
                html_mod = "".join(format_row(i['name'], i['total']) for i in mod_list)
                html_moi = "".join(format_row(i['name'], i['total']) for i in moi_list)
                html_caf = "".join(format_row(i['name'], i['total']) for i in caf_list)

                comp_total = sum(i['total'] for i in comp_list)
                mod_total = sum(i['total'] for i in mod_list)
                moi_total = sum(i['total'] for i in moi_list)
                caf_total = sum(i['total'] for i in caf_list)
                total_costo = comp_total + mod_total + moi_total + caf_total

                precio_venta_usd = 0.0
                precio_bs = 0.0
                
                if usar_precio_manual:
                    precio_bs = precio_manual_bs
                    etiqueta_precio = "Precio de Venta <u>(SUGERIDO):</u>"
                else:
                    etiqueta_precio = "Precio de Venta:"
                    if lista_seleccionada != "Ninguna" and tmpl_id:
                        plist_id = opciones_listas[lista_seleccionada]
                        
                        try:
                            domain_tmpl = [['pricelist_id', '=', plist_id], ['product_tmpl_id', '=', tmpl_id]]
                            reglas_tmpl = models.execute_kw(DB, uid, API_KEY, 'product.pricelist.item', 'search_read', [domain_tmpl], {'fields': ['fixed_price', 'price']})
                            
                            if reglas_tmpl:
                                precio_bs = float(reglas_tmpl[0].get('fixed_price', 0.0))
                                if precio_bs == 0.0: precio_bs = float(reglas_tmpl[0].get('price', 0.0))
                            
                            if precio_bs == 0.0:
                                domain_prod = [['pricelist_id', '=', plist_id], ['product_id', '=', prod_ids[0]]]
                                reglas_prod = models.execute_kw(DB, uid, API_KEY, 'product.pricelist.item', 'search_read', [domain_prod], {'fields': ['fixed_price', 'price']})
                                if reglas_prod:
                                    precio_bs = float(reglas_prod[0].get('fixed_price', 0.0))
                                    if precio_bs == 0.0: precio_bs = float(reglas_prod[0].get('price', 0.0))

                            if precio_bs == 0.0:
                                todas = models.execute_kw(DB, uid, API_KEY, 'product.pricelist.item', 'search_read', 
                                                          [[['pricelist_id', '=', plist_id]]], 
                                                          {'fields': ['product_tmpl_id', 'product_id', 'fixed_price', 'price'], 'limit': 100000})
                                
                                for r in todas:
                                    r_tmpl = r.get('product_tmpl_id')
                                    r_tmpl_id = r_tmpl[0] if isinstance(r_tmpl, list) else (r_tmpl or 0)
                                    
                                    r_prod = r.get('product_id')
                                    r_prod_id = r_prod[0] if isinstance(r_prod, list) else (r_prod or 0)
                                    
                                    if r_tmpl_id == tmpl_id or r_prod_id == prod_ids[0]:
                                        precio_bs = float(r.get('fixed_price', 0.0))
                                        if precio_bs == 0.0: precio_bs = float(r.get('price', 0.0))
                                        if precio_bs > 0: break
                        except Exception as e:
                            st.error(f"Error extrayendo de lista de precios: {e}")

                if tasa_cambio > 0 and precio_bs > 0:
                    precio_venta_usd = precio_bs / tasa_cambio

                margen_usd = precio_venta_usd - total_costo
                margen_pct = (margen_usd / total_costo * 100) if total_costo > 0 else 0.0

                if precio_bs == 0.0 and not usar_precio_manual:
                    st.markdown('<div class="no-print" style="padding: 15px; background-color: #fff3cd; color: #856404; border-left: 6px solid #ffeeba; border-radius: 4px; margin-bottom: 20px;">⚠️ <strong>Atención:</strong> Este producto no tiene precio asignado en la lista seleccionada. Usa la opción "Ingresar precio manualmente" en el menú de la izquierda.</div>', unsafe_allow_html=True)

                components.html(
                    """
                    <div style="text-align: center; font-family: sans-serif; margin-top: 10px;">
                        <button onclick="window.parent.print()" style="background-color: #2196F3; color: white; border: none; padding: 12px 24px; font-size: 16px; font-weight: bold; border-radius: 6px; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: 0.3s;">
                            🖨️ IMPRIMIR REPORTE
                        </button>
                    </div>
                    """,
                    height=70
                )

                html_doc = f'''
<div class="document-container">
<div class="company-header">MANUFACTURAS DE ALUMINIO I, C.A.</div>
<div class="text-center doc-title">Estructura de Costos</div>
<div class="text-center doc-subtitle">y<br>Determinación de Precio de Venta<br>(USD)</div>
<div class="row-flex">
<div><strong>Código:</strong> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {codigo_mostrar}</div>
<div><strong>Unidad/Medida:</strong> &nbsp;&nbsp;&nbsp;&nbsp; {uom_name}</div>
</div>
<div class="row-flex" style="margin-bottom: 20px;">
<div><strong>Aplicación:</strong> &nbsp;&nbsp;&nbsp;&nbsp; {target_description}</div>
</div>
<table class="table-cost">
<tr><td colspan="2" class="section-title">Componentes y Materiales:</td></tr>
{html_comp}
<tr class="subtotal-row"><td class="col-label">Sub-total Componentes:</td><td class="col-total">{fmt(comp_total)}</td></tr>
<tr><td colspan="2" class="section-title">Mano de Obra y Carga Fabril:</td></tr>
{html_mod}
{html_moi}
{html_caf}
<tr class="subtotal-row"><td class="col-label">Sub-total MO y CF:</td><td class="col-total">{fmt(mod_total + moi_total + caf_total)}</td></tr>
<tr><td colspan="2">&nbsp;</td></tr>
<tr class="subtotal-row"><td class="col-label">Total Costo:</td><td class="col-total">{fmt(total_costo)}</td></tr>
<tr><td colspan="2">&nbsp;</td></tr>
<tr class="subtotal-row"><td class="col-label">{etiqueta_precio}</td><td class="col-total" style="text-decoration: underline;">{fmt(precio_venta_usd)}</td></tr>
<tr><td colspan="2">&nbsp;</td></tr>
<tr><td class="col-label"><strong>Margen (USD):</strong></td><td class="col-total"><strong>{fmt(margen_usd)}</strong></td></tr>
<tr><td class="col-label"><strong>Margen (%):</strong></td><td class="col-total"><strong>{fmt(margen_pct)}%</strong></td></tr>
</table>
<div class="signatures">
<div class="signature-line">Elaborado por;</div>
<div class="signature-line">Aprobado por:</div>
</div>
</div>
'''
                st.markdown(html_doc, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error de ejecución: {e}")
