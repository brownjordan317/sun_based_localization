from datetime import datetime
from halo import Halo
import argparse
import os
from itertools import product
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
import numpy as np

from utils.random_location_Generator import random_locations
from utils.sun_localizer import SunLocalizer

def create_error_combinations(degrees_error=0, step=0.1):
    """
    Generate all combinations of error offsets for solar azimuth and elevation
    angles, supporting both integer and floating step sizes.

    Parameters
    ----------
    degrees_error : float
        The maximum error (in degrees) to add/subtract from the solar azimuth
        and elevation angles.
    step : float, default=1.0
        Step size between error offsets. Can be fractional.

    Returns
    -------
    list of tuple[float, float]
        A list of tuples, where each tuple contains the error offset for
        the solar azimuth and elevation angles.
    """
    # Generate ranges with numpy (ensures float support)
    l1 = np.arange(-degrees_error, degrees_error + step, step).round(6)
    l2 = np.arange(-degrees_error, degrees_error + step, step).round(6)

    return [(float(x), float(y)) for x, y in product(l1, l2)]

def generate_random_config(num_locations, datetime_rt):
    """
    Generate a random configuration file.

    Parameters
    ----------
    num_locations : int
        The number of random locations to generate.
    datetime_rt : str
        The current datetime in UTC timezone.

    Returns
    -------
    str
        The path to the generated random configuration file.
    """
    spinner = Halo(text='Generating random locations', spinner='dots')
    spinner.start()
    os.makedirs("random_location_csvs", exist_ok=True)
    file_name = os.path.join("random_location_csvs", f"{datetime_rt}.csv")
    random_locations(num_locations, file_name)
    spinner.stop()
    return file_name

def _worker(params):
    """Helper worker function for running SunLocalizer with an error combo."""
    args, datetime_rt, combo = params
    sun_localizer = SunLocalizer(args, datetime_rt)
    return sun_localizer.find_me(*combo, show_progress=False)


def run_localizer(args, datetime_rt):
    """
    Run the solar location finder on either a config file or a pandas dataframe.
    """
    # Always run the base case with no error
    print("Running solar location finder with no added error")
    base_localizer = SunLocalizer(args, datetime_rt)
    base_localizer.find_me()

    # If error offsets are requested, run them in parallel
    if args.doe > 0:
        error_combinations = create_error_combinations(args.doe, args.step)

        # Filter out (0, 0) because it's already run above
        error_combinations = [c for c in error_combinations if c != (0, 0)]

        with Pool(processes=min(16, cpu_count())) as pool:
            for _ in tqdm(
                pool.imap_unordered(
                    _worker, [(args, datetime_rt, combo) for combo in error_combinations]
                ),
                total=len(error_combinations),
                desc="Running solar location finder with different error offsets"
            ):
                pass  # tqdm updates as each task completes


def parse_args():
    """
    Parse command line arguments and return them as an object.

    Returns
    -------
    argparse.Namespace
        An object containing the parsed command line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, help="Path to the YAML configuration file")
    parser.add_argument("--random", type=int, help="Number of random locations to run on")
    parser.add_argument("--skip_map", action="store_true", help="Skip map generation")
    parser.add_argument("--open_map", action="store_true", help="Open the map in a web browser")
    parser.add_argument("--agent_description", action="store_true", help="Print navigation description")
    parser.add_argument("--doe", type=int, default=0, 
                        help="Degrees of error (doe). Range of degrees to test maximum allowed error")
    parser.add_argument("--step", type=float, default=0.1, 
                        help="Step size for degrees of error (doe). Range of degrees to test maximum allowed error")
    return parser.parse_args()

def main():
    """
    The main entry point of the script.

    This function parses the command line arguments and calls the
    `run_localizer` function to run the solar location finder.
    """
    datetime_rt = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    os.makedirs(os.path.join("results", datetime_rt), exist_ok=True)
    args = parse_args()
    if args.random:
        args.config = generate_random_config(args.random, datetime_rt)

    run_localizer(args, datetime_rt)


if __name__ == "__main__":
    main()
