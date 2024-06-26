#########################################################
#                                                        
#                  Data Quality Check
#                  
#                                                        
#                  Author: Egil Fischer                               
#                  Contact:   e.a.j.fischer@uu.nl                           
#                  Creation date: 16-11-2022                         
#########################################################
library(dplyr)


outlier_count <- function(data) {
  data$sample_measure <-as.numeric(data$sample_measure)
  Q1 <- quantile(data$sample_measure, 0.25,na.rm=TRUE)
  Q3 <- quantile(data$sample_measure, 0.75,na.rm=TRUE)
  lower.bound.mild <- Q1 - 1.5*IQR(data$sample_measure, na.rm = TRUE)
  upper.bound.mild <- Q3 + 1.5*IQR(data$sample_measure,na.rm = TRUE)
  lower.bound.extreme <- Q1 - 3*IQR(data$sample_measure, na.rm = TRUE)
  upper.bound.extreme <- Q3 + 3*IQR(data$sample_measure,na.rm = TRUE)
  
  data$sample_measure[is.na(data$sample_measure)]<-0
  
  extreme.outliers <- sum(data$sample_measure < lower.bound.extreme | data$sample_measure > upper.bound.extreme)
  extreme.outliers.perc <- round(extreme.outliers/length(data$sample_measure)*100, digits = 2) 
  
  mild.outliers <- sum(data$sample_measure < lower.bound.mild | data$sample_measure > upper.bound.mild )
 
  
  mild.outliers <-mild.outliers - extreme.outliers
  mild.outliers.perc <- round(mild.outliers/length(data$sample_measure)*100, digits = 2)
  

  outliers.sample.measure <- c(paste0(mild.outliers, 
                                      ' (', 
                                      mild.outliers.perc, 
                                      ' %) mild outliers(1.5x IQR)'),
                               paste0(extreme.outliers, 
                                      ' (', 
                                      extreme.outliers.perc , 
                                      ' %) extreme outliers(3x IQR)'))
  
  return(outliers.sample.measure)
}



sample_times <- function(data){
  ## TODO: what makes sense to have here
  # per host, get a list of all times with a result
  # 0 = susceptible, 1= latent, 2 = infectious : is this correct?
  # so the inoculated animals are 1 at time 1??    
  
  data$sample_measure<-as.character(data$sample_measure)
  # list hosts that are inoculated: latent at start experiment?
  inoculatedHosts <- subset(data,
                            ex_day == 0 & (inoculationStatus == '2' | inoculationStatus =='I' | inoculationStatus=='Inoculated'),
                            select = host_id)
  # split dataframe base on host ID
  inoculated <- subset(data,
                       host_id %in% inoculatedHosts$host_id)
  susceptible <- subset(data,
                        !(host_id %in% inoculatedHosts$host_id))
  # idea 1: do not group per host, just use all the sampling days.
  days_I <- inoculated %>%
    # remove rows without result:
    filter(!is.na(sample_measure) | !is.na(sample_result) | !is.na(detectionLimit)) %>%
    select(ex_day) %>%
    # make day range of 4 days
  #  step <-get.step(data$ex_day)
    mutate(range = cut(ex_day, 
                       breaks = seq(min(ex_day), max(ex_day), by=get.step(length(unique(ex_day)))), 
                       include.lowest=TRUE)) %>%
    # count number of results per day range
    group_by(range) %>%
    summarise(number_of_results = n())
  days_S <- susceptible %>%
    # remove rows without result:
    filter(!is.na(sample_measure) | !is.na(sample_result) | !is.na(detectionLimit)) %>%
    select(ex_day) %>%
    # make day range of 4 days
#    step <-
    mutate(range = cut(ex_day, 
                       breaks = seq(min(ex_day), max(ex_day), by=get.step(length(unique(ex_day)))), 
                       include.lowest=TRUE)) %>%
    # count number of results per day range
    group_by(range) %>%
    summarise(number_of_results = n())
  
  return(list(days_I,days_S))

    
  }

  
 


report.DataQuality <-function(data){
  #data quality report
  data.quality <- list()
  #check if the data is not empty
  if(is.null(data))  {
    data.quality$data.presence<-"No data present";
    return(data.quality);
  }else {data.quality$data.presence <- "Contains data."}
  
  #give the names of the variables in the data set
  data.quality$var.names <- colnames(data);
  
  #report per variable the summary after setting known variable to be numeric
  data[,c("ex_day", "ex_hour","hour_after_inoc", "inoculationHour","sample_measure")]<-sapply(data[,c("ex_day", "ex_hour","hour_after_inoc", "inoculationHour","sample_measure")],as.numeric)
  data.quality$summary <- summary(data);
  #data.quality$IQR <- IQR(data$sample_measure)
  data.quality$UnitOfMeasurement <- unique(data$unit_measure)
  data.quality$QuantityFunction <- unique(data$quantity_function)
  if(all(!is.na(data$sample_measure))){
  data.quality$outliers.sample.measure <- outlier_count(data)}
  if (length(unique(data$ex_day))>1){
  data.quality$SamplesInoculated <- sample_times(data)[1]
  data.quality$SamplesSusceptible <- sample_times(data)[2]}
   
  return(data.quality)
}

get.step<-function(days_len){
  mid <- days_len/2
   
  if (mid<1){
    return(0)
  }
  else{
    return(1 + get.step(mid) )
  }
}


