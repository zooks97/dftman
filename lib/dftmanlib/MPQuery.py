import tabulate

import persistent
import pymatgen
import qgrid

import pandas as pd


class MPQuery(persistent.Persistent):
    def __init__(self, criteria, properties, API):
        '''
        :param criteria: dictionary of query criteria
        :param properties: list of properties to retrieve
        :param API: Materials Project API key string
        '''
        self.properties = properties
        self.criteria = criteria
        self.API = API
        self.result = None

    def __repr__(self):
        '''
        Return a dataframe representation of the query results.
        '''
        if self.df:
            return self.df.set_index('material_id').__repr__()
        else:
            return self.df.__repr__()

#     # TODO: Figure out how to get show_toolbar to work with editing self.df
#     #    and self.result
#     def display(self):
#         '''
#         Display the query results in a qgrid
#         '''
#         display(qgrid.show_grid(self.df))

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
            'properties': self.properties,
            'criteria': self.criteria,
            'API': self.API,
            'result': self.result
        }
        return dict_
    
    @classmethod
    def from_dict(cls, dict_):
        return cls(**dict_)
