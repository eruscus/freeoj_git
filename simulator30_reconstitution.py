import pandas, random, numpy, math
from gpxpy import geo

# vectors
# -------------------------------------------------------------------------- #

products = ['ORA','POJ','ROJ','FCOJ']
regions = ['NE','MA','SE','MW','DS','NW','SW']
months = ['Sep','Oct','Nov','Dec','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug']
groves = ['FLA','CAL','TEX','ARZ','BRA','SPA']
plants = ['P07']
storages = ['S44','S51','S68']
transporters = ['IC', 'TC']
all_years = ['2015','2016','2017','2018','2019','2020']
this_year = '2016'
futures_ON = 0

# -------------------------------------------------------------------------- #




# read in excel spreasheets using pandas
# -------------------------------------------------------------------------- #

G_P = pandas.read_excel('Data/StaticData.xlsx', 'G->PS')
P_S = pandas.read_excel('Data/StaticData.xlsx', 'P->S')
S_M = pandas.read_excel('Data/StaticData.xlsx', 'S->M (avg)')
Terminals = pandas.read_excel('Data/StaticData.xlsx', 'Terminals')

raw_materials = pandas.read_excel('Data/MomPop/Results/MomPop2015.xlsm', 'raw_materials')
#grove = pandas.read_excel('Data/MomPop/Results/MomPop2015.xlsm', 'grove')
grove_USprices = pandas.read_excel('Data/HarvestPricesWith2017Projection.xlsx', '2017 Projections')

ORA_equations = pandas.read_csv('Data/ORA_equations.csv')
POJ_equations = pandas.read_csv('Data/POJ_equations.csv')
ROJ_equations = pandas.read_csv('Data/ROJ_equations.csv')
FCOJ_equations = pandas.read_csv('Data/FCOJ_equations.csv')

ORA_past_points =pandas.read_excel('Data/Monthly_Price_Demand.xlsx', 'ORA')
POJ_past_points =pandas.read_excel('Data/Monthly_Price_Demand.xlsx', 'POJ')
ROJ_past_points =pandas.read_excel('Data/Monthly_Price_Demand.xlsx', 'ROJ')
FCOJ_past_points =pandas.read_excel('Data/Monthly_Price_Demand.xlsx', 'FCOJ')

# -------------------------------------------------------------------------- #




# format panda tables (set dimensions/indices/columns)
# -------------------------------------------------------------------------- #

# US$ Prices of oranges at the Spot Market($/lb) ORA
#grove_USprices = grove.iloc[16:22, 2:14]
#grove_USprices.columns = months
#grove_USprices.set_index([groves], inplace=True)

# Future Prices
ORA_fut_prices = raw_materials.iloc[27:33, 13:14]
ORA_fut_prices.columns = ['Price']
ORA_fut_prices.set_index([all_years], inplace=True)

FCOJ_fut_prices = raw_materials.iloc[33:39, 13:14]
FCOJ_fut_prices.columns = ['Price']
FCOJ_fut_prices.set_index([all_years], inplace=True)

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

# Price-Demand Equations
ORA_slopes = ORA_equations.iloc[0:7, 1:13]
ORA_slopes.columns = [months]
ORA_slopes.set_index([regions], inplace=True)

ORA_intercepts = ORA_equations.iloc[0:7, 13:25]
ORA_intercepts.columns = [months]
ORA_intercepts.set_index([regions], inplace=True)

POJ_slopes = POJ_equations.iloc[0:7, 1:13]
POJ_slopes.columns = [months]
POJ_slopes.set_index([regions], inplace=True)

POJ_intercepts = POJ_equations.iloc[0:7, 13:25]
POJ_intercepts.columns = [months]
POJ_intercepts.set_index([regions], inplace=True)

ROJ_slopes = ROJ_equations.iloc[0:7, 1:13]
ROJ_slopes.columns = [months]
ROJ_slopes.set_index([regions], inplace=True)

ROJ_intercepts = ROJ_equations.iloc[0:7, 13:25]
ROJ_intercepts.columns = [months]
ROJ_intercepts.set_index([regions], inplace=True)

FCOJ_slopes = FCOJ_equations.iloc[0:7, 1:13]
FCOJ_slopes.columns = [months]
FCOJ_slopes.set_index([regions], inplace=True)

FCOJ_intercepts = FCOJ_equations.iloc[0:7, 13:25]
FCOJ_intercepts.columns = [months]
FCOJ_intercepts.set_index([regions], inplace=True)

# Past Points
ORA_past_points.set_index(ORA_past_points['Unnamed: 1'], inplace=True)
ORA_past_points.drop('Unnamed: 0', inplace=True, axis=1)
ORA_past_points.drop('Unnamed: 1', inplace=True, axis=1)

POJ_past_points.set_index(POJ_past_points['Unnamed: 1'], inplace=True)
POJ_past_points.drop('Unnamed: 0', inplace=True, axis=1)
POJ_past_points.drop('Unnamed: 1', inplace=True, axis=1)

ROJ_past_points.set_index(ROJ_past_points['Unnamed: 1'], inplace=True)
ROJ_past_points.drop('Unnamed: 0', inplace=True, axis=1)
ROJ_past_points.drop('Unnamed: 1', inplace=True, axis=1)

FCOJ_past_points.set_index(FCOJ_past_points['Unnamed: 1'], inplace=True)
FCOJ_past_points.drop('Unnamed: 0', inplace=True, axis=1)
FCOJ_past_points.drop('Unnamed: 1', inplace=True, axis=1)

# -------------------------------------------------------------------------- #




# final decision matrices
# -------------------------------------------------------------------------- #

# Purchases at the Spot Market(tons per week in a month) (ORA)
spot_purchases = pandas.DataFrame(data = 0.0, index = groves, columns = months)

# Purchases at the Futures Market(tons) (ORA and FCOJ)
fut_purchases_ORA = pandas.DataFrame(data = 0.0, index = all_years, columns = ['Price'])
fut_purchases_FCOJ = pandas.DataFrame(data = 0.0, index = all_years, columns = ['Price'])

# Arrival of matured ORA Futures and FCOJ Futures(%)
fut_arrivals = pandas.DataFrame(data = 0.0, index = ['ORA','FCOJ'], columns = months)
fut_arrivalsP = fut_arrivals.copy()

# Ship ORA from Groves to Plants or Storages(%)
shipping1 = pandas.DataFrame(data = 0.0, index = groves, columns = (plants+storages))
shipping1P = shipping1.copy()

# Process ORA into POJ or FCOJ(%)
manufacturing_columns = []
for p in plants:
    manufacturing_columns = manufacturing_columns + [p+'_POJ'] + [p+'_FCOJ']
manufacturing = pandas.DataFrame(data = 0.0, index = ['Proportion'], columns = manufacturing_columns)
manufacturingP = manufacturing.copy()

# Ship FCOJ (futures) from FLA to Storages; Ship POJ, FCOJ from Plants to Storages(%)
shipping2_columns = ['Futures_FCOJ']
for p in plants:
    shipping2_columns = shipping2_columns + [p+'_POJ'] + [p+'_FCOJ']
shipping2 = pandas.DataFrame(data = 0.0, index = storages, columns = shipping2_columns)
shipping2P = shipping2.copy()

# Reconstitute FCOJ into ROJ at Storages(%)
reconstitution = pandas.DataFrame(data = 0.0, index = storages, columns = months)
reconstitution2 = pandas.DataFrame(data = 0.0, index = storages, columns = months)
reconstitutionP = reconstitution.copy()

# Pricing for each product in each region($/lb)
pricing_ORA = pandas.DataFrame(data = 0.0, index = regions, columns = months)
pricing_POJ = pandas.DataFrame(data = 0.0, index = regions, columns = months)
pricing_ROJ = pandas.DataFrame(data = 0.0, index = regions, columns = months)
pricing_FCOJ = pandas.DataFrame(data = 0.0, index = regions, columns = months)

# all decisions together
decisions = [spot_purchases, shipping1, manufacturing, shipping2, reconstitution, pricing_ORA, pricing_POJ, pricing_ROJ, pricing_FCOJ]

total_profit = 0.0


# track how full each plant/storage will be in each month
capacity = pandas.DataFrame(data = 0.0, index = (plants+storages), columns = months)

# raj
raj_ORA = pandas.DataFrame(data = 0.0, index = regions, columns = months)
raj_POJ = pandas.DataFrame(data = 0.0, index = regions, columns = months)
raj_ROJ = pandas.DataFrame(data = 0.0, index = regions, columns = months)
raj_FCOJ = pandas.DataFrame(data = 0.0, index = regions, columns = months)


# -------------------------------------------------------------------------- #




# Optimizing Functions
# -------------------------------------------------------------------------- #

# determine all values for decision spreadsheet
def get_decisions():
    for p in products:
        for r in regions:
            for m in months:
                slope = get_slope(p, r, m)
                intercept = get_intercept(p, r, m)
                
                parameters = get_optimal_parameters(p, r, m, slope, intercept)
                
                grove = parameters[3]
                plant = parameters[4]
                storage = parameters[5]
                price = parameters[7]
                quantity = parameters[8]
                profit = parameters[9]
                
                update_spot_purchases(quantity, m, grove)
                update_fut_purchases(quantity, p, grove)
                update_fut_arrivals(quantity, p, m, grove)
                update_shipping1(quantity, p, grove, plant, storage)
                update_manufacturing(quantity, p, plant)
                update_shipping2(quantity, p, plant, storage)
                update_reconstitution(quantity, p, m, storage)
                update_reconstitution2(quantity, p, m, storage)
                update_pricing(price, p, r, m)
                update_total_profit(profit)
                
                update_capacity(quantity, p, m, plant, storage)
                update_raj(quantity, p, r, m)
    
    calculate_fut_arrivalsP()
    calculate_shipping1P()
    calculate_manufacturingP()
    calculate_shipping2P()
    calculate_reconstitutionP()
              
# return optimal path, price, and quantity for a product/region/month
def get_optimal_parameters(product, region, month, slope, intercept):
    slope = slope / .0005 # lbs -> tons
    intercept = intercept / .0005 # lbs -> tons 

    optimal_path = get_optimal_path(product, region, month)  
    path_cost = optimal_path[0]  
    grove = optimal_path[1]
    plant = optimal_path[2]
    storage = optimal_path[3]
    transporter = optimal_path[4]      
    
    quantity = (path_cost - intercept) / (2 * slope)
    price = slope*quantity + intercept
    
    if (price > 4.0/.0005):
        price = 4.0/.0005
        quantity = (price - intercept) / slope
        
    profit = quantity * (price - path_cost)
            
    if ((price < 0.0) | (quantity < 0.0) | (profit < 0.0) | math.isnan(slope) | math.isnan(intercept)):
        price = 0.0
        quantity = 0.0
        profit = 0.0
    
    past_points = get_past_points(product)
    price_index = region + ':Price'
    quantity_index = region + ':Demand'
    for i in range(1,13):
        col = month + str(i)
        price2 = past_points.loc[price_index, col] / .0005 # lbs -> tons
        quantity2 = past_points.loc[quantity_index, col]
        profit2 = quantity2 * (price2 - path_cost)
        
        if (profit2 > profit):
            price = price2
            quantity = quantity2
            profit = profit2    
        
    price = price * .0005 # tons -> lbs
    
    parameters = [product, region, month, grove, plant, storage, transporter, 
                  price, quantity, profit]
    
    return parameters

# return cheapest path from purchase to delivery
def get_optimal_path(product, region, month):
    transporter = 'IC' # for now no tankers available
    storage = get_closest_storage(region)
    
    min_cost = float('inf')
    if (futures_ON == 1): all_groves = groves+['FUT']
    if (futures_ON == 0): all_groves = groves
    for g in all_groves:
        plant = get_relevant_plant(product, g, storage)
            
        transportation_cost = get_transportation_cost(product, region, g, plant, storage, transporter)
        purchase_cost = get_purchase_cost(product, g, month)
        plant_cost = get_plant_cost(product, g)
        reconstitution_cost = get_reconstitution_cost(product)
        
        total_cost = transportation_cost + purchase_cost + plant_cost + reconstitution_cost      

        if (total_cost < min_cost):
            min_cost = total_cost
            optimal_path = [total_cost, g, plant, storage, transporter]
            
    return optimal_path
    
# return closest storage to market region
def get_closest_storage(region):
    min_dist = float('inf')
    for s in storages:
        d = S_M.loc[region, s]
        if (d < min_dist):
            min_dist = d
            closest_storage = s
    
    return closest_storage

# return closest plant to storage
def get_relevant_plant(product, grove, storage):
    if (grove != 'FUT'):
        if (product == 'ORA'): return None
    if (grove == 'FUT'):
        if (product == 'ORA'): return None
        if (product == 'ROJ'): return None
        if (product == 'FCOJ'): return None
    
    
    min_dist = float('inf')
    for p in plants:
        d = P_S.loc[storage, p]
        if (d < min_dist):
            min_dist = d
            plant = p
    
    return plant

# return cost of transporting from grove to market region
def get_transportation_cost(product, region, grove, plant, storage, transporter):
    if (grove != 'FUT'): 
        if (product == 'ORA'):
            cost_G_to_P = 0
            cost_P_to_S = 0
            cost_G_to_S = get_grove_to_storage_distance(grove, storage) * .22  
        elif (grove in ['FLA','CAL','TEX','ARZ']):
            cost_G_to_P = G_P.loc[plant, grove] * .22
            cost_P_to_S = P_S.loc[storage, plant] * .65
            cost_G_to_S = 0
        elif (grove in ['BRA','SPA']):
            cost_G_to_P = G_P.loc[plant, 'FLA'] * .22
            cost_P_to_S = P_S.loc[storage, plant] * .65
            cost_G_to_S = 0
    elif (grove == 'FUT'):
        if (product == 'POJ'):
            cost_G_to_P = G_P.loc[plant, 'FLA'] * .22
            cost_P_to_S = P_S.loc[storage, plant] * .65
            cost_G_to_S = 0 
        else:
            cost_G_to_P = 0
            cost_P_to_S = 0
            cost_G_to_S = get_grove_to_storage_distance('FLA', storage) * .22  
    
    cost_S_to_M = S_M.loc[region, storage] * 1.2    
    
    total_transportation_cost = cost_G_to_P + cost_P_to_S + cost_G_to_S + cost_S_to_M
    
    #print('cost_G_to_P = ' + str(cost_G_to_P))
    #print('cost_P_to_S = ' + str(cost_P_to_S))
    #print('cost_G_to_S = ' + str(cost_G_to_S))
    #print('cost_S_to_M = ' + str(cost_S_to_M))
    #print ('inventory hold cost = ' + str(inv_hold_cost))
    #print('total_transportation_cost = ' + str(total_transportation_cost))
    
    return total_transportation_cost
    
# return cost of purchasing oranges at grove during month
def get_purchase_cost(product, grove, month):
    if (grove != 'FUT'):
        purchase_cost = grove_USprices.loc[grove, month] / .0005 # lbs -> tons
    elif (grove == 'FUT'):
        if ((product == 'ORA') | (product == 'POJ')):
            purchase_cost = ORA_fut_prices.loc['2016', 'Price'] / .0005 # lbs -> tons
        elif ((product == 'ROJ') | (product == 'FCOJ')):
            purchase_cost = FCOJ_fut_prices.loc['2016', 'Price'] / .0005 # lbs -> tons

    #print('purchase_cost = ' + str(purchase_cost))

    return purchase_cost

# return cost of manufacturing POJ or ROJ
def get_plant_cost(product, grove):
    if (grove != 'FUT'):
        if (product == 'ORA'): plant_cost = 0
        if (product == 'POJ'): plant_cost = 2000
        if (product == 'ROJ'): plant_cost = 1000
        if (product == 'FCOJ'): plant_cost = 1000
    elif (grove == 'FUT'):
        if (product == 'ORA'): plant_cost = 0
        if (product == 'POJ'): plant_cost = 2000
        if (product == 'ROJ'): plant_cost = 0
        if (product == 'FCOJ'): plant_cost = 0
        
    #print('plant_cost = ' + str(plant_cost))
    
    return plant_cost

# return cost of reconstituting FCOJ into ROJ
def get_reconstitution_cost(product):
    if (product == 'ROJ'):
        reconstitution_cost = 650
    else:
        reconstitution_cost = 0
        
    #print('reconstitution_cost = ' + str(reconstitution_cost))
        
    return reconstitution_cost

# return miles distance from grove to storage
def get_grove_to_storage_distance(grove, storage):
    if (grove == 'FUT'):
        grove = 'FLA'
        
    grove_lat = float(Terminals.loc[grove, 'Latitude'])
    grove_long = float(Terminals.loc[grove, 'Longtitude'])
    storage_lat = float(Terminals.loc[storage, 'Latitude'])
    storage_long = float(Terminals.loc[storage, 'Longtitude'])

    # get distance in meters between two points
    dist = geo.haversine_distance(grove_lat, grove_long, storage_lat, storage_long)
    
    # convert to miles and return
    return (dist*0.000621371*1.26)    
    
def get_time_to_market(product, transportation_type, storage_location, processing_center, is_rand):
    time_G_to_P = 1
    time_processing = 1 #clarifying this on piazza
    time_reconstitution = 0
    time_S_to_M = 1
    
    distance_between_loc =  P_S.loc[storage_location, processing_center]
    # skip processing plant if oranges
    if (product == 'ORA'):
        time_G_to_P = 0 # change from "time_G_to_S = 0", typo?
        
    # ROJ requires one week to reconstitute
    if (product == 'ROJ'):
        time_reconstitution = 1        
    
    # two possible transportation types: 'T' (tanker), 'IC' (independent carrier)
    if (transportation_type == 'T'):
        time_P_to_S = 1 # tanker guaranteed to be one week
    else:
        # expected value calculation
        if (is_rand == 0):
            time_P_to_S = .61 * 1 + .3 * 2 + .09 * 3 + 1.0*(distance_between_loc > 2000)
        # random instance calculation
        else:
            rand_P_to_S = random.random()
            if (rand_P_to_S <= .61):
                time_P_to_S = 1
            elif (rand_P_to_S > .91):
                time_P_to_S = 3
            else:
                time_P_to_S = 2               
        time_P_to_S = time_P_to_S + 1.0*(distance_between_loc > 2000)    
        
    return time_G_to_P + time_processing + time_P_to_S + time_reconstitution + time_S_to_M
    
# return slope from appropriate product table
def get_slope(product, region, month):
    if (product == 'ORA'):
        slope = ORA_slopes.loc[region, month]
    elif (product == 'POJ'):
        slope = POJ_slopes.loc[region, month]
    elif (product == 'ROJ'):
        slope = ROJ_slopes.loc[region, month]
    elif (product == 'FCOJ'):
        slope = FCOJ_slopes.loc[region, month]
    
    return slope
    
# return slope from appropriate product table
def get_intercept(product, region, month):
    if (product == 'ORA'):
        intercept = ORA_intercepts.loc[region, month]
    if (product == 'POJ'):
        intercept = POJ_intercepts.loc[region, month]
    if (product == 'ROJ'):
        intercept = ROJ_intercepts.loc[region, month]
    if (product == 'FCOJ'):
        intercept = FCOJ_intercepts.loc[region, month]
    
    return intercept    

def get_past_points(product):
    if (product == 'ORA'):
        past_points = ORA_past_points
    if (product == 'POJ'):
        past_points = POJ_past_points
    if (product == 'ROJ'):
        past_points = ROJ_past_points
    if (product == 'FCOJ'):
        past_points = FCOJ_past_points
    
    return past_points
    
# -------------------------------------------------------------------------- #




# Updating/Counting Functions
# -------------------------------------------------------------------------- #

# add quantity to raw materials path
def update_spot_purchases(quantity, month, grove):
    if (grove != 'FUT'):
        spot_purchases.loc[grove, month] = spot_purchases.loc[grove, month] + quantity

# add quantity to futures path
def update_fut_purchases(quantity, product, grove):
    if (grove == 'FUT'):
        if ((product == 'ORA') | (product == 'POJ')):
            fut_purchases_ORA.loc[this_year, 'Price'] = fut_purchases_ORA.loc[this_year, 'Price'] + quantity
        if ((product == 'ROJ') | (product == 'FCOJ')):
            fut_purchases_FCOJ.loc[this_year, 'Price'] = fut_purchases_FCOJ.loc[this_year, 'Price'] + quantity

# add quantity to arrival month
def update_fut_arrivals(quantity, product, month, grove):
    if (grove == 'FUT'):
        if ((product == 'ORA') | (product == 'POJ')):
            fut_arrivals.loc['ORA', month] = fut_arrivals.loc['ORA', month] + quantity
        if ((product == 'ROJ') | (product == 'FCOJ')):
            fut_arrivals.loc['FCOJ', month] = fut_arrivals.loc['FCOJ', month] + quantity
    
# add quantity to shipping1 path
def update_shipping1(quantity, product, grove, plant, storage):
    if ((product == 'ORA') & (grove != 'FUT')):
        shipping1.loc[grove, storage] = shipping1.loc[grove, storage] + quantity
    elif (grove == 'FUT'):
        shipping1.loc['FLA', storage] = shipping1.loc['FLA', storage] + quantity
    else:
        shipping1.loc[grove, plant] = shipping1.loc[grove, plant] + quantity

# add quantity to manufacturing path
def update_manufacturing(quantity, product, plant):
    if (product == 'POJ'):
        manufacturing.loc['Proportion', (plant+'_POJ')] = manufacturing.loc['Proportion', (plant+'_POJ')] + quantity
    elif ((product == 'ROJ') | (product == 'FCOJ')):
        if (plant != None):
            manufacturing.loc['Proportion', (plant+'_FCOJ')] = manufacturing.loc['Proportion', (plant+'_FCOJ')] + quantity                      

# add quantity to shipping2 path
def update_shipping2(quantity, product, plant, storage):
    if (product == 'POJ'):
        shipping2.loc[storage, (plant+'_POJ')] = shipping2.loc[storage, (plant+'_POJ')] + quantity
    elif ((product == 'ROJ') | (product == 'FCOJ')):
        if (plant != None):
            shipping2.loc[storage, (plant+'_FCOJ')] = shipping2.loc[storage, (plant+'_FCOJ')] + quantity 
        elif (plant == None):
            shipping2.loc[storage, 'Futures_FCOJ'] = shipping2.loc[storage, ('Futures_FCOJ')] + quantity

# add quantity to reconstitution path
def update_reconstitution(quantity, product, month, storage):
    if (product == 'ROJ'):
        reconstitution.loc[storage, month] = reconstitution.loc[storage, month] + quantity

def update_reconstitution2(quantity, product, month, storage):
    if (product == 'FCOJ'):
        reconstitution2.loc[storage, month] = reconstitution2.loc[storage, month] + quantity
        
# update pricing for path        
def update_pricing(price, product, region, month):
    if (product == 'ORA'):
        pricing_ORA.loc[region, month] = price
    if (product == 'POJ'):
        pricing_POJ.loc[region, month] = price
    if (product == 'ROJ'):
        pricing_ROJ.loc[region, month] = price
    if (product == 'FCOJ'):
        pricing_FCOJ.loc[region, month] = price

# add path profit to total profit
def update_total_profit(profit):
    global total_profit
    total_profit = total_profit + profit

# add quantities to plant/storage for each month
def update_capacity(quantity, product, month, plant, storage):
    if (plant != None):
        capacity.loc[plant, month] = capacity.loc[plant, month] + quantity
        
    capacity.loc[storage, month] = capacity.loc[storage, month] + quantity

# update pricing for path        
def update_raj(quantity, product, region, month):
    if (product == 'ORA'):
        raj_ORA.loc[region, month] = raj_ORA.loc[region, month] + quantity
    if (product == 'POJ'):
        raj_POJ.loc[region, month] = raj_POJ.loc[region, month] + quantity
    if (product == 'ROJ'):
        raj_ROJ.loc[region, month] = raj_ROJ.loc[region, month] + quantity
    if (product == 'FCOJ'):
        raj_FCOJ.loc[region, month] = raj_FCOJ.loc[region, month] + quantity

# calculate future arrivals monthly percentages
def calculate_fut_arrivalsP(): 
    for r in range(0, 2):
        total = 0.0
        for c in range(0, 12):
            total = total + fut_arrivals.iloc[r, c]

        for c in range(0, 12):
            if (total == 0):
                fut_arrivalsP.iloc[r, c] = 0.0
            else:
                fut_arrivalsP.iloc[r, c] = fut_arrivals.iloc[r, c] / total * 100
    
# calculate shipping1 percentages
def calculate_shipping1P():
    nrow = shipping1.shape[0]
    ncol = shipping1.shape[1]
    
    for r in range(0, nrow):
        total = 0.0
        for c in range(0, ncol):
            total = total + shipping1.iloc[r, c]

        for c in range(0, ncol):
            if (total == 0):
                shipping1P.iloc[r, c] = 0.0
            else:
                shipping1P.iloc[r, c] = shipping1.iloc[r, c] / total * 100

# calculate manufacturing percentages
def calculate_manufacturingP():
    ncol = manufacturing.shape[1]
    num_plants = int(ncol/2)
    
    for p in range(0, num_plants):
        total = 0.0
        total = total + manufacturing.iloc[0, 2*p]
        total = total + manufacturing.iloc[0, 2*p+1]
        
        if (total == 0):
            manufacturingP.iloc[0, 2*p] = 0.0
            manufacturingP.iloc[0, 2*p+1] = 100.0
        else:
            manufacturingP.iloc[0, 2*p] = manufacturing.iloc[0, 2*p] / total * 100
            manufacturingP.iloc[0, 2*p+1] = manufacturing.iloc[0, 2*p+1] / total * 100
  
# calculate shipping2 percentages
def calculate_shipping2P():
    nrow = shipping2.shape[0]
    ncol = shipping2.shape[1]
    
    for c in range(0, ncol):
        total = 0.0
        for r in range(0, nrow):
            total = total + shipping2.iloc[r, c]

        for r in range(0, nrow):
            if (total == 0):
                shipping2P.iloc[r, c] = 0.0
            else:
                shipping2P.iloc[r, c] = shipping2.iloc[r, c] / total * 100  
  
# calculate reconstitution percentages
def calculate_reconstitutionP():
    nrow = reconstitution.shape[0]
    ncol = reconstitution.shape[1]
    
    for r in range(0, nrow):
        for c in range(0, ncol):
            total = reconstitution.iloc[r, c] + reconstitution2.iloc[r, c]
            if (total == 0):
                reconstitutionP.iloc[r, c] = 0.0
            else:
                reconstitutionP.iloc[r, c] = reconstitution.iloc[r, c] / total * 100

# -------------------------------------------------------------------------- #
    



# Test Code
# -------------------------------------------------------------------------- #

get_decisions()
print(total_profit)
print()

#product = 'FCOJ'
#region = 'NE'
#month = 'Apr'
#
#slope = FCOJ_slopes.loc[region, month]
#intercept = FCOJ_intercepts.loc[region, month]
#
#test_params = get_optimal_parameters(product, region, month, slope, intercept)
#print(test_params)

# -------------------------------------------------------------------------- #




# Action Items
# -------------------------------------------------------------------------- #
    

        
# -------------------------------------------------------------------------- #







