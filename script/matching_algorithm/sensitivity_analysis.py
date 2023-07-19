# =============================================================================
# proposed algorithm for matching acutations at advance & left-turn rear detector
# =============================================================================

import os
import ast
import pandas as pd
import numpy as np
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

# =============================================================================
# files & parameters
# =============================================================================

# select period and file
def getFileName(year, month, day, from_hour, from_min, to_hour, to_min):
    return(str(year) + str(month).zfill(2) + str(day).zfill(2) + '_' +
           str(from_hour).zfill(2) + str(from_min).zfill(2) + '_' +
           str(to_hour).zfill(2) + str(to_min).zfill(2))

# read file
path = "ignore/calibration_data"
files = list([getFileName(2022, 12, 6, 7, 45, 8, 15),
              getFileName(2022, 12, 6, 8, 45, 9, 15),
              getFileName(2022, 12, 14, 7, 45, 8, 15),
              getFileName(2022, 12, 14, 8, 45, 9, 15),
              getFileName(2022, 12, 14, 9, 45, 10, 15),
              getFileName(2023, 3, 27, 14, 15, 18, 45)])

# read results of video-verified matches
with open('data/calibration/manual_adv_left_pairs.txt') as f:
    left_result = ast.literal_eval(f.read())

with open('data/calibration/manual_adv_stop_pairs.txt') as f:
    thru_result = ast.literal_eval(f.read())

# detector length & spacing parameters
len_stop = 40 # length of stop-bar det
len_adv = 5 # length of advance det
dist_det = 300 # end-end distance between stop-bar and advance det
dist_adv_stop = dist_det - len_stop

# empirical min, max of through travel time
tt_thru_min = 3
tt_thru_max = 11

# empirical min, max, ideal left-turn travel time (from adv det to left-turn lane rear det)
tt_left_min = 4
tt_left_max = 7
tt_left_ideal = 5.4

# =============================================================================
# function to process candidate match pairs
# =============================================================================

def processCandidateMatches(match_initial):    
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
# sets of data frames and actuation ids
# =============================================================================

def matchAcutuationEvents(file_num, tt_thru_ideal_stop, tt_thru_ideal_run):
    df = pd.read_csv(os.path.join(path, files[file_num] + '_filtered.txt'), sep = '\t')
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
    
    # video-verified matches
    left_result_pairs = left_result[file_num + 1]
    thru_result_pairs = thru_result[file_num + 1]
    
    # =========================================================================
    # function to match events: adv det to left-turn rear det
    # =========================================================================
    
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
        
        # print(i, ":", left_candidate)
        if len(left_candidate) != 0: # consider only non-empty candidate matches
            left_match_initial.append(left_candidate)
     
    # =========================================================================
    # analysis of adv-rear match pairs
    # =========================================================================

    left_match_final = processCandidateMatches(left_match_initial)

    # final match of adv & left id pairs
    left_match_pairs = {}
    for key, value in left_match_final.items():
        left_match_pairs[value[0]] = key

    # set of unseen acutation ids at adv det
    seen_adv_id = set(left_match_pairs.keys())
    # unseen_adv_id = set_id_adv_left - seen_adv_id

    # # update key-value pairs of unseen adv ids
    # left_match_pairs_full = left_match_pairs.copy()
    # for i in unseen_adv_id:
    #     left_match_pairs_full[i] = 0
    # left_match_pairs_full = dict(sorted(left_match_pairs_full.items()))
    
    # # correct pairs in both match & result identified as left-turning
    # left_TP_pairs = dict(set(left_match_pairs.items()).intersection(left_result_pairs.items()))

    # # pairs in match not present in result (falsely classified as left-turning)
    # left_FP_pairs = dict(sorted(set(left_match_pairs.items()).difference(left_result_pairs.items())))

    # # pairs in result but not found in match (falsely classified as thru going)
    # left_FN_pairs = dict(sorted(set(left_result_pairs.items()).difference(left_match_pairs_full.items())))

    # # compute precision & recall
    # left_TP = len(left_TP_pairs)
    # left_FP = len(left_FP_pairs)
    # left_FN = len(left_FN_pairs)
    # left_TN = len(set_id_adv_left) - left_TP - left_FP - left_FN
    
    # try:
    #     left_precision = round(left_TP / (left_TP + left_FP), 2)
    #     left_recall = round(left_TP / (left_TP + left_FN), 2)
    # except ZeroDivisionError:
    #     left_precision, left_recall = 1, 1
    
    # =========================================================================
    # function to match events: adv det to stop-bar det
    # =========================================================================

    set_id_adv_look = set_id_adv - seen_adv_id
    
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
                    
        # print(i, ":", thru_candidate)
        if len(thru_candidate) != 0: # consider only non-empty candidate matches
            thru_match_initial.append(thru_candidate)
            
    # =========================================================================
    # analysis of adv-stop match pairs
    # =========================================================================

    thru_match_final = processCandidateMatches(thru_match_initial)

    # final match of adv & stop-bar id pairs
    thru_match_pairs = {}
    for key, value in thru_match_final.items():
        thru_match_pairs[key] = value[0]
    thru_match_pairs = dict(sorted(thru_match_pairs.items()))

    # correct pairs in both match & result
    thru_TP_pairs = dict(set(thru_match_pairs.items()).intersection(thru_result_pairs.items()))

    # pairs in match that were not in result
    thru_FP_pairs = dict(sorted(set(thru_match_pairs.items()).difference(thru_result_pairs.items())))

    # pairs in result but not found in match
    thru_FN_pairs = dict(sorted(set(thru_result_pairs.items()).difference(thru_match_pairs.items())))

    # stop ids not in both result & match
    set_stop_id_x_result = set_id_stop.difference(set(thru_result_pairs.keys()))
    set_stop_id_x_match = set_id_stop.difference(set(thru_match_pairs.keys()))
    thru_TN_pairs_stop = set_stop_id_x_result.intersection(set_stop_id_x_match)

    # adv ids not in both result & match
    set_adv_id_x_result = set_id_adv_look.difference(set(thru_result_pairs.values()))
    set_adv_id_x_match = set_id_adv_look.difference(set(thru_match_pairs.values()))
    thru_TN_pairs_adv = set_adv_id_x_result.intersection(set_adv_id_x_match)

    # compute precision & recall
    thru_TP = len(thru_TP_pairs)
    thru_FP = len(thru_FP_pairs)
    thru_FN = len(thru_FN_pairs)
    thru_TN = len(thru_TN_pairs_stop) + len(thru_TN_pairs_adv)
    
    # thru_precision = round(thru_TP / (thru_TP + thru_FP), 2)
    # thru_recall = round(thru_TP / (thru_TP + thru_FN), 1)
    
    # # append accuracy parameters to dictionary
    # left_accuracy['TP'].append(left_TP)
    # left_accuracy['FP'].append(left_FP)
    # left_accuracy['FN'].append(left_FN)
    # left_accuracy['TN'].append(left_TN)
    
    thru_accuracy['TP'].append(thru_TP)
    thru_accuracy['FP'].append(thru_FP)
    thru_accuracy['FN'].append(thru_FN)
    thru_accuracy['TN'].append(thru_TN)
    
    return None

# =============================================================================
# sensitivity analysis of thru ideal travel time
# =============================================================================

sensitivity = open("data/calibration/sensitivity.txt", 'w')

# based on 99% confidence interval
iqr_stop = np.arange(5.3, 7.9, 0.1)
iqr_run = np.arange(3.7, 6, 0.1)

for i in iqr_stop:
    for j in iqr_run:
        # store accuracy parameters
        left_accuracy = collections.defaultdict(list)
        thru_accuracy = collections.defaultdict(list)
        
        for file_num in range(len(files)):
            print("File, stop, run: ", file_num, j, i)
            matchAcutuationEvents(file_num, i, j)

        def computeAccuracy(x):
            TP = sum(x['TP'])
            FP = sum(x['FP'])
            FN = sum(x['FN'])
            
            precision = round(TP / (TP + FP), 4)
            recall = round(TP / (TP + FN), 4)
            f1_score = round(2/(1/precision + 1/recall), 4)
            
            return {'precision': precision, 'recall': recall, 'f1_score': f1_score}
        
        value = computeAccuracy(thru_accuracy)
        print("Result:", value, "\n")
        
        precision = value['precision']
        recall = value['recall']
        f1_score = value['f1_score']
        
        str_value = str(precision) + "\t" + str(recall) + "\t" + str(f1_score)
        sensitivity.write(str(round(i,1)) + "\t" + str(round(j,1)) + "\t" + str_value + "\n")

sensitivity.close()
