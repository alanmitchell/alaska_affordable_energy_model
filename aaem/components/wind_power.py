"""
wind_power.py

wind power component
"""
import numpy as np
from math import isnan
from pandas import DataFrame,concat,read_csv
import os
import shutil

from annual_savings import AnnualSavings
from aaem.community_data import CommunityData
from aaem.forecast import Forecast
from aaem.diagnostics import diagnostics
import aaem.constants as constants

#TODO 2016/06/01
# ambler



## List of yaml key/value pairs
yaml = {'enabled': False,
        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',
        'average load limit': 100.0,
        'percent generation to offset': 1.00,
        'data':'IMPORT',
         #'minimum wind class': 3,
        'wind cost': 'UNKNOWN',
        'secondary load': True,
        'secondary load cost': 200000,
        'road needed for transmission line' : True,
        'transmission line distance': 1,
        'transmission line cost': { True:500000, False:250000},
        'costs': 'IMPORT',
        'percent excess energy': .15,
        'percent excess energy capturable': .7,
        'efficiency electric boiler': .99,
        'efficiency heating oil boiler': .8,
        'percent heat recovered': .15,
        'percent o&m': .01
        }
      
## default values for yaml key/Value pairs
yaml_defaults = {'enabled': True,
        'lifetime': 20,
        'start year': 2020,
        }

## order to save yaml
yaml_order = ['enabled', 'lifetime', 'start year']

## comments for the yaml key/value pairs
yaml_comments = {'enabled': '',
        'lifetime': 'number years <int>',
        'start year': 'start year <int>',
        'average load limit': 
                'lower limint in kW on averge load reqired to do project',
        'percent generation to offset': '',
        'minimum wind class': 'minimum wind class for feasability',
        'secondary load': '',
        'secondary load cost': '',
        'road needed for transmission line':'',
        'transmission line distance': 'miles defaults to 1 mile',
        'transmission line cost': 'cost/mile',
        'assumed capacity factor': "TODO read in preprocessor",
        }
       
## Functions for CommunityData IMPORT keys
def process_data_import(data_dir):
    """
    Loads wind_power_data.csv
    
    pre:
        wind_power_data.csv exists at data_dir
    post:
        the values in wind_power_data.csv are returned as a dictionary 
    """
    data_file = os.path.join(data_dir, "wind_power_data.csv")
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    return data['value'].to_dict()
    
def load_wind_costs_table (data_dir):
    """
    loads the wind cost table
    
    pre:
        wind_costs.csv exists at data_dir
    post:
        the wind cost values are returned as a pandas DataFrame
    """
    data_file = os.path.join(data_dir, "wind_costs.csv")
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    data.index =data.index.astype(str)
    return data
    
## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = {'data':process_data_import,
                   'costs':load_wind_costs_table}

## wind preprocessing functons 
def wind_preprocess_header (ppo):
    """
    wind preporcess header
    
    pre:
        ppo: a Preprocessor object
    post:
        returns the header for the wind data preprocessed csv file
    """
    ## TODO Expand
    return  "# " + ppo.com_id + " wind data\n"+ \
            ppo.comments_dataframe_divide
    
def wind_preprocess (ppo):
    """
    Reprocesses the wind data
    
    pre:
        ppo is a Preprocessor object. wind_class_assumptions, 
    wind_data_existing.csv and wind_data_potential.csv file exist at 
    ppo.data_dir's location 
    
    post:
        preprocessed wind data is saved at ppo.out_dir as wind_power_data.csv
    """
    try:
        existing = read_csv(os.path.join(ppo.data_dir,"wind_data_existing.csv"),
                        comment = '#',index_col = 0).ix[ppo.com_id]
        existing = existing['Rated Power (kW)']
    except KeyError:
        existing = 0
    #~ #~ print existing
    try:
        potential = read_csv(os.path.join(ppo.data_dir,
                                "wind_data_potential.csv"),
                            comment = '#',index_col = 0).ix[ppo.com_id]
    except KeyError:
        potential = DataFrame(index = ['Wind Potential','Wind-Resource',
                                       'Assumed Wind Class',
                                       'Wind Developability','Site Accessible ',
                                       'Permittability','Site Availability',
                                       'Load','Certainty',
                                       'Estimated Generation','Estimated Cost',
                                       'Note','Resource Note'])
                                       
    try:
        intertie = read_csv(os.path.join(ppo.data_dir,
                            "wind_data_interties.csv"),
                            comment = '#',
                            index_col = 0).ix[ppo.com_id+"_intertie"]
        intertie = int(intertie['Highest Wind Class on Intertie'])
    except KeyError:
        intertie = 0
    
    try:
        if intertie > int(potential['Assumed Wind Class']):
            potential.ix['Assumed Wind Class'] = intertie
            ppo.diagnostics.add_note("wind", 
                    "Wind class updated to max on intertie")
        
    except KeyError:
        pass
    
    assumptions = read_csv(os.path.join(ppo.data_dir,
                                "wind_class_assumptions.csv"),
                           comment = '#',index_col = 0)
    
    try:
        capa = assumptions.ix[int(float(potential.ix['Assumed Wind Class']))]
        capa = capa.ix['REF V-VI Net CF']
    except (TypeError,KeyError):
        capa = 0
    #~ print capa
    
    #~ #~ print potential
    out_file = os.path.join(ppo.out_dir,"wind_power_data.csv")
    #~ #~ print ppo.out_dir,"wind_power_data.csv"
    fd = open(out_file,'w')
    fd.write(wind_preprocess_header(ppo))
    fd.write("key,value\n")
    fd.write("existing wind," + str(existing) +'\n')
    fd.write('assumed capacity factor,' +str(capa) +'\n')
    fd.close()

    #~ df = concat([ww_d,ww_a])
    potential.to_csv(out_file, mode = 'a',header=False)
    #~ self.wastewater_data = df
    ppo.MODEL_FILES['WIND_DATA'] = "wind_power_data.csv"
    
def copy_wind_cost_table(ppo):
    """
    copies wind cost table file to each community
    
    pre:
        ppo is a Preprocessor object. wind_costs.csv exists at ppo.data_dir
    post:
        wind_costs.csv is copied from ppo.data_dir to ppo.out_dir 
    """
    data_dir = ppo.data_dir
    out_dir = ppo.out_dir
    shutil.copy(os.path.join(data_dir,"wind_costs.csv"), out_dir)
    ppo.MODEL_FILES['WIND_COSTS'] = "wind_costs.csv"
## end wind preprocessing functions

## List of raw data files required for wind power preproecssing 
raw_data_files = ['wind_class_assumptions.csv',
                  'wind_costs.csv',
                  "wind_data_existing.csv",
                  "wind_data_potential.csv",
                  "diesel_data.csv",
                  'wind_data_interties.csv']

## list of wind preprocessing functions
preprocess_funcs = [wind_preprocess, copy_wind_cost_table]

## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = ['costs']

## component summary
def component_summary (coms, res_dir):
    """ """
    out = []
    for c in sorted(coms.keys()):
        it = coms[c]['model'].cd.intertie
        if it is None:
            it = 'parent'
        if it == 'child':
            continue
        try:
            # ??? NPV or year one
            wind = coms[c]['model'].comps_used['wind power']
            
            average_load = wind.average_load
            existing_load = wind.comp_specs['data']['existing wind']
            wind_class = float(wind.comp_specs['data']['Assumed Wind Class']) 
            proposed_load =  wind.load_offset_proposed
            cap_fac = float(wind.comp_specs['data']['assumed capacity factor'])
            heat_rec_opp = wind.cd['heat recovery operational']
            try:
                #~ offset = wind.load_offset_proposed
                net_gen_wind = wind.net_generation_wind
                decbb = wind.diesel_equiv_captured
                
                
                loss_heat = wind.loss_heat_recovery
                electric_diesel_reduction=wind.electric_diesel_reduction
                
                diesel_red = wind.reduction_diesel_used
                
                eff = wind.cd["diesel generation efficiency"]
                
            except AttributeError:
                offset = 0
                net_gen_wind = 0
                decbb = 0
                electric_diesel_reduction=0
                loss_heat = 0
                
                diesel_red = 0
                eff = wind.cd["diesel generation efficiency"]    
                
            #~ try:
                #~ red_per_year = net_gen_wind / eff
            #~ except ZeroDivisionError:
                #~ red_per_year = 0
            
            l = [c, 
                wind_class, 
                average_load, 
                proposed_load,
                existing_load,
                cap_fac,
                net_gen_wind,
                decbb, 
                loss_heat, 
                heat_rec_opp,
                diesel_red, 
                electric_diesel_reduction,
                eff,
                wind.get_NPV_benefits(),
                wind.get_NPV_costs(),
                wind.get_NPV_net_benefit(),
                wind.get_BC_ratio(),
                wind.reason
            ]
            out.append(l)
        except (KeyError,AttributeError) as e:
            #~ print e
            pass
        
    data = DataFrame(out,columns = \
       ['Community',
        'Assumed Wind Class',
        'Average Diesel Load [kw]',
        'Wind Capacity Proposed [kW]',
        'Existing Wind Capacity [kW]',
        'Assumed Capacity Factor [%]',
        'Net Generation [kWh]',
        'Heating Oil Equivalent Captured by Secondary Load [gal]',
        'Loss of Recovered Heat[gal]',
        'Heat Recovery Opperational',
        'Net in Heating Oil Consumption [gal]',
        'Reduction in Utility Diesel Consumed per year',
        'Diesel Denerator Efficiency',
        'NPV benefits [$]',
        'NPV Costs [$]',
        'NPV Net benefit [$]',
        'Benefit Cost Ratio',
        'notes']
                    ).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                'wind_power_summary.csv')
    fd = open(f_name,'w')
    fd.write(("# wind summary\n"))
    fd.close()
    data.to_csv(f_name, mode='a')

## component name
COMPONENT_NAME = "wind power"

## component
class WindPower(AnnualSavings):
    """
    """
    def __init__ (self, community_data, forecast, diag = None):
        """
        Class initialiser

        pre:
            community_data is a CommunityData object. diag (if provided) should 
        be a Diagnostics object
        post:
            the model can be run
        """
        
        self.diagnostics = diag
        if self.diagnostics == None:
            self.diagnostics = diagnostics()
        self.forecast = forecast
        self.cd = community_data.get_section('community')
       
        self.comp_specs = community_data.get_section(COMPONENT_NAME)
        self.component_name = COMPONENT_NAME

        self.set_project_life_details(self.comp_specs["start year"],
                                      self.comp_specs["lifetime"],
                        self.forecast.end_year - self.comp_specs["start year"])
                        
        ### ADD other intiatzation stuff
        
        
    
    def run (self):
        """
        run the forecast model
        
        pre:
            self.cd should be the community library from a community data object
        post:
            TODO: define output values. 
            the model is run and the output values are available
        """
        #~ #~ print self.comp_specs['data']
        self.run = True
        self.reason = "OK"
        try:
            self.generation = self.forecast.get_generation(self.start_year)
            self.calc_average_load()
            self.calc_generation_wind_proposed()
        except:
            self.diagnostics.add_warning(self.component_name, 
            "could not be run")
            self.run = False
            self.reason = "could not find average load or proposed generation"
            return
            
 
        
        #~ #~ print self.comp_specs['data']['Assumed Wind Class'] 
        # ??? some kind of failure message
        if self.average_load > self.comp_specs['average load limit']: #and\
            #~ float(self.comp_specs['data']['Assumed Wind Class']) > \
                #~ self.comp_specs['minimum wind class'] and \
                #~ self.load_offset_proposed > 0:
        # if the average load is greater that the lower limit run this component
        # else skip    
            
            self.calc_transmission_losses()
            self.calc_exess_energy()
            self.calc_net_generation_wind()
            self.calc_electric_diesel_reduction()
            self.calc_diesel_equiv_captured()
            self.calc_loss_heat_recovery()
            self.calc_reduction_diesel_used()
            
            
           
            if self.cd["model electricity"]:
                # change these below
                #~ self.calc_baseline_kWh_consumption()
                #~ self.calc_retrofit_kWh_consumption()
                #~ self.calc_savings_kWh_consumption()
                # NOTE*:
                #   some times is it easier to find the savings and use that to
                # calculate the retro fit values. If so, flip the function calls 
                # around, and change the functionality of
                # self.calc_savings_kWh_consumption() below
                pass
            
            if self.cd["model heating fuel"]:
                pass
                # see NOTE*
        
            if self.cd["model financial"]:
                # AnnualSavings functions (don't need to write)
                self.get_diesel_prices()
                
                # change these below
                self.calc_capital_costs()
                self.calc_maintainance_cost()
                self.calc_annual_electric_savings()
                self.calc_annual_heating_savings()
                
                # AnnualSavings functions (don't need to write)
                self.calc_annual_total_savings()
                self.calc_annual_costs(self.cd['interest rate'])
                self.calc_annual_net_benefit()
                self.calc_npv(self.cd['discount rate'], self.cd["current year"])
                #~ print self.benefit_cost_ratio
        else:
            #~ print "wind project not feasiable"
            self.run = False
            self.reason = "average load too small"
            self.diagnostics.add_note(self.component_name, 
            "communites average load is not large enough to consider project")
        #~ print self.benefit_cost_ratio
        
    def calc_average_load (self):
        """
            calculate the average load of the system
            
        pre: 
            self.generation should be a number (kWh/yr)
            
        post:
            self.average_load is a number (kW/yr)
        """
        self.generation = self.forecast.generation_by_type['generation diesel']\
                                                            [self.start_year]
        self.average_load = self.generation / constants.hours_per_year
        #~ print 'self.average_load',self.average_load
        
    def calc_generation_wind_proposed (self):
        """
            calulate the proposed generation for wind
        pre:
            self.generation should be a number (kWh/yr), 
            'percent generation to offset' is a decimal %
            'data' is a wind data object
            'assumed capacity factor' is a decimal %
        
        post:
            self.load_offest_proposed is a number (kW)
            self.generation_wind_proposed is a number (kWh/yr)
        """
        self.load_offset_proposed = 0
        
        offset = self.average_load*\
                self.comp_specs['percent generation to offset']
        #~ print self.forecast.generation_by_type['generation hydro'].sum()
        if self.forecast.generation_by_type['generation hydro'].fillna(0).sum() > 0:
            offset *= 2
        #~ self.comp_specs['data']['existing wind'] = 0
        if int(float(self.comp_specs['data']['existing wind'])) < \
                (round(offset/25) * 25): # ???
            #~ print "True"
            self.load_offset_proposed = round(offset/25) * 25 - \
                    float(self.comp_specs['data']['existing wind'])
        
        # not needed for now
        #~ self.total_wind_generation = self.generation_load_proposed + \
                            #~ int(self.comp_specs['data']['existing wind'])
        
        self.generation_wind_proposed =  self.load_offset_proposed * \
                    float(self.comp_specs['data']['assumed capacity factor'])*\
                                    constants.hours_per_year
        #~ print 'self.load_offset_proposed',self.load_offset_proposed
        #~ print 'self.generation_wind_proposed',self.generation_wind_proposed 
        
    def calc_transmission_losses (self):
        """
            calculate the line losses on proposed system
            
        pre:
            self.generation_wind_proposed is a number (kWh/yr). 
            self.cd is a CommunityData object
        """
        self.transmission_losses = self.generation_wind_proposed * \
                                                        self.cd['line losses']
        #~ print 'self.transmission_losses',self.transmission_losses
        
    def calc_exess_energy (self):
        """
            calculate the excess energy
            TODO add more:
        """
        #~ print sorted(self.cd.keys())
        self.exess_energy = \
            (self.generation_wind_proposed - self.transmission_losses) * \
            self.comp_specs['percent excess energy']
        #~ print 'self.exess_energy',self.exess_energy
            
    def calc_net_generation_wind (self):
        """
            calculate the proposed net generation
        """
        self.net_generation_wind = self.generation_wind_proposed  - \
                                    self.transmission_losses  -\
                                    self.exess_energy
        #~ print 'self.net_generation_wind',self.net_generation_wind 
            
    def calc_electric_diesel_reduction (self):
        """ 
            calculate the reduction in diesel due to the proposed wind
        """
        gen_eff = self.cd["diesel generation efficiency"]
            
        self.electric_diesel_reduction = self.net_generation_wind / gen_eff
        
        electric_diesel = self.generation/gen_eff
        if self.electric_diesel_reduction > electric_diesel:
            self.electric_diesel_reduction = electric_diesel
            
        
        
        #~ print 'self.electric_diesel_reduction',self.electric_diesel_reduction
        
    def calc_diesel_equiv_captured (self):
        """
            calulate the somthing ???
        """
        if self.generation_wind_proposed == 0:
            exess_percent = 0
        else:
            exess_percent = self.exess_energy / self.generation_wind_proposed
        exess_captured_percent = exess_percent * \
                    self.comp_specs['percent excess energy capturable']
        if self.comp_specs['secondary load']:
            net_exess_energy = exess_captured_percent * \
                                self.generation_wind_proposed 
        else:
            net_exess_energy = 0
       
        #~ conversion = 0.99/0.138/0.8/293 
        conversion = self.comp_specs['efficiency electric boiler']/ \
                     (1/constants.mmbtu_to_gal_HF)/ \
                     self.comp_specs['efficiency heating oil boiler']/\
                     (constants.mmbtu_to_kWh)
        self.diesel_equiv_captured = net_exess_energy * conversion
             
        #~ print 'self.diesel_equiv_captured ',self.diesel_equiv_captured 
        
    def calc_loss_heat_recovery (self):
        """ 
             calulate the somthing ???
        """
        hr_used = self.cd['heat recovery operational']
        self.loss_heat_recovery = 0
        if hr_used:# == 'Yes': 
            self.loss_heat_recovery = self.electric_diesel_reduction * \
            self.comp_specs['percent heat recovered']
        #~ print 'self.loss_heat_recovery',self.loss_heat_recovery
        
    def calc_reduction_diesel_used (self):
        """ 
             calulate the somthing ???
        """
        self.reduction_diesel_used = self.diesel_equiv_captured - \
                                     self.loss_heat_recovery
        #~ print 'self.reduction_diesel_used',self.reduction_diesel_used
                                     
    def calc_maintainance_cost (self):
        """ 
            calculate the maintainance cost
        """
        self.maintainance_cost = self.comp_specs['percent o&m'] * self.capital_costs
        #~ print 'self.maintainance_cost',self.maintainance_cost
        

    
    
    # Make this do stuff
    def calc_capital_costs (self):
        """
        caclulate the progect captial costs
        """
        powerhouse_control_cost = 0
        if not self.cd['switchgear suatable for RE']:
            powerhouse_control_cost = self.cd['switchgear cost']
        
        road_needed = self.comp_specs['road needed for transmission line']
        transmission_line_cost = self.comp_specs['transmission line distance']*\
            self.comp_specs['transmission line cost'][road_needed]
        
        secondary_load_cost = 0
        if self.comp_specs['secondary load']:
            secondary_load_cost = self.comp_specs['secondary load cost']
            
        if str(self.comp_specs['wind cost']) != 'UNKNOWN':
            wind_cost = str(self.comp_specs['wind cost'])
        else:
            for i in range(len(self.comp_specs['costs'])):
                if int(self.comp_specs['costs'].iloc[i].name) < \
                                            self.load_offset_proposed:
                    if i == len(self.comp_specs['costs']) - 1:
                        cost = float(self.comp_specs['costs'].iloc[i])
                        break
                    continue
               
                cost = float(self.comp_specs['costs'].iloc[i])
                break
        
            wind_cost = self.load_offset_proposed * cost
        
        self.capital_costs = powerhouse_control_cost + transmission_line_cost +\
                             secondary_load_cost + wind_cost
                             
        #~ print 'self.capital_costs',self.capital_costs
        
    
    # Make this do stuff
    def calc_annual_electric_savings (self):
        """
        """
        price = self.diesel_prices
        #TODO add rural v non rural
        self.base_generation_cost = self.electric_diesel_reduction * price
                        
        
        self.proposed_generation_cost = self.maintainance_cost
        
        self.annual_electric_savings = self.base_generation_cost - \
                            self.proposed_generation_cost
        #~ print 'self.annual_electric_savings',self.annual_electric_savings
        
        
        
    # Make this do sruff. Remember the different fuel type prices if using
    def calc_annual_heating_savings (self):
        """
        """
        price = (self.diesel_prices + self.cd['heating fuel premium'])
        
        #~ self.base_heating_cost =
        
        #~ self.proposed_heating_cost =
        
        
        
        
        self.annual_heating_savings = self.reduction_diesel_used * price
        #~ print 'self.annual_heating_savings',self.annual_heating_savings


    def save_component_csv (self, directory):
        """
        save the output from the component.
        """
        if not self.run:
            fname = os.path.join(directory,
                                   self.component_name + "_output.csv")
            fname = fname.replace(" ","_")
        
            fd = open(fname, 'w')
            fd.write("Wind Power minimum requirments not met\n")
            fd.close()
            return
        
        
        years = np.array(range(self.project_life)) + self.start_year
    
        # ??? +/- 
        # ???
        df = DataFrame({
                'Capacity [kW]':self.load_offset_proposed,
                "Generation [kWh/yr]": self.net_generation_wind,
                'Energy Captured by Secondary Load (gallons of heating oil equivalent)':
                                                    self.diesel_equiv_captured,
                'assumed capacity factor':
                    float(self.comp_specs['data']['assumed capacity factor']),
                'Utility Diesel Displaced [gal]' :self.electric_diesel_reduction,
                'Heat Recovery Lost [Gal/yr]':self.loss_heat_recovery, 
                "Heat Recovery Cost Savings": 
                                        self.get_heating_savings_costs(),
                "Electricity Cost Savings": 
                                    self.get_electric_savings_costs(),
                "Project Capital Cost": self.get_capital_costs(),
                "Total Cost Savings": self.get_total_savings_costs(),
                "Net Benefit": self.get_net_beneft(),
                       }, years)

        df["community"] = self.cd['name']
        
        ol = ["community",'Capacity [kW]',
        'Energy Captured by Secondary Load (gallons of heating oil equivalent)',
              'assumed capacity factor','Utility Diesel Displaced [gal]',
              'Heat Recovery Lost [Gal/yr]',
              "Generation [kWh/yr]",
                "Heat Recovery Cost Savings",
                "Electricity Cost Savings",
                "Project Capital Cost",
                "Total Cost Savings",
                "Net Benefit"]
        fname = os.path.join(directory,
                                   self.component_name + "_output.csv")
        fname = fname.replace(" ","_")
        
        
        fin_str = "Enabled" if self.cd["model financial"] else "Disabled"
        fd = open(fname, 'w')
        fd.write(("# " + self.component_name + " model outputs\n")) 
        fd.close()
        
        # save npv stuff
        df2 = DataFrame([self.get_NPV_benefits(),self.get_NPV_costs(),
                            self.get_NPV_net_benefit(),self.get_BC_ratio()],
                       ['NPV Benefits','NPV Cost',
                            'NPV Net Benefit','Benefit Cost Ratio'])
        df2.to_csv(fname, header = False, mode = 'a')
        
        # save to end of project(actual lifetime)
        df[ol].ix[:self.actual_end_year].to_csv(fname, index_label="year", 
                                                                    mode = 'a')
        
    
component = WindPower

def test ():
    """
    tests the class using the manley data.
    """
    pass
