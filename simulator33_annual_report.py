import pandas, numpy, math
from gpxpy import geo

# Vectors
# -------------------------------------------------------------------------- #

products = ['ORA','POJ','ROJ','FCOJ']
regions = ['NE','MA','SE','MW','DS','NW','SW']
months = ['Sep','Oct','Nov','Dec','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug']
groves = ['FLA','CAL','TEX','ARZ','BRA','SPA']
plants = ['P07']
storages = ['S44','S51','S68']
transporters = ['IC', 'TC']
max_capacities = [1748, 7684, 13204, 5458]

# -------------------------------------------------------------------------- #




# Read In Excel Spreasheets Using Pandas
# -------------------------------------------------------------------------- #

G_P = pandas.read_excel('Data/StaticData.xlsx', 'G->PS')
P_S = pandas.read_excel('Data/StaticData.xlsx', 'P->S')
S_M = pandas.read_excel('Data/StaticData.xlsx', 'S->M (avg)')
Terminals = pandas.read_excel('Data/StaticData.xlsx', 'Terminals')

grove_USprices = pandas.read_excel('Data/HarvestPricesWith2017Projection.xlsx', '2017 Projections')

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

# 336 rows of optimal parameters sorted by profit, iterate through until capacity filled
list_indices = numpy.arange(len(products)*len(regions)*len(months))
list_columns = ['Product', 'Region', 'Month', 'Grove', 'Plant', 'Storage', 'Transporter', 'Price', 'Quantity', 'Profit']
list_of_choices = pandas.DataFrame(index = list_indices, columns = list_columns)

# Purchases at the Spot Market(tons per week in a month) (ORA)
spot_purchases = pandas.DataFrame(data = 0.0, index = groves, columns = months)

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

# Total Profit
total_profit = 0.0

# -------------------------------------------------------------------------- #




# Annual Report (INCOMPLETE)
# -------------------------------------------------------------------------- #

activities	= pandas.DataFrame(data = 0.0, index = ['Sales (tons)','Fresh Oranges (ORA)','Premium Orange Juice (POJ)','Reconstituted Orange Juice (ROJ)','Frozen Concentrated Orange Juice (FCOJ)','Materials Acquisitions & Losses (tons)','Oranges Harvested','ORA Futures Matured','FCOJ Futures Matured','Premium Orange Juice (POJ) Manufactured','Frozen Concentrated Orange Juice (FCOJ) Manufactured','Reconstituted Orange Juice (ROJ) Manufactured','Products Lost due to Capacity Shortage','Products Lost due to Spoilage','Futures Contracts Purchases (tons)','ORA Futures Contracts','FCOJ Futures Contracts','Facilities Adjustment (tons of capacity)','Processing Plants Capacity Upgrade','Storage Centers Capacity Upgrade','Processing Plants Capacity Downgrade','Storage Centers Capacity Downgrade','Facilities Acquisitions (unit)','Processing Plants','Storage Centers','TankCars','Facilities Sold (unit)','Processing Plants','Storage Centers','TankCars'], columns = ['Value'])
                                                   
# -------------------------------------------------------------------------- #




# Optimizing Functions
# -------------------------------------------------------------------------- #

# iterate through list of choices sorted by profit, update decisions if choice doesn't overfill capacity
def get_decisions():
    get_list_of_choices()
    locations = plants + storages
    
    end = len(products) * len(regions) * len(months)
    for i in range(0, end):
        parameters = list_of_choices.iloc[i:i+1, 0:10]
        month = parameters.loc[i, 'Month']
        quantity = parameters.loc[i, 'Quantity']
        
        full = False
        for l in locations:
            if (capacity.loc[l, month] + quantity > max_capacities.loc[l, 'Max_Capacity']):
                full = True
        
        if (full == False):
            update_decisions(parameters, i)
            update_annual_report(parameters, i)

    calculate_decision_percentages()            

# get list of optimal parameters for every product/region/month and sort by profit
def get_list_of_choices():
    i = 0
    for p in products:
        for r in regions:
            for m in months:
                slope = get_slope(p, r, m)
                intercept = get_intercept(p, r, m)
                
                parameters = get_optimal_parameters(p, r, m, slope, intercept)
                
                list_of_choices.iloc[i:i+1, 0:10] = parameters
                i = i+1
    list_of_choices.sort_values('Profit', ascending = False, inplace = True)
    list_of_choices.set_index(list_indices, inplace=True)
    
                    
# return optimal path, price, and quantity for a product/region/month
def get_optimal_parameters(product, region, month, slope, intercept):
    slope = slope / .0005 # lbs -> tons
    intercept = intercept / .0005 # lbs -> tons 

    optimal_path = get_optimal_path(product, region, month)  
    grove = optimal_path[0]
    plant = optimal_path[1]
    storage = optimal_path[2]
    transporter = optimal_path[3]  
    path_cost = optimal_path[4]     
    
    # solve derivative of quadratic for quantity/price
    quantity = (path_cost - intercept) / (2 * slope)
    price = slope*quantity + intercept
    
    # game's max price is 4, so downgrade price/quantity if needed
    if (price > 4.0/.0005):
        price = 4.0/.0005
        quantity = (price - intercept) / slope
        
    profit = quantity * (price - path_cost)
    
    # if any negative values, don't try to provide demand there        
    if ((price < 0.0) | (quantity < 0.0) | (profit < 0.0) | math.isnan(slope) | math.isnan(intercept)):
        price = 0.0
        quantity = 0.0
        profit = 0.0
    
    # check all past points to see if anything has higher profit than the best point on the line
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
    for g in groves:
        plant = get_relevant_plant(product, g, storage)
            
        transportation_cost = get_transportation_cost(product, region, g, plant, storage, transporter)
        purchase_cost = get_purchase_cost(product, g, month)
        plant_cost = get_plant_cost(product, g)
        reconstitution_cost = get_reconstitution_cost(product)
        
        total_cost = transportation_cost + purchase_cost + plant_cost + reconstitution_cost      

        if (total_cost < min_cost):
            min_cost = total_cost
            optimal_path = [g, plant, storage, transporter, total_cost]
            
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

# return closest plant to storage, if Product == ORA return None
def get_relevant_plant(product, grove, storage):
    if (product == 'ORA'): return None
      
    min_dist = float('inf')
    for p in plants:
        d = P_S.loc[storage, p]
        if (d < min_dist):
            min_dist = d
            plant = p
    
    return plant

# return cost of transporting from grove to market region
def get_transportation_cost(product, region, grove, plant, storage, transporter):
    # if Product == ORA, transport straight to storage
    if (product == 'ORA'):
        cost_G_to_P = 0
        cost_P_to_S = 0
        cost_G_to_S = get_grove_to_storage_distance(grove, storage) * .22 
    # if Grove in USA, transport from grove
    elif (grove in ['FLA','CAL','TEX','ARZ']):
        cost_G_to_P = G_P.loc[plant, grove] * .22
        cost_P_to_S = P_S.loc[storage, plant] * .65
        cost_G_to_S = 0
    # if Grove NOT in USA, transport from FLA
    elif (grove in ['BRA','SPA']):
        cost_G_to_P = G_P.loc[plant, 'FLA'] * .22
        cost_P_to_S = P_S.loc[storage, plant] * .65
        cost_G_to_S = 0
    
    cost_S_to_M = S_M.loc[region, storage] * 1.2  
    
    inv_hold_cost = 60
    
    total_transportation_cost = cost_G_to_P + cost_P_to_S + cost_G_to_S + cost_S_to_M + inv_hold_cost
    
    #print('cost_G_to_P = ' + str(cost_G_to_P))
    #print('cost_P_to_S = ' + str(cost_P_to_S))
    #print('cost_G_to_S = ' + str(cost_G_to_S))
    #print('cost_S_to_M = ' + str(cost_S_to_M))
    #print ('inventory hold cost = ' + str(inv_hold_cost))
    #print('total_transportation_cost = ' + str(total_transportation_cost))
    
    return total_transportation_cost
    
# return cost of purchasing oranges at grove during month
def get_purchase_cost(product, grove, month):
    purchase_cost = grove_USprices.loc[grove, month] / .0005 # lbs -> tons

    #print('purchase_cost = ' + str(purchase_cost))

    return purchase_cost

# return cost of manufacturing POJ or ROJ
def get_plant_cost(product, grove):
    if (product == 'ORA'): plant_cost = 0
    if (product == 'POJ'): plant_cost = 2000
    if (product == 'ROJ'): plant_cost = 1000
    if (product == 'FCOJ'): plant_cost = 1000
        
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
    month = parameters.loc[i, 'Month'] 
    grove = parameters.loc[i, 'Grove']
    plant = parameters.loc[i, 'Plant']
    storage = parameters.loc[i, 'Storage']
    price = parameters.loc[i, 'Price']
    quantity = parameters.loc[i, 'Quantity']
    profit = parameters.loc[i, 'Profit']
        
    update_capacity(quantity, product, month, plant, storage)
    update_spot_purchases(quantity, month, grove)
    update_shipping1(quantity, product, grove, plant, storage)
    update_manufacturing(quantity, product, plant)
    update_shipping2(quantity, product, plant, storage)
    update_count_ROJ(quantity, product, month, storage)
    update_count_FCOJ(quantity, product, month, storage)
    update_pricing(price, product, region, month)
    update_quantities(quantity, product, region, month)
    update_total_profit(profit)

# add quantities to plant/storage for each month
def update_capacity(quantity, product, month, plant, storage):
    if (plant != None):
        capacity.loc[plant, month] = capacity.loc[plant, month] + quantity
        
    capacity.loc[storage, month] = capacity.loc[storage, month] + quantity
    
# add quantity to raw materials path
def update_spot_purchases(quantity, month, grove):
    spot_purchases.loc[grove, month] = spot_purchases.loc[grove, month] + quantity
    
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
        
# add quantity of ROJ at each storage
def update_count_ROJ(quantity, product, month, storage):
    if (product == 'ROJ'):
        count_ROJ.loc[storage, month] = count_ROJ.loc[storage, month] + quantity
        
# add quantity of FCOJ at each storage
def update_count_FCOJ(quantity, product, month, storage):
    if (product == 'FCOJ'):
        count_FCOJ.loc[storage, month] = count_FCOJ.loc[storage, month] + quantity
        
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

# update quantity for path        
def update_quantities(quantity, product, region, month):
    if (product == 'ORA'):
        quantity_ORA.loc[region, month] = quantity_ORA.loc[region, month] + quantity
    if (product == 'POJ'):
        quantity_POJ.loc[region, month] = quantity_POJ.loc[region, month] + quantity
    if (product == 'ROJ'):
        quantity_ROJ.loc[region, month] = quantity_ROJ.loc[region, month] + quantity
    if (product == 'FCOJ'):
        quantity_FCOJ.loc[region, month] = quantity_FCOJ.loc[region, month] + quantity
        
# add path profit to total profit
def update_total_profit(profit):
    global total_profit
    total_profit = total_profit + profit

# -------------------------------------------------------------------------- #




# Percentage Calculating Functions
# -------------------------------------------------------------------------- #

def calculate_decision_percentages():
    calculate_shipping1P()
    calculate_manufacturingP()
    calculate_shipping2P()
    calculate_reconstitutionP()
        
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

def update_annual_report(parameters, i):
    update_activities(parameters, i)

def update_activities(parameters, i):
    product = parameters.loc[i, 'Product']
    region = parameters.loc[i, 'Region']
    month = parameters.loc[i, 'Month'] 
    grove = parameters.loc[i, 'Grove']
    plant = parameters.loc[i, 'Plant']
    storage = parameters.loc[i, 'Storage']
    price = parameters.loc[i, 'Price']
    quantity = parameters.loc[i, 'Quantity']
    profit = parameters.loc[i, 'Profit']
    
    if (product == 'ORA'):
        activities.loc['Fresh Oranges (ORA)', 'Value'] = activities.loc['Fresh Oranges (ORA)', 'Value'] + quantity
    if (product == 'POJ'):
        activities.loc['Premium Orange Juice (POJ)', 'Value'] = activities.loc['Premium Orange Juice (POJ)', 'Value'] + quantity
    if (product == 'ROJ'):
        activities.loc['Reconstituted Orange Juice (ROJ)', 'Value'] = activities.loc['Reconstituted Orange Juice (ROJ)', 'Value'] + quantity
    if (product == 'FCOJ'):
        activities.loc['Frozen Concentrated Orange Juice (FCOJ)', 'Value'] = activities.loc['Frozen Concentrated Orange Juice (FCOJ)', 'Value'] + quantity

# -------------------------------------------------------------------------- #




# Test Code
# -------------------------------------------------------------------------- #

get_decisions()
print(total_profit)

# -------------------------------------------------------------------------- #




# Action Items
# -------------------------------------------------------------------------- #
    

        
# -------------------------------------------------------------------------- #







