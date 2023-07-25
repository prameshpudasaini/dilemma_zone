import os
import json
import pandas as pd

os.chdir(r"D:\GitHub\dilemma_zone")
input_path = "ignore/dz_data/processed"
output_path = "data/dz_analysis/"

with open('data/dz_analysis/match_results.txt') as f:
    thru_pairs = json.load(f)
    
# list of processed files
file_list = os.listdir(input_path)

def processMatchPairs():

    # pairs of video-verified matches
    pairs = thru_pairs[file]
    
    if len(pairs) == 0:
        pass
    else:
        set_id_adv = set(pairs.values())
        set_id_stop = set(map(int, pairs.keys()))
        
        # read data frame
        df = pd.read_csv(os.path.join(input_path, file), sep = '\t')
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
            
        # convert id data type: object -> int
        tdf = tdf[['ID_adv', 'ID_stop']].astype(str).astype(int)
        
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
        cols_remove = ['TimeStamp_adv', 'TimeStamp_stop', 'ID_adv', 'ID_stop', 'SCA_adv', 'SCA_stop']
        mdf.drop(cols_remove, axis = 1, inplace = True)
        mdf.dropna(axis = 0, inplace = True)
        
        # # create month, day, hour variables based on file name
        month, day, hour = file[4:6], file[6:8], file[9:11]
        mdf['month'] = month
        mdf['day'] = day
        mdf['hour'] = hour
        
        return mdf

# create full data frame for all processed files
fdf = []
for file in file_list:
    print("Processing file: ", file)    
    fdf.append(processMatchPairs())

# merge data frames
fdf = pd.concat(fdf)
fdf.to_csv(os.path.join(output_path, "matched_events_dataset_bulk.txt"), sep = '\t', index = False)
