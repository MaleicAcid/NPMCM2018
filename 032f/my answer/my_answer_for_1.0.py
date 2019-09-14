'''
我们只考虑 20 日到达或 20 日出发的航班和旅客，经过筛选，
总共需要对 303 架飞机，606 个航班进行航班-登机口方案的分配。
'''
# from future import print_function
import cplex
import data
# import mip_starts
from sys import argv

if len(argv) == 2:
    PROBLEM = str(argv[1])
else:
    PROBLEM = '1.0'
print('\n *** Solving problem {}... *** \n'.format(PROBLEM))

ANS = {
    '1.0': 47,
    '1.1': 65
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

"""
Objective function 目标函数
"""
if PROBLEM == '1.0':
    objective = [0] * x_num + [1] * xt_num # [0, 0, 0, 1, 1, 1, 1]
    # bounds
    lower_bounds = [0] * (x_num + xt_num) # 下界 [0, 0, 0, 0, 0, 0, 0]
    upper_bounds = [1] * (x_num + xt_num) # 上界 [1, 1, 1, 1, 1, 1, 1]
    # binary variables
    types = ['B'] * (x_num + xt_num) # ['B', 'B', 'B', 'B', 'B', 'B', 'B']


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

problem.parameters.timelimit.set(5 * 3600) # 5 hours 
problem.linear_constraints.add(lin_expr = constraints, 
                               senses = constraint_senses,
                               rhs = rhs,
                               names = constraint_names)
                        
print('solving...')
problem.solve()

# 查看结果 check answers 
obj = {
    '1.0': 0
}
assign = {}

for i in range(1, data.const['TotalPlane'] + 1): 
    for j in range(1, data.const['TotalGate'] + 1):
        v = problem.solution.get_values('x_{}_{}'.format(i, j)) 
        if int(v + 0.5) == 1:
            print('land plane {} at {}'.format(i, j)) 
            assign[i] = j
    # 获取临时停机位的解
    v = problem.solution.get_values('x_{}_0'.format(i)) 
    if int(v + 0.5) == 1:
        print('land plane {} at the temporary gate'.format(i)) 
        obj['1.0'] += 1
        assign[i] = 0

print('obj = {}'.format(obj)) 
print('assign = {}'.format(assign))