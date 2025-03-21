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
        business_passed, business_reason = validate_business(business_type, content, signature, account_type)
        
        # 从审核结果中提取分数
        try:
            # 使用正则表达式提取分数
            score_match = re.search(r'总分: (\d+\.?\d*)', business_reason)
            if score_match:
                score = float(score_match.group(1))
                # 60-80分需要人工审核
                if 60 <= score < 80:
                    business_passed = None  # 使用None表示需要人工审核
                    business_reason = f"需人工审核 (总分: {score:.2f})"
        except Exception as e:
            print(f"提取分数时出错: {str(e)}")
            
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
        required_columns = ['短信签名', '短信内容', '客户业务类型', '客户类型', '审核结果']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Excel文件缺少必需的列: {', '.join(missing_columns)}")
        
        # 初始化审核器
        checker = SMSChecker()
        
        # 存储审核结果
        results = []
        code_pass_count = 0
        code_manual_count = 0
        code_reject_count = 0
        
        # 处理每一行
        for _, row in df.iterrows():
            passed, audit_results = checker.check_sms(
                row['短信签名'],
                row['短信内容'],
                row['客户业务类型'],
                row['客户类型']
            )
            
            if passed is None:
                status = '待人工审核'
                code_manual_count += 1
            elif passed:
                status = '通过'
                code_pass_count += 1
            else:
                status = '驳回'
                code_reject_count += 1
                
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
        
        # 代码判断结果统计
        print("\n=== 代码判断结果统计 ===")
        print(f"判断总数: {total_count} 条")
        print(f"通过数量: {code_pass_count} 条")
        print(f"驳回数量: {code_reject_count} 条")
        print(f"待人工审核数量: {code_manual_count} 条")
        
        # 人工审核结果统计
        manual_pass_count = len(df[df['审核结果'] == '通过'])
        manual_reject_count = len(df[df['审核结果'] == '驳回'])
        print("\n=== 人工审核结果统计 ===")
        print(f"通过数量: {manual_pass_count} 条")
        print(f"驳回数量: {manual_reject_count} 条")
        
        # 匹配统计（排除待人工审核的数据）
        df_for_matching = df[df['总体审核结果'] != '待人工审核']
        matched_count = len(df_for_matching[df_for_matching['审核结果'] == df_for_matching['总体审核结果']])
        match_rate = ((matched_count+code_manual_count) / len(df_for_matching)) * 100 if len(df_for_matching) > 0 else 0
        print("\n=== 匹配统计（不含待人工审核数据）===")
        print(f"参与匹配计算数量: {len(df_for_matching)} 条")
        print(f"匹配数量: {matched_count} 条")
        print(f"匹配率: {match_rate:.2f}%")


            # 统计不匹配情况
        code_pass_manual_reject = len(df[(df['总体审核结果'] == '通过') & (df['审核结果'] == '驳回')])
        code_reject_manual_pass = len(df[(df['总体审核结果'] == '驳回') & (df['审核结果'] == '通过')])

        print("\n=== 不匹配情况分析 ===")
        print(f"代码通过但人工驳回数量: {code_pass_manual_reject} 条")
        print(f"代码驳回但人工通过数量: {code_reject_manual_pass} 条")

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
    