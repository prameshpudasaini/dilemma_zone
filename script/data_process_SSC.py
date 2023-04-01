import pandas as pd

class Vector():
    def __init__(self, data):
        self.data = data
    def __repr__(self):
        return repr(self.data)
    def __sub__(self, other):
        return list((a-b).total_seconds() for a, b in zip(self.data, other.data))

path = r"D:\GitHub\match_events\data\20221206_ISR_19Ave\data_process.txt"
df = pd.read_csv(path, sep = '\t')

df.TimeStamp = pd.to_datetime(df.TimeStamp, format = '%Y-%m-%d %H:%M:%S.%f').sort_values()

# =============================================================================
# phase/detector configuration for westbound
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
# process phase/detection events
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

# function to process phase/detection events
def processPhaseDetEvents(phase_dirc):
    
    # phase change events data frame
    pdf = df.copy(deep = True) 
    
    # filter phase direction and phase events
    pdf = pdf[(pdf.Parameter == phase[phase_dirc]) & (pdf.EventID.isin(list(pse.values())))]
    
    # compute cycle time assuming cycle starts on yellow
    ct = {'min': min((pdf.loc[pdf.EventID == pse['Ge']]).TimeStamp),
          'max': max((pdf.loc[pdf.EventID == pse['Ge']]).TimeStamp)}
    
    pdf = pdf[(pdf.TimeStamp >= ct['min']) & (pdf.TimeStamp <= ct['max'])]
    pdf = pdf[pdf.EventID.isin((pse['Ys'], pse['Rs'], pse['Gs']))]
    
    # indication start times: yellow, red, green
    ist = {'Y': tuple((pdf.loc[pdf.EventID == pse['Ys']]).TimeStamp),
          'R': tuple((pdf.loc[pdf.EventID == pse['Rs']]).TimeStamp),
          'G': tuple((pdf.loc[pdf.EventID == pse['Gs']]).TimeStamp)}
    
    print("Yellows, Red, Greens:", len(ist['Y']), len(ist['R']), len(ist['G']), "\n")
    
    # indication time intervals: yellow, red, green
    iti = {'Y': Vector(ist['R']) - Vector(ist['Y'][:-1]),
           'R': Vector(ist['G']) - Vector(ist['R']),
           'G': Vector(ist['Y'][1:]) - Vector(ist['G'])}
    
    # cycle number and length
    cycle = {'num': tuple(range(1, len(ist['Y']))),
             'len': Vector(ist['Y'][1:]) - Vector(ist['Y'][:-1])}
    
    print("Min, max of phase parameters:")
    print("Cycle length:", min(cycle['len']), max(cycle['len']))
    print("Yellow time:", min(iti['Y']), max(iti['Y']))
    print("Red time:", min(iti['R']), max(iti['R']))
    print("Green time:", min(iti['G']), max(iti['G']), "\n")
    
    # detector actutation events data frame
    ddf = df.copy(deep = True)
    
    # filter detection events and detector number
    if phase_dirc == 'thru':
        det_set = det['adv'] + det['stop']
        ddf = ddf[(ddf.EventID.isin((on, off))) & (ddf.Parameter.isin(det_set))]
    else:
        det_set = (det['front'], det['rear'])
        ddf = ddf[(ddf.EventID.isin((on, off))) & (ddf.Parameter.isin(det_set))]
    
    # filter detection events within cycle min-max time
    ddf = ddf[(ddf.TimeStamp > ct['min']) & (ddf.TimeStamp < ct['max'])]

    # count lane-by-lane detections
    print(ddf.Parameter.value_counts(dropna = False).sort_values(), "\n")
    print(ddf.groupby('Parameter').EventID.value_counts(), "\n")
    
    # merge events data sets
    mdf = pd.concat([pdf, ddf]).sort_values(by = 'TimeStamp')
    mdf = mdf[:-1] # end row is yellow start time of new cycle
    
    # add lane position (right, middle, left) and detector type
    if phase_dirc == 'thru':
        mdf['Lane'] = mdf.Parameter.map(lane['adv'] | lane['stop'])
        mdf.loc[mdf.Parameter.isin(det['adv']), 'Det'] = 'adv'
        mdf.loc[mdf.Parameter.isin(det['stop']), 'Det'] = 'stop'
    else:
        mdf['Lane'] = 'LT'
        mdf.loc[mdf.Parameter == det['front'], 'Det'] = 'front'
        mdf.loc[mdf.Parameter == det['rear'], 'Det'] = 'rear'
        
    # add signal category
    mdf['Signal'] = mdf.EventID.map(signal)
    mdf['Signal'].ffill(inplace = True)
    
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
    mdf.reset_index(drop = True, inplace = True)
    
    return {'pdf': pdf, 'ddf': ddf, 'mdf': mdf}

mdf_thru = processPhaseDetEvents('thru')['mdf']
mdf_left = processPhaseDetEvents('left')['mdf']
mdf_wb = pd.concat([mdf_thru, mdf_left]).sort_values(by = 'TimeStamp')

# mdf_wb.to_csv(r"D:\GitHub\match_events\data\20221206_ISR_19Ave\data_SSC.txt", sep = '\t', index = False)
