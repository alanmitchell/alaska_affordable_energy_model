"""
Transmission Outputs
--------------------

output functions for Transmission component

"""
import os.path
import numpy as np
from pandas import DataFrame
from config import COMPONENT_NAME, DESCRIPTION
import aaem.constants as constants
from aaem.components import comp_order
import aaem.web_lib as wl

## component summary
def component_summary (results, res_dir):
    """Creates the regional and communites summary for the component in provided 
    directory
    
    Parameters
    ----------
    results : dictionay
        results from the model, dictionay with each community or project 
        as key
    res_dir :  path
        location to save file
    
    """
    communities_summary (results, res_dir)
    save_regional_summary(create_regional_summary (results), res_dir)

def communities_summary (coms, res_dir):
    """Saves the component summary by community
    
    Parameters
    ----------
    coms : dictionay
        results from the model, dictionay with each community or project 
        as key
    res_dir :  path
        location to save file
    """
    out = []
    for c in sorted(coms.keys()):
        it = coms[c]['community data'].intertie
        if it is None:
            it = 'parent'
        if it == 'child':
            continue
        try:
            # ??? NPV or year one
            it = coms[c][COMPONENT_NAME]
            connect_to = it.comp_specs['nearest community']\
                        ['Nearest Community with Lower Price Power']
                
            if it.reason == 'Not a transmission project.':
                continue
            try:
                if it.connect_to_intertie:
                    connect_to += 'intertie'
            except AttributeError:
                pass
                
            start_yr = it.comp_specs['start year']
            
            dist = it.comp_specs['nearest community']['Distance to Community']
            
            it.get_diesel_prices()
            diesel_price = float(it.diesel_prices[0].round(2))
            
            try:
                diesel_price_it = float(it.intertie_diesel_prices[0].round(2))
            except AttributeError:
                diesel_price_it = np.nan
            
            
            if not it.comp_specs["project details"] is None:
                phase = it.comp_specs["project details"]['phase']
            else:
                phase = "Reconnaissance"
                
                
                
            heat_rec_opp = it.cd['heat recovery operational']
            
            try:
                generation_displaced = it.pre_intertie_generation[0]
            except AttributeError:
                generation_displaced = np.nan
            
            try:
                generation_conserved = it.intertie_offset_generation[0]
            except AttributeError:
                generation_conserved = np.nan
                    
            try:
                lost_heat = it.lost_heat_recovery[0]
            except AttributeError:
                lost_heat = np.nan
                
            try:
                levelized_cost = it.levelized_cost_of_energy
            except AttributeError:
                levelized_cost = 0

            try:
                break_even = it.break_even_cost
            except AttributeError:
                break_even = 0
            
            eff = it.cd["diesel generation efficiency"]
            try:
                pre_price = it.pre_intertie_generation_fuel_used[0] * \
                            diesel_price
            except AttributeError:
                pre_price = np.nan
                
            try:
                post_price = it.intertie_offset_generation_fuel_used[0] * \
                            diesel_price_it
            except AttributeError:
                post_price = np.nan
                
            try:
                eff_it = it.intertie_generation_efficiency
            except AttributeError:
                eff_it = np.nan
                
            
                
            
            try:
                losses = it.annual_tranmission_loss
            except AttributeError:
                losses = np.nan
                
            
                
            name = c
            if name == 'Barrow':
                name = 'Utqiagvik'
            l = [name,  
                connect_to,
                start_yr,
                phase,
                dist,

                generation_displaced,
                generation_conserved,
                
                lost_heat,
                heat_rec_opp,
                
                eff,
                eff_it,
                diesel_price,
                diesel_price_it,
                break_even,
                losses,
                
                levelized_cost,

                pre_price,
                post_price,
                pre_price - post_price,
                

                it.get_NPV_benefits(),
                it.get_NPV_costs(),
                it.get_NPV_net_benefit(),
                it.irr,
                it.get_BC_ratio(),
                it.reason
            ]
            out.append(l)
        except (KeyError,AttributeError) as e:
            print e
            pass
        
    
    cols = ['Community to connect',
            'Community/Intertie to connect to',
            'Start Year',
            'Project Phase',
            'Miles of Transmission Line',
            
            'Generation Displaced in community to connect [kWh]',
            'Electricity Generated, Conserved, or transmitted [kWh]',
            
            'Loss of Recovered Heat from Genset in community to connect  [gal]',
            'Heat Recovery Operational in community to connect',
           
           
            'Diesel Generator Efficiency in community to connect',
            'Diesel Generator Efficiency in community to connect to',
            'Diesel Price - year 1 [$/gal] in community to connect',
            'Diesel Price - year 1 [$/gal] in community to connect to',
            'Break Even Diesel Price [$/gal]',
            'Annual Transmission loss percentage',
            

            'Levelized Cost Of Energy [$/kWh]',

            'Status Quo generation Cost (Year 1)',
            'Proposed generation cost (Year 1)',
            'Benefit from reduced generation cost (year 1)',
            
            'Transmission NPV benefits [$]',
            'Transmission NPV Costs [$]',
            'Transmission NPV Net benefit [$]',
            'Transmission Internal Rate of Return',
            'Transmission Benefit-cost ratio',
            'notes'
            ]
        
    
    data = DataFrame(out,columns = cols).set_index('Community to connect')
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.replace(" ","_").lower() + '_summary.csv')

    data.to_csv(f_name, mode='w')
    
def create_regional_summary (results):
    """Creates the regional summary
    
    Parameters
    ----------
    results : dictionay
        results from the model, dictionay with each community or project 
        as key
            
    Returns
    -------
    DataFrame 
        containg regional results
    
    """
    #~ print "start"
    regions = {}
    for c in results:
        c_region = results[c]['community data'].get_item('community','region')
        comp = results[c][COMPONENT_NAME]
        #~ print comp
        bc_ratio = comp.get_BC_ratio()
        bc_ratio = (not type(bc_ratio) is str) and (not np.isinf(bc_ratio))\
                                              and (bc_ratio > 1)
        #~ print bc_ratio ,comp.get_BC_ratio()
        #~ return
        capex = round(comp.get_NPV_costs(),0)  if bc_ratio else 0
        net_benefit = round(comp.get_NPV_net_benefit(),0)  if bc_ratio else 0
       
        displaced_fuel = \
            round(comp.pre_intertie_generation_fuel_used[0] - comp.intertie_offset_generation_fuel_used[0] ,0) if bc_ratio else 0

        if (results[c]['community data'].intertie == 'child' or c.find('+') != -1):
            #~ print c
            continue
        if c_region in regions.keys():
            ## append entry
            regions[c_region]['Number of communities/interties in region'] +=1
            k = 'Number of communities with cost effective projects'
            regions[c_region][k] += 1 if bc_ratio else 0
            k = 'Investment needed for cost-effective projects ($)'
            regions[c_region][k] += capex 
            k = 'Net benefit of cost-effective projects ($)'
            regions[c_region][k] += net_benefit
            k = 'Generation diesel displaced by cost-effective projects (gallons)'
            regions[c_region][k] += displaced_fuel
            
        else:
            ## set up "first" entry
            regions[c_region] = {'Number of communities/interties in region':1}
            k = 'Number of communities with cost effective projects'
            regions[c_region][k] = 1 if bc_ratio else 0
            k = 'Investment needed for cost-effective projects ($)'
            regions[c_region][k] = capex 
            k = 'Net benefit of cost-effective projects ($)'
            regions[c_region][k] = net_benefit
            k = 'Generation diesel displaced by cost-effective projects (gallons)'
            regions[c_region][k] = displaced_fuel
            
    cols = ['Number of communities/interties in region',
            'Number of communities with cost effective projects',
            'Investment needed for cost-effective projects ($)',
            'Net benefit of cost-effective projects ($)',
            'Generation diesel displaced by cost-effective projects (gallons)']

    try:        
        summary = DataFrame(regions).T[cols]
    except KeyError:
        summary = DataFrame(columns = cols)
        
    summary.ix['All Regions'] = summary.sum()                 
    #~ print summary
    return summary
    
def save_regional_summary (summary, res_dir):
    """Saves the summary by region
    
    Parameters
    ----------
    summary : Dataframe
        compiled regional results
    res_dir :  path
        location to save file

    """
    f_name = os.path.join(res_dir, '__regional_' +
                COMPONENT_NAME.lower().replace(' ','_').\
                    replace('(','').replace(')','') + '_summary.csv')
    summary.to_csv(f_name, mode='w', index_label='region')
    
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
    
    ## get the component (the modelded one)
  
    modeled = web_object.results[community][COMPONENT_NAME]
    start_year = modeled.start_year
    end_year = modeled.actual_end_year
    
    ## for make table functions
    projects = {'Modeled ' + COMPONENT_NAME:  modeled}
    
    ## get forecast stuff (consumption, generation, etc)
    fc = modeled.forecast

    generation = fc.generation_by_type.\
                                        ix[start_year:end_year].sum(1)
    
    ## get the diesel prices
    diesel_price = web_object.results[community]['community data'].\
                            get_item('community','diesel prices').\
                            get_projected_prices(start_year, end_year+1)
           
    ## get diesel generator efficiency
    eff = modeled.cd['diesel generation efficiency']
    
    
    
    ## get generation fuel costs per year (modeled)
    base_cost = generation/eff * diesel_price
    base_cost.name = 'Base Cost'
    
    
    table1 = wl.make_costs_table(community, COMPONENT_NAME, projects, base_cost,
                              web_object.directory)
    
    
    ## get generation fule used (modeled)
    base_con = generation/eff 
    base_con.name = 'Base Consumption'
    table2 = wl.make_consumption_table(community, COMPONENT_NAME, 
                                    projects, base_con,
                                    web_object.directory,
                                    'pre_intertie_generation_fuel_used')
    
    
    
    current = wl.create_electric_system_summary (web_object.results[community])
    
    ## info for modeled
    info = create_project_details_list (modeled)
        
         
    ## info table (list to send to template)
    info_for_projects = [{'name': 'Current System', 'info':current},
                            {'name':'Modeled Transmission Project','info':info}]
            
    
    ## create list of charts
    charts = [
        {'name':'costs', 'data': str(table1).replace('nan','null'), 
         'title': 'Estimated Electricity Generation Costs per Year',
         'type': "'$'",'plot': True,},
        {'name':'consumption', 'data': str(table2).replace('nan','null'), 
         'title':'Diesel Consumed for Electricity Generation ',
         'type': "'other'",'plot': True,}
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
                                    
                                    message = msg,
                                    description =  DESCRIPTION,
                                    metadata = web_object.metadata, 
                                    ))
    
def create_project_details_list (project):
    """makes a projects details section for the html
    
    Parameters
    ----------
    projcet: Transmission
        A Transmission object thats run function has been called
            
    Returns
    -------
        A dictionary with values used by summary
    """
   
    return [
        {'words':'Capital cost', 
            'value': '${:,.0f}'.format(project.get_NPV_costs())},
        {'words':'Lifetime savings', 
            'value': '${:,.0f}'.format(project.get_NPV_benefits())},
        {'words':'Net lifetime savings', 
            'value': '${:,.0f}'.format(project.get_NPV_net_benefit())},
        {'words':'Benefit-cost ratio', 
            'value': '{:,.1f}'.format(project.get_BC_ratio())},
        {'words':'Nearest community', 
            'value': project.comp_specs['nearest community']\
            ['Nearest Community with Lower Price Power'] },
        {'words':'Distance', 
            'value': '{:,.0f} miles'.format(project.comp_specs\
            ['nearest community']['Distance to Community'] )},
        {'words':'Maximum savings', 
            'value': '${:,.2f}/kWh'.format(
                project.comp_specs['nearest community']\
                ['Maximum savings ($/kWh)']) },
        #~ {'words':'Expected Yearly Generation (kWh/year)', 
         #~ 'value': 
                #~ '{:,.0f}'.format(project.proposed_load *\
                                 #~ constants.hours_per_year)},

        #~ {'words':'Output per 10kW Solar PV', 
            #~ 'value': project.comp_specs['data']\
                                         #~ ['Output per 10kW Solar PV']},
            ]

