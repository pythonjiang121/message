import time
import json
import pandas as pd
from datetime import datetime
from ai_check import AIAuditor

def test_single_sms():
    """测试单条短信AI审核"""
    # 测试一条短信
    test_sms = {
        "signature": "广东商城",
        "content": "【广东商城】(温馨提示)尊敬的用户，您的电话号码卡已经办理成功，请插卡到手机使用，流量等优惠于48小时内到账，可关注微信公众号\"gdkf10000\"查询，感谢您的支持！",
        "business_type": "行业-通知"
    }
    
    print("=============== 短信信息 =============")
    print(f"签名: {test_sms['signature']}")
    print(f"内容: {test_sms['content']}")
    print(f"业务类型: {test_sms['business_type']}")
    print("\n")
   
    # 创建审核器
    auditor = AIAuditor()
    
    # 使用常规方法审核
    print("=============== AI审核 =============")
    start_time = time.time()
    passed, details = auditor.audit_sms(
        test_sms["signature"],
        test_sms["content"],
        test_sms["business_type"]
    )
    elapsed = time.time() - start_time
    
    print(f"AI审核结果: {'通过' if passed else '失败'}")
    print(f"AI审核详情: {json.dumps(details, ensure_ascii=False, indent=2)}")
    print(f"AI审核耗时: {elapsed:.2f}秒")
    
    print("\n=============== Token消耗 =============")
    standard_tokens = details.get("token_usage", {}).get("total_tokens", 0)
    
    print(f"Token消耗: {standard_tokens}")
    
    print("\n=============== 最终审核结果 =============")
    print(f"审核结果: {'通过' if passed else '失败'}")
    if not passed:
        print(f"失败原因: {', '.join(details.get('reasons', []))}")


def test_csv_batch():
    """测试批量CSV文件处理"""
    # 读取Excel文件
    try:
        df = pd.read_excel("AI审核结果_20250428_122359.xlsx", sheet_name="Sheet2")
    except Exception as e:
        print(f"读取Excel文件失败: {str(e)}")
        return
    
    # # 如果指定了样本大小，随机抽样
    # if sample_size and sample_size < len(df):
    #     df = df.sample(n=sample_size, random_state=42)
        
    print(f"读取Excel文件成功，处理{len(df)}条记录")
    
    # 准备AI审核数据
    ai_audit_list = []
    for _, row in df.iterrows():
        ai_audit_list.append({
            "signature": row['短信签名'],
            "content": row['短信内容'],
            "business_type": row['产品类型'],
        })
    
    # 进行批量审核
    method_desc = "常规方法"
    print(f"=============== 开始AI批量审核 ({method_desc}) =============")
    
    auditor = AIAuditor()
    start_time = time.time()
    
    results = auditor.batch_audit(ai_audit_list)
        
    elapsed = time.time() - start_time
    
    # 基础统计结果
    pass_count = sum(1 for result in results if result['passed'])
    reject_count = len(results) - pass_count
    reject_rate = (reject_count / len(results)) * 100 if len(results) > 0 else 0
    
    print(f"审核完成: 放行 {pass_count} 条, 失败 {reject_count} 条")
    print(f"失败率: {reject_rate:.2f}%")
    print(f"总耗时: {elapsed:.2f}秒, 平均每条: {elapsed/len(results):.2f}秒")
    print(f"Token消耗: 输入={auditor.total_input_tokens}, 输出={auditor.total_output_tokens}, 总计={auditor.total_tokens_used}")
    print(f"平均每条Token消耗: {auditor.total_tokens_used / len(results):.2f}")
    
    # 与操作类型比较的统计
    if '操作类型' in df.columns:
        # 创建结果对比
        df['AI审核结果'] = ['放行' if results[i]['passed'] else '失败' for i in range(len(results))]
        
        # 计算匹配率相关统计
        ai_pass_op_pass = sum(1 for i, result in enumerate(results) 
                           if result['passed'] and df.iloc[i]['操作类型'] == '放行')
        ai_reject_op_pass = sum(1 for i, result in enumerate(results) 
                             if not result['passed'] and df.iloc[i]['操作类型'] == '放行')
        ai_pass_op_reject = sum(1 for i, result in enumerate(results) 
                             if result['passed'] and df.iloc[i]['操作类型'] == '失败')
        ai_reject_op_reject = sum(1 for i, result in enumerate(results) 
                               if not result['passed'] and df.iloc[i]['操作类型'] == '失败')
        
        total_op_pass = sum(1 for i in range(len(results)) if df.iloc[i]['操作类型'] == '放行')
        total_op_reject = sum(1 for i in range(len(results)) if df.iloc[i]['操作类型'] == '失败')
        
        match_count = ai_pass_op_pass + ai_reject_op_reject
        match_rate = (match_count / len(results)) * 100 if len(results) > 0 else 0
        
        print("\n=============== AI与人工操作对比 =============")
        print(f"总记录数: {len(results)}")
        print(f"AI放行 & 人工放行: {ai_pass_op_pass} 条")
        print(f"AI失败 & 人工放行: {ai_reject_op_pass} 条")
        print(f"AI放行 & 人工失败: {ai_pass_op_reject} 条")
        print(f"AI失败 & 人工失败: {ai_reject_op_reject} 条")
        print(f"匹配率: {match_rate:.2f}%")
        
        # 细分统计
        if total_op_pass > 0:
            correct_pass_rate = (ai_pass_op_pass / total_op_pass) * 100
            print(f"人工放行中AI正确判断率: {correct_pass_rate:.2f}%")
        
        if total_op_reject > 0:
            correct_reject_rate = (ai_reject_op_reject / total_op_reject) * 100
            print(f"人工失败中AI正确判断率: {correct_reject_rate:.2f}%")

        if total_op_reject > 0:
            ai_wrong_rate = (ai_pass_op_reject / len(results)) * 100
            print(f"AI漏杀率: {ai_wrong_rate:.2f}%")
    
    # 添加结果列到DataFrame
    df['AI审核结果'] = ['放行' if results[i]['passed'] else '失败' for i in range(len(results))]
    
    # 添加失败原因
    reasons = []
    for result in results:
        if not result['passed'] and 'reasons' in result['details']:
            reasons.append(', '.join(result['details']['reasons']))
        else:
            reasons.append('')
    df['失败原因'] = reasons
    
    # 添加token使用情况
    tokens = []
    for result in results:
        if 'token_usage' in result['details']:
            tokens.append(result['details']['token_usage'].get('total_tokens', 0))
        else:
            tokens.append(0)
    df['Token消耗'] = tokens
    
    # 添加匹配情况
    if '操作类型' in df.columns:
        df['AI与人工是否匹配'] = [1 if ((result['passed'] and row['操作类型'] == '放行') or 
                           (not result['passed'] and row['操作类型'] == '失败')) else 0
                           for result, (_, row) in zip(results, df.iterrows())]
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"AI审核结果_{timestamp}.xlsx"
    df.to_excel(output_file, index=False)
    print(f"\n审核结果已保存至: {output_file}")

if __name__ == "__main__":
    # sample_size = int(input("请输入测试样本大小 "))
    test_csv_batch()

