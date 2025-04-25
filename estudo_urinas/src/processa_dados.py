import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO

# Funções de categorização

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

# Categorização de referência (limites uniformes)

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

st.title('Análise de Albumina/Creatinina e Proteína/Creatinina')

# Carregamento do ficheiro
uploaded = st.file_uploader('Carregue o ficheiro (Excel ou CSV)', type=['xlsx','csv'])
if not uploaded:
    st.info('Por favor, carregue um ficheiro para iniciar o processamento.')
    st.stop()

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
    'Área': 'Área',
    'A/C Arkray (mg/gCr)': 'AC Arkray',
    'P/C Arkray (mg/gCr)': 'PC Arkray',
    'A/C Sysmex (mg/gCr)': 'AC Sysmex',
    'P/C Sysmex (mg/gCr)': 'PC Sysmex',
    'A/C Cobas (mg/gCr)': 'AC Cobas',
    'P/C Cobas (mg/gCr)': 'PC Cobas'
})

# Categorização por equipamento
for dev in ['Arkray','Sysmex','Cobas']:
    col_ac = f'AC {dev}'
    col_pc = f'PC {dev}'
    if col_ac in df.columns:
        df[f'Status AC {dev}'] = df[col_ac].apply(categorize_ac)
        df[f'Ref AC {dev}'] = df[col_ac].apply(categorize_ref)
    if col_pc in df.columns:
        df[f'Status PC {dev}'] = df[col_pc].apply(categorize_pc)
        df[f'Ref PC {dev}'] = df[col_pc].apply(categorize_ref)

# Gráficos individuais por equipamento
st.header('Distribuição por Equipamento')
for dev, cor in zip(['Arkray','Sysmex','Cobas'], ['#1f77b4','#ff7f0e','#2ca02c']):
    st.subheader(f'{dev} – Albumina/Creatinina')
    data_ac = (
        df[f'Status AC {dev}']
        .value_counts()
        .reset_index()
        .rename(columns={'index':'Categoria', f'Status AC {dev}':'Contagem'})
    )
    chart_ac = (
        alt.Chart(data_ac)
        .mark_bar(color=cor)
        .encode(
            x=alt.X('Categoria:N', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('Contagem:Q', title='Número de amostras')
        )
        .properties(width=500)
    )
    st.altair_chart(chart_ac, use_container_width=True)

    st.subheader(f'{dev} – Proteína/Creatinina')
    data_pc = (
        df[f'Status PC {dev}']
        .value_counts()
        .reset_index()
        .rename(columns={'index':'Categoria', f'Status PC {dev}':'Contagem'})
    )
    chart_pc = (
        alt.Chart(data_pc)
        .mark_bar(color=cor)
        .encode(
            x=alt.X('Categoria:N', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('Contagem:Q', title='Número de amostras')
        )
        .properties(width=500)
    )
    st.altair_chart(chart_pc, use_container_width=True)

# Gráficos por área para valores NORMAL, MICRO e ALTO
limites = [
    ('Valores Normais (<30 mg/g)', 'normal (<30 mg/g)'),
    ('Microalbuminúria (30–300 mg/g)', 'microalbuminúria (30–300 mg/g)'),
    ('Albuminúria manifesta (>300 mg/g)', 'albuminúria manifesta (>300 mg/g)')
]
st.header('Distribuição por Área e Categoria')
for titulo, cat in limites:
    st.subheader(titulo)
    # Criar DF long format
    records = []
    for dev, cor in zip(['Arkray','Sysmex','Cobas'], ['#1f77b4','#ff7f0e','#2ca02c']):
        mask = df[f'Status AC {dev}']==cat
        contagens = df[mask].groupby('Área').size().reset_index(name='Contagem')
        contagens['Equipamento'] = dev
        records.append(contagens)
    df_lim = pd.concat(records)
    chart_area = (
        alt.Chart(df_lim)
        .mark_bar()
        .encode(
            x=alt.X('Área:N', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('Contagem:Q'),
            color=alt.Color('Equipamento:N', scale=alt.Scale(range=['#1f77b4','#ff7f0e','#2ca02c']))
        )
        .properties(width=600)
    )
    st.altair_chart(chart_area, use_container_width=True)

# Identificação de amostras discordantes
st.header('Amostras Discordantes nos Três Equipamentos')
for tipo in ['AC','PC']:
    st.subheader(f'{"Albumina/Creatinina" if tipo=="AC" else "Proteína/Creatinina"}')
    mask = df.apply(lambda r: len({r.get(f'Status {tipo} Arkray'), r.get(f'Status {tipo} Sysmex'), r.get(f'Status {tipo} Cobas')})==3, axis=1)
    cols = ['Tubo'] + [f'Status {tipo} ' + dev for dev in ['Arkray','Sysmex','Cobas']]
    df_diff = df.loc[mask, cols]
    st.write(df_diff if not df_diff.empty else 'Nenhuma amostra com três categorias distintas.')

# Transferir dados processados
towrite = BytesIO()
df.to_excel(towrite, index=False, engine='openpyxl')
towrite.seek(0)
st.download_button('📥 Transferir Excel Processado', data=towrite,
                file_name='dados_processados.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')