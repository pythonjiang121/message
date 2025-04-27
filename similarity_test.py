#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
短信相似度测试脚本
用于评估不同短信之间的相似度，使用多种算法进行对比
"""

import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from difflib import SequenceMatcher
import pandas as pd
from tabulate import tabulate
import time

# 示例短信列表
sms_examples = [
    # 组1: 非常相似的短信（日期/数字/联系方式变化）
    "您的订单#12345已发货，预计明天送达，如有问题请联系客服400-123-4567",
    "您的订单#12345已发货，预计后天送达，如有问题请联系客服400-123-4567",
    "您的订单#54321已发货，预计明天送达，如有问题请联系客服400-123-4567",
    
    # 组2: 中等相似度 - 结构相似但参数和部分内容不同的营销短信
    "五一特惠：全场商品8折，满300减50，活动时间5月1日-5月5日，机不可失！",
    "618特惠：全场商品7折，满500减100，活动时间6月1日-6月18日，抢购从速！",
    "双11狂欢：全场商品5折，满1000减300，活动时间11月1日-11月11日，限时抢购！",
    
    # 组3: 中等相似度 - 同一类型但不同用户的通知短信
    "尊敬的王先生，您的手机话费余额不足，请及时充值以免影响正常使用。",
    "尊敬的李女士，您的手机话费余额不足，请及时充值以免影响正常使用。",
    "尊敬的张先生，您的宽带费用已扣除，本月账单已生成，可登录APP查看详情。",
    
    # 组4: 完全不同的短信
    "您的验证码是1234，5分钟内有效，请勿泄露给他人。",
    "感谢您的反馈，我们将尽快处理您的问题并回复您。",
    "系统检测到您的账号在异地登录，如非本人操作，请立即修改密码。",
    
    # 新增 组5: 一般相似度 - 同类型服务但细节不同的通知短信
    "您好，您的火车票订单2345678已出票，张三 北京南-上海 G101次 05月20日14:30开，请提前取票。",
    "您好，您的火车票订单3456789已出票，李四 上海-广州 G202次 06月15日10:00开，请提前取票。",
    "温馨提示：您购买的北京-上海Z2345次列车06月01日的车票可以取票了，请携带证件前往车站。",
    
    # 新增 组6: 一般相似度 - 同产品不同促销活动短信
    "【京东】感谢您购买iPhone 13，请对商品进行评价，好评送20京豆，点击http://jd.com/r123完成。",
    "【京东】您购买的iPhone 13已签收，满意请确认收货，有问题可联系客服400-123-4567。",
    "【苏宁】您的iPhone 13已发货，顺丰快递12345678，预计明天送达，物流查询http://sn.com/wl123。",
    
    # 新增 组7: 一般相似度 - 相似主题但不同表达方式
    "您的信用卡本期账单已出，应还金额2345.67元，最后还款日为5月25日，逾期将收取滞纳金。",
    "尊敬的用户，您的信用卡5月账单已生成，金额3456.78元，请在6月15日前还款，避免产生额外费用。",
    "【招商银行】李先生，您有一笔3000元信用卡待还款，已逾期3天，请尽快还款以免影响信用记录。"
]

class SimilarityCalculator:
    def __init__(self):
        print("加载模型中...")
        start_time = time.time()
        
        # 加载向量模型
        try:
            self.embedder = SentenceTransformer('BAAI/bge-small-zh-v1.5')
            print(f"成功加载BAAI/bge-small-zh-v1.5模型，耗时: {time.time() - start_time:.2f}秒")
        except Exception as e:
            print(f"加载BAAI模型失败，尝试加载备用模型: {str(e)}")
            try:
                self.embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                print(f"成功加载备用模型，耗时: {time.time() - start_time:.2f}秒")
            except Exception as e:
                print(f"加载备用模型失败: {str(e)}")
                self.embedder = None
    
    def calculate_text_similarity(self, text1, text2):
        """使用difflib计算文本相似度"""
        return SequenceMatcher(None, text1, text2).ratio()
    
    def calculate_vector_similarity(self, text1, text2, normalize=True):
        """计算向量相似度，可选是否归一化"""
        if self.embedder is None:
            return None
            
        # 获取向量
        vec1 = self.embedder.encode([text1])[0]
        vec2 = self.embedder.encode([text2])[0]
        
        # 可选归一化
        if normalize:
            vec1 = vec1 / np.linalg.norm(vec1)
            vec2 = vec2 / np.linalg.norm(vec2)
        
        # 计算余弦相似度
        cosine_sim = np.dot(vec1, vec2)
        
        # 计算欧几里得距离
        l2_distance = np.linalg.norm(vec1 - vec2)
        
        return {
            "cosine_similarity": cosine_sim,
            "l2_distance": l2_distance,
            "similarity_from_distance": 1 / (1 + l2_distance)  # 将距离转换为相似度指标
        }
    
    def generate_similarity_matrix(self, texts, normalize=True):
        """生成相似度矩阵"""
        n = len(texts)
        text_sim_matrix = np.zeros((n, n))
        vector_sim_matrix = np.zeros((n, n))
        distance_matrix = np.zeros((n, n))
        
        # 计算所有文本对之间的相似度
        for i in range(n):
            for j in range(i, n):
                # 文本相似度
                text_sim = self.calculate_text_similarity(texts[i], texts[j])
                text_sim_matrix[i, j] = text_sim
                text_sim_matrix[j, i] = text_sim
                
                # 向量相似度
                if self.embedder is not None:
                    vector_result = self.calculate_vector_similarity(texts[i], texts[j], normalize)
                    vector_sim_matrix[i, j] = vector_result["cosine_similarity"]
                    vector_sim_matrix[j, i] = vector_result["cosine_similarity"]
                    
                    distance_matrix[i, j] = vector_result["l2_distance"]
                    distance_matrix[j, i] = vector_result["l2_distance"]
        
        return {
            "text_similarity": text_sim_matrix,
            "vector_similarity": vector_sim_matrix,
            "l2_distance": distance_matrix
        }

def show_similarity_results(texts, matrices, threshold=0.85):
    """展示相似度结果，并根据阈值判断是否匹配"""
    results = []
    
    for i in range(len(texts)):
        for j in range(i+1, len(texts)):  # 只比较不同的文本对
            text_sim = matrices["text_similarity"][i, j]
            vector_sim = matrices["vector_similarity"][i, j]
            l2_dist = matrices["l2_distance"][i, j]
            
            # 判断是否匹配(使用多种标准)
            match_by_text = "✓" if text_sim >= threshold else "✗"
            match_by_vector = "✓" if vector_sim >= threshold else "✗"
            match_by_l2 = "✓" if l2_dist <= threshold else "✗"  # 注意这里是小于等于
            
            results.append([
                f"SMS {i+1}", 
                f"SMS {j+1}", 
                f"{text_sim:.4f}",
                f"{vector_sim:.4f}",
                f"{l2_dist:.4f}",
                match_by_text,
                match_by_vector,
                match_by_l2
            ])
    
    # 创建表格
    headers = [
        "短信1", "短信2", "文本相似度", "向量相似度(余弦)", 
        "L2距离", "文本匹配", "向量匹配", "L2匹配"
    ]
    
    print("\n短信相似度分析结果:")
    print(tabulate(results, headers=headers, tablefmt="grid"))
    
    # 显示短信内容对照表
    sms_table = [[f"SMS {i+1}", texts[i][:80] + "..." if len(texts[i]) > 80 else texts[i]] 
                 for i in range(len(texts))]
    print("\n短信内容对照表:")
    print(tabulate(sms_table, headers=["编号", "内容"], tablefmt="grid"))
    
    return results

def main():
    calculator = SimilarityCalculator()
    
    # 准备测试数据
    test_sms = sms_examples
    
    print(f"\n分析 {len(test_sms)} 条短信的相似度...")
    
    # 测试不同阈值
    thresholds = [0.85, 0.7, 0.5, 0.4, 0.3]
    
    # 计算相似度矩阵
    print("计算相似度矩阵...")
    start_time = time.time()
    matrices_with_norm = calculator.generate_similarity_matrix(test_sms, normalize=True)
    print(f"计算完成，耗时: {time.time() - start_time:.2f}秒")
    
    # 测试不同阈值对匹配结果的影响
    for threshold in thresholds:
        print(f"\n\n使用阈值 {threshold}:")
        show_similarity_results(test_sms, matrices_with_norm, threshold)
    
    # 对比归一化和非归一化的区别
    print("\n\n计算非归一化的相似度矩阵...")
    start_time = time.time()
    matrices_without_norm = calculator.generate_similarity_matrix(test_sms, normalize=False)
    print(f"计算完成，耗时: {time.time() - start_time:.2f}秒")
    
    print("\n归一化与非归一化对比 (使用阈值 0.85):")
    print("归一化结果:")
    with_norm_results = show_similarity_results(test_sms, matrices_with_norm, 0.85)
    
    print("\n非归一化结果:")
    without_norm_results = show_similarity_results(test_sms, matrices_without_norm, 0.85)
    
    # 总结分析
    print("\n\n结论分析:")
    print("1. 文本相似度(difflib)与向量相似度(embeddings)的差异")
    print("2. 归一化对相似度计算的影响")
    print("3. 不同阈值对匹配结果的影响")
    print("4. L2距离与余弦相似度的对比")

if __name__ == "__main__":
    main() 