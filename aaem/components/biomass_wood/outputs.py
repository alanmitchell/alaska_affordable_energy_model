"""
Biomass cordwood outputs
------------------------

output functions for Biomass Cordwood component

"""
import os.path
import numpy as np
from pandas import DataFrame
from config import COMPONENT_NAME
import aaem.constants as constants
from aaem.components import comp_order, definitions


## component summary
def component_summary (results, res_dir):
    """Creates the regional and communities summary for the component in provided 
    directory
    
    Parameters
    ----------
    results : dictionary
        results from the model, dictionary with each community or project as key
        
    res_dir : path
        location to save file
    
    """
    communities_summary (results, res_dir)
    save_regional_summary(create_regional_summary (results), res_dir)

def communities_summary (coms, res_dir):
    """Saves the summary by: community biomass_cordwood_summary.csv
    
    Parameters
    ----------
    coms : dictionary
        results from the model, dictionary with each community or project as key
            
    res_dir : path
        location to save file
    
    """
    out = []
    for c in sorted(coms.keys()):
        #~ it = coms[c]['community data'].intertie
        #~ if it is None:
            #~ it = 'parent'
        #~ if it == 'child':
            #~ continue
        if c.find("_intertie") != -1:
            continue
        try:
            
           
            biomass = coms[c][COMPONENT_NAME]
            
            
            
            biomass.get_diesel_prices()
            diesel_price = float(biomass.diesel_prices[0].round(2))
            hf_price = diesel_price + biomass.cd['heating fuel premium']   
            
            try:
                break_even = biomass.break_even_cost
            except AttributeError:
                break_even = 0
               
            
            try:
                levelized_cost = biomass.levelized_cost_of_energy
            except AttributeError:
                levelized_cost = 0
            
            name = c
            if name == 'Barrow':
                name = 'Utqiagvik (Barrow)'
            l = [name,  
                 biomass.max_boiler_output,
                 biomass.heat_displaced_sqft,
                 biomass.biomass_fuel_consumed,
                 biomass.fuel_price_per_unit,
                 biomass.comp_specs['energy density'],
                 biomass.heat_diesel_displaced,
                 hf_price,
                 break_even,
                 levelized_cost,
                 biomass.get_NPV_benefits(),
                 biomass.get_NPV_costs(),
                 biomass.get_NPV_net_benefit(),
                 biomass.irr,
                 biomass.get_BC_ratio(),
                 biomass.reason
                ]
            out.append(l)
            
        except (KeyError,AttributeError) as e:
            #~ print e
            pass
    try:
        cols = ['Community',
            'Maximum Biomass Boiler Output [Btu/hr]',
            'Biomass Heat Displacement square footage [Sqft]',
            'Proposed ' + biomass.biomass_type + \
                            " Consumed [" + biomass.units +"]",
            'Price [$/' + biomass.units + ']',
            "Energy Density [Btu/" + biomass.units + "]",
            'Displaced Heating Oil by Biomass [Gal]',
            "Heating Fuel Price - year 1 [$/gal]",
            'Break Even Heating Fuel Price [$/gal]',
            'Levelized Cost Of Energy [$/MMBtu]',
            'Biomass Cordwood NPV benefits [$]',
            'Biomass Cordwood NPV Costs [$]',
            'Biomass Cordwood NPV Net benefit [$]',
            'Biomass Cordwood Internal Rate of Return',
            'Biomass Cordwood Benefit-cost ratio',
            'notes'
                ]
    except UnboundLocalError:
        return
    
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.lower().replace(' ','_').\
                    replace('(','').replace(')','') + '_summary.csv')
    fd = open(f_name,'w')
    fd.write(("# " + COMPONENT_NAME + " summary by community\n"
            '# Maximum Biomass Boiler Output [Btu/hr]:\n'
            '# Biomass Heat Displacement square footage [Sqft]: Non-residential area to heat with biomass\n'
            '# Proposed ' + biomass.biomass_type + ""
                " consumed [" + biomass.units +"]: Proposed biomass fuel consumed\n"
            '# Price [$/' + biomass.units + ']: Price of biomass fuel\n'
            "# Energy Density [Btu/" + biomass.units + "]: Energy Density of fuel\n"
            '# Displaced Heating Oil by Biomass [Gal]: Estimated heating fuel displace by biomass heating\n'
            '# Heating Fuel Price - year 1 [$/gal]: ' + definitions.PRICE_HF + '\n'
            '# Break Even Heating Fuel Price [$/gal]: ' + definitions.BREAK_EVEN_COST_HF + '\n'
            '# Levelized Cost Of Energy [$/kWh]:' + definitions.LCOE + '\n'
            '# '+ COMPONENT_NAME +' NPV benefits [$]: '+ definitions.NPV_BENEFITS + '\n'
            '# '+ COMPONENT_NAME +' NPV Costs [$]: ' + definitions.NPV_COSTS + '\n'
            '# '+ COMPONENT_NAME +' NPV Net benefit [$]: ' + definitions.NPV_NET_BENEFITS + '\n'
            '# '+ COMPONENT_NAME +' Internal Rate of Return: ' + definitions.IRR +'\n'
            '# '+ COMPONENT_NAME +' Benefit-cost ratio: ' + definitions.NPV_BC_RATIO +'\n'
            '# notes: '+ definitions.NOTES +'\n'))
    fd.close()
    data.to_csv(f_name, mode='a')
    
def create_regional_summary (results):
    """Creates the regional summary
    
    Parameters
    ----------
    results : dictionary
        results from the model, dictionary with each community or project 
        as key
            
    Returns
    -------
        pandas DataFrame containing regional results
    
    """
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
        displaced_hoil = round(comp.heat_diesel_displaced,0)  if bc_ratio else 0
        
        
        
        if results[c]['community data'].intertie == 'parent' or \
                                                            c.find('+') != -1:
            continue
        if c_region in regions.keys():
            ## append entry
            regions[c_region]['Number of communities in region'] +=1
            k = 'Number of communities with cost effective projects'
            regions[c_region][k] += 1 if bc_ratio else 0
            k = 'Investment needed for cost-effective projects ($)'
            regions[c_region][k] += capex 
            k = 'Net benefit of cost-effective projects ($)'
            regions[c_region][k] += net_benefit
            k = 'Heating oil displaced by cost-effective projects (gallons)'
            regions[c_region][k] += displaced_hoil
            
        else:
            ## set up "first" entry
            regions[c_region] = {'Number of communities in region':1}
            k = 'Number of communities with cost effective projects'
            regions[c_region][k] = 1 if bc_ratio else 0
            k = 'Investment needed for cost-effective projects ($)'
            regions[c_region][k] = capex 
            k = 'Net benefit of cost-effective projects ($)'
            regions[c_region][k] = net_benefit
            k = 'Heating oil displaced by cost-effective projects (gallons)'
            regions[c_region][k] = displaced_hoil
            
    cols = ['Number of communities in region',
            'Number of communities with cost effective projects',
            'Investment needed for cost-effective projects ($)',
            'Net benefit of cost-effective projects ($)',
            'Heating oil displaced by cost-effective projects (gallons)']
   
    try:        
        summary = DataFrame(regions).T[cols]
    except KeyError:
        summary = DataFrame(columns = cols)
   
   
    summary.ix['All Regions'] = summary.sum()                 
    
    return summary
    
def save_regional_summary (summary, res_dir):
    """Saves the summary by region:  __regional_residential_ashp_summary.csv
    
    Parameters
    ----------
    summary : DataFrame
        compiled regional results
    res_dir :  path
        location to save file

    """
    f_name = os.path.join(res_dir, '__regional_' +
                COMPONENT_NAME.lower().replace(' ','_').\
                    replace('(','').replace(')','') + '_summary.csv')
    summary.to_csv(f_name, mode='w', index_label='region')
    
