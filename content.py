import re
from urllib.parse import urlparse


class SMSContentValidator:
    def __init__(self):
        # 初始化禁用关键词列表（保留真正敏感的关键词）
        self.restricted_keywords = [
            "代开发票", "代办证件", "赌博", "色情", "博彩", "赌球", 
            "暴力", "恐吓", "走私", "成人用品", "虚拟货币", "刻章", "A货", 
            "烟酒", "代理注册",  "中奖", "一元夺宝", "代写论文"
        ]

    def validate_content(self, content: str) -> tuple:
        """
        短信内容审核主函数
        返回：(是否通过, 失败原因)
        """
        
        # 检查中文中括号数量
        left_brackets = content.count("【")
        right_brackets = content.count("】")
        
        # 检查是否只有一对中文中括号
        if left_brackets > 1 or right_brackets > 1:
            return False, "只允许使用一对中文中括号"
        
        # 检查禁用关键词
        lower_content = content.lower()
        for kw in self.restricted_keywords:
            if f" {kw} " in f" {lower_content} ":  # 确保是独立的词，而不是词的一部分
                return False, f"包含禁止内容：{kw}"

        return True, "审核通过"


# 测试用例
if __name__ == "__main__":
    validator = SMSContentValidator()
    
    test_cases = [
        ("您的验证码是1234", True),
        ("系统通知请查收", True),
        ("点击链接查看详情", True),
        ("回复TD退订", True),
        ("限时优惠活动", True),
        ("正常★符号", True),
        ("下载APP了解更多", True),
        ("代开发票优惠", False),
        ("加V12345678", True),
        ("點擊查看", True),
    ]

    for content, expected in test_cases:
        result, reason = validator.validate_content(content)
        status = "通过" if result else "拒绝"
        print(f"内容：{content[:20]:<20} 预期：{expected}\t实际：{status}\t原因：{reason}")