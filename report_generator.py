import subprocess
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

class AgriculturalReportGenerator:
    def __init__(self, analyzer, data_manager):
        """
        Initialise le générateur de rapports avec l’analyseur
        et le gestionnaire de données.
        """
        self.analyzer = analyzer
        self.data_manager = data_manager

    def generate_parcelle_report(self, parcelle_id):
        """
        Génère un rapport complet pour une parcelle donnée.

        Ce rapport combine les analyses historiques, l’état
        actuel et les recommandations pour l’avenir.
        """
        # Collecte des données pour la parcelle
        analysis = self.analyzer.analyze_yield_factors(parcelle_id)
        correlations = self.analyzer._calculate_yield_correlations(
            self.data_manager.yield_history,
            self.data_manager.weather_data,
            self.data_manager.soil_data
        )
        current_state = self.data_manager.monitoring_data[
            self.data_manager.monitoring_data['parcelle_id'] == parcelle_id
        ].iloc[-1]  # Dernier état connu pour la parcelle

        # Génération des figures
        self._generate_report_figures(parcelle_id, correlations)

        # Création du rapport Markdown
        markdown_content = self._create_markdown_report(parcelle_id, analysis, current_state)

        # Conversion en PDF
        self._convert_to_pdf(markdown_content, f"report_parcelle_{parcelle_id}.pdf")

    def _create_markdown_report(self, parcelle_id, analysis, current_state):
        """
        Crée le contenu du rapport en format Markdown.

        Le rapport est structuré en sections logiques pour
        faciliter la lecture et la compréhension.
        """
        markdown_content = f"""
# Rapport Agronomique - Parcelle {parcelle_id}

## 1. Analyse Historique
{self._format_historical_analysis(analysis)}

## 2. État Actuel
- Rendement Estimé : {current_state.get('rendement_estime', 'N/A')} t/ha
- Stress Hydrique : {current_state.get('stress_hydrique', 'N/A')}
- NDVI : {current_state.get('ndvi', 'N/A')}

## 3. Facteurs Limitants
{self._format_limiting_factors(analysis)}

## 4. Recommandations
{self._generate_recommendations(analysis, current_state)}

## Visualisations
- ![Évolution des Rendements](yield_evolution_{parcelle_id}.png)
- ![Matrice de Corrélation](correlation_matrix.png)
"""
        with open(f"report_parcelle_{parcelle_id}.md", "w") as f:
            f.write(markdown_content)
        return markdown_content

    def _generate_report_figures(self, parcelle_id, correlation_data):
        """
        Génère les visualisations pour le rapport.

        Crée plusieurs figures détaillées qui seront
        intégrées dans le rapport PDF final.
        """
        self._plot_yield_evolution(parcelle_id)
        self._plot_correlation_matrix(correlation_data)

    def _plot_yield_evolution(self, parcelle_id):
        """
        Crée un graphique détaillé de l’évolution des rendements.
        """
        data = self.data_manager.yield_history[
            self.data_manager.yield_history['parcelle_id'] == parcelle_id
        ]
        plt.figure(figsize=(10, 6))
        plt.plot(data['date'], data['rendement_final'], marker='o', label='Rendement Final')
        plt.title(f"Évolution des Rendements - Parcelle {parcelle_id}")
        plt.xlabel("Date")
        plt.ylabel("Rendement (t/ha)")
        plt.legend()
        plt.grid()
        plt.tight_layout()
        plt.savefig(f"yield_evolution_{parcelle_id}.png")
        plt.close()

    def _plot_correlation_matrix(self, correlation_data):
        """
        Crée une matrice de corrélation visuelle pour comprendre
        les relations entre les différentes variables agricoles.
        """
        print(f"Type de correlation_data : {type(correlation_data)}")
        print(f"Contenu de correlation_data :\n{correlation_data}")
        
        # Vérifiez si correlation_data est un DataFrame valide
        if correlation_data is None or not hasattr(correlation_data, 'shape'):
            raise ValueError("correlation_data est invalide ou vide.")
        
        # Vérifiez si correlation_data est carré
        if correlation_data.shape[0] != correlation_data.shape[1]:
            print(f"Dimensions de correlation_data : {correlation_data.shape}")
            raise ValueError("Matrice de corrélation invalide : elle doit être carrée.")
        
        # Générer la heatmap
        plt.figure(figsize=(12, 8))
        sns.heatmap(correlation_data, annot=True, cmap='coolwarm', fmt='.2f')
        plt.title("Matrice de Corrélation")
        plt.tight_layout()
        plt.savefig("correlation_matrix.png")
        plt.close()




    def _format_historical_analysis(self, analysis):
        """
        Formate l’analyse historique en un texte explicatif détaillé.
        """
        return "Cette section décrit les tendances historiques et les performances passées."

    def _format_limiting_factors(self, factors):
        """
        Transforme l’analyse des facteurs limitants en recommandations pratiques.
        """
        return "Les facteurs suivants limitent la performance : " + ", ".join(factors.index)

    def _generate_recommendations(self, analysis, current_state):
        """
        Génère des recommandations agronomiques basées sur
        l’analyse complète de la parcelle.
        """
        return "Basé sur les analyses, il est recommandé d'améliorer l'irrigation et la gestion des nutriments."

    def _convert_to_pdf(self, markdown_content, output_file):
        """
        Convertit le rapport Markdown en PDF en utilisant pandoc
        avec une mise en page professionnelle.
        """
        with open("temp_report.md", "w") as f:
            f.write(markdown_content)
        try:
            subprocess.run(
                ["pandoc", "temp_report.md", "-o", output_file, "--pdf-engine=xelatex"],
                check=True
            )
        except subprocess.CalledProcessError as e:
            print("Erreur lors de la conversion en PDF :", e)

if __name__ == "__main__":
    from data_manager import AgriculturalDataManager
    from analyzer import AgriculturalAnalyzer

    # Initialisez le gestionnaire de données et l'analyseur
    data_manager = AgriculturalDataManager()
    data_manager.load_data()
    analyzer = AgriculturalAnalyzer(data_manager)

    # Instanciez le générateur de rapports
    report_generator = AgriculturalReportGenerator(analyzer, data_manager)

    # Génération d'un rapport pour une parcelle spécifique
    parcelle_id = "P001"  # Remplacez par l'ID de parcelle que vous voulez tester
    report_generator.generate_parcelle_report(parcelle_id)
    print(f"Rapport généré pour la parcelle {parcelle_id}.")
