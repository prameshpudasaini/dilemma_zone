import os
import ast
import pandas as pd

os.chdir(r"D:\GitHub\dilemma_zone")

with open('data/calibration/manual_adv_stop_pairs.txt') as f:
    thru_pairs = ast.literal_eval(f.read())

# =============================================================================
# files & parameters
# =============================================================================

# select period and file
def getFileName(year, month, day, from_hour, from_min, to_hour, to_min):
    return(str(year) + str(month).zfill(2) + str(day).zfill(2) + '_' +
           str(from_hour).zfill(2) + str(from_min).zfill(2) + '_' +
           str(to_hour).zfill(2) + str(to_min).zfill(2))

# read file
input_path = "ignore/calibration_data"
output_path = "data/match_training"
files = list([getFileName(2022, 12, 6, 7, 45, 8, 15),
              getFileName(2022, 12, 6, 8, 45, 9, 15),
              getFileName(2022, 12, 14, 7, 45, 8, 15),
              getFileName(2022, 12, 14, 8, 45, 9, 15),
              getFileName(2022, 12, 14, 9, 45, 10, 15),
              getFileName(2023, 3, 27, 14, 15, 18, 45)])

def processMatchPairs(file_num):

    # pairs of video-verified matches
    pairs = thru_pairs[file_num + 1]
    set_id_adv = set(pairs.values())
    set_id_stop = set(pairs.keys())
    
    # read data frame
    df = pd.read_csv(os.path.join(input_path, files[file_num] + '_filtered.txt'), sep = '\t')
    df.TimeStamp = pd.to_datetime(df.TimeStamp, format = '%Y-%m-%d %H:%M:%S.%f')
    df.drop(['Parameter', 'Lane', 'Det', 'CycleNum', 'TUG', 'HeadwayLead', 'GapLead'], axis = 1, inplace = True)
    
    # data frame for advance, stop-bar det
    adf = df[df.ID.isin(set_id_adv)]
    sdf = df[df.ID.isin(set_id_stop)]
    
    # add suffix to column names
    adf.columns += '_adv'
    sdf.columns += '_stop'
    
    # temporary data frame
    tdf = pd.DataFrame(columns = ['ID_adv', 'ID_stop'])
    
    # add adv, stop IDs to tdf
    i = 0
    for key, value in pairs.items():
        tdf.loc[i, 'ID_adv'] = value
        tdf.loc[i, 'ID_stop'] = key
        i += 1
    
    mdf = adf.merge(tdf, how = 'right') # merge adf to right
    mdf = mdf.merge(sdf, how = 'outer') # merge sdf
    
    # compute travel time based on timestamps
    mdf['travel_time'] = round((mdf.TimeStamp_stop - mdf.TimeStamp_adv).dt.total_seconds(), 1)
    
    # indication at adv detector
    mdf.loc[mdf.SCA_adv.isin(['YY', 'YR']), 'adv_indication'] = 0 # yellow
    mdf.loc[mdf.SCA_adv.isin(['GG', 'GY']), 'adv_indication'] = 1 # green
    
    # decision at stop bar
    mdf.loc[mdf.SCA_stop == 'RG', 'decision'] = 0 # stop
    mdf.loc[mdf.SCA_stop != 'RG', 'decision'] = 1 # run
    
    # car-following
    car_follow_threshold = 1.5
    mdf.loc[mdf.GapFoll_adv > car_follow_threshold, 'car_follow'] = 0 # no car-following
    mdf.loc[mdf.GapFoll_adv <= car_follow_threshold, 'car_follow'] = 1 # car-following
    
    # ratio of occupancy times
    mdf['occ_ratio'] = round(mdf.OccTime_stop / mdf.OccTime_adv, 4)
    
    # remove redundant columns & rows with Nan values
    cols_remove = ['TimeStamp_adv', 'TimeStamp_stop', 'ID_adv', 'ID_stop', 'SCA_adv', 'SCA_stop', 'OccTime_adv', 'OccTime_stop']
    mdf.drop(cols_remove, axis = 1, inplace = True)
    mdf.dropna(axis = 0, inplace = True)
    
    return mdf

# train match pairs for each data set
fdf = []
for file_num in range(len(files)):
    print("Creating training dataset for file: ", file_num)
    fdf.append(processMatchPairs(file_num))

# merge data frames
fdf = pd.concat(fdf)
fdf.to_csv(os.path.join(output_path, "matched_events_dataset.txt"), sep = '\t', index = False)
