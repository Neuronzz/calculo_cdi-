import zipfile
import pandas as pd
from urllib.request import urlretrieve as retrieve
from io import BytesIO
import requests

# Obter a data de hoje
data_hoje = pd.Timestamp.today()

# Definir o mês anterior com base na data de hoje
mes_anterior = data_hoje - pd.DateOffset(months=4)

# Verificar se a data de hoje é um dos 5 primeiros dias úteis do mês
primeiros_5_dias = pd.date_range(start=mes_anterior, periods=5, freq='B')

if data_hoje in primeiros_5_dias:
    # Caso seja um dos 5 primeiros dias úteis do mês, pegar 2 meses atrás
    mes_anterior = data_hoje - pd.DateOffset(months=2)

# Formatar o resultado como 'yyyymm'
mes_anterior = mes_anterior.strftime('%Y%m')

def retrieve(url):
    response = requests.get(url)
    response.raise_for_status()
    return BytesIO(response.content)

# Base de dados para a carteira dos fundos
def carteiras_cvm(mes_anterior, arquivos):
    url = f'https://dados.cvm.gov.br/dados/FI/DOC/CDA/DADOS/cda_fi_{mes_anterior}.zip'  # Link do arquivo cadastral no site da CVM
    zip_file = retrieve(url)  # Baixar o arquivo da URL e retornar como BytesIO
    
    dataframes = {}
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        for i in arquivos:
            nome_arquivo = f'cda_fi_BLC_{i}_{mes_anterior}.csv'
            if nome_arquivo in zip_ref.namelist():
                with zip_ref.open(nome_arquivo) as file:
                    df = pd.read_csv(file, sep=';', encoding='ISO-8859-1')
                    dataframes[f'cda_fi_BLC_{i}'] = df
    
    return dataframes

# Exemplo de uso
arquivos_desejados = [1, 2, 3, 4, 5, 6, 7, 8]  # Números dos arquivos desejados
carteiras_cvm_dict = carteiras_cvm(mes_anterior, arquivos_desejados)

for key, df in carteiras_cvm_dict.items():
    print(key)

# Renomeia as colunas
novos_nomes = {
    'CNPJ_FUNDO': 'CNPJ',
    'DENOM_SOCIAL': 'Fundo',
    'TP_TITPUB': 'Ativo',
    'TP_ATIVO': 'Ativo',
    'VL_MERC_POS_FINAL': 'Financeiro',
    'NM_FUNDO_COTA': 'Ativo',
    'DS_ATIVO': 'Ativo',
    'CNPJ_FUNDO_COTA': 'Codigo',
    'CD_ATIVO': 'Codigo',
    'EMISSOR': 'Codigo'
}

substituicoes = {
    'LETRAS FINANCEIRAS DO TESOURO': 'LFT',
    'LETRAS DO TESOURO NACIONAL': 'LTN',
    'NOTAS DO TESOURO NACIONAL - SERIE F': 'NTNF',
    'NOTAS DO TESOURO NACIONAL SERIE B': 'NTNB',
    'NOTAS DO TESOURO NACIONAL SERIE C': 'NTNC',
    'NOTAS DO TESOURO NACIONAL SERIE I': 'NTNI'
}

carteira1 = carteiras_cvm_dict['cda_fi_BLC_1'][['CNPJ_FUNDO', 'DENOM_SOCIAL', 'TP_TITPUB', 'VL_MERC_POS_FINAL', 'DT_VENC']]
carteira1['TP_TITPUB'] = carteira1['TP_TITPUB'].replace(substituicoes)
carteira1['TP_TITPUB'] = carteira1.apply(lambda x: f"{x['TP_TITPUB']} {pd.to_datetime(x['DT_VENC']).year}", axis=1)
carteira1.rename(columns=novos_nomes, inplace=True)
carteira1 = carteira1[['CNPJ', 'Fundo', 'Financeiro', 'Ativo']]
carteira1['Tipo'] = 'Título Público'

carteira2 = carteiras_cvm_dict['cda_fi_BLC_2'][['CNPJ_FUNDO', 'DENOM_SOCIAL', 'VL_MERC_POS_FINAL', 'CNPJ_FUNDO_COTA', 'NM_FUNDO_COTA']]
carteira2.rename(columns=novos_nomes, inplace=True)
carteira2 = carteira2[['CNPJ', 'Fundo', 'Financeiro', 'Ativo', 'Codigo']]
carteira2['Tipo'] = 'Fundo de Investimento'

carteira3 = carteiras_cvm_dict['cda_fi_BLC_3'][['CNPJ_FUNDO', 'DENOM_SOCIAL', 'VL_MERC_POS_FINAL', 'TP_ATIVO', 'DS_SWAP']]
carteira3['TP_ATIVO'] = carteira3.apply(lambda x: f"{x['TP_ATIVO']} {x['DS_SWAP']}", axis=1)
carteira3.rename(columns=novos_nomes, inplace=True)
carteira3 = carteira3[['CNPJ', 'Fundo', 'Financeiro', 'Ativo']]
carteira3['Tipo'] = 'SWAP'

carteira4 = carteiras_cvm_dict['cda_fi_BLC_4'][['CNPJ_FUNDO', 'DENOM_SOCIAL', 'VL_MERC_POS_FINAL', 'DS_ATIVO', 'CD_ATIVO']]
carteira4.rename(columns=novos_nomes, inplace=True)
carteira4 = carteira4[['CNPJ', 'Fundo', 'Financeiro', 'Ativo', 'Codigo']]
carteira4['Tipo'] = 'Ações'

carteira5 = carteiras_cvm_dict['cda_fi_BLC_5'][['CNPJ_FUNDO', 'DENOM_SOCIAL', 'VL_MERC_POS_FINAL', 'TP_ATIVO', 'EMISSOR', 'DT_VENC']]
carteira5['Tipo'] = carteira5['TP_ATIVO']
carteira5['TP_ATIVO'] = carteira5['TP_ATIVO'].str.replace('Letra Financeira', 'LF')
carteira5['TP_ATIVO'] = carteira5.apply(lambda x: f"{x['TP_ATIVO']} {x['EMISSOR']} {pd.to_datetime(x['DT_VENC']).year}", axis=1)
carteira5.rename(columns=novos_nomes, inplace=True)
carteira5 = carteira5[['CNPJ', 'Fundo', 'Financeiro', 'Ativo', 'Tipo']]

carteira6 = carteiras_cvm_dict['cda_fi_BLC_6'][['CNPJ_FUNDO', 'DENOM_SOCIAL', 'VL_MERC_POS_FINAL', 'TP_ATIVO', 'EMISSOR', 'DT_VENC']]
carteira6['Tipo'] = carteira6['TP_ATIVO']
carteira6['TP_ATIVO'] = carteira6['TP_ATIVO'].str.replace('Debênture simples', 'Deb')
carteira6['TP_ATIVO'] = carteira6['TP_ATIVO'].str.replace('Debênture conversível', 'Deb')
carteira6['TP_ATIVO'] = carteira6.apply(lambda x: f"{x['TP_ATIVO']} {x['EMISSOR']} {pd.to_datetime(x['DT_VENC']).year}", axis=1)
carteira6.rename(columns=novos_nomes, inplace=True)
carteira6 = carteira6[['CNPJ', 'Fundo', 'Financeiro', 'Ativo', 'Tipo']]

carteira7 = carteiras_cvm_dict['cda_fi_BLC_7'][['CNPJ_FUNDO', 'DENOM_SOCIAL', 'VL_MERC_POS_FINAL', 'EMISSOR', 'DT_VENC', 'CD_ATIVO_BV_MERC', 'TP_ATIVO']]
carteira7['DS_ATIVO'] = carteira7.apply(
    lambda x: f"{x['EMISSOR']} {pd.to_datetime(x['DT_VENC']).year}" if pd.notnull(x['DT_VENC']) else x['EMISSOR'],
    axis=1
)
carteira7.rename(columns={'TP_ATIVO': 'Tipo'}, inplace=True)
carteira7.rename(columns=novos_nomes, inplace=True)
carteira7 = carteira7[['CNPJ', 'Fundo', 'Financeiro', 'Ativo', 'Codigo', 'Tipo']]

carteira8 = carteiras_cvm_dict['cda_fi_BLC_8'][['CNPJ_FUNDO', 'DENOM_SOCIAL', 'VL_MERC_POS_FINAL', 'DS_ATIVO', 'TP_APLIC']]
carteira8.rename(columns={'TP_APLIC': 'Tipo'}, inplace=True)
carteira8.rename(columns=novos_nomes, inplace=True)
carteira8.loc[carteira8['Tipo'] == 'Valores a pagar', 'Financeiro'] *= -1

# Lista de dataframes a serem concatenados
dataframes = [carteira1, carteira2, carteira3, carteira4, carteira5, carteira6, carteira7, carteira8]

# Junção de cada df de carteira em uma unica
carteira = pd.concat(dataframes, ignore_index=True, join='outer')

# Calcula a soma da coluna 'Financeiro' agrupada por 'CNPJ'
pl_por_cnpj = carteira.groupby('CNPJ')['Financeiro'].sum().reset_index()

# Renomeia a coluna da soma para 'PL'
pl_por_cnpj.rename(columns={'Financeiro': 'PL'}, inplace=True)

# Faz o merge do DataFrame combinado com o DataFrame das somas
carteira = carteira.merge(pl_por_cnpj, on='CNPJ', how='left')

# Calcula a exposição do PL
carteira['Exposicao'] = carteira['Financeiro'] / carteira['PL']
