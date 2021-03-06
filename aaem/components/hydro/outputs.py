"""
Hydropower outputs
------------------

output functions for Hydropower component

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
        results from the model, dictionary with each community or project 
        as key
    res_dir :  path
        location to save file
    
    """
    communities_summary (results, res_dir)
    save_regional_summary(create_regional_summary (results), res_dir)

def communities_summary (coms, res_dir):
    """Saves the summary by: community hydropower_summary.csv
    
    Parameters
    ----------
    coms : dictionary
        results from the model, dictionary with each community or project 
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
            hydro = coms[c]['Hydropower']
            
            start_yr = hydro.comp_specs['start year']
            hydro.get_diesel_prices()
            diesel_price = float(hydro.diesel_prices[0].round(2))
            #~ print hydro.diesel_prices[0]
            if hydro.comp_specs["name"] == 'none':
                phase = hydro.comp_specs['phase']
            else:
                phase = "Reconnaissance"

            name = hydro.comp_specs['name']
            
            average_load = hydro.average_load
            proposed_load =  hydro.load_offset_proposed
            
            
            heat_rec_opp = hydro.cd['heat recovery operational']
            
           
            net_gen_hydro = hydro.net_generation_proposed
            
            captured_energy = hydro.captured_energy
            
            
            lost_heat = hydro.lost_heat_recovery
            electric_diesel_reduction= hydro.generation_diesel_reduction
            
            diesel_red = hydro.captured_energy - hydro.lost_heat_recovery
            
            eff = hydro.cd["diesel generation efficiency"]
            
            levelized_cost = hydro.levelized_cost_of_energy
            break_even = hydro.break_even_cost
            #~ except AttributeError:
                #~ offset = 0
                #~ net_gen_hydro = 0
                #~ decbb = 0
                #~ electric_diesel_reduction=0
                #~ loss_heat = 0
                
                #~ diesel_red = 0
                #~ eff = hydro.cd["diesel generation efficiency"]    
                
            #~ try:
                #~ red_per_year = net_gen_hydro / eff
            #~ except ZeroDivisionError:
                #~ red_per_year = 0
            
            community = c
            if community == 'Barrow':
                community = 'Utqiagvik (Barrow)'
            l = [name,  
                name,
                start_yr,
                phase,

                average_load, 
                proposed_load,
                net_gen_hydro,
                
                captured_energy, 
                lost_heat, 
                heat_rec_opp,
                diesel_red, 
                electric_diesel_reduction,
                
                eff,
                diesel_price,
                break_even,
                levelized_cost,
                hydro.get_NPV_benefits(),
                hydro.get_NPV_costs(),
                hydro.get_NPV_net_benefit(),
                hydro.irr,
                hydro.get_BC_ratio(),
                hydro.reason
            ]
            out.append(l)
        except (KeyError,AttributeError,TypeError) as e:
            #~ print e
            pass
        
    
    cols = ['Community',
            'Project Name',
            'Start Year',
            'project phase',
            
            'Average Diesel Load [kw]',
            'Hydro Capacity Proposed [kW]:',
            'Net Proposed Hydro Generation [kWh]',
            
            'Heating Oil Equivalent Captured by Secondary Load [gal]',
            'Loss of Recovered Heat from Genset [gal]',
            'Heat Recovery Operational',
            'Net Reduction in Heating Oil Consumption [gal]',
            'Hydropower Reduction in Utility Diesel Consumed per year',
            'Diesel Generator Efficiency',
            'Diesel Price - year 1 [$/gal]',
            'Break Even Diesel Price [$/gal]',
            
            'Levelized Cost Of Energy [$/kWh]',
            'Hydro NPV benefits [$]',
            'Hydro NPV Costs [$]',
            'Hydro NPV Net benefit [$]',
            'Hydro Internal Rate of Return',
            'Hydro Benefit-cost ratio',
            'notes'
            ]
        
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.replace(" ","_").lower() + '_summary.csv')
    with open(f_name,'w') as summary:
        summary.write(('# Hydropower summary by community.\n'
            '# Community: ' + definitions.COMMUNITY + '\n'
            '# Project Name: Name of proposed hydropower project \n'
            '# Start Year: ' + definitions.START_YEAR + '\n'
            '# project phase: '+ definitions.PHASE + '\n'
            '# Average Diesel Load [kw]: ' + definitions.DIESEL_LOAD +'\n'
            '# Hydro Capacity Proposed [kW]: Proposed generation capacity from Hydropower.\n'
            '# Net Proposed Hydro Generation [kWh]: Net generation from proposed hydropower system.\n'
            '# Heating Oil Equivalent Captured by Secondary Load [gal]: \n'
            '# Loss of Recovered Heat from Genset [gal]: \n'
            '# Heat Recovery Operational' + definitions.HR_OP + '\n'
            '# Net Reduction in Heating Oil Consumption [gal]: Change in '
                'heating oil consumed between base and proposed systems\n'
            '# Hydropower Reduction in Utility Diesel Consumed per year: '
                'Reduction in diesel used from generation from hydropower project\n'
            '# Diesel Generator Efficiency: '+ definitions.GEN_EFF + ' \n'
            '# Diesel Price - year 1 [$\gal]: ' + definitions.PRICE_DIESEL + '\n'
            '# Break Even Diesel Price [$/gal]: ' + definitions.BREAK_EVEN_COST_DIESEL + '\n'
            '# Levelized Cost Of Energy [$/kWh]:' + definitions.LCOE + '\n'
            '# Hydropower NPV benefits [$]: '+ definitions.NPV_BENEFITS + '\n'
            '# Hydropower NPV Costs [$]: ' + definitions.NPV_COSTS + '\n'
            '# Hydropower NPV Net benefit [$]: ' + definitions.NPV_NET_BENEFITS + '\n'
            '# Hydropower Internal Rate of Return: ' + definitions.IRR +'\n'
            '# Hydropower Benefit-cost ratio: ' + definitions.NPV_BC_RATIO +'\n'
            '# notes: '+ definitions.NOTES +'\n'))
            

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
    DataFrame 
        containing regional results
    
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
            round(comp.generation_diesel_reduction,0) if bc_ratio else 0

        if not c.find('hydro') != -1:
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
            
    try:
        summary = DataFrame(regions).T[['Number of communities/interties in region',
                        'Number of communities with cost effective projects',
                        'Investment needed for cost-effective projects ($)',
                        'Net benefit of cost-effective projects ($)',
                    'Generation diesel displaced by cost-effective projects (gallons)']]
    except KeyError:
        summary = DataFrame(columns = ['Number of communities/interties in region',
                        'Number of communities with cost effective projects',
                        'Investment needed for cost-effective projects ($)',
                        'Net benefit of cost-effective projects ($)',
                    'Generation diesel displaced by cost-effective projects (gallons)'])
    summary.ix['All Regions'] = summary.sum()                 
    #~ print summary
    return summary
    
def save_regional_summary (summary, res_dir):
    """Saves the summary by region:  __regional_hydropower_summary.csv
    
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
    
