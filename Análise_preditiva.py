import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from datetime import datetime
import numpy as np

try:
    # 1. Leitura
    df = pd.read_excel('beneficios_skyone.xlsx')
    print("\n✅ Arquivo carregado.")
    print(df.head())

    # 2. Tratamento
    df['Mês/Ano'] = pd.to_datetime(df['Mês/Ano'], format='%m/%Y', errors='coerce')
    df['populacao'] = pd.to_numeric(df['populacao'], errors='coerce')
    df['Valor Total'] = df['Valor Total'].astype(str).str.replace(',', '.')
    df['Valor Total'] = pd.to_numeric(df['Valor Total'], errors='coerce')
    df['Valor per capita'] = df['Valor per capita'].astype(str).str.replace(',', '.')
    df['Valor per capita'] = pd.to_numeric(df['Valor per capita'], errors='coerce')

    df = df.dropna(subset=['Mês/Ano', 'populacao', 'Valor Total', 'Valor per capita'])
    df['mes'] = df['Mês/Ano'].dt.month
    df['ano'] = df['Mês/Ano'].dt.year

    # 3. Gerar dados futuros
    municipios = df['Município'].unique()
    ultima_data = df['Mês/Ano'].max()

    future_data = []
    for i in range(1, 7):
        data_futura = (ultima_data + pd.DateOffset(months=i)).replace(day=1)
        for mun in municipios:
            try:
                populacao_base = df[df['Município'] == mun]['populacao'].max()
                valor_base = df[df['Município'] == mun]['Valor Total'].mean()
                capita_base = df[df['Município'] == mun]['Valor per capita'].mean()

                future_data.append({
                    'UF': df[df['Município'] == mun]['UF'].iloc[0],
                    'Município': mun,
                    'Mês/Ano': data_futura,
                    'populacao': populacao_base * np.random.uniform(0.98, 1.02),
                    'Valor Total': valor_base * np.random.uniform(0.9, 1.1),
                    'Valor per capita': capita_base * np.random.uniform(0.9, 1.1),
                })
            except:
                continue

    future_df = pd.DataFrame(future_data)
    future_df['mes'] = future_df['Mês/Ano'].dt.month
    future_df['ano'] = future_df['Mês/Ano'].dt.year

    # 4. Unir
    df_completo = pd.concat([df, future_df], ignore_index=True)

    # 🔁 Codificar município
    df_completo['mun_id'] = df_completo['Município'].astype('category').cat.codes
    future_df['mun_id'] = future_df['Município'].astype('category').cat.codes

    # 5. Previsão de todas as variáveis com r2
    r2_scores = {}
    for target in ['populacao', 'Valor Total', 'Valor per capita']:
        X = df_completo[['mun_id', 'mes', 'ano']]
        y = df_completo[target]

        model = RandomForestRegressor(
            n_estimators=300,
            max_depth=10,
            min_samples_leaf=3,
            random_state=42
        )
        model.fit(X, y)

        y_pred = model.predict(X)
        r2 = r2_score(y, y_pred)
        r2_scores[target] = r2
        print(f"📈 Acurácia para {target}: {r2:.2%}")

        future_X = future_df[['mun_id', 'mes', 'ano']]
        future_df[f'{target}_previsto'] = model.predict(future_X)

    # 6. Calcular valor per capita previsto a partir de valor/pop
    future_df['Valor per capita_calc_previsto'] = future_df['Valor Total_previsto'] / future_df['populacao_previsto']

    # 7. Adicionar colunas de acurácia
    future_df['Acurácia_populacao'] = r2_scores['populacao']
    future_df['Acurácia_valor_total'] = r2_scores['Valor Total']
    future_df['Acurácia_valor_per_capita'] = r2_scores['Valor per capita']

    # 8. Organizar e salvar
    colunas_saida = [
        'Município', 'UF', 'Mês/Ano',
        'populacao', 'populacao_previsto', 'Acurácia_populacao',
        'Valor Total', 'Valor Total_previsto', 'Acurácia_valor_total',
        'Valor per capita', 'Valor per capita_previsto', 'Valor per capita_calc_previsto', 'Acurácia_valor_per_capita'
    ]

    output_df = future_df[colunas_saida].sort_values(['Município', 'Mês/Ano'])
    output_df.to_excel('previsao_multivariada_6_meses_comparada.xlsx', index=False)

    print("📁 Arquivo 'previsao_multivariada_6_meses_comparada.xlsx' gerado com sucesso!")

except Exception as e:
    print(f'❌ Erro no processamento: {e}')
