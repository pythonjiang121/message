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
        try:
            # 添加审核结果列
            df = df.copy()  # 创建副本避免修改原始数据
            
            # 安全地获取结果
            def get_audit_result(result_dict, key):
                if key not in result_dict:
                    return '未知'
                return '通过' if result_dict[key][0] else '驳回'
            
            # 添加结果列
            df['总体审核结果'] = ['通过' if passed else '驳回' for passed, _ in results]
            df['签名审核结果'] = ['通过' if r[1].get('签名审核', (False, '未知'))[0] else r[1].get('签名审核', (False, '未知'))[1] for _, r in results]
            df['内容审核结果'] = ['通过' if r[1].get('内容审核', (False, '未知'))[0] else r[1].get('内容审核', (False, '未知'))[1] for _, r in results]
            df['业务审核结果'] = ['通过' if r[1].get('业务审核', (False, '未知'))[0] else '驳回' for _, r in results]
            
            # 使用当前工作目录
            if output_file is None:
                output_file = "审核结果.xlsx"
            
            print(f"\n正在保存审核结果...")
            print(f"当前工作目录: {os.getcwd()}")
            print(f"目标文件: {output_file}")
            
            # 尝试保存文件
            df.to_excel(output_file, index=False, engine='openpyxl')
            print(f"审核结果已成功保存为: {output_file}")
            
            # 验证文件是否成功创建
            if os.path.exists(output_file):
                print(f"文件成功创建，大小: {os.path.getsize(output_file)} 字节")
            else:
                print("警告：文件似乎没有被创建")
            
            return output_file
            
        except Exception as e:
            print(f"保存文件时出错: {str(e)}")
            print(f"错误类型: {type(e)}")
            print(f"错误详细信息: {e.__dict__}")
            
            # 尝试使用时间戳作为文件名重试
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                retry_file = f"审核结果_{timestamp}.xlsx"
                print(f"尝试使用新文件名保存: {retry_file}")
                df.to_excel(retry_file, index=False, engine='openpyxl')
                print(f"已成功保存为: {retry_file}")
                return retry_file
            except Exception as e2:
                print(f"重试保存也失败: {str(e2)}")
                raise e  # 抛出原始错误

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
    
    # 1. 读取数据
    try:
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
    
    # 统计各类型审核失败的数量
    signature_failed = sum(1 for _, r in results if not r[1]['签名审核'][0])
    content_failed = sum(1 for _, r in results if not r[1]['内容审核'][0])
    business_failed = sum(1 for _, r in results if not r[1]['业务审核'][0])
    
    print("\n失败原因统计:")
    print(f"签名审核不通过: {signature_failed} 条")
    print(f"内容审核不通过: {content_failed} 条")
    print(f"业务审核不通过: {business_failed} 条")
    
    # 对比原始审核结果
    original_passed = sum(1 for result in df['审核结果'] if result == '通过')
    original_failed = total - original_passed
    
    print("\n原始审核结果对比:")
    print(f"原始通过: {original_passed} 条 ({original_passed/total*100:.2f}%)")
    print(f"原始拒绝: {original_failed} 条 ({original_failed/total*100:.2f}%)")
    print(f"\n差异分析:")
    
    # 详细分析差异
    differences = 0
    false_positives = 0  # 我们通过但原始拒绝的数量
    false_negatives = 0  # 我们拒绝但原始通过的数量
    
    print("\n前5条差异案例:")
    diff_count = 0
    for i, ((passed, result_dict), original) in enumerate(zip(results, df['审核结果'])):
        our_result = "通过" if passed else "驳回"
        if our_result != original:
            differences += 1
            if our_result == "通过" and original == "驳回":
                false_positives += 1
            elif our_result == "驳回" and original == "通过":
                false_negatives += 1
            
            if diff_count < 5:
                print(f"\n差异案例 {diff_count + 1}:")
                print(f"短信签名: {df.iloc[i]['短信签名']}")
                print(f"短信内容: {df.iloc[i]['短信内容']}")
                print(f"业务类型: {df.iloc[i]['客户业务类型']}")
                print(f"账户类型: {df.iloc[i]['账户类型']}")
                print(f"原始审核结果: {original}")
                print(f"当前审核结果: {our_result}")
                print("审核详情:")
                if not result_dict['签名审核'][0]:
                    print(f"- 签名审核: {result_dict['签名审核'][1]}")
                if not result_dict['内容审核'][0]:
                    print(f"- 内容审核: {result_dict['内容审核'][1]}")
                if not result_dict['业务审核'][0]:
                    print(f"- 业务审核: {result_dict['业务审核'][1]}")
                diff_count += 1
    
    print(f"\n总体差异统计:")
    print(f"差异总数: {differences} 条 ({differences/total*100:.2f}%)")
    print(f"误通过数(False Positives): {false_positives} 条 ({false_positives/total*100:.2f}%)")
    print(f"误拒绝数(False Negatives): {false_negatives} 条 ({false_negatives/total*100:.2f}%)")
    
    # 5. 导出结果
    return checker.export_results(df, results, output_file)

def main():
    """主函数"""
    try:
        # 处理命令行参数
        import sys
        # 默认输入文件名
        default_input = "短信内容审核记录.xlsx"  # 在这里修改默认输入文件名
        input_file = sys.argv[1] if len(sys.argv) > 1 else default_input
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        
        # 处理文件
        output_path = process_excel_file(input_file, output_file)
        print(f"\n处理完成！结果已保存至: {output_path}")
        
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()