import streamlit as st
import streamlit.components.v1 as components
from bokeh.embed import file_html
from bokeh.resources import CDN
from bokeh.layouts import column
from data_manager import AgriculturalDataManager
from dashboard import AgriculturalDashboard
from map_visualization import AgriculturalMap


class IntegratedDashboard:
    def __init__(self, data_manager):
        """
        Crée un tableau de bord intégré combinant graphiques Bokeh et carte Folium
        """
        self.data_manager = data_manager
        self.bokeh_dashboard = AgriculturalDashboard(data_manager)
        self.map_view = AgriculturalMap(data_manager)

    def initialize_visualizations(self):
        """
        Initialise toutes les composantes visuelles
        """
        # Charger les données nécessaires
        self.data_manager.load_data()

        # Initialiser la carte Folium
        self.map_view.create_base_map()
        self.map_view.add_yield_history_layer()
        self.map_view.add_current_ndvi_layer()
        self.map_view.add_risk_heatmap()

    def create_streamlit_dashboard(self):
        """
        Crée une interface Streamlit intégrant toutes les visualisations
        """
        st.title("Tableau de Bord Agricole Intégré")

        # Sélection de la parcelle
        parcelle_options = self.data_manager.monitoring_data['parcelle_id'].unique()
        selected_parcelle = st.selectbox("Sélectionnez une parcelle", parcelle_options)

        # Afficher les graphiques Bokeh
        st.subheader("Visualisations Bokeh")
        try:
            bokeh_layout = self.bokeh_dashboard.create_layout()
            bokeh_html = file_html(bokeh_layout, CDN, "Tableau de Bord Agricole")
            components.html(bokeh_html, height=1700)
        except Exception as e:
            st.error(f"Erreur lors de la génération des graphiques Bokeh : {e}")
            print(f"Erreur Bokeh : {e}")

        # Afficher la carte Folium
        st.subheader("Carte Interactive Folium")
        try:
            self.map_view.save_map("agricultural_map_temp.html")
            with open("agricultural_map_temp.html", "r", encoding="utf-8") as f:
                map_html = f.read()
            components.html(map_html, height=600)
        except Exception as e:
            st.error(f"Erreur lors de la génération de la carte Folium : {e}")
            print(f"Erreur Folium : {e}")

        # Mettre à jour les visualisations en fonction de la parcelle sélectionnée
        self.update_visualizations(selected_parcelle)

    def update_visualizations(self, parcelle_id):
        """
        Met à jour toutes les visualisations pour une parcelle donnée.
        """
        print(f"Visualisations mises à jour pour la parcelle {parcelle_id}")

    def setup_interactions(self):
        """
        Configure les interactions entre les composantes
        """
        # Configurer les interactions (exemple de lien entre les composants Streamlit)
        st.sidebar.write("Interactions en cours de développement...")

    def handle_parcelle_selection(self, attr, old, new):
        """
        Gère la sélection d’une nouvelle parcelle
        """
        self.update_visualizations(new)

    def handle_map_hover(self, feature):
        """
        Gère le survol d’une parcelle sur la carte
        """
        parcelle_id = feature.get("parcelle_id")
        if parcelle_id:
            print(f"Survol de la parcelle {parcelle_id}")

# Exemple d'utilisation
if __name__ == "__main__":
    data_manager = AgriculturalDataManager()

    # Vérifier si les données sont correctement chargées
    print("Chargement des données...")
    data_manager.load_data()

    if data_manager.yield_history is None or data_manager.yield_history.empty:
        raise ValueError("Yield History data is not loaded or is empty. Check the input files.")

    print("Initialisation du tableau de bord...")
    dashboard = IntegratedDashboard(data_manager)

    # Initialiser les visualisations
    print("Initialisation des visualisations...")
    dashboard.initialize_visualizations()

    # Créer le tableau de bord Streamlit
    print("Création du tableau de bord Streamlit...")
    dashboard.create_streamlit_dashboard()