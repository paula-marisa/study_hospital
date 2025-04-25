import streamlit as st
import pandas as pd
from io import BytesIO

# Categorization functions

def categorize_ac(val):
    try:
        if isinstance(val, str):
            v = val.strip().lower()
            if v.startswith('<'):
                return 'normal (<30)'
            if v.startswith('>') or 'over' in v:
                return 'albuminúria franca ou proteinúria (>300)'
            num = float(v)
        else:
            num = float(val)
    except:
        return None
    if num < 30:
        return 'normal (<30)'
    if num <= 300:
        return 'microalbuminúria (30–300)'
    return 'macro (>300)'


def categorize_pc(val):
    try:
        if isinstance(val, str):
            v = val.strip().lower()
            if v.startswith('<'):
                return 'normal (<150)'
            if v.startswith('>') or 'over' in v:
                return 'significativa (≥150)'
            num = float(v)
        else:
            num = float(val)
    except:
        return None
    return 'normal (<150)' if num < 150 else 'significativa (≥150)'

# Reference categorization for both ratios

def categorize_ref(val):
    try:
        v = str(val).strip().lower()
        if v.startswith('<'):
            num = float(v.lstrip('<'))
        elif v.startswith('>') or 'over' in v:
            num = float(v.lstrip('>').replace('over','301'))
        else:
            num = float(v)
    except:
        return None
    if num < 30:
        return 'normal (<30)'
    if num <= 300:
        return 'micro (30–300)'
    return 'macro (>300)'

st.title('Análise de A/C e P/C por Equipamento e Área')

uploaded = st.file_uploader('Carregue o arquivo Excel', type=['xlsx','csv'])
if not uploaded:
    st.info('Por favor, carregue um arquivo CSV ou Excel para iniciar.')
    st.stop()

# Read file
if uploaded.name.lower().endswith('.csv'):
    df = pd.read_csv(uploaded)
else:
    df = pd.read_excel(uploaded, header=3, engine='openpyxl')

# Clean columns
df.columns = df.columns.str.strip()

# Rename key columns
rename_map = {
    'Nº Tubo': 'tube', 'Área': 'area',
    'A/C Arkray (mg/gCr)': 'ac_arkray', 'P/C Arkray (mg/gCr)': 'pc_arkray',
    'A/C Sysmex (mg/gCr)': 'ac_sysmex', 'P/C Sysmex (mg/gCr)': 'pc_sysmex',
    'A/C Cobas (mg/gCr)': 'ac_cobas', 'P/C Cobas (mg/gCr)': 'pc_cobas'
}
df = df.rename(columns=rename_map)

# Categorize per equipment
for dev in ['arkray','sysmex','cobas']:
    df[f'status_ac_{dev}'] = df[f'ac_{dev}'].apply(categorize_ac)
    df[f'status_pc_{dev}'] = df[f'pc_{dev}'].apply(categorize_pc)

# Show individual equipment charts
st.header('Distribuição por Equipamento')
for dev in ['arkray','sysmex','cobas']:
    st.subheader(f'Arkray {dev.capitalize()} - A/C')
    st.bar_chart(df[f'status_ac_{dev}'].value_counts())
    st.subheader(f'P/C {dev.capitalize()}')
    st.bar_chart(df[f'status_pc_{dev}'].value_counts())

# Compare normal A/C by area for each equipment
st.header('Valores Normais de A/C por Área')
area_ac = pd.DataFrame({
    dev: df[df[f'status_ac_{dev}']=='normal (<30)'].groupby('area').size()
    for dev in ['arkray','sysmex','cobas']
}).fillna(0)
st.area_chart(area_ac)

# Identify samples with completely different A/C categories across 3 equipment
st.header('Amostras com A/C Discordante entre Equipamentos')
mask_ac3 = df.apply(lambda r: len({r['status_ac_arkray'],r['status_ac_sysmex'],r['status_ac_cobas']})==3, axis=1)
df_ac3 = df.loc[mask_ac3, ['tube','status_ac_arkray','status_ac_sysmex','status_ac_cobas']]
st.write(df_ac3 if not df_ac3.empty else 'Nenhuma amostra com três categorias totalmente diferentes.')

# Identify samples with completely different P/C categories across 3 equipment
st.header('Amostras com P/C Discordante entre Equipamentos')
mask_pc3 = df.apply(lambda r: len({r['status_pc_arkray'],r['status_pc_sysmex'],r['status_pc_cobas']})==3, axis=1)
df_pc3 = df.loc[mask_pc3, ['tube','status_pc_arkray','status_pc_sysmex','status_pc_cobas']]
st.write(df_pc3 if not df_pc3.empty else 'Nenhuma amostra com três categorias totalmente diferentes.')

# Download processed
st.subheader('Baixar Dados Processados')
btn = st.download_button('📥 Baixar Excel Processado', data=BytesIO(df.to_excel(index=False, engine='openpyxl', excel_writer=BytesIO())), file_name='processed.xlsx')
