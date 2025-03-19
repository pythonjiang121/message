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
    df = pd.read_excel("审核结果_20250319_155514.xlsx")
    
    # 计算匹配率
    total_count = len(df)
    matched_count = len(df[df['审核结果'] == df['总体审核结果']])
    match_rate = (matched_count / total_count) * 100
    
    print(f"\n总数据量: {total_count}")
    print(f"匹配数据量: {matched_count}")
    print(f"匹配率: {match_rate:.2f}%")
    
    # 分析匹配成功的数据
    matched_data = df[df['审核结果'] == df['总体审核结果']]
    print("\n匹配成功数据分析:")
    
    # 分析业务类型分布
    matched_business_types = matched_data['客户业务类型'].value_counts()
    print("\n匹配成功数据的业务类型分布:")
    for business_type, count in matched_business_types.items():
        print(f"{business_type}: {count}条")
    
    # 分析匹配成功数据的扣分原因
    matched_reasons = []
    for reason in matched_data['业务审核结果']:
        if isinstance(reason, str):
            matched_reasons.extend(analyze_rejection_reasons(reason))
    
    matched_reason_counts = Counter(matched_reasons)
    print("\n匹配成功数据的扣分原因统计:")
    for reason, count in matched_reason_counts.most_common():
        print(f"{reason}: {count}次")
    
    # 分析匹配成功数据的关键词
    matched_words = []
    for content in matched_data['短信内容']:
        if isinstance(content, str):
            words = re.findall(r'[\u4e00-\u9fa5]{2,}', content)
            matched_words.extend(words)
    
    matched_word_counts = Counter(matched_words)
    print("\n匹配成功数据的高频词统计 (出现20次以上):")
    for word, count in matched_word_counts.most_common():
        if count >= 20 and len(word) >= 2:
            print(f"{word}: {count}次")
    
    # 分析匹配成功数据的签名
    matched_signatures = []
    for signature in matched_data['短信签名']:
        if isinstance(signature, str):
            matched_signatures.append(signature)
    
    matched_signature_counts = Counter(matched_signatures)
    print("\n匹配成功数据的签名统计 (出现5次以上):")
    for signature, count in matched_signature_counts.most_common():
        if count >= 5:
            print(f"{signature}: {count}次")
    
    # 保存匹配成功数据的分析结果
    matched_data.to_excel("匹配成功数据分析.xlsx", index=False)
    print("\n匹配成功数据已保存到 '匹配成功数据分析.xlsx'")
    
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
    
    print(f"\n人工驳回但代码通过的数据分析 (264条):")
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
    
    print(f"\n人工通过但代码驳回的数据分析 (263条):")
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