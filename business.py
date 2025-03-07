import re

def validate_business(business_type: str, content: str, account_type: str) -> bool:
    """
    验证业务类型是否符合规则
    
    Args:
        business_type (str): 客户业务类型
        content (str): 短信内容
        account_type (str): 账户类型
        
    Returns:
        bool: True表示通过，False表示驳回
    """
    content = content.lower()  # 统一转小写方便匹配
    
    # 定义客户业务类型库
    business_type_library = {
        "行业": ["行业-通知", "行业-营销"],
        "会销": ["会销-普通", "会销-会员营销"],
        "营销": ["营销-拉新", "营销-促销"],
        "客户类型": ["客户类型-普通", "客户类型-会员"]
    }
    
    # 定义匹配规则
    # 营销特征词（减少敏感词数量，保留核心营销词）
    marketing_keywords = [
        "优惠券", "红包", "抢购", "秒杀", "特价",
        "限时特惠", "爆款", "秒杀", "0元购",
        "免费领取", "免费试用", "免费体验"
    ]
    
    # 私人号码匹配规则（放宽限制，只匹配明显的手机号）
    private_number_pattern = r'(?<![0-9])(1[3-9]\d{9})(?![0-9])'
    
    # 规则判断逻辑
    if business_type in business_type_library.get("行业", []):
        # 规则1: 检查营销内容（放宽限制）
        has_marketing = any(f" {keyword} " in f" {content} " for keyword in marketing_keywords)
        
        # 规则2: 检查私人号码
        has_private_number = bool(re.search(private_number_pattern, content))
        
        # 如果同时包含营销内容和私人号码，则驳回
        return not (has_marketing and has_private_number)
        
    elif business_type in business_type_library.get("会销", []):
        # 只检查明显的私人号码
        has_private_number = bool(re.search(private_number_pattern, content))
        # 如果是会员营销且包含私人号码，则驳回
        if "会员营销" in business_type:
            return not has_private_number
        # 普通会销允许包含私人号码
        return True
        
    elif business_type in business_type_library.get("营销", []):
        # 营销短信直接放行
        return True
    
    # 默认放行
    return True

# 测试用例
if __name__ == "__main__":
    test_cases = [
        ("行业-通知", "这是一条普通通知", "直客", True),
        ("行业-营销", "限时特惠活动", "直客", True),
        ("行业-通知", "联系电话13800138000限时特惠", "直客", False),
        ("会销-普通", "联系电话13800138000", "直客", True),
        ("会销-会员营销", "联系电话13800138000", "直客", False),
        ("营销-拉新", "限时特惠联系13800138000", "直客", True),
    ]
    
    for business_type, content, account_type, expected in test_cases:
        result = validate_business(business_type, content, account_type)
        print(f"业务类型: {business_type}")
        print(f"内容: {content}")
        print(f"账户类型: {account_type}")
        print(f"预期结果: {expected}")
        print(f"实际结果: {result}")
        print("---")

