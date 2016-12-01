import pandas, random, numpy
from gpxpy import geo

# vectors
# -------------------------------------------------------------------------- #

regions = ['NE','MA','SE','MW','DS','NW','SW']
months = ['Sep','Oct','Nov','Dec','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug']
products = ['ORA','POJ','FCOJ','ROJ']
groves = ['FLA','CAL','TEX','ARZ','BRA','SPA']
processing_centers = ['P07']
storage_locations = ['S14','S61']
transportation_methods = ['T', 'IC']

# -------------------------------------------------------------------------- #




# read excel spreasheets using pandas
# -------------------------------------------------------------------------- #

G_P = pandas.read_excel('Data/StaticData.xlsx', 'G->PS')
P_S = pandas.read_excel('Data/StaticData.xlsx', 'P->S')
S_M = pandas.read_excel('Data/StaticData.xlsx', 'S->M (avg)')
terminals = pandas.read_excel('Data/StaticData.xlsx', 'Terminals')

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




# pull specific tables into pandas and set indices/columns
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

# Equations
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
    shipping1 = pandas.DataFrame(data = 0.0, index = groves, columns = (processing_centers+storage_locations) )
    
    manufacturing_columns = []
    for p in processing_centers:
        manufacturing_columns = manufacturing_columns + [p+'_POJ'] + [p+'_FCOJ']
    manufacturing = pandas.DataFrame(data = 0.0, index = ['Proportion'], columns = manufacturing_columns)
    
    shipping2_columns = ['Futures_FCOJ']
    for p in processing_centers:
        shipping2_columns = shipping2_columns + [p+'_POJ'] + [p+'_FCOJ']
    shipping2 = pandas.DataFrame(data = 0.0, index = storage_locations, columns = shipping2_columns)
    
    reconstitution = pandas.DataFrame(data = 0.0, index = storage_locations, columns = months)
    
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


def get_optimal_parameters(product, region, month, slope, y_intercept):
    # SET CATCH SO PRICE <= 4
    
    N = 100
    max_profit = float('-inf')
    for i in range(1,N+1):
        price = 0 + i * y_intercept/N
        quantity = (price - y_intercept)/slope
        
        if (slope > 0):
            price = y_intercept
            quantity = i*60

        if (price > 4.0):
            price = 4.0
        if (quantity < 0.0):
            quantity = 0.0

        closest_storage = get_closest_storage(region)
        closest_processing = get_closest_processing(closest_storage)
        closest_grove = get_best_grove(closest_storage, month)
        transportation_method = 'IC' # for now no tankers available
        
        time_of_transport = time_to_market(product, 'IC', closest_storage,
                                           closest_processing, False)
        
        if (time_of_transport >= 4.0):
            if (month != 'Aug'):
                month_index = months.index(month) + 1
            else:
                month_index = 0
            month = months[month_index]
               
        path_cost = get_path_cost(product, region, month, closest_grove, closest_processing, closest_storage, transportation_method)
        cost = quantity * path_cost
        revenue = quantity * price / .0005 # lbs to tons
        profit = revenue - cost

        if (profit > max_profit):
            max_profit = profit
            optimal_price = price
            optimal_quantity = quantity
            optimal_grove = closest_grove
            optimal_processing = closest_processing
            optimal_storage = closest_storage
            optimal_transportation = transportation_method
            
    if (max_profit < 0.0):
        optimal_price = 0.0
        optimal_quantity = 0.0
    
    parameters = [product, month, region, optimal_price, optimal_quantity, optimal_grove, 
                  optimal_processing, optimal_storage, optimal_transportation,
                  max_profit, path_cost]
    
    return parameters
    
def get_closest_storage(region):
    min_dist = float('inf')
    for s in storage_locations:
        d = S_M.loc[region, s]
        if (d < min_dist):
            min_dist = d
            min_storage = s
    
    return min_storage
    
def get_closest_processing(closest_storage):
    min_dist = float('inf')
    for p in processing_centers:
        d = P_S.loc[closest_storage, p]
        if (d < min_dist):
            min_dist = d
            min_processing = p
    
    return min_processing
    
def get_best_grove(closest_processing, month):
    min_cost = float('inf')
    for g in groves:
        if( (g == 'BRA') | (g == 'SPA') ):
            d = G_P.loc[closest_processing, 'FLA']
        else:
            d = G_P.loc[closest_processing, g]

        d_cost = d * .22
        
        g_cost = get_grove_purchase_cost(g, month)

        total_cost = d_cost + g_cost       

        if (total_cost < min_cost):
            min_cost = total_cost
            min_grove = g
    
    #print('grove_purchase_cost = ' + str(g_cost))
            
    return min_grove
            
def get_path_cost(product, region, month, grove, processing_center, storage_location, transportation_method):
    grove_purchase_cost = get_grove_purchase_cost(grove, month)
    processing_cost = get_processing_cost(product)
    reconstitution_cost = get_reconstitution_cost(product)
    transportation_cost = get_transportation_cost(product, region, grove, processing_center, storage_location, transportation_method)
    
    total_cost = grove_purchase_cost + processing_cost + reconstitution_cost + transportation_cost    
    return total_cost
    
def get_grove_purchase_cost(grove, month):
    grove_purchase_cost = grove_USprices.loc[grove,month] / .0005

    #print('grove_purchase_cost = ' + str(grove_purchase_cost))

    return grove_purchase_cost
    
def get_processing_cost(product):
    if (product == 'POJ'):
        processing_cost = 2000
    elif ((product == 'FCOJ') | (product == 'ROJ')):
        processing_cost = 1000
    else:
        processing_cost = 0
        
    #print('processing_cost = ' + str(processing_cost))
    
    return processing_cost

def get_reconstitution_cost(product):
    if (product == 'ROJ'):
        reconstitution_cost = 650
    else:
        reconstitution_cost = 0
        
    #print('reconstitution_cost = ' + str(reconstitution_cost))
        
    return reconstitution_cost

def get_transportation_cost(product, region, grove, processing_center,
                            storage_location, transportation_method):
    
    if ((grove == 'BRA') | (grove == 'SPA')):
        grove = 'FLA'
    
    if (transportation_method == 'IC'):
        
        cost_G_to_P = G_P.loc[processing_center, grove] * .22
        cost_P_to_S = P_S.loc[storage_location, processing_center] * .65
    
        if (product == 'ORA'):
            cost_P_to_S = grove_to_storage_distance(grove, storage_location) * .22
            cost_G_to_P = 0
        cost_S_to_M = S_M.loc[region, storage_location] * 1.2
    
        # inventory hold cost at storage = 60 per ton per week
        inv_hold_cost = 60
    
    
    total_transportation_cost = cost_G_to_P + cost_P_to_S + cost_S_to_M + inv_hold_cost
    
    #print('cost_G_to_P = ' + str(cost_G_to_P))
    #print('cost_P_to_S = ' + str(cost_P_to_S))
    #print('cost_S_to_M = ' + str(cost_S_to_M))
    #print ('inventory hold cost = ' + str(inv_hold_cost))
    #print('total_transportation_cost = ' + str(total_transportation_cost))
    
    return total_transportation_cost
    
def time_to_market(product, transportation_type, storage_location, processing_center, is_rand):
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
        if (is_rand==0):
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
    
# add here later: given 48 demand curves, determine optimal allocation of
# products around them given transportation costs and time to market

def grove_to_storage_distance(grove, storage):
    
    locations = terminals['Location']
    
    grove_row = terminals[locations==grove]
    storage_row = terminals[locations==storage]

    grove_lat = float(grove_row['Latitude'])
    grove_long = float(grove_row['Longtitude'])
    storage_lat = float(storage_row['Latitude'])
    storage_long = float(storage_row['Longtitude'])

    # get distance in meters between two points
    dist = geo.haversine_distance(grove_lat, grove_long, storage_lat, storage_long)
    
    # convert to miles and return
    return (dist*0.000621371*1.26)    
    
# -------------------------------------------------------------------------- #
    



# test code
# -------------------------------------------------------------------------- #

# test path cost
#test_path_cost = get_path_cost('ROJ', 'NE', 'Sep', 'CAL', 'P07', 'S61', 'IC')
#print( test_path_cost )


# test time to market
#test_rand_time_to_market = time_to_market('POJ','IC', 'S61', 'P07', 1)
#print ('estimate of time to market, random: ' + str(test_rand_time_to_market))

#test_rand_time_to_market = time_to_market('POJ','IC', 'S61', 'P07', 1)
#print ('estimate of time to market, random: ' + str(test_rand_time_to_market))

#test_exp_time_to_market = time_to_market('POJ','IC', 'S61', 'P07', 0)
#print ('expected time to market: '+ str(test_exp_time_to_market))


# test profit
#optimal_parameters = get_optimal_parameters('ORA', 'NE', 'Sep', -.1, 4)
#print( optimal_parameters)


#decisions = get_decisions()

product = 'ROJ'
region = 'NE'
month = 'Sep'

slope = ROJ_slopes.loc[region, month]
intercept = ROJ_intercepts.loc[region, month]

test_params = get_optimal_parameters(product, region, month, slope, intercept)

print(test_params)

# -------------------------------------------------------------------------- #




# summary + action items
# -------------------------------------------------------------------------- #

# added function get_optimal_parameters to figure out optimal price and demand,
# as well as grove, processing, and storage location

# action item 1: create this function
# def my_new_function(stuff):
#    for every region and month:
#        for every product:
#            get_optimal_parameters(stuff)
#            tally total number of oranges bought
#            tally how many go to each processing center
#            tally how many go to each storage location
#            tally how many converted to POJ/FCOJ (which is just the total POJ/FCOJ made i believe)
#    
#    divide tally by total to figure out which percent goes where

#action item 2: test functions and think about special cases not covered
        
# -------------------------------------------------------------------------- #



# new thoughts
# -------------------------------------------------------------------------- #

# so for every product month and region, we have a price/demand curve
# how many should we try to supply to each region to maximize profit
# profit = price*quantity - cost*quantity
# ***NOTE regions only buy from CLOSEST storage

# probably want to read in price/demand curve slope/intercept as vector somehow

# -------------------------------------------------------------------------- #




