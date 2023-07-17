import os
import pandas as pd
import ast

os.chdir(r"D:\GitHub\dilemma_zone")

# define class to subtract timestamps
class Vector():
    def __init__(self, data):
        self.data = data
    def __repr__(self):
        return repr(self.data)
    def __sub__(self, other):
        return list((a-b).total_seconds() for a, b in zip(self.data, other.data))

path = "ignore\calibration_data"

# select period and file
def getFileDataSet(year, month, day, from_hour, from_min, to_hour, to_min):
    file = str(year) + str(month).zfill(2) + str(day).zfill(2) + '_' + str(from_hour).zfill(2) + str(from_min).zfill(2) + '_' + str(to_hour).zfill(2) + str(to_min).zfill(2)
    df = pd.read_csv(os.path.join(path, file + '_filtered.txt'), sep = '\t')
    df.TimeStamp = pd.to_datetime(df.TimeStamp, format = '%Y-%m-%d %H:%M:%S.%f').sort_values()
    return df

df1 = getFileDataSet(2022, 12, 6, 7, 45, 8, 15)
df2 = getFileDataSet(2022, 12, 6, 8, 45, 9, 15)
df3 = getFileDataSet(2022, 12, 14, 7, 45, 8, 15)
df4 = getFileDataSet(2022, 12, 14, 8, 45, 9, 15)
df5 = getFileDataSet(2022, 12, 14, 9, 45, 10, 15)
df6 = getFileDataSet(2023, 3, 27, 14, 15, 18, 45)

df = list([df1, df2, df3, df4, df5, df6])

# =============================================================================
# adv to left-turn lane actuations & parameter calibration
# =============================================================================

with open('data/calibration/manual_adv_left_pairs.txt') as f:
    left_result = ast.literal_eval(f.read())

# check acutations are same on data frame and left result
data_set = set(df6[df6.Parameter == 29].ID)
manual_set = set(left_result[6].keys())
print(data_set == manual_set)

# count total number of left-turn actuations
total_count, left_count = 0, 0
for key, value in left_result.items():
    for inner_key, inner_value in value.items():
        if inner_value != 0:
            left_count+= 1
        total_count += 1
        
print("Total count of left-turn actuations: ", left_count)
print("Percentage of left-turning vehicles on left lane: ", round(left_count/total_count*100, 1))

# actual travel time for adv to left-turn lane
i = 0 # counter for data frame
travel_time = [] # stores travel time from adv to rear det
file_left = open("data/calibration/calibration_left_turn.txt", 'w')

for key, value in left_result.items():
    for inner_key, inner_value in value.items():
        xdf = df[i]
        
        if inner_value != 0: # consider only key-value pairs with left-turn
            adv_time = xdf[xdf.ID == inner_key].TimeStamp
            left_time = xdf[xdf.ID == inner_value].TimeStamp
            
            diff = (Vector(left_time) - Vector(adv_time)).pop()
            travel_time.append(diff)
            
            file_left.write(str(diff)+"\n")
            
    i += 1
file_left.close()

# =============================================================================
# all through actuations & parameter calibration
# =============================================================================

with open('data/calibration/manual_adv_stop_pairs.txt') as f:
    thru_result = ast.literal_eval(f.read())

# count total number of thru actuations
count = 0
for key, value in thru_result.items():
    for inner_key, inner_value in value.items():
        count += 1
        
print("Total number of through actuations: ", count)

# calibration of parameters for adv to stop-bar
i = 0 # counter for data frame
travel_time = [] # stores travel time from adv to stop-bar det
file_thru = open("data/calibration/calibration_thru.txt", 'w')

for key, value in thru_result.items():
    for inner_key, inner_value in value.items():
        xdf = df[i]        
        adv_time = xdf[xdf.ID == inner_value].TimeStamp
        thru_time = xdf[xdf.ID == inner_key].TimeStamp
        
        diff = (Vector(thru_time) - Vector(adv_time)).pop()
        travel_time.append(diff)
        
        SCA = xdf[xdf.ID == inner_key].SCA.values[0] # signal change at stop-bar
        if SCA == 'RG': # stopping vehicle
            decision = 'stop'
        else:
            decision = 'go'
        
        adv_gap_foll = xdf[xdf.ID == inner_value].GapFoll.values[0]
        if adv_gap_foll <= 1.5:
            car_follow = 'T'
        else:
            car_follow = 'F'
            
        file_thru.write(str(diff)+"\t"+SCA+"\t"+decision+"\t"+car_follow+"\n")
            
    i += 1
file_thru.close()
