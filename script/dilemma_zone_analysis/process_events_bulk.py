import os
import pandas as pd
import numpy as np

os.chdir(r"D:\GitHub\dilemma_zone")
input_path = "ignore/dz_data/raw"
output_path = "ignore/dz_data/processed"

# define class to subtract timestamps
class Vector():
    def __init__(self, data):
        self.data = data
    def __repr__(self):
        return repr(self.data)
    def __sub__(self, other):
        return list((a-b).total_seconds() for a, b in zip(self.data, other.data))

# =============================================================================
# phase & detector configuration, threshold parameters
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
thru_det_set = det['adv'] + det['stop']

# lane position
# lane = {'adv': {27: 'R', 28: 'M', 29: 'L'},
#         'stop': {9: 'R', 10: 'M', 11: 'L'}}
lane = {'adv': {27: 0, 28: 1, 29: 2},
        'stop': {9: 0, 10: 1, 11: 2}}

# threshold parameters
crit_TUY_adv = 6 # critical TUY at adv det of YLR, RLR actuation over stop-bar det
crit_AIY_adv = 3.6 # critical AIY at adv det = length of yellow interval
crit_TUY_stop = 1.5 # critical TUY at stop bar det
crit_AIY_stop = 12 # critical AIY at stop bar det

# =============================================================================
# process phase change events
# =============================================================================

def processPhaseChanges():
    # phase change events data frame
    pdf = df.copy(deep = True)
    
    # filter phase direction and phase events
    pdf = pdf[(pdf.Parameter == phase['thru']) & (pdf.EventID.isin(list(pse.values())))]
    
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

def processDetectorActuations():
    # detector actutation events data frame
    ddf = df.copy(deep = True)
    
    # filter detection on/off events
    ddf = ddf[ddf.EventID.isin([on, off])]
    
    # filter detection events within cycle min-max time (exclude bounds)
    cycle_range = processPhaseChanges()['cycle_range']
    ddf = ddf[(ddf.TimeStamp > cycle_range['min']) & (ddf.TimeStamp < cycle_range['max'])]
    
    # filter detector number; add lane position and detector type
    
    ddf = ddf[ddf.Parameter.isin(thru_det_set)]
    ddf['Lane'] = ddf.Parameter.map(lane['adv'] | lane['stop'])
    ddf.loc[ddf.Parameter.isin(det['adv']), 'Det'] = 'adv'
    ddf.loc[ddf.Parameter.isin(det['stop']), 'Det'] = 'stop'
    
    return ddf

# =============================================================================
# process signal change during actuation and OHG parameters
# =============================================================================

# signal change during actuation (SCA)
# first on and last off (FOLO) over a detector
# computation of parameters: occupancy time, headway, gap
def processSCA_OHG(xdf, det_num):
    print("Checking signal change during actuation for detector: ", det_num)
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
        
        return {'dof': detOnFirst,
                'dol': detOffLast,
                'SCA': [i + j for i, j in zip(detOnSignal, detOffSignal)],
                'OccTime': OccTime,
                'HeadwayLead': HeadwayLead,
                'HeadwayFoll': HeadwayFoll,
                'GapLead': GapLead,
                'GapFoll': GapFoll}
    
# =============================================================================
# merge events and compute parameters
# =============================================================================

def processMergedEvents():
    # check phase parameters
    pdf = processPhaseChanges()['pdf']
    cdf = processPhaseChanges()['cdf']
    start_time = processPhaseChanges()['start_time']
    
    # check detector parameters
    ddf = processDetectorActuations()
    
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
    mdf['AIY'] = round((mdf.TimeStamp - mdf.YST).dt.total_seconds(), 1) # arrival in yellow
    mdf['TUY'] = round((mdf.YST_NC - mdf.TimeStamp).dt.total_seconds(), 1) # time until yellow
    mdf['TUG'] = round((mdf.GST - mdf.TimeStamp).dt.total_seconds(), 1) # time until green

    # signal change during actuation for each detector
    for det_num in thru_det_set:
        sca_ohg = processSCA_OHG(mdf, det_num)
        
        timestamp_limit = (mdf.TimeStamp >= sca_ohg['dof']) & (mdf.TimeStamp <= sca_ohg['dol'])
        cols = ['SCA', 'OccTime', 'HeadwayLead', 'HeadwayFoll', 'GapLead', 'GapFoll']
        
        for col in cols:
            mdf.loc[(mdf.EventID == on) & (mdf.Parameter == det_num) & timestamp_limit, col] = sca_ohg[col]
        
    # keep events with detection on
    mdf = mdf[mdf.EventID == on]
    
    # drop columns
    drop_cols = ['EventID', 'Signal', 'CycleLength', 'YellowTime', 'RedTime', 'GreenTime', 'YST', 'RST', 'GST', 'YST_NC']
    mdf.drop(drop_cols, axis = 1, inplace = True)
    
    # drop rows with SCA == Nan
    mdf.dropna(subset = ['SCA'], axis = 0, inplace = True)
    
    # convert parameter to character (for plotting)
    mdf.Parameter = mdf.Parameter.astype(str)

    return mdf

# =============================================================================
# process events in bulk
# =============================================================================

# list of raw files
file_list = os.listdir(input_path)

# list of hours with error in processing events
error_file_list = [
    '20230131_03_raw.txt',
    '20230131_04_raw.txt',
    '20230131_05_raw.txt',
    '20230131_06_raw.txt',
    '20230131_07_raw.txt',
    '20230131_08_raw.txt',
    '20230131_09_raw.txt',
    '20230131_10_raw.txt',
    '20230131_11_raw.txt',
    '20230131_12_raw.txt',
    '20230131_13_raw.txt',
    '20230131_14_raw.txt',
    '20230131_15_raw.txt',
    '20230131_16_raw.txt',
    '20230131_17_raw.txt',
    '20230131_18_raw.txt',
    '20230131_19_raw.txt',
    '20230131_20_raw.txt',
    '20230131_21_raw.txt',
    '20230131_22_raw.txt',
    '20230131_23_raw.txt',
    '20230201_00_raw.txt',
    '20230201_01_raw.txt',
    '20230227_03_raw.txt',
    '20230227_04_raw.txt',
    '20230227_05_raw.txt',
    '20230227_06_raw.txt',
    '20230227_07_raw.txt',
    '20230227_08_raw.txt',
    '20230227_09_raw.txt',
    '20230227_10_raw.txt',
    '20230227_11_raw.txt',
    '20230227_12_raw.txt',
    '20230227_13_raw.txt',
    '20230227_14_raw.txt',
    '20230227_15_raw.txt',
    '20230227_16_raw.txt',
    '20230227_17_raw.txt',
    '20230227_18_raw.txt',
    '20230227_19_raw.txt',
    '20230227_20_raw.txt',
    '20230227_21_raw.txt',
    '20230227_22_raw.txt',
    '20230227_23_raw.txt',
    '20230228_00_raw.txt',
    '20230228_01_raw.txt',
    '20230228_03_raw.txt',
    '20230228_04_raw.txt',
    '20230228_05_raw.txt',
    '20230228_06_raw.txt',
    '20230228_07_raw.txt',
    '20230228_08_raw.txt',
    '20230228_09_raw.txt',
    '20230228_10_raw.txt',
    '20230228_11_raw.txt',
    '20230228_12_raw.txt',
    '20230228_13_raw.txt',
    '20230228_14_raw.txt',
    '20230228_15_raw.txt',
    '20230228_16_raw.txt',
    '20230228_17_raw.txt',
    '20230228_18_raw.txt',
    '20230228_19_raw.txt',
    '20230228_20_raw.txt',
    '20230228_21_raw.txt',
    '20230228_22_raw.txt',
    '20230228_23_raw.txt'
]

num = 1
# process events for each file
for file in file_list[num:]:
    print("**************************************************")
    print("Processing events for file: ", file, "\n")
    
    if file in error_file_list:
        pass
    else:
        # read individual file
        df = pd.read_csv(os.path.join(input_path, file), sep = '\t')
        df.TimeStamp = pd.to_datetime(df.TimeStamp, format = '%Y-%m-%d %H:%M:%S.%f').sort_values()
        
        # merged (phase & actuation) data frames for through movement
        mdf_thru = processMergedEvents()
        
        # detection on the left-turn rear detector
        mdf_left = df.copy(deep = True)
        mdf_left = mdf_left[(mdf_left.EventID == on) & (mdf_left.Parameter == det['rear'])]
        mdf_left.drop('EventID', axis = 1, inplace = True)
        
        # add lane and det parameters
        mdf_left['Lane'] = -1
        mdf_left['Det'] = 'rear'
        
        # merge thru and left data frames
        mdf = pd.concat([mdf_thru, mdf_left]).sort_values(by = 'TimeStamp')
        mdf.reset_index(drop = True, inplace = True)
    
        # create ID for each actuation
        mdf['ID'] = mdf.index + 100000 # adv det IDs start with 1
        mdf.loc[mdf.Det == 'stop', 'ID'] = mdf.ID + 100000 # stop-bar det IDs start with 2
        mdf.loc[mdf.Lane == -1, 'ID'] = mdf.ID + 200000 # left-turn det IDs start with 3
    
        tdf = mdf.copy(deep = True) # temp data frame
    
        # filter out SCA (YG, RY, GR) over stop-bar and adv det
        remove_SCA = ['YG', 'RY', 'GR']
        tdf = tdf.drop(tdf[(tdf.Det.isin(['adv', 'stop'])) & (tdf.SCA.isin(remove_SCA))].index)
    
        # filter actuation at adv det susceptible to dilemma zone
        df_crit_adv = tdf[(tdf.Det == 'adv') & ((tdf.TUY <= crit_TUY_adv) | (tdf.AIY <= crit_AIY_adv))]
        id_adv = set(df_crit_adv.ID)
    
        # filter potential set of corresponding matches at stop-bar
        df_crit_stop = tdf[(tdf.Det == 'stop') & ((tdf.TUY <= crit_TUY_stop) | (tdf.AIY <= crit_AIY_stop))]
        id_stop = set(df_crit_stop.ID)
    
        # union set of ids
        id_adv_stop = sorted(set.union(id_adv, id_stop))
    
        # filtered data frame
        fdf = tdf[(tdf.Lane == -1) | (tdf.ID.isin(id_adv_stop))]
        fdf.to_csv(os.path.join(output_path, file[:11] + "_filtered.txt"), sep = '\t', index = False)
        
        print("Processing events complete \n")
        num += 1
