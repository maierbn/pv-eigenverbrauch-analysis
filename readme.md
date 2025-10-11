# PV-Anlagen und Batteriespeicher Analyse

Dieses Repository enthält eine Simulation und Optimierung von Photovoltaik-Anlagen mit Batteriespeicher für ein Gebäude in Waiblingen.

## Hauptanalyse

Die vollständige Analyse befindet sich im Jupyter Notebook: **[compact_analysis.ipynb](compact_analysis.ipynb)**

Das Notebook führt folgende Analysen durch:
- PV-Batterie Grundsimulation mit realen Wetterdaten (2005-2023)
- Batteriekapazitäts-Optimierung (0-80 kWh)
- Ost-West Ausrichtungs-Optimierung für maximalen Eigenverbrauch

## Datenquellen

- Wetterdaten: PVGIS Hourly API
- Verbrauchsdaten: Open Power System Data
- Referenzwerte: Statistisches Bundesamt

## Verwendung

Öffnen Sie `compact_analysis.ipynb` in Jupyter Notebook oder JupyterLab und führen Sie die Zellen der Reihe nach aus.