"""
outputs.py

    ouputs functions for Solar Power component
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
    """ 
    creats the regional and communites summary for the component 
    
    inputs:
        results: results from the model
        res_dir: location to save file
    
    outputs:
        saves a summaries in res-dir
    """
    communities_summary (results, res_dir)
    save_regional_summary(create_regional_summary (results), res_dir)

def communities_summary (coms, res_dir):
    """
    """
    out = []
    for c in sorted(coms.keys()):
        it = coms[c]['community data'].intertie
        if it is None:
            it = 'parent'
        if it == 'child':
            continue
        try:
            solar = coms[c][COMPONENT_NAME]

            start_yr = solar.comp_specs['start year']
            solar.get_diesel_prices()
            diesel_price = float(solar.diesel_prices[0].round(2))
            assumed_out = solar.comp_specs['data']['Output per 10kW Solar PV']
            average_load = solar.average_load
            proposed_capacity = solar.proposed_load + 0
            existing_capacity = solar.comp_specs['data']['Installed Capacity']
            wind_capacity = solar.comp_specs['data']['Wind Capacity']
           
            try:
                net_gen = solar.generation_proposed [0]
                loss_heat = solar.fuel_displaced[0]
                hr_op = solar.cd['heat recovery operational']
                net_heating =   -1* loss_heat
                eff = solar.cd["diesel generation efficiency"]
                red_per_year = solar.generation_fuel_used[0]
            except AttributeError:
                net_gen = 0
                loss_heat = 0
                hr_op = solar.cd['heat recovery operational']
                net_heating = 0
                eff = solar.cd["diesel generation efficiency"]
                red_per_year = 0
                
            try:
                levelized_cost = solar.levelized_cost_of_energy
            except AttributeError:
                levelized_cost = 0

            try:
                break_even = solar.break_even_cost
            except AttributeError:
                break_even = 0
            
            l = [c, assumed_out, average_load, proposed_capacity, 
                 existing_capacity, wind_capacity, net_gen, loss_heat, hr_op,
                 net_heating, red_per_year, eff, diesel_price,
                 break_even,
                 levelized_cost,
                 solar.get_NPV_benefits(),
                 solar.get_NPV_costs(),
                 solar.get_NPV_net_benefit(),
                 solar.irr,
                 solar.get_BC_ratio(),
                 solar.reason
                ]
            out.append(l)
            
        except (KeyError,AttributeError) as e:
            #~ print e
            pass
    
    
    
    cols = ['Community',
            'Assumed  Output per 10kW Solar PV Array',
            'Average Diesel Load [kw]',
            'Solar Capacity Proposed [kW]',
            'Existing Solar Capacity [kW]',
            'Existing Wind Capacity [kW]',
            'Net Proposed Solar Generation [kWh]',
            'Loss of Recovered Heat from Proposed Solar [gal]',
            'Heat Recovery Operational',
            'Net in Heating Oil Consumption from Proposed Solar [gal]',
            'Proposed Solar Reduction in Utility Diesel Consumed per year',
            'Diesel Generator Efficiency',
            'Diesel Price - year 1 [$/gal]',
            'Break Even Diesel Price [$/gal]',
            
            'Levelized Cost Of Energy [$/kWh]',
            'Solar NPV benefits [$]',
            'Solar NPV Costs [$]',
            'Solar NPV Net benefit [$]',
            
            'Solar Internal Rate of Return',
            'Solar Benefit Cost Ratio',
            'notes']
    
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.lower().replace(' ','_').\
                    replace('&','and') + '_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write(("# solar summary\n"))
    #~ fd.close()
    data.to_csv(f_name, mode='w')
    
def create_regional_summary (results):
    """
    create the regional summary for this component
    
    inputs:
        results: results from the model
       
    outputs:
        returns summary as a data frame
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
       
        #~ try:
        displaced_fuel = \
                round(comp.generation_fuel_used[0],0) if bc_ratio else 0
        #~ except StandardError as e:
            #~ print e

        if (results[c]['community data'].intertie == 'child' or c.find('+') != -1):
            #~ print c
            continue
        if c_region in regions.keys():
            ## append entry
            regions[c_region]['Number of communities/interties in region'] +=1
            k = 'Number of communities with cost effective projects'
            regions[c_region][k] += 1 if bc_ratio else 0
            k = 'Investment needed for cost-effective projects'
            regions[c_region][k] += capex 
            k = 'Net benefit of cost-effective projects'
            regions[c_region][k] += net_benefit
            k = 'Generation diesel displaced by cost-effective projects'
            regions[c_region][k] += displaced_fuel
            
        else:
            ## set up "first" entry
            regions[c_region] = {'Number of communities/interties in region':1}
            k = 'Number of communities with cost effective projects'
            regions[c_region][k] = 1 if bc_ratio else 0
            k = 'Investment needed for cost-effective projects'
            regions[c_region][k] = capex 
            k = 'Net benefit of cost-effective projects'
            regions[c_region][k] = net_benefit
            k = 'Generation diesel displaced by cost-effective projects'
            regions[c_region][k] = displaced_fuel
            
    summary = DataFrame(regions).T[['Number of communities/interties in region',
                        'Number of communities with cost effective projects',
                        'Investment needed for cost-effective projects',
                        'Net benefit of cost-effective projects',
                    'Generation diesel displaced by cost-effective projects']]
    summary.ix['All Regions'] = summary.sum()                 
    #~ print summary
    return summary
    
def save_regional_summary (summary, res_dir):
    """ 
    inputs:
        summary: summary dataframe
        res_dir: location to save file
    
    outputs:
        save a regional summary in res-dir
    """
    f_name = os.path.join(res_dir, '__regional_' +
                COMPONENT_NAME.lower().replace(' ','_').\
                    replace('(','').replace(')','') + '_summary.csv')
    summary.to_csv(f_name, mode='w', index_label='region')
    
def generate_web_summary (web_object, community):
    """
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

    generation = fc.generation_by_type['generation diesel'].\
                                        ix[start_year:end_year]
    
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
                                    'get_fuel_total_saved()')
    
    
    
    current = wl.create_electric_system_summary (web_object.results[community])
    
    ## info for modeled
    info = create_project_details_list (modeled)
        
         
    ## info table (list to send to template)
    info_for_projects = [{'name': 'Current System', 'info':current},
                            {'name':'Modeled Solar Project','info':info}]
            
    
    ## create list of charts
    charts = [
        {'name':'costs', 'data': str(table1).replace('nan','null'), 
         'title': 'Estimated Electricity Generation Fuel Costs per Year',
         'type': "'$'",'plot': True,},
        {'name':'consumption', 'data': str(table2).replace('nan','null'), 
         'title':'Diesel Consumed for Electricity Generation ',
         'type': "'other'",'plot': True,}
            ]
        
    ## generate html
    ## generate html
    pth = os.path.join(web_object.directory, community,
                    COMPONENT_NAME.replace(' ','_').lower() + '.html')
    with open(pth, 'w') as html:
        html.write(template.render( info = info_for_projects,
                                    type = COMPONENT_NAME, 
                                    com = community ,
                                    charts = charts,
                                    summary_pages = ['Summary'] + comp_order ,
                                    sections = web_object.get_summary_pages(),
                                    communities = web_object.get_all_coms(),
                                    description =  DESCRIPTION,
                                    metadata = web_object.metadata,
                                    ))
    





def create_project_details_list (project):
    """
    makes a projects details section for the html
    """
    pen = project.generation_proposed/\
          float(project.forecast.cd.get_item('community',
                                                'generation').iloc[-1:])
    pen *= 100
    pen = pen[0]
   
    return [
        {'words':'Capital Cost ($)', 
            'value': '${:,.0f}'.format(project.get_NPV_costs())},
        {'words':'Lifetime Savings ($)', 
            'value': '${:,.0f}'.format(project.get_NPV_benefits())},
        {'words':'Net Lifetime Savings ($)', 
            'value': '${:,.0f}'.format(project.get_NPV_net_benefit())},
        {'words':'Benefit Cost Ratio', 
            'value': '{:,.3f}'.format(project.get_BC_ratio())},
        {'words':'Proposed Nameplate Capacity(kW)', 
            'value': '{:,.0f}'.format(project.proposed_load)},
        {'words':'Expected Yearly Generation (kWh/year)', 
         'value': 
                '{:,.0f}'.format(project.proposed_load *\
                                 constants.hours_per_year)},

        {'words':'Output per 10kW Solar PV', 
            'value': project.comp_specs['data']\
                                         ['Output per 10kW Solar PV']},
        {'words':'Estimated Solar Penetration Level (%)', 
            'value': '{:,.2f}%'.format(pen)},
            ]
