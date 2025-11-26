import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Análise de Pneumonia", layout="wide")

st.title("Análise dos Casos de Pneumonia de 2007  -  2023 ")

arquivo = st.file_uploader("Envie o arquivo pneumonia.csv", type=["csv"])

if arquivo is not None:
    df = pd.read_csv(arquivo, sep=",", encoding="latin1")

    st.subheader("Visão geral dos dados")
    st.write("Linhas no conjunto de dados:", len(df))
    st.dataframe(df.head())

    colunas_esperadas = ["IDADE", "obito", "DIAS_PERM", "VAL_TOT"]
    faltantes = [c for c in colunas_esperadas if c not in df.columns]

    if faltantes:
        st.error(f"erro: nao há os arquivos necessarios: {faltantes}")
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

        df_val_idade = df.groupby("IDADE")["VAL_TOT"].mean().reset_index()
        df_val_dias = df.groupby("DIAS_PERM")["VAL_TOT"].mean().reset_index()

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
                title="VAL_TOT médio por idade"
            )
            st.plotly_chart(fig_val_idade, use_container_width=True)

        with col6:
            fig_val_dias = px.line(
                df_val_dias,
                x="DIAS_PERM",
                y="VAL_TOT",
                title="VAL_TOT médio por dias de permanência"
            )
            st.plotly_chart(fig_val_dias, use_container_width=True)

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
                df_completo["mes_nome"] = df_completo["mes"].apply(lambda x: meses_nomes[x-1])
                
                # Criar figura com plotly
                fig_heat = go.Figure(data=go.Heatmap(
                    z=[df_completo["casos"].values],  # Uma única linha
                    x=df_completo["mes_nome"],
                    y=[""],
                    colorscale="Greens",
                    showscale=True,
                    hoverongaps=False,
                    hovertemplate="Mês: %{x}<br>Casos: %{z}<extra></extra>",
                    colorbar=dict(title="Casos")
                ))
                
                fig_heat.update_layout(
                    title=f"Casos de Pneumonia - {ano}",
                    xaxis=dict(
                        title="",
                        side="bottom"
                    ),
                    yaxis=dict(
                        title="",
                        showticklabels=False
                    ),
                    height=150,
                    margin=dict(l=50, r=50, t=50, b=50)
                )
                
                st.plotly_chart(fig_heat, use_container_width=True)

        else:
            st.warning("A coluna DT_INTER não foi encontrada no arquivo. O heatmap por ano não pôde ser gerado.")
