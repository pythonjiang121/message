from business import validate_business
from typing import Tuple, Dict
import pandas as pd
import os
from datetime import datetime
import re
from collections import Counter
from ai_check import AIAuditor
import json


class SMSChecker:

    def check_sms(self, signature: str, content: str, business_type: str, account_type: str) -> Tuple[bool, Dict[str, str]]:
        """
        审核单条短信
        
        Args:
            signature: 短信签名
            content: 短信内容
            business_type: 产品类型
            account_type: 账户类型
            
        Returns:
            Tuple[bool, Dict]: (是否放行审核, 操作类型及原因)
        """
        results = {}

        # 产品类型审核（包含账户类型审核）
        business_passed, business_reason = validate_business(business_type, content, signature, account_type)
        
        # 从操作类型中提取分数
        try:
            # 使用正则表达式提取分数
            score_match = re.search(r'总分: (\d+\.?\d*)', business_reason)
            if score_match:
                score = float(score_match.group(1))
                
                
        except Exception as e:
            print(f"提取分数时出错: {str(e)}")
            
        results['业务审核'] = business_reason

        return business_passed, results

# checkexcel.py 中的修改部分

def process_excel(input_file: str) -> str:
    """
    处理Excel文件，包含规则审核和AI二次审核两个环节
    
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
        required_columns = ['短信签名', '短信内容', '产品类型', '账户类型', '操作类型']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Excel文件缺少必需的列: {', '.join(missing_columns)}")

        # 初始化审核器
        checker = SMSChecker()
        
        # 存储操作类型
        results = []
        code_pass_count = 0
        code_reject_count = 0
        
        # 第一轮：纯规则审核
        print("\n=== 开始规则审核 ===")
        for index, row in df.iterrows():
            try:
                # 只进行规则审核
                passed, audit_results = checker.check_sms(
                    row['短信签名'],
                    row['短信内容'],
                    row['产品类型'],
                    row['账户类型']
                )
                
                if passed:
                    status = '放行'
                    code_pass_count += 1
                else:
                    status = '失败'
                    code_reject_count += 1
                    
                results.append({
                    '总体操作类型': status,
                    '业务操作类型': audit_results['业务审核']
                })
            except Exception as e:
                results.append({
                    '总体操作类型': '处理错误',
                    '业务操作类型': f'处理错误: {str(e)}'
                })

        # 将规则审核结果添加到DataFrame
        for key in ['总体操作类型', '业务操作类型']:
            df[key] = [result[key] for result in results]
        
        # # 打印DataFrame的前5行，查看是否正确更新
        # print("\n=== 查看DataFrame更新情况 ===")
        # print("DataFrame前5行:")
        # for i in range(min(5, len(df))):
        #     print(f"行 {i}:")
        #     print(f"  短信签名: {df.iloc[i]['短信签名']}")
        #     print(f"  短信内容: {df.iloc[i]['短信内容'][:30]}...")  # 只显示前30个字符
        #     print(f"  产品类型: {df.iloc[i]['产品类型']}")
        #     print(f"  总体操作类型: {df.iloc[i]['总体操作类型']}")
        #     print(f"  业务操作类型: {df.iloc[i]['业务操作类型']}")               
        # return
    
        # 第二轮：AI审核
        print("\n=== 开始AI二次审核 ===")
        # 筛选出规则审核通过的短信
        passed_sms = df[df['总体操作类型'] == '放行']
        
        if not passed_sms.empty:
            # 准备AI审核数据
            ai_audit_list = []
            for _, row in passed_sms.iterrows():
                try:
                    score = 100.0  # 默认分数
                    try:
                        score_match = re.search(r'总分: (\d+\.?\d*)', row['业务操作类型'])
                        if score_match:
                            score = float(score_match.group(1))
                        elif "直接通过" in row['业务操作类型']:
                            score = 100.0  # 直接通过给高分
                    except Exception as e:
                        print(f"提取分数时出错: {str(e)}")
                    
                    ai_audit_list.append({
                        "signature": row['短信签名'],
                        "content": row['短信内容'],
                        "business_type": row['产品类型'],
                        "rule_score": score,
                        "rule_reason": row['业务操作类型']
                    })
                except Exception as e:
                    print(f"准备AI审核数据时出错: {str(e)}")
                    continue
            
            # 进行AI审核
            from ai_check import AIAuditor
            auditor = AIAuditor()
            ai_results = auditor.batch_audit(ai_audit_list)
            
            # 统计AI审核结果
            ai_reject_count = 0
            
            # 更新AI审核结果
            for result in ai_results:
                try:
                    idx = df[df['短信签名'] == result['sms']['signature']].index[0]
                    df.loc[idx, 'AI审核结果'] = '通过' if result['passed'] else '驳回'
                    df.loc[idx, 'AI审核详情'] = json.dumps(result['details'], ensure_ascii=False)
                    
                    # 如果AI审核驳回，更新总体操作类型
                    if not result['passed']:
                        df.loc[idx, '总体操作类型'] = '失败'
                        code_pass_count -= 1
                        code_reject_count += 1
                        ai_reject_count += 1
                except Exception as e:
                    print(f"更新审核结果时出错: {str(e)}")
            
            print(f"AI审核总数: {len(ai_audit_list)} 条")
            print(f"AI驳回数量: {ai_reject_count} 条")
            print(f"AI驳回率: {(ai_reject_count/len(ai_audit_list)*100):.2f}%" if ai_audit_list else "0.00%")

        # 将结果添加到DataFrame
        for key in ['总体操作类型', '业务操作类型']:
            df[key] = [result[key] for result in results]
        
        # 生成输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"操作类型_{timestamp}.xlsx"
        
        # 保存结果
        df.to_excel(output_file, index=False, engine='openpyxl')
        
        # 计算统计信息
        total_count = len(df)
        
        # 代码判断结果统计
        print("\n=== 代码判断结果统计 ===")
        print(f"判断总数: {total_count} 条")
        print(f"放行数量: {code_pass_count} 条")
        print(f"失败数量: {code_reject_count} 条")
        # 计算错误数量
        error_count = total_count - code_pass_count - code_reject_count
        if error_count > 0:
            print(f"处理错误数量: {error_count} 条")
        rejection_rate = (code_reject_count / total_count) * 100 if total_count > 0 else 0
        print(f"代码失败率: {rejection_rate:.2f}%")
        
        # 匹配统计（
        df_for_matching = df[df['总体操作类型'] ]
        # 只统计代码和人工结果都为放行或失败的情况
        matched_count = len(df_for_matching[
            ((df_for_matching['总体操作类型'] == '放行') & (df_for_matching['操作类型'] == '放行')) |
            ((df_for_matching['总体操作类型'] == '失败') & (df_for_matching['操作类型'] == '失败'))
        ])
        match_rate = (matched_count / len(df_for_matching)) * 100 if len(df_for_matching) > 0 else 0
        print("\n=========== 匹配统计==========")
        print(f"参与匹配计算数量: {len(df_for_matching)} 条")
        print(f"匹配数量: {matched_count} 条")
        print(f"匹配率: {match_rate:.2f}%")

        # 统计不匹配情况
        code_pass_manual_reject = len(df[(df['总体操作类型'] == '放行') & (df['操作类型'] == '失败')])
        code_reject_manual_pass = len(df[(df['总体操作类型'] == '失败') & (df['操作类型'] == '放行')])

        print("\n=== 不匹配情况分析 ===")
        print(f"代码放行但人工失败数量: {code_pass_manual_reject} 条")
        print(f"代码失败但人工放行数量: {code_reject_manual_pass} 条")

        return output_file
        
    except Exception as e:
        import traceback
        print(f"处理文件时出错: {str(e)}")
        print(f"错误详情:\n{traceback.format_exc()}")
        raise

def main():
    """主函数"""
    try:
        import sys
        input_file = sys.argv[1] if len(sys.argv) > 1 else "3月审核记录.xlsx"
        
        if not os.path.exists(input_file):
            print(f"错误: 输入文件 '{input_file}' 不存在")
            sys.exit(1)
            
        # 处理文件
        output_file = process_excel(input_file)
        print(f"\n审核完成，结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"程序运行出错: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
    