data#########################################################
#                                                        
#                  PLot experimental data for transmission experiments                                
#                                                        
#                  Author:   E.A.J. Fischer                            
#                  Contact:  e.a.j.fischer@uu.nl                             
#                  Creation date: 8-6-'23                         
#########################################################

#load libraries #############################

library(ggplot2)
library(reshape2)



############################
# plotting functions       #
############################
#plot the raw data when in an untidy format
raw.plot <-function(raw.data){
  raw.data.melt<- reshape2::melt(raw.data,
                                 id.vars = list("host_id",
                                                "level1",
                                                "level2",
                                                "treatment",
                                                "inoculationStatus"),
                                 variable.name = "time")
  raw.data.melt$ndpch <- reshape2::colsplit(raw.data.melt$time,"[.]",c("ndpch","X"))[,1]
  raw.data.melt$ndpch <-as.numeric(raw.data.melt$ndpch)
  raw.data.melt$delta <- 0;
  for(id in unique(raw.data.melt$bird.id)){
    raw.data.melt[raw.data.melt$bird.id== id,]$delta <-
      raw.data.melt[raw.data.melt$bird.id== id,]$ndpch-c(0,head(raw.data.melt[raw.data.melt$bird.id== id,]$ndpch,-1))  
  }
  
  
  return(raw.data.melt)
}


###################################
# change data to be able to plot  #
###################################

transform.data.for.plot <- function(sirdata){
  out <-data.frame(host_id =c(),
                   inoculationStatus=c(),
                   group =c(),
                   treatment=c(), 
                   lastneg = c(),
                   firstpos=c(),
                   lastpos=c(),
                   firstrec=c(),
                   lastObs=c())
  #iterate data
  for(i in unique(sirdata$host_id))
  {
          host.data <- sirdata%>%filter(host_id ==i);
          out <- rbind(out,
                 data.frame(host_id = i,
                            inoculationStatus = host.data[1,"inoculationStatus"],
                            group = paste0(host.data[1,"level1"],"_",host.data[1,"level2"]),
                            treatment = host.data[1,"treatment"], 
                            lastneg = max(0,max(host.data[host.data$sir == 0,]$times)),#select last negative time
                            firstpos = max(0,min(host.data[host.data$sir == 2,]$times)),#select first positive time
                            lastpos = max(0,max(host.data[host.data$sir == 2,]$times)),#select last positive time
                            firstrec = max(0,min(host.data[host.data$sir == 3,]$times)),#select first recovered time
                            lastObs = max(host.data$times)) #last observation
    )
    
  }
  return(out)
}

#plot the input from a transmission experiment
#data require the following headings: group, animal_id, inoc,lastneg, firstpos, lastpos, firstrec, lastObs
input.plot <- function(in.data, 
                       color_scheme = c("#999999","#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"), 
                       period.labels = c("Negative", 'Neg->Pos', 'Positive', 'Pos-> Neg',"Negative again"),
                       sampling.times = NULL){
  plot.data <-in.data[,c(1:4)];#only select indicators
    #replace all negative numbers for lastObs
  in.data$lastneg[in.data$lastneg<0 ]<- in.data$lastObs[in.data$lastneg<0 ]
  in.data$firstpos[in.data$firstpos<0 ]<- in.data$lastObs[in.data$firstpos<0 ]
  in.data$lastpos[in.data$lastpos<0 ]<- in.data$lastObs[in.data$lastpos<0 ]
  in.data$firstrec[in.data$firstrec<0 ]<- in.data$lastObs[in.data$firstrec<0 ]
  
  #replace infinity for appropriate values
  in.data[is.infinite(in.data$lastneg),]$lastneg<-in.data[is.infinite(in.data$lastneg),]$firstpos
  in.data[is.infinite(in.data$firstpos),]$firstpos<-in.data[is.infinite(in.data$firstpos),]$lastpos
  in.data[is.infinite(in.data$lastpos),]$lastpos<-in.data[is.infinite(in.data$lastpos),]$lastObs
  in.data[is.infinite(in.data$firstrec),]$firstrec<-in.data[is.infinite(in.data$firstrec),]$lastObs
  
  #make sure that lastneg<=firspos<=lastpos<=firstrec
  in.data$firstpos <- mapply(max,in.data$firstpos, in.data$lastneg);
  in.data$lastpos <-mapply(max,in.data$lastpos,in.data$firstpos);
  in.data$firstrec <-mapply(max,in.data$firstrec,in.data$lastpos);

  
  #replace real time with interval
  if(!is.null(sampling.times)){
  plot.data$neg1 <- in.data$lastneg;
  plot.data$negpos <- in.data$firstpos - in.data$lastneg;
  plot.data$pos <-in.data$lastpos - in.data$firstpos;
  plot.data$posneg2 <- in.data$firstrec - in.data$lastpos;
  plot.data$neg2 <-  in.data$lastObs-in.data$firstrec;}else
  {
    #take into account the sampling times
    plot.data$neg1 <- in.data$lastneg-min(sampling.times);
    plot.data$negpos <- in.data$firstpos - in.data$lastneg;
    plot.data$pos <-in.data$lastpos - in.data$firstpos;
    plot.data$posneg2 <- in.data$firstrec - in.data$lastpos;
    plot.data$neg2 <-  in.data$lastObs-in.data$firstrec;
  }
  
  
  #melt down
  plot.data <- melt(plot.data,id = c("host_id","inoculationStatus","group","treatment"))
  
 #create plots per treatment
  plots <- list();
  for(i in unique(plot.data$treatment)){
    y_breaks <- if(is.null(sampling.times)){c(0:max(plot.data$value[!is.infinite(plot.data$value)]))}else{sampling.times}
  plots[[length(plots)+1]]<- ggplot(data = plot.data[plot.data$treatment == i,]%>%
                   arrange(group)%>%
                   arrange(desc(host_id)))+
    geom_bar(aes(y = value, x = as.factor(host_id), 
                 fill = factor(variable,levels = c("neg1","negpos","pos","posneg2","neg2")[c(5,4,3,2,1)])),stat= 'identity')+
    coord_flip()+ 
    scale_fill_manual('State', 
                     values = color_scheme,
                     labels = period.labels[c(5,4,3,2,1)])+ylab("Days post challenge")+
    xlab("host ID")+
    ggtitle(i)+
    scale_y_continuous(breaks = y_breaks )+
    scale_x_discrete(limits = rev)+
          if(length(unique(plot.data$group))>1){facet_grid(group + inoculationStatus ~. , scales = "free_y")}
  }
  
  return(list(plots = plots, data = plot.data))
}

# 
# #plot the input from a transmission experiment and the distribution of estimated unobserved data 
# #data require the following headings: group, animal_id, inoc,lastneg, firstpos, lastpos, firstrec, lastObs
# estimated.times.plot <- function(stan.fit, input.data){
#   #extract estimated transitions
#   x<-data.frame(extract(stan.fit)$infT)
#   names(x) <- c(input.data$animal_id)
#   ex.data.infT <- reshape2::melt(x)
#   ex.data.infT$group <- rep(input.data$group, each = length(x[,1]))
#   ex.data.infT$treatment <- rep(input.data$treatment, each = length(x[,1]))
#   
#   x<-data.frame(extract(stan.fit)$latT)
#   names(x) <- c(input.data$animal_id)
#   ex.data.latT <- reshape2::melt(x)
#   
#   ex.data.latT$group <- rep(input.data$group, each = length(x[,1]))
#   ex.data.latT$treatment <- rep(input.data$treatment, each = length(x[,1]))
#   
#  
#   
#   #add extracted estimation times to the input plot
#   p <- input.plot(input.data)$plot+
#      geom_violin(data = ex.data.infT, aes(x =variable, y = value), colour = "gray", fill = "yellow")+
#      geom_violin(data = ex.data.latT, aes(x =variable, y = value), colour = "gray", fill ="green")+
#       coord_flip()+
#      scale_x_discrete()+
#      scale_y_discrete(limits = rev)+
#      xlab("Animals")+
#      ylab("time")+
#      if(length(unique(input.data$group))>1){facet_grid(group ~ treatment, scales = "free_y")}
#    return(list(plot = p))
# }
# 
# 
# #plot prior versus the posterior distributions 
# #requires the following input: prior-distributions, prior-parameters, parameter names, stan.fit object
# prior_posterior.plot <- function(prior.dist, prior.par, par.name, stan.fit){
#   #extract estimated transitions
#   d<-data.frame(k = extract(stan.fit)[par.name])
#   dist <- get(prior.dist[par.name])
#   pr.dist <- function(x){dist(x,  unlist(prior.par[par.name])[1],  unlist(prior.par[par.name])[2])}
#   pp.plot <- ggplot()  +
#     geom_density(aes(x = d[,par.name], y = ..density..), fill = "grey", alpha = .7, size = 0.5)   +
#     geom_area(aes(x = x, y = y), 
#               data = data.frame(x = seq(0,1.5 * max(d[,par.name]),max(d[,par.name])/30), 
#                                 y = sapply(X = seq(0,1.5 * max(d[,par.name]),max(d[,par.name])/30), FUN = pr.dist)),
#               size =1,
#               colour = "red",
#               fill ="red",
#               alpha = 0.1)  + xlab(par.name) 
#   
#   #return plot
#   return(pp.plot)
# }
# 
# #plot all
# prior_posterior.plots <- function(prior.dist, prior.par,  stan.fit, print.plot = T){
#   plots <- list();
#   pars <- names(prior.dist)
#   for(p.n in pars)
#   {
#     plots[[p.n]] <- prior_posterior.plot(prior.dist, prior.par, p.n, stan.fit);
#   }
#   if(print.plot){pp.grid <- plot_grid(plotlist = plots);
#     return(pp.grid)}
#   return(plots)
#   
# }
