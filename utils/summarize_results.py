import os
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go

class SolarResultsAnalyzer:
    def __init__(self, results_dir, datetime_rt):
        self.results_dir = results_dir
        self.datetime_rt = datetime_rt
        self.results_file = os.path.join(results_dir, datetime_rt, "results.csv")
        self.plot_dir = os.path.join(results_dir, datetime_rt)
        os.makedirs(self.plot_dir, exist_ok=True)
        self.distances = None
        self.results_df = None

    def load_results(self):
        """Load results CSV into a DataFrame."""
        self.results_df = pd.read_csv(self.results_file)
        self.distances = self.results_df["distance_miles"]

    def calculate_statistics(self):
        """Calculate basic stats, percentiles, and percent below thresholds."""
        distances = self.distances
        stats = {
            "mean": distances.mean(),
            "median": distances.median(),
            "mode": distances.mode()[0],
            "std": distances.std(),
            "variance": distances.var(),
            "min": {
                "distance": distances.min(),
                "location": self.results_df.loc[distances.idxmin()]["location"]
            },
            "max": {
                "distance": distances.max(),
                "location": self.results_df.loc[distances.idxmax()]["location"]
            },
            "percentiles": distances.quantile([0.1, 0.25, 0.5, 0.75, 0.9, 0.95]).to_dict(),
            "percent_below_thresholds (meters)": {t: float((distances < t).mean() * 100) 
                                                  for t in [1, 10, 50, 100, 1000, 
                                                            3000, 5000, 10000, 25000, 50000]},
        }
        return stats

    def save_json(self, summary_dict):
        """Save summary dictionary as JSON."""
        json_file = os.path.join(self.plot_dir, "summary.json")
        with open(json_file, "w") as f:
            json.dump(summary_dict, f, indent=4)

    def plot_histogram(self):
        """Generate and save an interactive histogram of distances using Plotly."""
        fig = px.histogram(self.distances, nbins=30, title="Distance Distribution",
                           labels={"value": "Distance (miles)"})
        fig.update_layout(xaxis_title="Distance (miles)", yaxis_title="Frequency")
        fig.write_html(os.path.join(self.plot_dir, "distance_histogram.html"))

    def plot_boxplot(self):
        """Generate and save an interactive boxplot of distances using Plotly."""
        fig = go.Figure()
        fig.add_trace(go.Box(x=self.distances, boxpoints='all', jitter=0.5, pointpos=-1.8))
        fig.update_layout(title="Distance Boxplot", xaxis_title="Distance (miles)")
        fig.write_html(os.path.join(self.plot_dir, "distance_boxplot.html"))

    def summarize(self):
        """Run the full analysis: load, calculate stats, save JSON, and plot."""
        self.load_results()
        stats = self.calculate_statistics()
        self.save_json(stats)
        self.plot_histogram()
        self.plot_boxplot()
