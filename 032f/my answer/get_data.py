
# D:\ScientificComputation\Anaconda3\python.exe
import xlrd
print('hello')
# 文件路径
file_path = r'E:/pythonspace/032/data/input.xlsx'
#文件路径的中文转码，如果路径非中文可以跳过
file_path = file_path.decode('utf-8')
#获取数据
data = xlrd.open_workbook(file_path)
#获取sheet 此处有图注释（见图1）
table = data.sheet_by_name('Tickets')
 
#获取总行数
nrows = table.nrows
 
#获取总列数
ncols = table.ncols
 
#获取一行的数值，例如第5行
rowvalue = table.row_values(5)
 
#获取一列的数值，例如第4列
col_values = table.col_values(4)
 
#获取一个单元格的数值，例如第5行第6列
cell_value = table.cell(5,4).value
 
print(rowvalue)
print(col_values)