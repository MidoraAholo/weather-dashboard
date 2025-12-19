"""Streamlit application (alternate entrypoint) for the Cambridge weather dashboard."""
from __future__ import annotations

import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Optional

from src.data_loader import load_cambridge_data, download_cambridge_data
from src.analysis import rolling_mean, estimate_trend, detect_heatwaves, detect_cold_spells, detect_droughts, get_monthly_records
from src.visualization import timeseries_plot, seasonal_boxplot, overlay_anomalies, save_fig_html


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    return load_cambridge_data(path)


def main():
    st.title("Tableau de bord météo — Station de Cambridge")
    st.sidebar.header("Chargement des données")
    url = st.sidebar.text_input("URL du fichier Cambridge (laisser vide si fichier local)")
    uploaded = st.sidebar.file_uploader("Ou chargez un fichier local", type=["txt", "csv"]) 

    data_path = None
    if uploaded is not None:
        # save to temporary file
        p = Path("data/uploaded_cambridge.txt")
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("wb") as f:
            f.write(uploaded.getvalue())
        data_path = str(p)
    elif url:
        try:
            p = download_cambridge_data(url, dest="data/cambridge.txt")
            data_path = p
        except Exception as exc:
            st.error(f"Erreur téléchargement: {exc}")
    else:
        # try default file
        default = Path("data/cambridge.txt")
        if default.exists():
            data_path = str(default)

    if not data_path:
        st.info("Aucune donnée chargée. Fournissez une URL ou un fichier local, ou placez `data/cambridge.txt`.")
        return

    df = load_data(data_path)
    st.success(f"Données chargées: {len(df)} enregistrements, colonnes: {', '.join(df.columns)}")

    st.sidebar.header("Filtres")
    vars = st.sidebar.multiselect("Variables à afficher", options=list(df.columns), default=[df.columns[0]])
    date_range = st.sidebar.date_input("Plage de dates", value=(df.index.min().date(), df.index.max().date()))
    rolling_days = st.sidebar.slider("Moyenne mobile (jours)", min_value=1, max_value=365, value=30)

    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])

    figs = []
    for var in vars:
        st.header(f"Variable: {var}")
        fig = timeseries_plot(df, var, start, end, rolling=rolling_days)
        st.plotly_chart(fig, use_container_width=True)
        figs.append(fig)
        # show seasonal boxplot
        st.subheader("Distribution saisonnière")
        box = seasonal_boxplot(df.loc[start:end], var)
        st.plotly_chart(box, use_container_width=True)
        # show records and trend
        rec = get_monthly_records(df.loc[start:end], var)
        st.write("Records:", rec)
        slope, p = estimate_trend(df.loc[start:end], var)
        st.write(f"Tendance (slope): {slope:.5f} (p={p})" if slope is not None else "Tendance: insuffisante")

    st.sidebar.header("Anomalies")
    if st.sidebar.checkbox("Détecter canicules") and vars:
        hw = detect_heatwaves(df.loc[start:end], var=vars[0])
        st.write(f"Canicules détectées ({len(hw)}):", hw)
        if hw:
            overlay_anomalies(figs[0], hw)
            st.plotly_chart(figs[0], use_container_width=True)

    if st.sidebar.checkbox("Détecter gelées") and vars:
        cs = detect_cold_spells(df.loc[start:end], var=vars[0])
        st.write(f"Gelées détectées ({len(cs)}):", cs)

    if st.sidebar.checkbox("Détecter sécheresses (par saison)"):
        dr = detect_droughts(df, prcp_var="PRCP")
        st.write(dr)

    # export
    st.sidebar.header("Export")
    if st.sidebar.button("Générer rapport HTML"):
        out = Path("reports/report.html")
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            from src.report import generate_html_report
            generate_html_report(figs, str(out), title="Rapport météo — Cambridge")
            st.success(f"Rapport HTML généré: {out}")
        except Exception as exc:
            st.error(f"Erreur génération rapport: {exc}")

    if st.sidebar.button("Générer PDF (wkhtmltopdf requis)") and figs:
        out_pdf = Path("reports/report.pdf")
        try:
            from src.report import generate_html_report, generate_pdf_report
            temp = Path("reports/_tmp_report.html")
            generate_html_report([figs[0]], str(temp))
            generate_pdf_report(str(temp), str(out_pdf))
            st.success(f"PDF généré: {out_pdf}")
        except Exception as exc:
            st.error(f"Erreur génération PDF: {exc}")


if __name__ == "__main__":
    main()
