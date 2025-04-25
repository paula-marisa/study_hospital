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

# — Leitura — #
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
    'Área':           'Área',
    'A/C Arkray (mg/gCr)': 'AC Arkray',
    'P/C Arkray (mg/gCr)': 'PC Arkray',
    'A/C Sysmex (mg/gCr)': 'AC Sysmex',
    'P/C Sysmex (mg/gCr)': 'PC Sysmex',
    'A/C Cobas (mg/gCr)':  'AC Cobas',
    'P/C Cobas (mg/gCr)':  'PC Cobas'
})

# — Categorização — #
for dev in ['Arkray','Sysmex','Cobas']:
    ac_col = f'AC {dev}'
    pc_col = f'PC {dev}'
    if ac_col in df.columns:
        df[f'Status AC {dev}'] = df[ac_col].apply(categorize_ac)
        df[f'Ref AC {dev}']    = df[ac_col].apply(categorize_ref)
    if pc_col in df.columns:
        df[f'Status PC {dev}'] = df[pc_col].apply(categorize_pc)
        df[f'Ref PC {dev}']    = df[pc_col].apply(categorize_ref)

# — Ordem das Categorias — #
ordem_cats = [
    'normal (<30 mg/g)',
    'microalbuminúria (30–300 mg/g)',
    'albuminúria manifesta (>300 mg/g)'
]
cores = {'Arkray':'#1f77b4','Sysmex':'#ff7f0e','Cobas':'#2ca02c'}

# — Gráficos Individuais (Limites de Referência) — #
st.header('Distribuição por Equipamento (Limites de Referência)')
for dev in ['Arkray','Sysmex','Cobas']:
    cor = cores[dev]
    # Albumina/Creatinina
    st.subheader(f'{dev} – Albumina/Creatinina')
    vc_ac = (df[f'Ref AC {dev}']
            .value_counts()
            .reindex(ordem_cats, fill_value=0)
            .reset_index(name='Contagem')
            .rename(columns={'index':'Categoria'}))
    chart_ac = (
        alt.Chart(vc_ac)
        .mark_bar(color=cor)
        .encode(
            x=alt.X('Categoria:N', sort=ordem_cats,
                    axis=alt.Axis(labelAngle=0, title='Categoria')),
            y=alt.Y('Contagem:Q', title='N.º de amostras')
        )
        .properties(width=600)
    )
    st.altair_chart(chart_ac, use_container_width=True)

    # Proteína/Creatinina
    st.subheader(f'{dev} – Proteína/Creatinina')
    vc_pc = (df[f'Ref PC {dev}']
            .value_counts()
            .reindex(ordem_cats, fill_value=0)
            .reset_index(name='Contagem')
            .rename(columns={'index':'Categoria'}))
    chart_pc = (
        alt.Chart(vc_pc)
        .mark_bar(color=cor)
        .encode(
            x=alt.X('Categoria:N', sort=ordem_cats,
                    axis=alt.Axis(labelAngle=0, title='Categoria')),
            y=alt.Y('Contagem:Q', title='N.º de amostras')
        )
        .properties(width=600)
    )
    st.altair_chart(chart_pc, use_container_width=True)

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

# — Transferir Dados Processados — #
towrite = BytesIO()
df.to_excel(towrite, index=False, engine='openpyxl')
towrite.seek(0)
st.download_button(
    '📥 Transferir Excel Processado',
    data=towrite,
    file_name='dados_processados.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)
