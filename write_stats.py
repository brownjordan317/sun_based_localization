import statistics
import numpy as np
import matplotlib.pyplot as plt
import os

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
        Plots a histogram of a set of values.

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
            bins = np.arange(0, max_value + 50, 50)
            
            # Create the plot
            plt.figure(figsize=(15, 9))
            counts, _, patches = plt.hist(values, bins=bins, edgecolor='black')
            plt.title(f'Histogram of {title} with 50-Step Bins')
            plt.xlabel('Distance from intended target in miles')
            plt.ylabel('Frequency')
            plt.xticks(bins, rotation=90, fontsize=6)
            plt.grid(True)
            
            # Add count labels to each bar
            for count, patch in zip(counts, patches):
                plt.text(patch.get_x() + patch.get_width() / 2, count, int(count), 
                         ha='center', va='bottom', fontsize=8)
            plt.savefig(filename)
            # plt.show()
        else:
            print(f"No {title.lower()} values found in the file.")

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

    filename = f"Tests/{timestamp}"
    mean_values, median_values, minimum_values, maximum_values = extract_values(filename + "/test_results.txt")


    with open(filename + "/test_results.txt", "a") as f:
        items = {"Means" : mean_values, 
                 "Medians" : median_values, 
                 "Minimums" : minimum_values, 
                 "Maximum": maximum_values}
        for key, value in items.items():
            plot_histograms(value, key, filename + "/" + key + "_distro.png")
            write_statistics(value, key, f)
        
        f.write(f"\n\nTotal runtime: {runtime}\n")
        f.write("!" * 100)


if __name__ == "__main__":
    write_stats(timestamp = "Mega_test")
