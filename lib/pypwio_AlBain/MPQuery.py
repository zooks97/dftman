import tabulate

import persistent
import pymatgen
import qgrid

import pandas as pd

class MPQuery(persistent.Persistent):
    def __init__(self, criteria, properties, API):
        self.properties = properties
        self.criteria = criteria
        self.API = API
        self.result = None

    def __repr__(self):
        if self.df:
            return self.df.set_index('material_id').__repr__()

    # TODO: Figure out how to get show_toolbar to work with editing self.df
    #    and self.result
    def display(self):
        display(qgrid.show_grid(self.df))

    def query(self):
        m = pymatgen.MPRester(self.API)
        self.result = m.query(criteria=self.criteria, properties=self.properties, mp_decode=False)
        
    @property
    def df(self):
        if self.result:
            df = pd.DataFrame(self.result)
        else:
            df = pd.DataFrame([])
        return df
    
    def as_dict(self):
        dict_ = {
            'properties': self.properties,
            'criteria': self.criteria,
            'API': self.API,
            'result': self.result
        }
        return dict_
    
    @classmethod
    def from_dict(cls, dict_):
        return cls(**dict_)
