import pandas as pd
import jieba
from collections import Counter
import re

def clean_text(text):
    # 移除标点符号和特殊字符
    text = re.sub(r'[^\w\s]', '', text)
    # 移除数字
    text = re.sub(r'\d+', '', text)
    # 移除空白字符
    text = re.sub(r'\s+', '', text)
    return text

def analyze_frequent_words(excel_file):
    # 读取Excel文件
    df = pd.read_excel(excel_file)
    
    # 合并所有短信内容
    all_content = ' '.join(df['短信内容'].astype(str))
    
    # 清理文本
    all_content = clean_text(all_content)
    
    # 使用结巴分词
    words = jieba.cut(all_content)
    
    # 过滤掉单个字符的词和停用词
    stop_words = {'拒收', '回复', '您好', '你好', '请问', '请', '的', '了', '和', '与', '及', '或', '在', '是', '我们', '可以', '已经', '这个', '那个', '这些', '那些', '如果', '什么', '为了', '因为', '所以', '但是', '可能', '一个', '没有', '不是', '就是', '这样', '那样', '只是', '还是', '也是', '到', '去', '从', '向', '于', '内', '中', '外', '上', '下', '前', '后', '里', '中'}
    words = [word for word in words if len(word) > 1 and word not in stop_words]
    
    # 统计词频
    word_counts = Counter(words)
    
    # 获取前50个最常见的词
    most_common = word_counts.most_common(50)
    
    print("\n短信内容中最常见的50个词及其出现次数：")
    print("-" * 40)
    for word, count in most_common:
        print(f"{word}: {count}")

if __name__ == "__main__":
    # 使用最新生成的Excel文件
    excel_file = "人工通过代码驳回数据_20250320_173617.xlsx"
    analyze_frequent_words(excel_file) 