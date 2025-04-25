import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO

# — Funções de categorização — #
def categorize_ac(valor):
    try:
        if isinstance(valor, str):
            v = valor.strip().lower()
            if v.startswith('<'):
                return 'normal (<30 mg/g)'
            if v.startswith('>') or 'over' in v:
                return 'albuminúria manifesta (>300 mg/g)'
            num = float(v)
        else:
            num = float(valor)
    except:
        return None
    if num < 30:
        return 'normal (<30 mg/g)'
    if num <= 300:
        return 'microalbuminúria (30–300 mg/g)'
    return 'albuminúria manifesta (>300 mg/g)'

def categorize_pc(valor):
    try:
        if isinstance(valor, str):
            v = valor.strip().lower()
            if v.startswith('<'):
                return 'normal (<150 mg/g)'
            if v.startswith('>') or 'over' in v:
                return 'proteinúria manifesta (>300 mg/g)'
            num = float(v)
        else:
            num = float(valor)
    except:
        return None
    if num < 150:
        return 'normal (<150 mg/g)'
    if num <= 300:
        return 'microproteinúria (150–300 mg/g)'
    return 'proteinúria manifesta (>300 mg/g)'

def categorize_ref(valor):
    try:
        v = str(valor).strip().lower()
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
        return 'microalbuminúria (30–300 mg/g)'
    return 'albuminúria manifesta (>300 mg/g)'

# — Título e uploader — #
st.title('Análise de Albumina/Creatinina e Proteína/Creatinina')
uploaded = st.file_uploader('Carregue o ficheiro (Excel ou CSV)', type=['xlsx','csv'])
if not uploaded:
    st.info('Por favor, carregue um ficheiro para iniciar o processamento.')
    st.stop()

# — Leitura e limpeza — #
if uploaded.name.lower().endswith('.csv'):
    df = pd.read_csv(uploaded)
else:
    df = pd.read_excel(uploaded, header=3, engine='openpyxl')

# Eliminar primeira coluna e colunas sem nome
if df.columns.size > 0:
    df = df.iloc[:, 1:]
df = df.loc[:, ~df.columns.str.startswith('Unnamed')]
df.columns = df.columns.str.strip()
df = df.loc[:, df.columns.astype(bool)]

# Renomear colunas chave
df = df.rename(columns={
    'Nº Tubo': 'Tubo',
    'Área': 'área',
    'A/C Arkray (mg/gCr)': 'ac_arkray',
    'P/C Arkray (mg/gCr)': 'pc_arkray',
    'A/C Sysmex (mg/gCr)': 'ac_sysmex',
    'P/C Sysmex (mg/gCr)': 'pc_sysmex',
    'A/C Cobas (mg/gCr)':  'ac_cobas',
    'P/C Cobas (mg/gCr)':  'pc_cobas'
})

# — Categorização por equipamento — #
for dev in ['arkray','sysmex','cobas']:
    if f'ac_{dev}' in df.columns:
        df[f'status_ac_{dev}'] = df[f'ac_{dev}'].apply(categorize_ac)
        df[f'ref_ac_{dev}']    = df[f'ac_{dev}'].apply(categorize_ref)
    if f'pc_{dev}' in df.columns:
        df[f'status_pc_{dev}'] = df[f'pc_{dev}'].apply(categorize_pc)
        df[f'ref_pc_{dev}']    = df[f'pc_{dev}'].apply(categorize_ref)

# — Exibir gráficos individuais (Status do equipamento) — #
st.header('Distribuição por equipamento (Status interno)')
for dev in ['arkray','sysmex','cobas']:
    nome = dev.capitalize()
    if f'status_ac_{dev}' in df.columns:
        st.subheader(f'{nome} – Albumina/Creatinina')
        st.bar_chart(df[f'status_ac_{dev}'].value_counts())
    if f'status_pc_{dev}' in df.columns:
        st.subheader(f'{nome} – Proteína/Creatinina')
        st.bar_chart(df[f'status_pc_{dev}'].value_counts())

# — Gráfico de valores por Área para Albumina/Creatinina — #
st.header('Distribuição de A/C por Área')

# Definimos as três categorias
cats_ac = [
    ('Valores abaixo do normal (<30 mg/g)', 'normal (<30 mg/g)'),
    ('Microalbuminúria (30–300 mg/g)',   'microalbuminúria (30–300 mg/g)'),
    ('Albuminúria manifesta (>300 mg/g)','albuminúria manifesta (>300 mg/g)')
]

# — Valores abaixo do normal (<30) — #
st.header('A/C abaixo do normal por área')
area_ac_abaixo = pd.DataFrame({
    dev.capitalize(): df[df[f'status_ac_{dev}']=='normal (<30 mg/g)']
                        .groupby('área').size()
    for dev in ['arkray','sysmex','cobas']
}).fillna(0)
st.area_chart(area_ac_abaixo)

# — Valores microalbuminúria (30–300) — #
st.header('A/C microalbuminúria por área')
area_ac_micro = pd.DataFrame({
    dev.capitalize(): df[df[f'status_ac_{dev}']=='microalbuminúria (30–300 mg/g)']
                        .groupby('área').size()
    for dev in ['arkray','sysmex','cobas']
}).fillna(0)
st.area_chart(area_ac_micro)

# — Albuminúria manifesta (>300) — #
st.header('A/C acima do normal por área')
area_ac_alta = pd.DataFrame({
    dev.capitalize(): df[df[f'status_ac_{dev}']=='albuminúria manifesta (>300 mg/g)']
                        .groupby('área').size()
    for dev in ['arkray','sysmex','cobas']
}).fillna(0)
st.area_chart(area_ac_alta)

# — Gráfico de valores por Área para Proteína/Creatinina — #
st.header('Distribuição de P/C por Área')

# As categorias agora com limites de P/C
cats_pc = [
    ('Valores abaixo do normal (<150 mg/g)', 'normal (<150 mg/g)'),
    ('Microproteinúria (150–300 mg/g)',      'microproteinúria (150–300 mg/g)'),
    ('Proteinúria manifesta (>300 mg/g)',    'proteinúria manifesta (>300 mg/g)')
]

# — P/C abaixo do normal (<150) — #
st.header('P/C abaixo do normal por área')
area_pc_abaixo = pd.DataFrame({
    dev.capitalize(): df[df[f'status_pc_{dev}']=='normal (<150 mg/g)']
                        .groupby('área').size()
    for dev in ['arkray','sysmex','cobas']
}).fillna(0)
st.area_chart(area_pc_abaixo)

# — P/C microproteinúria (150–300) — #
st.header('P/C microproteinúria por área')
area_pc_micro = pd.DataFrame({
    dev.capitalize(): df[df[f'status_pc_{dev}']=='microproteinúria (150–300 mg/g)']
                        .groupby('área').size()
    for dev in ['arkray','sysmex','cobas']
}).fillna(0)
st.area_chart(area_pc_micro)

# — P/C proteinúria manifesta (>300) — #
st.header('P/C acima do normal por área')
area_pc_alta = pd.DataFrame({
    dev.capitalize(): df[df[f'status_pc_{dev}']=='proteinúria manifesta (>300 mg/g)']
                        .groupby('área').size()
    for dev in ['arkray','sysmex','cobas']
}).fillna(0)
st.area_chart(area_pc_alta)


# — Amostras discordantes — #
st.header('Amostras com categorias totalmente diferentes')
for tipo,label in [('ac','Albumina/Creatinina'), ('pc','Proteína/Creatinina')]:
    st.subheader(label)
    mask = df.apply(lambda r: len({
        r.get(f'status_{tipo}_arkray'),
        r.get(f'status_{tipo}_sysmex'),
        r.get(f'status_{tipo}_cobas')
    })==3, axis=1)
    cols = ['Tubo'] + [f'status_{tipo}_{dev}' for dev in ['arkray','sysmex','cobas']]
    df_diff = df.loc[mask, cols]
    st.write(df_diff if not df_diff.empty else 'Nenhuma amostra com três categorias diferentes.')

# — Transferir dados processados — #
towrite = BytesIO()
df.to_excel(towrite, index=False, engine='openpyxl')
towrite.seek(0)
st.download_button(
    '📥 Transferir Excel Processado',
    data=towrite,
    file_name='dados_processados.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)

st.success('Os dados foram processados com sucesso!')  
