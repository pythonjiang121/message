import json
import re
import os

# 加载姓氏列表
def load_surnames(filename="surnames.json"):
    with open(filename, "r", encoding="utf-8") as f:
        return set(json.load(f))

# 签名审核函数
def validate_signature(signature, surnames):
    # 条件1：检查签名长度是否为2-12个字符
    if len(signature) < 2 or len(signature) > 12:
        return False, "签名长度必须为2~12个字符"

    # 条件2：检查是否包含非法字符（仅允许中文、英文、数字）
    if not re.fullmatch(r'^[\u4e00-\u9fa5a-zA-Z0-9]+$', signature):
        return False, "签名包含非法字符或符号"

    # 条件3：检查是否全英文
    if re.fullmatch(r'^[a-zA-Z]+$', signature):
        return False, "不支持全英文签名"

    # 条件4：检查是否全数字
    if re.fullmatch(r'^\d+$', signature):
        return False, "不支持全数字签名"

    # 条件5：检查测试相关词汇（不区分大小写）
    test_keywords = ["测试", "test", "测试使用"]
    lower_signature = signature.lower()
    for kw in test_keywords:
        if kw in lower_signature:
            return False, f"签名包含测试相关词汇'{kw}'"

    # 条件6：检查受限业务关键词
    restricted_keywords = [
        "贷款", "赌博", "彩票", "色情", "博彩", "赌球", "暴力", "恐吓", "走私",
        "棋牌", "成人用品", "运营商", "移动", "联通", "电信", "积分兑换", "APP下载",
        "金融推广", "投资理财", "整容", "医美"  # 此处应包含所有规范中的禁止关键词
    ]
    for kw in restricted_keywords:
        if kw in signature:
            return False, f"签名包含受限业务关键词'{kw}'"

    # 条件7：检查繁体字（依赖zhconv库）
    try:
        from zhconv import convert
        if convert(signature, 'zh-hans') != signature:
            return False, "签名包含繁体字"
    except ImportError:
        pass  # 未安装库时跳过检查

    # 条件8：检查是否疑似个人姓名（2-4个中文字符，且姓氏在列表中）
    if re.fullmatch(r'^[\u4e00-\u9fa5]{2,4}$', signature):
        if signature[0] in surnames:
            return False, "签名疑似个人姓名"

    # 所有检查通过
    return True, "审核通过"
