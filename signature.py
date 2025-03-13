import re
from unittest.mock import patch


def validate_signature(signature):
    """
    签名审核主函数
    
    参数:
        signature (str): 待审核的签名
        
    返回:
        tuple: (是否通过审核, 审核消息)
    """
    
    # 1. 检查签名是否包含非法字符（仅允许中文、英文、数字、短横线）
    if not re.fullmatch(r'^[\u4e00-\u9fa5a-zA-Z0-9-]+$', signature):
        return False, "签名包含非法字符或符号"

    # 2. 检查是否为纯数字签名
    if re.fullmatch(r'^\d+$', signature):
        return False, "不支持全数字签名"

    # 3. 检查是否为中性签名（没有明确主体的签名）
    neutral_keywords = [
        "恭喜发财", "温馨提醒", "友情提示", "特别通知", "紧急通知",
        "温馨服务", "贴心服务", "便民服务", "客户服务", "系统通知",
        "系统消息", "流动服务站", "特卖提示", "企业福利" , "城中区两个责任专班" , "企业福利" , "通道消防"
        "M会员商店","自助涮烤"
    ]

    #签名只有keywords，没有其他字，则不允许通过
    if signature in neutral_keywords:
        return False, f"不允许使用中性签名，如：{signature}"

    # 4. 检查是否为政府机构签名
    gov_keywords = ["国家", "部", "局", "公安", "机关"]
    if any(keyword in signature for keyword in gov_keywords):
        return True, "审核通过"

    # 5. 所有检查通过
    return True, "审核通过"


