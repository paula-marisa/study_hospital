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

st.title('Análise comparativa e significado clinico de A/C e P/C das urinas nos equipamentos Arkray, Sysmex e Roche')
uploaded = st.file_uploader('Carregue o arquivo Excel', type=['xlsx'])

if uploaded:
    # Leitura e limpeza
    df = pd.read_excel(uploaded, header=3, engine='xlrd')
    df.columns = df.columns.str.strip()
    # Renomear colunas
    df = df.rename(columns={
        'Albumina Arkray (mg/L)':    'alb_arkray',
        'Creatinina Arkray (mg/dL)': 'cre_arkray',
        'P/C Arkray (mg/gCr)':       'pc_arkray',
        'A/C Arkray (mg/gCr)':       'ac_arkray'
    })
    # Categorização e patologias
    df['status_ac_arkray'] = df['ac_arkray'].apply(categorize_ac)
    df['status_pc_arkray'] = df['pc_arkray'].apply(categorize_pc)
    df['patologia_ac_arkray'] = df['status_ac_arkray'].map(m_ac)
    df['patologia_pc_arkray'] = df['status_pc_arkray'].map(m_pc)

    # Exibir tabela processada
    st.subheader('Dados Processados')
    st.dataframe(df)

    # Botão de download do Excel processado
    towrite = BytesIO()
    df.to_excel(towrite, index=False, engine='openpyxl')
    towrite.seek(0)
    st.download_button(
        label='📥 Baixar Excel Processado',
        data=towrite,
        file_name='ESTUDO_URINAS_PROCESSADO.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    # Gráficos de distribuição usando Streamlit nativo
    st.subheader('Distribuição de A/C Arkray')
    ac_counts = df['status_ac_arkray'].value_counts()
    st.bar_chart(ac_counts)

    st.subheader('Distribuição de P/C Arkray')
    pc_counts = df['status_pc_arkray'].value_counts()
    st.bar_chart(pc_counts)

    st.success('Processamento concluído!')
else:
    st.info('Por favor, carregue um arquivo Excel para iniciar o processamento.')
