import pandas, random, numpy, math
from gpxpy import geo

# vectors
# -------------------------------------------------------------------------- #

regions = ['NE','MA','SE','MW','DS','NW','SW']
months = ['Sep','Oct','Nov','Dec','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug']
products = ['ORA','POJ','ROJ','FCOJ']
groves = ['FLA','CAL','TEX','ARZ','BRA','SPA']
plants = ['P07']
storages = ['S14','S61']
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

# -------------------------------------------------------------------------- #




# decision matrices
# -------------------------------------------------------------------------- #

raw_materials = pandas.DataFrame(data = 0.0, index = groves, columns = months)
shipping1 = pandas.DataFrame(data = 0.0, index = groves, columns = (plants+storages) )
shipping1P = shipping1
    
manufacturing_columns = []
for p in plants:
    manufacturing_columns = manufacturing_columns + [p+'_POJ'] + [p+'_FCOJ']
manufacturing = pandas.DataFrame(data = 0.0, index = ['Proportion'], columns = manufacturing_columns)
manufacturingP = manufacturing
    
shipping2_columns = ['Futures_FCOJ']
for p in plants:
    shipping2_columns = shipping2_columns + [p+'_POJ'] + [p+'_FCOJ']
shipping2 = pandas.DataFrame(data = 0.0, index = storages, columns = shipping2_columns)
shipping2P = shipping2

reconstitution = pandas.DataFrame(data = 0.0, index = storages, columns = months)
reconstitutionP = reconstitution

pricing_ORA = pandas.DataFrame(data = 0.0, index = regions, columns = months)
pricing_POJ = pandas.DataFrame(data = 0.0, index = regions, columns = months)
pricing_ROJ = pandas.DataFrame(data = 0.0, index = regions, columns = months)
pricing_FCOJ = pandas.DataFrame(data = 0.0, index = regions, columns = months)
    
decisions = [raw_materials, shipping1, manufacturing, shipping2, reconstitution, pricing_ORA, pricing_POJ, pricing_ROJ, pricing_FCOJ]
decisionsP = [raw_materials, shipping1P, manufacturingP, shipping2P, reconstitutionP, pricing_ORA, pricing_POJ, pricing_ROJ, pricing_FCOJ]

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
                
                update_raw_materials(quantity, grove, m)
                
    
                # shipping1
                if (p == 'ORA'):
                    shipping1.loc[grove, storage] = shipping1.loc[grove, storage] + quantity
                else:
                    shipping1.loc[grove, plant] = shipping1.loc[grove, plant] + quantity
                
                # manufacturing
                if (p == 'POJ'):
                    manufacturing.loc['Proportion', (plant+'_POJ')] = manufacturing.loc['Proportion', (plant+'_POJ')] + quantity
                elif ((p == 'ROJ') | (p == 'FCOJ')):
                    manufacturing.loc['Proportion', (plant+'_FCOJ')] = manufacturing.loc['Proportion', (plant+'_FCOJ')] + quantity                      
                
                # shipping2
                if (p == 'POJ'):
                    shipping2.loc[storage, (plant+'_POJ')] = shipping2.loc[storage, (plant+'_POJ')] + quantity
                elif ((p == 'ROJ') | (p == 'FCOJ')):
                    shipping2.loc[storage, (plant+'_FCOJ')] = shipping2.loc[storage, (plant+'_FCOJ')] + quantity                      
                
                # reconstitution
                if (p == 'ROJ'):
                    reconstitution.loc[storage, m] = reconstitution.loc[storage, m] + quantity
                    
                # pricing
                if (p == 'ORA'):
                    pricing_ORA.loc[r,m] = price
                if (p == 'POJ'):
                    pricing_POJ.loc[r,m] = price
                if (p == 'ROJ'):
                    pricing_ROJ.loc[r,m] = price
                if (p == 'FCOJ'):
                    pricing_FCOJ.loc[r,m] = price
                    
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

def update_raw_materials(quantity, grove, month):
    raw_materials.loc[grove, month] = raw_materials.loc[grove, m] + quantity
# -------------------------------------------------------------------------- #
    



# test code
# -------------------------------------------------------------------------- #

#product = 'ORA'
#region = 'NE'
#month = 'Sep'
#
#slope = ORA_slopes.loc[region, month]
#intercept = ORA_intercepts.loc[region, month]
#
#closest_storage = get_closest_storage(region)
#closest_plant = get_closest_plant(closest_storage)
#best_grove = get_best_grove(closest_storage, month)
#transportation_method = 'IC' # for now no tankers available
#               
#path_cost = get_path_cost(product, region, month, best_grove, closest_plant, closest_storage, "IC")
#        
#optimal_parameters = get_optimal_parameters(product, region, month, slope, intercept)
#
#print(slope)
#print(intercept)
#
#print(path_cost)

get_decisions()

# -------------------------------------------------------------------------- #




# summary + action items
# -------------------------------------------------------------------------- #

# summary:
    
    
# action item 1:
    
        
# -------------------------------------------------------------------------- #







