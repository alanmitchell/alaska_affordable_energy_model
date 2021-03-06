"""
Residential Efficiency outputs
------------------------------

output functions for Residential Efficiency component

"""
import os.path
import aaem.constants as constants
from aaem.components import comp_order
import aaem_summaries.web_lib as wl

from pandas import DataFrame

COMPONENT_NAME = "Residential Energy Efficiency"
DESCRIPTION = """
    This component calculates the potential change in heating fuel usage from residential-building energy efficiency improvements.
"""

def generate_web_summary (web_object, community):
    """generate html summary for a community.
    generates web_object.directory/community/<component>.html and
    associated csv files.

    Parameters
    ----------
    web_object: WebSummary
        a WebSummary object
    community: str
        community name

    See also
    --------
    aaem.web :
        WebSummary object definition
    """
    ## get the template
    template = web_object.component_html

    ## get the component (the modeled one)

    modeled = web_object.results[community][COMPONENT_NAME]
    start_year = modeled.start_year
    end_year = modeled.actual_end_year

    ## for make table functions
    projects = {'Modeled ' + COMPONENT_NAME:  modeled}

    ## get forecast stuff (consumption, generation, etc)
    fc = modeled.forecast

    generation = fc.generation['generation diesel'].\
                                        ix[start_year:end_year]

    ## get the diesel prices
    diesel_price = web_object.results[community]['community data'].\
        get_item('community','diesel prices').ix[start_year:end_year]

    ## get diesel generator efficiency
    eff = modeled.cd['diesel generation efficiency']



    ## get generation fuel costs per year (modeled)
    base_cost = generation/eff * diesel_price
    base_cost.name = 'Base Cost'
    base_cost = DataFrame(base_cost)
    base_cost['Base Cost'] = (modeled.baseline_HF_cost + modeled.baseline_kWh_cost)[:modeled.actual_project_life]
    table1 = wl.make_costs_table(community, COMPONENT_NAME, projects, base_cost,
                              web_object.directory)

    ## get generation fuel used (modeled)
    base_con = generation/eff
    base_con.name = 'Base Consumption'
    base_con = DataFrame(base_con)
    #~ base_con['Base Consumption'] = modeled.baseline_kWh_consumption
    #~ table2 = wl.make_consumption_table(community, COMPONENT_NAME,
                                    #~ projects, base_con,
                                    #~ web_object.directory,
                                    #~ 'proposed_kWh_consumption')


    base_con['Base Consumption'] = modeled.baseline_fuel_Hoil_consumption[:modeled.actual_project_life]
    table3 = wl.make_consumption_table(community, COMPONENT_NAME,
                                    projects, base_con,
                                    web_object.directory,
                                    'savings_HF')
    #~ table3[0][-1]
    year = modeled.comp_specs['data']['Year']
    current = [
        {'words':'Households ('+ str(int(year)) + ')' ,
                'value': int(modeled.comp_specs['data']['Total Occupied'])},

        {'words':'Households with BEES certification' + \
                ' ('+ str(int(year)) +')',
            'value': str(modeled.comp_specs['data']['BEES Number'])},
        {'words':
            'Households participating in weatherization of home ' + \
            'energy rebate programs ('+ str(int(year)) +')',
         'value': str(modeled.comp_specs['data']['Post-Retrofit Number'])},

         {'words':'Estimated Total Households (' +\
            str(int(modeled.start_year)) +')',
            'value': modeled.init_HH},

                ]

    ## info for modeled
    info = create_project_details_list (modeled)


    ## info table (list to send to template)
    info_for_projects = [{'name': 'Current System', 'info':current},
                            {'name':'Modeled Efficiency Project','info':info}]


    ## create list of charts
    charts = [
        {'name':'costs', 'data': str(table1).replace('nan','null'),
         'title': 'Estimated Heating Fuel + Electricity Costs for residential sector',
         'type': "'$'", 'plot': True,},
        #~ {'name':'E_consumption', 'data': str(table2).replace('nan','null'),
         #~ 'title':'Electricity Consumed',
         #~ 'type': "'other'",'plot': True,},
        {'name':'H_consumption', 'data': str(table3).replace('nan','null'),
         'title':'Heating Oil Consumed by residential sector',
         'type': "'other'", 'plot': True,}
            ]

    ## generate html
    ## generate html
    msg = None
    if community in web_object.bad_data_coms:
        msg = web_object.bad_data_msg

    pth = os.path.join(web_object.directory, community.replace("'",''),
                    COMPONENT_NAME.replace(' ','_').lower() + '.html')
    with open(pth, 'w') as html:
        html.write(template.render( info = info_for_projects,
                                    type = COMPONENT_NAME,
                                    com = community.replace("'",'') ,
                                    charts = charts,
                                    summary_pages = ['Summary'] + comp_order ,
                                    sections = web_object.get_summary_pages(),

                                    description =  DESCRIPTION,
                                    metadata = web_object.metadata,
                                    message = msg
                                    ))

def create_project_details_list (project):
    """makes a projects details section for the html

    Parameters
    ----------
    project: ResidentialBuildings
        A ResidentialBuildings object thats run function has been called

    Returns
    -------
        A dictionary with values used by summary
    """


    ex_h_savings = (1 - \
        (
        project.proposed_HF_consumption / project.baseline_HF_consumption
        )[0])*100
    #~ print ex_h_savings
    return [
        {'words':'Capital cost',
            'value': '${:,.0f}'.format(project.get_NPV_costs())},
        {'words':'Lifetime energy cost savings',
            'value': '${:,.0f}'.format(project.get_NPV_benefits())},
        {'words':'Net lifetime savings',
            'value': '${:,.0f}'.format(project.get_NPV_net_benefit())},
        {'words':'Benefit-cost ratio',
            'value': '{:,.1f}'.format(project.get_BC_ratio())},
        {'words':'Expected space heating savings ',
            'value': '{:,.2f}%'.format(ex_h_savings)},
        {'words':
            'Estimated households to be retrofit ('\
                + str(int(project.start_year)) +')' ,
            'value': int(project.opportunity_HH)},
        {'words':'Estimated cost to refit household',
            'value': '${:,.2f}/home'.format(project.refit_cost_rate)},
            ]
