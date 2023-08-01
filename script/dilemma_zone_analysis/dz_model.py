import os
import pandas as pd
import numpy as np

import plotly.express as px
import plotly.io as pio
pio.renderers.default = 'browser'

from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.svm import LinearSVC

os.chdir(r"D:\GitHub\dilemma_zone")

# read data
df = pd.read_csv("data/dz_analysis/dz_processed_bulk.txt", sep = '\t')
# print(df[['decision', 'zone']].groupby('zone').decision.value_counts())

# create boolean dilemma variable
df['dilemma'] = 0 # no dilemma
df.loc[((df.zone.isin(['dilemma', 'option'])) | ((df.zone == 'should-stop') & (df.decision == 1))), 'dilemma'] = 1

fig = px.scatter_3d(df, x = 'hour', y = 'Xi', z = 'velocity', color = 'dilemma')
fig.update_traces(marker_size = 2).show()

# convert hour to string
df.hour = 'H' + df.hour.astype(str)

# convert decision to categorical variable
df.loc[df.decision == 0, 'Decision'] = 'stop'
df.loc[df.decision == 1, 'Decision'] = 'run'

# select columns
df = df[['hour', 'weekday', 'velocity', 'Xi', 'Xc', 'Xs', 'Decision', 'dilemma']]

# convert categorical columns
cat_cols = ['hour', 'weekday', 'Decision', 'dilemma']
df[cat_cols] = df[cat_cols].astype('category')

ndf = df.copy(deep = True)[['hour', 'weekday', 'Decision']]

temp = ndf.hour.value_counts().sort_values(ascending = False)

# one-hot encoding
ohe = OneHotEncoder(handle_unknown = 'ignore')
feature_array = ohe.fit_transform(df[cat_cols[:-1]]).toarray()
print(ohe.categories_)

feature_labels = ohe.categories_
feature_labels = np.array(feature_labels).ravel()



