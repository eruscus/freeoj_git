import pandas, random, numpy
from gpxpy import geo

# vectors
# -------------------------------------------------------------------------- #

regions = ['NE','MA','SE','MW','DS','NW','SW']
months = ['Sep','Oct','Nov','Dec','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug']
products = ['ORA','POJ','FCOJ','ROJ']
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
FCOJ_slopes = pandas.read_excel('Data/Price_Demand_Equations.xlsx', 'FCOJ_Slope')
FCOJ_intercepts = pandas.read_excel('Data/Price_Demand_Equations.xlsx', 'FCOJ_Intercept')
ROJ_slopes = pandas.read_excel('Data/Price_Demand_Equations.xlsx', 'ROJ_Slope')
ROJ_intercepts = pandas.read_excel('Data/Price_Demand_Equations.xlsx', 'ROJ_Intercept')

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

FCOJ_slopes.set_index([regions], inplace=True)
FCOJ_slopes.drop('Region:Month', inplace=True, axis=1)

FCOJ_intercepts.set_index([regions], inplace=True)
FCOJ_intercepts.drop('Region:Month', inplace=True, axis=1)

ROJ_slopes.set_index([regions], inplace=True)
ROJ_slopes.drop('Region:Month', inplace=True, axis=1)

ROJ_intercepts.set_index([regions], inplace=True)
ROJ_intercepts.drop('Region:Month', inplace=True, axis=1)

# -------------------------------------------------------------------------- #




# functions
# -------------------------------------------------------------------------- #

def get_decisions():
    raw_materials = pandas.DataFrame(data = 0.0, index = groves, columns = months)
    shipping1 = pandas.DataFrame(data = 0.0, index = groves, columns = (plants+storages) )
    
    manufacturing_columns = []
    for p in plants:
        manufacturing_columns = manufacturing_columns + [p+'_POJ'] + [p+'_FCOJ']
    manufacturing = pandas.DataFrame(data = 0.0, index = ['Proportion'], columns = manufacturing_columns)
    
    shipping2_columns = ['Futures_FCOJ']
    for p in plants:
        shipping2_columns = shipping2_columns + [p+'_POJ'] + [p+'_FCOJ']
    shipping2 = pandas.DataFrame(data = 0.0, index = storages, columns = shipping2_columns)
    
    reconstitution = pandas.DataFrame(data = 0.0, index = storages, columns = months)
    
    pricing_ORA = pandas.DataFrame(data = 0.0, index = regions, columns = months)
    pricing_POJ = pandas.DataFrame(data = 0.0, index = regions, columns = months)
    pricing_FCOJ = pandas.DataFrame(data = 0.0, index = regions, columns = months)
    pricing_ROJ = pandas.DataFrame(data = 0.0, index = regions, columns = months)
     
    params_ORA = get_params_df('ORA', ORA_slopes, ORA_intercepts) 
    params_POJ = get_params_df('POJ', POJ_slopes, POJ_intercepts) 
    params_FCOJ = get_params_df('FCOJ', FCOJ_slopes, FCOJ_intercepts)  
    params_ROJ = get_params_df('ROJ', ROJ_slopes, ROJ_intercepts)  
    
    all_params = pandas.concat([params_ORA, params_POJ, params_FCOJ, params_ROJ], axis=0)
    
    # get a list of total quantity in each storage center
    storages_grouped_sums = all_params.groupby(['optimal_storage', 'month'])['optimal_quantity'].sum()
    capacity_test = (storages_grouped_sums<50000).all() # if this is true then don't need to worry about capacity
    
    if (capacity_test == False):
        storages_over_capacity = storages_grouped_sums.index[storages_grouped_sums>50000].tolist()
        for s_over in storages_over_capacity:
            params_temp = all_params[all_params.optimal_storage==s_over].sort_values(by='max_profit', ascending=False)
            all_params = all_params[all_params.optimal_storage!=s_over]
            temp_cumsum = params_temp.optimal_quantity.cumsum()
            end_index = sum(temp_cumsum < 50000)
            params_temp = params_temp.iloc[0:end_index,:]
            all_params = all_params.append(params_temp)
            
     ## DIDN'T FINISH CHANGING THIS PART
     
 ##################################################   

    grove_quantities_grouped = all_params.groupby(['optimal_grove', 'month'])['optimal_quantity'].sum()
     
    for g in all_params.optimal_grove.unique().tolist():
        raw_materials.loc[g,:] = grove_quantities_grouped[g]

    for i in range(len(all_params)):
        par = all_params.iloc[i,:]
        
        if (par['product'] == 'ORA'):    
            shipping1.loc[par.optimal_grove, par.optimal_storage] = shipping1.loc[par.optimal_grove, par.optimal_storage] + par.optimal_quantity
        else:
            shipping1.loc[par.optimal_grove, par.optimal_processing] = shipping1.loc[par.optimal_grove, par.optimal_processing] + par.optimal_quantity

        if (par['product'] == 'POJ'):
            manufacturing.loc['Proportion',(par.optimal_processing+'_POJ')] = manufacturing.loc['Proportion',(par.optimal_processing+'_POJ')] + par.optimal_quantity
        elif (par['product'] == 'FCOJ'):
            manufacturing.loc['Proportion',(par.optimal_processing+'_FCOJ')] = manufacturing.loc['Proportion',(par.optimal_processing+'_FCOJ')] + par.optimal_quantity                      


        if (par['product'] == 'POJ'):
            shipping2.loc[par.optimal_storage,(par.optimal_processing+'_POJ')] = shipping2.loc[par.optimal_storage,(par.optimal_processing+'_POJ')] + par.optimal_quantity
        elif (par['product'] == 'FCOJ'):
            shipping2.loc[par.optimal_storage,(par.optimal_processing+'_FCOJ')] = shipping2.loc[par.optimal_storage,(par.optimal_processing+'_FCOJ')] + par.optimal_quantity                      
           

        if (par['product'] == 'ROJ'):
            m = par['month']
            reconstitution.loc[par.optimal_storage,m] = reconstitution.loc[par.optimal_storage,m] + par.optimal_quantity

        if par['product'] == 'ORA':
            pricing_ORA.loc[par['region'],par['month']] = par.optimal_price
        elif par['product'] == 'POJ':
            pricing_POJ.loc[par['region'],par['month']] = par.optimal_price
        elif par['product'] == 'ROJ':
            pricing_ROJ.loc[par['region'],par['month']] = par.optimal_price
        else:
            pricing_FCOJ.loc[par['region'],par['month']] = par.optimal_price
   
##################################################

    print(all_params.max_profit.sum())

    return [raw_materials, shipping1, manufacturing, shipping2, reconstitution, pricing_ORA, pricing_POJ, pricing_ROJ, pricing_FCOJ]

#### helper functions for final decisions ####

def count_shipping1(ps): 
    if (ps['product'] == 'ORA'):    
        shipping1.loc[ps.optimal_grove, ps.optimal_storage] = shipping1.loc[ps.optimal_grove, ps.optimal_storage] + ps.optimal_quantity
    else:
        shipping1.loc[ps.optimal_grove, ps.optimal_processing] = shipping1.loc[ps.optimal_grove, ps.optimal_processing] + ps.optimal_quantity

def count_manufacturing(ps):
    if (ps['product'] == 'POJ'):
        manufacturing.loc['Proportion',(ps.optimal_processing+'_POJ')] = manufacturing.loc['Proportion',(ps.optimal_processing+'_POJ')] + ps.optimal_quantity
    elif (ps['product'] == 'FCOJ'):
        manufacturing.loc['Proportion',(ps.optimal_processing+'_FCOJ')] = manufacturing.loc['Proportion',(ps.optimal_processing+'_FCOJ')] + ps.optimal_quantity                      

def count_shipping2(ps):
    if (ps['product'] == 'POJ'):
        shipping2.loc[ps.optimal_storage,(ps.optimal_processing+'_POJ')] = shipping2.loc[ps.optimal_storage,(ps.optimal_processing+'_POJ')] + ps.optimal_quantity
    elif (ps['product'] == 'FCOJ'):
        shipping2.loc[ps.optimal_storage,(ps.optimal_processing+'_FCOJ')] = shipping2.loc[ps.optimal_storage,(ps.optimal_processing+'_FCOJ')] + ps.optimal_quantity                      
           
def count_reconstitution(ps):
    if (ps['product'] == 'ROJ'):
        m = ps['month']
        reconstitution.loc[ps.optimal_storage,m] = reconstitution.loc[ps.optimal_storage,m] + ps.optimal_quantity

def product_pricing(ps):
    if ps['product'] == 'ORA':
        pricing_ORA.loc[ps['region'],ps['month']] = ps.optimal_price
    elif ps['product'] == 'POJ':
        pricing_POJ.loc[ps['region'],ps['month']] = ps.optimal_price
    elif ps['product'] == 'ROJ':
        pricing_ROJ.loc[ps['region'],ps['month']] = ps.optimal_price
    else:
        pricing_FCOJ.loc[ps['region'],ps['month']] = ps.optimal_price


def get_params_df(product, slopes_df, intercepts_df):
     
    params_columns = ['product', 'month','region','optimal_price', 'optimal_quantity', 'optimal_grove', 
                  'optimal_processing', 'optimal_storage', 'optimal_transportation',
                  'max_profit', 'path_cost']
                  
    parameters_by_profit = pandas.DataFrame(columns = params_columns)
    
    for r in regions:
        for m in months:
            slope = ORA_slopes.loc[r,m]
            intercept = ORA_intercepts.loc[r,m]
            parameters = get_optimal_parameters(product, r, m, slope, intercept)
            
            parameters = pandas.DataFrame(parameters).transpose()
            parameters.columns = params_columns
            parameters_by_profit = parameters_by_profit.append(parameters)
            
    return parameters_by_profit        

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
    
    profit = quantity * (price - path_cost)
            
    if (profit < 0.0):
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
    elif ((product == 'FCOJ') | (product == 'ROJ')):
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
    
    if (product == 'ORA'):
        cost_G_to_S = get_grove_to_storage_distance(grove, storage) * .22
        cost_G_to_P = 0
        cost_P_to_S = 0
            
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
    
# -------------------------------------------------------------------------- #
    



# test code
# -------------------------------------------------------------------------- #

product = 'ORA'
region = 'NE'
month = 'Sep'

slope = ORA_slopes.loc[region, month]
intercept = ORA_intercepts.loc[region, month]

closest_storage = get_closest_storage(region)
closest_plant = get_closest_plant(closest_storage)
best_grove = get_best_grove(closest_storage, month)
transportation_method = 'IC' # for now no tankers available
               
path_cost = get_path_cost(product, region, month, best_grove, closest_plant, closest_storage, "IC")
        
optimal_parameters = get_optimal_parameters(product, region, month, slope, intercept)

print(slope)
print(intercept)

print(path_cost)

# -------------------------------------------------------------------------- #




# summary + action items
# -------------------------------------------------------------------------- #

# summary:
    
    
# action item 1:
    
        
# -------------------------------------------------------------------------- #







