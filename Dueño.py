import streamlit as st
import pandas as pd
import os

# Configuración de la pantalla del dueño
st.set_page_config(page_title="Consola de Administración - Dueño", page_icon="📈", layout="centered")

EXCEL_FILE = 'registro_barberia.xlsx'
BARBEROS_FILE = 'barberos.xlsx'
PIN_ADMIN = "1234"  # Tu PIN de administrador

# Precios de los servicios
SERVICIOS = {
    "Corte Normal ($200)": 200,
    "Solo Barba ($100)": 100,
    "Combo Corte + Barba ($280)": 280,
    "Tinte / Otro ($150)": 150
}

# Verificar bases de datos
if not os.path.exists(EXCEL_FILE) or not os.path.exists(BARBEROS_FILE):
    st.error("Faltan archivos de la base de datos. Asegúrate de que el sistema esté corriendo.")
    st.stop()

# Leer datos en tiempo real
df = pd.read_excel(EXCEL_FILE)
df_barberos_db = pd.read_excel(BARBEROS_FILE)
lista_barberos = df_barberos_db['Barbero'].tolist()

# Separar clientes activos para monitoreo visual
df_activos = df[df['Estado'].isin(['En espera', 'Atendiendo'])].copy()
if len(df_activos) > 0:
    df_activos['Prioridad'] = df_activos['Estado'].map({'Atendiendo': 1, 'En espera': 2})
    df_activos = df_activos.sort_values(by=['Prioridad', 'ID'])

# Estilos visuales
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .card-monitoreo-silla { background-color: #f0fdf4; color: #166534; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid #22c55e; border-right: 1px solid #bbf7d0; border-top: 1px solid #bbf7d0; border-bottom: 1px solid #bbf7d0; }
    .card-monitoreo-espera { background-color: #f0f9ff; color: #0369a1; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid #0284c7; border-right: 1px solid #bae6fd; border-top: 1px solid #bae6fd; border-bottom: 1px solid #bae6fd; }
    .titulo-seccion { font-size: 20px; font-weight: bold; color: #1e3a8a; margin-top: 20px; margin-bottom: 10px; border-bottom: 2px solid #e2e8f0; padding-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Consola de Mando - Barbería Reynosa")
st.write("Monitoreo en tiempo real de operaciones e ingresos.")

# ================= SECCIÓN 1: MÉTRICAS FINANCIERAS =================
df_terminados = df[df['Estado'] == 'Terminado']
total_generado = df_terminados['Total'].sum()
efectivo = df_terminados[df_terminados['Metodo_Pago'] == 'Efectivo']['Total'].sum()
tarjeta_trans = df_terminados[df_terminados['Metodo_Pago'].isin(['Tarjeta', 'Transferencia'])]['Total'].sum()

col_c1, col_c2, col_c3 = st.columns(3)
col_c1.metric("💰 Total Caja Hoy", f"${total_generado:,.2f}")
col_c2.metric("💵 En Efectivo", f"${efectivo:,.2f}")
col_c3.metric("💳 Tarjeta / Trans", f"${tarjeta_trans:,.2f}")

# ================= SECCIÓN 2: MONITOREO EN VIVO DE LA FILA =================
st.markdown("<div class='titulo-seccion'>👀 Estado Actual de la Sucursal</div>", unsafe_allow_html=True)

if len(df_activos) == 0:
    st.info("No hay ningún cliente en la sucursal en este momento (Fila vacía y sillas vacías).")
else:
    for idx, row in df_activos.iterrows():
        if row['Estado'] == 'Atendiendo':
            st.markdown(f"<div class='card-monitoreo-silla'>🟢 <b>EN SILLA:</b> {row['Cliente']} | 💈 Atendido por: <b>{row['Barbero']}</b> (Tel: {row['Telefono']})</div>", unsafe_allow_html=True)
        elif row['Estado'] == 'En espera':
            st.markdown(f"<div class='card-monitoreo-espera'>🔵 <b>EN ESPERA:</b> {row['Cliente']} | En fila general esperando barbero (Tel: {row['Telefono']})</div>", unsafe_allow_html=True)

# ================= SECCIÓN 3: HERRAMIENTAS DE DUEÑO (PROTEGIDAS) =================
st.markdown("<div class='titulo-seccion'>🔒 Panel de Control Administrativo</div>", unsafe_allow_html=True)

password = st.text_input("Introduce tu PIN de Dueño para gestionar el negocio:", type="password")

if password == PIN_ADMIN:
    st.success("Acceso Autorizado")
    
    # 1. Productividad por Barbero
    st.subheader("📊 Productividad y Comisiones (50%)")
    if len(df_terminados) > 0:
        resumen_barberos = df_terminados.groupby('Barbero').agg(
            Cortes_Hechos=('ID', 'count'),
            Dinero_Generado=('Total', 'sum')
        ).reset_index()
        
        resumen_barberos['Comisión Barbero'] = resumen_barberos['Dinero_Generado'] * 0.50
        resumen_barberos['Neto Barbería'] = resumen_barberos['Dinero_Generado'] * 0.50
        st.dataframe(resumen_barberos, use_container_width=True)
    else:
        st.info("Aún no se han cobrado servicios el día de hoy.")
        
    st.divider()
    
    # 2. Registrar y Eliminar Barberos
    st.subheader("👥 Gestión de Barberos (Usuarios)")
    col_b1, col_b2 = st.columns(2)
    
    with col_b1:
        st.markdown("**Alta de Personal:**")
        with st.form("form_nuevo_barbero", clear_on_submit=True):
            nuevo_b_nombre = st.text_input("Nombre del nuevo Barbero:")
            btn_add_b = st.form_submit_button("Registrar Usuario")
            if btn_add_b and nuevo_b_nombre:
                if nuevo_b_nombre not in lista_barberos:
                    nueva_b_row = pd.DataFrame({'Barbero': [nuevo_b_nombre]})
                    df_barberos_db = pd.concat([df_barberos_db, nueva_b_row], ignore_index=True)
                    df_barberos_db.to_excel(BARBEROS_FILE, index=False)
                    st.success(f"¡{nuevo_b_nombre} agregado correctamente!")
                    st.rerun()
                else:
                    st.warning("Ese barbero ya existe.")
                
    with col_b2:
        st.markdown("**Baja de Personal / Eliminar:**")
        # Selector para elegir a quién queremos borrar de la base de datos
        barbero_a_eliminar = st.selectbox("Selecciona quién ya no trabaja aquí:", ["Seleccionar..."] + lista_barberos)
        
        if barbero_a_eliminar != "Seleccionar...":
            if st.button(f"❌ Eliminar definitivamente a {barbero_a_eliminar}"):
                # Filtrar el DataFrame dejando fuera al barbero seleccionado
                df_barberos_db = df_barberos_db[df_barberos_db['Barbero'] != barbero_a_eliminar]
                df_barberos_db.to_excel(BARBEROS_FILE, index=False)
                st.success(f"Se ha dado de baja a {barbero_a_eliminar} de la lista.")
                st.rerun()

    st.divider()
    
    # 3. Cierre de caja
    st.subheader("🧹 Cierre de Jornada")
    if st.button("Reiniciar Caja (Iniciar Nuevo Día)"):
        df_vacio = pd.DataFrame(columns=['ID', 'Cliente', 'Telefono', 'Barbero', 'Estado', 'Servicio', 'Total', 'Metodo_Pago'])
        df_vacio.to_excel(EXCEL_FILE, index=False)
        st.warning("Se ha limpiado la lista del día de hoy. ¡Listo para mañana!")
        st.rerun()

elif password != "":
    st.error("PIN Incorrecto")