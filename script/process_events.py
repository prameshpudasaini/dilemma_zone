import os
import pandas as pd

os.chdir(r"D:\GitHub\match_events")

class Vector():
    def __init__(self, data):
        self.data = data
    def __repr__(self):
        return repr(self.data)
    def __sub__(self, other):
        return list((a-b).total_seconds() for a, b in zip(self.data, other.data))

df = pd.read_csv("data/20221206_ISR_19Ave/data_process.txt", sep = '\t')

# convert datetime
df.TimeStamp = pd.to_datetime(df.TimeStamp, format = '%Y-%m-%d %H:%M:%S.%f').sort_values()

# =============================================================================
# phase & detector configuration for westbound
# =============================================================================

# phase config
phase = {'thru': 2, 'left': 5}

# phase change (start, end) events
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
lane = {'adv': {27: 'R', 28: 'M', 29: 'L'},
        'stop': {9: 'R', 10: 'M', 11: 'L'}}

# =============================================================================
# process phase change events
# =============================================================================

def processPhaseChanges(phase_dirc):
    # phase change events data frame
    pdf = df.copy(deep = True) 
    
    # filter phase direction and phase events
    pdf = pdf[(pdf.Parameter == phase[phase_dirc]) & (pdf.EventID.isin(list(pse.values())))]
    
    # compute cycle time assuming cycle starts on yellow
    CycleTime = {'min': min((pdf.loc[pdf.EventID == pse['Ge']]).TimeStamp),
                 'max': max((pdf.loc[pdf.EventID == pse['Ge']]).TimeStamp)}
    
    pdf = pdf[(pdf.TimeStamp >= CycleTime['min']) & (pdf.TimeStamp <= CycleTime['max'])]
    pdf = pdf[pdf.EventID.isin((pse['Ys'], pse['Rs'], pse['Gs']))]
    
    # indication start times: yellow, red, green
    StartTime = {'Y': tuple((pdf.loc[pdf.EventID == pse['Ys']]).TimeStamp),
                 'R': tuple((pdf.loc[pdf.EventID == pse['Rs']]).TimeStamp),
                 'G': tuple((pdf.loc[pdf.EventID == pse['Gs']]).TimeStamp)}
    
    # indication time intervals: yellow, red, green
    interval = {'Y': Vector(StartTime['R']) - Vector(StartTime['Y'][:-1]),
                'R': Vector(StartTime['G']) - Vector(StartTime['R']),
                'G': Vector(StartTime['Y'][1:]) - Vector(StartTime['G'])}
    
    # cycle number and length
    cycle = {'num': tuple(range(1, len(StartTime['Y']))),
             'len': Vector(StartTime['Y'][1:]) - Vector(StartTime['Y'][:-1])}
    
    return {'pdf': pdf, 
            'CycleTime': CycleTime, 
            'StartTime': StartTime, 
            'interval': interval, 
            'cycle': cycle}

# =============================================================================
# process detector actuation events
# =============================================================================

def processDetectorActuations(phase_dirc):
    # detector actutation events data frame
    ddf = df.copy(deep = True)
    
    # filter detection on/off events
    ddf = ddf[ddf.EventID.isin([on, off])]
    
    # filter detection events within cycle min-max time
    CycleTime = processPhaseChanges(phase_dirc)['CycleTime']
    ddf = ddf[(ddf.TimeStamp > CycleTime['min']) & (ddf.TimeStamp < CycleTime['max'])]
    
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
        ddf['Lane'] = 'LT'
        ddf.loc[ddf.Parameter == det['front'], 'Det'] = 'front'
        ddf.loc[ddf.Parameter == det['rear'], 'Det'] = 'rear'
    
    return {'ddf': ddf, 'det_set': det_set}

# =============================================================================
# process signal status change
# =============================================================================

# signal status change and first on and last off (FOLO) over a detector
def SSC_FOLO(merge_df, det_num):
    print("Checking signal status change for detector: ", det_num)
    ldf = merge_df.copy(deep = True) # lane-based actuations events df
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
        detOn = tuple((ldf.loc[(ldf.EventID == on) & (ldf.Parameter == det_num)]).Signal)
        detOff = tuple((ldf.loc[(ldf.EventID == off) & (ldf.Parameter == det_num)]).Signal)
        
        return {'dof': detOnFirst,
                'dol': detOffLast,
                'SSC': [i + j for i, j in zip(detOn, detOff)]}
    
# =============================================================================
# merge events and compute parameters
# =============================================================================

def processMergedEvents(phase_dirc):
    
    phase_dict = processPhaseChanges(phase_dirc)
    det_dict = processDetectorActuations(phase_dirc)

    # check phase parameters
    StartTime = phase_dict['StartTime']
    interval = phase_dict['interval']
    cycle = phase_dict['cycle']
    
    print("Yellows, Reds, Greens:", 
          len(StartTime['Y']), 
          len(StartTime['R']), 
          len(StartTime['G']), "\n")
    
    print("Min, max of phase parameters:")
    print("Cycle length:", min(cycle['len']), max(cycle['len']))
    print("Yellow time:", min(interval['Y']), max(interval['Y']))
    print("Red time:", min(interval['R']), max(interval['R']))
    print("Green time:", min(interval['G']), max(interval['G']), "\n")
    
    pdf = phase_dict['pdf']
    ddf = det_dict['ddf']
    
    # count lane-by-lane detections
    print(ddf.Parameter.value_counts(dropna = False).sort_values(), "\n")
    print(ddf.groupby('Parameter').EventID.value_counts(), "\n")
    
    det_set = det_dict['det_set']
    
    # merge events data sets
    mdf = pd.concat([pdf, ddf]).sort_values(by = 'TimeStamp')
    mdf = mdf[:-1] # end row is yellow start time of new cycle

    # add signal category
    mdf['Signal'] = mdf.EventID.map(signal)
    
    # add phase data
    phase_cols = {'Cycle': cycle['num'],
                  'CycleLength': cycle['len'],
                  'YST': StartTime['Y'][:-1], # current cycle
                  'YST_NC': StartTime['Y'][1:], # next cycle
                  'RST': StartTime['R'],
                  'GST': StartTime['G'],
                  'RedTime': interval['R'],
                  'GreenTime': interval['G']}
    
    for key, value in phase_cols.items():
        mdf.loc[mdf.EventID == pse['Ys'], key] = value
        
    # forward fill phase columns
    fill_cols = [col for col in phase_cols.keys()]
    fill_cols.append('Signal')
    
    for col in fill_cols:
        mdf[col].ffill(inplace = True)
        
    # phase & detection parameters
    mdf['AIC'] = (mdf.TimeStamp - mdf.YST).dt.total_seconds() # arrival in cycle
    mdf['TUY'] = (mdf.YST_NC - mdf.TimeStamp).dt.total_seconds() # time until yellow
    mdf['TUG'] = (mdf.GST - mdf.TimeStamp).dt.total_seconds() # time until green
    
    # signal status change for each detector
    for det_num in det_set:
        ssc_folo = SSC_FOLO(mdf, det_num)
        
        timestamp_limit = (mdf.TimeStamp >= ssc_folo['dof']) & (mdf.TimeStamp <= ssc_folo['dol'])
        mdf.loc[(mdf.EventID == on) & (mdf.Parameter == det_num) & timestamp_limit, 'SSC'] = ssc_folo['SSC']
        print("SSC check complete!", "\n")
        
    # events with detection on
    mdf.dropna(axis = 0, inplace = True)
    mdf.drop('EventID', axis = 1, inplace = True)
    
    mdf.Parameter = mdf.Parameter.astype(str)
        
    return mdf

mdf_thru = processMergedEvents('thru')
mdf_left = processMergedEvents('left')

mdf = pd.concat([mdf_thru, mdf_left]).sort_values(by = 'TimeStamp')
mdf.reset_index(drop = True, inplace = True)

# mdf.to_csv(r"D:\GitHub\match_events\data\20221206_ISR_19Ave\data_SSC.txt", sep = '\t', index = False)
