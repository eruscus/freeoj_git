import pandas, numpy, math
from gpxpy import geo

# Vectors
# -------------------------------------------------------------------------- #

products = ['ORA','POJ','ROJ','FCOJ']
regions = ['NE','MA','SE','MW','DS','NW','SW']
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

# -------------------------------------------------------------------------- #




# Read In Excel Spreasheets Using Pandas
# -------------------------------------------------------------------------- #

G_P = pandas.read_excel('Data/StaticData.xlsx', 'G->PS')
P_S = pandas.read_excel('Data/StaticData.xlsx', 'P->S')
S_M = pandas.read_excel('Data/StaticData.xlsx', 'S->M (avg)')
Terminals = pandas.read_excel('Data/StaticData.xlsx', 'Terminals')

grove_USprices = pandas.read_excel('Data/2018_Spot_Projections.xlsx')

ORA_equations = pandas.read_csv('Data/ORA_equations.csv')
POJ_equations = pandas.read_csv('Data/POJ_equations.csv')
ROJ_equations = pandas.read_csv('Data/ROJ_equations.csv')
FCOJ_equations = pandas.read_csv('Data/FCOJ_equations.csv')

ORA_past_points = pandas.read_excel('Data/Monthly_Price_Demand.xlsx', 'ORA')
POJ_past_points = pandas.read_excel('Data/Monthly_Price_Demand.xlsx', 'POJ')
ROJ_past_points = pandas.read_excel('Data/Monthly_Price_Demand.xlsx', 'ROJ')
FCOJ_past_points = pandas.read_excel('Data/Monthly_Price_Demand.xlsx', 'FCOJ')

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

# 1344 rows of optimal parameters sorted by profit, iterate through until capacity filled
choice_indices = numpy.arange(len(products) * len(regions) * NUM_WEEKS)
choice_columns = ['Product', 'Region', 'Demand_Week', 'Storage_Week', 'Plant_Week', 'Purchase_Week', 'Grove', 'Plant', 'Storage', 'Transporter', 'Price', 'Path_Cost','Quantity', 'Profit', 'Year_Used', 'Contract']
choices_SPOT_ORA = pandas.DataFrame(index = choice_indices, columns = choice_columns)
choices_FUT_ORA = pandas.DataFrame(index = choice_indices, columns = choice_columns)
choices_FUT_FCOJ = pandas.DataFrame(index = choice_indices, columns = choice_columns)

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




# Annual Report (INCOMPLETE)
# -------------------------------------------------------------------------- #

activities	= pandas.DataFrame(data = 0.0, index = ['Sales (tons)','Fresh Oranges (ORA)','Premium Orange Juice (POJ)','Reconstituted Orange Juice (ROJ)','Frozen Concentrated Orange Juice (FCOJ)',' ','Materials Acquisitions & Losses (tons)','Oranges Harvested','ORA Futures Matured','FCOJ Futures Matured','Premium Orange Juice (POJ) Manufactured','Frozen Concentrated Orange Juice (FCOJ) Manufactured','Reconstituted Orange Juice (ROJ) Manufactured','Products Lost due to Capacity Shortage','Products Lost due to Spoilage',' ','Futures Contracts Purchases (tons)','ORA Futures Contracts','FCOJ Futures Contracts',' ','Facilities Adjustment (tons of capacity)','Processing Plants Capacity Upgrade','Storage Centers Capacity Upgrade','Processing Plants Capacity Downgrade','Storage Centers Capacity Downgrade',' ','Facilities Acquisitions (unit)','Processing Plants','Storage Centers','TankCars',' ','Facilities Sold (unit)','Processing Plants','Storage Centers','TankCars'], columns = ['Value'])
earnings = pandas.DataFrame(data = 0.0, index = ['Sales Revenue','Fresh Oranges (ORA)','Premium Orange Juice (POJ)','Reconstituted Orange Juice (ROJ)','Frozen Concentrated Orange Juice (FCOJ)','Total Revenue',' ','Materials Costs','Orange (ORA) Purchases','ORA Futures Costs','FCOJ Futures Costs','Transportation Costs from Groves (ORA & ORA futures)','Transportation Costs from Groves (FCOJ futures)','Total Materials Costs',' ','Manufacturing Costs','POJ Manufacturing Costs','FCOJ Manufacturing Costs','ROJ Reconstitution Costs','Total Processing Costs',' ','Transportation Costs from Plants and Storages & Inventory Hold Costs','Transportation Costs from Plants (TankCars)','Transportation Costs from Plants (Carriers)','Inventory Hold Costs at Storages','Transportation Costs from Storages','Total Transportation and Storage Costs',' ','Facilities Adjustment & Maintenance Costs','Processing Plant Maintenance Costs','Costs(/Gains) of Acquiring(/Selling) Processing Plant','Processing Plant Capacity Adjustment Costs(/Gains)','Storage Center Maintenance Costs','Costs(/Gains) of Acquiring(/Selling) Storage Center','Storage Center Capacity Adjustment Costs(/Gains)','TankCars Hold Costs','TankCars Purchase Costs(/Selling Gains)','Total Facilities Costs',' ','Net Profit'], columns = ['Value'])

# -------------------------------------------------------------------------- #




# Optimizing Functions
# -------------------------------------------------------------------------- #
def get_decisions():
    get_choices()
    
    # allocate futures first and then do regular choices
    allocate_resources('FUT_FCOJ')
    allocate_resources('FUT_ORA')
    allocate_resources('SPOT_ORA')
    
    calculate_decision_percentages() 
    
# iterate through list of choices sorted by profit, update decisions if choice doesn't overfill capacity
def allocate_resources(contract):
    end = len(products) * len(regions) * NUM_WEEKS
    for i in range(0, end):
        if (contract == 'SPOT_ORA'):
            parameters = choices_SPOT_ORA.iloc[i:i+1, 0:16]
        if (contract == 'FUT_ORA'):
            parameters = choices_FUT_ORA.iloc[i:i+1, 0:16]
        if (contract == 'FUT_FCOJ'):
            parameters = choices_FUT_FCOJ.iloc[i:i+1, 0:16]
            
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
        if (plant != None):
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
def get_choices():
    i = 0
    for p in products:
        for r in regions:
            for w in weeks:
                demand_month = months[int(math.floor(w / 4.0))] # convert from week to month
                slope = get_slope(p, r, demand_month)
                intercept = get_intercept(p, r, demand_month)
                
                parameters = get_optimal_parameters(p, r, w, slope, intercept, 'SPOT_ORA')
                choices_SPOT_ORA.iloc[i:i+1, 0:16] = parameters
                
                parameters = get_optimal_parameters(p, r, w, slope, intercept, 'FUT_ORA')
                choices_FUT_ORA.iloc[i:i+1, 0:16] = parameters
                
                if (p == 'ROJ') | (p == 'FCOJ'):
                    parameters = get_optimal_parameters(p, r, w, slope, intercept, 'FUT_FCOJ')
                    choices_FUT_FCOJ.iloc[i:i+1, 0:16] = parameters
                    
                i = i+1
                    
    # sort list of choices
    choices_SPOT_ORA.sort_values('Profit', ascending = False, inplace = True)
    choices_SPOT_ORA.set_index(choice_indices, inplace=True)
    choices_FUT_ORA.sort_values('Profit', ascending = False, inplace = True)
    choices_FUT_ORA.set_index(choice_indices, inplace=True) 
    choices_FUT_FCOJ.sort_values('Profit', ascending = False, inplace = True)
    choices_FUT_FCOJ.set_index(choice_indices, inplace=True)
                    
# return optimal path, price, and quantity for a product/region/month
def get_optimal_parameters(product, region, demand_week, slope, intercept, contract):
    slope = slope * 2000 # ($/lb) / (tons/week) -> ($/tons) / (tons/week)
    intercept = intercept * 2000 # $/lb -> $/ton 
    
    storage_week = get_storage_week(demand_week)
    plant_week = get_plant_week(product, demand_week, contract)
    purchase_week = get_purchase_week(product, demand_week, contract)
    
    demand_month = months[int(math.floor(demand_week / 4.0))] # convert from week to month
    purchase_month = months[int(math.floor(purchase_week / 4.0))] # convert from week to month
    optimal_path = get_optimal_path(product, region, purchase_month, contract) # month only needed for grove purchasing
    
    grove = optimal_path[0]
    plant = optimal_path[1]
    storage = optimal_path[2]
    transporter = optimal_path[3]  
    path_cost = optimal_path[4] # $/ton
    
    # solve derivative of quadratic for quantity/price
    quantity = (path_cost - intercept) / (2 * slope)
    price = slope*quantity + intercept
    
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
    year_used = 2017
    for i in range(1,15):
        col = demand_month + str(i)
        price2 = past_points.loc[price_index, col] * 2000 # lbs -> tons
        quantity2 = past_points.loc[quantity_index, col] / 4 # months -> weeks
        profit2 = quantity2 * (price2 - path_cost)
        
        if (profit2 > profit):
            price = price2
            quantity = quantity2
            profit = profit2    
            year_used = 2005+i

    price = price / 2000 # tons -> lbs
    
    # debugging statement: see how many regions/months rely on previous data over demand curves
    #print('Product: ' + product + ', Month: ' + month + ', Region: ' + region + ', Year Used = ' + str(year_used) + ', Price = ' + str(price))
    
    parameters = [product, region, demand_week, storage_week, plant_week, 
                  purchase_week, grove, plant, storage, transporter, price, 
                  path_cost, quantity, profit, year_used, contract]
                 
    if (price == 0):
        print(parameters)
    
    return parameters
    
# return cheapest path from purchase to delivery
def get_optimal_path(product, region, month, contract):
    transporter = 'TC' # for now not sure which to use
    storage = get_closest_storage(region)
    
    if (contract == 'SPOT_ORA'):
        all_groves = groves
    if (contract == 'FUT_ORA') | (contract == 'FUT_FCOJ'):
        all_groves = ['FLA']
        
    min_cost = float('inf')
    for g in all_groves:
        plant = get_relevant_plant(product, g, storage, contract)
            
        transportation_cost = get_transportation_cost(product, region, g, plant, storage, transporter, contract)
        purchase_cost = get_purchase_cost(product, g, month, contract)
        plant_cost = get_plant_cost(product, contract)
        reconstitution_cost = get_reconstitution_cost(product)
        
        total_cost = transportation_cost + purchase_cost + plant_cost + reconstitution_cost      

        if (total_cost < min_cost):
            min_cost = total_cost
            optimal_path = [g, plant, storage, transporter, total_cost]
            
    return optimal_path
    
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
def get_transportation_cost(product, region, grove, plant, storage, transporter, contract):
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
            cost_G_to_S = get_grove_to_storage_distance(grove, storage) * .22  
        else:
            cost_G_to_P = G_P.loc[plant, 'FLA'] * .22
            cost_P_to_S = my_P_to_S
            cost_G_to_S = 0
            
    if (contract == 'FUT_FCOJ'):
        cost_G_to_P = 0
        cost_P_to_S = 0
        cost_G_to_S = get_grove_to_storage_distance('FLA', storage) * .22  
    
    cost_S_to_M = S_M.loc[region, storage] * 1.2    
    
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
    if (plant != None):
        plant_month = months[int(math.floor(plant_week / 4.0))]
        update_capacity_plant(quantity, product, plant_month, plant)
        
    storage_month = months[int(math.floor(storage_week / 4.0))]    
    update_capacity_storage(quantity, product, storage_month, storage)
    
# add quantities to plant for each month
def update_capacity_plant(quantity, product, plant_month, plant):
    if (plant != None):
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
   



# Update Annual Report (INCOMPLETE)
# -------------------------------------------------------------------------- # 

def add_value_to_cell(value, table, index, column):
    table.loc[index, column] = table.loc[index, column] + value

# Update Annual Report
def update_annual_report(parameters, i):
    update_activities(parameters, i)
    update_earnings(parameters, i)
    
# Update Activities for Annual Report
def update_activities(parameters, i):
    product = parameters.loc[i, 'Product']
    grove = parameters.loc[i, 'Grove']
    quantity = parameters.loc[i, 'Quantity']
    
    # Sales (tons)
    if (product == 'ORA'):
        add_value_to_cell(quantity, activities, 'Fresh Oranges (ORA)', 'Value')
    if (product == 'POJ'):
        add_value_to_cell(quantity, activities, 'Premium Orange Juice (POJ)', 'Value')
    if (product == 'ROJ'):
        add_value_to_cell(quantity, activities, 'Reconstituted Orange Juice (ROJ)', 'Value')
    if (product == 'FCOJ'):
        add_value_to_cell(quantity, activities, 'Frozen Concentrated Orange Juice (FCOJ)', 'Value')
        
    # Materials Acquisitions & Losses (tons)
    if (grove in groves):
        add_value_to_cell(quantity, activities, 'Oranges Harvested', 'Value')
    # ORA Futures Matured
    # FCOJ Futures Matured
    if (product == 'POJ'):
        add_value_to_cell(quantity, activities, 'Premium Orange Juice (POJ) Manufactured', 'Value')
    if (product == 'FCOJ'):
        add_value_to_cell(quantity, activities, 'Frozen Concentrated Orange Juice (FCOJ) Manufactured', 'Value')
    if (product == 'ROJ'):
        add_value_to_cell(quantity, activities, 'Reconstituted Orange Juice (ROJ) Manufactured', 'Value')
    # Products Lost due to Capacity Shortage
    # Products Lost due to Spoilage
    
    # Futures Contracts Purchases (tons)
    # ORA Futures Contracts
    # FCOJ Futures Contracts
    
    # Facilities Adjustment (tons of capacity)
    # Processing Plants Capacity Upgrade
    # Storage Centers Capacity Upgrade
    # Processing Plants Capacity Downgrade
    # Storage Centers Capacity Downgrade
    
    # Facilities Acquisitions (unit)	
    # Processing Plants
    # Storage Centers
    # TankCars
	
    # Facilities Sold (unit)	
    # Processing Plants
    # Storage Centers
    # TankCars
    
# Update Earnings for Annual Report
def update_earnings(parameters, i):
    product = parameters.loc[i, 'Product']
    region = parameters.loc[i, 'Region']
    #demand_week = parameters.loc[i, 'Demand_Week'] 
    #storage_week = parameters.loc[i, 'Storage_Week'] 
    plant_week = parameters.loc[i, 'Plant_Week'] 
    purchase_week = parameters.loc[i, 'Purchase_Week'] 
    grove = parameters.loc[i, 'Grove']
    plant = parameters.loc[i, 'Plant']
    storage = parameters.loc[i, 'Storage']
    price = parameters.loc[i, 'Price']
    #path_cost = parameters.loc[i, 'Path_Cost']
    quantity = parameters.loc[i, 'Quantity']
    #profit = parameters.loc[i, 'Profit']
    
    if (plant != None):
        plant_month = months[int(math.floor(plant_week / 4.0))] 
    purchase_month = months[int(math.floor(purchase_week / 4.0))]
    
    # Sales Revenue
    if (product == 'ORA'):
        add_value_to_cell(quantity*price*2000, earnings, 'Fresh Oranges (ORA)', 'Value')
    if (product == 'POJ'):
        add_value_to_cell(quantity*price*2000, earnings, 'Premium Orange Juice (POJ)', 'Value')
    if (product == 'ROJ'):
        add_value_to_cell(quantity*price*2000, earnings, 'Reconstituted Orange Juice (ROJ)', 'Value')
    if (product == 'FCOJ'):
        add_value_to_cell(quantity*price*2000, earnings, 'Frozen Concentrated Orange Juice (FCOJ)', 'Value')
    add_value_to_cell(quantity*price*2000, earnings, 'Total Revenue', 'Value')
    
    # Materials Costs
    if (grove in groves):
        value = quantity*get_purchase_cost(product, grove, purchase_month)
        add_value_to_cell(value, earnings, 'Orange (ORA) Purchases', 'Value')
        add_value_to_cell(value, earnings, 'Total Materials Costs', 'Value')
    # ORA Futures Costs
    # FCOJ Futures Costs
    if (product == 'ORA'):
        value = get_grove_to_storage_distance(grove, storage) * .22
        add_value_to_cell(value, earnings, 'Transportation Costs from Groves (ORA & ORA futures)', 'Value')
        add_value_to_cell(value, earnings, 'Total Materials Costs', 'Value')
    # Transportation Costs from Groves (FCOJ futures)
    
    # Manufacturing Costs
    if (product == 'POJ'):
        add_value_to_cell(quantity*2000, earnings, 'POJ Manufacturing Costs', 'Value')
        add_value_to_cell(quantity*2000, earnings, 'Total Processing Costs', 'Value')
    if ((product == 'ROJ') | (product == 'FCOJ')):
        add_value_to_cell(quantity*1000, earnings, 'FCOJ Manufacturing Costs', 'Value')
        add_value_to_cell(quantity*1000, earnings, 'Total Processing Costs', 'Value')
    if (product == 'ROJ'):
        add_value_to_cell(quantity*650, earnings, 'ROJ Reconstitution Costs', 'Value')
        add_value_to_cell(quantity*650, earnings, 'Total Processing Costs', 'Value')
    
    # Transportation Costs from Plants and Storages & Inventory Hold Costs
    # Transportation Costs from Plants (TankCars)
    if (plant != None):
        if (capacity.loc[plant, plant_month] < 300):
            value = 36 * quantity/30 * P_S.loc[storage, plant]
            add_value_to_cell(value, earnings, 'Transportation Costs from Plants (TankCars)', 'Value')
            add_value_to_cell(value, earnings, 'Total Transportation and Storage Costs', 'Value')
    
    # Transportation Costs from Plants (Carriers)
    if (plant != None):
        if (capacity.loc[plant, plant_month] >= 300):
            value = .65 * quantity * P_S.loc[storage, plant]
            add_value_to_cell(value, earnings, 'Transportation Costs from Plants (Carriers)', 'Value')
            add_value_to_cell(value, earnings, 'Total Transportation and Storage Costs', 'Value')
            
    # Inventory Hold Costs at Storages
    add_value_to_cell(quantity*60, earnings, 'Inventory Hold Costs at Storages', 'Value')
    add_value_to_cell(quantity*60, earnings, 'Total Transportation and Storage Costs', 'Value')
    
    # Transportation Costs from Storages
    value = 1.2 * quantity * S_M.loc[region, storage]
    add_value_to_cell(value, earnings, 'Transportation Costs from Storages', 'Value')
    add_value_to_cell(value, earnings, 'Total Transportation and Storage Costs', 'Value')
    
# -------------------------------------------------------------------------- #




# Test Code
# -------------------------------------------------------------------------- #

get_decisions()
print('total profit: ' + str(4*total_profit))

#demand_month = months[int(math.floor(w / 4.0))] # convert from week to month
#slope = get_slope(p, r, demand_month)
#intercept = get_intercept(p, r, demand_month)
#
#parameters = get_optimal_parameters(p, r, w, slope, intercept)
#
#list_of_choices.iloc[i:i+1, 0:15] = parameters
#i = i+1
#    
##interpolate_list_of_choices()
# list_of_choices.sort_values(['Product','Region','Demand_Week'], ascending = [True,True,True], inplace = True)
#list_of_choices.set_index(list_indices, inplace=True)
    
                    
# return optimal path, price, and quantity for a product/region/month
# def get_optimal_parameters(product, region, demand_week, slope, intercept):

# -------------------------------------------------------------------------- #




# Action Items
# -------------------------------------------------------------------------- #
    

        
# -------------------------------------------------------------------------- #



