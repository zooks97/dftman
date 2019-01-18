import tinydb

class SubmitDoc():
    
    def __init__(self, db_path='./db.json', table_name='_default'):
        self.doc_id = None
        self.db_path = db_path
        self.table_name = table_name
        # 
        pass
    
    def drop(self):
        pass
    
    def insert(self):
        pass
    
    def upsert(self):
        pass
    
    def update(self):
        pass
    
    def get(self):
        pass
    
    @property
    def db(self):
        pass
    
    @property
    def table(self):
        pass  
    
    
# How can a calculation easily be modified and resubmittied?
# How will error management occur?
class PWDoc():
    
    def __init__(self):
        pass