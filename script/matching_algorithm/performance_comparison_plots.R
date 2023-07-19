library(data.table)
library(ggplot2)
library(plotly)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# results of sensitivity analysis from proposed algorithm
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

col_names <- c('tt_ideal_stop', 'tt_ideal_run', 'Precision', 'Recall', 'F1_score')
data <- fread('data/calibration/sensitivity.txt', col.names = col_names)

# 3D scatter plot
plot_ly(
    data, type = 'scatter3d', 
    x = ~tt_ideal_stop, y = ~tt_ideal_run, z = ~F1_score,
    mode = 'markers', marker = list(size = 2.5, color = 'black')
) |> 
    layout(scene = list(xaxis = list(title = 'Ideal travel time to stop (sec)'),
                        yaxis = list(title = 'Ideal travel time to run (sec)'),
                        zaxis = list(title = 'F1 score')))

# contour plot
ggplot(data, aes(tt_ideal_stop, tt_ideal_run, z = F1_score)) +
    geom_contour(bins = 20)

# heatmap
fig1 <- ggplot(data, aes(tt_ideal_stop, tt_ideal_run, fill = F1_score)) + 
    geom_tile(color = 'white', lwd = 0.2, linetype = 1) + 
    xlab('Ideal travel time to stop (sec)') + 
    ylab('Ideal travel time to run (sec)') + 
    scale_x_continuous(breaks = seq(5, 8, 0.5)) + 
    scale_y_continuous(breaks = seq(3.5, 6, 0.5)) + 
    scale_fill_gradient(low = 'white', high = 'blue') +
    guides(fill = guide_colorbar(title = 'F1 score', barwidth = 1, barheight = 20)) + 
    theme_classic() + 
    theme(axis.text = element_text(size = 14),
          axis.title = element_text(size = 16),
          legend.title = element_text(size = 16),
          legend.text = element_text(size = 14))
fig1

ggsave("output/match_events_sensitivity_analysis_heatmap.png",
       plot = fig1,
       units = "cm",
       width = 29.7,
       height = 21,
       dpi = 600)

# melt data frame
data <- melt(
    data, 
    measure.vars = c('Precision', 'Recall', 'F1_score'),
    variable.name = 'metric',
    value.name = 'value'
)

plot_ly(
    data, type = 'scatter3d', 
    x = ~tt_ideal_stop, y = ~value, z = ~tt_ideal_run, color = ~metric,
    mode = 'markers', marker = list(size = 2)
)

# metrics from proposed method
precision <- 0.92 
recall <- 0.9109 
f1_score <- 0.9154
n <- 10

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# results of sensitivity analysis from comparison algorithms
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

df <- data.table(
    algorithm = rep('Proposed', n),
    eff_veh_length = seq(18, 27, 1),
    precision = rep(precision, n),
    recall = rep(recall, n),
    f1_score = rep(f1_score, n)
)

dt <- fread("data/calibration/sensitivity_ding_lu_algorithms.csv", header = TRUE)

DT <- rbindlist(list(dt, df))
DT <- melt(
    DT, 
    measure.vars = c('precision', 'recall', 'f1_score'),
    variable.name = 'metric',
    value.name = 'value'
)
DT[, algorithm := as.factor(algorithm)]

fig2 <- ggplot(DT, aes(eff_veh_length, value, linetype = metric, shape = algorithm)) + 
    geom_point(size = 2.5) + 
    geom_line(alpha = 0.9) + 
    xlab('Effective vehicle length (ft)') + 
    ylab('Value of performance metric') + 
    scale_x_continuous(breaks = seq(17, 28, 1)) + 
    scale_y_continuous(breaks = seq(0.5, 0.95, 0.05)) + 
    scale_shape_manual(values = c(0, 1, 2), 
                         labels = c("Ding's method", "Lu's method", 'Proposed method')) +
    scale_linetype_manual(values = c(3, 2, 1), 
                          labels = c('Precision', 'Recall', 'F1 score')) + 
    theme_classic() + 
    theme(axis.text = element_text(size = 14),
          axis.title = element_text(size = 16),
          legend.title = element_blank(),
          legend.text = element_text(size = 14),
          legend.position = 'top')
fig2

ggsave("output/calibration_performance_comparison.png",
       plot = fig2,
       units = "cm",
       width = 29.7,
       height = 21,
       dpi = 600)
