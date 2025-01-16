import pandas as pd
import numpy as np
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime, timedelta


class AgriculturalAnalyzer:
    def __init__(self, data_manager):
        """
        Initialise l’analyseur avec le gestionnaire de données.

        Cette classe utilise les données historiques et actuelles
        pour générer des insights agronomiques pertinents.
        """
        self.data_manager = data_manager
        self.model = RandomForestRegressor(
            n_estimators=100,
            random_state=42
        )

    def analyze_yield_factors(self, parcelle_id):
        """
        Analyse les facteurs influençant les rendements.
        """
        # Filtrer les données de la parcelle
        parcelle_data = self.data_manager.monitoring_data[
            self.data_manager.monitoring_data['parcelle_id'] == parcelle_id
        ]
        weather_data = self.data_manager.weather_data
        soil_data = self.data_manager.soil_data[
            self.data_manager.soil_data['parcelle_id'] == parcelle_id
        ]

        # Fusionner les données
        combined_data = parcelle_data.merge(weather_data, on='date', how='inner')
        combined_data = combined_data.merge(soil_data, on='parcelle_id', how='left')

        # Ajouter les données de rendement
        combined_data = combined_data.merge(
            self.data_manager.yield_history[['parcelle_id', 'date', 'rendement_estime', 'rendement_final']],
            on=['parcelle_id', 'date'],
            how='left'
        )

        # Utiliser rendement_final si disponible, sinon rendement_estime
        combined_data['rendement'] = combined_data['rendement_final'].fillna(combined_data['rendement_estime'])
        
        # Supprimer les lignes avec des NaN dans la colonne rendement
        combined_data = combined_data.dropna(subset=['rendement'])

        # Vérifier la présence de la colonne rendement
        if 'rendement' not in combined_data.columns:
            raise KeyError("La colonne 'rendement' est manquante dans combined_data.")
        
        print("Colonnes après fusion avec rendement :", combined_data.columns)
        print("Aperçu des données fusionnées :", combined_data.head())

        # Extraire les caractéristiques et la cible
        X = combined_data.drop(['rendement', 'parcelle_id', 'date'], axis=1, errors='ignore')
        y = combined_data['rendement']

        # Vérifier la validité des données
        if X.empty or y.empty:
            raise ValueError("Les données pour l'analyse des facteurs sont vides.")
        print(f"Nombre de valeurs manquantes dans 'rendement': {y.isna().sum()}")

        # Identifier les colonnes non numériques
        non_numeric_cols = X.select_dtypes(include=['object']).columns
        print("Colonnes non numériques identifiées :", non_numeric_cols)

        # Encodage des colonnes catégoriques
        X = pd.get_dummies(X, columns=non_numeric_cols, drop_first=True)

        # Entraîner le modèle
        self.model.fit(X, y)
        feature_importance = pd.Series(self.model.feature_importances_, index=X.columns)
        return feature_importance.sort_values(ascending=False)



    def _calculate_yield_correlations(self, yield_data, weather_data, soil_data):
        """
        Calcule les corrélations entre les rendements et différents facteurs environnementaux.
        """
        # Fusionner les données
        combined_data = yield_data.merge(weather_data, on='date', how='inner')
        combined_data = combined_data.merge(soil_data, on='parcelle_id', how='left')
        
        # Exclure les colonnes non numériques
        numeric_columns = combined_data.select_dtypes(include=[np.number]).columns
        combined_data = combined_data[numeric_columns]
        
        # Vérifier que la colonne 'rendement' existe
        if 'rendement' not in combined_data.columns:
            raise KeyError("La colonne 'rendement' est manquante dans les données fusionnées.")
        
        # Calculer les corrélations
        correlations = combined_data.corr()
        return correlations


    def _identify_limiting_factors(self, parcelle_data, correlations):
        """
        Identifie les facteurs limitant le rendement.

        Cette analyse s’appuie sur la loi du minimum de Liebig
        pour identifier les ressources qui limitent potentiellement la croissance.
        """
        limiting_factors = correlations[correlations < 0.2]  # Seuil arbitraire
        return limiting_factors

    def _analyze_performance_trend(self, parcelle_data):
        """
        Analyse la tendance de performance de la parcelle.

        Examine l’évolution des rendements dans le temps et identifie les patterns significatifs.
        """
        trend = np.polyfit(parcelle_data['annee'], parcelle_data['rendement'], 1)
        return trend  # Coefficients de la tendance linéaire

    def _detect_yield_breakpoints(self, yield_series):
        """
        Détecte les changements significatifs dans la série temporelle des rendements.
        """
        breakpoints = []
        for i in range(1, len(yield_series) - 1):
            if abs(yield_series[i] - yield_series[i - 1]) > np.std(yield_series):
                breakpoints.append(i)
        return breakpoints

    def _analyze_yield_stability(self, yield_series):
        """
        Analyse la stabilité des rendements au fil du temps.

        Calcule plusieurs métriques de stabilité pour évaluer la résilience de la parcelle.
        """
        stability_metrics = {
            'mean': np.mean(yield_series),
            'std_dev': np.std(yield_series),
            'cv': np.std(yield_series) / np.mean(yield_series),  # Coefficient de variation
        }
        return stability_metrics

    def _calculate_stability_index(self, yield_series):
        """
        Calcule un index de stabilité personnalisé.

        Prend en compte la variabilité des rendements et leur tendance générale.
        """
        trend = np.polyfit(range(len(yield_series)), yield_series, 1)
        variability = np.std(yield_series)
        stability_index = trend[0] / (variability + 1e-5)  # Évite la division par zéro
        return stability_index

if __name__ == "__main__":
    from data_manager import AgriculturalDataManager  # Importez votre gestionnaire de données

    # Charger les données
    monitoring_file = r'C:\Users\PC\Documents\DSEF\projet_agricole\data\monitoring_cultures.csv'
    weather_file = r'C:\Users\PC\Documents\DSEF\projet_agricole\data\meteo_detaillee.csv'
    soil_file = r'C:\Users\PC\Documents\DSEF\projet_agricole\data\sols.csv'
    yield_file = r'C:\Users\PC\Documents\DSEF\projet_agricole\data\historique_rendements.csv'

    data_manager = AgriculturalDataManager()
    data_manager.load_data()

    # Instancier l'analyseur
    analyzer = AgriculturalAnalyzer(data_manager)

    # Tester l'analyse des facteurs de rendement pour une parcelle donnée
    parcelle_id = "P001"  # Remplacez par un ID de parcelle présent dans vos données
    print(f"Analyse des facteurs pour la parcelle {parcelle_id} :")
    feature_importance = analyzer.analyze_yield_factors(parcelle_id)
    print(feature_importance)

    # Tester d'autres méthodes
    print("Test des corrélations des rendements :")
    correlations = analyzer._calculate_yield_correlations(
        data_manager.yield_history, data_manager.weather_data, data_manager.soil_data
    )
    print(correlations)
