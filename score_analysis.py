import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from business import BusinessValidator
from collections import defaultdict

def analyze_deduction_rules():
    """分析扣分规则触发情况"""
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
    plt.rcParams['axes.unicode_minus'] = False    # 用来正常显示负号
    
    # 读取Excel文件
    df = pd.read_excel('合并审核.xlsx')
    print(f"总共读取 {len(df)} 条消息")
    
    # 初始化计数器
    mismatch_counts = defaultdict(int)  # 扣分规则计数器
    mismatch_scores = defaultdict(float)  # 扣分规则实际扣分计数器
    system_results = []  # 存储系统审核结果
    mismatches = 0  # 不一致的审核结果数量
    
    # 计算私人号码统计
    private_number_count = 0
    private_number_mismatches = 0
    
    # 导入BusinessValidator类
    validator = BusinessValidator()
    
    # 分析每一行
    for i, row in df.iterrows():
        content = row['短信内容']
        signature = row['短信签名']
        business_type = row['客户业务类型']
        customer_type = row['客户类型']
        manual_result = row['审核结果']
        
        # 清理内容和签名
        cleaned_content = validator._clean_content(content)
        cleaned_signature = validator._clean_content(signature)
        
        # 使用validator生成系统审核结果
        is_valid, _ = validator._validate_business_internal(business_type, cleaned_content, cleaned_signature, customer_type)
        system_result = '通过' if is_valid else '驳回'
        system_results.append(system_result)
        
        # 检查是否含有私人号码
        if validator._contains_private_number(cleaned_content):
            private_number_count += 1
            if manual_result != system_result:
                private_number_mismatches += 1
        
        # 比较审核结果
        if manual_result != system_result:
            mismatches += 1
            
            # 计算触发了哪些规则和对应扣分
            # 检查私人号码
            if validator._contains_private_number(cleaned_content):
                mismatch_counts['私人号码'] += 1
                # 实际扣分
                deduction = abs(validator.SCORE_RULES['ZERO_TOLERANCE']['PRIVATE_NUMBER'])
                mismatch_scores['私人号码'] += deduction
                
            # 检查固定电话
            has_fixed_phone, fixed_phone_count = validator._contains_fixed_phone(cleaned_content)
            if has_fixed_phone:
                mismatch_counts['固定电话'] += fixed_phone_count
                # 获取业务特定扣分规则
                if business_type in validator.SCORE_RULES['DEDUCTIONS']['FIXED_PHONE']['business_specific']:
                    specific_rule = validator.SCORE_RULES['DEDUCTIONS']['FIXED_PHONE']['business_specific'][business_type]
                    deduction = min(
                        abs(specific_rule['score']) * fixed_phone_count,
                        abs(specific_rule['max_deduction'])
                    )
                else:
                    deduction = min(
                        abs(validator.SCORE_RULES['DEDUCTIONS']['FIXED_PHONE']['score']) * fixed_phone_count,
                        abs(validator.SCORE_RULES['DEDUCTIONS']['FIXED_PHONE']['max_deduction'])
                    )
                mismatch_scores['固定电话'] += deduction
                
            # 检查链接
            has_link, link_count = validator._contains_link(cleaned_content)
            if has_link:
                mismatch_counts['链接'] += link_count
                # 获取业务特定扣分规则
                if business_type in validator.SCORE_RULES['DEDUCTIONS']['LINK']['business_specific']:
                    specific_rule = validator.SCORE_RULES['DEDUCTIONS']['LINK']['business_specific'][business_type]
                    deduction = min(
                        abs(specific_rule['score']) * link_count,
                        abs(specific_rule['max_deduction'])
                    )
                else:
                    deduction = min(
                        abs(validator.SCORE_RULES['DEDUCTIONS']['LINK']['score']) * link_count,
                        abs(validator.SCORE_RULES['DEDUCTIONS']['LINK']['max_deduction'])
                    )
                mismatch_scores['链接'] += deduction
                
            # 检查地址
            has_address, address_score, _ = validator._contains_address(cleaned_content)
            if has_address:
                mismatch_counts['地址'] += address_score
                # 获取业务特定扣分规则
                if business_type in validator.SCORE_RULES['DEDUCTIONS']['ADDRESS']['business_specific']:
                    specific_rule = validator.SCORE_RULES['DEDUCTIONS']['ADDRESS']['business_specific'][business_type]
                    deduction = min(
                        abs(specific_rule['score']) * address_score,
                        abs(specific_rule['max_deduction'])
                    )
                else:
                    deduction = min(
                        abs(validator.SCORE_RULES['DEDUCTIONS']['ADDRESS']['score']) * address_score,
                        abs(validator.SCORE_RULES['DEDUCTIONS']['ADDRESS']['max_deduction'])
                    )
                mismatch_scores['地址'] += deduction
                
            # 检查营销关键词
            for keyword in validator.SCORE_RULES['DEDUCTIONS']['MARKETING']['keywords']:
                if keyword in cleaned_content:
                    mismatch_counts['营销关键词'] += 1
                    # 获取业务特定扣分规则
                    if business_type in validator.SCORE_RULES['DEDUCTIONS']['MARKETING']['business_specific']:
                        specific_rule = validator.SCORE_RULES['DEDUCTIONS']['MARKETING']['business_specific'][business_type]
                        deduction = min(
                            abs(specific_rule['score']),
                            abs(specific_rule['max_deduction'])
                        )
                    else:
                        deduction = min(
                            abs(validator.SCORE_RULES['DEDUCTIONS']['MARKETING']['score']),
                            abs(validator.SCORE_RULES['DEDUCTIONS']['MARKETING']['max_deduction'])
                        )
                    mismatch_scores['营销关键词'] += deduction
                    break
                    
            # 检查强营销关键词
            for keyword in validator.SCORE_RULES['DEDUCTIONS']['MARKETING']['strong_keywords']:
                if keyword in cleaned_content:
                    mismatch_counts['强营销关键词'] += 1
                    # 获取业务特定扣分规则
                    if business_type in validator.SCORE_RULES['DEDUCTIONS']['MARKETING']['business_specific']:
                        specific_rule = validator.SCORE_RULES['DEDUCTIONS']['MARKETING']['business_specific'][business_type]
                        deduction = min(
                            abs(specific_rule.get('strong_score', validator.SCORE_RULES['DEDUCTIONS']['MARKETING']['strong_score'])),
                            abs(specific_rule['max_deduction'])
                        )
                    else:
                        deduction = min(
                            abs(validator.SCORE_RULES['DEDUCTIONS']['MARKETING']['strong_score']),
                            abs(validator.SCORE_RULES['DEDUCTIONS']['MARKETING']['max_deduction'])
                        )
                    mismatch_scores['强营销关键词'] += deduction
                    break
                    
            # 检查积分营销关键词
            for keyword in validator.SCORE_RULES['DEDUCTIONS']['POINTS_MARKETING']['keywords']:
                if keyword in cleaned_content:
                    mismatch_counts['积分营销'] += 1
                    # 获取业务特定扣分规则
                    if business_type in validator.SCORE_RULES['DEDUCTIONS']['POINTS_MARKETING']['business_specific']:
                        specific_rule = validator.SCORE_RULES['DEDUCTIONS']['POINTS_MARKETING']['business_specific'][business_type]
                        deduction = min(
                            abs(specific_rule['score']),
                            abs(specific_rule['max_deduction'])
                        )
                    else:
                        deduction = min(
                            abs(validator.SCORE_RULES['DEDUCTIONS']['POINTS_MARKETING']['score']),
                            abs(validator.SCORE_RULES['DEDUCTIONS']['POINTS_MARKETING']['max_deduction'])
                        )
                    mismatch_scores['积分营销'] += deduction
                    break
                    
            # 检查积分到期关键词
            for keyword in validator.SCORE_RULES['DEDUCTIONS']['POINTS_EXPIRY']['keywords']:
                if keyword in cleaned_content:
                    mismatch_counts['积分到期'] += 1
                    # 获取业务特定扣分规则
                    if business_type in validator.SCORE_RULES['DEDUCTIONS']['POINTS_EXPIRY']['business_specific']:
                        specific_rule = validator.SCORE_RULES['DEDUCTIONS']['POINTS_EXPIRY']['business_specific'][business_type]
                        deduction = min(
                            abs(specific_rule['score']),
                            abs(specific_rule['max_deduction'])
                        )
                    else:
                        deduction = min(
                            abs(validator.SCORE_RULES['DEDUCTIONS']['POINTS_EXPIRY']['score']),
                            abs(validator.SCORE_RULES['DEDUCTIONS']['POINTS_EXPIRY']['max_deduction'])
                        )
                    mismatch_scores['积分到期'] += deduction
                    break
                    
            # 检查平台关键词
            for keyword in validator.SCORE_RULES['DEDUCTIONS']['PLATFORM']['keywords']:
                if keyword in cleaned_content:
                    mismatch_counts['平台关键词'] += 1
                    # 获取业务特定扣分规则
                    if business_type in validator.SCORE_RULES['DEDUCTIONS']['PLATFORM']['business_specific']:
                        specific_rule = validator.SCORE_RULES['DEDUCTIONS']['PLATFORM']['business_specific'][business_type]
                        deduction = min(
                            abs(specific_rule['score']),
                            abs(specific_rule['max_deduction'])
                        )
                    else:
                        deduction = min(
                            abs(validator.SCORE_RULES['DEDUCTIONS']['PLATFORM']['score']),
                            abs(validator.SCORE_RULES['DEDUCTIONS']['PLATFORM']['max_deduction'])
                        )
                    mismatch_scores['平台关键词'] += deduction
                    break
                    
            # 检查问卷调查关键词
            for keyword in validator.SCORE_RULES['DEDUCTIONS']['SURVEY']['keywords']:
                if keyword in cleaned_content:
                    mismatch_counts['问卷调查'] += 1
                    # 获取业务特定扣分规则
                    if business_type in validator.SCORE_RULES['DEDUCTIONS']['SURVEY']['business_specific']:
                        specific_rule = validator.SCORE_RULES['DEDUCTIONS']['SURVEY']['business_specific'][business_type]
                        deduction = min(
                            abs(specific_rule['score']),
                            abs(specific_rule['max_deduction'])
                        )
                    else:
                        deduction = min(
                            abs(validator.SCORE_RULES['DEDUCTIONS']['SURVEY']['score']),
                            abs(validator.SCORE_RULES['DEDUCTIONS']['SURVEY']['max_deduction'])
                        )
                    mismatch_scores['问卷调查'] += deduction
                    break
                    
            # 检查教育营销关键词
            for keyword in validator.SCORE_RULES['DEDUCTIONS']['EDUCATION']['keywords']:
                if keyword in cleaned_content:
                    mismatch_counts['教育营销'] += 1
                    # 获取业务特定扣分规则
                    if business_type in validator.SCORE_RULES['DEDUCTIONS']['EDUCATION']['business_specific']:
                        specific_rule = validator.SCORE_RULES['DEDUCTIONS']['EDUCATION']['business_specific'][business_type]
                        deduction = min(
                            abs(specific_rule['score']),
                            abs(specific_rule['max_deduction'])
                        )
                    else:
                        deduction = min(
                            abs(validator.SCORE_RULES['DEDUCTIONS']['EDUCATION']['score']),
                            abs(validator.SCORE_RULES['DEDUCTIONS']['EDUCATION']['max_deduction'])
                        )
                    mismatch_scores['教育营销'] += deduction
                    break
            
            # 检查就业招聘关键词
            for keyword in validator.SCORE_RULES['DEDUCTIONS']['EMPLOYMENT']['keywords']:
                if keyword in cleaned_content:
                    mismatch_counts['就业招聘'] += 1
                    # 获取业务特定扣分规则
                    if business_type in validator.SCORE_RULES['DEDUCTIONS']['EMPLOYMENT']['business_specific']:
                        specific_rule = validator.SCORE_RULES['DEDUCTIONS']['EMPLOYMENT']['business_specific'][business_type]
                        deduction = min(
                            abs(specific_rule['score']),
                            abs(specific_rule['max_deduction'])
                        )
                    else:
                        deduction = min(
                            abs(validator.SCORE_RULES['DEDUCTIONS']['EMPLOYMENT']['score']),
                            abs(validator.SCORE_RULES['DEDUCTIONS']['EMPLOYMENT']['max_deduction'])
                        )
                    mismatch_scores['就业招聘'] += deduction
                    break
                
    # 输出统计信息
    mismatch_rate = (mismatches / len(df)) * 100
    print(f"不一致的审核结果数量: {mismatches}条 ({mismatch_rate:.1f}%)")
    
    # 输出私人号码统计
    if private_number_count > 0:
        private_number_mismatch_rate = (private_number_mismatches / private_number_count) * 100
        print(f"含有私人号码的消息: {private_number_count}条，其中不一致的: {private_number_mismatches}条 ({private_number_mismatch_rate:.1f}%)")
    
    # 输出触发次数
    total_score = sum(mismatch_scores.values())
    
    if mismatches > 0:
        print("\n审核结果不一致时的规则触发扣分分布（按扣分排序）:")
        # 按扣分排序
        sorted_items = sorted(mismatch_scores.items(), key=lambda x: x[1], reverse=True)
        
        for rule, score in sorted_items[:5]:  # 显示前5项
            count = mismatch_counts[rule]
            percentage = (score / total_score) * 100 if total_score > 0 else 0
            print(f"  {rule}: {score:.1f}分 ({percentage:.1f}%), 触发{count}次")
            
        # 可视化扣分分布
        rules = []
        scores = []
        counts = []
        
        for rule, score in sorted_items:
            rules.append(rule)
            scores.append(score)
            counts.append(mismatch_counts[rule])
            
        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # 横向条形图
        bars = ax.barh(rules, scores, color='skyblue')
        
        # 在条形上标注具体数值
        for i, bar in enumerate(bars):
            width = bar.get_width()
            percentage = (scores[i] / total_score) * 100 if total_score > 0 else 0
            label = f'{width:.1f}分 ({percentage:.1f}%), {counts[i]}次'
            ax.text(width + 1, bar.get_y() + bar.get_height()/2, label, va='center')
            
        ax.set_xlabel('扣分总值')
        ax.set_title('审核结果不一致时的规则扣分分布')
        plt.tight_layout()
        plt.savefig('deduction_distribution.png')
        print("图表已保存为 deduction_distribution.png")
    else:
        print("未发现审核结果不一致的情况")
        
    # 调用特定业务类型分析
    analyze_specific_business_types(df, system_results, validator)

def analyze_specific_business_types(df, system_results, validator):
    """
    专门分析会销普通和行业通知业务类型的误判详情
    
    Args:
        df: Excel数据
        system_results: 系统生成的审核结果
        validator: BusinessValidator实例
    """
    print("\n\n===== 会销普通和行业通知业务类型误判详细分析 =====")
    
    # 初始化计数器
    business_stats = {
        '会销-普通': {
            'false_positive': defaultdict(int),  # 系统拒绝但人工通过的规则触发统计
            'false_negative': defaultdict(int),  # 系统通过但人工拒绝的规则触发统计
            'false_positive_score': defaultdict(float),  # 系统拒绝但人工通过的规则扣分统计
            'false_negative_score': defaultdict(float),  # 系统通过但人工拒绝的规则扣分统计
            'total_fp': 0,  # 系统拒绝但人工通过的总数
            'total_fn': 0,  # 系统通过但人工拒绝的总数
            'total': 0     # 总数
        },
        '行业-通知': {
            'false_positive': defaultdict(int),
            'false_negative': defaultdict(int),
            'false_positive_score': defaultdict(float),
            'false_negative_score': defaultdict(float),
            'total_fp': 0,
            'total_fn': 0,
            'total': 0
        }
    }
    
    # 筛选这两种业务类型的行
    for i, row in df.iterrows():
        business_type = row['客户业务类型']
        
        # 只分析会销普通和行业通知
        if business_type not in ['会销-普通', '行业-通知']:
            continue
            
        manual_result = row['审核结果']
        system_result = system_results[i]
        
        # 计数
        business_stats[business_type]['total'] += 1
        
        # 判断不一致类型
        if manual_result != system_result:
            if manual_result == '通过' and system_result == '驳回':
                # 系统过于严格（误判为拒绝）
                business_stats[business_type]['total_fp'] += 1
                inconsistency_type = 'false_positive'
                score_type = 'false_positive_score'
            else:
                # 系统过于宽松（误判为通过）
                business_stats[business_type]['total_fn'] += 1
                inconsistency_type = 'false_negative'
                score_type = 'false_negative_score'
                
            # 计算触发了哪些规则和对应扣分
            content = row['短信内容']
            signature = row['短信签名']
            customer_type = row['客户类型']
            
            # 清理内容和签名
            cleaned_content = validator._clean_content(content)
            cleaned_signature = validator._clean_content(signature)
            
            # 检查私人号码
            if validator._contains_private_number(cleaned_content):
                business_stats[business_type][inconsistency_type]['私人号码'] += 1
                # 实际扣分
                deduction = abs(validator.SCORE_RULES['ZERO_TOLERANCE']['PRIVATE_NUMBER'])
                business_stats[business_type][score_type]['私人号码'] += deduction
                
            # 检查固定电话
            has_fixed_phone, fixed_phone_count = validator._contains_fixed_phone(cleaned_content)
            if has_fixed_phone:
                business_stats[business_type][inconsistency_type]['固定电话'] += fixed_phone_count
                # 获取业务特定扣分规则
                if business_type in validator.SCORE_RULES['DEDUCTIONS']['FIXED_PHONE']['business_specific']:
                    specific_rule = validator.SCORE_RULES['DEDUCTIONS']['FIXED_PHONE']['business_specific'][business_type]
                    deduction = min(
                        abs(specific_rule['score']) * fixed_phone_count,
                        abs(specific_rule['max_deduction'])
                    )
                else:
                    deduction = min(
                        abs(validator.SCORE_RULES['DEDUCTIONS']['FIXED_PHONE']['score']) * fixed_phone_count,
                        abs(validator.SCORE_RULES['DEDUCTIONS']['FIXED_PHONE']['max_deduction'])
                    )
                business_stats[business_type][score_type]['固定电话'] += deduction
                
            # 检查链接
            has_link, link_count = validator._contains_link(cleaned_content)
            if has_link:
                business_stats[business_type][inconsistency_type]['链接'] += link_count
                # 获取业务特定扣分规则
                if business_type in validator.SCORE_RULES['DEDUCTIONS']['LINK']['business_specific']:
                    specific_rule = validator.SCORE_RULES['DEDUCTIONS']['LINK']['business_specific'][business_type]
                    deduction = min(
                        abs(specific_rule['score']) * link_count,
                        abs(specific_rule['max_deduction'])
                    )
                else:
                    deduction = min(
                        abs(validator.SCORE_RULES['DEDUCTIONS']['LINK']['score']) * link_count,
                        abs(validator.SCORE_RULES['DEDUCTIONS']['LINK']['max_deduction'])
                    )
                business_stats[business_type][score_type]['链接'] += deduction
                
            # 检查地址
            has_address, address_score, _ = validator._contains_address(cleaned_content)
            if has_address:
                business_stats[business_type][inconsistency_type]['地址'] += address_score
                # 获取业务特定扣分规则
                if business_type in validator.SCORE_RULES['DEDUCTIONS']['ADDRESS']['business_specific']:
                    specific_rule = validator.SCORE_RULES['DEDUCTIONS']['ADDRESS']['business_specific'][business_type]
                    deduction = min(
                        abs(specific_rule['score']) * address_score,
                        abs(specific_rule['max_deduction'])
                    )
                else:
                    deduction = min(
                        abs(validator.SCORE_RULES['DEDUCTIONS']['ADDRESS']['score']) * address_score,
                        abs(validator.SCORE_RULES['DEDUCTIONS']['ADDRESS']['max_deduction'])
                    )
                business_stats[business_type][score_type]['地址'] += deduction
                
            # 检查营销关键词
            for keyword in validator.SCORE_RULES['DEDUCTIONS']['MARKETING']['keywords']:
                if keyword in cleaned_content:
                    business_stats[business_type][inconsistency_type]['营销关键词'] += 1
                    # 获取业务特定扣分规则
                    if business_type in validator.SCORE_RULES['DEDUCTIONS']['MARKETING']['business_specific']:
                        specific_rule = validator.SCORE_RULES['DEDUCTIONS']['MARKETING']['business_specific'][business_type]
                        deduction = min(
                            abs(specific_rule['score']),
                            abs(specific_rule['max_deduction'])
                        )
                    else:
                        deduction = min(
                            abs(validator.SCORE_RULES['DEDUCTIONS']['MARKETING']['score']),
                            abs(validator.SCORE_RULES['DEDUCTIONS']['MARKETING']['max_deduction'])
                        )
                    business_stats[business_type][score_type]['营销关键词'] += deduction
                    break
                    
            # 检查强营销关键词
            for keyword in validator.SCORE_RULES['DEDUCTIONS']['MARKETING']['strong_keywords']:
                if keyword in cleaned_content:
                    business_stats[business_type][inconsistency_type]['强营销关键词'] += 1
                    # 获取业务特定扣分规则
                    if business_type in validator.SCORE_RULES['DEDUCTIONS']['MARKETING']['business_specific']:
                        specific_rule = validator.SCORE_RULES['DEDUCTIONS']['MARKETING']['business_specific'][business_type]
                        deduction = min(
                            abs(specific_rule.get('strong_score', validator.SCORE_RULES['DEDUCTIONS']['MARKETING']['strong_score'])),
                            abs(specific_rule['max_deduction'])
                        )
                    else:
                        deduction = min(
                            abs(validator.SCORE_RULES['DEDUCTIONS']['MARKETING']['strong_score']),
                            abs(validator.SCORE_RULES['DEDUCTIONS']['MARKETING']['max_deduction'])
                        )
                    business_stats[business_type][score_type]['强营销关键词'] += deduction
                    break
                    
            # 检查积分营销关键词
            for keyword in validator.SCORE_RULES['DEDUCTIONS']['POINTS_MARKETING']['keywords']:
                if keyword in cleaned_content:
                    business_stats[business_type][inconsistency_type]['积分营销'] += 1
                    # 获取业务特定扣分规则
                    if business_type in validator.SCORE_RULES['DEDUCTIONS']['POINTS_MARKETING']['business_specific']:
                        specific_rule = validator.SCORE_RULES['DEDUCTIONS']['POINTS_MARKETING']['business_specific'][business_type]
                        deduction = min(
                            abs(specific_rule['score']),
                            abs(specific_rule['max_deduction'])
                        )
                    else:
                        deduction = min(
                            abs(validator.SCORE_RULES['DEDUCTIONS']['POINTS_MARKETING']['score']),
                            abs(validator.SCORE_RULES['DEDUCTIONS']['POINTS_MARKETING']['max_deduction'])
                        )
                    business_stats[business_type][score_type]['积分营销'] += deduction
                    break
                    
            # 检查积分到期关键词
            for keyword in validator.SCORE_RULES['DEDUCTIONS']['POINTS_EXPIRY']['keywords']:
                if keyword in cleaned_content:
                    business_stats[business_type][inconsistency_type]['积分到期'] += 1
                    # 获取业务特定扣分规则
                    if business_type in validator.SCORE_RULES['DEDUCTIONS']['POINTS_EXPIRY']['business_specific']:
                        specific_rule = validator.SCORE_RULES['DEDUCTIONS']['POINTS_EXPIRY']['business_specific'][business_type]
                        deduction = min(
                            abs(specific_rule['score']),
                            abs(specific_rule['max_deduction'])
                        )
                    else:
                        deduction = min(
                            abs(validator.SCORE_RULES['DEDUCTIONS']['POINTS_EXPIRY']['score']),
                            abs(validator.SCORE_RULES['DEDUCTIONS']['POINTS_EXPIRY']['max_deduction'])
                        )
                    business_stats[business_type][score_type]['积分到期'] += deduction
                    break
                    
            # 检查平台关键词
            for keyword in validator.SCORE_RULES['DEDUCTIONS']['PLATFORM']['keywords']:
                if keyword in cleaned_content:
                    business_stats[business_type][inconsistency_type]['平台关键词'] += 1
                    # 获取业务特定扣分规则
                    if business_type in validator.SCORE_RULES['DEDUCTIONS']['PLATFORM']['business_specific']:
                        specific_rule = validator.SCORE_RULES['DEDUCTIONS']['PLATFORM']['business_specific'][business_type]
                        deduction = min(
                            abs(specific_rule['score']),
                            abs(specific_rule['max_deduction'])
                        )
                    else:
                        deduction = min(
                            abs(validator.SCORE_RULES['DEDUCTIONS']['PLATFORM']['score']),
                            abs(validator.SCORE_RULES['DEDUCTIONS']['PLATFORM']['max_deduction'])
                        )
                    business_stats[business_type][score_type]['平台关键词'] += deduction
                    break
                    
            # 检查问卷调查关键词
            for keyword in validator.SCORE_RULES['DEDUCTIONS']['SURVEY']['keywords']:
                if keyword in cleaned_content:
                    business_stats[business_type][inconsistency_type]['问卷调查'] += 1
                    # 获取业务特定扣分规则
                    if business_type in validator.SCORE_RULES['DEDUCTIONS']['SURVEY']['business_specific']:
                        specific_rule = validator.SCORE_RULES['DEDUCTIONS']['SURVEY']['business_specific'][business_type]
                        deduction = min(
                            abs(specific_rule['score']),
                            abs(specific_rule['max_deduction'])
                        )
                    else:
                        deduction = min(
                            abs(validator.SCORE_RULES['DEDUCTIONS']['SURVEY']['score']),
                            abs(validator.SCORE_RULES['DEDUCTIONS']['SURVEY']['max_deduction'])
                        )
                    business_stats[business_type][score_type]['问卷调查'] += deduction
                    break
                    
            # 检查教育营销关键词
            for keyword in validator.SCORE_RULES['DEDUCTIONS']['EDUCATION']['keywords']:
                if keyword in cleaned_content:
                    business_stats[business_type][inconsistency_type]['教育营销'] += 1
                    # 获取业务特定扣分规则
                    if business_type in validator.SCORE_RULES['DEDUCTIONS']['EDUCATION']['business_specific']:
                        specific_rule = validator.SCORE_RULES['DEDUCTIONS']['EDUCATION']['business_specific'][business_type]
                        deduction = min(
                            abs(specific_rule['score']),
                            abs(specific_rule['max_deduction'])
                        )
                    else:
                        deduction = min(
                            abs(validator.SCORE_RULES['DEDUCTIONS']['EDUCATION']['score']),
                            abs(validator.SCORE_RULES['DEDUCTIONS']['EDUCATION']['max_deduction'])
                        )
                    business_stats[business_type][score_type]['教育营销'] += deduction
                    break
            
            # 检查就业招聘关键词
            for keyword in validator.SCORE_RULES['DEDUCTIONS']['EMPLOYMENT']['keywords']:
                if keyword in cleaned_content:
                    business_stats[business_type][inconsistency_type]['就业招聘'] += 1
                    # 获取业务特定扣分规则
                    if business_type in validator.SCORE_RULES['DEDUCTIONS']['EMPLOYMENT']['business_specific']:
                        specific_rule = validator.SCORE_RULES['DEDUCTIONS']['EMPLOYMENT']['business_specific'][business_type]
                        deduction = min(
                            abs(specific_rule['score']),
                            abs(specific_rule['max_deduction'])
                        )
                    else:
                        deduction = min(
                            abs(validator.SCORE_RULES['DEDUCTIONS']['EMPLOYMENT']['score']),
                            abs(validator.SCORE_RULES['DEDUCTIONS']['EMPLOYMENT']['max_deduction'])
                        )
                    business_stats[business_type][score_type]['就业招聘'] += deduction
                    break
                    
    # 输出每个业务类型的统计结果
    for business_type, stats in business_stats.items():
        total = stats['total']
        total_fp = stats['total_fp']
        total_fn = stats['total_fn']
        
        fp_rate = (total_fp / total) * 100 if total > 0 else 0
        fn_rate = (total_fn / total) * 100 if total > 0 else 0
        
        print(f"\n== {business_type} ==")
        print(f"总样本数: {total}条")
        print(f"系统过于严格（人工通过但系统拒绝）: {total_fp}条 ({fp_rate:.1f}%)")
        print(f"系统过于宽松（人工拒绝但系统通过）: {total_fn}条 ({fn_rate:.1f}%)")
        
        # 计算总扣分
        total_fp_score = sum(stats['false_positive_score'].values())
        total_fn_score = sum(stats['false_negative_score'].values())
        
        # 输出系统过于严格的情况下触发的规则统计
        if total_fp > 0:
            print(f"\n系统过严时触发的规则统计（按扣分排序，总计扣分: {total_fp_score:.1f}分）:")
            fp_rules = sorted([(rule, count, stats['false_positive_score'][rule]) 
                             for rule, count in stats['false_positive'].items()], 
                             key=lambda x: x[2], reverse=True)
            for rule, count, score in fp_rules:
                percentage = (score / total_fp_score) * 100 if total_fp_score > 0 else 0
                print(f"  {rule}: {score:.1f}分 ({percentage:.1f}%), 触发{count}次")
        
        # 输出系统过于宽松的情况下触发的规则统计
        if total_fn > 0:
            print(f"\n系统过松时触发的规则统计（按扣分排序，总计扣分: {total_fn_score:.1f}分）:")
            fn_rules = sorted([(rule, count, stats['false_negative_score'][rule]) 
                             for rule, count in stats['false_negative'].items()], 
                             key=lambda x: x[2], reverse=True)
            for rule, count, score in fn_rules:
                percentage = (score / total_fn_score) * 100 if total_fn_score > 0 else 0
                print(f"  {rule}: {score:.1f}分 ({percentage:.1f}%), 触发{count}次")
        
        print("\n规则共现分析:")
        # 分析规则共现情况 - 在同一条短信中同时触发多个规则的情况
        for inconsistency_type, score_type, label in [
            ('false_positive', 'false_positive_score', "系统过严"), 
            ('false_negative', 'false_negative_score', "系统过松")
        ]:
            # 找出扣分最多的前5个规则
            rule_scores = [(rule, stats[inconsistency_type][rule], stats[score_type][rule]) 
                          for rule in stats[inconsistency_type]]
            top_rules = sorted(rule_scores, key=lambda x: x[2], reverse=True)[:5]
            
            if not top_rules:
                continue
                
            print(f"  {label}时规则共现情况:")
            
            for i, (rule1, count1, score1) in enumerate(top_rules):
                # 只统计与排在前面的规则共现的情况，避免重复
                cooccur_with = []
                for rule2, count2, score2 in top_rules[:i]:
                    cooccur_with.append(f"{rule2}({score2:.1f}分)")
                    
                if cooccur_with:
                    print(f"    {rule1}({score1:.1f}分) 经常与 {', '.join(cooccur_with)} 共同出现")
                else:
                    print(f"    {rule1}({score1:.1f}分)")

if __name__ == "__main__":
    analyze_deduction_rules() 