library(data.table)
library(ggplot2)
library(plotly)

# confidence interval = (point estimate) +- (critical value) * (standard error)
getConfidenceInterval <- function(x, alpha) {
    n <- length(x)
    xbar <- mean(x)
    s <- sd(x)
    
    crit_value <- qt(1 - alpha/2, df = n-1)
    stnd_error <- s / sqrt(n)
    
    margin <- crit_value * stnd_error
    
    lower_int <- round(xbar - margin, 2)
    upper_int <- round(xbar + margin, 2)
    
    return(list(lower_int, upper_int))
}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# advance det to left-turn rear det
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

DT_left <- fread("data/calibration/calibration_left_turn.txt") # data frame

data_left <- c(DT_left$V1) # vector of travel times
summary(data_left)

# update data by removing outliers
data_left <- sort(data_left) |> head(-1)
summary(data_left)

# normality test
shapiro.test(data_left) 
shapiro.test(log(data_left))

getConfidenceInterval(data_left, 0.05)

round(mean(data_left), 1) # parameter for left

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# advance det to stop-bar det
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

DT <- fread("data/calibration/calibration_thru.txt")

DT_stop <- DT[V3 == 'stop']
DT_go <- DT[V3 == 'go']

data_stop <- c(DT_stop$V1)
summary(data_stop)
getConfidenceInterval(data_stop, 0.05)
getConfidenceInterval(data_stop, 0.01)

data_go <- c(DT_go$V1)
summary(data_go)
getConfidenceInterval(data_go, 0.05)
getConfidenceInterval(data_go, 0.01)

plot_ly(DT, type = 'box', x = ~V2, y = ~V1, boxmean = TRUE)
plot_ly(DT, type = 'box', x = ~V3, y = ~V1, boxmean = TRUE)

round(mean(data_stop), 1) # parameter for stop
round(mean(data_go), 1) # parameter for go

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# t-test for comparing means
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ggplot(DT_stop, aes(V1)) + geom_histogram()
ggplot(DT_go, aes(V1)) + geom_histogram()

# normality test
shapiro.test(data_stop)
shapiro.test(data_go)

# At the level 0.05 test, the p-value is greater, implying that there is evidence to
# believe that the distribution of the data is not significantly different from the
# normal distribution.

t.test(data_stop, data_go)
t.test(log(data_stop), log(data_go))
wilcox.test(data_stop, data_go)

DT_YLR <- DT[V2 %in% c('GY', 'YY')]
DT_RLR <- DT[V2 %in% c('YR', 'RR')]

data_ylr <- (DT_YLR$V1)
data_rlr <- (DT_RLR$V1)

shapiro.test(data_ylr)
shapiro.test(data_rlr)

t.test(data_ylr, data_rlr)
t.test(log(data_ylr), log(data_rlr))
wilcox.test(data_ylr, data_rlr)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# t-test for comparing means of car-following
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

data_follow_T <- c(DT[V4 == 'T']$V1)
data_follow_F <- c(DT[V4 == 'F']$V1)

summary(data_follow_T)
getConfidenceInterval(data_follow_T, 0.05)

summary(data_follow_F)
getConfidenceInterval(data_follow_F, 0.05)

shapiro.test(data_follow_T)
shapiro.test(data_follow_F)

t.test(data_follow_T, data_follow_F)
wilcox.test(data_follow_T, data_follow_F)
