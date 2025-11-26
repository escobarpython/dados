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

    colunas_esperadas = ["IDADE", "obito", "DIAS_PERM", "VAL_TOT"]
    faltantes = [c for c in colunas_esperadas if c not in df.columns]

    if faltantes:
        st.error(f"As seguintes colunas obrigatórias não foram encontradas no arquivo: {faltantes}")
    else:
        df["IDADE"] = pd.to_numeric(df["IDADE"], errors="coerce")
        df["obito"] = pd.to_numeric(df["obito"], errors="coerce")
        df["DIAS_PERM"] = pd.to_numeric(df["DIAS_PERM"], errors="coerce")
        df["VAL_TOT"] = pd.to_numeric(df["VAL_TOT"], errors="coerce")

        df = df.dropna(subset=["IDADE"])
        df = df.sort_values("IDADE")

        df_obitos = df.groupby("IDADE")["obito"].sum().reset_index()
        df_dias = df.groupby("IDADE")["DIAS_PERM"].mean().reset_index()

        df_relacao = pd.merge(df_obitos, df_dias, on="IDADE", how="inner")

        df_val_idade = df.groupby("IDADE")["VAL_TOT"].sum().reset_index()
        df_val_dias = df.groupby("DIAS_PERM")["VAL_TOT"].sum().reset_index()

        st.subheader("Óbitos por idade e dias de permanência médios por idade")

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
            fig_dias = px.line(
                df_dias,
                x="IDADE",
                y="DIAS_PERM",
                title="Dias de permanência médios por idade"
            )
            st.plotly_chart(fig_dias, use_container_width=True)

        st.subheader("Dispersão dos óbitos e dias de permanência por idade")

        col3, col4 = st.columns(2)

        with col3:
            fig_obitos_disp = px.scatter(
                df_obitos,
                x="IDADE",
                y="obito",
                title="Dispersão de óbitos por idade"
            )
            st.plotly_chart(fig_obitos_disp, use_container_width=True)

        with col4:
            fig_dias_disp = px.scatter(
                df_dias,
                x="IDADE",
                y="DIAS_PERM",
                title="Dispersão dos dias de permanência por idade"
            )
            st.plotly_chart(fig_dias_disp, use_container_width=True)

        st.subheader("Relação entre óbitos e dias de permanência por idade")

        fig_linhas = go.Figure()
        fig_linhas.add_trace(go.Scatter(
            x=df_relacao["IDADE"],
            y=df_relacao["obito"],
            mode="lines",
            name="óbitos"
        ))
        fig_linhas.add_trace(go.Scatter(
            x=df_relacao["IDADE"],
            y=df_relacao["DIAS_PERM"],
            mode="lines",
            name="dias de permanência (média)"
        ))
        fig_linhas.update_layout(
            title="Relação entre óbitos e dias de permanência por idade",
            xaxis_title="idade",
            yaxis_title="valor"
        )
        st.plotly_chart(fig_linhas, use_container_width=True)

        fig_disp = go.Figure()
        fig_disp.add_trace(go.Scatter(
            x=df_relacao["IDADE"],
            y=df_relacao["obito"],
            mode="markers",
            name="óbitos"
        ))
        fig_disp.add_trace(go.Scatter(
            x=df_relacao["IDADE"],
            y=df_relacao["DIAS_PERM"],
            mode="markers",
            name="dias de permanência (média)"
        ))
        fig_disp.update_layout(
            title="Dispersão entre óbitos e dias de permanência por idade",
            xaxis_title="idade",
            yaxis_title="valor"
        )
        st.plotly_chart(fig_disp, use_container_width=True)

        st.subheader("VAL_TOT por idade e por dias de permanência")

        col5, col6 = st.columns(2)

        with col5:
            fig_val_idade = px.line(
                df_val_idade,
                x="IDADE",
                y="VAL_TOT",
                title="VAL_TOT por idade"
            )
            st.plotly_chart(fig_val_idade, use_container_width=True)

        with col6:
            fig_val_dias = px.line(
                df_val_dias,
                x="DIAS_PERM",
                y="VAL_TOT",
                title="VAL_TOT por dias de permanência"
            )
            st.plotly_chart(fig_val_dias, use_container_width=True)

            st.subheader("Heatmap da quantidade de casos por mês ao longo dos anos")

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
            casos_mes["mes_ano"] = casos_mes["mes_nome"] + casos_mes["ano"].astype(str)

            casos_mes = casos_mes.sort_values(["ano", "mes"])

            valores = [casos_mes["casos"].values]
            labels_x = casos_mes["mes_ano"].tolist()

            fig_heat_grande = px.imshow(
                valores,
                x=labels_x,
                y=[""],
                aspect="auto",
                labels=dict(x="mês e ano", y="", color="quantidade de casos"),
                color_continuous_scale="Greens",
                title="Heatmap de casos por mês de cada ano"
            )

            fig_heat_grande.update_xaxes(tickangle=90)

            st.plotly_chart(fig_heat_grande, use_container_width=True)

        else:
            st.warning("A coluna DT_INTER não foi encontrada no arquivo. O heatmap por mês e ano não pôde ser gerado.")

