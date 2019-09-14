
# =TEXT(B2,"yyyy-mm-dd") & TEXT(C2," hh:mm")
'''
飞机转场记录号 到达日期	 到达时刻
到达航班	到达类型	飞机型号
出发日期	出发时刻	出发航班
出发类型	上线机场 下线机场
'''

# 登机口   终端厅     区域	    到达类型    出发类型    机体类别

import pandas as pd
data = {}
plane_file = pd.read_excel('20day_plane.xlsx')
plane_file = pd.DataFrame(plane_file)


print("获取到所有的值:\n{0}".format(data))#格式化输出