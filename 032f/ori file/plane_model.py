# types = ['B'] * (x_num + xt_num + z_num)

# from future import print_function
import cplex
import data
import mip_starts
from sys import argv

if len(argv) == 2:
    PROBLEM = str(argv[1])
else:
    PROBLEM = '1.0'
print('\n *** Solving problem {}... *** \n'.format(PROBLEM))

ANS = {
    '1.0': 47,
    '1.1': 65 # 没用到?
}
data = data.Data() 
"""
Linear programming model based on planes
初始化模型
"""
problem = cplex.Cplex()

"""
Objective function:
maximize the number of parked planes, which is equal to minimizing the number of planes assigned to the temporary gate
最小化临时停机位的使用
"""
problem.objective.set_sense(problem.objective.sense.minimize)

"""
Variables:
x_i_j: assign plane i to gate j
x_i_j：将飞机i分配给机位j
"""
names = []
x_num = 0
xt_num = 0 # 分配的临时机位数?
# assigned to a normal gate 分配给正常机位
for i in range(1, data.const['TotalPlane'] + 1): 
    for j in range(1, data.const['TotalGate'] + 1):
        names.append('x_{ }_{ }'.format(i, j))
        x_num += 1
# assigned to the temporary gate 分配给临时机位
for i in range(1, data.const['TotalPlane'] + 1):
    names.append('x_{}_0'.format(i))
    xt_num += 1

if PROBLEM == '1.1':
    # 1.1要求min{z}
    # z_j: 是否使用了机位j whether to use gate j 
    z_num = 0
    for j in range(1, data.const['TotalGate'] + 1): # 列出所有的机位
        names.append('z_{}'.format(j))
        z_num += 1
if PROBLEM == '2.0' or PROBLEM == '3.0':
# a_i1_i2_k: transfer from plane i to plane j using cost k 
    a_num = 0 # ??
    for (i1, i2) in data.const['TransferNumber']: # 转运的飞机??数量 和 TotalPlane有什么不同
        # NOTE: 0代表临时停机位路线 starts from 0 

        for k in range(0, data.const['TotalCost'][PROBLEM] + 1): # 总的路线数 0-16
            names.append('a_{}_{}_{}'.format(i1, i2, k))
            a_num += 1
    # y_i1_i2: whether successfully transfer from plane i to plane j
    y_num = 0
    for (i1, i2) in data.const['TransferNumber']: 
        names.append('y_{}_{}'.format(i1, i2)) 
        y_num += 1
    # cost_i1_i2: cost to transfer from plane i to plane j 
    cost_num = 0
    for (i1, i2) in data.const['TransferNumber']: 
        names.append('cost_{}_{}'.format(i1, i2)) 
        cost_num += 1
"""
Objective function 目标函数
"""

if PROBLEM == '1.0':
    objective = [0] * x_num + [1] * xt_num # [0, 0, 0, 1, 1, 1, 1] 临时停机位尽可能小
    # bounds 确定上下界
    lower_bounds = [0] * (x_num + xt_num) # 下界 [0, 0, 0, 0, 0, 0, 0]
    upper_bounds = [1] * (x_num + xt_num) # 上界 [1, 1, 1, 1, 1, 1, 1]
    # binary variables
    types = ['B'] * (x_num + xt_num) # ['B', 'B', 'B', 'B', 'B', 'B', 'B']
elif PROBLEM == '1.1':
    objective = [0] * (x_num + xt_num) + [1] * z_num # 因为作者想复用当前文件,所以name变量 []前面有很多0
    # bounds
    lower_bounds = [0] * (x_num + xt_num + z_num) 
    upper_bounds = [1] * (x_num + xt_num + z_num) 
    # binary variables
    types = ['B'] * (x_num + xt_num + z_num)
elif PROBLEM == '2.0' or PROBLEM == '3.0':
    if PROBLEM == '2.0':
        objective = [0] * (x_num + xt_num + a_num + y_num) 
        for (i1, i2) in data.const['TransferNumber']:
            objective.append(data.const['TransferNumber'][(i1, i2)])
    else:
        objective = [0] * (x_num + xt_num + a_num + y_num) 
        for (i1, i2) in data.const['TransferNumber']:
            objective.append(1.0 * data.const['TransferNumber'][(i1, i2)] / data.const['ConnectTime'][(i1,i2)])
    # bounds
    lower_bounds = [0] * (x_num + xt_num + a_num + y_num + cost_num)
    upper_bounds = [1] * (x_num + xt_num + a_num + y_num) + [10 * 24 * 60] * cost_num # some are binary
    types = ['B'] * (x_num + xt_num + a_num + y_num) + ['I'] * cost_num
else:
    raise NameError('No such problem: {}'.format(PROBLEM))
# add variables
problem.variables.add(obj = objective, 
                      lb = lower_bounds, 
                      ub = upper_bounds,
                      names = names, 
                      types = types)

"""
Constraints 约束
"""
constraints = [] 
constraint_names = [] 
constraint_senses = [] 
rhs = []

# arrival constraint 到达约束
# 约束 1：保证任一个飞机都分配至并仅分配至 1 个登机口(包含临时登机口)
for i in range(1, data.const['TotalPlane'] + 1): 
    c = [[], []]
    for j in range(1, data.const['TotalGate'] + 1): 
        c[0].append('x_{}_{}'.format(i, j)) 
        c[1].append(1)
    # 分配到临时机位
    c[0].append('x_{}_0'.format(i))
    c[1].append(1) 
    constraint_names.append('c_{}'.format(len(constraints))) 
    constraints.append(c)
    rhs.append(1) 
    constraint_senses.append('E') # E就是等号 =1

def add_zero_x_constraint(i, j):
    c = [['x_{}_{}'.format(i, j)], [1]] 
    constraint_names.append('c_{}'.format(len(constraints))) 
    constraints.append(c)
    rhs.append(0) 
    constraint_senses.append('E')  # 如果类型不同就 =0
    return

# identical constraint 类型一致性约束
# 约束 2：保证任一个飞机都分配到属性相同的登机口
for i in range(1, data.const['TotalPlane'] + 1): 
    plane_info = data.filtered_plane_dict[i]
    for j in range(1, data.const['TotalGate'] + 1): 
        gate_info = data.filtered_gate_dict[j]
        # 起飞和到达类型需相同 same size, arrive type and leave type
        if plane_info['size'] != gate_info['size']: 
            add_zero_x_constraint(i, j)
            continue
        # D国内 I国际 DI可国内可国际
        if (gate_info['arrive_type'] != 'DI' and plane_info['arrive_type'] != gate_info['arrive_type']): 
            add_zero_x_constraint(i, j)
            continue
        if (gate_info['leave_type'] != 'DI' and plane_info['leave_type'] != gate_info['leave_type']): 
            add_zero_x_constraint(i, j)
            continue

# 在下个for循环中被调用
# 约束 3：分配在同一登机口的两飞机之间的空挡间隔时间必须大于等于 45 分钟
def can_same_gate(p1, p2):
    at1 = p1['arrive_time_int'] 
    at2 = p2['arrive_time_int'] 
    lt1 = p1['leave_time_int'] 
    lt2 = p2['leave_time_int']
    if at2 - lt1 >= 45: return True 
    if at1 - lt2 >= 45: return True 
    return False

# gap constraint 
for j in range(1, data.const['TotalGate'] + 1):
    for i1 in range(1, data.const['TotalPlane'] + 1):
        for i2 in range(i1 + 1, data.const['TotalPlane'] + 1): # 取出两架飞机
            p1 = data.filtered_plane_dict[i1]
            p2 = data.filtered_plane_dict[i2] 
            if not can_same_gate(p1, p2): # (4-6)如果时间有交集 
                c = [['x_{}_{}'.format(i1, j), 'x_{}_{}'.format(i2, j)], [1, 1]] 
                constraint_names.append('c_{}'.format(len(constraints))) 
                constraints.append(c)
                rhs.append(1) 
                constraint_senses.append('L') # x_ai_j + x_a2_j <=1 
# 约束 3 END

# 约束 5 若有一个飞机被派给某个登机口,则该登机口就被使用
if PROBLEM == '1.1':
    M = data.const['TotalPlane'] + 1
    # gate usage constraint
    for j in range(1, data.const['TotalGate'] + 1):
        c = [[], []]
        for i in range(1, data.const['TotalPlane'] + 1):
            c[0].append('x_{}_{}'.format(i, j))
            c[1].append(1)
        c[0].append('z_{}'.format(j))
        c[1].append(-M)
        constraint_names.append('c_{}'.format(len(constraints)))
        constraints.append(c)
        rhs.append(0)
        constraint_senses.append('L')
        # 取飞机数M=3 x_1_1+x_2_1+x_3_1 <= 3z_1

# gate number constraint
# 分配到临时停机位的数量=47
c = [[], []]
for i in range(1, data.const['TotalPlane'] + 1): 
    c[0].append('x_{}_0'.format(i)) 
    c[1].append(1)
constraint_names.append('c_{}'.format(len(constraints))) 
constraints.append(c)
rhs.append(ANS['1.0']) 
constraint_senses.append('E') # =47 ??

if PROBLEM == '2.0' or PROBLEM == '3.0':
    # gate number constraint
    c = [[], []]
    for i in range(1, data.const['TotalPlane'] + 1): 
        c[0].append('x_{}_0'.format(i)) 
        c[1].append(1)
    constraint_names.append('c_{}'.format(len(constraints))) 
    constraints.append(c)
    rhs.append(ANS['1.0']) 
    constraint_senses.append('E')

    # constraint between (x_i1_j1, x_i2_j2) and a_i1_i2_k
    for (i1, i2) in data.const['TransferNumber']: 
        p1 = data.filtered_plane_dict[i1]
        p2 = data.filtered_plane_dict[i2] 
        if i1 == i2:
            for j in range(1, data.const['TotalGate'] + 1): 
                g = data.filtered_gate_dict[j]
                if PROBLEM == '2.0':
                    key = (p1['arrive_type'], g['hall'], p1['leave_type'], g['hall']) 
                elif PROBLEM == '3.0':
                    key = (p1['arrive_type'], g['hall'], g['area'],p1['leave_type'], g['hall'], g['area']) 
                k = data.const['k'][PROBLEM][key]
                c = [['x_{}_{}'.format(i1, j), 'a_{}_{}_{}'.format(i1, i2, k)], [2, -1]]
                constraint_names.append('c_{}'.format(len(constraints))) 
                constraints.append(c)
                rhs.append(1) 
                constraint_senses.append('L')
            c = [['x_{}_0'.format(i1), 'a_{}_{}_0'.format(i1, i2)], [1, -1]] 
            constraint_names.append('c_{}'.format(len(constraints))) 
            constraints.append(c)
            rhs.append(0) 
            constraint_senses.append('L') 
            continue

        for j1 in range(1, data.const['TotalGate'] + 1): 
            g1 = data.filtered_gate_dict[j1]
            for j2 in range(1, data.const['TotalGate'] + 1):
                g2 = data.filtered_gate_dict[j2]
                if PROBLEM == '2.0':
                    key = (p1['arrive_type'], g1['hall'], p2['leave_type'], g2['hall']) 
                elif PROBLEM == '3.0':
                    key = (p1['arrive_type'], g1['hall'], g1['area'],p2['leave_type'], g2['hall'], g2['area'])
                k = data.const['k'][PROBLEM][key]
                c = [['x_{}_{}'.format(i1, j1), 'x_{}_{}'.format(i2, j2), 'a_{}_{}_{}'.format(i1, i2, k)],
                [1, 1, -1]]
                constraint_names.append('c_{}'.format(len(constraints))) 
                constraints.append(c)
                rhs.append(1) 
                constraint_senses.append('L')
        # x_i1_0 <= a_i1_i2_0
        c = [['x_{}_0'.format(i1), 'a_{}_{}_0'.format(i1, i2)], [1, -1]] 
        constraint_names.append('c_{}'.format(len(constraints))) 
        constraints.append(c)
        rhs.append(0)
 
        constraint_senses.append('L')
        c = [['x_{}_0'.format(i2), 'a_{}_{}_0'.format(i1, i2)], [1, -1]] 
        constraint_names.append('c_{}'.format(len(constraints))) 
        constraints.append(c)
        rhs.append(0) 
        constraint_senses.append('L')

    # force some k that a_i1_i2_k = 1
    for (i1, i2) in data.const['TransferNumber']: 
        c = [[], []]
        # NOTE: starts from 0
        for k in range(0, data.const['TotalCost'][PROBLEM] + 1): 
            c[0].append('a_{}_{}_{}'.format(i1, i2, k)) 
            c[1].append(1)
        constraint_names.append('c_{}'.format(len(constraints))) 
        constraints.append(c)
        rhs.append(1) 
        constraint_senses.append('E')

    # constraint between y_i1_i2 and a_i1_i2_k 
    M = 10 * 24 * 60
    for (i1, i2) in data.const['TransferNumber']: 
        p1 = data.filtered_plane_dict[i1]
        p2 = data.filtered_plane_dict[i2] 
        arrive_time = p1['arrive_time_int'] 
        leave_time = p2['leave_time_int'] 
        diff = leave_time - arrive_time
        c = [[], []]
        for k in range(1, data.const['TotalCost'][PROBLEM] + 1): 
            c[0].append('a_{}_{}_{}'.format(i1, i2, k))
            c[1].append(data.const['Cost'][PROBLEM][k])
        c[0].append('y_{}_{}'.format(i1, i2)) 
        c[1].append(M)
        constraint_names.append('c_{}'.format(len(constraints))) 
        constraints.append(c)
        rhs.append(M + diff) 
        constraint_senses.append('L') 
        # y_i1_i2 >= a_i1_i2_0
        c = [['y_{}_{}'.format(i1, i2), 'a_{}_{}_0'.format(i1, i2)], [1, -1]] 
        constraint_names.append('c_{}'.format(len(constraints))) 
        constraints.append(c)
        rhs.append(0) 
        constraint_senses.append('G')

    # constraint between y_i1_i2 and cost_i1_i2
    for (i1, i2) in data.const['TransferNumber']: 
        c = [['cost_{}_{}'.format(i1, i2)], [1]]
        for k in range(1, data.const['TotalCost'][PROBLEM] + 1): 
            c[0].append('a_{}_{}_{}'.format(i1, i2, k))
            c[1].append(-data.const['Cost'][PROBLEM][k])
        c[0].append('y_{}_{}'.format(i1, i2)) 
        c[1].append(1)
        constraint_names.append('c_{}'.format(len(constraints))) 
        constraints.append(c)
        rhs.append(1) 
        constraint_senses.append('G')
        c = [['cost_{}_{}'.format(i1, i2), 'y_{}_{}'.format(i1, i2)], [1, 60 * 6]] 
        constraint_names.append('c_{}'.format(len(constraints))) 
        constraints.append(c)
        rhs.append(60 * 6) 
        constraint_senses.append('G')

    # NOTE: hack
    for (i1, i2) in data.const['TransferNumber']:
        c = [['y_{}_{}'.format(i1, i2)], [1]]
        constraint_names.append('c_{}'.format(len(constraints))) 
        constraints.append(c)
        rhs.append(1) 
        constraint_senses.append('E')

problem.parameters.timelimit.set(5 * 3600) # 5 hours 
problem.linear_constraints.add(lin_expr = constraints, 
                               senses = constraint_senses, #条件 比如 E 代表 =
                               rhs = rhs, # 右边的数
                               names = constraint_names)

if PROBLEM == '2.0':
    problem.MIP_starts.add(mip_starts.assign2, problem.MIP_starts.effort_level.solve_MIP)
elif PROBLEM == '3.0':
    problem.MIP_starts.add(mip_starts.assign3, problem.MIP_starts.effort_level.solve_MIP)

print('solving...')
problem.solve()

# check answers 
obj = {
    '1.0': 0
}
assign = {}

for i in range(1, data.const['TotalPlane'] + 1): 
    for j in range(1, data.const['TotalGate'] + 1):
        v = problem.solution.get_values('x_{}_{}'.format(i, j)) 
        if int(v + 0.5) == 1: # +0.5 ??
            print('land plane {} at {}'.format(i, j)) 
            assign[i] = j
    v = problem.solution.get_values('x_{}_0'.format(i)) 
    if int(v + 0.5) == 1:
        print('land plane {} at the temporary gate'.format(i)) 
        obj['1.0'] += 1
        assign[i] = 0

if PROBLEM == '1.1': 
    obj['1.1'] = 0
    for j in range(1, data.const['TotalGate'] + 1):
        # 1.1 额外处理结果中的z_i
        v = problem.solution.get_values('z_{}'.format(j)) 
        if int(v + 0.5) == 1:
            print('use gate {}'.format(j)) 
            obj['1.1'] += 1

if PROBLEM == '2.0': 
    obj['2.0'] = 0
    for (i1, i2) in data.const['TransferNumber']:
        v = problem.solution.get_values('cost_{}_{}'.format(i1, i2)) 
        v = int(v + 0.5)
        print('assign 1 person from plane {} to plane {} costs {} min'.format(i1, i2, v)) 
        obj['2.0'] += v

print('obj = {}'.format(obj)) 
print('assign = {}'.format(assign))
