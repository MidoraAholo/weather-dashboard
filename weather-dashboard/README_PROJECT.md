# Weather Dashboard — Cambridge Station

## Lancer l'application

1. Installer dépendances : `pip install -r requirements.txt`
2. Placer `cambridge.txt` dans `data/` ou fournir une URL dans l'interface
3. Lancer : `streamlit run src/app_streamlit.py`

## Structure
- `src/data_loader.py` - parsing et nettoyage
- `src/analysis.py` - mesures et détection d'anomalies
- `src/visualization.py` - fonctions Plotly
- `src/report.py` - export HTML/PDF
- `src/app_streamlit.py` - application Streamlit
- `tests/` - tests unitaires

## Remarques
- Pour générer un PDF, installez `wkhtmltopdf` et `pdfkit`.
- Améliorations possibles : support multi-stations, API Flask, CI, rapports avancés.
