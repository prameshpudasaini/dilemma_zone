import os
import pandas as pd
from datetime import datetime

import plotly.express as px
import plotly.io as pio
pio.renderers.default = 'browser'

# os.chdir(r"D:\SynologyDrive\Data\High Resolution Events Data\Indian School")

# # list of files
# files = list([
#     '2023_01_ISR_19Ave',
#     '2023_02_ISR_19Ave',
#     '2023_03_ISR_19Ave',
#     '2023_04_ISR_19Ave',
#     '2023_05_ISR_19Ave'
# ])

# # read each file
# df = []
# for file in files:
#     sdf = pd.read_csv(file + '.txt', sep = '\t')
#     sdf = sdf[sdf.DeviceID == 46] # select 19th Ave
#     df.append(sdf)

# # merge files into one df
# df = pd.concat(df)
# df.to_csv(r"D:\GitHub\dilemma_zone\ignore\dz_data\dz_data.txt", sep = '\t', index = False)

os.chdir(r"D:\GitHub\dilemma_zone")

# read data
df = pd.read_csv("ignore/dz_data/dz_data.txt", sep = '\t')
df.drop('DeviceID', axis = 1, inplace = True)
df.TimeStamp = pd.to_datetime(df.TimeStamp, format = '%m-%d-%Y %H:%M:%S.%f')

# unique months in df
months = list(df.TimeStamp.dt.month.unique())
months = months[1:] # remove December
df = df[df.TimeStamp.dt.month.isin(months)] # update df for months

# add month & day
df['month'] = df.TimeStamp.dt.month
df['day'] = df.TimeStamp.dt.day

# pairs of months and days
days = {}
for month in months:
    days[month] = list(df[df.month == month].day.unique())
    
# =============================================================================
# write events to html file
# =============================================================================

# signal & detector configuration
phase, on = 2, 82
sig = [1, 8, 10]
det = [9, 27, 10, 28, 11, 29, 5, 6]
det_order = {'Parameter': det}

# filter df for phase events
pdf = df.copy(deep = True)[(df.EventID.isin(sig) & (df.Parameter == phase))]
pdf.Parameter = pdf.Parameter.astype(str)

# filter df for detection events
adf = df.copy(deep = True)[((df.EventID == on) & (df.Parameter.isin(det)))]
adf.Parameter = adf.Parameter.astype(str)

# write events to html file for each month-day pairs
for key, value in days.items():
    # filter signal & detection dfs for month
    month_sig_df = pdf[pdf.month == key]
    month_det_df = adf[adf.month == key]

    for val in value:
        # filter signal & detection dfs for day
        day_sig_df = month_sig_df[month_sig_df.day == val]
        day_det_df = month_det_df[month_det_df.day == val]

        # plot data continuity for whole dataset
        fig_sig = px.scatter(day_sig_df, x = 'TimeStamp', y = 'EventID')
        fig_det = px.scatter(day_det_df, x = 'TimeStamp', y = 'Parameter', category_orders = det_order)
        
        file = '2023' + str(key).zfill(2) + str(val).zfill(2)
        output_sig = os.path.join("ignore/data_continuity_check", file + "_sig.html")
        output_det = os.path.join("ignore/data_continuity_check", file + "_det.html")
        fig_sig.write_html(output_sig)
        fig_det.write_html(output_det)
        
# =============================================================================
# create data set for January, February
# =============================================================================

for month in months[0:2]:
    mdf = df.copy(deep = True)
    mdf = mdf[mdf.month == month]
    
    for day in days[month]:
        ddf = mdf.copy(deep = True)[mdf.day == day]
        hours = list(ddf.TimeStamp.dt.hour.unique())
        
        for hour in hours:
            hdf = ddf.copy(deep = True)[ddf.TimeStamp.dt.hour == hour]
            
            c1 = (hour == 2)
            c2 = ((month == 1) & (day == 1) & (hour == 13))
            c3 = ((month == 2) & (day == 17) & (hour == 11))
            c4 = ((month == 2) & (day == 21) & (hour == 6))
            
            if (c1 | c2 | c3 | c4):
                pass
            else:
                hdf.drop(['month', 'day'], axis = 1, inplace = True)
                
                file = '2023' + str(month).zfill(2) + str(day).zfill(2) + '_' + str(hour).zfill(2)
                hdf.to_csv(os.path.join("ignore/dz_data/raw", file + "_raw.txt"), sep = '\t', index = False)
