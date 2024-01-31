library(data.table)
library(plotly)
library(ggplot2)

df <- fread("data/dz_analysis/dz_processed_bulk.txt", sep = '\t')

# update stop/run decision levels
df[, decision := fcase(decision == 0, 'stop', decision == 1, 'run')]

summary(df$velocity)
quantile(df$velocity, probs = seq(0, 1, 0.05))

summary(df$PRT)
quantile(df$PRT, probs = seq(0, 1, 0.05))

sdf <- copy(df)[decision == 'stop', ]
rdf <- copy(df)[decision == 'run', ]

summary(sdf$acceleration)
quantile(sdf$acceleration, probs = seq(0, 1, 0.05))

summary(rdf$acceleration)
quantile(rdf$acceleration, probs = seq(0, 1, 0.05))
