import pandas as pd
import tabulate
import pymatgen

class MPQuery(object):
    def __init__(self, criteria, properties, API):
        self.properties = properties
        self.criteria = criteria
        self.API = API
        self.result = None

    def __repr__(self):
        return self.df.__repr__()

    # TODO: Figure out how to get show_toolbar to work with editing self.df
    #    and self.result
    def display(self):
        display(qgrid.show_grid(self.df))

    def query(self):
        m = pymatgen.MPRester(self.API)
        self.result = m.query(criteria=self.criteria, properties=self.properties)

    @property
    def df(self):
        return pd.DataFrame(self.result)
    
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
