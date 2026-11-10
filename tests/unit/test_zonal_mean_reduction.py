import numpy as np
import pandas as pd
import pytest
import xarray as xr

from iliotropio.zonal_mean_reduction import (
    annual_mean_reduction_profiles,
    blockwise_zonal_reduction_means,
    on_grid_of,
    to_fraction,
    zonal_reduction_means,
)


TIMES = pd.date_range("2026-01-01", periods=2, freq="30min")


def reduction_percent(values: list[list[list[float]]]) -> xr.DataArray:
    """Reduction in percent as stored on THREDDS: (longitude, latitude, time)."""
    return xr.DataArray(
        values,
        dims=("longitude", "latitude", "time"),
        coords={"longitude": [0.0, 180.0], "latitude": [10.0, -10.0], "time": TIMES},
    )


def insolation(values: list[list[list[float]]]) -> xr.DataArray:
    """SWdnTOA as in the Ilio-1 file: (time_counter, lat, lon), float32 latitudes."""
    return xr.DataArray(
        np.array(values, dtype=np.float32),
        dims=("time_counter", "lat", "lon"),
        coords={
            "time_counter": TIMES,
            "lat": np.array([10.0, -10.0], dtype=np.float32),
            "lon": [0.0, 180.0],
        },
    )


def test_to_fraction_converts_percent_and_renames_dimensions() -> None:
    fraction = to_fraction(reduction_percent([[[1.0, 2.0], [3.0, 4.0]], [[5.0, 6.0], [7.0, 8.0]]]))

    assert set(fraction.dims) == {"lon", "lat", "time_counter"}
    assert fraction["lat"].to_numpy().tolist() == [-10.0, 10.0]
    assert float(fraction.sel(lon=0.0, lat=10.0).isel(time_counter=1)) == pytest.approx(0.02)


def test_on_grid_of_takes_the_reference_latitudes() -> None:
    reference = to_fraction(
        reduction_percent([[[0.0, 0.0], [0.0, 0.0]], [[0.0, 0.0], [0.0, 0.0]]])
    )
    swdntoa = insolation([[[1.0, 2.0], [3.0, 4.0]], [[5.0, 6.0], [7.0, 8.0]]])

    matched = on_grid_of(swdntoa, reference)

    assert matched["lat"].to_numpy().tolist() == [-10.0, 10.0]
    assert float(matched.sel(lat=-10.0, lon=180.0).isel(time_counter=0)) == pytest.approx(4.0)


def test_on_grid_of_rejects_other_latitudes() -> None:
    reference = to_fraction(
        reduction_percent([[[0.0, 0.0], [0.0, 0.0]], [[0.0, 0.0], [0.0, 0.0]]])
    )
    swdntoa = insolation([[[1.0, 2.0], [3.0, 4.0]], [[5.0, 6.0], [7.0, 8.0]]]).assign_coords(
        lat=[20.0, -20.0]
    )

    with pytest.raises(ValueError, match="latitudes"):
        on_grid_of(swdntoa, reference)


def test_profiles_skip_night_in_the_straight_mean_and_weight_by_insolation() -> None:
    # At 10°N: day at lon 0 (2 %, then 4 %), night at lon 180 (NaN), so the straight
    # mean is 3 %; insolation 100 then 300 W m-2 weights it to (2·100 + 4·300) / 400 = 3.5 %.
    nan = np.nan
    reduction = to_fraction(
        reduction_percent([[[2.0, 4.0], [1.0, 1.0]], [[nan, nan], [1.0, 1.0]]])
    )
    swdntoa = on_grid_of(
        insolation([[[100.0, 0.0], [50.0, 50.0]], [[300.0, 0.0], [50.0, 50.0]]]), reduction
    )

    profiles = annual_mean_reduction_profiles(zonal_reduction_means(reduction, swdntoa))

    assert float(profiles["straight"].sel(lat=10.0)) == pytest.approx(0.03)
    assert float(profiles["insolation_weighted"].sel(lat=10.0)) == pytest.approx(0.035)
    assert float(profiles["straight"].sel(lat=-10.0)) == pytest.approx(0.01)


def test_blockwise_zonal_means_weight_uneven_blocks_by_their_longitudes() -> None:
    # Three longitudes read two then one: the zonal mean of 3 %, 6 % and 9 % is 6 %,
    # not the 6.75 % that averaging the block means (4.5 % and 9 %) would give.
    reduction = xr.DataArray(
        [[[3.0]], [[6.0]], [[9.0]]],
        dims=("longitude", "latitude", "time"),
        coords={"longitude": [0.0, 120.0, 240.0], "latitude": [0.0], "time": TIMES[:1]},
    )
    swdntoa = xr.DataArray(
        np.ones((1, 1, 3), dtype=np.float32),
        dims=("time_counter", "lat", "lon"),
        coords={"time_counter": TIMES[:1], "lat": [0.0], "lon": [0.0, 120.0, 240.0]},
    )

    zonal = blockwise_zonal_reduction_means(reduction, swdntoa, longitudes_per_block=2)

    assert float(zonal["shading"].squeeze()) == pytest.approx(0.06)
    assert float(zonal["daylight"].squeeze()) == pytest.approx(1.0)
