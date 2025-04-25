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

# — Início da app — #
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

# Limpeza de colunas
if df.columns.size > 0:
    df = df.iloc[:, 1:]                               # remove primeira coluna
df = df.loc[:, ~df.columns.str.startswith('Unnamed')]  # remove Unnamed
df.columns = df.columns.str.strip()
df = df.loc[:, df.columns.astype(bool)]               # remove colunas sem nome

# Renomear colunas-chave
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

# Cria colunas de Status e de Referência para cada equipamento
for dev in ['Arkray','Sysmex','Cobas']:
    col_ac = f'AC {dev}'
    col_pc = f'PC {dev}'
    if col_ac in df:
        df[f'Status AC {dev}'] = df[col_ac].apply(categorize_ac)
        df[f'Ref AC {dev}']    = df[col_ac].apply(categorize_ref)
    if col_pc in df:
        df[f'Status PC {dev}'] = df[col_pc].apply(categorize_pc)
        df[f'Ref PC {dev}']    = df[col_pc].apply(categorize_ref)

# Ordem fixa das 3 categorias de referência
ordem_cats = [
    'normal (<30 mg/g)',
    'microalbuminúria (30–300 mg/g)',
    'albuminúria manifesta (>300 mg/g)'
]

# — Gráficos individuais por equipamento (Referência) — #
st.header('Distribuição por Equipamento (Limites de Referência)')
cores = {'Arkray':'#1f77b4','Sysmex':'#ff7f0e','Cobas':'#2ca02c'}

for dev in ['Arkray','Sysmex','Cobas']:
    cor = cores[dev]
    # Albumina/Creatinina
    st.subheader(f'{dev} – Albumina/Creatinina')
    vc_ac = ( df[f'Ref AC {dev}']
            .value_counts()
            .reindex(ordem_cats, fill_value=0)
            .reset_index(name='Contagem')
            .rename(columns={'index':'Categoria'}) )
    chart_ac = (
        alt.Chart(vc_ac)
        .mark_bar(color=cor)
        .encode(
            x=alt.X('Categoria:N', sort=ordem_cats, axis=alt.Axis(labelAngle=0)),
            y=alt.Y('Contagem:Q', title='N.º de amostras')
        )
        .properties(width=500)
    )
    st.altair_chart(chart_ac, use_container_width=True)

    # Proteína/Creatinina
    st.subheader(f'{dev} – Proteína/Creatinina')
    vc_pc = ( df[f'Ref PC {dev}']
            .value_counts()
            .reindex(ordem_cats, fill_value=0)
            .reset_index(name='Contagem')
            .rename(columns={'index':'Categoria'}) )
    chart_pc = (
        alt.Chart(vc_pc)
        .mark_bar(color=cor)
        .encode(
            x=alt.X('Categoria:N', sort=ordem_cats, axis=alt.Axis(labelAngle=0)),
            y=alt.Y('Contagem:Q', title='N.º de amostras')
        )
        .properties(width=500)
    )
    st.altair_chart(chart_pc, use_container_width=True)

# — Resto do código (áreas, discordantes e download) — #
# (mantém-se igual ao anterior, gerando gráficos por área e tabelas de amostras discordantes)

# Transferir dados processados
towrite = BytesIO()
df.to_excel(towrite, index=False, engine='openpyxl')
towrite.seek(0)
st.download_button(
    '📥 Transferir Excel Processado',
    data=towrite,
    file_name='dados_processados.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)
