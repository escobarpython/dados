import json
import os
import urllib.request

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Análise de Dados Hospitalares", layout="wide")

st.title("Análise de Dados Hospitalares: Visualização Interativa e Modelos Preditivos para Suporte à Gestão em Saúde")
st.markdown("feito por Pedro Escobar para o Programa de Iniciação Científica Júnior da PUCRS 2025")

arquivo = st.file_uploader("Envie o arquivo pneumonia.csv", type=["csv"])

def _groq_chat(api_key, model, messages, temperature=0.2, max_tokens=512):
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read()
    result = json.loads(body.decode("utf-8"))
    return result["choices"][0]["message"]["content"]


def _summarize_insights(df, df_obitos, df_obito_faixa, casos_por_raca, df_dt):
    total = len(df)
    obitos_total = int(df["obito"].sum()) if "obito" in df.columns else 0
    taxa_obito = (obitos_total / total) * 100 if total else 0

    idade_min = int(df["IDADE"].min()) if not df["IDADE"].empty else None
    idade_max = int(df["IDADE"].max()) if not df["IDADE"].empty else None
    idade_mediana = float(df["IDADE"].median()) if not df["IDADE"].empty else None

    faixa_top = None
    if df_obito_faixa is not None and not df_obito_faixa.empty:
        faixa_counts = (
            df_obito_faixa.groupby("faixa")
            .size()
            .reset_index(name="obitos")
            .sort_values("obitos", ascending=False)
        )
        faixa_top = faixa_counts.iloc[0]["faixa"]

    casos_raca_top = None
    if casos_por_raca is not None and not casos_por_raca.empty:
        casos_raca_top = (
            casos_por_raca.sort_values("casos", ascending=False)
            .iloc[0]["RACA_DESC"]
        )

    casos_por_sexo = {}
    if "SEXO_CAT" in df.columns:
        casos_por_sexo = (
            df["SEXO_CAT"]
            .value_counts(dropna=True)
            .to_dict()
        )

    obitos_por_sexo = {}
    if "SEXO_CAT" in df.columns and "obito" in df.columns:
        obitos_por_sexo = (
            df[df["obito"] == 1]["SEXO_CAT"]
            .value_counts(dropna=True)
            .to_dict()
        )

    ano_top = None
    mes_top = None
    if df_dt is not None and not df_dt.empty:
        casos_por_ano = df_dt.groupby("ano").size().reset_index(name="casos")
        if not casos_por_ano.empty:
            ano_top = int(casos_por_ano.sort_values("casos", ascending=False).iloc[0]["ano"])
        casos_por_mes = df_dt.groupby("mes").size().reset_index(name="casos")
        if not casos_por_mes.empty:
            mes_top = int(casos_por_mes.sort_values("casos", ascending=False).iloc[0]["mes"])

    return {
        "total_registros": total,
        "obitos_total": obitos_total,
        "taxa_obito_percentual": round(taxa_obito, 2),
        "idade_min": idade_min,
        "idade_max": idade_max,
        "idade_mediana": round(idade_mediana, 2) if idade_mediana is not None else None,
        "faixa_etaria_mais_obitos": str(faixa_top) if faixa_top is not None else None,
        "raca_mais_casos": str(casos_raca_top) if casos_raca_top is not None else None,
        "casos_por_sexo": casos_por_sexo,
        "obitos_por_sexo": obitos_por_sexo,
        "ano_com_mais_casos": ano_top,
        "mes_com_mais_casos": mes_top,
    }


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
        df["SEXO_CAT"] = (
            df["SEXO"]
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

        df_obitos = df.groupby("IDADE")["obito"].sum().reset_index()
        df_obito_faixa = None
        casos_por_raca = None
        df_dt = None

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
            fig_obitos.update_layout(height=500)
            st.plotly_chart(fig_obitos, use_container_width=True)

        with col2:
            df_sexo = df.dropna(subset=["SEXO_CAT"]).copy()

            df_sexo["faixa"] = pd.cut(
                df_sexo["IDADE"],
                bins=list(range(0, 105, 5)) + [200],
                labels=[f"{i}-{i+4}" for i in range(0, 100, 5)] + ["100+"],
                right=False
            )

            df_obito_faixa = df_sexo[df_sexo["obito"] == 1]

            obitos_faixa_sexo = (
                df_obito_faixa
                .groupby(["faixa", "SEXO_CAT"])
                .size()
                .reset_index(name="obitos")
            )

            fig_faixa = px.bar(
                obitos_faixa_sexo,
                x="faixa",
                y="obitos",
                color="SEXO_CAT",
                title="Óbitos por faixa etária e sexo",
                template="plotly_white"
            )

            fig_faixa.update_layout(
                xaxis_title="Faixa etária",
                yaxis_title="Número de óbitos",
                barmode="stack",
                height=500
            )

            st.plotly_chart(fig_faixa, use_container_width=True)

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

        df_sexo = df.dropna(subset=["IDADE", "SEXO_CAT"]).copy()

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

        st.subheader("Leitura automatizada dos gráficos (Groq)")

        col_ai1, col_ai2 = st.columns([2, 1])
        with col_ai1:
            st.caption("A chave sera lida de st.secrets ou da variavel GROQ_API_KEY.")
            user_focus = st.text_area(
                "Se quiser, descreva o foco da análise (opcional)",
                placeholder="Ex.: destaque diferenças por sexo e evolução temporal.",
            )
        with col_ai2:
            model_name = st.text_input("Modelo", value="llama3-70b-8192")
            max_tokens = st.number_input("Máx. tokens", min_value=128, max_value=2048, value=512, step=64)
            temp = st.slider("Temperatura", min_value=0.0, max_value=1.0, value=0.2, step=0.05)

        if st.button("Gerar leitura com Groq"):
            api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
            if not api_key:
                st.error("Defina GROQ_API_KEY em st.secrets ou como variavel de ambiente.")
            else:
                insights = _summarize_insights(df, df_obitos, df_obito_faixa, casos_por_raca, df_dt)
                system_msg = (
                    "Voce e um analista de dados em saude. "
                    "Resuma os resultados com linguagem clara, objetiva e acionavel. "
                    "Use PT-BR e formate em topicos curtos."
                )
                user_msg = {
                    "objetivo": "Leitura dos graficos para Streamlit",
                    "foco_usuario": user_focus or "Sem foco especifico",
                    "metricas": insights,
                }
                try:
                    resposta = _groq_chat(
                        api_key=api_key,
                        model=model_name,
                        messages=[
                            {"role": "system", "content": system_msg},
                            {"role": "user", "content": json.dumps(user_msg, ensure_ascii=False)},
                        ],
                        temperature=temp,
                        max_tokens=int(max_tokens),
                    )
                    st.markdown("**Resumo dos resultados**")
                    st.markdown(resposta)
                except Exception as exc:
                    st.error(f"Erro ao consultar Groq: {exc}")

else:
    st.info("Envie o arquivo pneumonia.csv para iniciar a análise.")
