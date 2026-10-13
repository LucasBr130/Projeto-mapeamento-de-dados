import os
import json
import pandas as pd

caminho_bruto = 'data/raw/dados_brutos_belem.csv'
caminho_csv = 'data/processed/dados_limpos_belem.csv'
caminho_json = 'dados_risco.json'

print("--- Processando Nova Base Oficial de Dados ---")

#Carregar e tratar dados
df = pd.read_csv(caminho_bruto)

#Garante a filtragem para Belém (removendo regiões metropolitanas fora do foco)
df_limpo = df[df['municipio'] == 'Belém'].dropna(subset=['bairro_belem']).copy()

#Cria a coluna padronizada 'bairro' para facilitar a integração
df_limpo['bairro'] = df_limpo['bairro_belem']

#Salva CSV limpo em data/processed/
os.makedirs('data/processed', exist_ok=True)
df_limpo.to_csv(caminho_csv, index=False)

#Mapeamento de Risco por Bairro para a Interface / HTML
matriz_risco = {}

for _, row in df_limpo.iterrows():
    bairro = row['bairro']
    volume = row['volume_amostral']
    
    #Classificação de risco baseada no volume amostral de ocorrências
    if volume >= 4000:
        nivel = "Alto"
        cor = "#c92a2a"
        bg = "#fdf0f4"
    elif volume >= 2500:
        nivel = "Médio"
        cor = "#d97706"
        bg = "#fef3c7"
    else:
        nivel = "Baixo"
        cor = "#10b981"
        bg = "#d1fae5"

    matriz_risco[bairro] = {
        "texto": nivel,
        "cor": cor,
        "bg": bg,
        "faixa_horario": row.get('faixa_horario', 'Não informado'),
        "tipo_registro": row.get('tipo_registro', 'Ocorrência geral')
    }

#Exporta JSON para o site
with open(caminho_json, 'w', encoding='utf-8') as f:
    json.dump(matriz_risco, f, ensure_ascii=False, indent=4)

print("'dados_limpos_belem.csv' e 'dados_risco.json' atualizados")