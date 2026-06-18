import streamlit as st
import pandas as pd
import os

# Configuración de pantalla optimizada para tablet o cel en sucursal
st.set_page_config(page_title="Panel de Barberos", page_icon="✂️", layout="centered")

EXCEL_FILE = 'registro_barberia.xlsx'
BARBEROS_FILE = 'barberos.xlsx'

# Precios de los servicios
SERVICIOS = {
    "Corte Normal ($200)": 200,
    "Solo Barba ($100)": 100,
    "Combo Corte + Barba ($280)": 280,
    "Tinte / Otro ($150)": 150
}

# Verificar que existan las bases de datos
if not os.path.exists(EXCEL_FILE) or not os.path.exists(BARBEROS_FILE):
    st.error("Falta algún archivo de base de datos. Asegúrate de correr primero el registro.")
    st.stop()

df = pd.read_excel(EXCEL_FILE)
df_barberos_db = pd.read_excel(BARBEROS_FILE)
lista_barberos = df_barberos_db['Barbero'].tolist()

# Filtrar solo los que no han terminado
df_visual = df[df['Estado'] != 'Terminado'].copy()
if len(df_visual) > 0:
    df_visual['Prioridad'] = df_visual['Estado'].map({'Atendiendo': 1, 'En espera': 2})
    df_visual = df_visual.sort_values(by=['Prioridad', 'ID'])

# Calcular el lugar en la fila
df_espera = df_visual[df_visual['Estado'] == 'En espera'].reset_index()
df_espera['Lugar'] = df_espera.index + 1
lugares_dict = dict(zip(df_espera['ID'], df_espera['Lugar']))
df_visual['Lugar'] = df_visual['ID'].map(lugares_dict).fillna(0).astype(int)

# Estilos visuales de alto contraste
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .card-silla { background-color: #f0fdf4; color: #166534; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #22c55e; border-right: 1px solid #bbf7d0; border-top: 1px solid #bbf7d0; border-bottom: 1px solid #bbf7d0; }
    .card-espera { background-color: #f0f9ff; color: #0369a1; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #0284c7; border-right: 1px solid #bae6fd; border-top: 1px solid #bae6fd; border-bottom: 1px solid #bae6fd; }
    </style>
""", unsafe_allow_html=True)

st.title("✂️ Panel de Control - Barberos")

# Identificación del barbero
barbero_activo = st.selectbox("Selecciona tu Usuario para trabajar:", ["Seleccionar..."] + lista_barberos)

if barbero_activo != "Seleccionar...":
    st.success(f"Sesión activa: **{barbero_activo}**")
    
    # Candado de seguridad: ¿Tiene a alguien en silla?
    tiene_cliente_en_silla = len(df_visual[(df_visual['Estado'] == 'Atendiendo') & (df_visual['Barbero'] == barbero_activo)]) > 0
    
    if tiene_cliente_en_silla:
        st.warning("⚠️ Tienes un cliente en la silla. Cóbbralo al terminar para poder atender al siguiente.")

    # Filtrar fila segura
    df_filtrado = df_visual[
        (df_visual['Estado'] == 'En espera') | 
        ((df_visual['Estado'] == 'Atendiendo') & (df_visual['Barbero'] == barbero_activo))
    ]
    
    if len(df_filtrado) == 0:
        st.info("No hay clientes en la lista por ahora.")
    
    for idx, row in df_filtrado.iterrows():
        orig_idx = df[df['ID'] == row['ID']].index[0]
        
        # Modo: Atendiendo (Solo el mío)
        if row['Estado'] == 'Atendiendo' and row['Barbero'] == barbero_activo:
            with st.container():
                st.markdown(f"<div class='card-silla'>💇‍♂️ En Silla: <b>{row['Cliente']}</b></div>", unsafe_allow_html=True)
                if st.button(f"💵 Terminar y Cobrar a {row['Cliente']}", key=f"btn_term_{row['ID']}"):
                    st.session_state[f"cobro_{row['ID']}"] = True
                    
            if st.session_state.get(f"cobro_{row['ID']}", False):
                with st.form(key=f"form_cobro_{row['ID']}"):
                    servicio_hecho = st.selectbox("Servicio realizado:", list(SERVICIOS.keys()))
                    pago_metodo = st.selectbox("Método de pago:", ["Efectivo", "Tarjeta", "Transferencia"])
                    confirmar_pago = st.form_submit_button("Finalizar Orden")
                    
                    if confirmar_pago:
                        df = pd.read_excel(EXCEL_FILE) # Re-leer por seguridad
                        df.at[orig_idx, 'Estado'] = 'Terminado'
                        df.at[orig_idx, 'Barbero'] = barbero_activo
                        df.at[orig_idx, 'Servicio'] = servicio_hecho
                        df.at[orig_idx, 'Total'] = SERVICIOS[servicio_hecho]
                        df.at[orig_idx, 'Metodo_Pago'] = pago_metodo
                        df.to_excel(EXCEL_FILE, index=False)
                        st.session_state[f"cobro_{row['ID']}"] = False
                        st.success("¡Corte guardado!")
                        st.rerun()
                        
        # Modo: En espera (Fila general)
        elif row['Estado'] == 'En espera':
            with st.container():
                st.markdown(f"<div class='card-espera'>🔵 Fila #{row['Lugar']}: <b>{row['Cliente']}</b></div>", unsafe_allow_html=True)
                
                # Bloquear botón si ya está ocupado
                if not tiene_cliente_en_silla:
                    if st.button(f"▶️ Sentar en mi Silla", key=f"btn_at_{row['ID']}"):
                        df = pd.read_excel(EXCEL_FILE)
                        df.at[orig_idx, 'Estado'] = 'Atendiendo'
                        df.at[orig_idx, 'Barbero'] = barbero_activo
                        df.to_excel(EXCEL_FILE, index=False)
                        st.rerun()