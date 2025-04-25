import streamlit as st
import pandas as pd
from io import BytesIO

# Funções de categorização

def categorize_ac(val):
    try:
        if isinstance(val, str):
            v = val.strip().lower()
            if v.startswith('<'):
                return 'normal'
            if v.startswith('>') or 'over' in v:
                return 'macro'
            num = float(v)
        else:
            num = float(val)
    except:
        return None
    if num < 30:
        return 'normal'
    if num <= 300:
        return 'micro'
    return 'macro'


def categorize_pc(val):
    try:
        if isinstance(val, str):
            v = val.strip().lower()
            if v.startswith('<'):
                return 'normal'
            if v.startswith('>') or 'over' in v:
                return 'significativa'
            num = float(v)
        else:
            num = float(val)
    except:
        return None
    return 'normal' if num < 150 else 'significativa'

# Mapeamentos de patologia
m_ac = {
    'normal': 'sem nefropatia',
    'micro': 'nefropatia incipiente (diabética)',
    'macro': 'nefropatia avançada'
}
m_pc = {
    'normal': 'função renal preservada',
    'significativa': 'alteração de função renal'
}

st.title('Análise comparativa de A/C e P/C por equipamento')
uploaded = st.file_uploader('Carregue o arquivo Excel', type=['xlsx'])

if uploaded:
    # Leitura
    df = pd.read_excel(uploaded, header=3, engine='openpyxl')
    df.columns = df.columns.str.strip()

    # Renomear colunas para todos os equipamentos
    df = df.rename(columns={
        'Albumina Arkray (mg/L)':    'alb_arkray',
        'Creatinina Arkray (mg/dL)': 'cre_arkray',
        'P/C Arkray (mg/gCr)':       'pc_arkray',
        'A/C Arkray (mg/gCr)':       'ac_arkray',
        'Albumina Sysmex (mg/L)':    'alb_sysmex',
        'Creatinina Sysmex (mg/dL)': 'cre_sysmex',
        'P/C Sysmex (mg/gCr)':       'pc_sysmex',
        'A/C Sysmex (mg/gCr)':       'ac_sysmex',
        'Proteínas Cobas (mg/dL)':   'prot_cobas',  # exemplo: renomeie conforme excel
        'P/C Cobas (mg/gCr)':        'pc_cobas',
        'A/C Cobas (mg/gCr)':        'ac_cobas'
    })

    # Categorização
    for dev in ['arkray','sysmex','cobas']:
        df[f'status_ac_{dev}'] = df[f'ac_{dev}'].apply(categorize_ac)
        df[f'status_pc_{dev}'] = df[f'pc_{dev}'].apply(categorize_pc)

    # Exibir tabela
    st.subheader('Dados Processados')
    st.dataframe(df)

    # Gráfico comparativo A/C
    st.subheader('Comparativo de categorias A/C')
    ac_counts = pd.concat([
        df['status_ac_arkray'].value_counts(),
        df['status_ac_sysmex'].value_counts(),
        df['status_ac_cobas'].value_counts()
    ], axis=1, keys=['Arkray','Sysmex','Cobas']).fillna(0)
    st.bar_chart(ac_counts)

    # Gráfico comparativo P/C
    st.subheader('Comparativo de categorias P/C')
    pc_counts = pd.concat([
        df['status_pc_arkray'].value_counts(),
        df['status_pc_sysmex'].value_counts(),
        df['status_pc_cobas'].value_counts()
    ], axis=1, keys=['Arkray','Sysmex','Cobas']).fillna(0)
    st.bar_chart(pc_counts)

    # Botão de download
    towrite = BytesIO()
    df.to_excel(towrite, index=False, engine='openpyxl')
    towrite.seek(0)
    st.download_button('📥 Download do Excel Processado', data=towrite,
                    file_name='ESTUDO_URINAS_PROCESSADO.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    st.success('Processamento concluído!')
else:
    st.info('Por favor, carregue um ficheiro de Excel para iniciar.')
