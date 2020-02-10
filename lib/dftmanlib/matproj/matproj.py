from . import MPQuery

def mpquery_helper(criteria, properties, API, postprocess=(lambda x: x)):
    '''
    Helper function for running Materials Project queries in
        DFTman
    Ensures that required properties for DFT calculations like
        material ID, formula, elements, and structure are retrieved
    :param criteria: query criteria in pymongo format
    :type criteria: dict
    :param properties: properties to retrieve from the Materials Project
    :type properties: list
    :param API: Materials Project API key
    :type API: str
    :param postprocess: postprocessing function to further refine results
    :type postprocess: function
    '''
    required_properties = ['job_id', 'pretty_formula',
                           'elements', 'structure']
    if properties:
        properties += required_properties
    else:
        properties = required_properties

    mpquery = MPQuery(criteria, sorted(properties), API, postprocess)
    return mpquery