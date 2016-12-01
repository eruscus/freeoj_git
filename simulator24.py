import pandas, random, numpy, math
from gpxpy import geo

# vectors
# -------------------------------------------------------------------------- #

regions = ['NE','MA','SE','MW','DS','NW','SW']
months = ['Sep','Oct','Nov','Dec','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug']
products = ['ORA','POJ','ROJ','FCOJ']
groves = ['FLA','CAL','TEX','ARZ','BRA','SPA']
plants = ['P07']
storages = ['S44','S51','S68']
transporters = ['IC', 'TC']

# -------------------------------------------------------------------------- #




# read in excel spreasheets using panda
# -------------------------------------------------------------------------- #

G_P = pandas.read_excel('Data/StaticData.xlsx', 'G->PS')
P_S = pandas.read_excel('Data/StaticData.xlsx', 'P->S')
S_M = pandas.read_excel('Data/StaticData.xlsx', 'S->M (avg)')
Terminals = pandas.read_excel('Data/StaticData.xlsx', 'Terminals')

grove = pandas.read_excel('Data/MomPop/Results/MomPop2015.xlsm', 'grove')

ORA_slopes = pandas.read_excel('Data/Price_Demand_Equations.xlsx', 'ORA_Slope')
ORA_intercepts = pandas.read_excel('Data/Price_Demand_Equations.xlsx', 'ORA_Intercept')
POJ_slopes = pandas.read_excel('Data/Price_Demand_Equations.xlsx', 'POJ_Slope')
POJ_intercepts = pandas.read_excel('Data/Price_Demand_Equations.xlsx', 'POJ_Intercept')
ROJ_slopes = pandas.read_excel('Data/Price_Demand_Equations.xlsx', 'ROJ_Slope')
ROJ_intercepts = pandas.read_excel('Data/Price_Demand_Equations.xlsx', 'ROJ_Intercept')
FCOJ_slopes = pandas.read_excel('Data/Price_Demand_Equations.xlsx', 'FCOJ_Slope')
FCOJ_intercepts = pandas.read_excel('Data/Price_Demand_Equations.xlsx', 'FCOJ_Intercept')

ORA_past_points =pandas.read_excel('Data/Monthly_Price_Demand.xlsx', 'ORA')
POJ_past_points =pandas.read_excel('Data/Monthly_Price_Demand.xlsx', 'POJ')
ROJ_past_points =pandas.read_excel('Data/Monthly_Price_Demand.xlsx', 'ROJ')
FCOJ_past_points =pandas.read_excel('Data/Monthly_Price_Demand.xlsx', 'FCOJ')

# -------------------------------------------------------------------------- #




# format panda tables (set indices/columns)
# -------------------------------------------------------------------------- #

# US$ Prices of oranges at the Spot Market($/lb) ORA
grove_USprices = grove.iloc[16:22, 2:14]
grove_USprices.columns = months
grove_USprices.set_index([groves], inplace=True)

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
ORA_slopes.set_index([regions], inplace=True)
ORA_slopes.drop('Region:Month', inplace=True, axis=1)

ORA_intercepts.set_index([regions], inplace=True)
ORA_intercepts.drop('Region:Month', inplace=True, axis=1)

POJ_slopes.set_index([regions], inplace=True)
POJ_slopes.drop('Region:Month', inplace=True, axis=1)

POJ_intercepts.set_index([regions], inplace=True)
POJ_intercepts.drop('Region:Month', inplace=True, axis=1)

ROJ_slopes.set_index([regions], inplace=True)
ROJ_slopes.drop('Region:Month', inplace=True, axis=1)

ROJ_intercepts.set_index([regions], inplace=True)
ROJ_intercepts.drop('Region:Month', inplace=True, axis=1)

FCOJ_slopes.set_index([regions], inplace=True)
FCOJ_slopes.drop('Region:Month', inplace=True, axis=1)

FCOJ_intercepts.set_index([regions], inplace=True)
FCOJ_intercepts.drop('Region:Month', inplace=True, axis=1)

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




# decision matrices
# -------------------------------------------------------------------------- #

raw_materials = pandas.DataFrame(data = 0.0, index = groves, columns = months)
shipping1 = pandas.DataFrame(data = 0.0, index = groves, columns = (plants+storages))
shipping1P = shipping1.copy()
    
manufacturing_columns = []
for p in plants:
    manufacturing_columns = manufacturing_columns + [p+'_POJ'] + [p+'_FCOJ']
manufacturing = pandas.DataFrame(data = 0.0, index = ['Proportion'], columns = manufacturing_columns)
manufacturingP = manufacturing.copy()

shipping2_columns = ['Futures_FCOJ']
for p in plants:
    shipping2_columns = shipping2_columns + [p+'_POJ'] + [p+'_FCOJ']
shipping2 = pandas.DataFrame(data = 0.0, index = storages, columns = shipping2_columns)
shipping2P = shipping2.copy()

reconstitution = pandas.DataFrame(data = 0.0, index = storages, columns = months)
reconstitutionP = reconstitution.copy()

pricing_ORA = pandas.DataFrame(data = 0.0, index = regions, columns = months)
pricing_POJ = pandas.DataFrame(data = 0.0, index = regions, columns = months)
pricing_ROJ = pandas.DataFrame(data = 0.0, index = regions, columns = months)
pricing_FCOJ = pandas.DataFrame(data = 0.0, index = regions, columns = months)
    
decisions = [raw_materials, shipping1, manufacturing, shipping2, reconstitution, pricing_ORA, pricing_POJ, pricing_ROJ, pricing_FCOJ]

total_profit = 0.0


capacity = pandas.DataFrame(data = 0.0, index = (plants+storages), columns = months)

# -------------------------------------------------------------------------- #




# functions
# -------------------------------------------------------------------------- #

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
                
                update_raw_materials(quantity, m, grove)
                update_shipping1(quantity, p, grove, plant, storage)
                update_manufacturing(quantity, p, plant)
                update_shipping2(quantity, p, plant, storage)
                update_reconstitution(quantity, p, m, storage)
                update_pricing(price, p, r, m)
                update_total_profit(profit)
                
                update_capacity(quantity, p, m, plant, storage)
    
    calculate_shipping1P()
    calculate_manufacturingP()
    calculate_shipping2P()
    calculate_reconstitutionP()
              
# return optimal path, price, and quantity for a product/region/month
def get_optimal_parameters(product, region, month, slope, intercept):
    slope = slope / .0005 # lbs -> tons
    intercept = intercept / .0005 # lbs -> tons
    
    closest_storage = get_closest_storage(region)
    closest_plant = get_closest_plant(closest_storage)
    best_grove = get_best_grove(closest_storage, month)
    transportation_method = 'IC' # for now no tankers available
               
    path_cost = get_path_cost(product, region, month, best_grove, 
                              closest_plant, closest_storage, 
                              transportation_method)
    
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
    
    parameters = [product, region, month, best_grove, closest_plant, 
                  closest_storage, transportation_method, price, quantity, 
                  profit]
    
    return parameters

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
def get_closest_plant(closest_storage):
    min_dist = float('inf')
    for p in plants:
        d = P_S.loc[closest_storage, p]
        if (d < min_dist):
            min_dist = d
            closest_plant = p
    
    return closest_plant

# return best grove (cheapest oranges and closest to plant)
def get_best_grove(closest_plant, month):
    min_cost = float('inf')
    for g in groves:
        if( (g == 'BRA') | (g == 'SPA') ):
            d = G_P.loc[closest_plant, 'FLA']
        else:
            d = G_P.loc[closest_plant, g]

        d_cost = d * .22
        g_cost = get_grove_purchase_cost(g, month)
        total_cost = d_cost + g_cost       

        if (total_cost < min_cost):
            min_cost = total_cost
            best_grove = g
    
    #print('grove_purchase_cost = ' + str(g_cost))
            
    return best_grove
    
# return total cost from buying oranges to delivering product in region          
def get_path_cost(product, region, month, grove, plant, storage, transporter):
    grove_purchase_cost = get_grove_purchase_cost(grove, month)
    plant_cost = get_plant_cost(product)
    reconstitution_cost = get_reconstitution_cost(product)
    transportation_cost = get_transportation_cost(product, region, grove, plant, storage, transporter)
    
    total_cost = grove_purchase_cost + plant_cost + reconstitution_cost + transportation_cost  
    
    return total_cost

# return cost of purchasing oranges at grove during month
def get_grove_purchase_cost(grove, month):
    grove_purchase_cost = grove_USprices.loc[grove, month] / .0005 # lbs -> tons

    #print('grove_purchase_cost = ' + str(grove_purchase_cost))

    return grove_purchase_cost

# return cost of manufacturing POJ or ROJ
def get_plant_cost(product):
    if (product == 'POJ'):
        plant_cost = 2000
    elif ((product == 'ROJ') | (product == 'FCOJ')):
        plant_cost = 1000
    else:
        plant_cost = 0
        
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

# return cost of transporting from grove to market region
def get_transportation_cost(product, region, grove, plant,
                            storage, transportater):
    
    if ((grove == 'BRA') | (grove == 'SPA')):
        grove = 'FLA'
    
    cost_G_to_P = G_P.loc[plant, grove] * .22
    cost_P_to_S = P_S.loc[storage, plant] * .65
    cost_G_to_S = 0
    
    if (product == 'ORA'):
        cost_G_to_P = 0
        cost_P_to_S = 0
        cost_G_to_S = get_grove_to_storage_distance(grove, storage) * .22
            
    cost_S_to_M = S_M.loc[region, storage] * 1.2    
    
    total_transportation_cost = cost_G_to_P + cost_P_to_S + cost_G_to_S + cost_S_to_M
    
    #print('cost_G_to_P = ' + str(cost_G_to_P))
    #print('cost_P_to_S = ' + str(cost_P_to_S))
    #print('cost_G_to_S = ' + str(cost_G_to_S))
    #print('cost_S_to_M = ' + str(cost_S_to_M))
    #print ('inventory hold cost = ' + str(inv_hold_cost))
    #print('total_transportation_cost = ' + str(total_transportation_cost))
    
    return total_transportation_cost

# return miles distance from grove to storage
def get_grove_to_storage_distance(grove, storage):
    grove_lat = float(Terminals.loc[grove, 'Latitude'])
    grove_long = float(Terminals.loc[grove, 'Longtitude'])
    storage_lat = float(Terminals.loc[storage, 'Latitude'])
    storage_long = float(Terminals.loc[storage, 'Longtitude'])

    # get distance in meters between two points
    dist = geo.haversine_distance(grove_lat, grove_long, storage_lat, storage_long)
    
    # convert to miles and return
    return (dist*0.000621371*1.26)    
    
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
    
    
# add quantity to raw materials path
def update_raw_materials(quantity, month, grove):
    raw_materials.loc[grove, month] = raw_materials.loc[grove, month] + quantity

# add quantity to shipping1 path
def update_shipping1(quantity, product, grove, plant, storage):
    if (product == 'ORA'):
        shipping1.loc[grove, storage] = shipping1.loc[grove, storage] + quantity
    else:
        shipping1.loc[grove, plant] = shipping1.loc[grove, plant] + quantity

# add quantity to manufacturing path
def update_manufacturing(quantity, product, plant):
    if (product == 'POJ'):
        manufacturing.loc['Proportion', (plant+'_POJ')] = manufacturing.loc['Proportion', (plant+'_POJ')] + quantity
    elif ((product == 'ROJ') | (product == 'FCOJ')):
        manufacturing.loc['Proportion', (plant+'_FCOJ')] = manufacturing.loc['Proportion', (plant+'_FCOJ')] + quantity                      

# add quantity to shipping2 path
def update_shipping2(quantity, product, plant, storage):
    if (product == 'POJ'):
        shipping2.loc[storage, (plant+'_POJ')] = shipping2.loc[storage, (plant+'_POJ')] + quantity
    elif ((product == 'ROJ') | (product == 'FCOJ')):
        shipping2.loc[storage, (plant+'_FCOJ')] = shipping2.loc[storage, (plant+'_FCOJ')] + quantity                      

# add quantity to reconstitution path
def update_reconstitution(quantity, product, month, storage):
    if (product == 'ROJ'):
        reconstitution.loc[storage, month] = reconstitution.loc[storage, month] + quantity
        
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
    if (product != 'ORA'):
        capacity.loc[plant, month] = capacity.loc[plant, month] + quantity
        
    capacity.loc[storage, month] = capacity.loc[storage, month] + quantity

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
        total = 0.0
        for c in range(0, ncol):
            total = total + reconstitution.iloc[r, c]

        for c in range(0, ncol):
            if (total == 0):
                reconstitutionP.iloc[r, c] = 0.0
            else:
                reconstitutionP.iloc[r, c] = reconstitution.iloc[r, c] / total * 100

# -------------------------------------------------------------------------- #
    



# test code
# -------------------------------------------------------------------------- #

get_decisions()
print(total_profit)
print()

product = 'FCOJ'
region = 'NE'
month = 'Apr'

slope = FCOJ_slopes.loc[region, month]
intercept = FCOJ_intercepts.loc[region, month]

test_params = get_optimal_parameters(product, region, month, slope, intercept)
print(test_params)

# -------------------------------------------------------------------------- #




# summary + action items
# -------------------------------------------------------------------------- #
    
# action item 1:
    # FCOJ Futures path

# action item 2:
    # for every positive slope / negative profit,
    # try out points we know exist and pick best one
    
# action item 3:
    # if we maxed out quantity last time, buy more
    # except now that we have different prices this doesn't make sense?    

# action item 4:
    # add expected time for carrier (30% slower?)
        
# -------------------------------------------------------------------------- #







