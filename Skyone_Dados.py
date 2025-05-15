import requests
import pandas as pd
from io import StringIO

url = 'https://skyone-dados-demo-1.oci-sp.data.census.skyone.tools:443/census-cust-skyone-dados-demo-1/download/output/beneficios.csv?token=lv7CugFweD9FEQh2qnr1'
response = requests.get(url)

# Verifica se a requisição foi bem-sucedida
if response.status_code == 200:
    try:
        csv_content = StringIO(response.text)
        df = pd.read_csv(csv_content)

        # Salva como arquivo Excel
        df.to_excel('beneficios_skyone.xlsx', index=False)
        print('Arquivo Excel salvo com sucesso!')
    except Exception as e:
        print('Erro ao processar o arquivo:', e)
else:
    print(f'Erro {response.status_code}: {response.text}')