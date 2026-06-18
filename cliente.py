import streamlit as st
import pandas as pd
from datetime import datetime
import os  # <-- Asegúrate de que esta línea esté para revisar los archivos

# Nombre del archivo de base de datos
EXCEL_FILE = "registro_barberia.xlsx"

# VERIFICACIÓN DE EMERGENCIA: Si el archivo no existe en internet, lo creamos limpio
if not os.path.exists(EXCEL_FILE):
    df_inicial = pd.DataFrame(columns=["Fecha", "Cliente", "Telefono", "Barbero", "Estado", "Precio", "Metodo_Pago"])
    df_inicial.to_excel(EXCEL_FILE, index=False)

df = pd.read_excel(EXCEL_FILE)

# Lógica de tiempos: solo cuenta la gente que está esperando físicamente
personas_en_espera = len(df[df['Estado'] == 'En espera'])
tiempo_estimado_total = personas_en_espera * 25

# Diseño visual limpio y de alto contraste
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 50px; background-color: #1e3a8a; color: white; }
    .msg-exito { background-color: #f0fdf4; color: #14532d; padding: 20px; border-radius: 10px; border: 1px solid #22c55e; margin-bottom: 20px; text-align: center; }
    .tiempo-contenedor { text-align: center; padding: 20px; background-color: #f8fafc; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e2e8f0; }
    .tiempo-numero { font-size: 56px; font-weight: bold; color: #1e3a8a; line-height: 1; }
    .tiempo-label { font-size: 14px; color: #64748b; text-transform: uppercase; font-weight: bold; letter-spacing: 1px; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

st.title("💈 Barbería Reynosa")
st.write("Registra tu llegada desde aquí para asegurar tu lugar en la fila.")

# Gran reloj estilo Great Clips
st.markdown(f"""
    <div class="tiempo-contenedor">
        <div class="tiempo-label">Tiempo de Espera Estimado Actual</div>
        <div class="tiempo-numero">{tiempo_estimado_total} min</div>
    </div>
""", unsafe_allow_html=True)

st.subheader("Formulario de Registro")

with st.form("form_cliente", clear_on_submit=True):
    nombre = st.text_input("Nombre completo *", placeholder="Ej. Tadeo Morales")
    telefono = st.text_input("Número de celular / WhatsApp *", placeholder="Ej. 8991234567")
    enviar_registro = st.form_submit_button("Anotarme en la Fila (Check In)")
    
    if enviar_registro:
        if not nombre or not telefono:
            st.error("Por favor ingresa tu nombre y teléfono para poder registrarte.")
        else:
            df = pd.read_excel(EXCEL_FILE)
            nuevo_id = df['ID'].max() + 1 if len(df) > 0 else 1
            
            nueva_fila = {
                'ID': nuevo_id, 'Cliente': nombre, 'Telefono': telefono, 'Barbero': 'Cualquiera',
                'Estado': "En espera", 'Servicio': '', 'Total': 0, 'Metodo_Pago': ''
            }
            df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
            df.to_excel(EXCEL_FILE, index=False)
            
            st.session_state['ultimo_registro'] = {
                'nombre': nombre, 'telefono': telefono, 'tiempo': tiempo_estimado_total
            }
            st.rerun()

if 'ultimo_registro' in st.session_state:
    reg = st.session_state['ultimo_registro']
    st.markdown(f"""
        <div class='msg-exito'>
            <h3>✅ ¡Registro Exitoso, {reg['nombre']}!</h3>
            <p>Ya estás en la lista de espera oficial.</p>
            <p>Tu tiempo estimado es de: <b>{reg['tiempo']} minutos</b>.</p>
        </div>
    """, unsafe_allow_html=True)
    
    texto_whatsapp = f"Hola {reg['nombre']}, tu registro en Barbería Reynosa quedó confirmado. Tiempo estimado: {reg['tiempo']} min. ¡Te esperamos!"
    st.link_button("📲 Recibir mi confirmación por WhatsApp", f"https://wa.me/{reg['telefono']}?text={urllib.parse.quote(texto_whatsapp)}")