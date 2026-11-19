# CLAUDE.md

Guidance for Claude Code when working in this repository. See [README.md](README.md) for user-facing setup, IGDB update steps and Railway deployment.

## What this is

Glass Explore is a single-page Dash app (`/energy`) for exploring glass products in the LBNL International Glazing Database (IGDB). The user picks a coated glass from a scatter plot or search, builds a double-glazed unit (coated lite + gas gap + clear/ultraclear lite), and gets U-value, SHGC / solar factor, visible transmittance, reflectance and colour, to either NFRC or EN 410 / EN 673.

## Commands

```powershell
poetry install
poetry run python glass_explore/app.py   # dev server, debug + reloader, http://127.0.0.1:8050
poetry run python production.py          # production-style, 0.0.0.0:8050
poetry run gunicorn production:server    # Linux only
```

- Target Python is 3.11 (`.python-version`). `pyproject.toml` allows `^3.11`, but 3.12+ is untested with `pywincalc`.
- There are no tests, no linter config and no CI. Verify changes by running the app and exercising the page. `en673.py`, `en410.py` and `glass_model/` are pure Python and are the easiest places to add tests.
- Run everything from the repo root so `glass_explore` is importable and `data/` resolves.

## Data — read before running anything

- **Importing `glass_explore` has side effects.** [glass_explore/__init__.py](glass_explore/__init__.py) resolves data paths, raises `FileNotFoundError` if any of `data/igdb.sqlite`, `data/glass.parquet`, `data/readable_glass.parquet` is missing, and loads `glass.parquet` into the module-level `DF_GLASS_TABLE`. Every submodule and script inherits this.
- **`data/igdb.sqlite` (~250 MB) is not in git.** It is over GitHub's file limit and the project deliberately does not use Git LFS, so the file is gitignored. It exists only on the developer's machine and, for production, on the Railway volume. A fresh clone has no database and the app will not start until the file is copied in or rebuilt; the README's "Setting up a new clone" section has the steps. Never force-add it. Older commits hold a 137-byte LFS pointer at this path, not the database.
- `glass.parquet` is the preprocessed `Glass` table (indexed by `ID`, plus `CssColor`, RGB and Lab columns) used for graphs and search. `igdb.sqlite` is used for per-product detail: spectral data, glazing properties, gas properties.
- `readable_glass.parquet` must exist but the app never reads it, and the code that generates it is commented out.
- **Do not run `scripts/update_igdb.py` without asking.** Its `__main__` currently has `convert_access_file = True`, which drops and rebuilds every table in `data/igdb.sqlite` from `C:/Users/Public/LBNL/WINDOW7.8/w7.mdb` (Windows + Access ODBC driver only). There is no other copy of the database in git to fall back on.
- `data/standards/` holds the WINDOW optical standard files; a `.std` file references its sibling files by name, so keep the directory intact.
- `references/` (copyrighted standards PDFs) and `.claude/` are gitignored on purpose. `cache/` is the local diskcache directory.

## Architecture

| File | Role |
| --- | --- |
| [glass_explore/__init__.py](glass_explore/__init__.py) | Config hub: paths, Railway detection, `DF_GLASS_TABLE`, `EnergyLayoutID` (every component ID), `Buildup` dict keys |
| [glass_explore/app.py](glass_explore/app.py) | Flask + Dash entry point; `/` redirects to `/energy` |
| [glass_explore/pages/energy.py](glass_explore/pages/energy.py) | Page registration and top-level layout; importing it registers the callbacks |
| [glass_explore/energy_layout.py](glass_explore/energy_layout.py) | Component builders: navbar, cards, modals, graph tabs |
| [glass_explore/callbacks_energy.py](glass_explore/callbacks_energy.py) | All Dash callbacks |
| [glass_explore/callback_helpers.py](glass_explore/callback_helpers.py) | Plotly figure construction, table filtering |
| [glass_explore/igdb.py](glass_explore/igdb.py) | SQLite lookups (`functools.cache`d) and the clear / ultraclear / gas ID tables |
| [glass_explore/mywincalc.py](glass_explore/mywincalc.py), [optics.py](glass_explore/optics.py) | `pywincalc` glazing-system setup |
| [glass_explore/en673.py](glass_explore/en673.py), [en410.py](glass_explore/en410.py) | Pure-Python EN 673 U-value and EN 410 solar factor |
| [glass_explore/glass_model/](glass_explore/glass_model/) | Buildup object model and the `gstr` share-string protocol (also published separately as `aegis1980/glass-model`) |
| [glass_explore/caching.py](glass_explore/caching.py) | diskcache of the thickness-filtered glass table |

### Callback flow

1. A graph click sets `GRAPH_IGDB.clickData`. Programmatic selection (page load, search modal OK, share URL, product link) works by *writing a fake `clickData`* via `callback_helpers.clickdata_for_glass_id`.
2. `glass_to_store` turns `clickData` plus the form controls into the buildup dict and writes it as JSON to the session `dcc.Store` `STORE_BUILDUP_IN_SESSION`.
3. That store's `modified_timestamp` triggers the SVG thumbnail, the product text and `run_analysis_and_update_results`.

`fast_highlight` patches `figure.data[-1]`, so the selected-point trace must stay the last trace in every figure.

### Buildup dict

```python
{
  "layers": [        # outside -> inside
    {"id": <Glass.ID>, "props": {...}, "thickness": mm, "coating": "Front|Back|Both|Neither", "color": "#rrggbb", "flipped": bool},
    {...},
  ],
  "gas_layers": [{"gas": "argon", "thickness": mm}],
}
```

The coated lite is `layers[0]` unless the outside/inside switch is on, in which case it is `layers[1]`.

### Calculation paths

- **NFRC** (`standard == "nfrc"`): everything from `pywincalc` with `W5_NFRC_2003.std` (ISO 15099 thermal).
- **EN**: `pywincalc` with `prEN_410.std` for visible and colour results only. U-value comes from `en673.u_value` and solar factor from `en410.solar_factor`; the `_trial = True` flag in `run_analysis_and_update_results` selects the pure-Python U-value over pywincalc's.
- Glass layers reach `pywincalc` by writing a temporary Optics-format file and parsing it (`optics.product_from_tempfile`). This is a deliberate workaround; `mywincalc.glass_layer_from_props` is the unused direct approach.

### Share links

`/energy?g=<gstr>`, for example `#9923(6MONO)_12.0AIR_#103(6MONO)`: `#<Glass.ID>` with an optional `x` suffix for flipped, `_` between lites and gaps. The callback parses it, stores it, then a clientside callback strips the query string from the address bar.

## Domain gotchas

- **IDs.** `Glass.ID` is the NFRC ID, equals `GlazingProperties.NFRC_ID`, and is the `DF_GLASS_TABLE` index. `GlazingProperties.GlazingID` is a different number and is the key into `SpectralData`.
- **Units.** Thickness is mm in the database and buildup dict; `pywincalc` wants metres. Spectral wavelengths are in microns.
- **Gas names are string keys used in three places** that must stay in step: `GASES_NFRC_LOOKUP` / `GASES_EN673_LOOKUP` in `igdb.py` (values are `Gap.ID`s; the EN 673 variants are 100–107), the mixture parser in `en673._parse_gas`, and gstr encoding/decoding in `glass_model_helpers.py`. The percentages in the names must match the IGDB `Gap` names, because `en673` parses them.
- **Gas mixtures live in `GapMixtures`**, as `(ParentID, GapID, Percentage)` component rows. A mixture's own `Gap` row (`nGasses > 0`) carries placeholder coefficients copied from air or SF6; `igdb.lookup_gas_props` must build mixtures from their components, never from the parent row. `GapMixtures` also has two zero-percentage rows under Air (ID 1), so filter on `Percentage > 0`.
- **The current `igdb.sqlite` stores the text `'NULL'` where Access had empty values** (e.g. `Gap.SpecificHeatRatio` for ID 9, `Glass.Comment`, `GlazingProperties.Appearance`). The converter in `scripts/update_igdb.py` now writes real NULLs, but that only takes effect on the next rebuild; until then, don't assume a column is numeric or `None` without checking.
- **Front/back and flipping.** `emis1`/`Rf` are the front (outside-facing) surface, `emis2`/`Rb` the back. A flipped layer swaps them; this logic is repeated in `optics.py`, `en673.py`, `en410.py` and `svg_glass.py`.
- The "generic" uncoated lite is a specific product per thickness (`CLEAR_LOOKUP`, `ULTRACLEAR_LOOKUP`); those IDs are also how a share link works out which lite is the coated one.

## Conventions

- Component IDs live in `EnergyLayoutID`; do not inline ID strings in layouts or callbacks.
- Source files start with `#(c)2026 Jon Robinson. All Rights Reserved.`; the project is licensed AGPL-3.0.
- UI text uses British spelling ("colour").
- Submodules import shared names from the package root (`from glass_explore import ...`), so adding package-level imports to `__init__.py` risks circular imports; `en410.py` imports `en673` inside the function for this reason.
- `logging.info` is used throughout but the app never configures logging, so those messages are not shown unless you add `logging.basicConfig`.
- `functools.cache` on the `igdb` lookups lasts for the process lifetime; restart the server after changing data files.

## Deployment

Railway, detected through `RAILWAY_ENVIRONMENT`. `RAILWAY_ENVIRONMENT_NAME=staging` turns on the Dash dev tools. Production reads its data from a Railway volume mounted at `/igdb` (files under `/igdb/storage/data`), uploaded by hand through the FileBrowser service as the README describes. Updating production data therefore means uploading to the volume, not deploying.

`GLASS_EXPLORE_DATA_SOURCE` is `bundled`, `volume` or `auto`; the code default is `auto` (use the volume when it has all three files, otherwise the deployed `data/`). A deploy contains no `igdb.sqlite`, so `bundled`, or `auto` with an incomplete volume, fails at startup. The parquet files are read from the volume as well, so a repo change to `glass.parquet` does not reach production until it is uploaded.

There is no Procfile or Railway config in the repo, so the start command is set in the Railway dashboard.
