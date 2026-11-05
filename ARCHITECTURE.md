# Architecture

This document describes the high-level architecture of `template-repo`.
Read it first to find your way around the code. It explains *where things are*
and *why*, not *how* each function works: that belongs in docstrings.

Keep it short, and update it when you add, move or remove a top-level module.

## Bird's eye view

The project reads climate model output from the ILIO THREDDS server and writes
annual area-weighted temperature and precipitation series to CSV and PNG, and
a plot of the zonal mean shading (`1 - sunfract`):

```
THREDDS OPeNDAP ─┬─> template_repo.annual_mean ─────────> annual CSV + PNG per variable
                 └─> template_repo.zonal_mean_sunfract ──> .cache ──> zonal mean shading PNGs
```

## Code map

| Path                    | Role                                                       |
| ----------------------- | ---------------------------------------------------------- |
| `src/template_repo/`    | The installable package.                                   |
| `src/template_repo/cli.py` | Entry point of the `template-repo` command.             |
| `src/template_repo/annual_mean.py` | Remote annual t2m and pr analysis, precipitation sensitivity, and CLI. |
| `src/template_repo/zonal_mean_sunfract.py` | Zonal mean of `1 - sunfract` for Ilio-1: local cache, map and profiles, and CLI. |
| `src/template_repo/config.py` | Settings, read from the environment and `.env`.      |
