import pandas as pd
from datetime import datetime

import plotly.express as px
import plotly.io as pio
pio.renderers.default = 'browser'

path = r"D:\GitHub\match_events\data\20221206_ISR_19Ave\data_raw.txt"
df = pd.read_csv(path, sep = '\t')
print(df.shape)

df.TimeStamp = pd.to_datetime(df.TimeStamp, format = '%m-%d-%Y %H:%M:%S.%f')

# detector configuration
det_wb_thru_adv = (27, 28, 29)
det_wb_thru_stop = (9, 10, 11)
det_wb_lt_stop = (5, 6)
det = det_wb_thru_adv + det_wb_thru_stop + det_wb_lt_stop

# filter events and detector parameters
fdf = df.copy(deep = True)
fdf = fdf.loc[(fdf.EventID == 82) & (fdf.Parameter.isin(det))]
fdf.Parameter = fdf.Parameter.astype(str)

# plot data continuity for whole dataset
det_order = {'Parameter': sorted(det)}
px.scatter(
    fdf, x = 'TimeStamp', y = 'Parameter', 
    category_orders = det_order
).show()

# filter timestamp for test period: December 6, 2022; 7:45 to 8:15
from_time = datetime(2022, 12, 6, 7, 45)
to_time = datetime(2022, 12, 6, 8, 15)
ndf = df[(df.TimeStamp >= from_time) & (df.TimeStamp <= to_time)]

# ndf.to_csv(r"D:\GitHub\match_events\data\20221206_ISR_19Ave\data_process.txt", sep = '\t', index = False)

# detection count by lane
sdf = ndf.copy(deep = True)
sdf = sdf.loc[(sdf.EventID == 82) & (sdf.Parameter.isin(det))]
sdf.Parameter = sdf.Parameter.astype(str)
print(sdf.Parameter.value_counts().sort_values())

# plot detection points for subset
px.scatter(
    sdf, x = 'TimeStamp', y = 'Parameter', 
    category_orders = det_order
).show()
