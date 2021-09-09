
from pyiron_base import HasStorage
from abc import ABC, abstractmethod
from pyiron_continuum.schroedinger.mesh import RectMesh
from typing import Type
import numpy as np


class Potential(HasStorage, ABC):
    """
    An abstract class for "potentials" that map (d, l, m, n)-dimensional `RectMesh` objects onto (l, m, n)-dimensional
    fields.
    """

    @abstractmethod
    def __call__(self, mesh: Type[RectMesh]) -> np.ndarray:
        pass


class SquareWell(Potential):
    """
    Square potentials occupying some fraction of the mesh in each direction.

    TODO: Allow different widths in each dimension.

    TODO: Units?

    Attributes:
        width (float): What fraction of the mesh to set to a potential of 0. (Default is 0.5, half the space.)
        depth (float): How high to make the rest of the space. (Default is 1.)
    """

    def __init__(self, width=0.5, depth=1):
        """
        Instantiate a square well.

        Args:
            width (float): What fraction of the mesh to set to a potential of 0. (Default is 0.5, half the space.)
            depth (float): How high to make the rest of the space. (Default is 1.)
        """
        super().__init__()
        self.storage.width = width
        self.storage.depth = depth

    @property
    def width(self):
        return self.storage.width

    @width.setter
    def width(self, width):
        self.storage.width = width

    @property
    def depth(self):
        return self.storage.depth

    @depth.setter
    def depth(self, depth):
        self.storage.depth = depth

    def __call__(self, mesh: Type[RectMesh]) -> np.ndarray:
        potential = np.ones_like(mesh.mesh) * self.depth
        lengths = np.array([np.amax(m) for m in mesh.mesh]) + mesh.steps
        mask = np.array([
            (m >= 0.5 * l * (1 - self.width)) * (m < 0.5 * l * (1 + self.width))
            for m, l in zip(mesh.mesh, lengths)
        ])
        potential[mask] = 0
        return np.amax(potential, axis=0)


class Sinusoidal(Potential):
    """
    A product of sines that repeats periodically in each dimension of the mesh on which it is evaluated.

    TODO: Allow different number of waves in each dimension.

    TODO: Units?

    TODO: Fix periodicity bug.

    Attributes:
        width (float): What fraction of the mesh to set to a potential of 0. (Default is 0.5, half the space.)
        depth (float): How high to make the rest of the space. (Default is 1.)
    """

    def __init__(self, n_waves=1, amplitude=1):
        """
        Instantiate a periodic product of sines.

        Args:
            n_waves (float): How many wave repetitions to have along all dimensions. (Default is 1.)
            amplitude (float): The amplitude of the waves. (Default is 1.)
        """
        super().__init__()
        self.storage.n_waves = self._clean_waves(n_waves)
        self.storage.amplitude = amplitude

    def _clean_waves(self, n_waves):
        if not np.issubdtype(type(n_waves), np.integer):
            raise TypeError(
                f'Waves must come in integers to obey periodic boundary conditions, but got {type(n_waves)}'
            )
        return n_waves

    @property
    def n_waves(self):
        return self.storage.n_waves

    @n_waves.setter
    def n_waves(self, n):
        self.storage.n_waves = self._clean_waves(n)

    @property
    def amplitude(self):
        return self.storage.amplitude

    @amplitude.setter
    def amplitude(self, a):
        self.storage.amplitude = a

    def __call__(self, mesh: Type[RectMesh]) -> np.ndarray:
        return np.prod([self.amplitude * np.sin(self.n_waves * m) for m in mesh.mesh], axis=0)
