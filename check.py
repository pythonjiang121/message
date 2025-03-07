from signature import validate_signature, load_surnames
from content import SMSContentValidator
from business import validate_business
from typing import Tuple, List, Dict
import os
import pandas as pd
from datetime import datetime

class SMSChecker:
    def __init__(self):
        """初始化短信审核器"""
        # 加载姓氏数据
        current_dir = os.path.dirname(os.path.abspath(__file__))
        surnames_path = os.path.join(current_dir, "surnames.json")
        self.surnames = load_surnames(surnames_path)
        
        # 初始化内容验证器
        self.content_validator = SMSContentValidator()

    def check_single_sms(self, signature: str, content: str, business_type: str, account_type: str) -> Tuple[bool, Dict[str, Tuple[bool, str]]]:
        """
        审核单条短信
        
        Args:
            signature: 短信签名
            content: 短信内容
            business_type: 业务类型
            account_type: 账户类型
            
        Returns:
            Tuple[bool, Dict]: (是否全部通过, 详细审核结果)
        """
        # 1. 签名审核
        signature_result = validate_signature(signature, self.surnames)
        
        # 2. 内容审核
        content_result = self.content_validator.validate_content(content)
        
        # 3. 业务类型审核
        business_result = validate_business(business_type, content, account_type)
        
        # 整合审核结果
        results = {
            "签名审核": signature_result,
            "内容审核": content_result,
            "业务审核": (business_result, "业务审核通过" if business_result else "业务审核不通过")
        }
        
        # 判断是否全部通过
        all_passed = all(result[0] for result in results.values())
        
        return all_passed, results

    def batch_check_sms(self, df: pd.DataFrame) -> List[Tuple[bool, Dict]]:
        """
        批量审核短信
        
        Args:
            df: 包含短信数据的DataFrame
            
        Returns:
            List[Tuple]: 审核结果列表，每个元素为 (是否通过, 详细结果)
        """
        results = []
        for _, row in df.iterrows():
            result = self.check_single_sms(
                row['短信签名'],
                row['短信内容'],
                row['客户业务类型'],
                row['账户类型']
            )
            results.append(result)
        return results

    def export_results(self, df: pd.DataFrame, results: List[Tuple[bool, Dict]], output_file: str = None) -> str:
        """
        将审核结果导出到Excel文件
        
        Args:
            df: 原始数据DataFrame
            results: 审核结果列表
            output_file: 输出文件路径（可选）
            
        Returns:
            str: 输出文件路径
        """
        # 添加审核结果列
        df = df.copy()  # 创建副本避免修改原始数据
        
        # 添加结果列
        df['总体审核结果'] = ['通过' if passed else '驳回' for passed, _ in results]
        
        # 安全地获取审核结果
        def get_result(result_dict, key):
            try:
                return result_dict[key][1] if not result_dict[key][0] else '通过'
            except (KeyError, IndexError, TypeError):
                return '未知'
        
        # 添加各项审核结果
        for i, (_, result_dict) in enumerate(results):
            df.loc[i, '签名审核结果'] = get_result(result_dict, '签名审核')
            df.loc[i, '内容审核结果'] = get_result(result_dict, '内容审核')
            df.loc[i, '业务审核结果'] = get_result(result_dict, '业务审核')
        
        # 生成输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"审核结果_{timestamp}.xlsx"
        
        # 保存文件
        print(f"\n正在保存审核结果到: {output_file}")
        df.to_excel(output_file, index=False, engine='openpyxl')
        
        return output_file

def process_excel_file(input_file: str, output_file: str = None) -> str:
    """
    处理Excel文件的完整流程
    
    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径（可选）
        
    Returns:
        str: 输出文件路径
    """
    print(f"开始处理文件: {input_file}")
    
    try:
        # 1. 读取数据
        df = pd.read_excel(input_file)
        
        # 验证必需的列是否存在
        required_columns = ['短信签名', '短信内容', '客户业务类型', '账户类型']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Excel文件缺少必需的列: {', '.join(missing_columns)}")
            
        print("\n数据预览:")
        print("\n列名:", df.columns.tolist())
        print("\n前两行数据:")
        print(df.head(2).to_string())
            
    except Exception as e:
        raise ValueError(f"读取Excel文件失败: {str(e)}")
    
    # 2. 初始化审核器
    checker = SMSChecker()
    
    # 3. 批量审核
    print(f"\n开始审核 {len(df)} 条数据...")
    results = checker.batch_check_sms(df)
    
    # 4. 统计结果
    total = len(results)
    passed = sum(1 for passed, _ in results if passed)
    failed = total - passed
    
    print(f"\n审核完成:")
    print(f"总计: {total} 条")
    print(f"通过: {passed} 条")
    print(f"拒绝: {failed} 条")
    print(f"通过率: {(passed/total*100):.2f}%")
    
    # 5. 导出结果
    return checker.export_results(df, results, output_file)

def main():
    """主函数"""
    try:
        # 显示当前工作目录
        print(f"当前工作目录: {os.getcwd()}")
        
        # 处理命令行参数
        import sys
        # 默认输入文件名
        default_input = "短信内容审核记录.xlsx"
        input_file = sys.argv[1] if len(sys.argv) > 1 else default_input
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        
        # 检查输入文件是否存在
        if not os.path.exists(input_file):
            print(f"错误: 输入文件 '{input_file}' 不存在")
            print(f"当前目录下的文件:")
            os.system('ls -l')
            sys.exit(1)
            
        # 检查输入文件是否可读
        if not os.access(input_file, os.R_OK):
            print(f"错误: 没有权限读取文件 '{input_file}'")
            sys.exit(1)
            
        # 处理文件
        try:
            output_path = process_excel_file(input_file, output_file)
            print(f"\n处理完成！结果已保存至: {output_path}")
            
            # 验证输出文件
            if os.path.exists(output_path):
                print(f"输出文件大小: {os.path.getsize(output_path)} 字节")
            else:
                print(f"警告: 输出文件似乎没有被创建")
                
        except Exception as e:
            print(f"处理文件时出错: {str(e)}")
            import traceback
            print("详细错误信息:")
            traceback.print_exc()
            sys.exit(1)
            
    except Exception as e:
        print(f"程序运行出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()