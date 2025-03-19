import pandas as pd
import os
from datetime import datetime

# 配置文件路径（用户可以直接修改这些路径）
FEB_FILE = "2月审核.xlsx"  # 2月审核文件路径
MAR_FILE = "3月审核.xlsx"  # 3月审核文件路径
OUTPUT_FILE = f"合并审核数据_{datetime.now().strftime('%Y%m%d')}.xlsx"  # 输出文件路径

def merge_audit_files():
    """
    合并2月和3月的审核Excel文件
    """
    print("开始合并Excel文件...")
    
    # 检查文件是否存在
    if not os.path.exists(FEB_FILE):
        print(f"错误: 2月审核文件不存在: {FEB_FILE}")
        return False
    
    if not os.path.exists(MAR_FILE):
        print(f"错误: 3月审核文件不存在: {MAR_FILE}")
        return False
    
    try:
        # 读取Excel文件
        df_feb = pd.read_excel(FEB_FILE)
        print(f"成功读取2月审核文件，包含 {len(df_feb)} 条记录")
        
        df_mar = pd.read_excel(MAR_FILE)
        print(f"成功读取3月审核文件，包含 {len(df_mar)} 条记录")
        
        # 添加月份标识列
        df_feb['审核月份'] = '2月'
        df_mar['审核月份'] = '3月'
        
        # 合并数据
        df_merged = pd.concat([df_feb, df_mar], ignore_index=True)
        print(f"合并后共有 {len(df_merged)} 条记录")
        
        # 保存合并后的数据
        df_merged.to_excel(OUTPUT_FILE, index=False)
        print(f"合并数据已保存至: {OUTPUT_FILE}")
        return True
        
    except Exception as e:
        print(f"处理过程中出错: {str(e)}")
        return False

if __name__ == "__main__":
    # 执行合并操作
    if merge_audit_files():
        print("合并操作完成!")
    else:
        print("合并操作失败，请检查错误信息。") 