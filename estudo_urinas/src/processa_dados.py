import streamlit as st
import pandas as pd
from io import BytesIO

# Funções de categorização (faixas de cada equipamento)

def categorize_ac(val):
    try:
        if isinstance(val, str):
            v = val.strip().lower()
            if v.startswith('<'):
                return 'normal (<30)'
            if v.startswith('>') or 'over' in v:
                return 'macro (>300)'
            num = float(v)
        else:
            num = float(val)
    except:
        return None
    if num < 30:
        return 'normal (<30)'
    if num <= 300:
        return 'micro (30–300)'
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

# Categorização segundo limites de referência para ambas as razões (0–30, 30–300, >300)
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

st.title('Comparativo Clínico de A/C e P/C')
uploaded = st.file_uploader('Carregue o arquivo Excel', type=['xlsx'])

if uploaded:
    # Leitura básica
    df = pd.read_excel(uploaded, header=3, engine='openpyxl')
    df.columns = df.columns.str.strip()

    # Renomear colunas
    rename_map = {
        'Albumina Arkray (mg/L)': 'alb_arkray', 'Creatinina Arkray (mg/dL)': 'cre_arkray',
        'P/C Arkray (mg/gCr)': 'pc_arkray', 'A/C Arkray (mg/gCr)': 'ac_arkray',
        'Albumina Sysmex (mg/L)': 'alb_sysmex', 'Creatinina Sysmex (mg/dL)': 'cre_sysmex',
        'P/C Sysmex (mg/gCr)': 'pc_sysmex', 'A/C Sysmex (mg/gCr)': 'ac_sysmex',
        'Proteínas Cobas (mg/dL)': 'prot_cobas', 'P/C Cobas (mg/gCr)': 'pc_cobas',
        'A/C Cobas (mg/gCr)': 'ac_cobas'
    }
    df = df.rename(columns=rename_map)

    # Categorizações por equipamento
    for dev in ['arkray', 'sysmex', 'cobas']:
        df[f'status_ac_{dev}'] = df[f'ac_{dev}'].apply(categorize_ac)
        df[f'status_pc_{dev}'] = df[f'pc_{dev}'].apply(categorize_pc)
        # também segundo referência
        df[f'ref_ac_{dev}'] = df[f'ac_{dev}'].apply(categorize_ref)
        df[f'ref_pc_{dev}'] = df[f'pc_{dev}'].apply(categorize_ref)

    # Mostrar dados e categorias
    st.subheader('Amostra de Dados Processados')
    st.dataframe(df.head())

    # Gráfico comparativo A/C (Equipamento x Referência)
    st.subheader('A/C: Equipamento vs Limites de Referência')
    comp_ac = pd.concat([
        df['status_ac_arkray'].value_counts().rename('Arkray (EQP)'),
        df['ref_ac_arkray'].value_counts().rename('Arkray (REF)'),
        df['status_ac_sysmex'].value_counts().rename('Sysmex (EQP)'),
        df['ref_ac_sysmex'].value_counts().rename('Sysmex (REF)'),
        df['status_ac_cobas'].value_counts().rename('Cobas (EQP)'),
        df['ref_ac_cobas'].value_counts().rename('Cobas (REF)')
    ], axis=1).fillna(0)
    st.bar_chart(comp_ac)

    # Gráfico comparativo P/C (Equipamento x Referência)
    st.subheader('P/C: Equipamento vs Limites de Referência')
    comp_pc = pd.concat([
        df['status_pc_arkray'].value_counts().rename('Arkray (EQP)'),
        df['ref_pc_arkray'].value_counts().rename('Arkray (REF)'),
        df['status_pc_sysmex'].value_counts().rename('Sysmex (EQP)'),
        df['ref_pc_sysmex'].value_counts().rename('Sysmex (REF)'),
        df['status_pc_cobas'].value_counts().rename('Cobas (EQP)'),
        df['ref_pc_cobas'].value_counts().rename('Cobas (REF)')
    ], axis=1).fillna(0)
    st.bar_chart(comp_pc)

    # Download do Excel completo
    towrite = BytesIO(); df.to_excel(towrite, index=False, engine='openpyxl'); towrite.seek(0)
    st.download_button('📥 Download do Excel Completo', data=towrite,
                file_name='ESTUDO_URINAS_COMPARATIVO.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    st.success('Comparativo gerado com limites visíveis!')

else:
    st.info('Carregue o Excel para iniciar o comparativo.')
