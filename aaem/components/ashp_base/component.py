"""
component.py

    Air Source Heat Pumps Base component body
"""
import numpy as np
from pandas import DataFrame, concat
import os


from aaem.components.annual_savings import AnnualSavings
from aaem.community_data import CommunityData
from aaem.forecast import Forecast
from aaem.diagnostics import diagnostics
import aaem.constants as constants
from config import COMPONENT_NAME, UNKNOWN

class ASHPBase (AnnualSavings):
    """
    """
    def __init__ (self, community_data, forecast, 
                        diag = None, prerequisites = {}):
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
       
        try:
            self.comp_specs = community_data.get_section(self.component_name)
        except AttributeError:
            self.comp_specs = community_data.get_section(COMPONENT_NAME)

        self.set_project_life_details(self.comp_specs["start year"],
                                      self.comp_specs["lifetime"],
                        self.forecast.end_year - self.comp_specs["start year"])
                        
        self.ashp_sector_system = "N/a"
                        
        ### ADD other intiatzation stuff
        self.load_prerequisite_variables(prerequisites)
        self.regional_multiplier = \
                community_data.get_item('community','construction multiplier')
        
    def load_prerequisite_variables (self, comps):
        """
        load variables from prerequisites
        
        pre:
             prerequisites: dictonary of componentes
        """
        # written in child classes
        pass
        
    def calc_cop_per_month (self):
        """
        calculate the coefficient of performance (COP) per month
        COP = output/input
        """
        #find m & b from performance data
        temp = self.comp_specs['perfromance data']['Temperature']
        cop = self.comp_specs['perfromance data']['COP']
        m, b = np.polyfit(temp,cop,1) 
        #~ print m, b
        # apply to months 
        mtk = ['Avg. Temp (F) JUL','Avg. Temp (F) AUG','Avg. Temp (F) SEP',
               'Avg. Temp (F) OCT','Avg. Temp (F) NOV','Avg. Temp (F) DEC',
               'Avg. Temp (F) JAN','Avg. Temp (F) FEB','Avg. Temp (F) MAR',
               'Avg. Temp (F) APR','Avg. Temp (F) MAY','Avg. Temp (F) JUN']
        monthly_temps = self.comp_specs['data'].ix[mtk].astype(float)
        
        monthly_temps = monthly_temps.T
        
        for c in monthly_temps.columns:
            mon = c[-3:]
            monthly_temps[mon] = monthly_temps[c]
            del monthly_temps[c]
        
        monthly_temps = monthly_temps.T
        monthly_temps['Temperature'] =  monthly_temps["value"]
        del monthly_temps['value']
        
        monthly_cop =  m * monthly_temps + b
        
        maxes = monthly_temps >= max(temp)
        monthly_cop[maxes] = max(cop)
        zeros =  monthly_temps < min(temp)
        monthly_cop[zeros] = 0
        monthly_cop['COP'] = monthly_cop['Temperature']
        del monthly_cop['Temperature']
        
        self.monthly_value_table = concat([monthly_temps,monthly_cop],axis = 1)
        del monthly_temps
        del monthly_cop
        #~ print self.monthly_value_table
        
        
    def calc_heat_energy_produced_per_year (self):
        """
        """
        #~ self.heat_energy_produced_per_year = None
        pass # depends on child to implement
        
    def calc_heat_energy_produced_per_month (self):
        """
        calc the mmbtu consumbed per month
        
        pre: mmbtu per year
        """
        # mmbty/mon = mmbtu/year * montly%s 
        mtk = ['% Heating Load JUL','% Heating Load AUG','% Heating Load SEP',
               '% Heating Load OCT','% Heating Load NOV','% Heating Load DEC',
               '% Heating Load JAN','% Heating Load FEB','% Heating Load MAR',
               '% Heating Load APR','% Heating Load MAY','% Heating Load JUN']
        monthly_percents = self.comp_specs['data'].ix[mtk].astype(float).T
        for c in monthly_percents.columns:
            mon = c[-3:]
            monthly_percents[mon] = monthly_percents[c]
            del monthly_percents[c]
        monthly_percents = monthly_percents.T
        self.monthly_value_table['% of total heating'] = monthly_percents
        del monthly_percents
        
        self.monthly_value_table['mmbtu/mon'] = \
                self.heat_energy_produced_per_year *\
                self.monthly_value_table['% of total heating']
        
        #~ print self.monthly_value_table
        
        
    
    def calc_electric_energy_input_per_month (self):
        """
        """
        # mmbtu/mon -> kwh/mon / COP
        #~ idx = self.monthly_value_table['COP'] > 0
        
        self.monthly_value_table['kWh consumed'] = \
                (self.monthly_value_table['mmbtu/mon']*\
                constants.mmbtu_to_kWh / \
                self.monthly_value_table['COP'] ).replace([np.inf,-np.inf],0)
        pass
        
    def calc_heating_oil_consumed_per_month (self):
        """"""
        # per month if cop = 0 : consumprion mmbtu -> gal / eff
        idx = self.monthly_value_table['COP'] == 0
        
        self.monthly_value_table["Heating Oil Consumed (gal)"] = 0
        self.monthly_value_table["Heating Oil Consumed (gal)"][idx] = \
                self.monthly_value_table['mmbtu/mon']*\
                constants.mmbtu_to_gal_HF /\
                self.comp_specs['heating oil efficiency']
        
        pass
        
    def calc_heating_oil_saved_per_month (self):
        """"""
        # for each month mmbtu -> gal /eff - heating_oil_consumed
        #~ idx = self.monthly_value_table['COP'] == 0
        
        self.monthly_value_table["Heating Oil Saved (gal)"] = \
                self.monthly_value_table['mmbtu/mon']*\
                constants.mmbtu_to_gal_HF /\
                self.comp_specs['heating oil efficiency'] - \
                self.monthly_value_table["Heating Oil Consumed (gal)"]
    
    def calc_electric_consumption (self):
        """
        """
        self.electric_consumption = \
            self.monthly_value_table['kWh consumed'].sum()
        
    def calc_heating_oil_saved (self):
        self.heating_oil_saved = \
            self.monthly_value_table['Heating Oil Saved (gal)'].sum()
        
    def calc_average_cop (self):
        self.monthly_value_table['mmbtu/mon'].sum()
        consumed_Hoil =\
            self.monthly_value_table['Heating Oil Consumed (gal)'].sum()
        
        factor_1 = (self.monthly_value_table['COP'] *\
                   self.monthly_value_table['% of total heating']).sum()
        factor_2 = self.monthly_value_table['% of total heating']\
                                    [self.monthly_value_table['COP'] > 0].sum()
            
        self.average_cop = factor_1 / factor_2
      
    def calc_baseline_heating_oil_cost (self):
        
        self.get_diesel_prices()
        price = self.diesel_prices + self.cd['heating fuel premium']
        self.baseline_heating_oil_cost = self.heating_oil_saved * price
    
    def calc_proposed_ashp_operation_cost (self):
        self.get_electricity_prices()
        cost = self.electricity_prices * self.electric_consumption +\
                                       self.comp_specs["o&m per year"]
        self.proposed_ashp_operation_cost = cost.values.T[0].tolist()
        
    def calc_ashp_system_pramaters (self):
        """
        """
        self.calc_cop_per_month()
        #~ self.calc_heat_energy_produced_per_year()
        self.calc_heat_energy_produced_per_month()
        self.calc_electric_energy_input_per_month()
        self.calc_heating_oil_consumed_per_month()
        self.calc_heating_oil_saved_per_month()
        self.calc_electric_consumption()
        self.calc_heating_oil_saved()
        self.calc_average_cop()

    def run (self, scalers = {'captial costs':1.0}):
        """
        run the forecast model
        
        pre:
            self.cd should be the community library from a community data object
        post:
            TODO: define output values. 
            the model is run and the output values are available
        """
        #~ self.calc_heat_energy_produced_per_year()
        #~ self.calc_ashp_system_pramaters()
        #~ self.calc_baseline_heating_oil_cost()
        #~ self.calc_proposed_ashp_operation_cost()
        #~ print self.monthly_value_table
        #~ print self.electric_consumption
        #~ print self.heating_oil_saved
        #~ print self.average_cop
        #~ print self.baseline_heating_oil_cost
        #~ print self.proposed_ashp_operation_cost
        pass # depends on child to implement
 
 
    # Make this do stuff
    def calc_capital_costs (self):
        """ Function Doc"""
        self.capital_costs = np.nan
        
    
    # Make this do stuff
    def calc_annual_electric_savings (self):
        """
        """
        self.annual_electric_savings = 0
        
        
    # Make this do sruff. Remember the different fuel type prices if using
    def calc_annual_heating_savings (self):
        """
        """
        self.annual_heating_savings = self.baseline_heating_oil_cost - \
                                      self.proposed_ashp_operation_cost
                            
    def get_fuel_total_saved (self):
        """
        returns the total fuel saved in gallons
        """
        #~ eff = self.cd["diesel generation efficiency"]
        #~ proposed = self.electric_consumption/eff
        return self.heating_oil_saved #- proposed 
                                
    def get_total_enery_produced (self):
        """
        returns the total energy produced
        """
        return self.heat_energy_produced_per_year #+ \
                #~ self.electric_consumption * (1/constants.mmbtu_to_kWh) 
                                     
    
    def save_component_csv (self, directory):
        """
        save the component output csv in directory
        """
        pass