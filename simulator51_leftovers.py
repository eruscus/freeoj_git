import pandas, numpy, math, time

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

max_capacities = [1748, 7684, 13204, 5458]
NUM_WEEKS = 48

NUM_ORA_FUTURES = 9279
ORA_futures_used = 0

NUM_FCOJ_FUTURES = 12368 + 37632
FCOJ_futures_used = 0

1720.695459 - 352
120.6702479 - 120.6702479
2749.470483 - 281.8770765
325.4944302 - 160.8770765

# -------------------------------------------------------------------------- #




# Read In Excel Spreasheets Using Pandas
# -------------------------------------------------------------------------- #

path_indices = numpy.arange(len(products) * len(all_markets) * len(weeks))
paths_SPOT_ORA = pandas.read_excel('Data/paths_SPOT_ORA.xlsx')
paths_FUT_ORA = pandas.read_excel('Data/paths_FUT_ORA.xlsx')
paths_FUT_FCOJ = pandas.read_excel('Data/paths_FUT_FCOJ.xlsx')

ORA_equations = pandas.read_csv('Data/ORA_equations.csv')
POJ_equations = pandas.read_csv('Data/POJ_equations.csv')
ROJ_equations = pandas.read_csv('Data/ROJ_equations.csv')
FCOJ_equations = pandas.read_csv('Data/FCOJ_equations.csv')

ORA_past_points = pandas.read_excel('Data/Monthly_Price_Demand2018.xlsx', 'ORA')
POJ_past_points = pandas.read_excel('Data/Monthly_Price_Demand2018.xlsx', 'POJ')
ROJ_past_points = pandas.read_excel('Data/Monthly_Price_Demand2018.xlsx', 'ROJ')
FCOJ_past_points = pandas.read_excel('Data/Monthly_Price_Demand2018.xlsx', 'FCOJ')

# -------------------------------------------------------------------------- #




# Format Panda Tables (set dimensions/indices/columns)
# -------------------------------------------------------------------------- #

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




# Create Final Decision Tables
# -------------------------------------------------------------------------- #

# track how full each plant/storage is in each month
capacity = pandas.DataFrame(data = 0.0, index = (plants+storages), columns = months)
max_capacities = pandas.DataFrame(data = max_capacities, index = (plants+storages), columns = ['Max_Capacity'])

# Purchases at the Spot Market(tons per week in a month) (ORA)
spot_purchases = pandas.DataFrame(data = 0.0, index = groves, columns = months)

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
count_ROJ = pandas.DataFrame(data = 0.0, index = storages, columns = months)
count_FCOJ = pandas.DataFrame(data = 0.0, index = storages, columns = months)
reconstitutionP = pandas.DataFrame(data = 0.0, index = storages, columns = months)

# Pricing for each product in each region($/lb)
pricing_ORA = pandas.DataFrame(data = 0.0, index = regions, columns = months)
pricing_POJ = pandas.DataFrame(data = 0.0, index = regions, columns = months)
pricing_ROJ = pandas.DataFrame(data = 0.0, index = regions, columns = months)
pricing_FCOJ = pandas.DataFrame(data = 0.0, index = regions, columns = months)

# Quantity for each product in each region(tons)
quantity_ORA = pandas.DataFrame(data = 0.0, index = regions, columns = months)
quantity_POJ = pandas.DataFrame(data = 0.0, index = regions, columns = months)
quantity_ROJ = pandas.DataFrame(data = 0.0, index = regions, columns = months)
quantity_FCOJ = pandas.DataFrame(data = 0.0, index = regions, columns = months)

# Source for each product
source_ORA = pandas.DataFrame(data = 0.0, index = regions, columns = months)
source_POJ = pandas.DataFrame(data = 0.0, index = regions, columns = months)
source_ROJ = pandas.DataFrame(data = 0.0, index = regions, columns = months)
source_FCOJ = pandas.DataFrame(data = 0.0, index = regions, columns = months)

# Total Profit
total_profit = 0.0

# -------------------------------------------------------------------------- #




# Optimizing Functions
# -------------------------------------------------------------------------- #
def get_decisions():
    # get price, quantity, profit, and year_used for every market path
    apply_demand_curves(paths_SPOT_ORA)
    apply_demand_curves(paths_FUT_ORA)
    apply_demand_curves(paths_FUT_FCOJ)
    
    # allocate futures first and then do spot paths
    allocate_resources('FUT_FCOJ')
    allocate_resources('FUT_ORA')
    allocate_resources('SPOT_ORA')

    calculate_decision_percentages() 
    
# iterate through list of choices sorted by profit, update decisions if choice doesn't overfill capacity
def allocate_resources(contract):
    end = len(products) * len(all_markets) * len(weeks)
    for i in range(0, end):
        if (contract == 'SPOT_ORA'):
            parameters = paths_SPOT_ORA.iloc[i:i+1, 0:19]
        if (contract == 'FUT_ORA'):
            parameters = paths_FUT_ORA.iloc[i:i+1, 0:19]
        if (contract == 'FUT_FCOJ'):
            parameters = paths_FUT_FCOJ.iloc[i:i+1, 0:19]
            
        # have to divide a weeks quantity by 4 because want average weekly quantity for month when added
        parameters.loc[i, 'Quantity'] = parameters.loc[i, 'Quantity'] / 4.0
        parameters.loc[i, 'Profit'] = parameters.loc[i, 'Profit'] / 4.0
        
        product = parameters.loc[i, 'Product']
        region = parameters.loc[i, 'Region']
        demand_week = parameters.loc[i, 'Demand_Week']
        plant_week = parameters.loc[i, 'Plant_Week']
        storage_week = parameters.loc[i, 'Storage_Week']
        plant = parameters.loc[i, 'Plant']
        storage = parameters.loc[i, 'Storage']
        price = parameters.loc[i, 'Price']
        path_cost = parameters.loc[i, 'Path_Cost']
        quantity = parameters.loc[i, 'Quantity']
        
        # if end of FCOJ paths, break
        if (math.isnan(demand_week) == True): break
        demand_month = months[int(math.floor(demand_week / 4.0))]
        
        # check if used all ORA futures
        global ORA_futures_used
        if (contract == 'FUT_ORA'):
            if (ORA_futures_used + quantity*4 > NUM_ORA_FUTURES):
                quantity = (NUM_ORA_FUTURES - ORA_futures_used) / 4
                profit = quantity*(price*2000 - path_cost)
                
                parameters.loc[i, 'Quantity'] = quantity
                parameters.loc[i, 'Profit'] = profit
        
        # check if used all FCOJ futures
        global FCOJ_futures_used
        if (contract == 'FUT_FCOJ'):
            if (FCOJ_futures_used + quantity*4 > NUM_FCOJ_FUTURES):
                quantity = (NUM_FCOJ_FUTURES - FCOJ_futures_used) / 4
                profit = quantity*(price*2000 - path_cost)
                
                parameters.loc[i, 'Quantity'] = quantity
                parameters.loc[i, 'Profit'] = profit
        
        # check if plant over capacity
        if (plant in plants):
            plant_month = months[int(math.floor(plant_week / 4.0))]
            if (capacity.loc[plant, plant_month] + quantity > max_capacities.loc[plant, 'Max_Capacity']):
                quantity = max_capacities.loc[plant, 'Max_Capacity'] - capacity.loc[plant, plant_month]
                profit = quantity*(price*2000 - path_cost)
                
                parameters.loc[i, 'Quantity'] = quantity
                parameters.loc[i, 'Profit'] = profit
        
        # check if storage over capacity
        storage_month = months[int(math.floor(storage_week / 4.0))]
        if (capacity.loc[storage, storage_month] + quantity > max_capacities.loc[storage, 'Max_Capacity']):
            quantity = max_capacities.loc[storage, 'Max_Capacity'] - capacity.loc[storage, storage_month]
            profit = quantity*(price*2000 - path_cost)
            
            parameters.loc[i, 'Quantity'] = quantity
            parameters.loc[i, 'Profit'] = profit
        
        # check to make sure don't satisfy demand twice with both FUT and SPOT    
        if (product == 'ORA'):
            if (source_ORA.loc[region, demand_month] == 0):
                pass
            elif ((source_ORA.loc[region, demand_month] == 'FUT_FCOJ') & (contract != 'FUT_FCOJ')):
                quantity = 0
            elif ((source_ORA.loc[region, demand_month] == 'FUT_ORA') & (contract != 'FUT_ORA')):
                quantity = 0
        if (product == 'POJ'):
            if (source_POJ.loc[region, demand_month] == 0):
                pass
            elif ((source_POJ.loc[region, demand_month] == 'FUT_FCOJ') & (contract != 'FUT_FCOJ')):
                quantity = 0
            elif ((source_POJ.loc[region, demand_month] == 'FUT_ORA') & (contract != 'FUT_ORA')):
                quantity = 0
        if (product == 'ROJ'):
            if (source_ROJ.loc[region, demand_month] == 0):
                pass
            elif ((source_ROJ.loc[region, demand_month] == 'FUT_FCOJ') & (contract != 'FUT_FCOJ')):
                quantity = 0
            elif ((source_ROJ.loc[region, demand_month] == 'FUT_ORA') & (contract != 'FUT_ORA')):
                quantity = 0
        if (product == 'FCOJ'):
            if (source_FCOJ.loc[region, demand_month] == 0):
                pass
            elif ((source_FCOJ.loc[region, demand_month] == 'FUT_FCOJ') & (contract != 'FUT_FCOJ')):
                quantity = 0
            elif ((source_FCOJ.loc[region, demand_month] == 'FUT_ORA') & (contract != 'FUT_ORA')):
                quantity = 0
        
        # update decisions
        if (quantity != 0):
            update_decisions(parameters, i)
            #update_annual_report(parameters, i)
            if (contract == 'FUT_ORA'):
                ORA_futures_used = ORA_futures_used + quantity*4
            if (contract == 'FUT_FCOJ'):
                FCOJ_futures_used = FCOJ_futures_used + quantity*4

    calculate_decision_percentages()           

# get list of optimal parameters for every product/region/month and sort by profit
def apply_demand_curves(table):
    end = len(products) * len(all_markets) * len(weeks)
    for i in range(0, end):
        product = table.loc[i, 'Product']
        if (product in products):
            region = table.loc[i, 'Region']
            demand_week = table.loc[i, 'Demand_Week']
            path_cost = table.loc[i, 'Path_Cost']
            avg_cost = table.loc[i, 'Avg_Cost']
            
            demand_month = months[int(math.floor(demand_week / 4.0))] # convert from week to month
            
            slope = get_slope(product, region, demand_month)
            intercept = get_intercept(product, region, demand_month)
            
            parameters = get_optimal_parameters(product, region, demand_month, path_cost, avg_cost, slope, intercept)
            table.loc[i, 'Price'] = parameters[0]
            table.loc[i, 'Quantity'] = parameters[1]
            table.loc[i, 'Profit'] = parameters[2]
            table.loc[i, 'Year_Used'] = parameters[3]
                    
    # sort list of paths
    table.sort_values('Profit', ascending = False, inplace = True)
    table.set_index(path_indices, inplace=True)
                    
# return optimal path, price, and quantity for a product/region/month
def get_optimal_parameters(product, region, demand_month, path_cost, avg_cost, slope, intercept):
    slope = slope * 2000 # ($/lb) / (tons/week) -> ($/tons) / (tons/week)
    intercept = intercept * 2000 # $/lb -> $/ton                        
        
    # solve derivative of quadratic for quantity/price
    quantity = (avg_cost - intercept) / (2 * slope)
    price = slope*quantity + intercept
    profit = quantity * (price - path_cost)    
    
    # game's max price is 4, so downgrade price/quantity if needed
    if (price > 4.0*2000):
        price = 4.0*2000
        quantity = (price - intercept) / slope    
        profit = quantity * (price - path_cost)
    
    # if any negative values, don't try to provide demand there        
    if ((price < 0.0) | (quantity < 0.0) | (profit < 0.0) | math.isnan(slope) | math.isnan(intercept)):
        price = 4.0*2000     #maximum price
        quantity = 0.0
        profit = 0.0
    
    # check all past points to see if anything has higher profit than the best point on the line
    past_points = get_past_points(product)
    price_index = region + ':Price'
    quantity_index = region + ':Demand'
    
    # remember which year of data was used
    year_used = 2018
    for i in range(1,16):
        col = demand_month + str(i)
        price2 = past_points.loc[price_index, col] * 2000 # lbs -> tons
        quantity2 = past_points.loc[quantity_index, col] / 4 # months -> weeks
        profit2 = quantity2 * (price2 - path_cost)
        
        if (profit2 > profit):
            price = price2
            quantity = quantity2
            profit = profit2    
            year_used = 2005+i

    # convert to correct units/scale
    these_markets = get_markets(region)
    length = len(these_markets)
    quantity = quantity/length
    profit = profit/length
    price = price / 2000 # tons -> lbs
    
    parameters = [price, quantity, profit, year_used]
    
    return parameters   
    
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




# Updating/Counting Functions
# -------------------------------------------------------------------------- #

def update_decisions(parameters, i):
    product = parameters.loc[i, 'Product']
    region = parameters.loc[i, 'Region']
    demand_week = parameters.loc[i, 'Demand_Week'] 
    storage_week = parameters.loc[i, 'Storage_Week'] 
    plant_week = parameters.loc[i, 'Plant_Week'] 
    purchase_week = parameters.loc[i, 'Purchase_Week'] 
    grove = parameters.loc[i, 'Grove']
    plant = parameters.loc[i, 'Plant']
    storage = parameters.loc[i, 'Storage']
    price = parameters.loc[i, 'Price']
    #path_cost = parameters.loc[i, 'Path_Cost']
    quantity = parameters.loc[i, 'Quantity']
    profit = parameters.loc[i, 'Profit']
    contract = parameters.loc[i, 'Contract']
    
    
    update_capacity(quantity, product, storage_week, plant_week, plant, storage)
    update_spot_purchases(product, quantity, purchase_week, grove, contract)
    update_fut_arrivals(quantity, product, purchase_week, grove, contract)
    update_shipping1(quantity, product, grove, plant, storage, contract)
    update_manufacturing(quantity, product, plant, contract)
    update_shipping2(quantity, product, plant, storage, contract)
    update_count_ROJ(quantity, product, storage_week, storage)
    update_count_FCOJ(quantity, product, storage_week, storage)
    update_pricing(price, product, region, demand_week)
    update_quantities(quantity, product, region, demand_week)
    update_sources(product, region, demand_week, grove, contract)
    update_total_profit(profit)

def update_capacity(quantity, product, storage_week, plant_week, plant, storage):  
    if (plant in plants):
        plant_month = months[int(math.floor(plant_week / 4.0))]
        update_capacity_plant(quantity, product, plant_month, plant)
        
    storage_month = months[int(math.floor(storage_week / 4.0))]    
    update_capacity_storage(quantity, product, storage_month, storage)
    
# add quantities to plant for each month
def update_capacity_plant(quantity, product, plant_month, plant):
    if (plant in plants):
        capacity.loc[plant, plant_month] = capacity.loc[plant, plant_month] + quantity
        
def update_capacity_storage(quantity, product, storage_month, storage):
    capacity.loc[storage, storage_month] = capacity.loc[storage, storage_month] + quantity
    
# add quantity to raw materials path
def update_spot_purchases(product, quantity, purchase_week, grove, contract):
    if (contract == 'SPOT_ORA'):
        purchase_month = months[int(math.floor(purchase_week / 4.0))]
        spot_purchases.loc[grove, purchase_month] = spot_purchases.loc[grove, purchase_month] + quantity

# add quantity to arrival month
def update_fut_arrivals(quantity, product, purchase_week, grove, contract):
    purchase_month = months[int(math.floor(purchase_week / 4.0))]
    if (contract == 'FUT_ORA'):
        fut_arrivals.loc['ORA', purchase_month] = fut_arrivals.loc['ORA', purchase_month] + quantity
    if (contract == 'FUT_FCOJ'):
        fut_arrivals.loc['FCOJ', purchase_month] = fut_arrivals.loc['FCOJ', purchase_month] + quantity
        
# add quantity to shipping1 path
def update_shipping1(quantity, product, grove, plant, storage, contract):
    if (contract == 'SPOT_ORA') | (contract == 'FUT_ORA'):
        if (product == 'ORA'):
            shipping1.loc[grove, storage] = shipping1.loc[grove, storage] + quantity
        else:
            shipping1.loc[grove, plant] = shipping1.loc[grove, plant] + quantity

# add quantity to manufacturing path
def update_manufacturing(quantity, product, plant, contract):
    if (contract == 'SPOT_ORA') | (contract == 'FUT_ORA'):    
        if (product == 'POJ'):
            manufacturing.loc['Proportion', (plant+'_POJ')] = manufacturing.loc['Proportion', (plant+'_POJ')] + quantity
        if (product == 'ROJ') | (product == 'FCOJ'):
            manufacturing.loc['Proportion', (plant+'_FCOJ')] = manufacturing.loc['Proportion', (plant+'_FCOJ')] + quantity                      

# add quantity to shipping2 path
def update_shipping2(quantity, product, plant, storage, contract):
    if (contract == 'SPOT_ORA') | (contract == 'FUT_ORA'):
        if (product == 'POJ'):
            shipping2.loc[storage, (plant+'_POJ')] = shipping2.loc[storage, (plant+'_POJ')] + quantity
        if (product == 'ROJ') | (product == 'FCOJ'):
            shipping2.loc[storage, (plant+'_FCOJ')] = shipping2.loc[storage, (plant+'_FCOJ')] + quantity 
                
    if (contract == 'FUT_FCOJ'):
        shipping2.loc[storage, 'Futures_FCOJ'] = shipping2.loc[storage, ('Futures_FCOJ')] + quantity
        
# add quantity of ROJ at each storage
def update_count_ROJ(quantity, product, storage_week, storage):
    storage_month = months[int(math.floor(storage_week / 4.0))]
    if (product == 'ROJ'):
        count_ROJ.loc[storage, storage_month] = count_ROJ.loc[storage, storage_month] + quantity
        
# add quantity of FCOJ at each storage
def update_count_FCOJ(quantity, product, storage_week, storage):
    storage_month = months[int(math.floor(storage_week / 4.0))]
    if (product == 'FCOJ'):
        count_FCOJ.loc[storage, storage_month] = count_FCOJ.loc[storage, storage_month] + quantity
        
# update pricing for path        
def update_pricing(price, product, region, demand_week):
    demand_month = months[int(math.floor(demand_week / 4.0))]
    if (product == 'ORA'):
        pricing_ORA.loc[region, demand_month] = price
    if (product == 'POJ'):
        pricing_POJ.loc[region, demand_month] = price
    if (product == 'ROJ'):
        pricing_ROJ.loc[region, demand_month] = price
    if (product == 'FCOJ'):
        pricing_FCOJ.loc[region, demand_month] = price

# update quantity for path        
def update_quantities(quantity, product, region, demand_week):
    demand_month = months[int(math.floor(demand_week / 4.0))]
    if (product == 'ORA'):
        quantity_ORA.loc[region, demand_month] = quantity_ORA.loc[region, demand_month] + quantity
    if (product == 'POJ'):
        quantity_POJ.loc[region, demand_month] = quantity_POJ.loc[region, demand_month] + quantity
    if (product == 'ROJ'):
        quantity_ROJ.loc[region, demand_month] = quantity_ROJ.loc[region, demand_month] + quantity
    if (product == 'FCOJ'):
        quantity_FCOJ.loc[region, demand_month] = quantity_FCOJ.loc[region, demand_month] + quantity

# update sources for path        
def update_sources(product, region, demand_week, grove, contract):
    demand_month = months[int(math.floor(demand_week / 4.0))]
    if (contract == 'SPOT_ORA'):
        if (product == 'ORA'):
            source_ORA.loc[region, demand_month] = grove
        if (product == 'POJ'):
            source_POJ.loc[region, demand_month] = grove
        if (product == 'ROJ'):
            source_ROJ.loc[region, demand_month] = grove
        if (product == 'FCOJ'):
            source_FCOJ.loc[region, demand_month] = grove
    if (contract == 'FUT_ORA') | (contract == 'FUT_FCOJ'):
        if (product == 'ORA'):
            source_ORA.loc[region, demand_month] = contract
        if (product == 'POJ'):
            source_POJ.loc[region, demand_month] = contract
        if (product == 'ROJ'):
            source_ROJ.loc[region, demand_month] = contract
        if (product == 'FCOJ'):
            source_FCOJ.loc[region, demand_month] = contract
        
# add path profit to total profit
def update_total_profit(profit):
    global total_profit
    total_profit = total_profit + profit
    
def add_value_to_cell(value, table, index, column):
    table.loc[index, column] = table.loc[index, column] + value

# -------------------------------------------------------------------------- #




# Percentage Calculating Functions
# -------------------------------------------------------------------------- #

def calculate_decision_percentages():
    calculate_fut_arrivalsP()
    calculate_shipping1P()
    calculate_manufacturingP()
    calculate_shipping2P()
    calculate_reconstitutionP()

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
    nrow = count_ROJ.shape[0]
    ncol = count_ROJ.shape[1]
    
    for r in range(0, nrow):
        for c in range(0, ncol):
            total = count_ROJ.iloc[r, c] + count_FCOJ.iloc[r, c]
            if (total == 0):
                reconstitutionP.iloc[r, c] = 0.0
            else:
                reconstitutionP.iloc[r, c] = count_ROJ.iloc[r, c] / total * 100

# -------------------------------------------------------------------------- #
   



# Test Code
# -------------------------------------------------------------------------- #
start_time = time.time()

get_decisions()
#print('total profit: ' + str(4*total_profit))


#product = 'ORA'
#region = 'MW'
#demand_week = 4
#slope = -.00035
#intercept = 3.0
#contract= 'SPOT_ORA'
#parameters = get_optimal_parameters(product, region, demand_week, slope, intercept, contract)
#print(parameters)

print("--- %s seconds ---" % (time.time() - start_time))
# -------------------------------------------------------------------------- #




# Action Items
# -------------------------------------------------------------------------- #
    

        
# -------------------------------------------------------------------------- #



