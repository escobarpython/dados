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

        st.subheader("Heatmap de casos por dia da semana e mês (2007-2023)")

        if "DT_INTER" in df.columns:
            df_dt = df.copy()
            df_dt["DT_INTER"] = pd.to_datetime(df_dt["DT_INTER"], errors="coerce")
            df_dt = df_dt.dropna(subset=["DT_INTER"])

            df_dt["ano"] = df_dt["DT_INTER"].dt.year
            df_dt["mes"] = df_dt["DT_INTER"].dt.month
            df_dt["dia_semana"] = df_dt["DT_INTER"].dt.dayofweek  # 0=Mon, 6=Sun
            df_dt["dia_mes"] = df_dt["DT_INTER"].dt.day

            # Nomes dos dias da semana
            dias_semana_nomes = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            
            # Nomes dos meses
            meses_nomes = ["January", "February", "March", "April", "May", "June", 
                          "July", "August", "September", "October", "November", "December"]

            # Anos disponíveis
            anos_disponiveis = sorted(df_dt["ano"].unique())
            
            # Criar um heatmap para cada ano
            for ano in anos_disponiveis:
                df_ano = df_dt[df_dt["ano"] == ano].copy()
                
                # Criar matriz de heatmap (7 dias x ~365 dias)
                # Agrupar por data completa
                casos_por_data = df_ano.groupby("DT_INTER").size().reset_index(name="casos")
                
                # Criar todas as datas do ano
                data_inicio = pd.Timestamp(f"{ano}-01-01")
                data_fim = pd.Timestamp(f"{ano}-12-31")
                todas_datas = pd.date_range(start=data_inicio, end=data_fim, freq="D")
                
                # Criar DataFrame completo
                df_completo = pd.DataFrame({"DT_INTER": todas_datas})
                df_completo = df_completo.merge(casos_por_data, on="DT_INTER", how="left")
                df_completo["casos"] = df_completo["casos"].fillna(0)
                
                df_completo["dia_semana"] = df_completo["DT_INTER"].dt.dayofweek
                df_completo["semana_ano"] = df_completo["DT_INTER"].dt.isocalendar().week
                df_completo["mes"] = df_completo["DT_INTER"].dt.month
                
                # Criar matriz 7x52 (dia da semana x semana do ano)
                matriz_heat = df_completo.pivot_table(
                    index="dia_semana",
                    columns="semana_ano",
                    values="casos",
                    fill_value=0
                )
                
                # Criar labels para os meses (aproximadamente)
                semanas_por_mes = df_completo.groupby("mes")["semana_ano"].first().to_dict()
                
                # Criar figura com plotly
                fig_heat = go.Figure(data=go.Heatmap(
                    z=matriz_heat.values,
                    x=list(range(1, matriz_heat.shape[1] + 1)),
                    y=dias_semana_nomes,
                    colorscale="Greens",
                    showscale=True,
                    hoverongaps=False,
                    hovertemplate="Semana: %{x}<br>Dia: %{y}<br>Casos: %{z}<extra></extra>"
                ))
                
                # Adicionar linhas verticais para separar os meses
                shapes = []
                for mes, semana in semanas_por_mes.items():
                    if semana > 1:
                        shapes.append(dict(
                            type="line",
                            x0=semana - 0.5,
                            x1=semana - 0.5,
                            y0=-0.5,
                            y1=6.5,
                            line=dict(color="white", width=2)
                        ))
                
                # Criar annotations para os meses
                annotations = []
                for mes, semana in semanas_por_mes.items():
                    annotations.append(dict(
                        x=semana + 2,
                        y=-1,
                        text=meses_nomes[mes - 1],
                        showarrow=False,
                        xanchor="left",
                        yanchor="top"
                    ))
                
                fig_heat.update_layout(
                    title=f"Casos de Pneumonia - {ano}",
                    xaxis=dict(
                        title="",
                        showticklabels=False,
                        side="bottom"
                    ),
                    yaxis=dict(
                        title="",
                        autorange="reversed"
                    ),
                    shapes=shapes,
                    annotations=annotations,
                    height=250,
                    margin=dict(l=50, r=50, t=50, b=80)
                )
                
                st.plotly_chart(fig_heat, use_container_width=True)

        else:
            st.warning("A coluna DT_INTER não foi encontrada no arquivo. O heatmap por ano não pôde ser gerado.")
