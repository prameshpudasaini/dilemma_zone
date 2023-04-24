import pandas as pd

import plotly.express as px
import plotly.io as pio
pio.renderers.default = 'browser'

path = r"D:\GitHub\match_events\data\20221206_ISR_19Ave\data_SSC.txt"
df = pd.read_csv(path, sep = '\t')

df.TimeStamp = pd.to_datetime(df.TimeStamp, format = '%Y-%m-%d %H:%M:%S.%f').sort_values()
df.Parameter = df.Parameter.astype(str)

# plot detection points for subset
det_order = [9, 27, 10, 28, 11, 29, 6, 5]
cat_order = {'SSC': ['YY', 'YR', 'RR', 'RG', 'GG', 'GY', 'GR'],
             'Parameter': det_order,
             'Lane': ['R', 'M', 'L', 'LT']}
ssc_color = {'YY': 'orange',
             'YR': 'brown',
             'RR': 'red',
             'RG': 'black',
             'GG': 'green',
             'GY': 'limegreen',
             'GR': 'navy'}

# individual detector
fig = px.scatter(
    df, x = 'TimeStamp', y = 'Parameter',
    color = 'SSC',
    category_orders = cat_order,
    color_discrete_map = ssc_color
).update_traces(marker = dict(size = 10))

fig.show()
fig.write_html(r"D:\GitHub\match_events\output\20221206_ISR_19Ave_EDA_SSC.html")

# # lane-by-lane
# px.scatter(
#     df, x = 'TimeStamp', y = 'Lane',
#     color = 'SSC',
#     symbol = 'Det',
#     category_orders = cat_order,
#     color_discrete_map = ssc_color
# ).update_traces(marker = dict(size = 8)).show()