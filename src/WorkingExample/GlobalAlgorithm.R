#######################################################################
#                                                        
#                  Global algorithm                                 
#                 - apply meta-analyses methods to output of local algorithm                       
#                                                        
#                  Author: Egil A.J. Fischer                              
#                  Contact: e.a.j.fischer@uu.nl                             
#                  Creation date: 13-12-2021
#######################################################################

## If a package is installed, it will be loaded. If any 
## are not, the missing package(s) will be installed 
## from CRAN and then loaded.

# ## First specify the packages of interest
packages = c("tidyverse",
             "meta",
             "metafor")

## Now load or install&load all
package.check <- lapply(
  packages,
  FUN = function(x) {
    if (!require(x, character.only = TRUE)) {
      install.packages(x, dependencies = TRUE)
      library(x, character.only = TRUE)
    }
  }
)

library(meta)
library(metafor)
library(tidyverse)


#combine.estimates of glm's
combine.estimates.glm <- function(local.output,
                              select.treatment = "All",
                              sub.group = c()){
  #get the means and standard errors
  estimates = NULL;
  for(i in c(1:length(local.output)))      {
        estimates <- rbind(estimates,
                           cbind(data.frame(mean = summary(local.output[[i]]$estimation)$coefficients[,1],
                                            se  = summary(local.output[[i]]$estimation)$coefficients[,2],
                                            
                                 treatment =row.names(summary(local.output[[i]]$estimation)$coefficients)),
                                 study = i))
  }
  #select treatments
  if(select.treatment == "reference" | select.treatment == "control" ){
    estimates <- estimates%>%filter(treatment == "(Intercept)")
    
   }
   else if(treatment!= "All")
     estimates <- estimates%>%filter(treatment == select.treatment)
  
  #if sub.group analysis indicates some sort of additional information for example from meta-data on study design
   if(length(sub.group)>0){
     if(length(sub.group)!= length(estimates$treatment)) stop("lengths of sub.group and estimates not equal")
     estimates$treatment <- mapply(paste,
                                   estimates$treatment,sub.group)
     
   }
    
  # #simply only use the intercepts
  metaout<- metagen(TE =  estimates$mean,
                    seTE = estimates$se,
                    studlab = estimates$study,
                    subgroup = estimates$treatment,
                    fixed = FALSE)
  
  return(metaout)
}
