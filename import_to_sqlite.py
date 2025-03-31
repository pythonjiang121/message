import pandas as pd
import sqlite3
from datetime import datetime
import os

def create_database():
    # 连接到SQLite数据库（如果不存在则创建）
    conn = sqlite3.connect('sms_data.db')
    cursor = conn.cursor()
    
    # 创建表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sms_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone_number TEXT,
        content TEXT,
        customer_name TEXT,
        gateway_name TEXT,
        submit_time DATETIME,
        receive_time DATETIME,
        message_count INTEGER,
        status TEXT,
        remarks TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建索引以提高查询性能
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_phone_number ON sms_records(phone_number)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON sms_records(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_submit_time ON sms_records(submit_time)')
    
    conn.commit()
    return conn

def import_data(conn, csv_file):
    # 设置分块大小
    chunk_size = 100000
    
    # 记录开始时间
    start_time = datetime.now()
    print(f"开始导入数据: {start_time}")
    
    # 分块读取CSV文件并导入数据库
    total_rows = 0
    for chunk_number, chunk in enumerate(pd.read_csv(csv_file, chunksize=chunk_size)):
        # 转换日期时间格式
        chunk['提单时间'] = pd.to_datetime(chunk['提单时间'], format='%d/%m/%Y %H:%M:%S')
        chunk['接收时间'] = pd.to_datetime(chunk['接收时间'], format='%d/%m/%Y %H:%M:%S')
        
        # 重命名列以匹配数据库表结构
        chunk = chunk.rename(columns={
            '号码': 'phone_number',
            '内容': 'content',
            '客户名称': 'customer_name',
            '网关名称': 'gateway_name',
            '提单时间': 'submit_time',
            '接收时间': 'receive_time',
            '条数': 'message_count',
            '状态': 'status',
            '备注': 'remarks'
        })
        
        # 将数据写入数据库
        chunk.to_sql('sms_records', conn, if_exists='append', index=False)
        
        total_rows += len(chunk)
        
        # 打印进度
        if (chunk_number + 1) % 10 == 0:
            current_time = datetime.now()
            elapsed_time = (current_time - start_time).total_seconds()
            print(f"已导入 {total_rows:,} 行数据，当前速度: {total_rows/elapsed_time:.2f} 行/秒")
    
    # 记录结束时间
    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds()
    
    print(f"\n导入完成!")
    print(f"总行数: {total_rows:,}")
    print(f"总耗时: {total_time:.2f} 秒")
    print(f"平均导入速度: {total_rows/total_time:.2f} 行/秒")

def main():
    # 创建数据库连接
    conn = create_database()
    
    # 导入数据
    import_data(conn, "无标题.csv")
    
    # 关闭数据库连接
    conn.close()

if __name__ == "__main__":
    main() 