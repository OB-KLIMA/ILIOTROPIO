"""Plot ``1 - sunfract`` for Ilio-1, mostly as zonal means, from the ILIO THREDDS catalog."""

import argparse
import calendar
import logging
from pathlib import Path
from urllib.parse import urljoin
lazy from collections.abc import Callable

import matplotlib.pyplot as plt
import xarray as xr

from iliotropio.annual_mean import (
    EXPERIMENT_COLORS,
    LATITUDE_DIMENSION,
    LONGITUDE_DIMENSION,
    OPENDAP_BASE_URL,
    TIME_DIMENSION,
)


LOGGER = logging.getLogger(__name__)
SUNFRACT_VARIABLE = "sunfract"
INSOLATION_VARIABLE = "SWdnTOA"
# Ten days of half-hourly steps, about 40 MB per variable and chunk on the 143 x 144 grid.
TIME_CHUNK_STEPS = 480
ILIO_1_HISTHF_URL = urljoin(
    OPENDAP_BASE_URL, "TEST-CM61-LR-pi-AM-Ilio-1_20260101_20261231_HF_histhf.nc"
)
CACHE_DIRECTORY = Path(".cache")
CACHE_PATH = CACHE_DIRECTORY / "Ilio-1_histhf_zonal_means.nc"
DEFAULT_OUTPUT = Path("data/zonal_mean_shading_Ilio-1.png")
PROFILES_FILENAME = "zonal_mean_profiles_Ilio-1.png"
# A boreal summer month for the zoomed maps, first and last days included.
ZOOM_DAYS = ("2026-07-01", "2026-07-31")
# Longitude of the raw, not zonally averaged, latitude-time map over ZOOM_DAYS.
SECTION_LONGITUDE = 0.0
ZONAL_MEAN_LABEL = "Zonal mean (1 − sunfract)"
PROFILE_LABELS = {"straight": "straight", "insolation_weighted": "insolation weighted"}
PROFILE_LINESTYLES = {"straight": "--", "insolation_weighted": "-"}
# The straight mean counts night steps, where 1 - sunfract is 0; doubling it puts it
# on the scale of the insolation weighted mean, which only counts sunlit steps.
STRAIGHT_PLOT_FACTOR = 2
# Arbitrary planetary albedo turning shaded insolation into a climate forcing.
ALBEDO = 0.3
FORCING_LABEL = "(1 − sunfract)·SWdnTOA·(1 − α) (W m⁻²)"
# Constant fraction of insolation removed everywhere, for comparison with Ilio-1.
UNIFORM_REDUCTION = 0.0055
FORCING_CURVE_LABELS = ("G8a", "uniform G8b")
FORCING_PROFILE_FILENAME = "forcing_profile_Ilio-1.png"
FORCING_MONTHLY_FILENAME = "forcing_monthly_Ilio-1.png"


def zonal_mean_shading(sunfract: xr.DataArray) -> xr.DataArray:
    """Average ``1 - sunfract`` over longitude.

    Parameters
    ----------
    sunfract : xarray.DataArray
        Fraction of solar radiation with a longitude dimension.

    Returns
    -------
    xarray.DataArray
        Zonal mean of ``1 - sunfract``, with the remaining dimensions of ``sunfract``.

    Raises
    ------
    ValueError
        If ``sunfract`` has no longitude dimension.
    """
    if LONGITUDE_DIMENSION not in sunfract.dims:
        raise ValueError(f"sunfract data is missing the {LONGITUDE_DIMENSION} dimension")
    return (1 - sunfract).mean(dim=LONGITUDE_DIMENSION)


def longitude_shading(sunfract: xr.DataArray, longitude: float) -> xr.DataArray:
    """Return the raw ``1 - sunfract`` at one longitude of the grid.

    Parameters
    ----------
    sunfract : xarray.DataArray
        Fraction of solar radiation with a longitude dimension.
    longitude : float
        Longitude in degrees east, one of the grid's.

    Returns
    -------
    xarray.DataArray
        ``1 - sunfract`` at ``longitude``, with the remaining dimensions of ``sunfract``.

    Raises
    ------
    ValueError
        If ``sunfract`` has no longitude dimension or ``longitude`` is not on its grid.
    """
    if LONGITUDE_DIMENSION not in sunfract.dims:
        raise ValueError(f"sunfract data is missing the {LONGITUDE_DIMENSION} dimension")
    if longitude not in sunfract[LONGITUDE_DIMENSION].to_numpy():
        raise ValueError(f"Longitude {longitude:g} is not on the sunfract grid")
    return 1 - sunfract.sel({LONGITUDE_DIMENSION: longitude})


def zonal_means(sunfract: xr.DataArray, swdntoa: xr.DataArray) -> xr.Dataset:
    """Average shading, shaded insolation and insolation over longitude.

    Parameters
    ----------
    sunfract : xarray.DataArray
        Fraction of solar radiation with a longitude dimension.
    swdntoa : xarray.DataArray
        Downward shortwave radiation at the top of the atmosphere, on the grid of
        ``sunfract``.

    Returns
    -------
    xarray.Dataset
        Zonal means of ``1 - sunfract`` (``shading``), ``(1 - sunfract) * SWdnTOA``
        (``shaded_insolation``) and ``SWdnTOA`` (``insolation``).

    Raises
    ------
    ValueError
        If either input has no longitude dimension.
    """
    if LONGITUDE_DIMENSION not in swdntoa.dims:
        raise ValueError(f"SWdnTOA data is missing the {LONGITUDE_DIMENSION} dimension")
    return xr.Dataset(
        {
            "shading": zonal_mean_shading(sunfract),
            "shaded_insolation": ((1 - sunfract) * swdntoa).mean(dim=LONGITUDE_DIMENSION),
            "insolation": swdntoa.mean(dim=LONGITUDE_DIMENSION),
        }
    )


def annual_mean_profiles(zonal: xr.Dataset) -> xr.Dataset:
    """Average the zonal means over the whole period, one year here.

    Parameters
    ----------
    zonal : xarray.Dataset
        Zonal means as returned by `zonal_means`.

    Returns
    -------
    xarray.Dataset
        Profiles by latitude: the straight time mean of the shading (``straight``)
        and the shading weighted by insolation (``insolation_weighted``), that is the
        fraction of incoming solar radiation removed.
    """
    return xr.Dataset(
        {
            "straight": zonal["shading"].mean(dim=TIME_DIMENSION),
            "insolation_weighted": zonal["shaded_insolation"].sum(dim=TIME_DIMENSION)
            / zonal["insolation"].sum(dim=TIME_DIMENSION),
        }
    )


def daily_insolation_weighted_shading(zonal: xr.Dataset) -> xr.DataArray:
    """Weight the shading by insolation over each calendar day.

    Parameters
    ----------
    zonal : xarray.Dataset
        Zonal means as returned by `zonal_means`.

    Returns
    -------
    xarray.DataArray
        Daily fraction of incoming solar radiation removed, by day and latitude,
        with time labelled by the start of each day; NaN on days without insolation
        (polar night).
    """
    daily = zonal[["shaded_insolation", "insolation"]].resample({TIME_DIMENSION: "1D"}).sum()
    return daily["shaded_insolation"] / daily["insolation"].where(daily["insolation"] > 0)


def zonal_forcing(zonal: xr.Dataset, albedo: float) -> xr.DataArray:
    """Return the climate forcing ``(1 - sunfract) * SWdnTOA * (1 - albedo)``, zonally averaged.

    Parameters
    ----------
    zonal : xarray.Dataset
        Zonal means as returned by `zonal_means`.
    albedo : float
        Planetary albedo, the fraction of the removed sunlight that would have been
        reflected anyway.

    Returns
    -------
    xarray.DataArray
        Forcing in W m-2 by time and latitude, positive for less absorbed sunlight.
    """
    return (1 - albedo) * zonal["shaded_insolation"]


def uniform_reduction_forcing(zonal: xr.Dataset, reduction: float, albedo: float) -> xr.DataArray:
    """Return the forcing ``reduction * SWdnTOA * (1 - albedo)`` of a uniform dimming.

    Parameters
    ----------
    zonal : xarray.Dataset
        Zonal means as returned by `zonal_means`.
    reduction : float
        Constant fraction of insolation removed, standing in for ``1 - sunfract``.
    albedo : float
        Planetary albedo, as in `zonal_forcing`.

    Returns
    -------
    xarray.DataArray
        Forcing in W m-2 by time and latitude, positive for less absorbed sunlight.
    """
    return reduction * (1 - albedo) * zonal["insolation"]


def monthly_means(data: xr.DataArray) -> xr.DataArray:
    """Average a time series over each calendar month.

    Parameters
    ----------
    data : xarray.DataArray
        Values with a time dimension.

    Returns
    -------
    xarray.DataArray
        Monthly means, with time labelled by the start of each month.
    """
    return data.resample({TIME_DIMENSION: "1MS"}).mean()


def select_days(data: xr.DataArray, first_day: str, last_day: str) -> xr.DataArray:
    """Select the time steps from the start of ``first_day`` to the end of ``last_day``.

    Parameters
    ----------
    data : xarray.DataArray
        Values with a time dimension.
    first_day, last_day : str
        ISO dates, such as ``"2026-07-01"``.

    Returns
    -------
    xarray.DataArray
        The selected time steps.

    Raises
    ------
    ValueError
        If no time step falls in the period.
    """
    selected = data.sel({TIME_DIMENSION: slice(first_day, last_day)})
    if selected.sizes[TIME_DIMENSION] == 0:
        raise ValueError(f"No data from {first_day} to {last_day}")
    return selected


def read_zonal_means(url: str) -> xr.Dataset:
    """Read ``sunfract`` and ``SWdnTOA`` from a remote OPeNDAP dataset and average them.

    Parameters
    ----------
    url : str
        OPeNDAP URL of a NetCDF file with ``sunfract`` and ``SWdnTOA`` variables.

    Returns
    -------
    xarray.Dataset
        Zonal means by time and latitude, as returned by `zonal_means`.

    Raises
    ------
    ValueError
        If the dataset lacks ``sunfract`` or ``SWdnTOA``.
    """
    with xr.open_dataset(
        url,
        engine="netcdf4",
        chunks={TIME_DIMENSION: TIME_CHUNK_STEPS},
    ) as dataset:
        for variable in (SUNFRACT_VARIABLE, INSOLATION_VARIABLE):
            if variable not in dataset:
                raise ValueError(f"Dataset at {url} has no {variable!r} variable")
        return zonal_means(dataset[SUNFRACT_VARIABLE], dataset[INSOLATION_VARIABLE]).compute()


def read_longitude_shading(
    url: str, longitude: float, first_day: str, last_day: str
) -> xr.Dataset:
    """Read the raw ``1 - sunfract`` at one longitude and over some days from OPeNDAP.

    Only that slice is transferred.

    Parameters
    ----------
    url : str
        OPeNDAP URL of a NetCDF file with a ``sunfract`` variable.
    longitude : float
        Longitude in degrees east, one of the grid's.
    first_day, last_day : str
        ISO dates of the first and last days, both included.

    Returns
    -------
    xarray.Dataset
        ``1 - sunfract`` by time and latitude (``shading``).

    Raises
    ------
    ValueError
        If the dataset has no ``sunfract`` variable, or the longitude or days are not
        in it.
    """
    with xr.open_dataset(url, engine="netcdf4") as dataset:
        if SUNFRACT_VARIABLE not in dataset:
            raise ValueError(f"Dataset at {url} has no {SUNFRACT_VARIABLE!r} variable")
        days = select_days(dataset[SUNFRACT_VARIABLE], first_day, last_day)
        return xr.Dataset({"shading": longitude_shading(days, longitude).load()})


def load_cached(cache_path: Path, read: Callable[[], xr.Dataset]) -> xr.Dataset:
    """Return the dataset cached in ``cache_path``, calling ``read`` and caching it if absent.

    Parameters
    ----------
    cache_path : pathlib.Path
        NetCDF cache file; delete it to read the remote data again.
    read : callable
        Returns the dataset to cache.

    Returns
    -------
    xarray.Dataset
        The cached or freshly read dataset.
    """
    if cache_path.exists():
        LOGGER.info("Using cached data from %s", cache_path)
        return xr.load_dataset(cache_path)
    data = read()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    # Write then rename, so an interrupted run leaves no partial cache behind.
    partial_path = cache_path.with_name(f"{cache_path.name}.partial")
    data.to_netcdf(partial_path)
    partial_path.replace(cache_path)
    LOGGER.info("Cached data to %s", cache_path)
    return data


def load_zonal_means(url: str, cache_path: Path) -> xr.Dataset:
    """Return the zonal means from ``cache_path``, reading and caching them if absent.

    Parameters
    ----------
    url : str
        OPeNDAP URL to read when the cache is absent.
    cache_path : pathlib.Path
        NetCDF cache file; delete it to read the remote data again.

    Returns
    -------
    xarray.Dataset
        Zonal means by time and latitude, as returned by `zonal_means`.
    """

    def read() -> xr.Dataset:
        LOGGER.info("Reading sunfract and SWdnTOA from %s", url)
        return read_zonal_means(url)

    return load_cached(cache_path, read)


def save_shading_plot(
    shading: xr.DataArray, title: str, value_label: str, output_path: Path
) -> None:
    """Save a latitude-time map of the shading as a PNG image.

    Undefined values, such as weighted shading in polar night, are drawn in grey.
    """
    figure, axis = plt.subplots(figsize=(12, 6))
    mesh = axis.pcolormesh(
        shading[TIME_DIMENSION],
        shading[LATITUDE_DIMENSION],
        shading.transpose(LATITUDE_DIMENSION, TIME_DIMENSION),
        cmap=plt.get_cmap("Blues").with_extremes(bad="lightgrey"),
        shading="nearest",
    )
    figure.colorbar(mesh, ax=axis, label=value_label)
    axis.set(
        xlabel="Time",
        ylabel="Latitude (°)",
        title=title,
    )
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def save_profiles_plot(profiles: xr.Dataset, output_path: Path) -> None:
    """Save the straight (doubled) and insolation weighted profiles on one PNG plot."""
    figure, axis = plt.subplots(figsize=(10, 6))
    for name, label in PROFILE_LABELS.items():
        profile = profiles[name] * (STRAIGHT_PLOT_FACTOR if name == "straight" else 1)
        axis.plot(
            profile[LATITUDE_DIMENSION],
            profile,
            color=EXPERIMENT_COLORS["Ilio-1"],
            linestyle=PROFILE_LINESTYLES[name],
            label=label,
        )
    axis.set(
        xlabel="Latitude (°)",
        ylabel="Annual mean zonal (1 − sunfract)",
        title="Annual mean zonal (1 − sunfract), Ilio-1",
        xlim=(-90, 90),
    )
    axis.grid(visible=True, alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def save_forcing_profile_plot(
    forcing: xr.DataArray, uniform_forcing: xr.DataArray, output_path: Path
) -> None:
    """Save the annual mean Ilio-1 and uniform reduction forcings by latitude as a PNG."""
    figure, axis = plt.subplots(figsize=(10, 6))
    for profile, label, color, linestyle in zip(
        (forcing, uniform_forcing),
        FORCING_CURVE_LABELS,
        (EXPERIMENT_COLORS["Ilio-1"], "black"),
        ("-", "--"),
        strict=True,
    ):
        axis.plot(
            profile[LATITUDE_DIMENSION], profile, color=color, linestyle=linestyle, label=label
        )
    axis.legend()
    axis.set(
        xlabel="Latitude (°)",
        ylabel=FORCING_LABEL,
        title=f"Annual mean zonal forcing, α = {ALBEDO:g}, Ilio-1",
        xlim=(-90, 90),
    )
    axis.grid(visible=True, alpha=0.3)
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def save_monthly_forcing_plot(forcing: xr.DataArray, output_path: Path) -> None:
    """Save a latitude-month map of the monthly mean forcing as a PNG image."""
    months = forcing[TIME_DIMENSION].dt.month
    figure, axis = plt.subplots(figsize=(12, 6))
    mesh = axis.pcolormesh(
        months,
        forcing[LATITUDE_DIMENSION],
        forcing.transpose(LATITUDE_DIMENSION, TIME_DIMENSION),
        cmap="Blues",
        shading="nearest",
    )
    figure.colorbar(mesh, ax=axis, label=FORCING_LABEL)
    axis.set(
        xticks=months,
        xticklabels=[calendar.month_abbr[month] for month in months.to_numpy()],
        xlabel="Month",
        ylabel="Latitude (°)",
        title=f"Monthly mean zonal forcing, α = {ALBEDO:g}, Ilio-1",
    )
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def main(argv: list[str] | None = None) -> None:
    """Plot ``1 - sunfract`` for Ilio-1: zonal mean maps and profiles, and a raw map."""
    parser = argparse.ArgumentParser(
        description="Plot the zonal mean of 1 - sunfract for Ilio-1 from the ILIO THREDDS data."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=(
            f"PNG output path of the latitude-time map (default: {DEFAULT_OUTPUT}); "
            "the zoomed and daily maps go next to it with _zoom and _daily suffixes, "
            f"the profiles to {PROFILES_FILENAME}, the forcing plots to "
            f"{FORCING_PROFILE_FILENAME} and {FORCING_MONTHLY_FILENAME}, and the raw map "
            "at one longitude to shading_lon<longitude>_Ilio-1.png in the same directory"
        ),
    )
    arguments = parser.parse_args(argv)
    output: Path = arguments.output

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    zonal = load_zonal_means(ILIO_1_HISTHF_URL, CACHE_PATH)
    output.parent.mkdir(parents=True, exist_ok=True)
    save_shading_plot(
        zonal["shading"], "Zonal mean (1 − sunfract), Ilio-1", ZONAL_MEAN_LABEL, output
    )
    LOGGER.info("Wrote zonal mean shading plot to %s", output)
    zoom_output = output.with_name(f"{output.stem}_zoom{output.suffix}")
    first_day, last_day = ZOOM_DAYS
    save_shading_plot(
        select_days(zonal["shading"], first_day, last_day),
        f"Zonal mean (1 − sunfract), Ilio-1, {first_day} to {last_day}",
        ZONAL_MEAN_LABEL,
        zoom_output,
    )
    LOGGER.info("Wrote zoomed zonal mean shading plot to %s", zoom_output)
    daily_output = output.with_name(f"{output.stem}_daily{output.suffix}")
    save_shading_plot(
        daily_insolation_weighted_shading(zonal),
        "Daily insolation weighted zonal (1 − sunfract), Ilio-1",
        ZONAL_MEAN_LABEL,
        daily_output,
    )
    LOGGER.info("Wrote daily insolation weighted zonal shading plot to %s", daily_output)
    profiles_output = output.with_name(PROFILES_FILENAME)
    save_profiles_plot(annual_mean_profiles(zonal), profiles_output)
    LOGGER.info("Wrote annual mean profiles plot to %s", profiles_output)
    forcing = zonal_forcing(zonal, ALBEDO)
    forcing_profile_output = output.with_name(FORCING_PROFILE_FILENAME)
    save_forcing_profile_plot(
        forcing.mean(dim=TIME_DIMENSION),
        uniform_reduction_forcing(zonal, UNIFORM_REDUCTION, ALBEDO).mean(dim=TIME_DIMENSION),
        forcing_profile_output,
    )
    LOGGER.info("Wrote annual mean forcing plot to %s", forcing_profile_output)
    forcing_monthly_output = output.with_name(FORCING_MONTHLY_FILENAME)
    save_monthly_forcing_plot(monthly_means(forcing), forcing_monthly_output)
    LOGGER.info("Wrote monthly mean forcing plot to %s", forcing_monthly_output)

    section_name = f"shading_lon{SECTION_LONGITUDE:g}_{first_day}_{last_day}"

    def read_section() -> xr.Dataset:
        LOGGER.info("Reading sunfract at %g°E from %s", SECTION_LONGITUDE, ILIO_1_HISTHF_URL)
        return read_longitude_shading(ILIO_1_HISTHF_URL, SECTION_LONGITUDE, first_day, last_day)

    section = load_cached(CACHE_DIRECTORY / f"Ilio-1_histhf_{section_name}.nc", read_section)
    section_output = output.with_name(f"shading_lon{SECTION_LONGITUDE:g}_Ilio-1.png")
    save_shading_plot(
        section["shading"],
        f"(1 − sunfract) at {SECTION_LONGITUDE:g}°E, Ilio-1, {first_day} to {last_day}",
        "1 − sunfract",
        section_output,
    )
    LOGGER.info("Wrote raw shading plot at %g°E to %s", SECTION_LONGITUDE, section_output)


if __name__ == "__main__":
    main()
