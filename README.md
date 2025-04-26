# Análise de Albumina/Creatinina e Proteína/Creatinina

Este projeto disponibiliza uma aplicação **Streamlit** para processar ficheiros de análises de urina (Excel ou CSV), categorizar as razões A/C (albumina/creatinina) e P/C (proteína/creatinina) segundo limites de referência, e gerar visualizações interativas.

---

## Funcionalidades

- Leitura automática de Excel ou CSV, com deteção da linha de cabeçalho.
- Limpeza das colunas, remoção de colunas sem nome.
- Categorização dos valores de A/C e P/C em:
  - **Abaixo do normal** (<30 mg/g ou <150 mg/g)
  - **Normal** (30–300 mg/g ou 150–300 mg/g)
  - **Acima do normal** (>300 mg/g)
- Geração de gráficos:
  - **Barras** por equipamento (Arkray, Sysmex, Cobas) para status interno.
  - **Área** por categoria e área clínica, cores distintas (azul, verde, vermelho).
- Identificação de amostras com discordância total entre os três equipamentos.
- Exportação do resultado processado para Excel.

---

## Requisitos

- Python 3.8+
- [Streamlit](https://streamlit.io/) >=1.0.0
- Pandas
- Openpyxl
- Altair

Exemplo de `requirements.txt`:

```txt
streamlit==1.44.1
pandas==2.2.3
openpyxl==3.1.5
altair==5.5.0
```

---

## Instalação

1. Clonar este repositório:
   ```bash
git clone https://github.com/usuario/estudo_urinas.git
cd estudo_urinas
```  
2. Criar e ativar um ambiente virtual:
   ```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\\Scripts\\activate   # Windows
```  
3. Instalar dependências:
   ```bash
pip install -r requirements.txt
```  

---

## Execução local

```bash
streamlit run src/processa_dados.py
```  
Abra o browser em `http://localhost:8501`.

---

## Estrutura do projeto

```
estudo_urinas/
├── data/                     # Ficheiros Excel/CSV de exemplo
├── src/
│   └── processa_dados.py     # App Streamlit
├── .venv/                    # Ambiente virtual (não versionar)
├── requirements.txt         # Dependências
└── README.md                # Este ficheiro
```

---

## Deploy

É possível hospedar gratuitamente no [Streamlit Community Cloud](https://streamlit.io/cloud):
1. Criar repositório no GitHub e enviar o código.  
2. Conectar no Streamlit Cloud e apontar para o repositório e ficheiro principal (`src/processa_dados.py`).  

---

## Customização

- **Cores**: ajustar o dicionário `color_map` no código para outros hexadecimais.
- **Limites**: modificar as funções `categorize_ac` e `categorize_pc` conforme necessidade.
- **Deteção de cabeçalho**: ajustar `keywords` em `detect_header_row` para novas versões de ficheiro.

---