import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

os.chdir(r"D:\GitHub\dilemma_zone")

col_names = ['tt_ideal_stop', 'tt_ideal_run', 'precision', 'recall', 'f1_score']
df = pd.read_csv("data/calibration/sensitivity.txt", sep = '\t', names = col_names)

X = np.asarray(df.tt_ideal_stop, dtype = np.float32)
Y = np.asarray(df.tt_ideal_run, dtype = np.float32)
Z = np.asarray(df.f1_score, dtype = np.float32)

fig = plt.figure(figsize = (12, 12))
ax = fig.add_subplot(projection = '3d')
ax.scatter(X, Y, Z, color = 'black')
ax.view_init(azim = 45, elev = 10)

lsize, lpad = 18, 16
ax.set_xlabel('Ideal travel time to stop (sec)', fontsize = lsize, labelpad = lpad)
ax.set_ylabel('Ideal travel time to run (sec)', fontsize = lsize, labelpad = lpad)
ax.set_zlabel('F1 score', fontsize = lsize, labelpad = lpad)

tsize, tpad = 16, 8
ax.xaxis.set_tick_params(labelsize = tsize, pad = tpad)
ax.yaxis.set_tick_params(labelsize = tsize, pad = tpad)
ax.zaxis.set_tick_params(labelsize = tsize, pad = tpad)

plt.savefig('output/match_events_sensitivity_analysis.png', dpi = 600)
plt.show()
