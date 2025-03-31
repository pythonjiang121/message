import pandas as pd
import os
from datetime import datetime

def process_sms_file(input_file, output_file):
    # 设置分块大小
    chunk_size = 100000
    
    # 用于存储处理统计信息
    total_rows = 0
    processed_rows = 0
    
    # 记录开始时间
    start_time = datetime.now()
    print(f"开始处理文件: {start_time}")
    
    # 分块读取并处理文件
    for chunk_number, chunk in enumerate(pd.read_csv(input_file, chunksize=chunk_size)):
        # 更新总行数
        total_rows += len(chunk)
        
        # 在这里添加你的数据处理逻辑
        # 例如：过滤、转换、计算等
        
        # 将处理后的数据写入输出文件
        if chunk_number == 0:
            chunk.to_csv(output_file, index=False, mode='w')
        else:
            chunk.to_csv(output_file, index=False, mode='a', header=False)
        
        processed_rows += len(chunk)
        
        # 打印进度
        if (chunk_number + 1) % 10 == 0:
            current_time = datetime.now()
            elapsed_time = (current_time - start_time).total_seconds()
            print(f"已处理 {processed_rows:,} 行数据，当前速度: {processed_rows/elapsed_time:.2f} 行/秒")
    
    # 记录结束时间
    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds()
    
    print(f"\n处理完成!")
    print(f"总行数: {total_rows:,}")
    print(f"总耗时: {total_time:.2f} 秒")
    print(f"平均处理速度: {total_rows/total_time:.2f} 行/秒")

if __name__ == "__main__":
    input_file = "无标题.csv"
    output_file = "处理无标题.csv"
    process_sms_file(input_file, output_file) 