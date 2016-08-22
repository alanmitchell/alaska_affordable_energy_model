"""
config.py

    config info for cd yaml file
"""
COMPONENT_NAME = "diesel efficiency"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

## List of yaml key/value pairs
yaml = {'enabled': False,
        "project details": {'phase': 'Reconnaissance',
                            'capital costs': UNKNOWN,
                            'operational costs': UNKNOWN,
                            'expected years to operation': 3,
                            },
        'data': IMPORT,
        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',
        'efficiency improvment': 1.1,
        'o&m costs': {150: 84181.00,
                      360: 113410.00,
                      600: 134434.00,
                      'else':103851.00 }
        }

## default values for yaml key/Value pairs
yaml_defaults = {'enabled': True,
        'lifetime': 20,
        #~ 'start year': 2017,
        }
    
## order to save yaml
yaml_order = ['enabled', 'lifetime', 'start year']

## comments for the yaml key/value pairs
yaml_comments = {'enabled': '',
        'lifetime': 'number years <int>',
        'start year': 'start year <int>'}



## list of prerequisites for module
prereq_comps = [] ## FILL in if needed

## List of raw data files required for wind power preproecssing 
raw_data_files = ['project_development_timeframes.csv']# fillin

## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = []
