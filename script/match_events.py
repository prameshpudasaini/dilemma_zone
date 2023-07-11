import os
import pandas as pd
import statistics as st

os.chdir(r"D:\GitHub\dilemma_zone")

# define class to subtract timestamps
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

# read file, convert timestamp
file = getFileName(2023, 3, 27, 14, 15, 18, 45)
path = "ignore/calibration_data"

df = pd.read_csv(os.path.join(path, file + '_filtered.txt'), sep = '\t')
df.TimeStamp = pd.to_datetime(df.TimeStamp, format = '%Y-%m-%d %H:%M:%S.%f').sort_values()

# data frames for adv, stop, left-turn
adf = df[df.Det == 'adv']
sdf = df[df.Det == 'stop']
ldf = df[df.Det == 'rear']

# actuation IDs
set_id_adv = set(adf.ID)
set_id_stop = set(sdf.ID)
set_id_left = set(ldf.ID)

# =============================================================================
# parameters
# =============================================================================

# intersection geometry
len_stop = 40 # length of stop-bar det
len_adv = 5 # length of advance det
dist_det = 300 # end-end distance between stop-bar and advance det
dist_adv_stop = dist_det - len_stop

# speed
speed_limit = round(35*5280/3600, 1)
speed_max = round(50*5280/3600, 1)

# min, max of through travel time
dec = round((speed_limit**2) / (2*dist_det), 1) # constant stopping dec for veh traveling at speed limit
tt_thru_min = round(dist_adv_stop / speed_max, 1)
tt_thru_max = round(speed_limit / dec, 1)

# empirical travel time to stop/run over stop-bar det
tt_thru_ideal_stop = 6.5
tt_thru_ideal_run = 4.4

# empirical min, max, ideal left-turn travel time (from adv det to left-turn lane rear det)
tt_left_min = 4.5
tt_left_max = 6.5
tt_left_ideal = 5.5

# =============================================================================
# match events: advance det to left-turn rear det
# =============================================================================

# initial candidates match of adv to left-turn
left_match_initial = []

for i in sorted(set_id_adv):
    adv_lane = adf[adf.ID == i].Lane.values[0].astype(int)
    
    if adv_lane == 2: # consider left-turn from only left-most thru lane
        adv_time = adf[adf.ID == i].TimeStamp
    
        left_candidate = {}        
        for k in sorted(set_id_left):
            left_time = ldf[ldf.ID == k].TimeStamp
            
            if left_time.values[0] > adv_time.values[0]: # look forward in timestamp
                tt_adv_left = (Vector(left_time) - Vector(adv_time)).pop() # travel time from adv to rear
                
                if tt_adv_left < tt_left_min or tt_adv_left > tt_left_max:
                    pass
                else:
                    diff_tt_left = abs(tt_adv_left - tt_left_ideal)
                    
                    if diff_tt_left == 0: diff_tt_left = 0.1 # avoid zero division error
                    
                    left_match_strength = round(1/diff_tt_left, 2)
                    left_candidate[k] = list([i, left_match_strength])
        
        print(i, ":", left_candidate)
        
        if len(left_candidate) != 0: # consider only non-empty candidate matches
            left_match_initial.append(left_candidate)

# final candidates match of adv to left-turn based on highest matching strength
left_match_final = {}
seen_left_id = []

for candidate in left_match_initial:
    current_match_strength = 0
    
    for key, value in candidate.items():
        current_left_id = key
        current_adv_id = value[0]
        current_match_strength = value[1]
        
        if current_left_id in seen_left_id: # this left id already found a match with adv det
            seen_match_strength = left_match_final[current_left_id][1] # update seen match strength
            if current_match_strength > seen_match_strength: # check which match strength is higher
                left_match_final[current_left_id] = list([current_adv_id, current_match_strength])
        else:
            seen_left_id.append(current_left_id)
            left_match_final[current_left_id] = list([current_adv_id, current_match_strength])

# list of actuation IDs over adv det that took left-turn
seen_adv_id = []
for i in seen_left_id:
    seen_adv_id.append(left_match_final[i][0])
    
# =============================================================================
# match events: advance det to stop-bar det
# =============================================================================

thru_match_initial = []

for i in sorted(set_id_adv):
    if i not in seen_adv_id: # consider only thru moving vehicles
        adv_time = adf[adf.ID == i].TimeStamp
        adv_lane = adf[adf.ID == i].Lane.values[0].astype(int)
        adv_sca = adf[adf.ID == i].SCA.values[0]
        
        thru_candidate = {}
        for j in sorted(set_id_stop):
            stop_time = sdf[sdf.ID == j].TimeStamp
            
            if stop_time.values[0] > adv_time.values[0]: # look forward in timestamp
                stop_lane = sdf[sdf.ID == j].Lane.values[0].astype(int)
                stop_sca = sdf[sdf.ID == j].SCA.values[0]
                
                tt_adv_stop = (Vector(stop_time) - Vector(adv_time)).pop() # travel time from adv to stop-bar
                num_lane_change = abs(stop_lane - adv_lane)
                
                if tt_adv_stop < tt_thru_min or tt_adv_stop > tt_thru_max or num_lane_change > 1:
                    pass
                else:
                    if stop_sca == 'RG': # if vehicle stops at stop bar
                        diff_tt_thru = abs(tt_adv_stop - tt_thru_ideal_stop)
                    else: # if vehicle runs over stop bar
                        diff_tt_thru = abs(tt_adv_stop - tt_thru_ideal_run)
                    
                    if diff_tt_thru == 0: diff_tt_thru = 0.1 # avoid zero division error
                    
                    thru_match_strength = round(1/diff_tt_thru, 2)
                    thru_candidate[j] = list([i, thru_match_strength, num_lane_change])
                    
        print(i, ":", thru_candidate)
            
        if len(thru_candidate) != 0: # consider only non-empty candidate matches
            thru_match_initial.append(thru_candidate)

# convert list of nested dictionaries to flat list
thru_match_flat = []
for candidate in thru_match_initial:
    for key, value in candidate.items():
        thru_match_flat.append({key: value})
        
thru_match_final = {}
seen_stop_id, seen_adv_id = [], []
seen_match_strength_stop, seen_match_strength_adv = {}, {}

# function to update match pairs and seen match strength at stop-bar and adv
def updateMatchingProcess():
    thru_match_final[current_stop_id] = list([current_adv_id, current_match_strength, current_lane_change])
    seen_match_strength_stop[current_stop_id] = current_match_strength
    seen_match_strength_adv[current_adv_id] = current_match_strength

for item in thru_match_flat:
    key = list(item.keys())
    value = list(item.values())[0]
    
    current_stop_id = key[0]
    current_adv_id = value[0]
    current_match_strength = value[1]
    current_lane_change = value[2]
    
    if current_stop_id not in seen_stop_id:
        if current_adv_id not in seen_adv_id:
            seen_stop_id.append(current_stop_id)
            seen_adv_id.append(current_adv_id)
            updateMatchingProcess()
        else: # current adv id already seen
            seen_match_strength = seen_match_strength_adv[current_adv_id]
            if current_match_strength > seen_match_strength:
                updateMatchingProcess()
    else: # current stop id already seen
        if current_adv_id not in seen_adv_id:
            seen_match_strength = seen_match_strength_stop[current_stop_id]
            if current_match_strength > seen_match_strength:
                updateMatchingProcess()
        else: # current adv id already seen (look for greater matching strength of adv & stop)
            seen_match_strength = max(seen_match_strength_stop[current_stop_id], seen_match_strength_adv[current_adv_id])
            if current_match_strength > seen_match_strength:
                updateMatchingProcess()

# final match of stop-adv id pairs                
thru_match = {}
for key, value in thru_match_final.items():
    thru_match[key] = value[0]