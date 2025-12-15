import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Análise de internações", layout="wide")

st.title("Análise de internações por pneumonia")
st.markdown("Feito por Pedro Escobar para o Programa de Iniciacao Cientifica Junior da PUCRS - 2025")

arquivo = st.file_uploader("Envie o arquivo pneumonia.csv", type=["csv"])

if arquivo is not None:
    df = pd.read_csv(arquivo, sep=",", encoding="latin1")

    st.subheader("Visão geral dos dados")
    st.write("Linhas no conjunto de dados:", len(df))
    st.dataframe(df.head())

    colunas_esperadas = ["IDADE", "obito", "SEXO", "DT_INTER", "RACA_COR"]
    faltantes = [c for c in colunas_esperadas if c not in df.columns]

    if faltantes:
        st.error(f"As seguintes colunas obrigatórias não foram encontradas no arquivo: {faltantes}")
    else:
        df["IDADE"] = pd.to_numeric(df["IDADE"], errors="coerce")
        df["obito"] = pd.to_numeric(df["obito"], errors="coerce")

        df = df.dropna(subset=["IDADE"])
        df = df.sort_values("IDADE")

        df_obitos = df.groupby("IDADE")["obito"].sum().reset_index()

        st.subheader("Óbitos por idade")

        col1, col2 = st.columns(2)

        with col1:
            fig_obitos = px.line(
                df_obitos,
                x="IDADE",
                y="obito",
                title="Quantidade de óbitos por idade",
                markers=True,
                template="plotly_white"
            )
            st.plotly_chart(fig_obitos, use_container_width=True)

        with col2:
            df_obitos_pontos = df[df["obito"] == 1].copy()
            df_obitos_pontos = df_obitos_pontos.sort_values("IDADE")
            df_obitos_pontos["ordem"] = df_obitos_pontos.groupby("IDADE").cumcount() + 1

            fig_obitos_pontos = px.scatter(
                df_obitos_pontos,
                x="IDADE",
                y="ordem",
                title="Distribuição de óbitos por idade",
                opacity=0.5,
                template="plotly_white"
            )
            fig_obitos_pontos.update_layout(
                xaxis_title="Idade",
                yaxis_title="Óbitos acumulados por idade",
                height=650
            )
            st.plotly_chart(fig_obitos_pontos, use_container_width=True)

        st.subheader("Gráfico de barras por raça")

        df_raca = df.copy()
        df_raca["RACA_COR_NUM"] = pd.to_numeric(df_raca["RACA_COR"], errors="coerce")

        df_raca["RACA_DESC"] = df_raca["RACA_COR_NUM"].map({
            1: "Branca",
            2: "Preta",
            3: "Parda",
            4: "Amarela",
            5: "Indígena",
            9: "Sem informação",
            99: "Sem informação"
        })

        df_raca["RACA_DESC"] = df_raca["RACA_DESC"].fillna("Sem informação")

        casos_por_raca = df_raca.groupby("RACA_DESC").size().reset_index(name="casos")

        ordem_raca = ["Branca", "Preta", "Parda", "Amarela", "Indígena", "Sem informação"]
        casos_por_raca["RACA_DESC"] = pd.Categorical(casos_por_raca["RACA_DESC"], categories=ordem_raca, ordered=True)
        casos_por_raca = casos_por_raca.sort_values("RACA_DESC")

        fig_raca = px.bar(
            casos_por_raca,
            x="RACA_DESC",
            y="casos",
            title="Número de casos por raça",
            color="RACA_DESC",
            template="plotly_white"
        )
        fig_raca.update_layout(xaxis_title="Raça", yaxis_title="Número de casos", showlegend=False)
        st.plotly_chart(fig_raca, use_container_width=True)

        st.subheader("Heatmap de casos por mês (2007-2023)")

        if "DT_INTER" in df.columns:
            df_dt = df.copy()
            df_dt["DT_INTER"] = pd.to_datetime(df_dt["DT_INTER"], errors="coerce")
            df_dt = df_dt.dropna(subset=["DT_INTER"])

            df_dt["ano"] = df_dt["DT_INTER"].dt.year
            df_dt["mes"] = df_dt["DT_INTER"].dt.month

            meses_nomes = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

            anos_disponiveis = sorted(df_dt["ano"].unique())

            for ano in anos_disponiveis:
                df_ano = df_dt[df_dt["ano"] == ano].copy()
                casos_por_mes = df_ano.groupby("mes").size().reset_index(name="casos")

                df_completo = pd.DataFrame({"mes": range(1, 13)})
                df_completo = df_completo.merge(casos_por_mes, on="mes", how="left")
                df_completo["casos"] = df_completo["casos"].fillna(0)
                df_completo["mes_nome"] = df_completo["mes"].apply(lambda x: meses_nomes[x - 1])

                fig_heat = go.Figure(data=go.Heatmap(
                    z=[df_completo["casos"].values],
                    x=df_completo["mes_nome"],
                    y=[""],
                    colorscale=[
                        [0.0, "#ebedf0"],
                        [0.2, "#c6e48b"],
                        [0.4, "#7bc96f"],
                        [0.6, "#239a3b"],
                        [0.8, "#196127"],
                        [1.0, "#0f3d1c"]
                    ],
                    showscale=True,
                    hoverongaps=False,
                    hovertemplate="Mês: %{x}<br>Casos: %{z}<extra></extra>",
                    colorbar=dict(title="Casos")
                ))
                fig_heat.update_layout(
                    title=f"Casos de Pneumonia - {ano}",
                    xaxis=dict(title="", side="bottom"),
                    yaxis=dict(title="", showticklabels=False),
                    height=150,
                    margin=dict(l=40, r=40, t=60, b=40),
                    template="plotly_white"
                )
                st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.warning("A coluna DT_INTER não foi encontrada no arquivo. O heatmap por ano não pôde ser gerado.")

        st.subheader("Pirâmide etária de casos por sexo")

        df_sexo = df.copy()
        df_sexo["SEXO_CAT"] = (
            df_sexo["SEXO"]
            .astype(str)
            .str.strip()
            .str.upper()
            .map({
                "M": "Homem",
                "MASCULINO": "Homem",
                "1": "Homem",
                "F": "Mulher",
                "FEMININO": "Mulher",
                "3": "Mulher"
            })
        )

        df_sexo = df_sexo.dropna(subset=["IDADE", "SEXO_CAT"])

        df_sexo["faixa"] = pd.cut(
            df_sexo["IDADE"],
            bins=list(range(0, 105, 5)) + [200],
            labels=[f"{i}-{i+4}" for i in range(0, 100, 5)] + ["100+"],
            right=False
        )

        piramide_total = df_sexo.groupby(["faixa", "SEXO_CAT"]).size().reset_index(name="casos")

        piramide_homem_total = piramide_total[piramide_total["SEXO_CAT"] == "Homem"].copy()
        piramide_mulher_total = piramide_total[piramide_total["SEXO_CAT"] == "Mulher"].copy()
        piramide_homem_total["casos_neg"] = -piramide_homem_total["casos"]

        fig_piramide_total = go.Figure()
        fig_piramide_total.add_trace(go.Bar(y=piramide_homem_total["faixa"], x=piramide_homem_total["casos_neg"], name="Homem", orientation="h", marker_color="#1f77b4"))
        fig_piramide_total.add_trace(go.Bar(y=piramide_mulher_total["faixa"], x=piramide_mulher_total["casos"], name="Mulher", orientation="h", marker_color="#e377c2"))
        fig_piramide_total.update_layout(title="Pirâmide etária de casos por sexo", barmode="overlay", xaxis_title="Número de casos", yaxis_title="Faixa etária", template="plotly_white")
        st.plotly_chart(fig_piramide_total, use_container_width=True)

        st.subheader("Pirâmide etária de óbitos por sexo")

        df_obito_sexo = df_sexo[df_sexo["obito"] == 1].copy()
        piramide_obito = df_obito_sexo.groupby(["faixa", "SEXO_CAT"]).size().reset_index(name="casos")

        piramide_homem_obito = piramide_obito[piramide_obito["SEXO_CAT"] == "Homem"].copy()
        piramide_mulher_obito = piramide_obito[piramide_obito["SEXO_CAT"] == "Mulher"].copy()
        piramide_homem_obito["casos_neg"] = -piramide_homem_obito["casos"]

        fig_piramide_obito = go.Figure()
        fig_piramide_obito.add_trace(go.Bar(y=piramide_homem_obito["faixa"], x=piramide_homem_obito["casos_neg"], name="Homem", orientation="h", marker_color="#1f77b4"))
        fig_piramide_obito.add_trace(go.Bar(y=piramide_mulher_obito["faixa"], x=piramide_mulher_obito["casos"], name="Mulher", orientation="h", marker_color="#e377c2"))
        fig_piramide_obito.update_layout(title="Pirâmide etária de óbitos por sexo", barmode="overlay", xaxis_title="Número de óbitos", yaxis_title="Faixa etária", template="plotly_white")
        st.plotly_chart(fig_piramide_obito, use_container_width=True)

else:
    st.info("Envie o arquivo pneumonia.csv para iniciar a análise.")
