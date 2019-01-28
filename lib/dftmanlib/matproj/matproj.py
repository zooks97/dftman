from . import MPQuery

def mpquery_helper(criteria, properties, API):
        required_properties = ['material_id', 'pretty_formula',
                               'elements', 'structure']
        if properties:
            properties += required_properties
        else:
            properties = required_properties
            
        mpquery = MPQuery(criteria, sorted(properties), API)
        return mpquery