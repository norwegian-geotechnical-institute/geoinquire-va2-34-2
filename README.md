
[![DOI](https://zenodo.org/badge/792319296.svg)](https://zenodo.org/doi/10.5281/zenodo.11073060)

# Introduction 
This repository contains the codes for the Geo-INQUIRE tool to compute the rainfall-induced landslide hazard over an area. This verison of the code assumes a constant 24-h rainfall acummulation over the entire area covered by the susceptibility map.

# Getting Started
1.	Installation process: The landslide hazard tool requires to have installed python and Poetry.
2.	Software dependencies: Python version and dependecies are specified in the Poetry .toml file. 

## REQUIRED INPUT DATA AND FILES:
Input files must be saved (before running the hazard tool) in the ../Data/ folder:
        - `input_variables.csv`: csv file where input rainfall can be specified.
        - `*_sus.tif` : Tile of the susceptibility map over hazard will be computed. Must be downloaded from map repository.
        - `StdMaxDayRain.txt`: Standard deviation of the maximum daily rainfall.

## RUN THE HAZARD TOOL:
1. In place the tile of the susceptibiluty map covering the area you want to compute the hazard in the folder `./Tool-Hazard-Map/input`
2. Modify the `input_variables.csv` excel with the 24 h rainfall acummulation in [mm] you want to check.
2. The code you need to runn is stored in `./Tool-Hazard-Map/Code` folder
3. Before you runn the code make sure you have activated the poetry enviroment: `poetry shell`
4. From the `./Tool-Hazard-Map/Code` folder in the terminal run: `python Hazard.py`
5. The outpurs are stored in the `../Results/constant/` folder.

## OUTPUT:
Results from the Hazard Tool are saved in the following folder which is authomatically generated `../Results/constant/`
1. Rainfall Hazard: Rainfall hazard class in .tif format. Saved as: `./RainHazard/*_RainHazard.tif`
2. Hazard map: in .tif format. Saved as: `./Hazard/*_Hazard.tif`

23.04.2024

# Contribute
Work in a separate branch. Do a pull request to merge with main. Merging with main requires review.

