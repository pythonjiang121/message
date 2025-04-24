import time
import json
import pandas as pd
import csv
import os
from datetime import datetime
import random
from ai_check import AIAuditor

def test_single_sms():
    """测试单条短信AI审核，比较常规方法和规则过滤方法"""
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
    print("=============== 常规AI审核 =============")
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
    
    # 使用规则过滤方法审核
    print("\n=============== 规则过滤方法AI审核 =============")
    start_time = time.time()
    passed_filtered, details_filtered = auditor.audit_sms_with_rules_filtering(
        test_sms["signature"],
        test_sms["content"],
        test_sms["business_type"]
    )
    elapsed_filtered = time.time() - start_time
    
    print(f"AI审核结果: {'通过' if passed_filtered else '失败'}")
    print(f"AI审核详情: {json.dumps(details_filtered, ensure_ascii=False, indent=2)}")
    print(f"AI审核耗时: {elapsed_filtered:.2f}秒")
    
    # 比较两种方法的token使用情况
    print("\n=============== Token消耗对比 =============")
    standard_tokens = details.get("token_usage", {}).get("total_tokens", 0)
    filtered_tokens = details_filtered.get("token_usage", {}).get("total_tokens", 0)
    
    print(f"常规方法Token消耗: {standard_tokens}")
    print(f"规则过滤方法Token消耗: {filtered_tokens}")
    
    token_diff = standard_tokens - filtered_tokens
    token_percent = (token_diff / standard_tokens * 100) if standard_tokens > 0 else 0
    print(f"Token差异: {token_diff} ({token_percent:.2f}%)")
    
    print("\n=============== 最终审核结果 =============")
    print(f"审核结果: {'一致' if passed == passed_filtered else '不一致'}")
    if not passed:
        print(f"失败原因: {', '.join(details.get('reasons', []))}")

def test_sms_with_cache():
    """测试缓存机制对相似短信的效果"""
    print("=============== 缓存机制测试 =============")
    
    # 创建一组相似的测试短信
    test_sms_list = [
        {
            "signature": "广东商城",
            "content": "尊敬的用户，您的电话卡已经办理成功，流量等优惠将于48小时内到账，感谢支持！",
            "business_type": "行业-通知"
        },
        {
            "signature": "广东商城",
            "content": "尊敬的用户，您的电话卡已经办理成功，流量等优惠将于48小时内到账。感谢您的支持！",
            "business_type": "行业-通知"
        },
        {
            "signature": "广东商城",
            "content": "尊敬的王先生，您的电话卡已经办理成功，流量等优惠将于48小时内到账，感谢支持！",
            "business_type": "行业-通知"
        },
        {
            "signature": "广东电信",
            "content": "尊敬的用户，您的电话卡已经办理成功，流量等优惠将于48小时内到账，感谢支持！",
            "business_type": "行业-通知"
        }
    ]
    
    # 创建审核器
    auditor = AIAuditor()
    if not auditor.vector_enabled:
        print("向量化功能未启用，无法进行缓存测试。请安装sentence-transformers和faiss-cpu")
        return
        
    print("开始测试缓存机制，连续处理类似短信...\n")
    
    # 依次处理短信并记录时间和token
    results = []
    for i, sms in enumerate(test_sms_list):
        print(f"处理第 {i+1} 条短信:")
        print(f"签名: {sms['signature']}")
        print(f"内容: {sms['content']}")
        print(f"业务类型: {sms['business_type']}")
        
        start_time = time.time()
        passed, details = auditor.audit_sms_with_cache(
            sms["signature"],
            sms["content"],
            sms["business_type"]
        )
        elapsed = time.time() - start_time
        
        # 判断是否是缓存命中
        is_cached = False
        similarity = 0
        if isinstance(details, dict) and "cached" in details:
            is_cached = details["cached"]
            similarity = details.get("similarity_score", 0)
            
        # 收集结果
        results.append({
            "index": i+1,
            "passed": passed,
            "elapsed": elapsed,
            "is_cached": is_cached,
            "similarity": similarity,
            "tokens": details.get("token_usage", {}).get("total_tokens", 0) if not is_cached else 0
        })
        
        # 输出结果
        print(f"审核结果: {'通过' if passed else '失败'}")
        print(f"处理时间: {elapsed:.4f}秒")
        if is_cached:
            print(f"缓存命中: 是 (相似度: {similarity:.4f})")
            print(f"Token消耗: 0 (使用缓存结果)")
        else:
            print(f"缓存命中: 否")
            print(f"Token消耗: {results[-1]['tokens']}")
        print("")
    
    # 打印总结
    print("=============== 缓存效果总结 =============")
    cache_hits = sum(1 for r in results if r["is_cached"])
    total_time = sum(r["elapsed"] for r in results)
    total_tokens = sum(r["tokens"] for r in results)
    
    print(f"总短信数: {len(results)}")
    print(f"缓存命中数: {cache_hits}")
    print(f"缓存命中率: {cache_hits/len(results)*100:.2f}%")
    print(f"总处理时间: {total_time:.4f}秒")
    print(f"总Token消耗: {total_tokens}")
    print(f"平均每条Token消耗: {total_tokens/len(results):.2f}")
    
    # 展示详细的相似度矩阵
    print("\n短信之间的相似关系:")
    for i, r1 in enumerate(results):
        if i > 0 and r1["is_cached"]:
            # 找到它命中的是哪条短信
            for j, r2 in enumerate(results[:i]):
                if j != i:  # 不和自己比
                    print(f"短信 {i+1} 与短信 {j+1} 相似度: {r1['similarity']:.4f}" + 
                          (" (缓存命中)" if r1["is_cached"] else ""))
                    break

def test_clustering_audit():
    """测试聚类批量审核功能"""
    print("=============== 聚类批量审核测试 =============")
    
    # 创建审核器
    auditor = AIAuditor()
    if not auditor.vector_enabled:
        print("向量化功能未启用，无法进行聚类测试。请安装sentence-transformers和faiss-cpu")
        return
    
    # 读取Excel文件
    try:
        df = pd.read_excel("3月审核记录.xlsx")
    except Exception as e:
        print(f"读取Excel文件失败: {str(e)}")
        return
        
    # 使用一个小样本进行测试
    sample_size = int(input("请输入测试样本大小 (建议10-20): ") or "10")
    if sample_size > len(df):
        sample_size = len(df)
        
    df_sample = df.sample(n=sample_size, random_state=42)
    print(f"从Excel文件中随机抽取 {sample_size} 条短信进行测试")
    
    # 准备AI审核数据
    sms_list = []
    for _, row in df_sample.iterrows():
        sms_list.append({
            "signature": row['短信签名'],
            "content": row['短信内容'],
            "business_type": row['产品类型'],
        })
    
    # 设置聚类参数
    max_clusters = int(input("请输入最大聚类数量 (建议3-5): ") or "3")
    use_rules_filtering = input("是否使用规则过滤方法? (y/n): ").lower() == 'y'
    
    # 先使用常规批量审核
    print("\n=============== 常规批量审核 =============")
    start_time = time.time()
    standard_results = auditor.batch_audit(sms_list, use_rules_filtering=use_rules_filtering)
    standard_elapsed = time.time() - start_time
    
    standard_tokens = auditor.total_tokens_used
    
    # 重置token计数器
    auditor.total_tokens_used = 0
    auditor.total_input_tokens = 0
    auditor.total_output_tokens = 0
    
    # 使用聚类批量审核
    print("\n=============== 聚类批量审核 =============")
    start_time = time.time()
    clustering_results = auditor.batch_audit_with_clustering(
        sms_list, 
        max_clusters=max_clusters,
        use_rules_filtering=use_rules_filtering
    )
    clustering_elapsed = time.time() - start_time
    
    clustering_tokens = auditor.total_tokens_used
    
    # 分析结果差异
    print("\n=============== 聚类效果分析 =============")
    
    # 计算结果一致性
    matches = sum(1 for s, c in zip(standard_results, clustering_results) 
                 if s["passed"] == c["passed"])
    match_rate = matches / len(sms_list) * 100
    
    # 计算时间和token节省
    time_saved = standard_elapsed - clustering_elapsed
    time_saved_percent = (time_saved / standard_elapsed) * 100 if standard_elapsed > 0 else 0
    
    token_saved = standard_tokens - clustering_tokens
    token_saved_percent = (token_saved / standard_tokens) * 100 if standard_tokens > 0 else 0
    
    print(f"总处理短信数: {len(sms_list)}")
    print(f"结果一致性: {match_rate:.2f}% ({matches}/{len(sms_list)})")
    print(f"时间节省: {time_saved:.2f}秒 ({time_saved_percent:.2f}%)")
    print(f"Token节省: {token_saved} ({token_saved_percent:.2f}%)")
    
    # 聚类统计
    is_representative = [r.get("is_representative", False) for r in clustering_results]
    total_api_calls = sum(1 for r in is_representative if r)
    saved_calls = len(sms_list) - total_api_calls
    
    print(f"实际API调用数: {total_api_calls}")
    print(f"节省API调用: {saved_calls} ({saved_calls/len(sms_list)*100:.2f}%)")
    
    # 显示每个聚类的详情
    cluster_details = {}
    for r in clustering_results:
        if "details" in r and isinstance(r["details"], dict) and "cluster_id" in r["details"]:
            cluster_id = r["details"]["cluster_id"]
            if cluster_id in cluster_details:
                cluster_details[cluster_id] += 1
            else:
                cluster_details[cluster_id] = 1
    
    if cluster_details:
        print("\n聚类详情:")
        for cluster_id, count in cluster_details.items():
            print(f"聚类 {cluster_id}: {count} 条短信")

def test_csv_batch(use_rules_filtering=False, use_parallel=False, max_workers=5, sample_size=None, use_clustering=False, max_clusters=5):
    """测试批量CSV文件处理，支持选择使用规则过滤方法、并行处理和聚类处理"""
    # 读取Excel文件
    df = pd.read_excel("3月审核记录.xlsx")
    
    # 如果指定了样本大小，随机抽样
    if sample_size and sample_size < len(df):
        df = df.sample(n=sample_size, random_state=42)
        
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
    method_desc = "规则过滤方法" if use_rules_filtering else "常规方法"
    process_desc = "并行处理" if use_parallel else "串行处理"
    cluster_desc = "使用聚类" if use_clustering else "不使用聚类"
    print(f"=============== 开始AI批量审核 ({method_desc}, {process_desc}, {cluster_desc}) =============")
    
    auditor = AIAuditor()
    start_time = time.time()
    
    if use_parallel:
        results = auditor.parallel_batch_audit(
            ai_audit_list, 
            max_workers=max_workers, 
            use_rules_filtering=use_rules_filtering,
            use_clustering=use_clustering,
            max_clusters=max_clusters
        )
    else:
        if use_clustering and auditor.vector_enabled:
            results = auditor.batch_audit_with_clustering(
                ai_audit_list,
                max_clusters=max_clusters,
                use_rules_filtering=use_rules_filtering
            )
        else:
            results = auditor.batch_audit(ai_audit_list, use_rules_filtering=use_rules_filtering)
        
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
    
    # 如果使用了聚类，显示聚类统计
    if use_clustering and auditor.vector_enabled:
        rep_count = sum(1 for r in results if r.get("is_representative", False))
        print(f"API调用次数: {rep_count} (节省率: {(1-rep_count/len(results))*100:.2f}%)")
    
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
    method_suffix = "规则过滤" if use_rules_filtering else "标准"
    parallel_suffix = "并行" if use_parallel else "串行"
    cluster_suffix = "聚类" if use_clustering else "常规"
    output_file = f"AI审核结果_{method_suffix}_{parallel_suffix}_{cluster_suffix}_{timestamp}.xlsx"
    df.to_excel(output_file, index=False)
    print(f"\n审核结果已保存至: {output_file}")

def compare_methods():
    """比较不同方法的性能和准确性"""
    print("======= 比较不同审核方法 =======")
    
    # 设置样本大小
    sample_size = 20
    
    print(f"使用{sample_size}条短信进行比较测试...")
    
    # 测试四种组合
    methods = [
        {"name": "常规方法 (串行)", "rules_filtering": False, "parallel": False, "clustering": False},
        {"name": "常规方法 (并行)", "rules_filtering": False, "parallel": True, "clustering": False},
        {"name": "规则过滤方法 (串行)", "rules_filtering": True, "parallel": False, "clustering": False},
        {"name": "规则过滤方法 (并行)", "rules_filtering": True, "parallel": True, "clustering": False}
    ]
    
    # 如果向量功能可用，加入聚类方法测试
    auditor = AIAuditor()
    if auditor.vector_enabled:
        methods.extend([
            {"name": "常规方法 (聚类)", "rules_filtering": False, "parallel": True, "clustering": True},
            {"name": "规则过滤方法 (聚类)", "rules_filtering": True, "parallel": True, "clustering": True}
        ])
    
    results = []
    
    for method in methods:
        print(f"\n===== 测试: {method['name']} =====")
        start_time = time.time()
        
        # 调用测试函数
        test_csv_batch(
            use_rules_filtering=method["rules_filtering"], 
            use_parallel=method["parallel"], 
            max_workers=5,
            sample_size=sample_size,
            use_clustering=method["clustering"],
            max_clusters=3
        )
        
        elapsed = time.time() - start_time
        results.append({
            "method": method["name"],
            "time": elapsed
        })
    
    # 显示比较结果
    print("\n======= 性能比较结果 =======")
    for result in results:
        print(f"{result['method']}: {result['time']:.2f}秒")

if __name__ == "__main__":
    print("======= 短信AI审核测试工具 =======")
    
    print("请选择测试模式:")
    print("1. 测试单条短信 (对比常规方法和规则过滤方法)")
    print("2. 测试缓存机制 (相似短信处理)")
    print("3. 测试聚类审核")
    print("4. 批量测试 (常规方法)")
    print("5. 批量测试 (规则过滤方法)")
    print("6. 批量测试 (规则过滤 + 并行)")
    print("7. 批量测试 (规则过滤 + 聚类)")
    print("8. 比较所有方法")
    
    choice = input("请输入选项 (1-8): ")
    
    if choice == "1":
        test_single_sms()
    elif choice == "2":
        test_sms_with_cache()
    elif choice == "3":
        test_clustering_audit()
    elif choice == "4":
        test_csv_batch(use_rules_filtering=False, use_parallel=False)
    elif choice == "5":
        test_csv_batch(use_rules_filtering=True, use_parallel=False)
    elif choice == "6":
        max_workers = int(input("请输入最大并行数 (建议5-10): ") or "5")
        test_csv_batch(use_rules_filtering=True, use_parallel=True, max_workers=max_workers)
    elif choice == "7":
        max_clusters = int(input("请输入最大聚类数 (建议3-5): ") or "3")
        test_csv_batch(use_rules_filtering=True, use_parallel=True, use_clustering=True, max_clusters=max_clusters)
    elif choice == "8":
        compare_methods()
    else:
        print("无效选项，请输入1-8")