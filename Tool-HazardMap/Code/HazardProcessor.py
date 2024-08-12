"""
HazardProcessor.py

Implements the calculation of the hazard maps of the GIRI model.

Rosa M Palau (NGI)     08.04.2024
"""
import numpy as np
import pandas as pd

from pathlib import Path
from multiprocessing import Process, Semaphore
import cProfile
import pstats
from abc import ABC, abstractmethod

class HazardProcessor(ABC):
    def __init__(self, **kwargs):
        """
        Runs the script by calling multi_process_rasters or process_raster according to the
        boolean variable MULTIPROCESSING. It also creates an output folder, and adds a
        profiler and a file handler to logger.
        """
        # paths
        self.path_bas = Path().resolve().parent
        self.path_data = self.path_bas / "Data"
        
        # projection
        self.epsg_wgs84 = kwargs["epsg_wgs84"]
        
        # classes
        self.sclass = kwargs["sclass"]
        self.I_lim = kwargs["I_lim"]
        
        # read user-defined parameters from excel file
        inparam_file = self.path_data / "input_variables.xlsx"
        df = pd.read_excel(inparam_file, header = None)
        UserParam = dict(zip(df[0], df[1]))
        self.mode = UserParam["mode"]
        
        if UserParam["mode"] == "constant":
            self.in_acum = np.float32(UserParam["input rain"])
        if UserParam["mode"] == "map":
            self.name_in_rain = UserParam["input rain map name"]
    
        # Multiprocess param
        self.MULTIPROCESSING = kwargs['MULTIPROCESSING']
        self.MAX_NUMBER_OF_PROCESSES = kwargs['MAX_NUMBER_OF_PROCESSES']
        
        # Check if the folder for output files exists. Create it if not.
        self.path_out = self.path_bas / "Results"
        if not self.path_out.exists():
            self.path_out.mkdir(parents=True, exist_ok=True)
        
        # # Create profiler
        # profiler = cProfile.Profile()
        # profiler.enable()

        # Run script
        if self.MULTIPROCESSING:
            self.multi_process_rasters()
        else:
            self.process_rasters()

        # profiler.disable()
    
    def multi_process_rasters(self):
        """
        Calls CompGiriHazard for each susceptibility map in the Data folder
        by spawning multiple processes.
        """
        # Find files that end with '_sus.tif'
        files = list(self.path_data.glob('*_sus'))
        
        processes = []
        sema = Semaphore(self.MAX_NUMBER_OF_PROCESSES)
        
        for file_susc in files:
                sema.acquire() # Subtract 1 from sema. Block if allready empty.
                
                # Get name of the raster file
                file_name = Path(file_susc).name
                file_name1 = Path(file_susc).stem
                
                p = Process(target=self.CompGiriHazard,
                            args=(file_susc, file_name1, sema)) ## check
                p.start()
                processes.append(p)
        
                # Finish one group at the time.
                for p in processes:
                    p.join()

    def process_rasters(self):
        """
        Calls CompGiriHazard for each susceptibility map in the Data folder.
        """
        # Find files that end with '_sus.tif'
        files = list(self.path_data.glob('*_sus.tif'))
        
        for file_susc in files:
                # Get name of the raster file
                file_name = Path(file_susc).name
                file_name1 = Path(file_susc).stem
                self.CompGiriHazard(file_susc = file_susc, file_name1 = file_name1)
                
    @abstractmethod
    def CompGiriHazard(self, file_susc, file_name1, sema=None):
        """
        Calls successive operations on input_rasters. May be edited to include other operations.
        :param output_dir: Directory to place folder for output from methods.
        :param input_raster: Path to DEM for processing.
        :sema: Semapore (to limit number of processes).
        """
        # This part needs to be implemented in subclass.
        pass 