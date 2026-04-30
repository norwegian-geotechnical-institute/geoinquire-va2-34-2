
[![DOI](https://zenodo.org/badge/792319296.svg)](https://zenodo.org/doi/10.5281/zenodo.11073060)

# Introduction 
This repository contains the codes for the Geo-INQUIRE tool to compute the rainfall-induced landslide hazard over an area. This verison of the code can assume a constant 24-h rainfall acummulation over the entire area covered by the susceptibility map, or use a user-provided map with the 24h rainfall acummulations over the area covered by the susceptibility map.

Precipitation-induced landslide hazard is one of the services included in the GEO-INQUIRE Virtual Access to products enabling curiosity-driven science for geohazard and multi-risk assessment
(see https://www.geo-inquire.eu/virtual-access/geohazard-and-multi-risk-assessment for details).

![GEO-INQUIRE project logo](Geo-INQUIRE_logo_small.png)

# Getting Started

## Before you start
This tool cannot be run until a susceptibility tile (`*_sus.tif`) has been downloaded and placed in `Tool-HazardMap/Data/`.

## Required input files
Before running the tool, the following files must be present in `Tool-HazardMap/Data/`:

- `input_variables.yaml`: configuration file for the rainfall input
- `*_sus.tif`: susceptibility tile(s) covering the area of interest
- `StdMaxDayRain.asc`: standard deviation of the maximum daily rainfall
- `MeanMaxDayRain.asc`: mean of the maximum daily rainfall

If you want to use spatially variable rainfall, also place your rainfall raster in `Tool-HazardMap/Data/`. The map must be in `.tif` format, cover the area of the susceptibility tile(s), and use WGS84 (`EPSG:4326`).

## Download a susceptibility tile
The susceptibility data are available at [https://zenodo.org/records/15119418](https://zenodo.org/records/15119418).

Each susceptibility tile covers a 5 degree x 5 degree area, and the tile name encodes the lower-left corner of the tile:
- `n` / `s` = north / south latitude
- `e` / `w` = east / west longitude

Example: `n60e005_sus.tif` covers latitude 60 to 65 N and longitude 5 to 10 E.

For Kvam, Norway (around 60.37 N, 6.14 E), the lower boundaries are 60 and 5, so the correct tile is `n60e005_sus.tif`.

### Linux example
```bash
cd Tool-HazardMap/Data

wget -O Landslide_Susceptibility_GIRI_W5E5.zip \
        https://zenodo.org/records/15119418/files/Landslide_Susceptibility_GIRI_W5E5.zip?download=1

unzip -l Landslide_Susceptibility_GIRI_W5E5.zip | grep "n60e005_sus.tif"

unzip -j Landslide_Susceptibility_GIRI_W5E5.zip \
        "dem_tif_n60e000/n60e005_sus.tif" \
        -d .
```

Notes:
- Use `-j` to extract only the file, without the subfolder structure.
- If you use the SSP126 scenario, replace the archive filename with `Landslide_Susceptibility_GIRI_SSP126.zip`.

## Configure the tool
Edit `Tool-HazardMap/Data/input_variables.yaml`.

Use `mode: constant` for a single rainfall value over the whole area, or `mode: map` for a rainfall raster.

Example configuration:

```yaml
mode: constant
input_rain: 80
input_rain_map_name: your_rainfall_map_name
```

For `mode: constant`, the tool reads `input_rain` as the 24-hour rainfall accumulation in millimeters.

For `mode: map`, the tool reads `input_rain_map_name` as the name of the rainfall raster without the `.tif` extension.

## Install dependencies
The Python version and dependencies are defined in `Tool-HazardMap/Code/pyproject.toml`.

From `Tool-HazardMap/Code`, run:

```bash
Code$ poetry install
```

## Run the tool
From `Tool-HazardMap/Code`, run:

```bash
Code$ poetry run python Hazard.py
```

## Outputs
Results are written to `Tool-HazardMap/Results/{mode}/`. The tool creates:
1. Rainfall hazard raster: `RainHazard/*_RainHazard.tif`
2. Landslide hazard raster: `Hazard/*_Hazard.tif`


# Contribute
Work in a separate branch. Do a pull request to merge with main. Merging with main requires review.

