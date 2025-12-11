import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Análise de internações", layout="wide")

st.title("Análise de internações por pneumonia")

arquivo = st.file_uploader("Envie o arquivo pneumonia.csv", type=["csv"])

if arquivo is not None:
    df = pd.read_csv(arquivo, sep=",", encoding="latin1")

    st.subheader("Visão geral dos dados")
    st.write("Linhas no conjunto de dados:", len(df))
    st.dataframe(df.head())

    colunas_esperadas = ["IDADE", "obito", "SEXO"]
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
                title="Quantidade de óbitos por idade"
            )
            st.plotly_chart(fig_obitos, use_container_width=True)

        with col2:
            fig_obitos_disp = px.scatter(
                df_obitos,
                x="IDADE",
                y="obito",
                title="Dispersão de óbitos por idade"
            )
            st.plotly_chart(fig_obitos_disp, use_container_width=True)

        st.subheader("Heatmap da quantidade de casos por mês e ano")

        if "DT_INTER" in df.columns:
            df_dt = df.copy()
            df_dt["DT_INTER"] = pd.to_datetime(df_dt["DT_INTER"], errors="coerce")
            df_dt = df_dt.dropna(subset=["DT_INTER"])

            df_dt["ano"] = df_dt["DT_INTER"].dt.year
            df_dt["mes"] = df_dt["DT_INTER"].dt.month

            casos_mes = df_dt.groupby(["ano", "mes"]).size().reset_index(name="casos")

            meses_label = {
                1: "JAN",
                2: "FEV",
                3: "MAR",
                4: "ABR",
                5: "MAI",
                6: "JUN",
                7: "JUL",
                8: "AGO",
                9: "SET",
                10: "OUT",
                11: "NOV",
                12: "DEZ"
            }

            casos_mes["mes_nome"] = casos_mes["mes"].map(meses_label)

            matriz = casos_mes.pivot(index="ano", columns="mes_nome", values="casos")

            ordem_meses = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
            matriz = matriz.reindex(columns=ordem_meses)
            matriz = matriz.fillna(0)

            fig_heat = px.imshow(
                matriz,
                x=ordem_meses,
                y=matriz.index.astype(int),
                aspect="auto",
                labels=dict(x="mês", y="ano", color="quantidade de casos"),
                color_continuous_scale="Greens",
                title="Heatmap de casos por mês e ano"
            )

            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.warning("A coluna DT_INTER não foi encontrada no arquivo. O heatmap por mês e ano não pôde ser gerado.")

        st.subheader("Pirâmide etária de número de casos por sexo (faixas de 5 anos)")

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

        piramide_total = (
            df_sexo
            .groupby(["faixa", "SEXO_CAT"])
            .size()
            .reset_index(name="casos")
        )

        piramide_homem_total = piramide_total[piramide_total["SEXO_CAT"] == "Homem"].copy()
        piramide_mulher_total = piramide_total[piramide_total["SEXO_CAT"] == "Mulher"].copy()

        piramide_homem_total["casos_neg"] = -piramide_homem_total["casos"]

        fig_piramide_total = go.Figure()

        fig_piramide_total.add_trace(
            go.Bar(
                y=piramide_homem_total["faixa"],
                x=piramide_homem_total["casos_neg"],
                name="Homem",
                orientation="h"
            )
        )

        fig_piramide_total.add_trace(
            go.Bar(
                y=piramide_mulher_total["faixa"],
                x=piramide_mulher_total["casos"],
                name="Mulher",
                orientation="h"
            )
        )

        fig_piramide_total.update_layout(
            title="Pirâmide etária de casos por sexo (faixas de 5 anos)",
            barmode="overlay",
            xaxis_title="Número de casos",
            yaxis_title="Faixa etária"
        )

        st.plotly_chart(fig_piramide_total, use_container_width=True)

        st.subheader("Pirâmide etária de óbitos por sexo (faixas de 5 anos)")

        df_obito_sexo = df_sexo[df_sexo["obito"] == 1].copy()

        piramide_obito = (
            df_obito_sexo
            .groupby(["faixa", "SEXO_CAT"])
            .size()
            .reset_index(name="casos")
        )

        piramide_homem_obito = piramide_obito[piramide_obito["SEXO_CAT"] == "Homem"].copy()
        piramide_mulher_obito = piramide_obito[piramide_obito["SEXO_CAT"] == "Mulher"].copy()

        piramide_homem_obito["casos_neg"] = -piramide_homem_obito["casos"]

        fig_piramide_obito = go.Figure()

        fig_piramide_obito.add_trace(
            go.Bar(
                y=piramide_homem_obito["faixa"],
                x=piramide_homem_obito["casos_neg"],
                name="Homem",
                orientation="h"
            )
        )

        fig_piramide_obito.add_trace(
            go.Bar(
                y=piramide_mulher_obito["faixa"],
                x=piramide_mulher_obito["casos"],
                name="Mulher",
                orientation="h"
            )
        )

        fig_piramide_obito.update_layout(
            title="Pirâmide etária de óbitos por sexo (faixas de 5 anos)",
            barmode="overlay",
            xaxis_title="Número de óbitos",
            yaxis_title="Faixa etária"
        )

        st.plotly_chart(fig_piramide_obito, use_container_width=True)

else:
    st.info("Envie o arquivo pneumonia.csv para iniciar a análise.")
