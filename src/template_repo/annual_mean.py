"""Compute annual area-weighted series from the ILIO THREDDS catalog."""

import argparse
import logging
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from urllib.parse import urljoin

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr


LOGGER = logging.getLogger(__name__)
TIME_DIMENSION = "time_counter"
LATITUDE_DIMENSION = "lat"
LONGITUDE_DIMENSION = "lon"
TIME_CHUNK_DAYS = 365
SECONDS_PER_DAY = 86400
DEFAULT_OUTPUT_DIRECTORY = Path("data")
DEFAULT_SENSITIVITY_OUTPUT = DEFAULT_OUTPUT_DIRECTORY / "precipitation_sensitivity.csv"
SENSITIVITY_YEARS = 20
# Experiment each one is compared with for the precipitation sensitivity.
REFERENCE_EXPERIMENTS = {"2XCO2": "picontrol", "Ilio-1": "2XCO2", "Ilio-S1": "2XCO2"}
EXPERIMENT_COLORS = {
    "picontrol": "black",
    "2XCO2": "tab:red",
    "Ilio-1": "#08519c",
    "Ilio-S1": "#6baed6",
}
OPENDAP_BASE_URL = "https://thredds-su.ipsl.fr/thredds/dodsC/tgcc_thredds/work/oboucher/ILIO/"
SS1_OPENDAP_BASE_URL = (
    "https://thredds-su.ipsl.fr/thredds/dodsC/tgcc_thredds/work/maattana/"
    "TEST-CM61-LR-pi-AM-ss1/ATM/ATM/Analyse/TS_DA/TS_DA/"
)
FILE_PERIOD = "20260101_20751231_1D"


class Variable(StrEnum):
    """Variables the command can compute."""

    T2M = "t2m"
    PR = "pr"


@dataclass(frozen=True)
class VariableSpec:
    """Where to read a variable and how to report it.

    Attributes
    ----------
    netcdf_name : str
        Variable name inside the NetCDF files.
    urls : dict[str, str]
        OPeNDAP URL of each experiment's file.
    scale : float
        Factor converting the file's units to ``units``.
    units : str
        Units of the reported series.
    long_name : str
        Name used in the plot.
    """

    netcdf_name: str
    urls: dict[str, str]
    scale: float
    units: str
    long_name: str


def experiment_urls(ilio_file_variable: str, ss1_file_variable: str) -> dict[str, str]:
    """Return the OPeNDAP URL of each experiment's file for one variable.

    Parameters
    ----------
    ilio_file_variable : str
        Variable part of the file names in the ILIO directory.
    ss1_file_variable : str
        Variable part of the file name of the ``ss1`` experiment.

    Returns
    -------
    dict[str, str]
        URL of each experiment, keyed by experiment name.
    """
    return {
        "2XCO2": urljoin(OPENDAP_BASE_URL, f"tmp_2XCO2_{FILE_PERIOD}_{ilio_file_variable}.nc"),
        "Ilio-1": urljoin(OPENDAP_BASE_URL, f"tmp_Ilio-1_{FILE_PERIOD}_{ilio_file_variable}.nc"),
        "Ilio-S1": urljoin(
            SS1_OPENDAP_BASE_URL,
            f"TEST-CM61-LR-pi-AM-ss1_{FILE_PERIOD}_{ss1_file_variable}.nc",
        ),
        "picontrol": urljoin(
            OPENDAP_BASE_URL, f"tmp_picontrol_{FILE_PERIOD}_{ilio_file_variable}.nc"
        ),
    }


VARIABLE_SPECS = {
    Variable.T2M: VariableSpec(
        netcdf_name="t2m",
        urls=experiment_urls("tas", "t2m"),
        scale=1.0,
        units="K",
        long_name="temperature",
    ),
    Variable.PR: VariableSpec(
        netcdf_name="precip",
        urls=experiment_urls("pr", "precip"),
        scale=SECONDS_PER_DAY,
        units="mm/day",
        long_name="precipitation",
    ),
}


def column_name(variable: Variable, experiment: str) -> str:
    """Return the CSV column name of one experiment's series, e.g. ``pr_2XCO2_mm_day``."""
    units = VARIABLE_SPECS[variable].units.replace("/", "_")
    return f"{variable}_{experiment}_{units}"


def default_series_path(variable: Variable) -> Path:
    """Return the default CSV path of one variable's annual series."""
    return DEFAULT_OUTPUT_DIRECTORY / f"annual_mean_{variable}.csv"


def annual_spatial_mean(data: xr.DataArray) -> xr.DataArray:
    """Calculate annual means after cosine-latitude-weighted spatial averaging.

    Parameters
    ----------
    data : xarray.DataArray
        Data with time, latitude, and longitude dimensions.

    Returns
    -------
    xarray.DataArray
        Annual area-weighted values in the input units, indexed by year.

    Raises
    ------
    ValueError
        If a required time or spatial dimension is missing.
    """
    required_dimensions = {
        TIME_DIMENSION,
        LATITUDE_DIMENSION,
        LONGITUDE_DIMENSION,
    }
    missing_dimensions = required_dimensions.difference(data.dims)
    if missing_dimensions:
        missing = ", ".join(sorted(missing_dimensions))
        raise ValueError(f"data is missing required dimensions: {missing}")

    latitude = data[LATITUDE_DIMENSION].to_numpy()
    weights = xr.DataArray(
        np.cos(np.deg2rad(latitude)),
        dims=LATITUDE_DIMENSION,
        coords={LATITUDE_DIMENSION: latitude},
    )
    spatial_mean = data.weighted(weights).mean(dim=(LATITUDE_DIMENSION, LONGITUDE_DIMENSION))
    return spatial_mean.groupby(f"{TIME_DIMENSION}.year").mean(dim=TIME_DIMENSION)


def read_annual_series(url: str, variable_name: str) -> xr.DataArray:
    """Read one experiment's annual series from its remote OPeNDAP dataset.

    Parameters
    ----------
    url : str
        OPeNDAP URL for an experiment's NetCDF file.
    variable_name : str
        Name of the variable to read in the file.

    Returns
    -------
    xarray.DataArray
        Annual area-weighted values in the file's units, indexed by year.

    Raises
    ------
    ValueError
        If the dataset has no variable named ``variable_name``.
    """
    with xr.open_dataset(
        url,
        engine="netcdf4",
        chunks={TIME_DIMENSION: TIME_CHUNK_DAYS},
    ) as dataset:
        if variable_name not in dataset:
            raise ValueError(f"Dataset at {url} has no {variable_name!r} variable")
        return annual_spatial_mean(dataset[variable_name]).compute()


def compute_experiment_series(variable: Variable) -> xr.Dataset:
    """Read every experiment's series of one variable, in its reported units."""
    spec = VARIABLE_SPECS[variable]
    series = {}
    for experiment, url in spec.urls.items():
        LOGGER.info("Reading annual %s series for %s", variable, experiment)
        series[column_name(variable, experiment)] = (
            read_annual_series(url, spec.netcdf_name) * spec.scale
        )
    return xr.Dataset(series)


def save_annual_plot(annual: xr.Dataset, variable: Variable, output_path: Path) -> None:
    """Save a plot of the experiment series of one variable as a PNG image."""
    spec = VARIABLE_SPECS[variable]
    figure, axis = plt.subplots(figsize=(10, 6))
    for experiment in spec.urls:
        axis.plot(
            annual["year"],
            annual[column_name(variable, experiment)],
            label=experiment,
            color=EXPERIMENT_COLORS[experiment],
        )
    axis.set(
        xlabel="Year",
        ylabel=f"Annual mean {spec.long_name} ({spec.units})",
        title=f"Annual area-weighted mean {spec.long_name}",
    )
    axis.grid(visible=True, alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def standard_error(series: pd.Series) -> float:
    """Return the standard error of the mean of independent samples."""
    return float(series.std(ddof=1) / np.sqrt(len(series)))


def precipitation_sensitivity(t2m: pd.DataFrame, pr: pd.DataFrame, years: int) -> pd.DataFrame:
    """Compare each experiment's last years with its reference experiment.

    The sensitivity is the precipitation change divided by the temperature change,
    both relative to the experiment's reference in ``REFERENCE_EXPERIMENTS``;
    percentages are of the reference's precipitation. Standard errors treat years
    as independent and are combined in quadrature.

    Parameters
    ----------
    t2m : pandas.DataFrame
        Annual temperatures in K, indexed by year, one column per experiment as
        named by `column_name`.
    pr : pandas.DataFrame
        Annual precipitation in mm/day, laid out like ``t2m``.
    years : int
        Number of final years to average.

    Returns
    -------
    pandas.DataFrame
        Reference, means, changes and sensitivities with their standard errors,
        indexed by experiment; an experiment without a reference has only means.

    Raises
    ------
    ValueError
        If an experiment's column is missing or a series has fewer than ``years`` years.
    """
    experiments = list(VARIABLE_SPECS[Variable.T2M].urls)
    windows = {}
    for variable, frame in ((Variable.T2M, t2m), (Variable.PR, pr)):
        missing = [
            column_name(variable, experiment)
            for experiment in experiments
            if column_name(variable, experiment) not in frame
        ]
        if missing:
            raise ValueError(f"{variable} series is missing columns: {', '.join(missing)}")
        if len(frame) < years:
            raise ValueError(
                f"{variable} series has {len(frame)} years, fewer than the {years} to average"
            )
        windows[variable] = frame.sort_index().iloc[-years:]

    def series(variable: Variable, experiment: str) -> pd.Series:
        return windows[variable][column_name(variable, experiment)]

    rows = {}
    for experiment in experiments:
        experiment_t2m = series(Variable.T2M, experiment)
        experiment_pr = series(Variable.PR, experiment)
        reference = REFERENCE_EXPERIMENTS.get(experiment)
        row = {
            "reference": reference,
            "t2m_K": experiment_t2m.mean(),
            "pr_mm_day": experiment_pr.mean(),
        }
        if reference is not None:
            reference_t2m = series(Variable.T2M, reference)
            reference_pr = series(Variable.PR, reference)
            delta_t2m = experiment_t2m.mean() - reference_t2m.mean()
            delta_pr = experiment_pr.mean() - reference_pr.mean()
            delta_t2m_se = np.hypot(standard_error(experiment_t2m), standard_error(reference_t2m))
            delta_pr_se = np.hypot(standard_error(experiment_pr), standard_error(reference_pr))
            sensitivity = delta_pr / delta_t2m
            sensitivity_se = abs(sensitivity) * np.hypot(
                delta_pr_se / delta_pr, delta_t2m_se / delta_t2m
            )
            percent = 100 / reference_pr.mean()
            row |= {
                "delta_t2m_K": delta_t2m,
                "delta_t2m_se_K": delta_t2m_se,
                "delta_pr_mm_day": delta_pr,
                "delta_pr_se_mm_day": delta_pr_se,
                "delta_pr_percent": delta_pr * percent,
                "sensitivity_mm_day_per_K": sensitivity,
                "sensitivity_se_mm_day_per_K": sensitivity_se,
                "sensitivity_percent_per_K": sensitivity * percent,
                "sensitivity_se_percent_per_K": sensitivity_se * percent,
            }
        rows[experiment] = row
    return pd.DataFrame.from_dict(rows, orient="index").rename_axis("experiment")


def write_sensitivity(output: Path) -> None:
    """Write the precipitation sensitivity table computed from the default series CSVs."""
    t2m = pd.read_csv(default_series_path(Variable.T2M), index_col="year")
    pr = pd.read_csv(default_series_path(Variable.PR), index_col="year")
    table = precipitation_sensitivity(t2m, pr, SENSITIVITY_YEARS)
    output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output)
    LOGGER.info(
        "Precipitation sensitivity over the last %d years:\n%s",
        SENSITIVITY_YEARS,
        table.to_string(float_format="{:.5g}".format),
    )
    LOGGER.info("Wrote precipitation sensitivity to %s", output)


def write_annual_series(variable: Variable, output: Path) -> None:
    """Write one variable's annual series to CSV and a companion PNG plot."""
    annual = compute_experiment_series(variable)
    frame = annual.to_dataframe().reset_index()
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    LOGGER.info("Wrote annual %s series to %s", variable, output)
    plot_output = output.with_suffix(".png")
    save_annual_plot(annual, variable, plot_output)
    LOGGER.info("Wrote annual %s plot to %s", variable, plot_output)


def main(argv: list[str] | None = None) -> None:
    """Write annual series of one variable, or the precipitation sensitivity table."""
    parser = argparse.ArgumentParser(
        description="Compute annual area-weighted means from the ILIO THREDDS data."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--variable",
        type=Variable,
        choices=list(Variable),
        default=Variable.T2M,
        help=f"variable to compute (default: {Variable.T2M})",
    )
    mode.add_argument(
        "--sensitivity",
        action="store_true",
        help=(
            f"compute the precipitation sensitivity over the last {SENSITIVITY_YEARS} years "
            "from the default t2m and pr series CSVs"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            f"CSV output path (default: {DEFAULT_OUTPUT_DIRECTORY}/"
            f"annual_mean_<variable>.csv, or {DEFAULT_SENSITIVITY_OUTPUT} with --sensitivity)"
        ),
    )
    arguments = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if arguments.sensitivity:
        write_sensitivity(arguments.output or DEFAULT_SENSITIVITY_OUTPUT)
    else:
        write_annual_series(
            arguments.variable, arguments.output or default_series_path(arguments.variable)
        )


if __name__ == "__main__":
    main()
