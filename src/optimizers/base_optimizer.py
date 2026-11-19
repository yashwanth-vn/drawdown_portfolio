from abc import ABC, abstractmethod
import pandas as pd

class BaseOptimizer(ABC):
    """Abstract base class for all optimizers"""

    @abstractmethod
    def optimize(self, returns: pd.DataFrame):
        pass
