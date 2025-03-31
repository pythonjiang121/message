from business import validate_business
from typing import Tuple, Dict, List
import pandas as pd
import os
from datetime import datetime
import re
from collections import Counter
import sqlite3
import logging
from tqdm import tqdm

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sms_audit.log'),
        logging.StreamHandler()
    ]
)

class SMSChecker:
    def __init__(self):
        self.stats = {
            'total': 0,
            'pass': 0,
            'reject': 0,
            'by_customer': Counter(),
            'by_status': Counter()
        }

    def check_sms(self, content: str, customer_name: str) -> Tuple[bool, Dict[str, str]]:
        """
        审核单条短信
        
        Args:
            content: 短信内容
            customer_name: 客户名称
            
        Returns:
            Tuple[bool, Dict]: (是否通过审核, 审核结果及原因)
        """
        results = {}

        # 从客户名称中提取业务类型
        business_type = customer_name.split('_')[0] if '_' in customer_name else customer_name

        # 业务类型审核
        business_passed, business_reason = validate_business(business_type, content, "", "")
        results['业务审核'] = business_reason
        return business_passed, results

    def update_stats(self, status: str, customer_name: str):
        """更新统计信息"""
        self.stats['total'] += 1
        self.stats['by_status'][status] += 1
        self.stats['by_customer'][customer_name] += 1
        
        if status == '通过':
            self.stats['pass'] += 1
        else:
            self.stats['reject'] += 1

    def print_stats(self):
        """打印统计信息"""
        logging.info("\n=== 审核统计信息 ===")
        logging.info(f"总处理数量: {self.stats['total']:,} 条")
        logging.info(f"通过数量: {self.stats['pass']:,} 条")
        logging.info(f"驳回数量: {self.stats['reject']:,} 条")
        
        logging.info("\n=== 按客户统计 ===")
        for customer, count in self.stats['by_customer'].most_common():
            logging.info(f"{customer}: {count:,} 条")

def process_database(db_file: str, batch_size: int = 10000) -> str:
    """
    处理数据库文件
    
    Args:
        db_file: 数据库文件路径
        batch_size: 批处理大小
        
    Returns:
        str: 输出文件路径
    """
    try:
        # 连接到数据库
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 检查必要的表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sms_records'")
        if not cursor.fetchone():
            raise ValueError("数据库中缺少必需的sms_records表")
        
        # 删除已存在的审核结果表（如果存在）
        cursor.execute("DROP TABLE IF EXISTS audit_results")
        
        # 创建审核结果表
        cursor.execute('''
        CREATE TABLE audit_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            customer_name TEXT,
            audit_status TEXT,
            audit_reason TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 获取总记录数
        cursor.execute("SELECT COUNT(*) FROM sms_records")
        total_records = cursor.fetchone()[0]
        
        # 初始化审核器
        checker = SMSChecker()
        
        # 分批处理数据
        for offset in tqdm(range(0, total_records, batch_size), desc="处理进度"):
            # 读取一批数据
            query = """
            SELECT 
                content as '短信内容',
                customer_name as '客户名称'
            FROM sms_records
            LIMIT ? OFFSET ?
            """
            df = pd.read_sql_query(query, conn, params=(batch_size, offset))
            
            # 处理每一行
            results = []
            for _, row in df.iterrows():
                passed, audit_results = checker.check_sms(
                    row['短信内容'],
                    row['客户名称']
                )
                
                status = '通过' if passed else '驳回'
                
                # 更新统计信息
                checker.update_stats(status, row['客户名称'])
                
                results.append({
                    '总体审核结果': status,
                    '业务审核结果': audit_results['业务审核']
                })
            
            # 将结果添加到DataFrame
            for key in ['总体审核结果', '业务审核结果']:
                df[key] = [result[key] for result in results]
            
            # 批量插入审核结果
            for _, row in df.iterrows():
                cursor.execute('''
                INSERT INTO audit_results (
                    content, customer_name, audit_status, audit_reason
                ) VALUES (?, ?, ?, ?)
                ''', (
                    row['短信内容'],
                    row['客户名称'],
                    row['总体审核结果'],
                    row['业务审核结果']
                ))
            
            # 每批处理完后提交事务
            conn.commit()
        
        # 生成Excel报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"审核结果_{timestamp}.xlsx"
        
        # 从数据库读取所有审核结果并保存到Excel
        query = "SELECT * FROM audit_results"
        df = pd.read_sql_query(query, conn)
        df.to_excel(output_file, index=False)
        
        # 打印统计信息
        checker.print_stats()
        
        return output_file
        
    except Exception as e:
        logging.error(f"处理数据库时出错: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """主函数"""
    try:
        # 获取输入文件
        import sys
        db_file = sys.argv[1] if len(sys.argv) > 1 else "sms_data.db"
        
        if not os.path.exists(db_file):
            logging.error(f"错误: 数据库文件 '{db_file}' 不存在")
            sys.exit(1)
            
        # 处理文件
        output_file = process_database(db_file)
        logging.info(f"审核完成，结果已保存到: {output_file}")
        
    except Exception as e:
        logging.error(f"程序运行出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 