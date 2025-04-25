import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO

# — Funções de Categorização — #
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

# — Título da App — #
st.title('Análise de Albumina/Creatinina e Proteína/Creatinina')

# — Carregamento do Ficheiro — #
uploaded = st.file_uploader('Carregue o ficheiro (Excel ou CSV)', type=['xlsx','csv'])
if not uploaded:
    st.info('Por favor, carregue um ficheiro para iniciar o processamento.')
    st.stop()

# — Leitura do Ficheiro — #
if uploaded.name.lower().endswith('.csv'):
    df = pd.read_csv(uploaded)
else:
    df = pd.read_excel(uploaded, header=3, engine='openpyxl')

# — Limpeza de Colunas — #
if df.columns.size > 0:
    df = df.iloc[:, 1:]  # elimina a primeira coluna
df = df.loc[:, ~df.columns.str.startswith('Unnamed')]  # remove Unnamed
df.columns = df.columns.str.strip()
df = df.loc[:, df.columns.astype(bool)]  # remove colunas sem nome

# — Renomear Colunas — #
df = df.rename(columns={
    'Nº Tubo':        'Tubo',
    'Área':           'área',
    'A/C Arkray (mg/gCr)': 'ac_arkray',
    'P/C Arkray (mg/gCr)': 'pc_arkray',
    'A/C Sysmex (mg/gCr)': 'ac_sysmex',
    'P/C Sysmex (mg/gCr)': 'pc_sysmex',
    'A/C Cobas (mg/gCr)':  'ac_cobas',
    'P/C Cobas (mg/gCr)':  'pc_cobas'
})

# — Categorização por Equipamento — #
for dev in ['arkray','sysmex','cobas']:
    if f'ac_{dev}' in df.columns:
        df[f'status_ac_{dev}'] = df[f'ac_{dev}'].apply(categorize_ac)
    if f'pc_{dev}' in df.columns:
        df[f'status_pc_{dev}'] = df[f'pc_{dev}'].apply(categorize_pc)

# — Gráficos Originais (Status do Equipamento) — #
st.header('Distribuição por Equipamento (Status do Equipamento)')
for dev in ['arkray','sysmex','cobas']:
    nome = dev.capitalize()
    if f'status_ac_{dev}' in df.columns:
        st.subheader(f'{nome} – Albumina/Creatinina')
        st.bar_chart(df[f'status_ac_{dev}'].value_counts())
    if f'status_pc_{dev}' in df.columns:
        st.subheader(f'{nome} – Proteína/Creatinina')
        st.bar_chart(df[f'status_pc_{dev}'].value_counts())
        
# — Ordem das Categorias — #
ordem_cats = [
    'normal (<30 mg/g)',
    'microalbuminúria (30–300 mg/g)',
    'albuminúria manifesta (>300 mg/g)'
]
cores = {'Arkray':'#1f77b4','Sysmex':'#ff7f0e','Cobas':'#2ca02c'}
        
# — Gráficos por Área — #
st.header('Distribuição por Área e Categoria')
for titulo, categoria in [
    ('Valores Normais (<30 mg/g)',       'normal (<30 mg/g)'),
    ('Microalbuminúria (30–300 mg/g)',    'microalbuminúria (30–300 mg/g)'),
    ('Albuminúria manifesta (>300 mg/g)', 'albuminúria manifesta (>300 mg/g)')
]:
    st.subheader(titulo)
    records = []
    for dev in ['Arkray','Sysmex','Cobas']:
        cor = cores[dev]
        mask = df[f'Status AC {dev}'] == categoria
        grp = (df[mask]
            .groupby('Área')
            .size()
            .reset_index(name='Contagem'))
        grp['Equipamento'] = dev
        records.append(grp)
    df_area = pd.concat(records, ignore_index=True)
    chart_area = (
        alt.Chart(df_area)
        .mark_bar()
        .encode(
            x=alt.X('Área:N', axis=alt.Axis(labelAngle=0, title='Área')),
            y=alt.Y('Contagem:Q', title='N.º de amostras'),
            color=alt.Color('Equipamento:N',
                            scale=alt.Scale(range=list(cores.values())))
        )
        .properties(width=700)
    )
    st.altair_chart(chart_area, use_container_width=True)

# — Amostras Discordantes — #
st.header('Amostras Discordantes nos Três Equipamentos')
for tipo, label in [('AC','Albumina/Creatinina'), ('PC','Proteína/Creatinina')]:
    st.subheader(label)
    mask = df.apply(
        lambda r: len({
            r.get(f'Status {tipo} Arkray'),
            r.get(f'Status {tipo} Sysmex'),
            r.get(f'Status {tipo} Cobas')
        }) == 3,
        axis=1
    )
    cols = ['Tubo'] + [f'Status {tipo} {dev}' for dev in ['Arkray','Sysmex','Cobas']]
    df_diff = df.loc[mask, cols]
    st.write(df_diff if not df_diff.empty else 'Nenhuma amostra com três categorias diferentes.')


# — Amostras Discordantes — #
st.header('Amostras com Categorias Diferentes nos Três Equipamentos')
for tipo,label in [('ac','Albumina/Creatinina'), ('pc','Proteína/Creatinina')]:
    st.subheader(label)
    mask = df.apply(lambda r: len({
        r.get(f'status_{tipo}_arkray'),
        r.get(f'status_{tipo}_sysmex'),
        r.get(f'status_{tipo}_cobas')
    })==3, axis=1)
    cols = ['Tubo'] + [f'status_{tipo}_{dev}' for dev in ['arkray','sysmex','cobas']]
    df_diff = df.loc[mask, cols]
    if df_diff.empty:
        st.write('Nenhuma amostra com três categorias diferentes.')
    else:
        st.write(df_diff)

# — Transferir Dados Processados — #
towrite = BytesIO()
df.to_excel(towrite, index=False, engine='openpyxl')
towrite.seek(0)
st.download_button('📥 Transferir Excel Processado',
                data=towrite,
                file_name='dados_processados.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
