from bokeh.layouts import column
from bokeh.models import ColumnDataSource, HoverTool, Select, CustomJS, LinearColorMapper, ColorBar
from bokeh.plotting import figure
from bokeh.io import show
from bokeh.models import DatetimeTickFormatter  
from bokeh.palettes import RdYlBu11 as palette
from data_manager import AgriculturalDataManager
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np


class AgriculturalDashboard:
    def __init__(self, data_manager):
        """
        Initialise le tableau de bord avec le gestionnaire de données.
        """
        self.data_manager = data_manager
        self.source = None
        self.hist_source = None
        self.selected_parcelle = None
        self.create_data_sources()

    def create_data_sources(self):
        """
        Prépare les sources de données pour Bokeh.
        """
        monitoring_data = self.data_manager.monitoring_data.reset_index()
        self.source = ColumnDataSource(monitoring_data)

        yield_history = self.data_manager.yield_history
        self.hist_source = ColumnDataSource(yield_history)

        # Vérifier et remplir les valeurs manquantes
        yield_history['rendement'] = yield_history['rendement'].fillna(method='bfill').fillna(method='ffill')
        yield_history['annee'] = pd.to_numeric(yield_history['annee'], errors='coerce')
        yield_history = yield_history.dropna(subset=['annee']).drop_duplicates(subset=['parcelle_id', 'annee'])
        self.hist_source = ColumnDataSource(yield_history)


    def create_yield_history_plot(self):
        """
        Crée un graphique montrant l’historique des rendements pour chaque parcelle
        """
        try:
            # Initialiser les données
            yield_data = self.hist_source.data
            parcelles = sorted(list(set(yield_data['parcelle_id'])))  # Liste des parcelles disponibles

            if not parcelles:
                raise ValueError("Aucune parcelle trouvée dans les données.")

            # Source dynamique pour filtrer les données
            filtered_source = ColumnDataSource(data={key: [] for key in yield_data.keys()})

            # Initialisation du graphique
            p = figure(
                title="Historique des Rendements par Parcelle",
                x_axis_type="datetime",
                height=400,
                tools="pan,wheel_zoom,box_zoom,reset,save",
            )

            # Ajouter la courbe et les points (initialement vide)
            p.line(
                x='annee',
                y='rendement',
                source=filtered_source,
                line_width=2,
                color="blue",
                legend_label="Rendement",
            )
            p.circle(
                x='annee',
                y='rendement',
                source=filtered_source,
                size=8,
                color="red",
                legend_label="Points de rendement",
            )

            # Ajouter les outils interactifs
            p.add_tools(HoverTool(
                tooltips=[
                    ("Parcelle", "@parcelle_id"),
                    ("Année", "@annee{%Y}"),
                    ("Rendement", "@rendement{0.2f} t/ha"),
                ],
                formatters={"@annee": "datetime"},
                mode="vline",
            ))

            p.legend.location = "top_left"
            p.xaxis.axis_label = "Année"
            p.yaxis.axis_label = "Rendement (t/ha)"

            # Widget de sélection
            select = Select(
                title="Sélectionnez une parcelle :",
                value=parcelles[0],  # Parcelle par défaut
                options=parcelles,
            )

            # Callback JavaScript pour mettre à jour les données affichées
            callback = CustomJS(
                args=dict(source=self.hist_source, filtered_source=filtered_source, select=select),
                code="""
                const data = source.data;
                const filtered = filtered_source.data;
                const selected_parcelle = select.value;

                // Réinitialiser les données filtrées
                for (let key in filtered) {
                    filtered[key] = [];
                }

                // Filtrer les données pour la parcelle sélectionnée
                for (let i = 0; i < data['parcelle_id'].length; i++) {
                    if (data['parcelle_id'][i] === selected_parcelle) {
                        for (let key in filtered) {
                            filtered[key].push(data[key][i]);
                        }
                    }
                }

                // Mettre à jour la source filtrée
                filtered_source.change.emit();
                """
            )
            select.js_on_change('value', callback)

            # Préremplir les données pour la parcelle initiale
            initial_parcelle = parcelles[0]
            filtered_source.data = {
                key: [val for i, val in enumerate(yield_data[key]) if yield_data['parcelle_id'][i] == initial_parcelle]
                for key in yield_data
            }

            return column(select, p)

        except Exception as e:
            print(f"Erreur lors de la création du graphique : {e}")
            return None

    def create_ndvi_temporal_plot(self):
        """
        Crée un graphique montrant l’évolution du NDVI avec des lignes uniquement.
        """
        try:
            ndvi_data = self.source.data
            parcelles = sorted(list(set(ndvi_data['parcelle_id'])))

            if not parcelles:
                raise ValueError("Aucune parcelle trouvée dans les données.")

            # Source de données dynamique
            filtered_source = ColumnDataSource(data={key: [] for key in ndvi_data.keys()})

            # Initialisation du graphique
            p = figure(
                title="Évolution du NDVI par Mois",
                x_axis_type="datetime",
                height=450,
                width=700,
                tools="pan,wheel_zoom,box_zoom,reset,save",
                background_fill_color="#f5f5f5",  # Couleur d'arrière-plan claire
            )

            # Tracer uniquement la ligne du NDVI
            p.line(
                x='date',
                y='ndvi',
                source=filtered_source,
                line_width=3,  # Épaisseur de ligne plus importante pour plus de clarté
                color="steelblue",  # Couleur de la ligne
                legend_label="NDVI",
            )

            # Ajouter les outils interactifs
            p.add_tools(HoverTool(
                tooltips=[
                    ("Parcelle", "@parcelle_id"),
                    ("Date", "@date{%F}"),
                    ("NDVI", "@ndvi{0.2f}"),
                ],
                formatters={"@date": "datetime"},
                mode="vline",
            ))

            # Améliorer la grille et les axes
            p.xgrid.grid_line_color = "lightgray"
            p.ygrid.grid_line_color = "lightgray"
            p.legend.location = "top_left"
            p.legend.label_text_font_size = "10pt"
            p.legend.label_text_font_style = "bold"
            p.xaxis.axis_label = "Date"
            p.xaxis.axis_label_text_font_size = "12pt"
            p.xaxis.major_label_text_font_size = "10pt"
            p.yaxis.axis_label = "NDVI"
            p.yaxis.axis_label_text_font_size = "12pt"
            p.yaxis.major_label_text_font_size = "10pt"

            # Widget de sélection
            select = Select(
                title="Sélectionnez une parcelle :",
                value=parcelles[0],
                options=parcelles,
            )

            # Callback JavaScript
            callback = CustomJS(
                args=dict(source=self.source, filtered_source=filtered_source, select=select),
                code="""
                const data = source.data;
                const filtered = filtered_source.data;
                const selected_parcelle = select.value;

                for (let key in filtered) {
                    filtered[key] = [];
                }

                for (let i = 0; i < data['parcelle_id'].length; i++) {
                    if (data['parcelle_id'][i] === selected_parcelle) {
                        for (let key in filtered) {
                            filtered[key].push(data[key][i]);
                        }
                    }
                }

                filtered_source.change.emit();
                """
            )
            select.js_on_change('value', callback)

            # Préremplir les données initiales
            initial_parcelle = parcelles[0]
            filtered_source.data = {
                key: [val for i, val in enumerate(ndvi_data[key]) if ndvi_data['parcelle_id'][i] == initial_parcelle]
                for key in ndvi_data
            }

            return column(select, p)

        except Exception as e:
            print(f"Erreur lors de la création du graphique NDVI : {e}")
            return None
        
    def create_yield_prediction_plot(self):
        """
        Crée un graphique interactif avec Bokeh pour les prédictions de rendements.
        """
        # Récupérer les données historiques
        yield_history = self.data_manager.yield_history
        grouped_data = yield_history.groupby("annee")["rendement_final"].mean().reset_index()

        # Vérification et conversion des années
        grouped_data["annee"] = pd.to_numeric(grouped_data["annee"], errors="coerce")
        grouped_data = grouped_data.dropna(subset=["annee"])
        grouped_data["annee"] = grouped_data["annee"].astype(int)

        # Préparer les données pour le modèle
        X = grouped_data["annee"].values.reshape(-1, 1)
        y = grouped_data["rendement_final"].values

        # Modèle de régression linéaire
        model = LinearRegression()
        model.fit(X, y)

        # Générer des prédictions pour les années futures
        future_years = np.arange(X[-1][0] + 1, X[-1][0] + 6).reshape(-1, 1)
        predictions = model.predict(future_years)

        # Fusionner données historiques et prédictions
        future_data = pd.DataFrame({"annee": future_years.flatten(), "rendement_final": predictions})
        combined_data = pd.concat([grouped_data, future_data])

        # Préparer les sources de données pour Bokeh
        source = ColumnDataSource(combined_data)
        future_source = ColumnDataSource(future_data)

        # Créer la figure Bokeh
        p = figure(
            title="Prédictions des Rendements Futurs",
            x_axis_label="Année",
            y_axis_label="Rendement (t/ha)",
            height=400,
            tools="pan,wheel_zoom,box_zoom,reset",
        )

        # Tracer les données historiques
        p.line(
            x="annee",
            y="rendement_final",
            source=source,
            line_width=2,
            color="blue",
            legend_label="Historique",
        )
        p.circle(
            x="annee",
            y="rendement_final",
            source=source,
            size=8,
            color="blue",
            legend_label="Historique",
        )

        # Tracer les prédictions futures
        p.line(
            x="annee",
            y="rendement_final",
            source=future_source,
            line_width=2,
            color="orange",
            legend_label="Prédictions",
        )
        p.square(
            x="annee",
            y="rendement_final",
            source=future_source,
            size=8,
            color="orange",
            legend_label="Prédictions",
        )

        # Ajouter un outil de survol
        hover = HoverTool(tooltips=[("Année", "@annee"), ("Rendement", "@rendement_final{0.2f}")])
        p.add_tools(hover)

        p.legend.location = "top_left"
        return p

        
    def create_stress_matrix(self):
        """
        Crée une matrice de stress combinant stress hydrique
        et conditions météorologiques
        """
        try:
            # Charger les données nécessaires
            monitoring_data = self.data_manager.monitoring_data
            source = ColumnDataSource(monitoring_data)

            # Initialisation du graphique
            p = figure(
                title="Matrice de Stress",
                x_axis_label="LAI (Indice de Surface Foliaire)",
                y_axis_label="Stress Hydrique",
                x_range=(monitoring_data['lai'].min(), monitoring_data['lai'].max()),
                y_range=(monitoring_data['stress_hydrique'].min(), monitoring_data['stress_hydrique'].max()),
                height=400,
            )

            # Ajouter des points
            p.circle(
                x="lai", y="stress_hydrique", size=8, 
                color="blue", source=source, legend_label="Stress"
            )

            # Ajouter des outils interactifs
            hover = HoverTool()
            hover.tooltips = [
                ("Date", "@date"),
                ("Parcelle", "@parcelle_id"),
                ("Stress Hydrique", "@stress_hydrique"),
                ("LAI", "@lai"),
            ]
            p.add_tools(hover)

            return p
        except Exception as e:
            print(f"Erreur lors de la création de la matrice de stress : {e}")
            return None

    def create_layout(self):
        """
        Crée la disposition du tableau de bord.
        """
        plots = [
            self.create_yield_history_plot(),
            self.create_ndvi_temporal_plot(),
            self.create_stress_matrix(),
            self.create_yield_prediction_plot()  # Assurez-vous que cette ligne est correcte
        ]

        # Filtrer les graphiques non valides (None)
        valid_plots = [plot for plot in plots if plot is not None]

        return column(*valid_plots)

# Exemple d'utilisation
if __name__ == "__main__":
    from data_manager import AgriculturalDataManager

    data_manager = AgriculturalDataManager()
    data_manager.load_data()

    dashboard = AgriculturalDashboard(data_manager)
    layout = dashboard.create_layout()
    show(layout)