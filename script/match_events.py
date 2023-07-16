import os
import ast
import pandas as pd
import collections

os.chdir(r"D:\GitHub\dilemma_zone")

# define class to subtract timestamps
class Vector():
    def __init__(self, data):
        self.data = data
    def __repr__(self):
        return repr(self.data)
    def __sub__(self, other):
        return list((a-b).total_seconds() for a, b in zip(self.data, other.data))
    
# read results of video-verified matches
with open('data/calibration/manual_adv_left_pairs.txt') as f:
    left_result = ast.literal_eval(f.read())

with open('data/calibration/manual_adv_stop_pairs.txt') as f:
    thru_result = ast.literal_eval(f.read())
    
# store accuracy parameters
left_accuracy = collections.defaultdict(list)
thru_accuracy = collections.defaultdict(list)
    
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

# empirical min, max of through travel time
tt_thru_min = 3
tt_thru_max = 11

# empirical travel time to stop/run over stop-bar det
tt_thru_ideal_stop = 6.6
tt_thru_ideal_run = 4.6

# empirical min, max, ideal left-turn travel time (from adv det to left-turn lane rear det)
tt_left_min = 4
tt_left_max = 7
tt_left_ideal = 5.4
    
# =============================================================================
# read data
# =============================================================================

num = 5 # file number (6 files in total for calibration)

# select period and file
def getFileName(year, month, day, from_hour, from_min, to_hour, to_min):
    return(str(year) + str(month).zfill(2) + str(day).zfill(2) + '_' +
           str(from_hour).zfill(2) + str(from_min).zfill(2) + '_' +
           str(to_hour).zfill(2) + str(to_min).zfill(2))

# read file, convert timestamp
path = "ignore/calibration_data"
files = list([getFileName(2022, 12, 6, 7, 45, 8, 15),
              getFileName(2022, 12, 6, 8, 45, 9, 15),
              getFileName(2022, 12, 14, 7, 45, 8, 15),
              getFileName(2022, 12, 14, 8, 45, 9, 15),
              getFileName(2022, 12, 14, 9, 45, 10, 15),
              getFileName(2023, 3, 27, 14, 15, 18, 45)])

df = pd.read_csv(os.path.join(path, files[num] + '_filtered.txt'), sep = '\t')
df.TimeStamp = pd.to_datetime(df.TimeStamp, format = '%Y-%m-%d %H:%M:%S.%f').sort_values()

# data frames for adv, stop, left-turn
adf = df[df.Det == 'adv']
sdf = df[df.Det == 'stop']
ldf = df[df.Det == 'rear']

# actuation IDs
set_id_adv = set(sorted(adf.ID))
set_id_stop = set(sorted(sdf.ID))
set_id_rear = set(sorted(ldf.ID))

set_id_adv_left = set(sorted(adf[adf.Lane == 2].ID))

# =============================================================================
# function to match events: adv det to left-turn rear det
# =============================================================================

def processCandidateMatchesAdvLeft():
    print("Processing candidate match pairs from adv to rear det \n")
    
    left_match_initial = [] # initial candidate match pairs of adv to left-turn
    
    for i in set_id_adv_left:
        adv_time = adf[adf.ID == i].TimeStamp
    
        left_candidate = {}        
        for k in set_id_rear:
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
                
    return left_match_initial
    
# =============================================================================
# function to process candidate match pairs
# =============================================================================

def processFinalMatchPairs(match_initial):
    print("Processing final match pairs \n")
    
    # convert list of nested dictionaries to flat list
    match_flat = []
    for candidate in match_initial:
        for key, value in candidate.items():
            match_flat.append({key: value})
            
    match_final = {}
    seen_target_id, seen_adv_id = [], []
    seen_match_strength_target, seen_match_strength_adv = {}, {}
    
    # function to update match pairs based on highest matching strength
    def updateMatchPairs():
        match_final[current_target_id] = list([current_adv_id, current_match_strength])
        seen_match_strength_target[current_target_id] = current_match_strength
        seen_match_strength_adv[current_adv_id] = current_match_strength
        return None
        
    for item in match_flat:
        key = list(item.keys())
        value = list(item.values())[0]
        
        current_target_id = key[0]
        current_adv_id = value[0]
        current_match_strength = value[1]
        
        if current_target_id not in seen_target_id:
            if current_adv_id not in seen_adv_id:
                seen_target_id.append(current_target_id)
                seen_adv_id.append(current_adv_id)
                updateMatchPairs()
            else: # current adv id already seen
                seen_match_strength = seen_match_strength_adv[current_adv_id]
                if current_match_strength > seen_match_strength:
                    updateMatchPairs()
        else: # current target id already seen
            if current_adv_id not in seen_adv_id:
                seen_match_strength = seen_match_strength_target[current_target_id]
                if current_match_strength > seen_match_strength:
                    updateMatchPairs()
            else: # current target id and current adv id both seen
                # look for greater matching strength out of adv and target
                seen_match_strength = max(seen_match_strength_target[current_target_id],
                                          seen_match_strength_adv[current_adv_id])
                if current_match_strength > seen_match_strength:
                    updateMatchPairs()
                    
    return match_final

# =============================================================================
# analysis of adv-rear match pairs
# =============================================================================

left_match_initial = processCandidateMatchesAdvLeft()
left_match_final = processFinalMatchPairs(left_match_initial)

# final match of adv & left id pairs
left_match_pairs = {}
for key, value in left_match_final.items():
    left_match_pairs[value[0]] = key

# set of unseen acutation ids at adv det
seen_adv_id = set(left_match_pairs.keys())
unseen_adv_id = set_id_adv_left - seen_adv_id

# update key-value pairs of unseen adv ids
left_match_pairs_full = left_match_pairs.copy()
for i in unseen_adv_id:
    left_match_pairs_full[i] = 0
left_match_pairs_full = dict(sorted(left_match_pairs_full.items()))

left_result_pairs = left_result[num+1]

# correct pairs in both match & result identified as left-turning
TP_pairs = dict(set(left_match_pairs.items()).intersection(left_result_pairs.items()))

# pairs in match not present in result (falsely classified as left-turning)
FP_pairs = dict(sorted(set(left_match_pairs.items()).difference(left_result_pairs.items())))

# pairs in result but not found in match (falsely classified as thru going)
FN_pairs = dict(sorted(set(left_result_pairs.items()).difference(left_match_pairs_full.items())))

# compute precision & recall
TP = len(TP_pairs)
FP = len(FP_pairs)
FN = len(FN_pairs)
TN = len(set_id_adv_left) - TP - FP - FN

# append accuracy parameters to dictionary
left_accuracy['TP'].append(TP)
left_accuracy['FP'].append(FP)
left_accuracy['FN'].append(FN)
left_accuracy['TN'].append(TN)

# =============================================================================
# function to match events: adv det to stop-bar det
# =============================================================================

set_id_adv_look = set_id_adv - seen_adv_id
        
def processCandidateMatchesAdvStop():
    print("Processing candidate match pairs from adv to stop-bar det \n")
    
    thru_match_initial = [] # initial candidate match pairs of adv to left-turn

    for i in set_id_adv_look:
        adv_time = adf[adf.ID == i].TimeStamp
        adv_lane = adf[adf.ID == i].Lane.values[0].astype(int)
        set_id_stop_look = set(sdf[sdf.Lane == adv_lane].ID)
    
        thru_candidate = {}
        for j in set_id_stop_look:        
            stop_time = sdf[sdf.ID == j].TimeStamp
            
            if stop_time.values[0] > adv_time.values[0]: # look forward in timestamp
                stop_sca = sdf[sdf.ID == j].SCA.values[0]
                tt_adv_stop = (Vector(stop_time) - Vector(adv_time)).pop() # travel time from adv to stop-bar
                
                if tt_adv_stop < tt_thru_min or tt_adv_stop > tt_thru_max:
                    pass
                else:
                    if stop_sca == 'RG': # if vehicle stops at stop bar
                        diff_tt_thru = abs(tt_adv_stop - tt_thru_ideal_stop)
                    else: # if vehicle runs over stop bar
                        diff_tt_thru = abs(tt_adv_stop - tt_thru_ideal_run)
                    
                    if diff_tt_thru == 0: diff_tt_thru = 0.1 # avoid zero division error
                    
                    thru_match_strength = round(1/diff_tt_thru, 2)
                    thru_candidate[j] = list([i, thru_match_strength])
                    
        print(i, ":", thru_candidate)
            
        if len(thru_candidate) != 0: # consider only non-empty candidate matches
            thru_match_initial.append(thru_candidate)
                
    return thru_match_initial

# =============================================================================
# analysis of adv-stop match pairs
# =============================================================================

thru_match_initial = processCandidateMatchesAdvStop()
thru_match_final = processFinalMatchPairs(thru_match_initial)

# final match of adv & stop-bar id pairs
thru_match_pairs = {}
for key, value in thru_match_final.items():
    thru_match_pairs[key] = value[0]
thru_match_pairs = dict(sorted(thru_match_pairs.items()))

thru_result_pairs = thru_result[num+1]

# correct pairs in both match & result
TP_pairs = dict(set(thru_match_pairs.items()).intersection(thru_result_pairs.items()))

# pairs in match that were not in result
FP_pairs = dict(sorted(set(thru_match_pairs.items()).difference(thru_result_pairs.items())))

# pairs in result but not found in match
FN_pairs = dict(sorted(set(thru_result_pairs.items()).difference(thru_match_pairs.items())))

# stop ids not in both result & match
set_stop_id_x_result = set_id_stop.difference(set(thru_result_pairs.keys()))
set_stop_id_x_match = set_id_stop.difference(set(thru_match_pairs.keys()))
TN_pairs_stop = set_stop_id_x_result.intersection(set_stop_id_x_match)

# adv ids not in both result & match
set_adv_id_x_result = set_id_adv_look.difference(set(thru_result_pairs.values()))
set_adv_id_x_match = set_id_adv_look.difference(set(thru_match_pairs.values()))
TN_pairs_adv = set_adv_id_x_result.intersection(set_adv_id_x_match)

# compute precision & recall
TP = len(TP_pairs)
FP = len(FP_pairs)
FN = len(FN_pairs)
TN = len(TN_pairs_stop) + len(TN_pairs_adv)

print("Precision: ", round(TP / (TP + FP)*100, 1))
print("Recall: ", round(TP / (TP + FN)*100, 1))

# append accuracy parameters to dictionary
thru_accuracy['TP'].append(TP)
thru_accuracy['FP'].append(FP)
thru_accuracy['FN'].append(FN)
thru_accuracy['TN'].append(TN)

# =============================================================================
# analysis of precision/recall based on full data set
# =============================================================================

def computeAccuracy(x):
    TP = sum(x['TP'])
    FP = sum(x['FP'])
    FN = sum(x['FN'])
    TN = sum(x['TN'])
    
    print("TP, FP, FN, TN: ", TP, FP, FN, TN)
    
    precision = round(TP / (TP + FP)*100, 1)
    recall = round(TP / (TP + FN)*100, 1)
    
    return {'precision': precision, 'recall': recall}

print(computeAccuracy(left_accuracy))
print(computeAccuracy(thru_accuracy))
