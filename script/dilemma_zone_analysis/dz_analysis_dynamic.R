library(data.table)
library(plotly)
library(ggplot2)

df <- fread("data/dz_analysis/dz_processed_bulk.txt", sep = '\t')

# update stop/run decision levels
df[, decision := fcase(decision == 0, 'stop', decision == 1, 'run')]

# specify weekday and TOD levels
weekday_levels <- c('weekday', 'weekend')
TOD_levels <- c('morning', 'midday', 'evening', 'overnight')
zone_levels <- c('should-stop', 'should-go', 'dilemma', 'option')

# add weekday and TOD levels
df[, weekday := factor(weekday, levels = weekday_levels)]
df[, TOD := factor(TOD, levels = TOD_levels)]
df[, zone := factor(zone, levels = zone_levels)]

# specify plot colors for points
col_stop <- 'black'
col_go <- 'forestgreen'
col_dilemma <- 'blue'
col_option <- 'red'

# specify plot color for lines
col_dz1 <- 'red'
col_oz <- 'darkorange'
col_dz2p <- 'blue'
col_dz2t <- 'forestgreen'

# specify shapes for stop/run
shape_run_stop <- c(3, 20)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# plot: all actuation by Type I decision rule
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

dx_max <- max(df$dx)

plot0 <- ggplot(df) + 
    geom_point(aes(Xi, velocity, color = zone, shape = decision), size = 1) +
    scale_color_manual(values = c(col_stop, col_go, col_dilemma, col_option),
                       labels = c('Should-stop', 'Should-go', 'Dilemma', 'Option')) + 
    scale_shape_manual(values = shape_run_stop, labels = c('Run', 'Stop')) + 
    scale_x_continuous(breaks = seq(0, dx_max, 100)) +
    xlab("Distance from intersection stop line (ft)") +
    ylab("Velocity (mph)") +
    labs(color = 'Type I decision rule:',
         shape = 'Actual decision taken:') + 
    theme_minimal() + 
    theme(axis.text = element_text(size = 14),
          axis.title = element_text(size = 16, face = 'bold'),
          legend.title = element_text(size = 16, face = 'bold'),
          legend.text = element_text(size = 14),
          legend.position = 'top',
          legend.box = 'vertical',
          legend.spacing = unit(0, 'cm'),
          legend.box.margin = margin(0, 0, 0, 0, 'cm'),
          panel.border = element_rect(color = 'black', fill = NA),
          strip.text = element_text(size = 16, face = 'bold'),
          plot.background = element_rect(fill = 'white', color = 'NA')) + 
    guides(shape = guide_legend(override.aes = list(size = 5, alpha = 1)),
           color = guide_legend(override.aes = list(size = 5, alpha = 1)))
plot0

ggsave("output/dz_analysis/actuation_distance_velocity_bulk.png",
       plot = plot0,
       units = "cm",
       width = 29.7,
       height = 21,
       dpi = 600)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# plot: actuation events by TOD & day of week
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

df1 <- copy(df)

# add sample size by weekday and TOD
count <- df1[, .N, by = .(weekday, TOD)]
df1[, counts_TOD_weekday := .N, by = .(weekday, TOD)]
df1[, lab_TOD_weekday := paste0('n = ', counts_TOD_weekday)]

df_wday <- df1[weekday == 'weekday', ] # dataset for weekdays
df_wend <- df1[weekday == 'weekend', ] # dataset for weekends

plotDZTOD <- function(xdf, xx){
    dx_max = max(xdf$dx)
    
    plot <- ggplot(xdf, aes(Xi, velocity, color = zone, shape = decision)) + 
        geom_point(size = 1) + 
        facet_wrap(~TOD, labeller = labeller(TOD = c('morning' = 'a) Morning',
                                                     'midday' = 'b) Mid-day', 
                                                     'evening' = 'c) Evening', 
                                                     'overnight' = 'd) Overnight'))) + 
        geom_text(aes(xx, 17, label = lab_TOD_weekday), color = 'black', size = 5) +
        scale_color_manual(values = c(col_stop, col_go, col_dilemma, col_option),
                           labels = c('Should-stop', 'Should-go', 'Dilemma', 'Option')) + 
        scale_shape_manual(values = shape_run_stop, labels = c('Run', 'Stop')) + 
        scale_x_continuous(breaks = seq(0, dx_max, 100)) + 
        xlab("Distance from intersection stop line (ft)") +
        ylab("Velocity (mph)") + 
        labs(color = 'Type I decision rule:',
             shape = 'Actual decision taken:') + 
        theme_minimal() + 
        theme(axis.text = element_text(size = 14),
              axis.title = element_text(size = 16, face = 'bold'),
              legend.title = element_text(size = 16, face = 'bold'),
              legend.text = element_text(size = 14),
              legend.position = 'top',
              legend.box = 'vertical',
              legend.spacing = unit(0, 'cm'),
              legend.box.margin = margin(0, 0, 0, 0, 'cm'),
              panel.border = element_rect(color = 'black', fill = NA),
              panel.background = element_rect(color = 'NA'),
              strip.text = element_text(size = 16, face = 'bold'),
              plot.background = element_rect(fill = 'white', color = 'NA')) + 
        guides(shape = guide_legend(override.aes = list(size = 5)),
               color = guide_legend(override.aes = list(size = 5)))
    
    return(plot)
}

plot_DZ_TOD_wday <- plotDZTOD(df_wday, 500)
plot_DZ_TOD_wend <- plotDZTOD(df_wend, 475)

ggsave("output/dz_analysis/actuation_DZ_TOD_weekday.png",
       plot = plot_DZ_TOD_wday,
       units = "cm",
       width = 29.7,
       height = 21,
       dpi = 600)

ggsave("output/dz_analysis/actuation_DZ_TOD_weekend.png",
       plot = plot_DZ_TOD_wend,
       units = "cm",
       width = 29.7,
       height = 21,
       dpi = 600)
