import tabulate
import json

import pymatgen
import qgrid

import pandas as pd

from monty.json import MontyEncoder, MontyDecoder

class MPQuery():
    def __init__(self, criteria, properties, API):
        '''
        Object representing a query to the Materials Project database
            and its result
        :param criteria: query criteria in pymongo format
        :type criteria: dict
        :param properties: properties to retrieve
        :type properties: list
        :param API: Materials Project API key
        :type API: str
        '''
        self.properties = properties
        self.criteria = criteria
        self.API = API
        self.result = None

    def __repr__(self):
        '''
        Return a dataframe representation of the query results.
        '''
        if not self.df.empty:
            df = self.df.set_index('material_id')
            return df.__repr__()
        else:
            return self.df.__repr__()

#     # TODO: Figure out how to get show_toolbar to work with editing self.df
#     #    and self.result
    def display(self):
        '''
        Display the query results in a qgrid
        '''
        if not self.df.empty:
            df = self.df.set_index('material_id')
        else:
            df = self.df
        display(qgrid.show_grid(df))

    def query(self):
        '''
        Submit the query to the materials project and retrieve
            the results
        '''
        m = pymatgen.MPRester(self.API)
        # mp_decode set to false makes sure that the returned
        #     Structure and other objects are dictionaries.
        # This is useful for creating database keys by avoiding
        #     needing to ensure all objects are serializable
        self.result = m.query(criteria=self.criteria,
                              properties=self.properties,
                              mp_decode=False)
        
    @property
    def df(self):
        if self.result:
            df = pd.DataFrame(self.result)
        else:
            df = pd.DataFrame([])
        return df
    
    def as_dict(self):
        dict_ = {
            '@module': self.__class__.__module__,
            '@class': self.__class__.__name__,
            'properties': self.properties,
            'criteria': self.criteria,
            'API': self.API,
            'result': self.result
        }
        return dict_
    
    @classmethod
    def from_dict(cls, dict_):
        decoded = {key: MontyDecoder().process_decoded(value)
                   for key, value in dict_.items()
                   if not key.startswith("@")}
        return cls(**decoded)
