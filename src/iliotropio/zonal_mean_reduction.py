"""Plot the solar irradiance reduction of experiments 8A and 8B by latitude, from THREDDS.

The reduction files hold no insolation, so ``SWdnTOA`` comes from the Ilio-1 half-hourly
file: top-of-atmosphere insolation depends only on the date, the time and the grid.
"""

import argparse
import functools
import logging
from pathlib import Path
from urllib.parse import urljoin

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from iliotropio.annual_mean import LATITUDE_DIMENSION, LONGITUDE_DIMENSION, TIME_DIMENSION
from iliotropio.zonal_mean_sunfract import (
    ALBEDO,
    CACHE_DIRECTORY,
    ILIO_1_HISTHF_URL,
    INSOLATION_VARIABLE,
    PROFILE_LABELS,
    PROFILE_LINESTYLES,
    TIME_CHUNK_STEPS,
    load_cached,
    zonal_forcing,
    zonal_means,
)


LOGGER = logging.getLogger(__name__)
ILIOTROPIO_OPENDAP_BASE_URL = (
    "https://thredds-su.ipsl.fr/thredds/dodsC/ipsl_thredds/oboucher/ILIOTROPIO/"
)
REDUCTION_VARIABLE = "solar_irradiance_reduction"
REDUCTION_FILE_PERIOD = "20260101-20291231"
EXPERIMENTS = ("8A", "8B")
EXPERIMENT_COLORS = {"8A": "#08519c", "8B": "tab:orange"}
YEAR = "2026"
# The reduction is stored in percent, from 0 to 100.
PERCENT = 100
# Dimension names in the reduction files, and their names in the Ilio-1 files.
SOURCE_DIMENSIONS = {
    "longitude": LONGITUDE_DIMENSION,
    "latitude": LATITUDE_DIMENSION,
    "time": TIME_DIMENSION,
}
# The reduction files store time last: a whole year at a few longitudes reads in
# seconds, whereas one day over the whole grid takes minutes.
LONGITUDES_PER_READ = 8
# Degrees; the Ilio-1 latitudes are single precision.
LATITUDE_TOLERANCE = 1e-4
DEFAULT_OUTPUT_DIRECTORY = Path("data")
PROFILES_FILENAME = "zonal_mean_profiles_8A_8B.png"
FORCING_PROFILE_FILENAME = "forcing_profile_8A_8B.png"
GLOBAL_MEANS_FILENAME = "global_means_8A_8B.csv"
# CSV column of each global mean profile, with its units.
GLOBAL_MEAN_COLUMNS = {
    "straight": "straight_fraction",
    "insolation_weighted": "insolation_weighted_fraction",
    "forcing": "forcing_W_m2",
}
FORCING_LABEL = "reduction·SWdnTOA·(1 − α) (W m⁻²)"


def experiment_url(experiment: str) -> str:
    """Return the OPeNDAP URL of one experiment's reduction file, e.g. for ``"8A"``."""
    return urljoin(
        ILIOTROPIO_OPENDAP_BASE_URL,
        f"{REDUCTION_VARIABLE}_{experiment}_{REDUCTION_FILE_PERIOD}.nc",
    )


def cache_path(experiment: str) -> Path:
    """Return the cache file of one experiment's zonal means."""
    return CACHE_DIRECTORY / f"ILIOTROPIO_{experiment}_{YEAR}_zonal_means.nc"


def to_fraction(reduction: xr.DataArray) -> xr.DataArray:
    """Convert a reduction in percent, as stored on THREDDS, to a fraction on the Ilio-1 axes.

    Parameters
    ----------
    reduction : xarray.DataArray
        Solar irradiance reduction in percent, with ``longitude``, ``latitude`` and
        ``time`` dimensions; NaN at night.

    Returns
    -------
    xarray.DataArray
        Fraction of solar irradiance removed, with the dimensions renamed as in the
        Ilio-1 files and latitudes in increasing order; still NaN at night.
    """
    return (reduction / PERCENT).rename(SOURCE_DIMENSIONS).sortby(LATITUDE_DIMENSION)


def on_grid_of(data: xr.DataArray, reference: xr.DataArray) -> xr.DataArray:
    """Put ``data`` on the latitudes of ``reference``, which match only to single precision.

    Parameters
    ----------
    data : xarray.DataArray
        Values with a latitude dimension, such as ``SWdnTOA``.
    reference : xarray.DataArray
        Values whose latitudes ``data`` should take.

    Returns
    -------
    xarray.DataArray
        ``data`` sorted by latitude, with the latitudes of ``reference``.

    Raises
    ------
    ValueError
        If the latitudes differ by more than ``LATITUDE_TOLERANCE``.
    """
    data = data.sortby(LATITUDE_DIMENSION)
    latitudes = reference[LATITUDE_DIMENSION].to_numpy()
    if data.sizes[LATITUDE_DIMENSION] != latitudes.size or not np.allclose(
        data[LATITUDE_DIMENSION].to_numpy(), latitudes, rtol=0, atol=LATITUDE_TOLERANCE
    ):
        raise ValueError("data and reference latitudes differ")
    return data.assign_coords({LATITUDE_DIMENSION: latitudes})


def zonal_reduction_means(reduction: xr.DataArray, swdntoa: xr.DataArray) -> xr.Dataset:
    """Average the reduction, shaded insolation, insolation and daylight over longitude.

    Night steps, NaN in ``reduction``, count as no reduction.

    Parameters
    ----------
    reduction : xarray.DataArray
        Fraction of solar irradiance removed, NaN at night, as from `to_fraction`.
    swdntoa : xarray.DataArray
        Downward shortwave radiation at the top of the atmosphere, on the grid of
        ``reduction``.

    Returns
    -------
    xarray.Dataset
        Zonal means of the reduction (``shading``), ``reduction * SWdnTOA``
        (``shaded_insolation``) and ``SWdnTOA`` (``insolation``), as from
        `iliotropio.zonal_mean_sunfract.zonal_means`, and the fraction of longitudes
        where the reduction is defined (``daylight``).

    Raises
    ------
    ValueError
        If either input has no longitude dimension, or their coordinates differ.
    """
    reduction, swdntoa = xr.align(reduction, swdntoa, join="exact")
    zonal = zonal_means(1 - reduction.fillna(0), swdntoa)
    zonal["daylight"] = reduction.notnull().mean(dim=LONGITUDE_DIMENSION)
    return zonal


def blockwise_zonal_reduction_means(
    reduction: xr.DataArray, swdntoa: xr.DataArray, longitudes_per_block: int
) -> xr.Dataset:
    """Compute `zonal_reduction_means` a few longitudes at a time, loading each block.

    Parameters
    ----------
    reduction : xarray.DataArray
        Reduction in percent, as stored on THREDDS; may be lazy.
    swdntoa : xarray.DataArray
        Downward shortwave radiation at the top of the atmosphere, in memory, on the
        grid and times of ``reduction`` up to the latitude precision.
    longitudes_per_block : int
        Number of longitudes to load at once.

    Returns
    -------
    xarray.Dataset
        Zonal means as from `zonal_reduction_means`.
    """
    longitudes = reduction.sizes["longitude"]
    weighted_blocks = []
    for start in range(0, longitudes, longitudes_per_block):
        block = to_fraction(
            reduction.isel(longitude=slice(start, start + longitudes_per_block)).load()
        )
        block_swdntoa = on_grid_of(
            swdntoa.sel({LONGITUDE_DIMENSION: block[LONGITUDE_DIMENSION]}), block
        )
        block_means = zonal_reduction_means(block, block_swdntoa)
        weighted_blocks.append(block_means * block.sizes[LONGITUDE_DIMENSION])
    return xr.concat(weighted_blocks, dim="block").sum(dim="block") / longitudes


def annual_mean_reduction_profiles(zonal: xr.Dataset) -> xr.Dataset:
    """Average the zonal means over the whole period, one year here.

    Parameters
    ----------
    zonal : xarray.Dataset
        Zonal means as from `zonal_reduction_means`.

    Returns
    -------
    xarray.Dataset
        Profiles by latitude: the reduction averaged over daytime steps and longitudes
        (``straight``), and weighted by insolation (``insolation_weighted``), that is
        the fraction of incoming solar radiation removed.
    """
    return xr.Dataset(
        {
            "straight": zonal["shading"].sum(dim=TIME_DIMENSION)
            / zonal["daylight"].sum(dim=TIME_DIMENSION),
            "insolation_weighted": zonal["shaded_insolation"].sum(dim=TIME_DIMENSION)
            / zonal["insolation"].sum(dim=TIME_DIMENSION),
        }
    )


def global_means(profiles: xr.Dataset) -> xr.Dataset:
    """Average profiles over latitude, weighted by the cosine of latitude.

    Parameters
    ----------
    profiles : xarray.Dataset
        Zonal mean profiles by latitude, in degrees.

    Returns
    -------
    xarray.Dataset
        Global mean of each profile.
    """
    latitude = profiles[LATITUDE_DIMENSION]
    weights = latitude.copy(data=np.cos(np.deg2rad(latitude.to_numpy())))
    return profiles.weighted(weights).mean(dim=LATITUDE_DIMENSION)


def read_insolation(url: str, year: str) -> xr.DataArray:
    """Read ``SWdnTOA`` over one year from a remote OPeNDAP dataset into memory.

    Parameters
    ----------
    url : str
        OPeNDAP URL of a NetCDF file with an ``SWdnTOA`` variable.
    year : str
        Year to read, such as ``"2026"``.

    Returns
    -------
    xarray.DataArray
        ``SWdnTOA`` by time, latitude and longitude.

    Raises
    ------
    ValueError
        If the dataset has no ``SWdnTOA`` variable.
    """
    with xr.open_dataset(
        url, engine="netcdf4", chunks={TIME_DIMENSION: TIME_CHUNK_STEPS}
    ) as dataset:
        if INSOLATION_VARIABLE not in dataset:
            raise ValueError(f"Dataset at {url} has no {INSOLATION_VARIABLE!r} variable")
        return dataset[INSOLATION_VARIABLE].sel({TIME_DIMENSION: year}).load()


def read_zonal_reduction_means(url: str, year: str, swdntoa: xr.DataArray) -> xr.Dataset:
    """Read one experiment's reduction over one year from OPeNDAP and average it zonally.

    Parameters
    ----------
    url : str
        OPeNDAP URL of a reduction file.
    year : str
        Year to read, such as ``"2026"``.
    swdntoa : xarray.DataArray
        ``SWdnTOA`` over the same year, as from `read_insolation`.

    Returns
    -------
    xarray.Dataset
        Zonal means by time and latitude, as from `zonal_reduction_means`.

    Raises
    ------
    ValueError
        If the dataset has no reduction variable, or its grid or times differ from
        those of ``swdntoa``.
    """
    with xr.open_dataset(url, engine="netcdf4") as dataset:
        if REDUCTION_VARIABLE not in dataset:
            raise ValueError(f"Dataset at {url} has no {REDUCTION_VARIABLE!r} variable")
        reduction = dataset[REDUCTION_VARIABLE].sel(time=year)
        return blockwise_zonal_reduction_means(reduction, swdntoa, LONGITUDES_PER_READ)


def save_reduction_profiles_plot(profiles: dict[str, xr.Dataset], output_path: Path) -> None:
    """Save the straight and insolation weighted profiles of each experiment on one PNG."""
    figure, axis = plt.subplots(figsize=(10, 6))
    for experiment, experiment_profiles in profiles.items():
        for name, label in PROFILE_LABELS.items():
            profile = experiment_profiles[name]
            axis.plot(
                profile[LATITUDE_DIMENSION],
                profile,
                color=EXPERIMENT_COLORS[experiment],
                linestyle=PROFILE_LINESTYLES[name],
                label=f"{experiment} {label}",
            )
    axis.set(
        xlabel="Latitude (°)",
        ylabel="Annual mean zonal solar irradiance reduction (fraction)",
        title=f"Annual mean zonal solar irradiance reduction, {YEAR}",
        xlim=(-90, 90),
    )
    axis.grid(visible=True, alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def save_forcing_profiles_plot(forcing: dict[str, xr.DataArray], output_path: Path) -> None:
    """Save the annual mean forcing profile of each experiment by latitude as a PNG."""
    figure, axis = plt.subplots(figsize=(10, 6))
    for experiment, profile in forcing.items():
        axis.plot(
            profile[LATITUDE_DIMENSION],
            profile,
            color=EXPERIMENT_COLORS[experiment],
            label=experiment,
        )
    axis.set(
        xlabel="Latitude (°)",
        ylabel=FORCING_LABEL,
        title=f"Annual mean zonal forcing, α = {ALBEDO:g}, {YEAR}",
        xlim=(-90, 90),
    )
    axis.grid(visible=True, alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def main(argv: list[str] | None = None) -> None:
    """Plot the annual mean reduction and forcing profiles of experiments 8A and 8B."""
    parser = argparse.ArgumentParser(
        description=(
            "Plot the annual and zonal mean solar irradiance reduction and forcing of "
            f"experiments {' and '.join(EXPERIMENTS)} in {YEAR} from the ILIOTROPIO "
            "THREDDS data."
        )
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=DEFAULT_OUTPUT_DIRECTORY,
        help=(
            f"directory of {PROFILES_FILENAME}, {FORCING_PROFILE_FILENAME} and "
            f"{GLOBAL_MEANS_FILENAME} "
            f"(default: {DEFAULT_OUTPUT_DIRECTORY})"
        ),
    )
    arguments = parser.parse_args(argv)
    output_directory: Path = arguments.output_directory

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    @functools.cache
    def insolation() -> xr.DataArray:
        LOGGER.info("Reading %s for %s from %s", INSOLATION_VARIABLE, YEAR, ILIO_1_HISTHF_URL)
        return read_insolation(ILIO_1_HISTHF_URL, YEAR)

    zonal = {}
    for experiment in EXPERIMENTS:
        url = experiment_url(experiment)

        def read(url: str = url) -> xr.Dataset:
            swdntoa = insolation()
            LOGGER.info("Reading %s for %s from %s", REDUCTION_VARIABLE, YEAR, url)
            return read_zonal_reduction_means(url, YEAR, swdntoa)

        zonal[experiment] = load_cached(cache_path(experiment), read)

    profiles = {
        experiment: annual_mean_reduction_profiles(experiment_zonal).assign(
            forcing=zonal_forcing(experiment_zonal, ALBEDO).mean(dim=TIME_DIMENSION)
        )
        for experiment, experiment_zonal in zonal.items()
    }
    output_directory.mkdir(parents=True, exist_ok=True)
    profiles_output = output_directory / PROFILES_FILENAME
    save_reduction_profiles_plot(profiles, profiles_output)
    LOGGER.info("Wrote annual mean reduction profiles plot to %s", profiles_output)
    forcing_output = output_directory / FORCING_PROFILE_FILENAME
    save_forcing_profiles_plot(
        {experiment: profiles[experiment]["forcing"] for experiment in profiles},
        forcing_output,
    )
    LOGGER.info("Wrote annual mean forcing profiles plot to %s", forcing_output)

    table = (
        xr.concat([global_means(profiles[experiment]) for experiment in profiles], "experiment")
        .assign_coords(experiment=list(profiles))
        .to_dataframe()
        .rename(columns=GLOBAL_MEAN_COLUMNS)
    )
    global_means_output = output_directory / GLOBAL_MEANS_FILENAME
    table.to_csv(global_means_output)
    LOGGER.info(
        "Global means, weighted by cos(latitude), of the annual mean profiles:\n%s",
        table.to_string(float_format="{:.5g}".format),
    )
    LOGGER.info("Wrote global means to %s", global_means_output)


if __name__ == "__main__":
    main()
