"""
driver.py

    will run the model
"""
from community_data import CommunityData
from forecast import Forecast

from components.residential_buildings import ResidentialBuildings
from components.community_buildings import CommunityBuildings
from components.wastewater import WaterWastewaterSystems

from pandas import DataFrame, read_pickle
import numpy as np



def test (com_data_file = "test_case/manley_data.yaml"):
    """
    """
    cd = CommunityData(com_data_file, "test_case/data_defaults.yaml")
    
    fc = Forecast(cd)
    
    rb = ResidentialBuildings(cd, fc)
    rb.run()
    cb = CommunityBuildings(cd, fc)
    cb.run()
    ww = WaterWastewaterSystems(cd, fc)
    ww.run()
    cd.save_model_inputs("../test_case/saved_inputs_from_test_driver.yaml")
    #~ fc.calc_electricity_totals()
    #~ fc.forecast_population()
    fc.forecast_consumption()
    fc.forecast_generation()
    fc.forecast_average_kW()
    #~ fc.forecast_households()
    fc.calc_total_HF_forecast()
    #~ fc.population[0] = 11
    df = DataFrame( {"pop": fc.population,
                     "HH" : fc.households,
                     "kWh consumed" : fc.consumption,
                     "kWh generation": fc.generation,
                     "avg. kW": fc.average_kW,
                     "res HF": fc.res_HF,
                     "com HF":fc.com_HF,
                     "ww HF":fc.www_HF,
                     "total HF": fc.total_HF,}, 
                     np.array(range(len(fc.population))) + fc.start_year)
                     
    if com_data_file == "test_case/manley_data.yaml":
        df.to_csv("../test_case/run_df.csv",columns =["pop","HH","kWh consumed",
                                                    "kWh generation","avg. kW",
                                                    "res HF", "com HF","ww HF",
                                                    "total HF"])
        base_df = read_pickle("../test_case/base.pckl")
        (base_df == df).to_csv("../test_case/test_truth_table.csv", 
                                          columns =["pop","HH", "kWh consumed",
                                                    "kWh generation","avg. kW",
                                                    "res HF", "com HF", "ww HF",
                                                    "total HF"])
    

    return df, (cd,fc,rb,cb,ww)
