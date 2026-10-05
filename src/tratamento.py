import os
import pandas as pd

#Caminhos dos arquivos
caminho_bruto = 'data/raw/dados_brutos_belem.csv'
caminho_processado = 'data/processed/dados_limpos_belem.csv'

print('--- Iniciando Pipeline de Tratamento de Dados ---')

#Carregar dados brutos
df = pd.read_csv(caminho_bruto)

#Tratamento e Limpeza (LGPD / Padronização)
#Garante apenas dados de Belém e remove linhas vazias
df_limpo = df[df['municipio'] == 'Belém'].copy()
df_limpo = df_limpo.dropna()

#Criar pasta de destino se não existir
os.makedirs('data/processed', exist_ok=True)

#Exportar base tratada para o Streamlit/Ryan
df_limpo.to_csv(caminho_processado, index=False)

print(f'Sucesso! Base tratada salva em: {caminho_processado}')