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

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# plot: dynamic DZ boundary by hour and day of week
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

df2 <- copy(df)

df2[, counts_weekday_hour := .N, by = .(weekday, hour)]
df2[, lab_weekday_hour := paste0('n = ', counts_weekday_hour)]

sdf <- copy(df2)[, .(hour, dx, weekday, dz1_start, dz1_end, oz_start, oz_end,
                     dz2_prob_start, dz2_prob_end, dz2_tt_start, dz2_tt_end, 
                     lab_weekday_hour)]

sdf <- melt(
    sdf,
    id.vars = c('hour', 'dx', 'weekday', 'lab_weekday_hour'),
    measure.vars = c('dz1_start', 'dz1_end', 
                     'oz_start', 'oz_end',
                     'dz2_prob_start', 'dz2_prob_end', 
                     'dz2_tt_start', 'dz2_tt_end')
)

sdf[, zone := fcase(like(variable, 'dz1'), 'DZ1',
                    like(variable, 'oz'), 'OZ',
                    like(variable, 'dz2_prob'), 'DZ2_Prob',
                    like(variable, 'dz2_tt'), 'DZ2_TT')]

sdf[, boundary := fcase(like(variable, 'start'), 'Start',
                        like(variable, 'end'), 'End')]

# specify levels
zone_levels <- c('DZ1', 'OZ', 'DZ2_Prob', 'DZ2_TT')
boundary_levels <- c('Start', 'End')

# update levels
sdf[, zone := factor(zone, levels = zone_levels)]
sdf[, boundary := factor(boundary, levels = boundary_levels)]

# update Type II travel-time based for mph to ft/s conversion
sdf[zone == 'DZ2_TT', value := value * 5280/3600]

dx_max <- max(sdf$value, na.rm = TRUE)

plot2 <- ggplot(sdf, aes(hour, value, group = interaction(zone, boundary), 
                         color = zone, linetype = boundary)) + 
    geom_point(size = 1.2, shape = 1) + 
    geom_line() +
    facet_wrap(~weekday,
               labeller = labeller(weekday = c('weekday' = 'a) Weekdays',
                                               'weekend' = 'b) Weekends'))) + 
    scale_color_manual(values = c(col_dz1, col_oz, col_dz2p, col_dz2t),
                       labels = c('Type I', 'Option', 'Type II (probabilistic)',
                                  'Type II (travel time-based)')) + 
    scale_linetype_manual(values = c('solid', 'longdash')) + 
    scale_x_continuous(breaks = seq(0, 23, 3)) + 
    scale_y_continuous(breaks = seq(0, dx_max, 50)) + 
    xlab("Hour of day") +
    ylab("Distance from intersection stop line (ft)") + 
    labs(color = 'Zone type:',
         linetype = 'Zone boundary:') + 
    theme_minimal() + 
    theme(axis.text = element_text(size = 14),
          axis.title = element_text(size = 16, face = 'bold'),
          legend.title = element_text(size = 16, face = 'bold'),
          legend.text = element_text(size = 14),
          legend.position = 'top',
          legend.box = 'vertical',
          legend.spacing = unit(0, 'cm'),
          legend.key.width = unit(1.4, 'cm'),
          legend.box.margin = margin(0, 0, 0, 0, 'cm'),
          panel.border = element_rect(color = 'black', fill = NA),
          panel.grid.minor = element_blank(),
          strip.text = element_text(size = 16, face = 'bold'),
          plot.background = element_rect(fill = 'white', color = 'NA')) + 
    guides(color = guide_legend(override.aes = list(shape = NA, linewidth = 2)))
plot2

ggsave("output/dz_analysis/DZ_boundary_TOD_weekend_updated.png",
       plot = plot2,
       units = "cm",
       width = 29.7,
       height = 21,
       dpi = 600)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# plot: dynamic DZ boundary by approach speed
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

df3 <- copy(df)
df3[, dilemma := 'No']
df3[zone == 'dilemma' | zone == 'option' | (decision == 'run' & zone  == 'should-stop'), dilemma := 'Yes']
df3[, dilemma := factor(dilemma, levels = c('Yes', 'No'))]
df3[, .N, by = dilemma]

# type I dilemma zone
df3[zone == 'dilemma', ddz1_start := round(mean(Xs), 0), by = as.factor(velocity)]
df3[zone == 'dilemma', ddz1_end := round(mean(Xc), 0), by = as.factor(velocity)]

# option zone
df3[zone == 'option', doz_start := round(mean(Xc), 0), by = as.factor(velocity)]
df3[zone == 'option', doz_end := round(mean(Xs), 0), by = as.factor(velocity)]

# type II dilemma zone: travel time based
df3[, ddz2_tt_start := round(5.5*velocity*5280/3600, 0)]
df3[, ddz2_tt_end := round(2.5 * velocity*5280/3600, 0)]

# # type II dilemma zone: probabilistic
# speed_cuts <- seq(15, 60, 5)
# speed_labels <- paste0('below_', seq(20, 60, 5))
# df3[, speed_group := cut(cdf$velocity, breaks = speed_cuts, right = TRUE, labels = speed_labels)]
# df3[, .N, by = speed_group]

# count_vel_group <- copy(cdf)
# count_vel_group[, velocity := as.factor(velocity)]
# count_vel_group <- count_vel_group[, .(counts = .N), by = velocity][order(velocity)]
# count_vel_group[, perc := round(counts / sum(counts) * 100, 2)]
# count_vel_group[, cum_perc := cumsum(perc)]

getTypeIIDZ <- function(){
    # count number of stopping vehicles by dx
    dt <- copy(df3)[decision == 'stop', ]
    dx_max <- max(dt$dx)
    n <- nrow(dt)
    
    dt[, dx := as.factor(dx)]
    dt <- dt[, .(count = .N), by = dx]
    dt[, dx := as.numeric(as.character(dx))]
    dt <- dt[order(dx)]
    
    # percentage of vehicles stopping in each dx
    dt[, perc_stop := round(count / n * 100, 4)]
    dt$count <- NULL
    
    # join with new data frame of sequential dx
    sdf <- data.table(dx = seq(0, dx_max, 10))
    jdf <- dt[sdf, on = .(dx)]
    
    # replace NA values with 0
    jdf[is.na(jdf)] <- 0
    
    # compute cumulative percentage of stopping at each dx
    jdf[, cum_perc_stop := round(cumsum(perc_stop), 1)]
    
    # linear interpolation of distance where 10% and 90% vehicles stop
    model <- lm(dx ~ cum_perc_stop, data = jdf)
    stop10 <- round(approx(jdf$cum_perc_stop, jdf$dx, xout = 10)$y, 0)
    stop90 <- round(approx(jdf$cum_perc_stop, jdf$dx, xout = 90)$y, 0)
    
    return(list(stop10 = stop10, stop90 = stop90))
}

stop10 <- round(getTypeIIDZ()$stop10, 0)
stop90 <- round(getTypeIIDZ()$stop90, 0)

df3[, ddz2_prob_start := stop90]
df3[, ddz2_prob_end := stop10]

dx_max <- max(df3$dx)
speed_min <- min(df3$velocity)
speed_max <- max(df3$velocity)

plot4 <- ggplot(df3) + 
    geom_point(aes(Xi, velocity, color = zone, shape = decision), size = 1, alpha = 0.4) +
    geom_line(aes(ddz1_start, velocity), linetype = 'solid', color = col_dz1, size = 1) + 
    geom_line(aes(ddz1_end, velocity), linetype = 'solid', color = col_dz1, size = 1) +
    geom_line(aes(doz_start, velocity), linetype = 'solid', color = col_oz, size = 1) + 
    geom_line(aes(doz_end, velocity), linetype = 'solid', color = col_oz, size = 1) +
    geom_ribbon(aes(xmin = ddz2_tt_end, xmax = ddz2_tt_start, y = velocity), fill = 'grey', alpha = 0.6) + 
    scale_color_manual(values = c(col_stop, col_go, col_dilemma, col_option),
                       labels = c('Should-stop', 'Should-go', 'Dilemma', 'Option')) + 
    scale_shape_manual(values = shape_run_stop, labels = c('Run', 'Stop')) + 
    scale_x_continuous(breaks = seq(0, dx_max, 100)) +
    xlab("Distance from intersection stop line (ft)") +
    ylab("Velocity (mph)") +
    labs(color = 'Type I decision rule:',
         shape = 'Actual decision taken:') + 
    annotate('rect', xmin = stop10, xmax = stop90, ymin = speed_min, ymax = speed_max,
             fill = 'blue', alpha = 0.1) + 
    annotate('text', x = 490, y = 42, label = 'Type II (probabilistic)', size = 5, fontface = 'bold') + 
    annotate('text', x = 95, y = 15, label = 'Type II (travel time-based)', size = 5, fontface = 'bold') + 
    annotate('text', x = 145, y = 26.5, label = 'Option', size = 5, fontface = 'bold') + 
    annotate('text', x = 350, y = 60.5, label = 'Type I', size = 5, fontface = 'bold') + 
    # geom_segment(aes(x = 430, y = 43, xend = 390, yend = 41), arrow = arrow(length = unit(0.4, 'cm'))) + 
    # geom_segment(aes(x = 75, y = 21, xend = 100, yend = 27), arrow = arrow(length = unit(0.4, 'cm'))) + 
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
plot4

ggsave("output/dz_analysis/DZ_boundary_velocity_updated.png",
       plot = plot4,
       units = "cm",
       width = 29.7,
       height = 21,
       dpi = 600)
