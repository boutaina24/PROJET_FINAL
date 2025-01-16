import pandas as pd
import folium
from folium import plugins
from branca.colormap import LinearColormap
from sklearn.linear_model import LinearRegression
import numpy as np
from data_manager import AgriculturalDataManager

class AgriculturalMap:
    def __init__(self, data_manager):
        """
        Initialise la carte avec le gestionnaire de données.
        """
        self.data_manager = data_manager
        self.map = None
        self.yield_colormap = LinearColormap(
            colors=['red', 'yellow', 'green'],
            vmin=0,
            vmax=12  # Rendement maximum en tonnes/ha
        )

    def validate_columns(self, dataset, required_columns):
        """
        Vérifie si les colonnes nécessaires sont présentes dans un dataset.
        Ajoute des colonnes manquantes avec des valeurs par défaut si nécessaire.
        """
        for column in required_columns:
            if column not in dataset.columns:
                print(f"Colonne manquante ajoutée : {column}")
                dataset[column] = 0.0  # Valeur par défaut
        return dataset

    def create_base_map(self):
        """
        Crée la carte de base avec les couches appropriées.
        """
        monitoring_data = self.validate_columns(
            self.data_manager.monitoring_data, ['latitude', 'longitude']
        )
        center_lat = monitoring_data['latitude'].mean()
        center_lon = monitoring_data['longitude'].mean()

        # Initialiser la carte
        self.map = folium.Map(location=[center_lat, center_lon], zoom_start=12)

    def add_yield_history_layer(self):
        """
        Ajoute une couche visualisant l’historique des rendements.
        """
        yield_history = self.validate_columns(
            self.data_manager.yield_history, ['latitude', 'longitude', 'rendement']
        )

        # Validation des valeurs de rendement
        yield_history['rendement'] = yield_history['rendement'].apply(
            lambda x: max(0, min(x, 12)) if pd.notnull(x) else 0
        )

        for _, row in yield_history.iterrows():
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=8,
                color=self.yield_colormap(row['rendement']),
                fill=True,
                fill_opacity=0.6,
                popup=f"Parcelle: {row['parcelle_id']}<br>Rendement: {row['rendement']} t/ha"
            ).add_to(self.map)

    def add_current_ndvi_layer(self):
        """
        Ajoute une couche de la situation NDVI actuelle.
        """
        monitoring_data = self.validate_columns(
            self.data_manager.monitoring_data, ['latitude', 'longitude', 'ndvi']
        )
        for _, row in monitoring_data.iterrows():
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=6,
                color='blue',
                fill=True,
                fill_opacity=0.5,
                popup=f"Parcelle: {row['parcelle_id']}<br>NDVI: {row['ndvi']}"
            ).add_to(self.map)

    def add_risk_heatmap(self):
        """
        Ajoute une carte de chaleur des zones à risque.
        """
        try:
            monitoring_data = self.validate_columns(
                self.data_manager.monitoring_data, ['latitude', 'longitude', 'risk_score']
            )
            risk_data = monitoring_data[['latitude', 'longitude', 'risk_score']].dropna()
            heat_data = [[row['latitude'], row['longitude'], row['risk_score']] for _, row in risk_data.iterrows()]
            plugins.HeatMap(heat_data, radius=15, max_zoom=13).add_to(self.map)
        except ValueError as e:
            print(f"Erreur : {e}")

    def save_map(self, file_name="agricultural_map.html"):
        """
        Sauvegarde la carte dans un fichier HTML.
        """
        self.map.save(file_name)

if __name__ == "__main__":
    # Charger les données à partir des fichiers fournis
    monitoring_file = '/mnt/data/monitoring_cultures.csv'
    weather_file = '/mnt/data/meteo_detaillee.csv'
    soil_file = '/mnt/data/sols.csv'
    yield_file = '/mnt/data/historique_rendements.csv'

    data_manager = AgriculturalDataManager(
        monitoring_file, weather_file, soil_file, yield_file
    )
    data_manager.load_data()

    # Initialiser la carte
    agri_map = AgriculturalMap(data_manager)
    agri_map.create_base_map()
    agri_map.add_yield_history_layer()
    agri_map.add_current_ndvi_layer()
    agri_map.add_risk_heatmap()

    # Sauvegarder et afficher la carte
    agri_map.save_map("agricultural_map.html")
    print("La carte a été générée et sauvegardée sous 'agricultural_map.html'.")
