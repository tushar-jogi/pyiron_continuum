from pyiron_base import GenericJob, DataContainer
import numpy as np
import matplotlib.pyplot as plt
from damask import Grid
from damask import Result
from damask import seeds
import pyvista as pv
import h5py
import os

class DAMASKjob(GenericJob):
    def __init__(self, project, job_name):
        super(DAMASKjob, self).__init__(project, job_name)
        self.input = DataContainer()
        self.output = DataContainer()
        self._material = None 
        self._load = None
        self._geometry = None
        self._damask_results = None
        self.input.create_group('geometry')
        self.input.create_group('material')
        self.input.create_group('load')
        self.output.create_group('stress')
        self.output.create_group('strain')
        self.executable = "DAMASK_grid -l tensionX.yaml -g damask.vtr" # this will be updated with new damask version
        
    @property
    def material(self):
        return self._material
    
    @material.setter
    def material(self, path=None):
        self._material = self.input.material.read(path)
        
    @property
    def load(self):
        return self._load
    
    @load.setter
    def load(self, path=None):
        self._load = self.input.load.read(path)
    
    def load_write(self):
        self.input.load.write('tensionX.yaml')
        
    def material_write(self):
        self.input.material.write('material.yaml')
    
    def geometry_write(self):
        seed = seeds.from_random(self.input.geometry['size'], self.input.geometry['grains'])
        new_geom = Grid.from_Voronoi_tessellation(self.input.geometry['grid'], self.input.geometry['size'], seed)
        new_geom.save(os.path.join(self.working_directory, "damask"))
    
    def write_input(self):
        os.chdir(self.working_directory)
        self.load_write()
        self.geometry_write()
        self.material_write()
             
    def collect_output(self):
        self.load_results()
        self.stress()
        self.strain()
    
    def load_results(self, file_name="damask_tensionX.hdf5"):
        if self._damask_results is None:
            self._file_name = os.path.join(self.working_directory, file_name)
            self._damask_results = Result(self._file_name)
            self._damask_results.add_stress_Cauchy()
            self._damask_results.add_strain()
            self._damask_results.add_equivalent_Mises('sigma')
            self._damask_results.add_equivalent_Mises('epsilon_V^0.0(F)')
            self._damask_results.add_calculation('avg_sigma',"np.average(#sigma_vM#)")
            self._damask_results.add_calculation('avg_epsilon',"np.average(#epsilon_V^0.0(F)_vM#)")
            self._damask_results.save_VTK(['sigma','epsilon_V^0.0(F)','sigma_vM','epsilon_V^0.0(F)_vM'])
        return self._damask_results
    
    def stress(self):
        """
        return the stress as a numpy array
        Parameters
        ----------
        job_file : str
          Name of the job_file
        """
        self.load_results()
        if self._damask_results is not None:
            stress_path = self._damask_results.get_dataset_location('avg_sigma')
            stress = np.zeros(len(stress_path))
            hdf = h5py.File(self._damask_results.fname)
            for count,path in enumerate(stress_path):
                stress[count] = np.array(hdf[path])
            self.output.stress = np.array(stress)/1E6

    def strain(self):
        """
        return the strain as a numpy array
        Parameters
        ----------
        job_file : str
          Name of the job_file
        """
        self.load_results()
        if self._damask_results is not None:
            stress_path = self._damask_results.get_dataset_location('avg_sigma')
            strain = np.zeros(len(stress_path))
            hdf = h5py.File(self._damask_results.fname)
            for count,path in enumerate(stress_path):
                strain[count] = np.array(hdf[path.split('avg_sigma')[0]+ 'avg_epsilon'])
            self.output.strain = strain
    
    @property
    def plot_stress_strain(self):
        """
        Plot the stress strain curve from the job file
        Parameters
        ----------
        self.stress
        self.strain
        """
        #stress = self.stress()
        #strain = self.strain()
        plt.plot(self.output.strain, self.output.stress, linestyle='-', linewidth='2.5')
        plt.xlabel(r'$\varepsilon_{VM} $', fontsize=18)
        plt.ylabel(r'$\sigma_{VM}$ (MPa)', fontsize=18)
     
    def mesh(self, inc=20):
        """
        mesh
        """
        mesh = pv.read(os.path.join(self.working_directory, self._file_name.split('.')[0] + f'_inc0{inc}.vtr'))
        return mesh
