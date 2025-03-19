import pandas as pd
import re
from collections import Counter

def analyze_rejection_reasons(text):
    # 从文本中提取扣分原因
    pattern = r'\((.*?分)\)'
    matches = re.findall(pattern, text)
    return [match.strip() for match in matches]

def analyze_discrepancy():
    # 读取Excel文件
    df = pd.read_excel("审核结果_20250319_180503.xlsx")
    
    # 计算匹配率
    total_count = len(df)
    matched_count = len(df[df['审核结果'] == df['总体审核结果']])
    match_rate = (matched_count / total_count) * 100
    
    print(f"\n总数据量: {total_count}")
    print(f"匹配数据量: {matched_count}")
    print(f"匹配率: {match_rate:.2f}%")
    
    # 筛选出审核结果和总体审核结果不一致的数据
    df_discrepancy = df[df['审核结果'] != df['总体审核结果']]
    
    # 分别分析人工驳回但代码通过，以及人工通过但代码驳回的数据
    human_reject_code_pass = df_discrepancy[
        (df_discrepancy['审核结果'] == '驳回') & 
        (df_discrepancy['总体审核结果'] == '通过')
    ]
    
    human_pass_code_reject = df_discrepancy[
        (df_discrepancy['审核结果'] == '通过') & 
        (df_discrepancy['总体审核结果'] == '驳回')
    ]
    
    print(f"\n人工驳回但代码通过的数据分析 ({len(human_reject_code_pass)}条):")
    print("\n业务类型分布:")
    business_type_counts = human_reject_code_pass['客户业务类型'].value_counts()
    for business_type, count in business_type_counts.items():
        print(f"{business_type}: {count}条")
    
    print("\n扣分原因统计:")
    reasons = []
    for reason in human_reject_code_pass['业务审核结果']:
        if isinstance(reason, str):
            reasons.extend(analyze_rejection_reasons(reason))
    reason_counts = Counter(reasons)
    for reason, count in reason_counts.most_common():
        print(f"{reason}: {count}次")
    
    print("\n高频词统计 (出现5次以上):")
    words = []
    for content in human_reject_code_pass['短信内容']:
        if isinstance(content, str):
            words.extend(re.findall(r'[\u4e00-\u9fa5]{2,}', content))
    word_counts = Counter(words)
    for word, count in word_counts.most_common():
        if count >= 5 and len(word) >= 2:
            print(f"{word}: {count}次")
    
    print(f"\n人工通过但代码驳回的数据分析 ({len(human_pass_code_reject)}条):")
    print("\n业务类型分布:")
    business_type_counts = human_pass_code_reject['客户业务类型'].value_counts()
    for business_type, count in business_type_counts.items():
        print(f"{business_type}: {count}条")
    
    print("\n扣分原因统计:")
    reasons = []
    for reason in human_pass_code_reject['业务审核结果']:
        if isinstance(reason, str):
            reasons.extend(analyze_rejection_reasons(reason))
    reason_counts = Counter(reasons)
    for reason, count in reason_counts.most_common():
        print(f"{reason}: {count}次")
    
    print("\n高频词统计 (出现5次以上):")
    words = []
    for content in human_pass_code_reject['短信内容']:
        if isinstance(content, str):
            words.extend(re.findall(r'[\u4e00-\u9fa5]{2,}', content))
    word_counts = Counter(words)
    for word, count in word_counts.most_common():
        if count >= 5 and len(word) >= 2:
            print(f"{word}: {count}次")
    
    # 保存详细分析结果
    human_reject_code_pass.to_excel("人工驳回代码通过数据.xlsx", index=False)
    human_pass_code_reject.to_excel("人工通过代码驳回数据.xlsx", index=False)
    print("\n详细分析结果已保存到相应Excel文件")

if __name__ == "__main__":
    analyze_discrepancy() 