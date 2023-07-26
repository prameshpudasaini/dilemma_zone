import os
import pandas as pd
import numpy as np

import plotly.express as px
import plotly.io as pio
pio.renderers.default = 'browser'

os.chdir(r"D:\GitHub\dilemma_zone")

# parameters
yellow_interval = 3.6

v85 = 38 # 85th percentile speed computed using INRIX data
v85 = round(v85 * 5280/3600, 2)

dist_stop_stop = 10 # distance between stop line and stop bar
len_stop_det = 40 # length of stop bar det
dist_adv_stop = 260 # distance between adv and stop-bar det

space_stop_stop = dist_stop_stop + len_stop_det
space_adv_stop = dist_stop_stop + len_stop_det + dist_adv_stop

crit_TUY_stop = 1.5 # critical TUY at stop bar det

# =============================================================================
# function to compute Type I DZ parameters (Wei et al., 2011)
# =============================================================================

# minimum perception reaction time
def minPerceptionReactionTime(v0):
    prt = round(0.445 + 21.478/v0, 2)
    return prt

# maximum deceleration rate    
def maxDecelerationRate(v0):
    dec = round(np.exp(3.379 - 36.099/v0) - 9.722 + 429.692/v85, 2)
    return -dec

# maximum acceleration rate
def maxAccelerationRate(v0):
    acc = round(-27.91 + 760.258/v0 + 0.266*v85, 2)
    # if acc < 0: acc = 0
    # if acc > 6: acc = 6
    return acc

# minimum stopping distance
def minStoppingDistance(v0, prt, acc):
    Xs = round(v0*prt + (v0**2) / (2*(abs(acc))), 0)
    return Xs

# maximum clearing distance
def maxClearingDistance(v0, prt, acc):
    Xc = round(v0*yellow_interval + 0.5*(acc)*((yellow_interval - prt)**2), 0)
    return Xc
    
# =============================================================================
# dilemma zone parameters
# =============================================================================

# read data
df = pd.read_csv("data/dz_analysis/matched_events_dataset_bulk.txt", sep = '\t')

# filter outliers: low stopping travel times
tt_stop_lower_limit = df[df.decision == 0].travel_time.quantile(q = 0.02)
df.drop(df[((df.decision == 0) & (df.travel_time < tt_stop_lower_limit))].index, inplace = True)

# filter outliers: high running travel times
tt_run_upper_limit = df[df.decision == 1].travel_time.quantile(q = 0.98)
df.drop(df[((df.decision == 1) & (df.travel_time > tt_run_upper_limit))].index, inplace = True)

# drop redundant columns
df.drop('occ_ratio', axis = 1, inplace = True)

# compute approach velocity based on travel time
df['velocity'] = round(dist_adv_stop / df.travel_time, 2)

# categorize arrival at advance det
df.loc[df.AIY_adv > df.TUY_adv, 'arrival_adv'] = 'before'
df.loc[df.AIY_adv < df.TUY_adv, 'arrival_adv'] = 'after'

# categorize arrival at stop-bar det
df.loc[df.AIY_stop > df.TUY_stop, 'arrival_stop'] = 'before'
df.loc[df.AIY_stop < df.TUY_stop, 'arrival_stop'] = 'after'

# vehicle's position at yellow onset (beyond advance detector)
df.loc[(df.arrival_adv == 'after'), 'Xi'] = round(space_adv_stop + df.AIY_adv * df.velocity, 0)

# vehicle's position at yellow onset (between stop-bar and advance det)
df.loc[((df.arrival_adv == 'before') & (df.arrival_stop == 'after')), 'Xi'] = round(space_stop_stop + df.AIY_stop * df.velocity, 0)

# vehicle's position at yellow onset (between stop line and stop-bar det)
df.loc[((df.arrival_adv == 'before') & (df.arrival_stop == 'before')), 'Xi'] = round(space_stop_stop - df.TUY_stop * df.velocity, 0)

# remove Xi's less than 0
df.drop(df[df.Xi <= 0].index, inplace = True)

# round Xi to nearest 10
df['dx'] = (df.Xi + 9) // 10 * 10

# compute prt, acceleration, deceleration
df['PRT'] = minPerceptionReactionTime(df.velocity)

df.loc[df.decision == 0, 'acceleration'] = maxDecelerationRate(df.velocity) # stopping
df.loc[df.decision == 1, 'acceleration'] = maxAccelerationRate(df.velocity) # running

# compute min stopping and max clearing distances
df.loc[df.decision == 0, 'Xs'] = minStoppingDistance(df.velocity, df.PRT, df.acceleration)
df.loc[df.decision == 1, 'Xs'] = minStoppingDistance(df.velocity, df.PRT, 10)

df.loc[df.decision == 1, 'Xc'] = maxClearingDistance(df.velocity, df.PRT, df.acceleration)
df.loc[df.decision == 0, 'Xc'] = maxClearingDistance(df.velocity, df.PRT, 6)

# compute zone vehicle's position is in
df.loc[(((df.Xi <= df.Xc) & (df.Xc <= df.Xs)) | ((df.Xi <= df.Xs) & (df.Xs <= df.Xc))), 'zone'] = 'should-go'
df.loc[(((df.Xi >= df.Xc) & (df.Xc >= df.Xs)) | ((df.Xi >= df.Xs) & (df.Xs >= df.Xc))), 'zone'] = 'should-stop'
df.loc[((df.Xc < df.Xi) & (df.Xi < df.Xs)), 'zone'] = 'dilemma'
df.loc[((df.Xs < df.Xi) & (df.Xi < df.Xc)), 'zone'] = 'option'

# covert unit of velocity
df.velocity = round(df.velocity * 3600/5280, 0)

# drop redundant columns
df.drop(df.columns[:12], axis = 1, inplace = True)

# add weekday, weekend categories
df['year'] = 2023
df['TimeStamp'] = pd.to_datetime(dict(year = df.year, month = df.month, day = df.day, hour = df.hour))
df['dayofweek'] = df.TimeStamp.dt.dayofweek # day of week
df['weekday'] = 'weekday' # all rows as weekdays
df.loc[df.dayofweek.isin([5, 6]), 'weekday'] = 'weekend' # update weekends
df.loc[((df.month == 1) & (df.day.isin([1, 2, 16]))), 'weekday'] = 'weekend' # holidays
df.drop(['year', 'TimeStamp', 'dayofweek'], axis = 1, inplace = True)

# add time of day categories
df['TOD'] = 'overnight'
df.loc[df.hour.isin([5, 6, 7, 8]), 'TOD'] = 'morning'
df.loc[df.hour.isin([9, 10, 11, 12, 13, 14]), 'TOD'] = 'midday'
df.loc[df.hour.isin([15, 16, 17, 18]), 'TOD'] = 'evening'

# print(df[['decision', 'zone']].groupby('zone').decision.value_counts())

# =============================================================================
# type I dilemma zone
# =============================================================================

# dilemma zone
ddf = df.copy(deep = True)
ddf = ddf[ddf.zone == 'dilemma'].groupby(['weekday', 'hour'])['Xs', 'Xc'].mean().round(0).reset_index()
ddf.rename(columns = {'Xs': 'dz1_start', 'Xc': 'dz1_end'}, inplace = True)
df = df.merge(ddf, how = 'outer') # merge DZ to dataframe

# option zone
odf = df.copy(deep = True)
odf = odf[odf.zone == 'option'].groupby(['weekday', 'hour'])['Xs', 'Xc'].mean().round(0).reset_index()
odf.rename(columns = {'Xc': 'oz_start', 'Xs': 'oz_end'}, inplace = True)
df = df.merge(odf, how = 'outer') # merge DZ to dataframe

# =============================================================================
# type II dilemma zone
# =============================================================================

# type II dilemma zone: probabilistic method
def stoppingPercentile(weekday, hour):
    df2 = df.copy(deep = True)
    
    # filter stopping decisions, weekday, TOD
    fdf = df2[((df2.decision == 0) & (df2.weekday == weekday) & (df2.hour == hour))]
    n = len(fdf)
    
    # count number of vehicles stopping by dx
    cdf = fdf.dx.value_counts().reset_index()
    cdf.columns = ['dx', 'counts']
    cdf.sort_values('dx', inplace = True)
    
    # percentage of vehicles stopping by dx
    cdf['perc_stop'] = round(cdf.counts.div(n)*100, 4)
    cdf.drop('counts', axis = 1, inplace = True)
    
    # dummy dataframe
    dx_max = int(max(cdf.dx))
    dx_range = list(range(0, dx_max + 10, 10))
    temp = pd.DataFrame(dx_range, columns = ['dx'])
    
    # merge temp and cdf
    mdf = temp.merge(cdf, how = 'outer')
    mdf.perc_stop.fillna(0, inplace = True)
    mdf['cum_perc_stop'] = mdf.perc_stop.cumsum()
    
    # compute 10%, 90% stopping percentile by interpolation
    stop_perc = np.interp([10, 90], mdf.cum_perc_stop, mdf.dx)
    stop_perc = list(np.around(stop_perc / 5, decimals = 0)*5)
    
    return stop_perc

# store DZ start, end parameters in dataframe
result = []
for i in list(df.weekday.unique()):
    for j in list(df.hour.unique()):
        stop10 = stoppingPercentile(i, j)[0]
        stop90 = stoppingPercentile(i, j)[1]
        result.append([i, j, stop10, stop90])

rdf = pd.DataFrame([i for i in result], columns = ['weekday', 'hour', 'dz2_prob_end', 'dz2_prob_start'])

# merge dataframe
df = df.merge(rdf, how = 'outer')

# type II dilemma zone: TT-based method
tdf = df.copy(deep = True)
tdf = tdf.groupby(['weekday', 'hour']).velocity.mean().round(0).reset_index()
tdf.rename(columns = {'velocity': 'avg_hour_velocity'}, inplace = True)
tdf['dz2_tt_end'] = round(tdf.avg_hour_velocity * 2.5, 0)
tdf['dz2_tt_start'] = round(tdf.avg_hour_velocity * 5.5, 0)
df = df.merge(tdf, how = 'outer') # merge DZ to dataframe

df.to_csv("data/dz_analysis/dz_processed_bulk.txt", sep = '\t', index = False)
