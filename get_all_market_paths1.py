import pandas, numpy, math, time
from gpxpy import geo

# Vectors
# -------------------------------------------------------------------------- #

products = ['ORA','POJ','ROJ','FCOJ']
regions = ['NE','MA','SE','MW','DS','NW','SW']
NE_markets = ['ANY','BOS','CLP','KEE','LAK','MBK','MVY','PGH','PHI','PVD','RER','SCR','SMS','SUP']
MA_markets = ['CRS','CVE','CWV','DTN','FRY','HIP','JTC','LXK','MAO','MAY','MSD','MSP','MTH','RCH','RRN','SHK','TIL']
SE_markets = ['CHR','DAY','FPR','FSC','GRN','HVA','JFL','MTG','OCL','PAN','WPB','YEM']
MW_markets = ['ABL','BYO','CED','CUP','ELK','FWA','GBW','GEE','GFK','HER','JAC','LSL','MAS','MND','NLW','OWT','SDL','SHL','SJF','STP','SWI','TRV']
DS_markets = ['BST','DEL','ELP','FTW','GRL','LAF','LRO','MCX','MKO','MRE','PRA','RSW','SGE','SME','SNA','TYE']
NW_markets = ['BTT','DIM','EUG','LEW','PCO','RSP','TWF','YKM']
SW_markets = ['BKR','DOZ','FSO','GRU','HUL','LOS','RFE','RNE','SCM','SFC','TCY']
all_markets = NE_markets + MA_markets + SE_markets + MW_markets + DS_markets + NW_markets + SW_markets

months = ['Sep','Oct','Nov','Dec','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug']
weeks = numpy.arange(0, 48, 1)
groves = ['FLA','CAL','TEX','ARZ','BRA','SPA']
plants = ['P07']
storages = ['S44','S51','S68']
transporters = ['TC', 'IC']

NUM_WEEKS = 48
NUM_MARKETS = 100

# -------------------------------------------------------------------------- #




# Read In Excel Spreasheets Using Pandas
# -------------------------------------------------------------------------- #

G_P = pandas.read_excel('Data/StaticData.xlsx', 'G->PS')
P_S = pandas.read_excel('Data/StaticData.xlsx', 'P->S')
S_M = pandas.read_excel('Data/StaticData.xlsx', 'S->M (avg)')
Terminals = pandas.read_excel('Data/StaticData.xlsx', 'Terminals')

grove_USprices = pandas.read_excel('Data/2019_Spot_Projections.xlsx')

# -------------------------------------------------------------------------- #




# Format Panda Tables (set dimensions/indices/columns)
# -------------------------------------------------------------------------- #

# G->PS
G_P.set_index(G_P['To:Fr'], inplace=True)
G_P.drop('To:Fr', inplace=True, axis=1)

# P->S
P_S.set_index(P_S['To:Fr'], inplace=True)
P_S.drop('To:Fr', inplace=True, axis=1)

# S->M
S_M.set_index(S_M['To:Fr'], inplace=True)
S_M.drop('To:Fr', inplace=True, axis=1)

# Terminals
Terminals.set_index(Terminals['Location'], inplace=True)
Terminals.drop('Location', inplace=True, axis=1)

# -------------------------------------------------------------------------- #




# Create Final Decision Tables
# -------------------------------------------------------------------------- #

# 1344 rows of optimal parameters sorted by profit, iterate through until capacity filled
path_indices = numpy.arange(len(products) * len(all_markets) * len(weeks))
path_columns = ['Contract', 'Product', 'Region', 'Market', 
                'Demand_Week', 'Storage_Week', 'Plant_Week', 'Purchase_Week', 
                'Grove', 'Plant', 'Storage', 'Transporter', 'Path_Cost', 'Avg_Cost', 
                'Price', 'Quantity', 'Profit', 'Year_Used']
paths_SPOT_ORA = pandas.DataFrame(index = path_indices, columns = path_columns, dtype = float)
paths_FUT_ORA = pandas.DataFrame(index = path_indices, columns = path_columns, dtype = float)
paths_FUT_FCOJ = pandas.DataFrame(index = path_indices, columns = path_columns, dtype = float)

# -------------------------------------------------------------------------- #




# Optimizing Functions
# -------------------------------------------------------------------------- #       

# get list of optimal parameters for every product/region/month and sort by profit
def get_all_market_paths():
    i = 0
    for p in products:
        for w in weeks:
            for m in all_markets:   
#                path = get_optimal_path(p, m, w, 'SPOT_ORA')
#                paths_SPOT_ORA.iloc[i:i+1, 0:17] = path
                
                path = get_optimal_path(p, m, w, 'FUT_ORA')
                paths_FUT_ORA.iloc[i:i+1, 0:17] = path
                
#                if (p == 'ROJ') | (p == 'FCOJ'):
#                    path = get_optimal_path(p, m, w, 'FUT_FCOJ')
#                    paths_FUT_FCOJ.iloc[i:i+1, 0:17] = path
                    
                i = i+1
    
    #paths_SPOT_ORA['Avg_Cost'] = paths_SPOT_ORA.groupby(['Product', 'Region', 'Demand_Week'])['Path_Cost'].transform(numpy.mean)
    paths_FUT_ORA['Avg_Cost'] = paths_FUT_ORA.groupby(['Product', 'Region', 'Demand_Week'])['Path_Cost'].transform(numpy.mean)
    #paths_FUT_FCOJ['Avg_Cost'] = paths_FUT_FCOJ.groupby(['Product', 'Region', 'Demand_Week'])['Path_Cost'].transform(numpy.mean)
    
# return cheapest path from purchase to delivery
def get_optimal_path(product, market, demand_week, contract):
    region = get_region(market)
    
    storage_week = get_storage_week(demand_week)
    plant_week = get_plant_week(product, demand_week, contract)
    purchase_week = get_purchase_week(product, demand_week, contract)
    purchase_month = months[int(math.floor(purchase_week / 4.0))] # convert from week to month
    
    transporter = 'TC' # for now not sure which to use
    storage = get_closest_storage(market)
    
    if (contract == 'SPOT_ORA'):
        all_groves = groves
    if (contract == 'FUT_ORA') | (contract == 'FUT_FCOJ'):
        all_groves = ['FLA']
        
    min_cost = float('inf')
    for g in all_groves:
        plant = get_relevant_plant(product, g, storage, contract)
            
        transportation_cost = get_transportation_cost(product, market, g, plant, storage, transporter, contract)
        purchase_cost = get_purchase_cost(product, g, purchase_month, contract)
        plant_cost = get_plant_cost(product, contract)
        reconstitution_cost = get_reconstitution_cost(product)
        
        total_cost = transportation_cost + purchase_cost + plant_cost + reconstitution_cost      

        if (total_cost < min_cost):
            min_cost = total_cost
            optimal_path = [contract, product, region, market, 
                            demand_week, storage_week, plant_week, purchase_week,
                            g, plant, storage, transporter, total_cost, 
                            0.0, 0.0, 0.0, 0]
            
    return optimal_path
     
# return closest storage to market region
def get_closest_storage(market):
    min_dist = float('inf')
    for s in storages:
        d = get_distance(market, s)
        if (d < min_dist):
            min_dist = d
            closest_storage = s
    
    return closest_storage

# return closest plant to storage
def get_relevant_plant(product, grove, storage, contract):
    if (contract == 'SPOT_ORA') | (contract == 'FUT_ORA'):
        if (product == 'ORA'): 
            return None
            
    if (contract == 'FUT_FCOJ'):
        if (product == 'ROJ'):
            return None
        if (product == 'FCOJ'):
            return None
        
    min_dist = float('inf')
    for p in plants:
        d = P_S.loc[storage, p]
        if (d < min_dist):
            min_dist = d
            plant = p
    
    return plant
    
# return cost of transporting from grove to market region
def get_transportation_cost(product, market, grove, plant, storage, transporter, contract):
    if (plant != None):
        if (transporter == 'TC'):
            my_P_to_S = P_S.loc[storage, plant] * 1.2
        elif (transporter == 'IC'):
            my_P_to_S = P_S.loc[storage, plant] * .65
    
    grove = get_transporting_grove(grove, contract)
    
    if (contract == 'SPOT_ORA') | (contract == 'FUT_ORA'): 
        if (product == 'ORA'):
            cost_G_to_P = 0
            cost_P_to_S = 0
            cost_G_to_S = get_distance(grove, storage) * .22  
        else:
            cost_G_to_P = G_P.loc[plant, grove] * .22
            cost_P_to_S = my_P_to_S
            cost_G_to_S = 0
            
    if (contract == 'FUT_FCOJ'):
        cost_G_to_P = 0
        cost_P_to_S = 0
        cost_G_to_S = get_distance('FLA', storage) * .22  
    
    cost_S_to_M = get_distance(storage, market) * 1.2    
    
    total_transportation_cost = cost_G_to_P + cost_P_to_S + cost_G_to_S + cost_S_to_M
    
    return total_transportation_cost
    
# return cost of purchasing oranges at grove during month
def get_purchase_cost(product, grove, month, contract):
    if (contract == 'SPOT_ORA'):
        purchase_cost = grove_USprices.loc[grove, month] * 2000 # lbs -> tons
    elif (contract == 'FUT_ORA') | (contract == 'FUT_FCOJ'):
        purchase_cost = 0

    return purchase_cost

# return cost of manufacturing POJ or ROJ
def get_plant_cost(product, contract):
    if (contract == 'SPOT_ORA') | (contract == 'FUT_ORA'):
        if (product == 'ORA'): plant_cost = 0
        if (product == 'POJ'): plant_cost = 2000
        if (product == 'ROJ'): plant_cost = 1000
        if (product == 'FCOJ'): plant_cost = 1000
    elif (contract == 'FUT_FCOJ'):
        if (product == 'ROJ'): plant_cost = 0
        if (product == 'FCOJ'): plant_cost = 0
    
    return plant_cost

# return cost of reconstituting FCOJ into ROJ
def get_reconstitution_cost(product):
    if (product == 'ROJ'):
        reconstitution_cost = 650
    else:
        reconstitution_cost = 0
        
    return reconstitution_cost

def get_transporting_grove(grove, contract):
    if (contract == 'SPOT_ORA'):
        if (grove in ['BRA','SPA']):
            return 'FLA'
    
    if (contract == 'FUT_ORA') | (contract == 'FUT_FCOJ'):
        return 'FLA'
    
    return grove
    
def get_storage_week(demand_week):
    storage_week = demand_week - 1
    
    if (storage_week < 0):
        storage_week = 48 + storage_week
        
    return storage_week
    
# return week that product is in processing plant
def get_plant_week(product, demand_week, contract):
    if (contract == 'SPOT_ORA') | (contract == 'FUT_ORA'):
        if (product == 'ORA'):
            return None
        if (product == 'POJ'):
            plant_week =  demand_week - 3
        if (product == 'ROJ'):
            plant_week  = demand_week - 4
        if (product == 'FCOJ'):
            plant_week =  demand_week - 3  
            
    if (contract == 'FUT_FCOJ'):
        if (product == 'ROJ'):
            return None
        if (product == 'FCOJ'):
            return None
        
        
    if (plant_week < 0):
        plant_week = 48 + plant_week
        
    return plant_week
    
# return week that product is purchased from grove
def get_purchase_week(product, demand_week, contract):
    if (contract == 'SPOT_ORA') | (contract == 'FUT_ORA'):
        if (product == 'ORA'):
            purchase_week = demand_week - 2
        if (product == 'POJ'):
            purchase_week = demand_week - 4
        if (product == 'ROJ'):
            purchase_week = demand_week - 5
        if (product == 'FCOJ'):
            purchase_week = demand_week - 4
            
    if (contract == 'FUT_FCOJ'):
        if (product == 'ROJ'):
            purchase_week = demand_week - 3
        if (product == 'FCOJ'):
            purchase_week = demand_week - 2
        
        
    if (purchase_week < 0):
        purchase_week = 48 + purchase_week
        
    return purchase_week

# return miles distance from grove to storage
def get_distance(a, b):       
    a_lat = float(Terminals.loc[a, 'Latitude'])
    a_long = float(Terminals.loc[a, 'Longtitude'])
    b_lat = float(Terminals.loc[b, 'Latitude'])
    b_long = float(Terminals.loc[b, 'Longtitude'])

    # get distance in meters between two points
    dist = geo.haversine_distance(a_lat, a_long, b_lat, b_long)
    
    # convert to miles and return
    return (dist*0.000621371*1.26)   
       
def get_region(market):
    if (market in NE_markets):
        return 'NE'
    if (market in MA_markets):
        return 'MA'
    if (market in SE_markets):
        return 'SE'
    if (market in MW_markets):
        return 'MW'
    if (market in DS_markets):
        return 'DS'
    if (market in NW_markets):
        return 'NW'
    if (market in SW_markets):
        return 'SW'

def get_markets(region):
    if (region == 'NE'):
        return NE_markets
    if (region == 'MA'):
        return MA_markets
    if (region == 'SE'):
        return SE_markets
    if (region == 'MW'):
        return MW_markets
    if (region == 'DS'):
        return DS_markets
    if (region == 'NW'):
        return NW_markets
    if (region == 'SW'):
        return SW_markets
    
# -------------------------------------------------------------------------- #




# Test Code
# -------------------------------------------------------------------------- #
start_time = time.time()

get_all_market_paths()

#product = 'FCOJ'
#market = 'ANY'
#demand_week = 4
#contract = 'FUT_FCOJ'
#path = get_optimal_path(product, market, demand_week, contract)
#print(path)

print("--- %s seconds ---" % (time.time() - start_time))
# -------------------------------------------------------------------------- #




# Action Items
# -------------------------------------------------------------------------- #
    

        
# -------------------------------------------------------------------------- #



