import pandas as pd
import geopandas as gpd
from j40_model.community_case import CommunityCase


def read_geo_state_file(city, state):
    geo = gpd.read_file(f'test_inputs/_geo_file_{state}.geojson')
    geo = geo.loc[geo.ctyname == city].copy()
    geo.GEOID = geo.GEOID.astype('int64')
    return geo


# read the geographic information from the state file
geo_file = read_geo_state_file(city='Wayne County, MI', state='mi')

# read the community file
state_file = pd.read_pickle('test_inputs/community_file_mi_demo.pkl')

# extract a community based on tract IDs within a county
com_file = state_file.loc[
    state_file.fips.isin(geo_file.GEOID.values)].copy()

cost_table = pd.read_pickle(
    'test_inputs/cost_assumptions.pkl')

# defining an EB target
eb_target = 0.07

# create a community case object
my_community = CommunityCase(df=com_file,
                             eb_target=eb_target,
                             cost_table=cost_table)

# Export community information to csv
my_community.community_table.to_csv('df.csv')

# Make changes to the eligible population
# Examples:
# 1 - define eligible AMI groups: pass a list [examples below]
my_community.el_ami = ['0-30%', '30-60%', '60-80%', '100%+', '80-100%']  # all
my_community.el_ami = my_community.community_table.ami.unique()  # all available in your community
my_community.el_ami = ['80-100%']  # one specific

# 2 - define eligible Tenure households
my_community.el_tenure = ['OWNER', 'RENTER']

# 3 - you can even update the energy burden target
my_community.eb_target = 0.06

# update settings
settings = {
    'inv_rate': 0.03,  # discount rate for investments
    'eb_weight': 1,  # energy burden weight (value between 0-1)
    'budget_limit': 1e6,  # maximum available budget
    'solver': 'glpk'
}

# run intervention
my_community.run_intervention(optimization=True, **settings)

# get a pandas dataframe with the eligible community inputs per tract
df1 = my_community.get_base_per_tract()

# get a pandas dataframe with the results per building
# select "just_eligible=False" to include results for non-eligible groups
df2 = my_community.get_results_per_building(just_eligible=True)

# get a pandas dataframe with the results per tract
df3 = my_community.get_results_per_tract(just_eligible=True)

print('run completed !!!')
