"""
summaries.py
ross spicer

functions for the creation of log and summary files form model results 
"""
from pandas import DataFrame, read_csv, concat
import os
import numpy as np

from constants import mmbtu_to_kWh, mmbtu_to_gal_HF


def res_log (coms, res_dir):
    """
    create a 
    
    """
    out = []
    for c in sorted(coms.keys()):
        if c.find("_intertie") != -1:
            continue
        try:
            res = coms[c]['model'].comps_used['residential buildings']
            out.append([c,
                res.get_NPV_benefits(),res.get_NPV_costs(),
                res.get_NPV_net_benefit(),res.get_BC_ratio(),
                res.hoil_price[0], res.init_HH, res.opportunity_HH,
                res.baseline_fuel_Hoil_consumption[0]/mmbtu_to_gal_HF,
                res.baseline_fuel_Hoil_consumption[0]/mmbtu_to_gal_HF - \
                        res.refit_fuel_Hoil_consumption[0]/mmbtu_to_gal_HF,
                round(float(res.fuel_oil_percent)*100,2),
                res.baseline_HF_consumption[0],
                res.baseline_HF_consumption[0] - \
                        res.refit_HF_consumption[0],
                ])
        except (KeyError,AttributeError) :
            pass
    data = DataFrame(out,columns = ['community','NPV Benefit','NPV Cost', 
                           'NPV Net Benefit', 'B/C Ratio',
                           'Heating Oil Price - year 1',
                           'Occupied Houses', 'Houses to Retrofit', 
                           'Heating Oil Consumed(mmbtu) - year 1',
                           'Heating Oil Saved(mmbtu/year)',
                           'Heating Oil as percent of Total Heating Fuels',
                           'Total Heating Fuels (mmbtu) - year 1',
                           'Total Heating Fuels Saved (mmbtu/year)',]
                    ).set_index('community').round(2)
    f_name = os.path.join(res_dir,'residential_summary.csv')
    fd = open(f_name,'w')
    fd.write("# residental building component summary by community\n")
    fd.close()
    data.to_csv(f_name, mode='a')
    
def com_log (coms, res_dir): 
    """
    """
    out = []
    for c in sorted(coms.keys()):
        if c.find("_intertie") != -1:
            continue
        try:
            com = coms[c]['model'].comps_used['non-residential buildings']
            savings = com.baseline_fuel_Hoil_consumption -\
                      com.refit_fuel_Hoil_consumption
            out.append([c,
                com.get_NPV_benefits(),com.get_NPV_costs(),
                com.get_NPV_net_benefit(),com.get_BC_ratio(),
                com.hoil_price[0], com.elec_price[0], 
                com.num_buildings , com.refit_sqft_total,
                com.baseline_fuel_Hoil_consumption,
                com.baseline_kWh_consumption,
                savings,
                com.baseline_kWh_consumption - com.refit_kWh_consumption])
        except (KeyError,AttributeError) as e:
            #~ print c +":"+ str(e)
            pass
    data = DataFrame(out,columns = ['community','NPV Benefit','NPV Cost', 
                           'NPV Net Benefit', 'B/C Ratio',
                           'Heating Oil Price - year 1','$ per kWh - year 1',
                           'Number Buildings', 'Total Square Footage', 
                           'Heating Oil Consumed(gal) - year 1',
                           'Electricity Consumed(kWh) - year 1',
                           'Heating Oil Saved(gal/year)',
                           'Electricity Saved(kWh/year)'
                           ]
                    ).set_index('community').round(2)
    f_name = os.path.join(res_dir,'non-residential_summary.csv')
    fd = open(f_name,'w')
    fd.write("# non residental building component summary by community\n")
    fd.close()
    data.to_csv(f_name, mode='a')
    
def building_log(coms, res_dir):
    """
    """
    out = []
    for c in sorted(coms.keys()):
        if c.find("_intertie") != -1:
            continue
        try:
            com = coms[c]['model'].comps_used['non-residential buildings']
            
            
            types = coms[c]['model'].cd.get_item('non-residential buildings',
                                                "com building estimates").index
            estimates =coms[c]['model'].cd.get_item('non-residential buildings',
                                                    "com building data")
            
            num  = 0
            try:
                num = len(estimates.ix['Average'])
            except KeyError:
                pass
            estimates = estimates.groupby(estimates.index).sum()
            try:
                estimates.ix["Unknown"] =  estimates.ix["Average"] 
                estimates = estimates[estimates.index != "Average"]
            except KeyError:
                pass
            count = []
            act = []
            est = []
            #~ print types
            for t in types:
                if t in ['Water & Sewer',]:
                    continue
                try:
                    n = 0
                    sf_m = np.nan
                    sf_e = np.nan
                    if t == 'Average':
                        
                        n = num
                        sf_e = estimates['Square Feet']['Unknown']
                    else:
                        n = com.buildings_df['count'][t]
                        sf_e = estimates['Square Feet'][t]
                    
                    
                    sf_m = com.buildings_df['Square Feet'][t]
                    
                except KeyError:
                    pass
                count.append(n)
                act.append(sf_m)
                est.append(sf_e)
            percent = com.buildings_df['Square Feet'].sum() / estimates['Square Feet'].sum()
            percent2 = float(com.buildings_df['count'].sum())/(com.buildings_df['count'].sum()+num)
            
            if np.isnan(percent):
                percent = 0.0
                
            if np.isnan(percent2):
                percent2 = 0.0
            
            
            out.append([c,percent*100,percent2*100]+ count+act+est)
            
        except (KeyError,AttributeError)as e :
            #~ print c +":"+ str(e)
            pass
    #~ print out
    l = [n for n in types if n not in  ['Water & Sewer',]]
    c = []
    e = []
    m = []
    for i in range(len(l)):
        if l[i] == 'Average':
            l[i] = 'Unknown'
        c.append('number buildings')
        m.append('square feet(measured)')
        e.append('square feet(including estimates)')

    
    data = DataFrame(out,columns = ['community','% sqft measured','% buildings from inventory'] + l + l + l
                    ).set_index('community').round(2)
    f_name = os.path.join(res_dir,'non-residential_building_summary.csv')
    fd = open(f_name,'w')
    fd.write(("# non residental building component building "
             "summary by community\n"))
    fd.write(",%,%," + str(c)[1:-1].replace(" '",'').replace("'",'') + "," + \
             str(m)[1:-1].replace("' ",'').replace("'",'') + "," + \
             str(e)[1:-1].replace("' ",'').replace("'",'') +'\n')
    fd.close()
    data.to_csv(f_name, mode='a')
    
    
def village_log (coms, res_dir): 
    """
    """
    out = []
    for c in sorted(coms.keys()):
        if c.find("_intertie") != -1:
            continue
        try:
            try:
                res = coms[c]['model'].comps_used['residential buildings']
                res_con = [res.baseline_HF_consumption[0], 
                                res.baseline_kWh_consumption[0] / mmbtu_to_kWh]
                res_cost = [res.baseline_HF_cost[0], res.baseline_kWh_cost[0]]
            except KeyError:
                res_con = [np.nan, np.nan]
                res_cost = [np.nan, np.nan]
            try:
                com = coms[c]['model'].comps_used['non-residential buildings']
                com_con = [com.baseline_HF_consumption,
                            com.baseline_kWh_consumption / mmbtu_to_kWh]
                com_cost = [com.baseline_HF_cost[0],com.baseline_kWh_cost[0]]
            except KeyError:
                com_con = [np.nan, np.nan]
                com_cost = [np.nan, np.nan]
            try:
                ww = coms[c]['model'].comps_used['water wastewater']
                ww_con = [ww.baseline_HF_consumption[0],
                          ww.baseline_kWh_consumption[0] / mmbtu_to_kWh ]
                ww_cost = [ww.baseline_HF_cost[0],ww.baseline_kWh_cost[0]]
            except KeyError:
                ww_con = [np.nan, np.nan]
                ww_cost = [np.nan, np.nan]
            t = [c, coms[c]['model'].cd.get_item('community','region')] +\
                res_con + com_con + ww_con + res_cost + com_cost + ww_cost 
            out.append(t)
        except AttributeError:
            pass
    start_year = 2017
    data = DataFrame(out,columns = ['community','Region',
                    'Residential Heat (MMBTU)', 
                    'Residential Electricity (MMBTU)',
                    'Non-Residential Heat (MMBTU)', 
                    'Non-Residential Electricity (MMBTU)',
                    'Water/Wastewater Heat (MMBTU)', 
                    'Water/Wastewater Electricity (MMBTU)',
                    'Residential Heat (cost ' + str(start_year)+')', 
                    'Residential Electricity (cost ' + str(start_year)+')',
                    'Non-Residential Heat (cost ' + str(start_year)+')',
                    'Non-Residential Electricity (cost ' + str(start_year)+')',
                    'Water/Wastewater Heat (cost ' + str(start_year)+')', 
                    'Water/Wastewater Electricity (cost ' + str(start_year)+')',
                    ]
                    ).set_index('community')
    f_name = os.path.join(res_dir,'village_sector_consumption_summary.csv')
    fd = open(f_name,'w')
    fd.write("# summary of consumption and cost\n")
    fd.close()
    data.to_csv(f_name, mode='a')