from fastapi import FastAPI
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from datetime import datetime

app = FastAPI()

# Conexão com o PostgreSQL
engine = create_engine("postgresql://postgres:123456@localhost:5999/postgres")

@app.get("/prever")
def prever_dados():
    try:
        # 1. Consulta base de dados
        query = """
        SELECT 
            v.data_venda AS "Mês/Ano",
            i.localizacao AS "Município",
            'GO' AS "UF",
            EXTRACT(MONTH FROM v.data_venda) AS mes,
            EXTRACT(YEAR FROM v.data_venda) AS ano,
            SUM(v.valor_total) AS "Valor Total",
            COUNT(DISTINCT i.id_infra) * 1000 AS populacao
        FROM public.vendas_corporativas v
        JOIN public.infraestrutura_corporativa i
            ON v.regiao = i.localizacao
        GROUP BY v.data_venda, i.localizacao
        """
        df = pd.read_sql(query, engine)

        # 2. Tratamento
        df['Mês/Ano'] = pd.to_datetime(df['Mês/Ano'], errors='coerce')
        df['Valor Total'] = pd.to_numeric(df['Valor Total'], errors='coerce')
        df['populacao'] = pd.to_numeric(df['populacao'], errors='coerce')
        df['Valor per capita'] = df['Valor Total'] / df['populacao']
        df = df.dropna()

        # 3. Geração de dados futuros
        municipios = df['Município'].unique()
        ultima_data = df['Mês/Ano'].max()
        future_data = []
        for i in range(1, 7):
            data_futura = (ultima_data + pd.DateOffset(months=i)).replace(day=1)
            for mun in municipios:
                base = df[df['Município'] == mun]
                future_data.append({
                    'UF': base['UF'].iloc[0],
                    'Município': mun,
                    'Mês/Ano': data_futura,
                    'populacao': base['populacao'].max() * np.random.uniform(0.98, 1.02),
                    'Valor Total': base['Valor Total'].mean() * np.random.uniform(0.9, 1.1),
                })

        future_df = pd.DataFrame(future_data)
        future_df['mes'] = future_df['Mês/Ano'].dt.month
        future_df['ano'] = future_df['Mês/Ano'].dt.year
        future_df['Valor per capita'] = future_df['Valor Total'] / future_df['populacao']

        # 4. Preparação para previsão
        df['mes'] = df['Mês/Ano'].dt.month
        df['ano'] = df['Mês/Ano'].dt.year
        df_completo = pd.concat([df, future_df], ignore_index=True)

        df_completo['mun_id'] = df_completo['Município'].astype('category').cat.codes
        future_df['mun_id'] = future_df['Município'].astype('category').cat.codes

        # 5. Previsão
        r2_scores = {}
        for target in ['populacao', 'Valor Total', 'Valor per capita']:
            X = df_completo[['mun_id', 'mes', 'ano']]
            y = df_completo[target]

            model = RandomForestRegressor(n_estimators=300, max_depth=10, min_samples_leaf=3, random_state=42)
            model.fit(X, y)

            y_pred = model.predict(X)
            r2_scores[target] = r2_score(y, y_pred)

            future_X = future_df[['mun_id', 'mes', 'ano']]
            future_df[f'{target}_previsto'] = model.predict(future_X)

        future_df['Valor per capita_calc_previsto'] = future_df['Valor Total_previsto'] / future_df['populacao_previsto']
        future_df['Acurácia_populacao'] = r2_scores['populacao']
        future_df['Acurácia_valor_total'] = r2_scores['Valor Total']
        future_df['Acurácia_valor_per_capita'] = r2_scores['Valor per capita']

        # 6. Saída formatada
        colunas_saida = [
            'Município', 'UF', 'Mês/Ano',
            'populacao', 'populacao_previsto', 'Acurácia_populacao',
            'Valor Total', 'Valor Total_previsto', 'Acurácia_valor_total',
            'Valor per capita', 'Valor per capita_previsto', 'Valor per capita_calc_previsto', 'Acurácia_valor_per_capita'
        ]

        resultado = future_df[colunas_saida].sort_values(['Município', 'Mês/Ano'])
        resultado['Mês/Ano'] = resultado['Mês/Ano'].astype(str)  # para JSON

        return resultado.to_dict(orient="records")

    except Exception as e:
        return {"erro": str(e)}
