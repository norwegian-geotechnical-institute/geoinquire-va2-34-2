"""
Hazard.py

Implements the calculation of the hazard of the GIRI model for the cases:
    1) mode == "constant" --> Generic rainfall, constat over an area.
                                Rainfall amount specified by user in .csv file.
    2) mode == "map" --> User-provided raster with 24h rainfall acummulations map
                        .tif format, wgs84 projection. Filename specified in .csv file.
                        
as a subclass of HazardProcessor.


IMPORTANT:
    - mode (constant/map) must be specified by the user in the "/Data/input_variables.xlsx" file.
    - mode == constant: Rainfall ammount set by user as "input constant rain" in the ".xlsx" file.
    - mode == map: 24h rainfall map provided by the user in wgs84. Filename set in ".xlsx" file.

INPUT:
    Required input files to be saved in the ../Data/ folder:
        - input_variables.csv: csv file where input rainfall can be specified.
        - *_sus.tif: Tile of the susceptibility map over hazard will be computed.
                            Must be downloaded from map repository.
        - StdMaxDayRain.txt: Standar deviation of the maximum daily rainfall. 

OUTPUT:
    Results saved in ../Results/constant/ folder
        - Rainfall Hazard: Rainfall hazard class in .tif format. Saved as: ./RainHazard/{}_RainHazard.tif
        - Hazard map: in .tif format. Saved as: ./Hazard/{}_Hazard.tif

Rosa M Palau (NGI)            08.08.2024
"""
import numpy as np
import rasterio
import rioxarray
import xarray as xr

#import geojson
#import json
#from shapely.geometry import shape, mapping, Point, LineString
#from shapely.ops import unary_union

from pyproj import Proj, Transformer

from pathlib import Path

from HazardProcessor import HazardProcessor

## Define input parameters
KWARGS = {
    "sclass": [1, 2, 3, 4, 5],
    "I_lim": [0.7, 2.0, 3.7, 5.0],
    "epsg_wgs84": 4326,
    'MULTIPROCESSING': False,
    'MAX_NUMBER_OF_PROCESSES': 10,
}

class CalcHazard(HazardProcessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def read_raster(self, path_map):
        """
        Implements rasterio open to read a raster map. Saves variables which are interesting 
            INPUT: 
                -path_map: file of the susceptibility map
        """
        # function to read raster maps with rasterio
        
        with rasterio.open(path_map) as src_dataset:
            print("Reading data: {}".format(path_map))
            kwds = src_dataset.profile
            features_in = src_dataset.read(1, masked = True).astype(float).filled(np.nan)
            bbox = src_dataset.bounds

            top = bbox.top
            bottom = bbox.bottom
            left = bbox.left
            right = bbox.right

        ncols = kwds["width"]
        nrows = kwds["height"]
        
        return(features_in, ncols, nrows, kwds, bbox)
    
    def read_susceptibility_classified(self, file_susc):
        """
        Reads susceptibility map using rasterio.
        Converts into xarray
            INPUT: 
                -file_susc: file of the susceptibility map
        """
        
        # read raster
        susc_class, ncols, nrows, kwds, bbox = self.read_raster(file_susc)
        dx = kwds["transform"][0]
        
        crs = kwds["crs"]
        nodata = kwds["nodata"]
        transform = kwds["transform"]
        
        # Create coordinate arrays using bounding box
        x_coords = np.linspace(bbox.left, bbox.right, num = ncols)
        y_coords = np.linspace(bbox.top, bbox.bottom, num = nrows)
        
        # Convert the raster data to xarray DataArray
        susc_da = xr.DataArray(susc_class, coords=[('y', y_coords), ('x', x_coords)])
        
        # Assign CRS and nodata value to the DataArray attributes
        susc_da.attrs['crs'] = crs
        susc_da.attrs['nodata'] = nodata
        susc_da.attrs["_FillValue"] = np.nan

        return(susc_da, ncols, nrows, kwds, bbox, dx, crs) 
        
    def OpenRainNorm(self, susc_da, crs_susc):#(self, susc_da, bbox_susc, ncols_susc, nrows_susc, dx_susc, kwds_susc):
        """
        Opens rainfall data that is required for the normalization of the rain.
        Reprojects, cuts and resamples the raster to cover the area of the susc map.
            INPUT: 
                -bbox_susc: bounding box of susceptibility map
                -ncols_susc, nrows_susc: umber of columns and number of rows of susc map
        """
        
        # files to read
        file_mean_day_rain = self.path_data / "MeanMaxDayRain.asc"
        file_std_day_rain = self.path_data / "StdMaxDayRain.txt"

        
        # read rasters
        rioxarray.set_options(export_grid_mapping = True)
        MeanRain = rioxarray.open_rasterio(file_mean_day_rain)
        StdRain = rioxarray.open_rasterio(file_std_day_rain)
        
        # Make sure we have crs information
        MeanRain.rio.write_crs(crs_susc, inplace = True) # Write crs in data array (.asc don't have crs)
        StdRain.rio.write_crs(crs_susc, inplace = True) # Write crs in data array (.asc don't have crs)
        
        # Reproject MeanRain/StdRain object to match the resolution, projection, and region of susc_da.
        repr_mean = MeanRain.rio.reproject_match(susc_da)
        repr_std  = StdRain.rio.reproject_match(susc_da)
        
        # Get only values (array)
        repr_mean = repr_mean.isel(band=0).values
        repr_std  = repr_std.isel(band=0).values
        
        return(repr_mean, repr_std)
        
    
    def CreateCntRain(self, ncols, nrows):
        """
        Creates am empty array like the input-susceptibility map filled with constant user-defined
        24 h rainfall acummmulation value. 
            INPUT: 
                -ncols, nrows: number of columns and number of rows 
        """
        acum24 = np.full((nrows, ncols), self.in_acum)
        return(acum24)


    def ReadInRainMap(self, susc_da, crs_susc):
        """
        Opens provided maps with 24h rainfall acumulations.
        Clips and resamples rainfall to the extent of susc map. 
            INPUT: 
                -bbox_susc: bounding box of susceptibility map
                -ncols_susc, nrows_susc: umber of columns and number of rows of susc map
        """
        nameinfile = self.name_in_rain + ".tif"
        file_in_rain = self.path_data / nameinfile
        
        rioxarray.set_options(export_grid_mapping = True)
        acum24 = rioxarray.open_rasterio(file_in_rain)
        
        # Reproject acum24h object to match the resolution, projection, and region of susc_da.
        repr_acum24 = acum24.rio.reproject_match(susc_da)
        
        # Get only values (array)
        repr_acum24 = repr_acum24.isel(band=0).values
        
        # Make sure nan values are set as np.nan (no negative rainfall acummulations).
        repr_acum24 = np.where(repr_acum24 < 0, np.nan, repr_acum24)
        
        return(repr_acum24)


    def ComputeRainCnt(self, MeanRain, StdRain, acum24):
        """
        Normalizes 24h rainfall acummulations.
            INPUT:
                - MeanRain: array with mean of the 24h rainfall acummulations over area.
                - StdRain: array with standard deviation of 24h rainfall acummulations over area.
                - acum24: array with the event 24h rainfall acummulations 
    
        """
        # Normalize
        I24norm_da = (acum24-MeanRain)/StdRain
        
        return(I24norm_da)
    
    def ComputeRainHazard(self, I24norm_da, I_lim, file_name1, ncols, nrows, kwds):
        """
        Implements computation of the rainfall hazard.
            INPUT: 
                -I24norm_da, normalized rainfall map array 
                -I_lim: input array with limits of the rainfall hazard classes
                -file_name1, input name of he susceptibility map sheet
                -ncols, nrows: number of columns and number of rows
                -kwds
        """
        
        aux = I24norm_da # raster array
        #time_coord = aux.time
        
        RainHazard_aux = np.zeros_like(aux)
        
        # Assign rain hazard
        for ii in range(len(I_lim)): 
            if ii == 0:
                mask = (aux <= ii)
                RainHazard_aux = np.where(mask, ii + 1, RainHazard_aux)
            else:
                if ii < 3:
                    mask = (aux <= ii) & (aux > ii-1)
                    RainHazard_aux = np.where(mask, ii + 1, RainHazard_aux)
                else:
                    mask = (aux <= ii) & (aux > ii-1)
                    RainHazard_aux = np.where(mask, ii + 1, RainHazard_aux)
                    
                    mask = (aux > ii)
                    RainHazard_aux = np.where(mask, ii + 2, RainHazard_aux)
        
        # Save to file
        folder_out = self.path_out / self.mode
        if not folder_out.exists(): # Create the folder if it doesn't exist
            folder_out.mkdir(parents=True, exist_ok=True)
        
        folder_out = self.path_out / self.mode / "RainHazard"
        if not folder_out.exists(): # Create the folder if it doesn't exist
            folder_out.mkdir(parents=True, exist_ok=True)
            
        prefix = file_name1.split('_')[0]
            
        file_save_name = prefix + "_RainHazard.tif"
        file_save = folder_out / file_save_name
        
        # Save Rain Hazard raster
        outfile = file_save
        with rasterio.open(outfile, "w", **kwds) as dst_dataset:
            dst_dataset.write(RainHazard_aux, 1)
        
        return(RainHazard_aux)
    
    def ComputeHazard(self, susc_da, RainHazard_aux, file_name1, kwds):
        """
        Implements computation of the hazard matrix.
            INPUT: 
                -susc_da, Susceptibility map array 
                -RainHazard_aux, rainfall hazard array
                -file_name1, input name of he susceptibility map sheet
                -kwds
        """
        
        # Hazard matrix
        hazard_aux = np.zeros_like(susc_da) # initialise array to store the hazard
        
        # Check hazard by going through hazard matrix
        hazard_aux = np.where(np.isnan(susc_da), np.nan, hazard_aux)
        
        mask = (susc_da == 2) & (RainHazard_aux == 2)
        hazard_aux = np.where(mask, 1, hazard_aux)
        mask = (susc_da == 2) & (RainHazard_aux == 3)
        hazard_aux = np.where(mask, 2, hazard_aux)
        mask = (susc_da == 2) & (RainHazard_aux == 4)
        hazard_aux = np.where(mask, 3, hazard_aux)
        mask = (susc_da == 2) & (RainHazard_aux == 5)
        hazard_aux = np.where(mask, 5, hazard_aux)
        
        mask = (susc_da == 3) & (RainHazard_aux == 2)
        hazard_aux = np.where(mask, 2, hazard_aux)
        mask = (susc_da == 3) & (RainHazard_aux == 3)
        hazard_aux = np.where(mask, 3, hazard_aux)
        mask = (susc_da == 3) & (RainHazard_aux == 4)
        hazard_aux = np.where(mask, 5, hazard_aux)
        mask = (susc_da == 3) & (RainHazard_aux == 5)
        hazard_aux = np.where(mask, 10, hazard_aux)
        
        mask = (susc_da == 4) & (RainHazard_aux == 2)
        hazard_aux = np.where(mask, 3, hazard_aux)
        mask = (susc_da == 4) & (RainHazard_aux == 3)
        hazard_aux = np.where(mask, 5, hazard_aux)
        mask = (susc_da == 4) & (RainHazard_aux == 4)
        hazard_aux = np.where(mask, 10, hazard_aux)
        mask = (susc_da == 4) & (RainHazard_aux == 5)
        hazard_aux = np.where(mask, 15, hazard_aux)
        
        mask = (susc_da == 5) & (RainHazard_aux == 2)
        hazard_aux = np.where(mask, 5, hazard_aux)
        mask = (susc_da == 5) & (RainHazard_aux == 3)
        hazard_aux = np.where(mask, 10, hazard_aux)
        mask = (susc_da == 5) & (RainHazard_aux == 4)
        hazard_aux = np.where(mask, 15, hazard_aux)
        mask = (susc_da == 5) & (RainHazard_aux == 5)
        hazard_aux = np.where(mask, 20, hazard_aux)
        
        # Save to file
        folder_out = self.path_out / self.mode / "Hazard"
        if not folder_out.exists(): # Create the folder if it doesn't exist
            folder_out.mkdir(parents=True, exist_ok=True)
        
        prefix = file_name1.split('_')[0]
        
        file_save_name = prefix + "_Hazard.tif"
        file_save = folder_out / file_save_name
        
        # Save Rain Hazard raster
        outfile = file_save
        with rasterio.open(outfile, "w", **kwds) as dst_dataset:
            dst_dataset.write(hazard_aux, 1)
        
        return(hazard_aux)
    
    def CompGiriHazard(self, file_susc, file_name1, sema=None):
        """
        Implements different steps for hazard computation. 
            INPUT:
            -file_susc: file of the susceptibility map
            -file_name1: name of he susceptibility map sheet
        """
        # read susceptibility raster 
        susc, ncols, nrows, kwds, bbox, dx, crs = self.read_susceptibility_classified(file_susc)
        
        # Check if we use constant user-defined rain or an input rainfall map.
        if self.mode == "constant":
            # Create rainfall grid.
            acum24 = self.CreateCntRain(ncols, nrows)
        if self.mode == "map":
            # Read rainfall acummulation map
            acum24 = self.ReadInRainMap(susc, crs) 
        
        # Compute mean and sd to normalize rain.
        MeanRain, StdRain = self.OpenRainNorm(susc, crs)

        # Normalize rain.
        I24norm = self.ComputeRainCnt(MeanRain, StdRain, acum24)
        
        # Compute rainfall hazard.
        print("Computing rainfall hazard")
        RainHazard = self.ComputeRainHazard(I24norm, self.I_lim, file_name1, ncols, nrows, kwds)
        
        # Compute landslide hazard.
        print("Computing hazard")
        LandsHazard = self.ComputeHazard(susc, RainHazard, file_name1, kwds)
        
        if sema is not None: 
            sema.release() # Release will add 1 to sema.
    
if __name__ == '__main__':
    CalcHazard(**KWARGS)
    

    
    