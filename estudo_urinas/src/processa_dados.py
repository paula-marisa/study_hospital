import streamlit as st
import pandas as pd
from io import BytesIO

# Funções de categorização
def categorize_ac(val):
    try:
        if isinstance(val, str):
            v = val.strip().lower()
            if v.startswith('<'):
                return 'normal (<30 mg/g)'
            if v.startswith('>') or 'over' in v:
                return 'albuminúria manifesta (>300 mg/g)'
            num = float(v)
        else:
            num = float(val)
    except:
        return None
    if num < 30:
        return 'normal (<30 mg/g)'
    if num <= 300:
        return 'microalbuminúria (30–300 mg/g)'
    return 'albuminúria manifesta (>300 mg/g)'


def categorize_pc(val):
    try:
        if isinstance(val, str):
            v = val.strip().lower()
            if v.startswith('<'):
                return 'normal (<150 mg/g)'
            if v.startswith('>') or 'over' in v:
                return 'proteinúria manifesta (>300 mg/g)'
            num = float(v)
        else:
            num = float(val)
    except:
        return None
    if num < 150:
        return 'normal (<150 mg/g)'
    if num <= 300:
        return 'microproteinúria (150–300 mg/g)'
    return 'proteinúria manifesta (>300 mg/g)'

# Categorização de referência (mesmos limites para ambas razões)

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
        return 'normal (<30 mg/g)'
    if num <= 300:
        return 'micro (30–300 mg/g)'
    return 'macro (>300 mg/g)'

st.title('Análise de Albumina/Creatinina e Proteína/Creatinina')

uploaded = st.file_uploader('Carregue o ficheiro (Excel ou CSV)', type=['xlsx','csv'])
if not uploaded:
    st.info('Por favor, carregue um ficheiro para iniciar o processamento.')
    st.stop()

# Leitura do ficheiro
if uploaded.name.lower().endswith('.csv'):
    df = pd.read_csv(uploaded)
else:
    df = pd.read_excel(uploaded, header=3, engine='openpyxl')

# Limpeza de colunas: eliminar primeira e sem nome
if df.columns.size > 0:
    df = df.iloc[:, 1:]
# remover colunas 'Unnamed'
df = df.loc[:, ~df.columns.str.startswith('Unnamed')]
# remover colunas sem nome
df.columns = df.columns.str.strip()
df = df.loc[:, df.columns.astype(bool)]

# Renomear colunas chave
df = df.rename(columns={
    'Nº Tubo': 'tubo',
    'Área': 'área',
    'A/C Arkray (mg/gCr)': 'ac_arkray',
    'P/C Arkray (mg/gCr)': 'pc_arkray',
    'A/C Sysmex (mg/gCr)': 'ac_sysmex',
    'P/C Sysmex (mg/gCr)': 'pc_sysmex',
    'A/C Cobas (mg/gCr)': 'ac_cobas',
    'P/C Cobas (mg/gCr)': 'pc_cobas'
})

# Categorização por equipamento
for dev in ['arkray','sysmex','cobas']:
    if f'ac_{dev}' in df:
        df[f'status_ac_{dev}'] = df[f'ac_{dev}'].apply(categorize_ac)
    if f'pc_{dev}' in df:
        df[f'status_pc_{dev}'] = df[f'pc_{dev}'].apply(categorize_pc)

# Exibir gráficos individuais
st.header('Distribuição por equipamento')
for dev in ['arkray','sysmex','cobas']:
    label_ac = 'Albumina/Creatinina'
    label_pc = 'Proteína/Creatinina'
    if f'status_ac_{dev}' in df:
        st.subheader(f'{dev.capitalize()} - {label_ac}')
        st.bar_chart(df[f'status_ac_{dev}'].value_counts())
    if f'status_pc_{dev}' in df:
        st.subheader(f'{dev.capitalize()} - {label_pc}')
        st.bar_chart(df[f'status_pc_{dev}'].value_counts())

# Gráfico de valores normais por área
st.header('Valores normais de Albumina/Creatinina por área')
area_ac = pd.DataFrame({
    dev.capitalize(): df[df[f'status_ac_{dev}']=='normal (<30 mg/g)'].groupby('área').size()
    for dev in ['arkray','sysmex','cobas']
}).fillna(0)
st.area_chart(area_ac)

# Amostras discordantes
st.header('Amostras com categorias totalmente diferentes')

st.subheader('Albumina/Creatinina')
mask_ac3 = df.apply(lambda r: len({r.get('status_ac_arkray'), r.get('status_ac_sysmex'), r.get('status_ac_cobas')})==3, axis=1)
df_ac3 = df.loc[mask_ac3, ['tubo','status_ac_arkray','status_ac_sysmex','status_ac_cobas']]
st.write(df_ac3 if not df_ac3.empty else 'Nenhuma amostra com três categorias diferentes.')

st.subheader('Proteína/Creatinina')
mask_pc3 = df.apply(lambda r: len({r.get('status_pc_arkray'), r.get('status_pc_sysmex'), r.get('status_pc_cobas')})==3, axis=1)
df_pc3 = df.loc[mask_pc3, ['tubo','status_pc_arkray','status_pc_sysmex','status_pc_cobas']]
st.write(df_pc3 if not df_pc3.empty else 'Nenhuma amostra com três categorias diferentes.')

# Transferir dados processados
towrite = BytesIO()
df.to_excel(towrite, index=False, engine='openpyxl')
towrite.seek(0)
st.download_button('📥 Transferir Excel Processado', data=towrite,
                file_name='dados_processados.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
