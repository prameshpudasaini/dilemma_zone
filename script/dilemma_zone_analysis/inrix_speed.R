library(RODBC)
library(data.table)
library(readr)

source("ignore/keys.R")

# collect data from SQL server
query <- read_file("script/dilemma_zone_analysis/query_speed.sql")
DT <- as.data.table(sqlQuery(getSQLConnection('STL5'), query))

# 85th percentile speed
quantile(DT$speed, probs = seq(0, 1, 0.05))
