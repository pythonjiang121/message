from business import validate_business
from typing import Tuple, Dict
import pandas as pd
import os
from datetime import datetime
import re
from collections import Counter

class SMSChecker:

    def check_sms(self, signature: str, content: str, business_type: str, account_type: str) -> Tuple[bool, Dict[str, str]]:
        """
        审核单条短信
        
        Args:
            signature: 短信签名
            content: 短信内容
            business_type: 业务类型
            account_type: 客户类型
            
        Returns:
            Tuple[bool, Dict]: (是否通过审核, 审核结果及原因)
        """
        results = {}

        # 业务类型审核（包含客户类型审核）
        business_passed, business_reason = validate_business(business_type, content, signature)
        results['业务审核'] = business_reason

        return business_passed, results

def process_excel(input_file: str) -> str:
    """
    处理Excel文件
    
    Args:
        input_file: 输入文件路径
        
    Returns:
        str: 输出文件路径
    """
    try:
        # 检查是否安装了openpyxl
        try:
            import openpyxl
        except ImportError:
            print("正在安装必要的依赖 openpyxl...")
            import subprocess
            subprocess.check_call(["pip", "install", "openpyxl"])
            print("openpyxl 安装完成")

        # 读取Excel文件
        df = pd.read_excel(input_file, engine='openpyxl')
        required_columns = ['短信签名', '短信内容', '客户业务类型', '客户类型']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Excel文件缺少必需的列: {', '.join(missing_columns)}")
        
        # 初始化审核器
        checker = SMSChecker()
        
        # 存储审核结果
        results = []
        code_pass_count = 0
        
        # 处理每一行
        for _, row in df.iterrows():
            passed, audit_results = checker.check_sms(
                row['短信签名'],
                row['短信内容'],
                row['客户业务类型'],
                row['客户类型']
            )
            
            if passed:
                status = '通过'
                code_pass_count += 1
            else:
                status = '驳回'
                
            results.append({
                '总体审核结果': status,
                '业务审核结果': audit_results['业务审核']
            })
        
        # 将结果添加到DataFrame
        for key in ['总体审核结果', '业务审核结果']:
            df[key] = [result[key] for result in results]
        
        # 生成输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"审核结果_{timestamp}.xlsx"
        
        # 保存结果
        df.to_excel(output_file, index=False, engine='openpyxl')
        
        # 计算统计信息
        total_count = len(df)
        code_reject_count = total_count - code_pass_count
        matched_count = len(df[df['审核结果'] == df['总体审核结果']])
        match_rate = (matched_count / total_count) * 100
        
        # 打印统计信息
        print("\n=== 审核统计信息 ===")
        print(f"总数据量: {total_count} 条")
        print(f"代码通过: {code_pass_count} 条")
        print(f"代码驳回: {code_reject_count} 条")
        print(f"匹配数据量: {matched_count} 条")
        print(f"匹配率: {match_rate:.2f}%")
        
        # 分析不一致数据
        df_discrepancy = df[df['审核结果'] != df['总体审核结果']]
        human_reject_code_pass = df_discrepancy[
            (df_discrepancy['审核结果'] == '驳回') & 
            (df_discrepancy['总体审核结果'] == '通过')
        ]
        human_pass_code_reject = df_discrepancy[
            (df_discrepancy['审核结果'] == '通过') & 
            (df_discrepancy['总体审核结果'] == '驳回')
        ]
        
        print(f"\n=== 不一致数据分析 ===")
        print(f"人工驳回但代码通过: {len(human_reject_code_pass)} 条")
        print(f"人工通过但代码驳回: {len(human_pass_code_reject)} 条")
        
        # 分析人工驳回但代码通过的高频词
        if len(human_reject_code_pass) > 0:
            print("\n=== 人工驳回但代码通过的高频词分析（前10） ===")
            words = []
            for content in human_reject_code_pass['短信内容']:
                if isinstance(content, str):
                    # 使用正则表达式匹配中文词组（2个或更多字符）
                    words.extend(re.findall(r'[\u4e00-\u9fa5]{2,}', content))
            
            # 统计词频
            word_counts = Counter(words)
            
            # 输出前10个高频词
            for word, count in word_counts.most_common(10):
                print(f"{word}: {count}次")
            
        # 保存不一致数据
        if len(human_reject_code_pass) > 0:
            human_reject_code_pass.to_excel(f"人工驳回代码通过数据_{timestamp}.xlsx", index=False)
        if len(human_pass_code_reject) > 0:
            human_pass_code_reject.to_excel(f"人工通过代码驳回数据_{timestamp}.xlsx", index=False)
                
        return output_file
        
    except Exception as e:
        print(f"处理文件时出错: {str(e)}")
        raise

def main():
    """主函数"""
    try:
        # 获取输入文件
        import sys
        input_file = sys.argv[1] if len(sys.argv) > 1 else "合并审核.xlsx"
        
        if not os.path.exists(input_file):
            print(f"错误: 输入文件 '{input_file}' 不存在")
            sys.exit(1)
            
        # 处理文件
        output_file = process_excel(input_file)
        print(f"审核完成，结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"程序运行出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
    