import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.seasonal import seasonal_decompose
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings("ignore")

class AgriculturalDataManager:
    def __init__(self, monitoring_file=None, weather_file=None, soil_file=None, yield_file=None):
        """
        Initialize the agricultural data manager with optional file paths.
        """
        self.monitoring_file = monitoring_file
        self.weather_file = weather_file
        self.soil_file = soil_file
        self.yield_file = yield_file
        self.monitoring_data = None
        self.weather_data = None
        self.soil_data = None
        self.yield_history = None

    def load_data(self):
        """Load all necessary datasets"""
        self.monitoring_data = pd.read_csv(r'C:\Users\PC\Documents\DSEF\projet_agricole\data\monitoring_cultures.csv', parse_dates=["date"])
        self.weather_data = pd.read_csv(r'C:\Users\PC\Documents\DSEF\projet_agricole\data\meteo_detaillee.csv', parse_dates=["date"])
        self.soil_data = pd.read_csv(r'C:\Users\PC\Documents\DSEF\projet_agricole\data\sols.csv')
        self.yield_history = pd.read_csv(r'C:\Users\PC\Documents\DSEF\projet_agricole\data\historique_rendements.csv', parse_dates=["date"])

        # Extract 'annee' and process yields
        self.yield_history["annee"] = self.yield_history["date"].dt.year
        self.yield_history["rendement"] = pd.to_numeric(self.yield_history["rendement_final"], errors="coerce")

    def prepare_features(self):
        """Merge monitoring, weather, and soil data"""
        # Assurez-vous que les données sont triées par date
        self.monitoring_data.sort_index(inplace=True)
        self.weather_data.sort_index(inplace=True)

        # Merge monitoring and weather data
        data = pd.merge_asof(
            self.monitoring_data,
            self.weather_data,
            left_index=True,
            right_index=True,
            direction="nearest"
        )

        # Add soil data
        data = data.merge(self.soil_data, how="left", on="parcelle_id")

        # Vérifier les valeurs manquantes après la fusion
        missing = data.isnull().sum().sum()
        if missing > 0:
            print(f"Warning: {missing} missing values detected after merging.")
            data.fillna(method="ffill", inplace=True)

        return data

    def _enrich_with_yield_history(self, data):
        """Enrich current data with historical yield information"""
        enriched_data = data.merge(
            self.yield_history[["parcelle_id", "annee", "rendement"]],
            how="left",
            on="parcelle_id"
        )
        # Add historical average yield
        enriched_data["rendement_moyen"] = enriched_data.groupby("parcelle_id")["rendement"].transform("mean")
        return enriched_data

    def calculate_risk_metrics(self, data):
        """Calculate hydric and global risk metrics"""
        data["risque_hydrique"] = data["stress_hydrique"] / (data["capacite_retention_eau"] + 1e-6)
        data["risque_global"] = (
            0.5 * data["risque_hydrique"] +
            0.3 * (1 - data["ndvi"]) +
            0.2 * (1 - data["rendement_moyen"] / (data["rendement_moyen"].max() + 1e-6))
        )
        return data[["parcelle_id", "risque_hydrique", "risque_global"]]

    def analyze_yield_patterns(self, parcelle_id):
        """Analyze yield patterns for a specific parcel"""
        # Filtrer les données pour la parcelle spécifique
        history = self.yield_history[self.yield_history["parcelle_id"] == parcelle_id].copy()

        if history.empty:
            print(f"No data found for parcel {parcelle_id}.")
            return None

        if len(history) < 3:
            print(f"Not enough data for parcel {parcelle_id} to perform analysis.")
            return None

        # Gérer les valeurs manquantes
        if history["rendement"].isnull().sum() > 0:
            print(f"Filling missing values for parcel {parcelle_id}.")
            history["rendement"] = history["rendement"].interpolate(method="linear", limit_direction="both")
            history["rendement"].fillna(history["rendement"].mean(), inplace=True)

        # Définir l'index temporel
        history.set_index("date", inplace=True)

        # Appliquer la décomposition saisonnière
        decomposition = seasonal_decompose(history["rendement"], model="additive", period=12)
        trend = decomposition.trend
        seasonal = decomposition.seasonal
        resid = decomposition.resid

        # Calculer la pente de la tendance et la variation résiduelle moyenne
        valid_trend = trend.dropna()
        slope = np.polyfit(range(len(valid_trend)), valid_trend.values, 1)[0]
        variation_mean = resid.std() / history["rendement"].mean()

        return {
            "trend": trend,
            "seasonal": seasonal,
            "resid": resid,
            "slope": slope,
            "variation_mean": variation_mean
        }

    def plot_yield_decomposition(self, patterns):
        """Plot yield decomposition"""
        if not patterns:
            print("No patterns to plot.")
            return
        plt.figure(figsize=(10, 6))

        plt.subplot(3, 1, 1)
        patterns["trend"].plot(title="Trend", ylabel="Yield")

        plt.subplot(3, 1, 2)
        patterns["seasonal"].plot(title="Seasonality", ylabel="Yield")

        plt.subplot(3, 1, 3)
        patterns["resid"].plot(title="Residuals", ylabel="Yield")

        plt.tight_layout()
        plt.show()


# Example usage
data_manager = AgriculturalDataManager()
data_manager.load_data()

# Prepare features and enrich with yield history
features = data_manager.prepare_features()
enriched_features = data_manager._enrich_with_yield_history(features)

# Calculate risk metrics
risk_metrics = data_manager.calculate_risk_metrics(enriched_features)
print(risk_metrics.head())

# Analyze patterns for a specific parcel
parcelle_id = "P001"
patterns = data_manager.analyze_yield_patterns(parcelle_id)
if patterns:
    print(f"Trend slope: {patterns['slope']:.2f} tonnes/ha/year")
    print(f"Average residual variation: {patterns['variation_mean'] * 100:.1f}%")
    data_manager.plot_yield_decomposition(patterns)