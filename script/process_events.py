import os
import pandas as pd
import numpy as np

import plotly.express as px
import plotly.io as pio
pio.renderers.default = 'browser'

os.chdir(r"D:\GitHub\match_events")

class Vector():
    def __init__(self, data):
        self.data = data
    def __repr__(self):
        return repr(self.data)
    def __sub__(self, other):
        return list((a-b).total_seconds() for a, b in zip(self.data, other.data))

# select period and file
def getFileName(year, month, day, from_hour, from_min, to_hour, to_min):
    return(str(year) + str(month).zfill(2) + str(day).zfill(2) + '_' +
           str(from_hour).zfill(2) + str(from_min).zfill(2) + '_' +
           str(to_hour).zfill(2) + str(to_min).zfill(2))

file = getFileName(2023, 3, 27, 14, 15, 18, 45)

# read file, convert timestamp
df = pd.read_csv(os.path.join("ignore\data", file + '.txt'), sep = '\t')
df.TimeStamp = pd.to_datetime(df.TimeStamp, format = '%Y-%m-%d %H:%M:%S.%f').sort_values()

# =============================================================================
# phase & detector configuration for westbound
# =============================================================================

# phase config
phase = {'thru': 2, 'left': 5}

# phase change events (s = start, e = end)
pse = {'Gs': 1, 'Ge': 7,
       'Ys': 8, 'Ye': 9,
       'Rs': 10, 'Re': 11}
signal = {8: 'Y', 10: 'R', 1: 'G'}

# detector configuration
on, off = 82, 81
det = {'adv': (27, 28, 29), 
       'stop': (9, 10, 11), 
       'front': 5, 
       'rear': 6}

# lane position
# lane = {'adv': {27: 'R', 28: 'M', 29: 'L'},
#         'stop': {9: 'R', 10: 'M', 11: 'L'}}
lane = {'adv': {27: 0, 28: 1, 29: 2},
        'stop': {9: 0, 10: 1, 11: 2}}

# =============================================================================
# process phase change events
# =============================================================================

def processPhaseChanges(phase_dirc):
    # phase change events data frame
    pdf = df.copy(deep = True)
    
    # filter phase direction and phase events
    pdf = pdf[(pdf.Parameter == phase[phase_dirc]) & (pdf.EventID.isin(list(pse.values())))]
    
    # compute cycle time range assuming cycle starts on yellow
    cycle_range = {'min': min((pdf.loc[pdf.EventID == pse['Ge']]).TimeStamp),
                   'max': max((pdf.loc[pdf.EventID == pse['Ge']]).TimeStamp)}
    
    pdf = pdf[(pdf.TimeStamp >= cycle_range['min']) & (pdf.TimeStamp <= cycle_range['max'])]
    pdf = pdf[pdf.EventID.isin((pse['Ys'], pse['Rs'], pse['Gs']))]
    
    # indication start times: yellow, red, green
    start_time = {'Y': tuple((pdf.loc[pdf.EventID == pse['Ys']]).TimeStamp),
                  'R': tuple((pdf.loc[pdf.EventID == pse['Rs']]).TimeStamp),
                  'G': tuple((pdf.loc[pdf.EventID == pse['Gs']]).TimeStamp)}
    
    # indication time intervals: yellow, red, green
    interval = {'Y': Vector(start_time['R']) - Vector(start_time['Y'][:-1]),
                'R': Vector(start_time['G']) - Vector(start_time['R']),
                'G': Vector(start_time['Y'][1:]) - Vector(start_time['G'])}
    
    # cycle number and length
    cycle_index = {'num': tuple(range(1, len(start_time['Y']))),
                   'length': Vector(start_time['Y'][1:]) - Vector(start_time['Y'][:-1])}
    
    cycle = {
        'CycleNum': cycle_index['num'],
        'CycleLength': cycle_index['length'],
        'YST': start_time['Y'][:-1], # current cycle
        'RST': start_time['R'],
        'GST': start_time['G'],
        'YST_NC': start_time['Y'][1:], # next cycle
        'YellowTime': interval['Y'],
        'RedTime': interval['R'],
        'GreenTime': interval['G']
    }
    
    cdf = pd.DataFrame(cycle)
    
    return {'pdf': pdf, # phase data frame
            'cdf': cdf, # cycle data frame
            'start_time': start_time,
            'cycle_range': cycle_range}

# =============================================================================
# process detector actuation events
# =============================================================================

def processDetectorActuations(phase_dirc):
    # detector actutation events data frame
    ddf = df.copy(deep = True)
    
    # filter detection on/off events
    ddf = ddf[ddf.EventID.isin([on, off])]
    
    # filter detection events within cycle min-max time (exclude bounds)
    cycle_range = processPhaseChanges(phase_dirc)['cycle_range']
    ddf = ddf[(ddf.TimeStamp > cycle_range['min']) & (ddf.TimeStamp < cycle_range['max'])]
    
    # filter detector number; add lane position and detector type
    if phase_dirc == 'thru':
        det_set = det['adv'] + det['stop']
        ddf = ddf[ddf.Parameter.isin(det_set)]
        ddf['Lane'] = ddf.Parameter.map(lane['adv'] | lane['stop'])
        ddf.loc[ddf.Parameter.isin(det['adv']), 'Det'] = 'adv'
        ddf.loc[ddf.Parameter.isin(det['stop']), 'Det'] = 'stop'
    else:
        det_set = (det['front'], det['rear'])
        ddf = ddf[ddf.Parameter.isin(det_set)]
        ddf['Lane'] = -1 # left-turn lane
        ddf.loc[ddf.Parameter == det['front'], 'Det'] = 'front'
        ddf.loc[ddf.Parameter == det['rear'], 'Det'] = 'rear'
    
    return {'ddf': ddf, 
            'det_set': det_set}

# =============================================================================
# process signal status change and OHG parameters
# =============================================================================

# signal status change and first on and last off (FOLO) over a detector
def processSignalStatusChange(xdf, det_num):
    print("Checking signal status change for detector: ", det_num)
    ldf = xdf.copy(deep = True) # lane-based actuations events df
    ldf = ldf[ldf.Parameter == det_num] # filter for detector number
    
    # timestamps of detector on and off
    detOn = tuple((ldf.loc[ldf.EventID == on]).TimeStamp)
    detOff = tuple((ldf.loc[ldf.EventID == off]).TimeStamp)
    
    # filter df for timestamp between first det on and last det off
    detOnFirst, detOffLast = min(detOn), max(detOff)
    ldf = ldf[(ldf.TimeStamp >= detOnFirst) & (ldf.TimeStamp <= detOffLast)]
    
    # check number of on/off actutations are equal
    lenDetOn = len(ldf.loc[ldf.EventID == on])
    lenDetOff = len(ldf.loc[ldf.EventID == off])
    
    if lenDetOn != lenDetOff:
        print("Error!")
        return None
    else:
        print("Pass!")
        # get signal status for detector on and off
        detOnSignal = tuple((ldf.loc[ldf.EventID == on]).Signal)
        detOffSignal = tuple((ldf.loc[ldf.EventID == off]).Signal)
        
        # filtered timestamps of detector on and off
        detOnTime = tuple((ldf.loc[ldf.EventID == on]).TimeStamp)
        detOffTime = tuple((ldf.loc[ldf.EventID == off]).TimeStamp)
        
        # compute on-detector time
        OccTime = np.array(Vector(detOffTime) - Vector(detOnTime))
        
        # compute leading and following headway
        Headway = np.array(Vector(detOnTime[1:]) - Vector(detOnTime))
        HeadwayLead = np.append(Headway, np.nan)
        HeadwayFoll = np.insert(Headway, 0, np.nan)
        
        # compute leading and following gap
        Gap = np.array(Vector(detOnTime[1:]) - Vector(detOffTime))
        GapLead = np.append(Gap, np.nan)
        GapFoll = np.insert(Gap, 0, np.nan)
        
        # detOn = tuple((ldf.loc[(ldf.EventID == on) & (ldf.Parameter == det_num)]).Signal)
        # detOff = tuple((ldf.loc[(ldf.EventID == off) & (ldf.Parameter == det_num)]).Signal)
        
        return {'dof': detOnFirst,
                'dol': detOffLast,
                'SSC': [i + j for i, j in zip(detOnSignal, detOffSignal)],
                'OccTime': OccTime,
                'HeadwayLead': HeadwayLead,
                'HeadwayFoll': HeadwayFoll,
                'GapLead': GapLead,
                'GapFoll': GapFoll}
    
# =============================================================================
# merge events and compute parameters
# =============================================================================

def processMergedEvents(phase_dirc):
    
    # check phase parameters
    pdf = processPhaseChanges(phase_dirc)['pdf']
    cdf = processPhaseChanges(phase_dirc)['cdf']
    start_time = processPhaseChanges(phase_dirc)['start_time']
    
    print("Yellows, Reds, Greens:", 
          len(start_time['Y']), 
          len(start_time['R']), 
          len(start_time['G']), "\n")
    
    print("Min, max of cycle parameters:")
    print("Cycle length:", min(cdf['CycleLength']), max(cdf['CycleLength']))
    print("Yellow time:", min(cdf['YellowTime']), max(cdf['YellowTime']))
    print("Red time:", min(cdf['RedTime']), max(cdf['RedTime']))
    print("Green time:", min(cdf['GreenTime']), max(cdf['GreenTime']), "\n")
    
    # check detector parameters
    ddf = processDetectorActuations(phase_dirc)['ddf']
    det_set = processDetectorActuations(phase_dirc)['det_set']

    print("Lane-by-lane detector actuations:")
    print(ddf.Parameter.value_counts(dropna = False).sort_values(), "\n")
    print(ddf.groupby('Parameter').EventID.value_counts(), "\n")
    
    # merge events data sets
    mdf = pd.concat([pdf, ddf]).sort_values(by = 'TimeStamp')
    mdf = mdf[:-1] # end row is yellow start time of new cycle

    # add signal category
    mdf['Signal'] = mdf.EventID.map(signal)
    mdf.Signal.ffill(inplace = True)
    
    # add cycle number
    mdf.loc[mdf.EventID == pse['Ys'], 'CycleNum'] = list(range(1, len(start_time['Y'])))
    mdf.CycleNum.ffill(inplace = True)
    
    # left join merged and cycle data frames
    mdf = mdf.merge(cdf, how = 'left', on = 'CycleNum')
    
    # phase & detection parameters
    mdf['AIC'] = round((mdf.TimeStamp - mdf.YST).dt.total_seconds(), 1) # arrival in cycle
    mdf['TUY'] = round((mdf.YST_NC - mdf.TimeStamp).dt.total_seconds(), 1) # time until yellow
    mdf['TUG'] = round((mdf.GST - mdf.TimeStamp).dt.total_seconds(), 1) # time until green

    # signal status change for each detector
    for det_num in det_set:
        ssc_ohg = processSignalStatusChange(mdf, det_num)
        
        timestamp_limit = (mdf.TimeStamp >= ssc_ohg['dof']) & (mdf.TimeStamp <= ssc_ohg['dol'])
        cols = ['SSC', 'OccTime', 'HeadwayLead', 'HeadwayFoll', 'GapLead', 'GapFoll']
        
        for col in cols:
            mdf.loc[(mdf.EventID == on) & (mdf.Parameter == det_num) & timestamp_limit, col] = ssc_ohg[col]
        print("SSC check complete!", "\n")
        
    # keep events with detection on
    mdf = mdf[mdf.EventID == on]
    
    # drop columns
    drop_cols = ['EventID', 'Signal', 'CycleLength', 'YellowTime', 'RedTime', 'GreenTime', 'YST', 'RST', 'GST', 'YST_NC']
    mdf.drop(drop_cols, axis = 1, inplace = True)
    
    # drop rows with SSC == Nan
    mdf.dropna(subset = ['SSC'], axis = 0, inplace = True)
    
    # convert parameter to character (for plotting)
    mdf.Parameter = mdf.Parameter.astype(str)

    return mdf

mdf_thru = processMergedEvents('thru')
mdf_left = processMergedEvents('left')

# merged data set for thru + left-turn
mdf = pd.concat([mdf_thru, mdf_left]).sort_values(by = 'TimeStamp')
mdf.reset_index(drop = True, inplace = True)

cdf = processPhaseChanges('thru')['cdf']

# save data sets
mdf.to_csv(os.path.join("ignore\data", file + "_processed.txt"), sep = '\t', index = False)
cdf.to_csv(os.path.join("ignore\data", file + "_cycle.txt"), sep = '\t', index = False)

# =============================================================================
# visualize actuation and signal status change
# =============================================================================

# create ID for each actuation
mdf['ID'] = mdf.index + 100000 # adv det IDs start with 1
mdf.loc[mdf.Det == 'stop', 'ID'] = mdf.ID + 100000 # stop-bar det IDs start with 2
mdf.loc[mdf.Lane == -1, 'ID'] = mdf.ID + 200000 # left-turn det IDs start with 3

# plot detection points for subset
det_order = [9, 27, 10, 28, 11, 29, 6, 5]
cat_order = {'SSC': ['YY', 'YR', 'RR', 'RG', 'GG', 'GY', 'GR'],
             'Parameter': det_order}

ssc_color = {'YY': 'orange',
             'YR': 'brown',
             'RR': 'red',
             'RG': 'black',
             'GG': 'green',
             'GY': 'limegreen',
             'GR': 'navy'}

def plotActuationSSC(xdf):
    fig = px.scatter(
        xdf, x = 'TimeStamp', y = 'Parameter',
        color = 'SSC',
        hover_name = 'ID',
        hover_data = ['AIC', 'TUY', 'TUG', 'OccTime', 'HeadwayLead', 'GapLead'],
        category_orders = cat_order,
        color_discrete_map = ssc_color
    ).update_traces(marker = dict(size = 10))
    
    fig.show()
    return fig
    
fig = plotActuationSSC(mdf)
fig.write_html(os.path.join("output/actuation_html", file + "_processed.html"))

# =============================================================================
# filter actuation at onset of yellow
# =============================================================================

# threshold parameters
crit_TUY_adv = 7 # critical TUY at adv det of YLR, RLR actuation over stop-bar det
crit_AIC_adv = 4 # critical AIC at adv det = length of yellow interval
crit_AIC_stop = 15 # critical AIC at stop bar detector

tdf = mdf.copy(deep = True) # temp data frame

# filter actuation at adv det susceptible to dilemma zone
df_crit_adv = tdf[(tdf.Det == 'adv') & ((tdf.TUY <= crit_TUY_adv) | (tdf.AIC <= crit_AIC_adv))]
id_adv = set(df_crit_adv.ID)

# filter potential set of corresponding matches at stop-bar
df_crit_stop = tdf[(tdf.Det == 'stop') & ((tdf.AIC <= crit_AIC_stop) | (tdf.TUY == 0))]
id_stop = set(df_crit_stop.ID)

# union set of ids
id_adv_stop = sorted(set.union(id_adv, id_stop))

# filtered data frame
fdf = tdf[(tdf.Lane == -1) | (tdf.ID.isin(id_adv_stop))]
fdf.to_csv(os.path.join("ignore\data", file + "_filtered.txt"), sep = '\t', index = False)

fig = plotActuationSSC(fdf)
fig.write_html(os.path.join("output/actuation_html", file + "_filtered.html"))