import statistics
import numpy as np
import matplotlib.pyplot as plt
import os
import plotly.express as px
import plotly.graph_objects as go

def write_stats(timestamp, runtime="unavailable"):
    """
    Writes statistics of the results of a test to a file.

    Parameters
    ----------
    timestamp : str
        A timestamp to identify the test results.
    runtime : str, optional
        The total runtime of the test in seconds. Defaults to "unavailable".
    """
    def extract_values(filename):
        """
        Extracts the mean, median, minimum, and maximum values from a file.

        Parameters
        ----------
        filename : str
            The name of the file to extract the values from.

        Returns
        -------
        mean_values : list of float
            A list of mean values extracted from the file.
        median_values : list of float
            A list of median values extracted from the file.
        minimum_values : list of float
            A list of minimum values extracted from the file.
        maximum_values : list of float
            A list of maximum values extracted from the file.
        """
        mean_values = []
        median_values = []
        minimum_values = []
        maximum_values = []
        with open(filename, 'r') as file:
            for line in file:
                if "Maximum:" in line:
                    # Extract the maximum value from the line
                    maximum_value = float(line.split("Maximum:")[1].strip())
                    maximum_values.append(maximum_value)
                elif "Mean:" in line:
                    # Extract the mean value from the line
                    mean_value = float(line.split("Mean:")[1].strip())
                    mean_values.append(mean_value)
                elif "Median:" in line:
                    # Extract the median value from the line
                    median_value = float(line.split("Median:")[1].strip())
                    median_values.append(median_value)
                elif "Minimum:" in line:
                    # Extract the minimum value from the line
                    minimum_value = float(line.split("Minimum:")[1].strip())
                    minimum_values.append(minimum_value)
        return mean_values, median_values, minimum_values, maximum_values

    def plot_histograms(values, title, filename):
        """
        Plots a histogram of a set of values using Plotly and adds statistics annotations.

        Parameters
        ----------
        values : list of float
            A list of values to plot the histogram for.
        title : str
            A title to describe the values (e.g. "Means", "Medians", etc.)
        filename : str
            A filename to save the plot to.

        Returns
        -------
        None
        """
        if values:
            max_value = max(values)
            bins = np.arange(0, max_value + 100, 100)
                 
            # Calculate percentiles
            percentiles = [np.percentile(values, p) for p in [95, 90, 85, 80]]
            
            # Create the histogram trace
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=values, xbins=dict(start=0, end=max_value, size=100), 
                                    marker_color='#1f77b4', opacity=0.75, name='Histogram'))
            
            # Update layout
            fig.update_layout(
                title=f'Histogram of {title} with 100-Step Bins',
                xaxis_title='Distance from intended target in miles',
                yaxis_title='Frequency',
                xaxis=dict(tickvals=bins, ticktext=[str(b) for b in bins], tickangle=90, tickfont=dict(size=10)),
                bargap=0.1,
                bargroupgap=0.1,
                showlegend=True,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                autosize=False,
                width=900,
                height=600
            )
            
            
            # Add annotations for percentiles with staggered heights
            for i, (percentile, p_value) in enumerate(zip([95, 90, 85, 80], percentiles)):
                fig.add_annotation(
                    x=p_value,
                    y=i * 200,  # Stagger heights by multiplying by a factor (adjust as needed)
                    text=f'{percentile}th percentile: {p_value:.2f}',
                    showarrow=True,
                    arrowhead=2,
                    ax=0,
                    ay=-40
                )
            
            # Save the plot to a file
            fig.write_html(filename)
            # Alternatively, you can use fig.show() to display the plot interactively
            
        else:
            print(f"No {title.lower()} values found in the file.")

    def plot_combined_histograms(mean_values, median_values, minimum_values, maximum_values, filename):
        # Determine the max value across all datasets for binning
        max_value = max(
            max(mean_values, default=0),
            max(median_values, default=0),
            max(minimum_values, default=0),
            max(maximum_values, default=0)
        )
        
        bins = np.arange(0, max_value + 100, 100)
        
        # Create the histogram trace for each dataset
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=mean_values, name='Means', xbins=dict(start=0, end=max_value, size=100), marker_color='#1f77b4', opacity=0.75))
        fig.add_trace(go.Histogram(x=median_values, name='Medians', xbins=dict(start=0, end=max_value, size=100), marker_color='#ff7f0e', opacity=0.75))
        fig.add_trace(go.Histogram(x=minimum_values, name='Minimums', xbins=dict(start=0, end=max_value, size=100), marker_color='#2ca02c', opacity=0.75))
        fig.add_trace(go.Histogram(x=maximum_values, name='Maximums', xbins=dict(start=0, end=max_value, size=100), marker_color='#d62728', opacity=0.75))
        
        # Update layout
        fig.update_layout(
            barmode='group',
            title='Histogram of Means, Medians, Minimums, and Maximums with 100-Step Bins',
            xaxis_title='Value',
            yaxis_title='Frequency',
            xaxis=dict(tickvals=bins, ticktext=[str(b) for b in bins], tickangle=90, tickfont=dict(size=10)),
            bargap=0.1,
            bargroupgap=0.1,
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            autosize=False,
            width=900,
            height=600
        )
        
        # Save the plot to a file
        fig.write_html(filename)
        
    def percentile_below_threshold(values, threshold=300):
        values = np.array(values)
        percentile = np.sum(values <= threshold) / len(values) * 100
        return percentile

    def write_statistics(values, label, f):
        """
        Writes the statistics of a set of values to a file.

        Parameters
        ----------
        values : list of float
            A list of values to calculate the statistics for.
        label : str
            A label to describe the values (e.g. "Means", "Medians", etc.)
        f : file
            A file to write the statistics to.
        """
        if values:
            mean = statistics.mean(values)
            median = statistics.median(values)
            minimum = min(values)
            maximum = max(values)
            f.write(f"\n\nMean {label} value: {mean}")
            f.write(f"\nMedian {label} value: {median}")
            f.write(f"\nMinimum {label} value: {minimum}")
            f.write(f"\nMaximum {label} value: {maximum}")
        else:
            print(f"No {label.lower()} values found in the file.")
        """
        The statistics are written in the format:

        Mean <label> value: <mean>
        Median <label> value: <median>
        Minimum <label> value: <minimum>
        Maximum <label> value: <maximum>
        """

    def filter_percentiles(values, lower_percentile=5, upper_percentile=95):
        lower_bound = np.percentile(values, lower_percentile)
        upper_bound = np.percentile(values, upper_percentile)
        return [v for v in values if lower_bound <= v <= upper_bound]

    def create_combined_box_plot(mean_values, median_values, minimum_values, maximum_values, filepath):
        # Filter values to be within the 5th and 95th percentiles
        mean_values_filtered = filter_percentiles(mean_values)
        median_values_filtered = filter_percentiles(median_values)
        minimum_values_filtered = filter_percentiles(minimum_values)
        maximum_values_filtered = filter_percentiles(maximum_values)
        
        # Create the box plot
        fig = go.Figure()
        fig.add_trace(go.Box(y=mean_values_filtered, name='Means', boxpoints=False, showlegend=False))
        fig.add_trace(go.Box(y=median_values_filtered, name='Medians', boxpoints=False, showlegend=False))
        fig.add_trace(go.Box(y=minimum_values_filtered, name='Minimums', boxpoints=False, showlegend=False))
        fig.add_trace(go.Box(y=maximum_values_filtered, name='Maximums', boxpoints=False, showlegend=False))
        
        fig.update_layout(title='Combined Box Plot', yaxis_title='Value')
        fig.write_html(filepath)

    def create_box_plot(values, title, filepath):
        filtered_values = filter_percentiles(values)
        fig = go.Figure()
        fig.add_trace(go.Box(y=filtered_values, name=title, boxpoints=False, showlegend=False))
        fig.update_layout(title=f'{title} Box Plot', yaxis_title='Value')
        fig.write_html(filepath)

    filename = f"Tests/{timestamp}"
    mean_values, median_values, minimum_values, maximum_values = extract_values(filename + "/test_results.txt")


    with open(filename + "/test_results.txt", "a") as f:
        items = {"Means" : mean_values, 
                 "Medians" : median_values, 
                 "Minimums" : minimum_values, 
                 "Maximums": maximum_values}
        for key, value in items.items():
            plot_histograms(value, key, filename + "/" + key + "_distro.html")
            create_box_plot(value, key, f"{filename}/{key.lower()}_box_plot.html")
            write_statistics(value, key, f)
            percentile_below_threshold(value, threshold=300)
            print(f"{key} percentile below 300: {percentile_below_threshold(value, threshold=300)}%")
        create_combined_box_plot(mean_values, median_values, minimum_values, maximum_values, f"{filename}/combined_box_plot.html")
        plot_combined_histograms(mean_values, median_values, minimum_values, maximum_values, f"{filename}/combined_histograms.html")

        
        f.write(f"\n\nTotal runtime: {runtime}\n")
        f.write("!" * 100)


if __name__ == "__main__":
    write_stats(timestamp = "")
