from signature import validate_signature
from content import SMSContentValidator
from business import validate_business
from account_type import validate_account
from typing import Tuple, List, Dict
import pandas as pd
import json
import os
from datetime import datetime



class SMSChecker:
    def __init__(self):
        """初始化短信审核器"""
        # 加载姓氏数据
        try:
            with open('surnames.json', 'r', encoding='utf-8') as f:
                self.surnames = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load surnames.json: {e}")
            self.surnames = []
        
        # 初始化内容验证器
        self.content_validator = SMSContentValidator()

    def check_sms(self, signature: str, content: str, business_type: str, account_type: str) -> Tuple[bool, Dict[str, str]]:
        """
        审核单条短信
        
        Args:
            signature: 短信签名
            content: 短信内容
            business_type: 业务类型
            account_type : 客户账户
            
        Returns:
            Tuple[bool, Dict]: (是否通过审核, 各项审核结果及原因)
        """
        results = {}

        # 特例判断：特定签名或客户账户直接通过
        if signature == "饿了么" or account_type in ["巨辰移动行业", "河南旺呈三网行业", "巨辰移动会销（汽车4s）", "巨辰联通会销（汽车4s）"]:
            results['签名审核'] = "特例直接通过"
            results['内容审核'] = "特例直接通过"
            results['业务审核'] = "特例直接通过"
            results['账户审核'] = "特例直接通过"
            return True, results
            
        # 特定关键词签名直接通过
        special_keywords = ["国家", "部", "电力"]
        if any(keyword in signature for keyword in special_keywords):
            results['签名审核'] = "关键词直接通过"
            results['内容审核'] = "关键词直接通过"
            results['业务审核'] = "关键词直接通过"
            results['账户审核'] = "关键词直接通过"
            return True, results
        
        # 1. 签名审核
        sig_passed, sig_reason = validate_signature(signature)
        results['签名审核'] = sig_reason
        
        # 2. 内容审核
        content_passed, content_reason = self.content_validator.validate_content(content)
        results['内容审核'] = content_reason
        
        # 3. 业务类型审核
        business_passed, business_reason = validate_business(business_type, content, signature)
        results['业务审核'] = business_reason

        # 判断最终审核结果
        all_passed = sig_passed and content_passed and business_passed 
        return all_passed, results

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
        required_columns = ['短信签名', '短信内容', '客户业务类型', '客户账户']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Excel文件缺少必需的列: {', '.join(missing_columns)}")
        
        # 初始化审核器
        checker = SMSChecker()
        
        # 存储审核结果
        results = []
        passed_count = 0
        
        # 处理每一行
        for index, row in df.iterrows():
            passed, audit_results = checker.check_sms(
                row['短信签名'],
                row['短信内容'],
                row['客户业务类型'],
                row['客户账户']
            )
            
            if passed:
                status = '通过'
                passed_count += 1
            else:
                status = '驳回'
                
            results.append({
                '总体审核结果': status,
                '签名审核结果': audit_results['签名审核'],
                '内容审核结果': audit_results['内容审核'],
                '业务审核结果': audit_results['业务审核'],
                
            })
        
        # 将结果添加到DataFrame
        for key in ['总体审核结果', '签名审核结果', '内容审核结果', '业务审核结果']:
            df[key] = [result[key] for result in results]
        
        # 生成输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"审核结果_{timestamp}.xlsx"
        
        # 保存结果
        df.to_excel(output_file, index=False, engine='openpyxl')
        
        # 打印统计信息
        total = len(df)
        print(f"\n审核完成:")
        print(f"总计: {total} 条")
        print(f"通过: {passed_count} 条")
        print(f"驳回: {total - passed_count} 条")
        print(f"\n结果已保存至: {output_file}")
        
        return output_file
        
    except Exception as e:
        print(f"处理文件时出错: {str(e)}")
        raise

def main():
    """主函数"""
    try:
        # 获取输入文件
        import sys
        input_file = sys.argv[1] if len(sys.argv) > 1 else "3月反诈审核.xlsx"
        
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