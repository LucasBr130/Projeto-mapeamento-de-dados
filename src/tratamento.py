import os
import re
import json
import pandas as pd

CAMINHO_BRUTO = 'data/raw/dados_brutos_belem.csv'
CAMINHO_CSV = 'data/processed/dados_limpos.csv'
CAMINHO_JSON = 'dados_risco.json'

# Fontes que não são registros de ocorrência (ex.: pesquisas de percepção)
# e por isso não entram no cálculo de risco. Ajuste conforme sua base.
FONTES_IGNORADAS = {'DataSenado'}

# Períodos do select do site (cobrem as 24h)
PERIODOS = {
    'pico':      [18, 19, 20, 21],
    'madrugada': [22, 23, 0, 1, 2, 3, 4, 5],
    'manha':     [6, 7, 8, 9, 10, 11],
    'tarde':     [12, 13, 14, 15, 16, 17],
}

NIVEIS = [
    ("Baixo", "#10b981", "#d1fae5"),
    ("Médio", "#d97706", "#fef3c7"),
    ("Alto",  "#c92a2a", "#fdf0f4"),
]
CORTE_ALTO = 4000
CORTE_MEDIO = 2500


def nivel_base(volume):
    """Nível do bairro pelo volume de ocorrências (0=Baixo, 1=Médio, 2=Alto)."""
    if volume >= CORTE_ALTO:
        return 2
    if volume >= CORTE_MEDIO:
        return 1
    return 0


def horas_da_faixa(faixa):
    """'20h00 - 02h00' -> {20,21,22,23,0,1}. Retorna None se não houver faixa válida."""
    if not isinstance(faixa, str):
        return None
    m = re.match(r'\s*(\d{1,2})h(\d{2})\s*-\s*(\d{1,2})h(\d{2})\s*$', faixa)
    if not m:
        return None
    h_ini, _, h_fim, min_fim = map(int, m.groups())
    ultima = (h_fim - 1 if min_fim == 0 else h_fim) % 24   # 02h00 termina antes das 2h
    horas, h = set(), h_ini % 24
    while True:
        horas.add(h)
        if h == ultima:
            break
        h = (h + 1) % 24
    return horas


print("--- Processando base de dados ---")

df = pd.read_csv(CAMINHO_BRUTO)

# Aceita a coluna nova 'bairro' ou a antiga 'bairro_belem'
if 'bairro' not in df.columns:
    df['bairro'] = df['bairro_belem']

# 'Ananindeua (RMB)' -> 'Ananindeua'
df['municipio'] = df['municipio'].astype(str).str.replace(r'\s*\(.*\)\s*$', '', regex=True).str.strip()

df_limpo = df.dropna(subset=['bairro', 'municipio']).copy()
if 'fonte_dados' in df_limpo.columns:
    df_limpo = df_limpo[~df_limpo['fonte_dados'].isin(FONTES_IGNORADAS)]

# Uma linha por bairro+município (fica a de maior volume)
df_limpo = (df_limpo.sort_values('volume_amostral', ascending=False)
                    .drop_duplicates(['bairro', 'municipio']))

os.makedirs('data/processed', exist_ok=True)
df_limpo.to_csv(CAMINHO_CSV, index=False)

matriz_risco = {}
for _, row in df_limpo.iterrows():
    base = nivel_base(row['volume_amostral'])
    faixa = row.get('faixa_horario')
    horas_faixa = horas_da_faixa(faixa)
    tipo = row.get('tipo_registro', 'Ocorrência geral')
    chave = f"{row['bairro']}, {row['municipio']}"

    matriz_risco[chave] = {}
    for periodo, horas_periodo in PERIODOS.items():
        if horas_faixa is None:
            # Sem faixa horária na base: não há como variar, mantém o nível base
            nivel, na_faixa = base, None
        else:
            cobertura = len(horas_faixa & set(horas_periodo)) / len(horas_periodo)
            na_faixa = cobertura >= 0.5
            nivel = base if na_faixa else max(base - 1, 0)

        texto, cor, bg = NIVEIS[nivel]
        matriz_risco[chave][periodo] = {
            "bairro": row['bairro'],
            "municipio": row['municipio'],
            "texto": texto,
            "cor": cor,
            "bg": bg,
            "na_faixa_de_pico": na_faixa,
            "faixa_pico": faixa if isinstance(faixa, str) else "Não informado",
            "tipo_registro": tipo,
            "volume": int(row['volume_amostral']),
            "fonte": row.get('fonte_dados', 'Não informado'),
        }

with open(CAMINHO_JSON, 'w', encoding='utf-8') as f:
    json.dump(matriz_risco, f, ensure_ascii=False, indent=4)

print(f"{len(matriz_risco)} bairros gravados em dados_risco.json")
