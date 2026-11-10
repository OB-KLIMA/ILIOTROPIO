# Architecture

This document describes the high-level architecture of `iliotropio`.
Read it first to find your way around the code. It explains *where things are*
and *why*, not *how* each function works: that belongs in docstrings.

Keep it short, and update it when you add, move or remove a top-level module.

## Bird's eye view

The project reads climate model output from the ILIO THREDDS server and writes
annual area-weighted temperature and precipitation series to CSV and PNG,
plots of the zonal mean shading (`1 - sunfract`) of Ilio-1, and profiles of the
solar irradiance reduction of experiments 8A and 8B:

```
THREDDS OPeNDAP ─┬─> iliotropio.annual_mean ──────────> annual CSV + PNG per variable
                 ├─> iliotropio.zonal_mean_sunfract ──> .cache ──> zonal mean shading PNGs
                 └─> iliotropio.zonal_mean_reduction ─> .cache ──> 8A and 8B profile PNGs
```

## Code map

| Path                                     | Role                                                                                             |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `src/iliotropio/`                        | The installable package.                                                                         |
| `src/iliotropio/cli.py`                  | Entry point of the `iliotropio` command.                                                         |
| `src/iliotropio/annual_mean.py`          | Remote annual t2m and pr analysis, precipitation sensitivity, and CLI.                           |
| `src/iliotropio/zonal_mean_sunfract.py`  | Zonal mean of `1 - sunfract` for Ilio-1: local cache, map and profiles, and CLI.                 |
| `src/iliotropio/zonal_mean_reduction.py` | Solar irradiance reduction of 8A and 8B, with `SWdnTOA` from Ilio-1: profiles, forcing, and CLI. |
| `src/iliotropio/config.py`               | Settings, read from the environment and `.env`.                                                  |
