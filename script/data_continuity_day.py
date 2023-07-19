import os
import pandas as pd
from datetime import datetime

import plotly.express as px
import plotly.io as pio
pio.renderers.default = 'browser'

os.chdir(r"D:\SynologyDrive\Data\High Resolution Events Data\Indian School")

# read file
year, month = 2023, 3
file = str(year) + '_' + str(month).zfill(2)
df = pd.read_csv(file + "_ISR_19Ave.txt", sep = '\t')

# filter intersection, convert timestamp
ID = 46
df = df[df.DeviceID == ID]
df.drop('DeviceID', axis = 1, inplace = True)
df.TimeStamp = pd.to_datetime(df.TimeStamp, format = '%m-%d-%Y %H:%M:%S.%f')
df = df[df.TimeStamp.dt.month == month]

# filter day
day = 27
df = df[df.TimeStamp.dt.day == day]

# detector configuration for wb
det = {'adv': (27, 28, 29), 
       'stop': (9, 10, 11), 
       'left': (5, 6)}
det_set = det['adv'] + det['stop'] + det['left']

# filter events and detector parameters
fdf = df.copy(deep = True)
fdf = fdf[(df.EventID == 82) & (df.Parameter.isin(det_set))]
fdf.Parameter = fdf.Parameter.astype(str)

# plot data continuity for whole dataset
det_order = {'Parameter': sorted(det)}
fig = px.scatter(
    fdf, x = 'TimeStamp', y = 'Parameter', 
    category_orders = det_order
)
fig.show()

file = str(year) + str(month).zfill(2) + str(day).zfill(2)
output_fig = os.path.join(r"D:\GitHub\match_events\output\actuation_html", file + "_raw.html")
fig.write_html(output_fig)

# filter timestamp for data subset
start = datetime(year, month, day, 14, 15)
end = datetime(year, month, day, 18, 45)
sdf = df[(df.TimeStamp >= start) & (df.TimeStamp <= end)]

output_period = str(start.hour).zfill(2) + str(start.minute).zfill(2) + '_' + str(end.hour).zfill(2) + str(end.minute).zfill(2)

output_file = os.path.join(r"D:\GitHub\match_events\ignore\data", file + '_' + output_period + ".txt")
sdf.to_csv(output_file, sep = '\t', index = False)
