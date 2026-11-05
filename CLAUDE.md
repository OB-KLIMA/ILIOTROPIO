ILIOTROPIO analyses IPSL-CM6 (CM61-LR) climate model runs of the ILIO experiments, which
shade incoming sunlight (`1 - sunfract` is the fraction removed), against `2XCO2` and
`picontrol`.

- Working method and standards: `.claude/rules/`.
- Architecture and code map: `ARCHITECTURE.md`. Workflow and setup: `CONTRIBUTING.md`.
  Commands and their outputs: `docs/index.md`.
- Dependencies: `uv add <pkg>` (`--group dev|test|docs` if not runtime), never pip.

## Data

- All input is read remotely through OPeNDAP from the IPSL THREDDS server
  (`thredds-su.ipsl.fr`), never downloaded; the URLs are constants in `annual_mean.py`
  and `zonal_mean_sunfract.py`.
- Daily files cover 2026–2075 for `2XCO2`, `Ilio-1`, `picontrol` (`oboucher/ILIO/`,
  variables `tas`/`pr` in file names) and `Ilio-S1` (another user's `ss1` run, `t2m`/`precip`
  in file names). The half-hourly `histhf` file (`sunfract`, `SWdnTOA`) covers Ilio-1 in
  2026 only.
- Dimensions are `time_counter`, `lat`, `lon` on a 143 × 144 grid.

## Running

- Remote reads are slow: `annual-mean` takes about 4 min per variable on every run;
  `zonal-mean-sunfract` takes about 6 min the first time, then reads `.cache/`. Delete a
  cache file to read THREDDS again.
- `.cache/` and `data/` (outputs) are gitignored. `annual-mean --sensitivity` reads the
  default `t2m` and `pr` CSVs in `data/`, so compute both first.
- The `iliotropio` command is still the template's placeholder greeting.
