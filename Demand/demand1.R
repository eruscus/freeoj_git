load('ORA.RData')
load('POJ.RData')
load('FCOJ.RData')
load('ROJ.RData')



split.region <- function(NAME) {
  RE = (ORA$Region == NAME) #NEED TO REPLACE ORA BY APPROPRIATE PRODUCT HERE AND ON LINE 5
  Per.region = cbind(ORA$Time[RE], ORA$Month[RE], ORA$Week[RE], ORA$Price[RE], ORA$Sales[RE], ORA$Capacity[RE], ORA$Indicator[RE])
  return(Per.region)  
}

#FIRST, COMMAND+A THEN CLICK RUN (to compile all functions. Don't worry about the outputs.)

#GO TO LINE 120. NO NEED TO READ THIS.

remove.zeros <- function(X){ #X is a matrix
  year = vector(,576)
  year[1] = 1
  for (i in {2:576}){
    year[i] = year[i-1]
    if (X[i,3] == 1) {
      year[i] = year[i-1]+1
    }
  }
  
  NZ = (X[,6] != 0)
  Y = cbind(X[,1][NZ], year[NZ], X[,2][NZ], X[,3][NZ], X[,4][NZ], X[,5][NZ], X[,6][NZ], X[,7][NZ])
  return(Y)  
}

est.demand <- function(A){
  X = A[,6]
  for (i in {1:length(A[,1])}){
    if(A[,8][i] == 1){
      a = runif(1, min = .1, max = .5)
      X[i] = A[,6][i]*(1+a)
    }
  }
  Y = cbind(A[,1], A[,2], A[,3], A[,4], A[,5], X, A[,7], A[,8])
  return(Y)
}

#TIME, YEAR, MONTH, WEEK, PRICE, DEMAND, CAPACITY, INDICATOR 
plot.h.season <- function(X){
  is.H = (X[,2] <= 10)
  WEEK = X[,4][is.H]
  DEMAND = X[,6][is.H]
  
  plot(WEEK, DEMAND)
  axis(1, at = WEEK)
  grid(nx = 49)
  return()
}

plot.all.season <- function(X){
  WEEK = X[,4]
  DEMAND = X[,6]
  
  plot(WEEK, DEMAND)
  axis(1, at = WEEK)
  grid(nx = 49)
  return()
}

#TIME, YEAR, MONTH, WEEK, PRICE, DEMAND, CAPACITY, INDICATOR   
fit.demand <- function(S.start, S.end, X){
  season.length = S.end-S.start + 1
  HTD = vector(,season.length)
  HTP = vector(,season.length)
  OneTP = vector(,season.length)
  OneTD = vector(,season.length)
  TwoTD = vector(,season.length)
  TwoTP = vector(,season.length)
  
  #first, average the historical data
  
  for(i in {1:length(X[,1])}){
    if((X[,4][i] <= S.end) && (X[,4][i] >= S.start)){
      
      if(X[,2][i] <= 10){
        
        HTD[X[,4][i]] = HTD[X[,4][i]] + X[,6][i]
        HTP[X[,4][i]] = HTP[X[,4][i]] + X[,5][i]
        
      }
      
      if(X[,2][i] == 11){
        OneTD[X[,4][i]] = OneTD[X[,4][i]] + X[,6][i]
        OneTP[X[,4][i]] = OneTP[X[,4][i]] + X[,5][i]
      }
      
      if(X[,2][i] == 12){
        TwoTD[X[,4][i]] = TwoTD[X[,4][i]] + X[,6][i]
        TwoTP[X[,4][i]] = TwoTP[X[,4][i]] + X[,5][i]
      }
    }
  }
  
  
  HD = HTD/10
  HP = HTP/10
  
  OneD = OneTD
  OneP = OneTP
  
  TwoD = TwoTD
  TwoP = TwoTP
  
  DEMAND = c(HD, OneD, TwoD)
  PRICE = c(HP, OneP, TwoP)
  
  
  LINE = lsfit(DEMAND, PRICE)
  return(LINE$coeff)
  
}

#EXAMPLE REGION CODE. NEED TO REPLACE DS BY APPRPRIATE REGION IN WHAT FOLLOWS
DS = split.region('DS')
DS_Zero =  remove.zeros(DS)
DS.est = est.demand(DS_Zero)

plot.h.season(DS.est) #PLOTS HISTORICAL DATA 
#LOOK AT THE PLOT AND DECIDE ON THE SEASONS. IF SHITTY, THEN RUN FOLLOWING FUNCTION:
plot.all.season(DS.est)

#THEN FOR EACH SEASON RUN:
#HERE, 1 AND 8 ARE THE BEGINNING AND END WEEKS OF THE SEASON
fit.demand(1,8,DS.est)
#COPY OUTPUT TO EXCEL FILE
