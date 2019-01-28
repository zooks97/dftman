import persistent

class EOSWorkflow(persistent.Persistent):
    
    def __init__(self, structure, pseudo, inputs, db,
                 strain_min=0.95, strain_max=1.15, n_strains=8):
        pass