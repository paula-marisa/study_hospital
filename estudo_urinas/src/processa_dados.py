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

# — Definições gerais — #
st.title('Análise de Albumina/Creatinina e Proteína/Creatinina')
cores = {'arkray':'blue','sysmex':'green','cobas':'red'}
equipamentos = ['arkray','sysmex','cobas']

# — Upload e leitura — #
uploaded = st.file_uploader('Carregue o ficheiro (Excel ou CSV)', type=['xlsx','csv'])
if not uploaded:
    st.info('Por favor, carregue um ficheiro para iniciar o processamento.')
    st.stop()

if uploaded.name.lower().endswith('.csv'):
    df = pd.read_csv(uploaded)
else:
    df = pd.read_excel(uploaded, header=3, engine='openpyxl')

# — Limpeza de colunas — #
if df.columns.size > 0:
    df = df.iloc[:, 1:]
df = df.loc[:, ~df.columns.str.startswith('Unnamed')]
df.columns = df.columns.str.strip()
df = df.loc[:, df.columns.astype(bool)]

# — Renomear colunas — #
df = df.rename(columns={
    'Nº Tubo': 'Tubo',
    'Área':    'área',
    'A/C Arkray (mg/gCr)': 'ac_arkray',
    'P/C Arkray (mg/gCr)': 'pc_arkray',
    'A/C Sysmex (mg/gCr)': 'ac_sysmex',
    'P/C Sysmex (mg/gCr)': 'pc_sysmex',
    'A/C Cobas (mg/gCr)':  'ac_cobas',
    'P/C Cobas (mg/gCr)':  'pc_cobas'
})

# — Categorização — #
for dev in equipamentos:
    if f'ac_{dev}' in df:
        df[f'status_ac_{dev}'] = df[f'ac_{dev}'].apply(categorize_ac)
        df[f'ref_ac_{dev}']    = df[f'ac_{dev}'].apply(categorize_ref)
    if f'pc_{dev}' in df:
        df[f'status_pc_{dev}'] = df[f'pc_{dev}'].apply(categorize_pc)
        df[f'ref_pc_{dev}']    = df[f'pc_{dev}'].apply(categorize_ref)

# — Gráficos de barras com Altair (Status interno) — #
st.header('Distribuição por Equipamento (Status Interno)')
for tipo, func in [('Albumina/Creatinina','status_ac_'),
                ('Proteína/Creatinina','status_pc_')]:
    for dev in equipamentos:
        campo = f'{func}{dev}'
        if campo in df:
            nome = dev.capitalize()
            vc = (df[campo]
                .value_counts()
                .reset_index(name='Contagem')
                .rename(columns={'index':'Categoria'}))
            chart = (alt.Chart(vc)
                    .mark_bar(color=cores[dev])
                    .encode(
                        x=alt.X('Categoria:N', axis=alt.Axis(labelAngle=0,title='Categoria')),
                        y=alt.Y('Contagem:Q', title='N.º de amostras')
                    )
                    .properties(width=400, title=f'{nome} – {tipo}'))
            st.altair_chart(chart, use_container_width=True)

# — Gráficos de área por Categoria e Área (Status interno) — #
st.header('Valores por Área e Categoria (Status Interno)')
for tipo, func, cats in [
    ('A/C','status_ac_',['normal (<30 mg/g)','microalbuminúria (30–300 mg/g)','albuminúria manifesta (>300 mg/g)']),
    ('P/C','status_pc_',['normal (<150 mg/g)','microproteinúria (150–300 mg/g)','proteinúria manifesta (>300 mg/g)'])
]:
    st.subheader(f'{tipo} por Área')
    for cat in cats:
        st.markdown(f'**{cat}**')
        records = []
        for dev in equipamentos:
            campo = f'{func}{dev}'
            df_area = (df[df[campo]==cat]
                    .groupby('área')
                    .size()
                    .reset_index(name='Contagem'))
            df_area['Equipamento'] = dev.capitalize()
            records.append(df_area)
        long = pd.concat(records,ignore_index=True)
        chart = (alt.Chart(long)
                .mark_area(opacity=0.4)
                .encode(
                    x=alt.X('área:N', axis=alt.Axis(labelAngle=0,title='Área')),
                    y='Contagem:Q',
                    color=alt.Color('Equipamento:N',
                                    scale=alt.Scale(domain=[d.capitalize() for d in equipamentos],
                                                    range=[cores[d] for d in equipamentos]))
                )
                .properties(width=600))
        st.altair_chart(chart, use_container_width=True)

# — Amostras discordantes — #
st.header('Amostras com Categorias Diferentes')
for tipo,label in [('ac','Albumina/Creatinina'),('pc','Proteína/Creatinina')]:
    st.subheader(label)
    mask = df.apply(lambda r: len({
        r.get(f'status_{tipo}_arkray'),
        r.get(f'status_{tipo}_sysmex'),
        r.get(f'status_{tipo}_cobas')
    })==3, axis=1)
    cols = ['Tubo']+[f'status_{tipo}_{dev}' for dev in equipamentos]
    df_diff = df.loc[mask,cols]
    st.write(df_diff if not df_diff.empty else 'Nenhuma amostra com três categorias diferentes.')

# — Transferir Excel processado — #
towrite = BytesIO()
df.to_excel(towrite, index=False, engine='openpyxl')
towrite.seek(0)
st.download_button('📥 Transferir Excel Processado',
                data=towrite,
                file_name='dados_processados.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
