library(data.table)
library(plotly)
library(ggplot2)

DT <- fread("data/dz_analysis/dz_processed_bulk.txt", sep = '\t')
DT <- DT[decision == 0, .(dx, decision)]
DT$decision <- NULL

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Type II dilemma zone
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# count number of stopping vehicles by dx
dt <- copy(DT)
dt[, dx := as.factor(dx)]
dt <- dt[, .(count = .N), by = dx]
dt[, dx := as.numeric(as.character(dx))]
dt <- dt[order(dx)]

# percentage of vehicles stopping in each dx
dt[, perc_stop := round(count / nrow(DT) * 100, 4)]
dt$count <- NULL

# join with new data frame of sequential dx
max_dx <- max(dt$dx)
sdf <- data.table(dx = seq(0, 620, 10))
jdf <- dt[sdf, on = .(dx)]

# replace NA values with 0
jdf[is.na(jdf)] <- 0

# compute cumulative percentage of stopping at each dx
jdf[, cum_perc_stop := round(cumsum(perc_stop), 1)]

# plot: cumulative percentage of stopping by distance
plot_ly(jdf, type = 'scatter', 
        x = ~dx, y = ~cum_perc_stop,
        mode = 'lines')

# linear interpolation of distance where 10% and 90% vehicles stop
model <- lm(dx ~ cum_perc_stop, data = jdf)
stop10 <- round(approx(jdf$cum_perc_stop, jdf$dx, xout = 10)$y, 0)
stop90 <- round(approx(jdf$cum_perc_stop, jdf$dx, xout = 90)$y, 0)

# plot
fig1 <- ggplot(jdf, aes(dx, cum_perc_stop)) + 
    geom_line(size = 1.2) + 
    geom_segment(aes(x = stop10, xend = stop10, y = 0, yend = 100), color = 'red', linetype = 5, size = 1) + 
    geom_segment(aes(x = stop90, xend = stop90, y = 0, yend = 100), color = 'forestgreen', linetype = 5, size = 1) + 
    geom_segment(aes(x = 0, xend = 40, y = 90, yend = 90), color = 'forestgreen', linetype = 5, size = 1) + 
    geom_segment(aes(x = 0, xend = 40, y = 85, yend = 85), color = 'red', linetype = 5, size = 1) +
    annotate('text', x = 50, y = 90, label = "Type II DZ start", size = 6, alpha = 0.8, hjust = 0) + 
    annotate('text', x = 50, y = 85, label = "Type II DZ end", size = 6, alpha = 0.8, hjust = 0) + 
    annotate('text', x = stop10, y = 103, label = "265'", alpha = 0.8, size = 6) +
    annotate('text', x = stop90, y = 103, label = "465'", alpha = 0.8, size = 6) + 
    xlab('Distance from stop line (ft)') + 
    ylab('Cumulative % of vehicles stopping') + 
    scale_x_continuous(breaks = seq(0, max_dx, 50)) + 
    scale_y_continuous(breaks = seq(0, 100, 20)) + 
    theme_classic() + 
    theme(axis.text = element_text(size = 14),
          axis.title = element_text(size = 16))
fig1

fig1 <- ggsave("output/type_II_DZ.png",
       plot = fig1,
       units = "cm",
       width = 29.7,
       height = 21,
       dpi = 600)
