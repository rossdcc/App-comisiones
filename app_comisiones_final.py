
import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Calculadora de Comisiones", layout="centered")
st.title("💼 Comisiones con archivo de ventas y archivo de vendedores")

# 📤 Cargar archivos
ventas_file = st.file_uploader("📄 Sube el archivo de VENTAS (productos)", type=["xlsx"], key="ventas")
vendedores_file = st.file_uploader("📄 Sube el archivo de CLIENTES/VENDEDORES", type=["xlsx"], key="vendedores")

if ventas_file and vendedores_file:
    df = pd.read_excel(ventas_file)
    vendedores = pd.read_excel(vendedores_file)

    # Asegurar nombres consistentes
    # Limpiar texto en columnas relevantes
    df['Nombre'] = df['Nombre'].astype(str).str.strip().str.upper()
    df['Descrip'] = df['Descrip'].astype(str).str.strip()
    df['Clave'] = df['Clave'].astype(str).str.strip()
    
    # Reordenar columnas (opcional)
    df = df[sorted(df.columns)]

    # Ahora sí: quitar duplicados
    df = df.drop_duplicates()

    # Limpiar texto en columnas relevantes
    vendedores['Nombre'] = vendedores['Nombre'].astype(str).str.strip().str.upper()
    vendedores['Vendedor'] = vendedores['Vendedor'].astype(str).str.strip().str.upper()

    # Reordenar columnas (opcional)
    vendedores = vendedores[sorted(vendedores.columns)]

    # Ahora sí: quitar duplicados
    vendedores = vendedores.drop_duplicates()

    # Crear un diccionario {cliente: vendedor}
    diccionario_vendedores = dict(zip(vendedores['Nombre'], vendedores['Vendedor']))

    # Crear nueva columna "Vendedor" sin usar merge
    df['Vendedor'] = df['Nombre'].map(diccionario_vendedores)

    # Normalizar descripción
    df['Descrip'] = df['Descrip'].str.lower()

    # Filtros por material
    filtro_oro = df['Descrip'].str.contains(r'\b\d{2}k\b', na=False) & ~df['Descrip'].str.contains(r'\bcha\b|\bchapa\b|\bace\b|\bacero\b', na=False)
    filtro_plata = (
    df['Clave'].str.contains("TP", na=False) |
    (df['Descrip'].str.contains(r'.925|\\bplata\\b|\\barras', na=False) &
     ~df['Descrip'].str.contains(r'\\bcha\\b|\\bchapa\\b|\\bace\\b|\\bacero\\b|\\breloj\\b', na=False))
    )
    filtro_acero = df['Descrip'].str.contains(r'\bace\b|\bacero\b', na=False) & ~filtro_oro & ~filtro_plata
    filtro_chapa = df['Descrip'].str.contains(r'\bcha\b|\bchapa\b', na=False) & ~filtro_acero
    filtro_reloj = df['Descrip'].str.contains(r'\breloj\b', na=False)
    filtro_fantasia = df['Clave'].str.contains('JF', na=False)

    # Separar por tipo de material
    df_oro = df[filtro_oro]
    df_plata = df[filtro_plata & ~filtro_oro]
    df_acero = df[filtro_acero & ~filtro_oro & ~filtro_plata]
    df_chapa = df[filtro_chapa & ~filtro_oro & ~filtro_plata & ~filtro_acero]
    df_reloj = df[filtro_reloj & ~filtro_oro & ~filtro_plata & ~filtro_acero & ~filtro_chapa]
    df_fantasia = df[filtro_fantasia & ~filtro_oro & ~filtro_plata & ~filtro_acero & ~filtro_chapa & ~filtro_reloj]

    # Otros (no clasificados)
    df_clasificados = pd.concat([df_oro, df_reloj, df_plata, df_acero, df_chapa, df_fantasia])
    df_otros = df[~df.index.isin(df_clasificados.index)]

    # Agrupar Oro + Reloj
    df_oro_reloj = pd.concat([df_oro, df_reloj])
    resumen_oro_reloj = df_oro_reloj.groupby('Vendedor')['Importe'].sum().reset_index()
    resumen_oro_reloj = resumen_oro_reloj.sort_values(by='Importe', ascending=False)
    resumen_oro_reloj['Comision'] = [
        row['Importe'] * 0.009 if i == 0 else row['Importe'] * 0.008
        for i, row in resumen_oro_reloj.iterrows()
    ]

    # Agrupar Plata + Chapa + Acero + Fantasía
    df_otros_materiales = pd.concat([df_plata, df_chapa, df_acero, df_fantasia])
    resumen_otros = df_otros_materiales.groupby('Vendedor')['Importe'].sum().reset_index()
    resumen_otros = resumen_otros.sort_values(by='Importe', ascending=False)

    # Mostrar tabla
    st.subheader("📊 Comisiones por Vendedor (Oro + Reloj)")
    st.dataframe(resumen_oro_reloj)

    st.subheader("📋 Totales por Vendedor (Plata, Chapa, Acero, Fantasía)")
    st.dataframe(resumen_otros)

    # Descargar archivo final
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_oro.to_excel(writer, sheet_name="Oro", index=False)
        df_reloj.to_excel(writer, sheet_name="Reloj", index=False)
        df_plata.to_excel(writer, sheet_name="Plata", index=False)
        df_acero.to_excel(writer, sheet_name="Acero", index=False)
        df_chapa.to_excel(writer, sheet_name="Chapa", index=False)
        df_fantasia.to_excel(writer, sheet_name="Fantasia", index=False)
        df_otros.to_excel(writer, sheet_name="Otros", index=False)
        resumen_oro_reloj.to_excel(writer, sheet_name="Comisiones_OroReloj", index=False)
        resumen_otros.to_excel(writer, sheet_name="Totales_Otros_Materiales", index=False)

    st.download_button("📥 Descargar archivo con comisiones",
                       data=output.getvalue(),
                       file_name="comisiones_resultado.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
