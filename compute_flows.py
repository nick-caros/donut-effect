"""

This program takes a shapefile containing polygons representing all ZIP
code boundaries in the United States, as well as the USPS Change of Address
data, and returns a geoJSON file containing the net change in residents 
for a specified time frame for a specified state or city. 

Author: Nick Caros, October 2021

"""

import pandas as pd
import geopandas as gpd

" ----- User Inputs ----- "

# Define city and state filters (set list to empty if no filter needed)
filter_city = [] 
filter_state = ['IN', 'IL', 'WI']

# Choose a flow type from "INDIVIDUAL", "FAMILY", "BUSINESS", "TOTAL"
flow_type = 'INDIVIDUAL'

# Choose time frame from "Full", "2020 Only", "2021 Only"
timeframe = "Full"

# Output file name
outfile = 'chicago_flows_full.geojson'

" ----- Main Program ----- "

# Import shapes and filter
zip_shp = gpd.read_file('tl_2019_us_zcta510/tl_2019_us_zcta510.shp')
zip_shp = zip_shp[['GEOID10', 'geometry']]
zip_shp.columns = ['ZIPCODE', 'geometry']
zip_shp['ZIPCODE'] = zip_shp['ZIPCODE'].astype('float')  # first convert to float before int
zip_shp['ZIPCODE'] = zip_shp['ZIPCODE'].astype('Int32')

# Import 2020 USPS data and filter out January - March data
if timeframe != "2021 Only":
    df20 = pd.read_csv('usps_coa_2020.csv')
    df20 = df20[df20.YYYYMM.isin([202004,202005,202006,202007,202008,202009,202010,202011,202012])]
    df20['ZIPCODE'] = df20['ZIPCODE'].str.replace(r'\D', '', regex=True)
    df20['ZIPCODE'] = df20['ZIPCODE'].astype('float')
    df20['ZIPCODE'] = df20['ZIPCODE'].astype('Int32')

# Append 2021 USPS data and filter / format
if timeframe != "2020 Only":
    df21 = pd.read_csv('usps_coa_sept2021.csv')
    df21['ZIPCODE'] = df21['ZIPCODE'].astype('float') 
    df21['ZIPCODE'] = df21['ZIPCODE'].astype('Int32')

if timeframe == "Full":
    df = df21.append(df20)
elif timeframe == "2021 Only": 
    df = df21
else:
    df = df20

df['CITY'] = df['CITY'].str.rstrip()
if len(filter_state) > 0: df = df[df.STATE.isin(filter_state)]
if len(filter_city) > 0: df = df[df.CITY.isin(filter_city)]

type_dict = {'INDIVIDUAL': ['TOTAL INDIVIDUAL','TOTAL INDIVIDUAL.1'],
             'FAMILY': ['TOTAL FAMILY','TOTAL FAMILY.1'],
             'BUSINESS': ['TOTAL BUSINESS','TOTAL BUSINESS.1'],
             'TOTAL': ['TOTAL FROM ZIP', 'TOTAL TO ZIP']}

flow_dfs = df.groupby(by=['ZIPCODE'], as_index = False)[type_dict[flow_type]].sum()
df = df.groupby(by=['ZIPCODE'], as_index = False)[['CITY', 'STATE']].first()
df['TOTAL_TO'] = flow_dfs[type_dict[flow_type][1]]   
df['TOTAL_FROM'] = flow_dfs[type_dict[flow_type][0]]   
df['TOTAL_FLOW'] = df['TOTAL_TO'] - df['TOTAL_FROM']

gdf = pd.merge(df, zip_shp, on='ZIPCODE')
gdf = gpd.GeoDataFrame(gdf)
gdf.to_file(outfile, driver="GeoJSON")