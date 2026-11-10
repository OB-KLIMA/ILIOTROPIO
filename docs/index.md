# Annual mean series

Run `uv run annual-mean --variable VAR` to read one variable from four
experiments and write its annual series to `data/annual_mean_VAR.csv`, with a
companion plot at `data/annual_mean_VAR.png`. The script reads through OPeNDAP
in time chunks rather than downloading the NetCDF files.

| `VAR`         | Variable in the files | Units                               |
| ------------- | --------------------- | ----------------------------------- |
| `t2m` (default) | `t2m`               | K, as stored                        |
| `pr`          | `precip`              | mm/day (kg m⁻² s⁻¹ × 86400)         |

It computes a cosine-latitude-weighted spatial mean for each day, then averages
those daily means by calendar year. Use `--output PATH` to select another CSV
path; the plot uses the same path with a `.png` extension.

The experiments are `2XCO2`, `Ilio-1`, `Ilio-S1` (source experiment `ss1`),
and `picontrol`.

## Precipitation sensitivity

Once both series exist, run `uv run annual-mean --sensitivity` to write
`data/precipitation_sensitivity.csv`. Over the last 20 years, it compares
`2XCO2` with `picontrol`, and `Ilio-1` and `Ilio-S1` with `2XCO2`: mean `t2m`
and `pr`, their changes ΔT and ΔP, and the sensitivity ΔP/ΔT in mm/day/K and
in %/K of the reference experiment's precipitation.
Each value comes with a standard error that treats years as independent, so
it is a lower bound.

## Zonal mean shading

Run `uv run zonal-mean-sunfract` to plot the zonal mean of `1 - sunfract`
(the fraction of solar radiation removed) for `Ilio-1` in 2026, from the
half-hourly `TEST-CM61-LR-pi-AM-Ilio-1_20260101_20261231_HF_histhf.nc`. It
writes seven plots:

- `data/zonal_mean_shading_Ilio-1.png`: a latitude-time map at every
  half-hourly step;
- `data/zonal_mean_shading_Ilio-1_zoom.png`: the same map for July 2026;
- `data/shading_lon0_Ilio-1.png`: raw `1 - sunfract` at 0°E, not zonally
  averaged, for July 2026;
- `data/zonal_mean_shading_Ilio-1_daily.png`: the same map with daily means
  weighted by `SWdnTOA`, Σ(1 - sunfract)·SWdnTOA / ΣSWdnTOA over each day and
  longitude; days without insolation (polar night) are grey;
- `data/zonal_mean_profiles_Ilio-1.png`: two annual mean profiles by
  latitude. "straight" is the plain mean over time and longitude, multiplied
  by 2 on the plot because night steps, where `1 - sunfract` is 0, make up
  about half of it. "insolation weighted" is Σ(1 - sunfract)·SWdnTOA /
  ΣSWdnTOA over time and longitude, which is the fraction of incoming
  sunlight removed;
- `data/forcing_profile_Ilio-1.png` and `data/forcing_monthly_Ilio-1.png`:
  the climate forcing (1 - sunfract)·SWdnTOA·(1 - α), with an arbitrary
  albedo α = 0.3, in W m⁻², as an annual mean profile by latitude and as
  monthly means by latitude. The profile also shows the forcing of a uniform
  0.0055 reduction in insolation, 0.0055·SWdnTOA·(1 - α). It is positive for
  less absorbed sunlight.

Use `--output PATH` to move the map; the other six plots go to the same
directory. The first run
caches the zonal means in `.cache/Ilio-1_histhf_zonal_means.nc` (about 30 MB)
and the 0°E slice in `.cache/Ilio-1_histhf_shading_lon0_2026-07-01_2026-07-31.nc`
(about 1 MB); later runs read the cache instead of THREDDS. Delete a file to
read its remote data again.

## Solar irradiance reduction of 8A and 8B

Run `uv run zonal-mean-reduction` to plot, for experiments `8A` and `8B` in
2026, the annual and zonal mean of `solar_irradiance_reduction` from the
[ILIOTROPIO catalog](https://thredds-su.ipsl.fr/thredds/catalog/ipsl_thredds/oboucher/ILIOTROPIO/catalog.html).
The files store the reduction itself, in percent and NaN at night; the plots
show it as a fraction. The files hold no insolation, so `SWdnTOA` comes from
the Ilio-1 half-hourly file, on the same grid and time steps. It writes two
plots and a table:

- `data/zonal_mean_profiles_8A_8B.png`: for each experiment, the "straight"
  mean over daytime steps and longitudes, night excluded, and the "insolation
  weighted" mean Σ reduction·SWdnTOA / ΣSWdnTOA, the fraction of incoming
  sunlight removed;
- `data/forcing_profile_8A_8B.png`: the annual mean forcing
  reduction·SWdnTOA·(1 - α), α = 0.3, in W m⁻², by latitude;
- `data/global_means_8A_8B.csv`: the global mean of each of these profiles,
  weighted by cos(latitude), also written to the log.

Use `--output-directory DIR` to write them elsewhere. The first run takes
about 11 minutes and caches the zonal means (70 MB each) in
`.cache/ILIOTROPIO_8A_2026_zonal_means.nc` and `..._8B_...`; later runs read
the cache.

The [API reference](api.md) is generated from the package docstrings.
