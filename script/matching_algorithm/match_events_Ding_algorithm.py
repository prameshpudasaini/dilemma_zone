# =============================================================================
# algorithm for matching acutations at advance & stop-bar detectors
# performance of Ding's algorithm (Ding et al., 2016)
# =============================================================================

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

with open('data/calibration/manual_adv_stop_pairs.txt') as f:
    thru_result = ast.literal_eval(f.read())
    
# store accuracy parameters
thru_accuracy = collections.defaultdict(list)

# =============================================================================
# files & parameters
# =============================================================================

# select period and file
def getFileName(year, month, day, from_hour, from_min, to_hour, to_min):
    return(str(year) + str(month).zfill(2) + str(day).zfill(2) + '_' +
           str(from_hour).zfill(2) + str(from_min).zfill(2) + '_' +
           str(to_hour).zfill(2) + str(to_min).zfill(2))

path = "ignore/calibration_data"
files = list([getFileName(2022, 12, 6, 7, 45, 8, 15),
              getFileName(2022, 12, 6, 8, 45, 9, 15),
              getFileName(2022, 12, 14, 7, 45, 8, 15),
              getFileName(2022, 12, 14, 8, 45, 9, 15),
              getFileName(2022, 12, 14, 9, 45, 10, 15),
              getFileName(2023, 3, 27, 14, 15, 18, 45)])

# detector length & spacing parameters
len_stop = 40 # length of stop-bar det
len_adv = 5 # length of advance det
dist_det = 300 # end-end distance between stop-bar and advance det
dist_adv_stop = dist_det - len_stop

# vehicle length parameters
veh_length = 22
eff_length_adv = len_adv + veh_length
eff_length_stop = len_stop + veh_length

# other parameters
acc_max = 6
    
# =============================================================================
# match acutation events: Ding's algorithm
# =============================================================================

def matchAcutuationEvents(file_num):
    df = pd.read_csv(os.path.join(path, files[file_num] + '_filtered.txt'), sep = '\t')
    df.TimeStamp = pd.to_datetime(df.TimeStamp, format = '%Y-%m-%d %H:%M:%S.%f').sort_values()
    
    # data frames for adv, stop, left-turn
    adf = df[df.Det == 'adv']
    sdf = df[df.Det == 'stop']

    # actuation IDs
    set_id_adv = set(sorted(adf.ID))
    set_id_stop = set(sorted(sdf.ID))
    
    print("Processing candidate match pairs from adv to stop-bar det")
    match_initial = [] # initial candidate match pairs of adv to left-turn
    
    for i in set_id_adv:
        adv_time = adf[adf.ID == i].TimeStamp
        adv_occ = adf[adf.ID == i].OccTime.values[0]
        adv_lane = adf[adf.ID == i].Lane.values[0].astype(int)
        set_id_stop_look = set(sdf[sdf.Lane == adv_lane].ID)
        
        adv_vel = eff_length_adv / adv_occ
        tt_max = 2*dist_adv_stop / adv_vel
        tt_min = 2*dist_adv_stop / (adv_vel + ((adv_vel)**2 + 2*acc_max*dist_adv_stop)**(1/2))
        
        thru_candidate = {}
        for j in set_id_stop_look:
            stop_time = sdf[sdf.ID == j].TimeStamp
            
            if (stop_time.values[0] > adv_time.values[0]): # look forward in timestamp
                tt_adv_stop = (Vector(stop_time) - Vector(adv_time)).pop()
                
                if tt_adv_stop < tt_min or tt_adv_stop > tt_max: # search within time window
                    pass
                else:
                    stop_occ = sdf[sdf.ID == j].OccTime.values[0]
                    stop_vel = eff_length_stop / stop_occ
                    
                    tt_ideal = 2*dist_adv_stop / (adv_vel + stop_vel) # ideal travel time
                    error = abs(1 - tt_ideal/tt_adv_stop)
                    thru_match_strength = round(1 - error, 2)
                    
                    thru_candidate[j] = list([i, thru_match_strength])
            
        if len(thru_candidate) != 0: # consider only non-empty candidate matches
            match_initial.append(thru_candidate)
            
    print("Processing final match pairs")
    match_flat = []
    
    # convert list of nested dictionaries to flat list
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

    # final match of adv & stop-bar id pairs
    thru_match_pairs = {}
    for key, value in match_final.items():
        thru_match_pairs[key] = value[0]
    thru_match_pairs = dict(sorted(thru_match_pairs.items()))
    
    thru_result_pairs = thru_result[file_num+1]
    
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
    set_adv_id_x_result = set_id_adv.difference(set(thru_result_pairs.values()))
    set_adv_id_x_match = set_id_adv.difference(set(thru_match_pairs.values()))
    TN_pairs_adv = set_adv_id_x_result.intersection(set_adv_id_x_match)

    # compute precision & recall
    TP = len(TP_pairs)
    FP = len(FP_pairs)
    FN = len(FN_pairs)
    TN = len(TN_pairs_stop) + len(TN_pairs_adv)
    
    print("Performance: ", "\n", "TP, FP, FN, TN: ", TP, FP, FN, TN)
    print("Precision: ", round(TP / (TP + FP), 1))
    print("Recall: ", round(TP / (TP + FN), 1), "\n")

    # append accuracy parameters to dictionary
    thru_accuracy['TP'].append(TP)
    thru_accuracy['FP'].append(FP)
    thru_accuracy['FN'].append(FN)
    thru_accuracy['TN'].append(TN)
    
    return thru_accuracy

# =============================================================================
# analysis of precision/recall based on full data set
# =============================================================================

for file_num in range(len(files)):
    print("Running algorithm for file: ", file_num)
    matchAcutuationEvents(file_num)

def computeAccuracy(x):
    TP = sum(x['TP'])
    FP = sum(x['FP'])
    FN = sum(x['FN'])
    TN = sum(x['TN'])
    
    print("Overall performance: ", "\n", "TP, FP, FN, TN: ", TP, FP, FN, TN)
    
    precision = round(TP / (TP + FP), 4)
    recall = round(TP / (TP + FN), 4)
    f1_score = round(2/(1/precision + 1/recall), 4)
    
    return {'precision': precision, 'recall': recall, 'f1_score': f1_score}

print(computeAccuracy(thru_accuracy))
