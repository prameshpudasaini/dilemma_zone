import os
import pandas as pd
import json

os.chdir(r"D:\GitHub\dilemma_zone")
input_path = "ignore/dz_data/processed"

# define class to subtract timestamps
class Vector():
    def __init__(self, data):
        self.data = data
    def __repr__(self):
        return repr(self.data)
    def __sub__(self, other):
        return list((a-b).total_seconds() for a, b in zip(self.data, other.data))
    
# detector length & spacing parameters
len_stop = 40 # length of stop-bar det
len_adv = 5 # length of advance det
dist_det = 300 # end-end distance between stop-bar and advance det
dist_adv_stop = dist_det - len_stop

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

def matchAcutuationEvents():
    cdf = df.copy(deep = True) # copied df
    
    # data frames for adv, stop, left-turn
    adf = cdf[cdf.Det == 'adv']
    sdf = cdf[cdf.Det == 'stop']
    ldf = cdf[cdf.Det == 'rear']
    
    # actuation IDs
    set_id_adv = set(sorted(adf.ID))
    set_id_stop = set(sorted(sdf.ID))
    set_id_rear = set(sorted(ldf.ID))
    set_id_adv_left = set(sorted(adf[adf.Lane == 2].ID))
    
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
            
    left_match_final = processCandidateMatches(left_match_initial)

    # final match of adv & left id pairs
    left_match_pairs = {}
    for key, value in left_match_final.items():
        left_match_pairs[value[0]] = key
     
    # =========================================================================
    # analysis of adv-stop match pairs
    # =========================================================================

    # set of seen/unseen acutation ids at adv det
    seen_adv_id = set(left_match_pairs.keys())
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

    thru_match_final = processCandidateMatches(thru_match_initial)

    # final match of adv & stop-bar id pairs
    thru_match_pairs = {}
    for key, value in thru_match_final.items():
        thru_match_pairs[key] = value[0]
    thru_match_pairs = dict(sorted(thru_match_pairs.items()))
    
    return thru_match_pairs

# =============================================================================
# match events in bulk
# =============================================================================

# list of raw files
file_list = os.listdir(input_path)

result = {}

# match events for each file
for file in file_list:
    print("**************************************************")
    print("Processing events for file: ", file, "\n")
    
    # read data
    df = pd.read_csv(os.path.join(input_path, file), sep = '\t')
    df.TimeStamp = pd.to_datetime(df.TimeStamp, format = '%Y-%m-%d %H:%M:%S.%f').sort_values()
    
    result[file] = matchAcutuationEvents()

match_count = 0    
for value in result.values():
    match_count += len(value)
    
with open("data/dz_analysis/match_results.txt", 'w') as f:
    json.dump(result, f)
