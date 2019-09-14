"""
This file contains Solver class for solving problem 1 to 3. There are mainly three handlers for three problems respectfully:
-	solve1():
solve1 function applies extended interval scheduling algorithm to arrange planes to different categories of gates, and further assign planes to each gate.
See 4.3 for more details.
-	solve2_swap():
Base on the arrangement of solve1 function, solver2_swap function adopts Simulate Anneal concept to keep swapping planes of two different gates trying to reduce total procedure time.
See 5.3 for more details.
-	solve3_cooling() 
solve3_cooling function supplements the evaluation function by walking time and metro time and keeps other logic unchanged.
See 6.3 for more details.
"""

import data
import checker

class Solver:
    def init (self):
        self.data = data.Data()
        self.plane_dict = self.data.copy_plane_dict() 
        self.plane_list = self.data.copy_plane_list() 
        self.gate_cato_list = self.data.copy_gate_cato_list() 
        self.gate_dict = self.data.copy_gate_dict()

    def mini_temp(self, plane_dict=None, gate_cato_list=None): 
        if plane_dict is None:
            plane_dict = self.plane_dict
        if gate_cato_list is None:
            gate_cato_list = self.gate_cato_list 
        temp = [] # 停在临时停机位的飞机编号
        idx_list = plane_dict.keys()
        idx_list.sort(key=lambda idx: (plane_dict[idx]['arrive_time_int'],plane_dict[idx]['leave_time_int']),reverse=True)
        for gate_cato in gate_cato_list: 
            gate_cato['plane_queue'] = [] 
            gate_cato['end_time'] = []
            if len(gate_cato['gate_list']) > 0: 
                gate_cato['plane_queue'].append([]) 
                gate_cato['end_time'].append(1e9)
        for plane_idx in idx_list:
            plane_info = plane_dict[plane_idx] 
            tar_cato = None
            tar_queue = None
            tar_endt = None
            for i in range(len(gate_cato_list)): 
                gate_cato = gate_cato_list[i] 
                cato = gate_cato['cato'] 
                end_time = gate_cato['end_time']
                # check if plane match the category
                if plane_info['arrive_type'] not in cato[0]: 
                    continue
                if plane_info['leave_type'] not in cato[1]:
                    continue
                if plane_info['size'] != cato[2]: 
                    continue
                for j in range(len(end_time)):
                    if plane_info['leave_time_int'] <= end_time[j]: 
                        if tar_cato is None or tar_endt > end_time[j]:
                            tar_cato = i 
                            tar_queue = j
                            tar_endt = end_time[j]
                # gate category is arranged with increasing priority 
                # found one and break
                if tar_cato is not None: 
                    break
            if tar_cato is None:
                # move to temporary areat 
                temp.append(plane_idx)
            else:
                # 有停机位
                gate_cato_list[tar_cato]['plane_queue'][tar_queue].append(plane_idx) 
                gate_cato_list[tar_cato]['end_time'][tar_queue] = plane_info['arrive_time_int'] - 45 
                if tar_endt == 1e9:
                    if len(gate_cato_list[tar_cato]['plane_queue']) \
                        < len(gate_cato_list[tar_cato]['gate_list']): 
                    # add new queue
                    gate_cato_list[tar_cato]['plane_queue'].append([])
                    gate_cato_list[tar_cato]['end_time'].append(1e9) 
        print("Un-arranged: " + str(len(temp)))
        return temp

def solve1(self): 
    arrangement = {}
    temp = self.mini_temp() 
    for idx in temp:
        arrangement[idx] = 0
    for gate_cato in self.gate_cato_list:
        for i in range(len(gate_cato['plane_queue'])): 
            for plane_idx in gate_cato['plane_queue'][i]:
                arrangement[plane_idx] = gate_cato['gate_list'][i] 
    return arrangement

def solve2_swap(self, T=100, r=0.99): 
    from math import exp
    from random import random

    arrangement = {}
    c = checker.Checker()

    # initial arrangement
    queue2gate = {gate_cato: {} for gate_cato in range(len(self.gate_cato_list))} 
    temp = self.mini_temp()
    for idx in temp: 
        arrangement[idx] = 0
    for i in range(len(self.gate_cato_list)): 
        gate_cato = self.gate_cato_list[i]
        for j in range(len(gate_cato['plane_queue'])): 
            queue2gate[i][j] = j
            for plane_idx in gate_cato['plane_queue'][j]: 
                arrangement[plane_idx] = gate_cato['gate_list'][j]

    tar_proc_time = c.get_proc_time(arrangement) 
    old_proc_time = None
    while old_proc_time is None or old_proc_time > tar_proc_time: 
        old_proc_time = tar_proc_time
        for i in range(len(self.gate_cato_list)):
            queue = self.gate_cato_list[i]['plane_queue'] 
            gate = self.gate_cato_list[i]['gate_list'] 
            for q1 in range(len(queue)):
                for q2 in range(q1 + 1, len(queue)): 
                    g1 = queue2gate[i][q1]
                    g2 = queue2gate[i][q2] 
                    new_arrangement = dict(arrangement)
                    # swap g1 and g2
                    for plane_idx in queue[q1]: 
                        new_arrangement[plane_idx] = gate[g2]
                    for plane_idx in queue[q2]: 
                        new_arrangement[plane_idx] = gate[g1]
                    new_proc_time = c.get_proc_time(new_arrangement) 
                    if new_proc_time < tar_proc_time:
                        print('proc time: {} -> {}'.format(tar_proc_time, new_proc_time)) 
                        tar_proc_time = new_proc_time
                        arrangement = dict(new_arrangement) 
                        queue2gate[i][q1] = g2 
                        queue2gate[i][q2] = g1
                        break
                    elif new_proc_time > tar_proc_time: 
                        dE = tar_proc_time - new_proc_time 
                        if exp(dE / T) > random():
                            print('{} cooling: proc time: {} -> {}'.format(exp(dE / T),tar_proc_time, new_proc_time))
                            tar_proc_time = new_proc_time 
                            arrangement = dict(new_arrangement) 
                            queue2gate[i][q1] = g2 
                            queue2gate[i][q2] = g1
                            break
                        T *= r
                if old_proc_time > tar_proc_time: 
                    break 
            if old_proc_time > tar_proc_time:
                break
    return arrangement

def solve3_cooling(self): 
    from math import exp
    from random import random

    arrangement = {}
    c = checker.Checker()

    # initial arrangement
    queue2gate = {gate_cato: {} for gate_cato in range(len(self.gate_cato_list))} 
    temp = self.mini_temp()
    for idx in temp:
        arrangement[idx] = 0
    for i in range(len(self.gate_cato_list)): 
        gate_cato = self.gate_cato_list[i]
        for j in range(len(gate_cato['plane_queue'])):
            queue2gate[i][j] = j
            for plane_idx in gate_cato['plane_queue'][j]: 
                arrangement[plane_idx] = gate_cato['gate_list'][j]

    tar_tense = c.get_all_time(arrangement) 
    old_tense = None
    T = 1
    r = 0.01
    while old_tense is None or old_tense > tar_tense: 
        old_tense = tar_tense
        for i in range(len(self.gate_cato_list)):
            queue = self.gate_cato_list[i]['plane_queue'] 
            gate = self.gate_cato_list[i]['gate_list'] 
            for q1 in range(len(queue)):
                for q2 in range(q1 + 1, len(queue)): 
                    g1 = queue2gate[i][q1]
                    g2 = queue2gate[i][q2] 
    new_arrangement = dict(arrangement)
    # swap g1 and g2
    for plane_idx in queue[q1]:
        new_arrangement[plane_idx] = gate[g2]
    for plane_idx in queue[q2]: 
        new_arrangement[plane_idx] = gate[g1]
    new_tense = c.get_all_time(new_arrangement) 
    if new_tense < tar_tense:
        print('tense: {} -> {}'.format(tar_tense, new_tense)) 
        tar_tense = new_tense
        arrangement = dict(new_arrangement) 
        queue2gate[i][q1] = g2 queue2gate[i][q2] = g1
        break
    elif new_tense > tar_tense: 
        dE = tar_tense - new_tense 
        if T == 0: continue
        if exp(dE / T) > random():
            print('{} cooling: tense: {} -> {}'.format(exp(dE / T), tar_tense, new_tense)) 
            tar_tense = new_tense
            arrangement = dict(new_arrangement) 
            queue2gate[i][q1] = g2 queue2gate[i][q2] = g1
            break
        T *= r
if old_tense > tar_tense: break if old_tense > tar_tense: break
return arrangement



if name == ' main ':
 
c = checker.Checker()

def print_temp(arrangement): c.check(arrangement)
cnt = 0
for i in arrangement:
if arrangement[i] == 0: cnt += 1
print(cnt)
solver = Solver() # p1
arrangement = solver.solve1() print(arrangement) print_temp(arrangement)

# p2
arrangement = solver.solve2_swap() print(arrangement) print(c.get_proc_time(arrangement))

# p3
arrangement = solver.solve3_cooling() print(arrangement) print(c.get_all_time(arrangement))
