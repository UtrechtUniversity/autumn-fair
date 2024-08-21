#########################################################
#                                                        
#                  Example using SUMMERFAIR framework                                 
#                  Local and global algorithms 
#                                                        
#                  Author: Egil A.J. Fischer                               
#                  Contact: e.a.j.fischer@uu.nl                             
#                  Creation date: 7-3-2022                         
#########################################################

#load required packages (install if required)####
lapply(
  c("ggplot2",
    "tidyverse",
    "rje",
    "readxl",
    "magrittr"),
  FUN = function(x) {
    if (!require(x, character.only = TRUE)) {
      install.packages(x, dependencies = TRUE)
      library(x, character.only = TRUE)
    }
  }
)


# source required R scripts  ####
# scripts should be in subfolder "src/WorkingExample" 
source("./src/WorkingExample/DataInterpretationRules.R")    #Data manipulation rules are pre- or user defined
source("./src/WorkingExample/LocalAlgorithm.R")             #Estimation methods
source("./src/WorkingExample/ExperimentalPlots.R")          #Data visualisation
source("./src/WorkingExample/GlobalAlgorithm.R")            #Meta analysis

# get pre-saved data ####
dataE<- readRDS("./src/WorkingExample/dataE.RDS")
dataF<- readRDS("./src/WorkingExample/dataF.RDS")

#run local algorithm for each data set ####
rm(localE, localF)
#run analysis over data set E with different levels of mixing and results is coded 0/1 
localE <- analyseTransmission(inputdata = dataE,           #data set
                              rule = rule.sincefirst, #rule to determine infection status
                              var.id = c("sample_result"),#variable defining infection status
                              method = "mll",              #estimation method
                              #cutoff = 0,                  #cutoff value for infection status
                              preventError = TRUE,         #TRUE = remove entries with > 1 case but FOI = 0
                              covars = "treatment",        #co-variates 
                              reference = "control",       #reference category for multivariable estimation
                              control = "Control")               #value of control treatment
localE$estimation
localE$data
#run analysis over data set F with no levels of mixing and measurements that are either a detectionLimit or a value
localF<- analyseTransmission(inputdata = dataF,            #data set
                             rule = rule.sincefirst.cutoff.detectionLimit,  #rule to determine infection status
                             cutoff = "0",                 #define the cutoff value
                             var.id = c("sample_measure"),  #variable defining infection status
                             method = "glm",               #estimation method
                             codesposnegmiss = c("+","-","NA"), #values determining infection status pos, neg of missing
                             preventError = TRUE,          #TRUE = remove entries with > 1 case but FOI = 0
                             covars = "treatment",         #co-variates 
                             reference = "control",        #reference category for multivariable estimation
                             control = "aangezuurd water",                 #value of control treatment
                             inoMarker = "I")                
localF$estimation
View(localF$data)

#run analysis over data set F with no levels of mixing and measurements that are either a detectionLimit or a value
localF.alternative<- analyseTransmission(inputdata = dataF,            #data set
                             rule = rule.asis.cutoff.detectionLimit,  #rule to determine infection status
                             cutoff = "0",                 #define the cutoff value
                             var.id = c("sample_measure"),  #variable defining infection status
                             method = "glm",               #estimation method
                             codesposnegmiss = c("+","-","NA"), #values determining infection status pos, neg of missing
                             preventError = TRUE,          #TRUE = remove entries with > 1 case but FOI = 0
                             covars = "treatment",         #co variates 
                             reference = "control",        #reference category for multivariable estimation
                             control = "aangezuurd water",                 #value of control treatment
                             inoMarker = "I")                
localF.alternative$estimation


#Use input files
localE.configfile <- get.local.transmission(dataE,
                                            config.file =  "./src/WorkingExample/summerfair_config_E.yaml")

localF.configfile <- get.local.transmission(dataF,
                                            config.file =  "./src/WorkingExample/summerfair_config_F.yaml")


#Visualize the data
raw.plot(localF$data)
test <- input.plot(transform.data.for.plot(localF$data),sampling.times = seq(0,3,.1))

#output estimation
localF$estimation

#combine estimates of control group with standard meta-analysis techniques ####
#method only takes glm results up to now
metaana <- combine.estimates.glm(list(localF.alternative,localF.configfile$analysis),
                             select.treatment = "control") 
print(metaana)
forest(metaana)
funnel(metaana,studlab=TRUE,contour = c(0.9, 0.95, 0.99))
