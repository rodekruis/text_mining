# Author: Michael Osunga 
# Date: 7th, May 2019

# Task: Historical flood data analysis

# Table of contents
# 1. House keeping
# 2. Loading dataframes
# 3. Data cleaning
# 4. Parsing county, subcounty and ward names on 'Comments' strings


## 1. Housekeeping ------------------------------------------------------------

## clear workspace
rm(list = ls(all = TRUE))

# installing and reading multiple packages
packages <- c("tidyverse", "dplyr","ggplot2", "anytime", "lubridate", "rgdal")

ipak <- function(pkg){
  new.pkg <- pkg[!(pkg %in% installed.packages()[, "Package"])]
  if (length(new.pkg)) 
    install.packages(new.pkg, dependencies = TRUE)
  sapply(pkg, require, character.only = TRUE)
}

ipak(packages)

# setting working directory
setwd("E:/ICHA/Projects/flood_impact/data/raw_data") 

## 2. Loading flood dataframes and Kenya shapefile ----------------------------

floodWRA<- read.csv("Flood Impact Database Main.csv")
floodEoC<- read.csv("Floods Historical data.csv")
desinventar <- read.csv("Desinventar_kenya_impact_data_v1.csv",stringsAsFactors = FALSE)

# loading shapefiles
KENadmin<-readOGR(dsn="E:/ICHA/Projects/flood_impact/data/raw_data/shapefiles/KenAdminData", layer="cooksKE_data_v6")
KENadmin.old <- readOGR(dsn="E:/ICHA/Geospatial Data/KEN_adm", layer = "KEN_adm5")

#  cleaning new admin shapefile
KENadmin@data <- KENadmin@data %>%
  dplyr::select(1:3) %>%
  mutate_if(is.factor,as.character)

# cleaning old admin shapefile
KENadmin.old@data<-KENadmin.old@data %>%
  dplyr::select(matches("NAME")) %>%
  mutate_if(is.factor, as.character) %>%
  mutate_if(is.character, str_trim)

# coercing old official administrative names to vectors
admin5.names<-as.character(unique(KENadmin.old@data$NAME_5))
admin4.names<-as.character(unique(KENadmin.old@data$NAME_4))
admin3.names<-as.character(unique(KENadmin.old@data$NAME_3))

# coercing official administrative names to vectors
county.names<-as.character(unique(KENadmin@data$countis))
subcounty.names<-as.character(unique(KENadmin@data$subcnts))
ward.names<-as.character(unique(KENadmin@data$wards))

## 3. Data cleaning -----------------------------------------------------------

# cleaning WRA data
floodWRA.clean <- floodWRA %>%
  dplyr::select(1:14) %>%
  mutate_if(is.factor,as.character) %>%
  mutate_if(is.character, str_trim) %>%
  filter(!X24.04.18=="") %>%
  mutate(X24.04.18.1=as.character(X24.04.18.1),
         X24.04.18.1=lubridate::dmy(X24.04.18.1),
         Kiaoni..Makueni.County.=as.character(Kiaoni..Makueni.County.)) %>%
  rename(date=X24.04.18.1,
         Location=Kiaoni..Makueni.County.,
         Houses.Destroyed=X150)
  
# setting variable names based on value names in row 10
my.names <- floodWRA.clean[10,]
my.names<-as.character(my.names)
colnames(floodWRA.clean) <- my.names

# further cleaning
floodWRA.cleaned<-floodWRA.clean[-10,] %>%
  mutate_if(is.character, str_to_title) %>%
  filter(`Type (Riverine, flash, fluctuating lake levels, Dam failure)` %in% c("Flash",
                                                                               "Flash Floods",
                                                                               "Flash Flood",
                                                                               "Flood", "Riverine/Flash Flood")) %>%
  mutate(Start=lubridate::dmy(Start)) %>%
  rename(Date=Start,
         Event=`Type (Riverine, flash, fluctuating lake levels, Dam failure)`,
         Deaths=`Human losses (Dead)`,
         Directly.affected=`Total Affected Residents`,
         Lost.Livestock=`Livestock losses`,
         Affected.Area=`Affected Area (km2)`,
        Losses..Local= `Estimated Damage (Ksh)`)
         
# exporting dataframe as .csv        
write.csv(floodWRA.cleaned, "floodWRA_data.csv", row.names = F)

# cleaning Desinventar data
desinventar.clean <- desinventar %>%
  dplyr::select(Date,County,Event,Location,Deaths:Damages.in.roads.Mts,Comments) %>%
  mutate_if(is.character,str_trim) %>%
  mutate_if(is.character, str_to_title) %>%
  mutate(Location=gsub("Flash Reported In |Floods |Floods In |Flash Floods In| Sub-County| Area|At |Flash Floods At| District| Division| Town| Village| village| Sub County| Subcounty| County| Location|Sub-Location| Sub-Location","",Location)) %>%
  mutate(Date=lubridate::dmy(Date)) %>%
  filter(!Location=="") %>%
  mutate_if(is.character,str_trim) %>%
  mutate_if(is.character, str_to_title) %>%
  mutate(source="Desinventar") %>%
  mutate_if(is.numeric,replace_na, replace = NA) %>%
  mutate(Directly.affected=gsub("[^0-9]","",Directly.affected),
         Relocated=gsub("[^0-9]","",Relocated))


# cleaning EoC data
floodEoC.clean <- floodEoC %>%
  mutate(Injured=MINOR_CAS+CRITICAL_CAS) %>%
  dplyr::select(DATE_TIME,COUNTIES,TYPE,SCENE,DEAD,Injured,MISSING,HH.AFFECTED,DAMAGE,RESCUED,SITUATION) %>%
  rename(Date=DATE_TIME,
         County=COUNTIES,
         Event=TYPE,
         Location=SCENE,
         Deaths=DEAD,
         Missing=MISSING,
         Houses.Destroyed=HH.AFFECTED,
         Houses.Damaged=DAMAGE,
         Evacuated=RESCUED,
         Comments=SITUATION) %>%
  mutate_if(is.factor, as.character) %>%
  mutate_if(is.character,str_trim) %>%
  mutate_if(is.character,str_to_title) %>%
  mutate(Date=lubridate::dmy(Date)) %>%
  mutate(Location=gsub("Rainfall Situation | Constituency| Coun|Situation Update|Mudslide |Mudslide Incident |Landslides |Landslide |Lightning Strikes |Lightening Strike | Sub-County| Sub Counties| Flash Floods|In |Flash Flood In |Floods |Floods In |Flash Floods |Flash Floods In |At | County| Sub County| Sub Location| Sub -County| Sub-Location| Flash Floods In","",Location)) %>%
  mutate(source="EoC") %>%
  mutate(Houses.Damaged=gsub("[^0-9]"," ",Houses.Damaged),
         Houses.Destroyed=gsub("[^0-9]"," ",Houses.Destroyed)) %>%
  tidyr::separate(col = Houses.Damaged, 
                  into = "Houses.Damaged",
                  sep = " ",
                  remove = FALSE) %>%
  mutate(Directly.affected=0,
         Indirectly.Affected=0,
         Relocated=0,
         Losses..Local=0,
         Education.centers=0,
         Damages.in.crops.Ha.=0,
         Lost.Cattle=0,
         Lost.Goats=0,
         Lost.Livestock=0)

# selecting desinventar variables based on variable names in EoC data
desinventar.clean2 <- desinventar.clean %>%
  dplyr::select(names(floodEoC.clean))

# appending EoC and desinventar dataframes
EocDesinventar<-rbind(floodEoC.clean,desinventar.clean2) %>%
  mutate_if(is.character,str_trim) %>%
  mutate_if(is.numeric,replace_na, replace = NA) %>%
  dplyr::select(1:10,13:21,12:13,11)


# Note that geocoding was done in python


# 4. Parsing county, subcounty and ward names on 'Comments' strings -----------

# loading the geocoded dataframe
EocDesinventarGeocoded<-read.csv("EocDesinventar_data3_geocoded.csv", stringsAsFactors = F)

# further cleaning of county names
EocDesinventar.admin.coded<-EocDesinventarGeocoded %>%
  mutate(Date1=anydate(Date),
         Date3=if_else(is.na(Date1),lubridate::dmy(Date),Date1)) %>% 
  dplyr::select(-Date, -Date1,-X) %>%
  rename(Date=Date3) %>%
  dplyr::select(23,1:22) %>%
  mutate(County=if_else(County=="Taita-Taveta","Taita Taveta",
                        if_else(County=="Keiyo-Marakwet","Elgeyo-Marakwet",
                                if_else(County=="Tana-River","Tana River",
                                        if_else(str_detect(County,"Muran"),"Muranga",
                                                if_else(County=="Uasin-Gishu","Uasin Gishu",County)))))) %>%
  mutate(Comments=str_to_title(Comments),
         Country="Kenya") %>%
  
  # parsing county, subcounty and ward names on 'Comments' strings
  mutate(Wards.comments=str_extract(Comments, paste(ward.names, collapse = "|"))) %>%
  mutate(Subcounty.comments=str_extract(Comments, paste(subcounty.names, collapse = "|"))) %>%
  mutate(County.comments=str_extract(Comments, paste(county.names, collapse = "|"))) 

# checking for NAs in newly created admin variables
sapply(EocDesinventar.admin.coded, function(x) sum(is.na(x)))

# subsetting flood events with 0 lats and lons
flood_events_lats0<-EocDesinventar.admin.coded %>%
  filter(Long==0.0000000)

# subsetting flood events where County name is None
EocDesinventarGeocoded_None <- EocDesinventar %>%
  filter(County=="None") %>%
  mutate(County=if_else(County=="Taita-Taveta","Taita Taveta",
                        if_else(County=="Keiyo-Marakwet","Elgeyo-Marakwet",
                                if_else(County=="Tana-River","Tana River",
                                        if_else(str_detect(County,"Muran"),"Muranga",
                                                if_else(County=="Uasin-Gishu","Uasin Gishu",County)))))) %>%
  mutate(Comments=str_to_title(Comments),
         Country="Kenya",
         Lat=0,
         Long=0) %>%
  # parsing county, subcounty and ward names on 'Comments' strings
  mutate(Wards.comments=str_extract(Comments, paste(ward.names, collapse = "|"))) %>%
  mutate(Subcounty.comments=str_extract(Comments, paste(subcounty.names, collapse = "|"))) %>%
  mutate(County.comments=str_extract(Comments, paste(county.names, collapse = "|"))) 

# appending the 2 dataframes 
EocDesinventarGeocoded.master<-rbind(EocDesinventarGeocoded_None,EocDesinventar.admin.coded)

# checking for NAs amongst variables
sapply(EocDesinventarGeocoded.master, function(x) sum(is.na(x)))

# checking for wards that did not parse by source
(wards.x<-EocDesinventarGeocoded.master %>%
  filter(is.na(Wards.comments)) %>%
  dplyr::select(Wards.comments,source) %>%
  group_by(source) %>%
  count(source))

# checking for sub-counties that did not parse by source
(county.x<-EocDesinventarGeocoded.master %>%
  filter(is.na(Subcounty.comments)) %>%
  dplyr::select(Subcounty.comments,source) %>%
  group_by(source) %>%
  count(source))

# exporting dataframe to .csv
write.csv(EocDesinventarGeocoded.master,"E:/ICHA/Projects/flood_impact/data/clean_data/EocDesinventar_master.csv", row.names = FALSE) 


admin5.names<-as.character(unique(KENadmin.old@data$NAME_5))
admin4.names<-as.character(unique(KENadmin.old@data$NAME_4))
admin3.names<-as.character(unique(KENadmin.old@data$NAME_3))

floodWRA.cleaned.geocoded <- floodWRA.cleaned %>%
  mutate(Location=str_to_title(Location)) %>%
# parsing county, subcounty and ward names on 'Comments' strings
mutate(Wards=str_extract(Location, paste(ward.names, collapse = "|"))) %>%
  mutate(Subcounty=str_extract(Location, paste(subcounty.names, collapse = "|"))) %>%
  mutate(County=str_extract(Location, paste(county.names, collapse = "|"))) %>%
  mutate(admin3=str_extract(Location,paste(admin3.names, collapse = "|"))) %>%
  mutate(admin4=str_extract(Location,paste(admin4.names, collapse = "|"))) %>%
  mutate(admin5=str_extract(Location,paste(admin5.names, collapse = "|"))) %>%
  dplyr::select(Location,County,Subcounty,Wards,admin3,admin4,admin5)

#### END OF SCRIPT
