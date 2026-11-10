# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Rename the project and its package to `iliotropio`.

### Added

- Add an `annual-mean` command to compute annual area-weighted series remotely
  for all four experiments, including `Ilio-S1` (source experiment `ss1`):
  `--variable t2m` (K) or `--variable pr` (mm/day).
- Save a PNG plot of the annual series alongside the CSV output.
- Add `annual-mean --sensitivity` to compute the precipitation sensitivity
  (dpr/dt2m) over the last 20 years: `2XCO2` relative to `picontrol`, `Ilio-1`
  and `Ilio-S1` relative to `2XCO2`.
- Add a `zonal-mean-sunfract` command to plot the zonal mean of
  `1 - sunfract` for `Ilio-1` in 2026 as latitude-time maps (half-hourly, a
  July zoom, daily insolation-weighted means, and raw values at 0°E in July),
  with straight
  (doubled) and insolation-weighted annual mean profiles on one plot, and the
  forcing (1 - sunfract)·SWdnTOA·(1 - 0.3) by latitude (against a uniform
  0.0055 reduction in insolation) and by latitude and month; the zonal means are cached locally.
- Add a `zonal-mean-reduction` command to plot the annual and zonal mean
  solar irradiance reduction of experiments `8A` and `8B` in 2026, straight
  (daytime only) and insolation-weighted, and their forcing by latitude, with
  their cos(latitude)-weighted global means in a CSV.
