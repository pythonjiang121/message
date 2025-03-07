import re
import requests
from urllib.parse import urlparse
from zhconv import convert  # 需要安装：pip install zhconv

class SMSContentValidator:
    def __init__(self):
        # 初始化禁用关键词列表（保留真正敏感的关键词）
        self.restricted_keywords = [
            "代开发票", "代办证件", "贷款", "赌博", "彩票", "色情", "博彩", "赌球", 
            "暴力", "恐吓", "走私", "成人用品", "虚拟货币", "刻章", "A货", 
            "烟酒", "代理注册", "信用卡提额", "中奖", "一元夺宝", "代写论文"
        ]
        
        # 允许的特殊符号（放宽限制）
        self.allowed_symbols = r'''★→㎡①✓✔'''
        
        # 链接检测正则
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )

        # 允许的短链接域名（增加常用的短链接服务）
        self.allowed_short_domains = [
            't.cn', 'url.cn', 'dwz.cn'  # 允许常用的短链接服务
        ]
        
    def validate_content(self, content: str) -> tuple:
        """
        短信内容审核主函数
        返回：(是否通过, 失败原因)
        """
        # 1. 长度校验
        if len(content) < 1 or len(content) > 500:
            return False, "内容长度需在1-500个字符之间"

        # 2. 括号校验（放宽限制）
        left_count = content.count('【')
        right_count = content.count('】')
        if left_count != right_count:
            return False, "【】符号必须成对出现"
        if left_count > 2:  # 允许最多两对【】
            return False, "【】符号最多出现两次"

        # 3. 特殊符号校验（只检查不在允许列表中的符号）
        for char in content:
            if char not in self.allowed_symbols and ord(char) > 0x2000:  # 只检查扩展字符集
                if not char.isalnum() and not char.isspace() and char not in '，。！？【】()（）:：;；""\'\'':
                    return False, f"包含未经允许的特殊符号: {char}"

        # 4. 繁体字校验（保持）
        if convert(content, 'zh-hans') != content:
            return False, "包含繁体字或异体字"

        # 5. 禁用关键词校验（使用更严格的匹配）
        lower_content = content.lower()
        for kw in self.restricted_keywords:
            if f" {kw} " in f" {lower_content} ":  # 确保是独立的词，而不是词的一部分
                return False, f"包含禁止内容：{kw}"

        # 6. 联系方式校验（放宽限制）
        if self._contains_illegal_contact_info(content):
            return False, "包含非法联系方式"

        # 7. 链接校验（放宽限制）
        url_violation = self._check_urls(content)
        if url_violation:
            return False, url_violation

        return True, "审核通过"

    def _contains_illegal_contact_info(self, text: str) -> bool:
        """检测非法联系方式（放宽限制）"""
        patterns = [
            r'[加➕](v|V|w|W).*\d{6,}',  # 只匹配明显的微信号码
            r'[加➕](q|Q){2}.*\d{6,}',   # 只匹配明显的QQ号码
            r'\d{5,11}@qq\.com',         # QQ邮箱
        ]
        return any(re.search(pattern, text) for pattern in patterns)

    def _check_urls(self, text: str) -> str:
        """链接合规性检查（放宽限制）"""
        urls = self.url_pattern.findall(text)
        for url in urls:
            # 检查短链接（允许指定的短链接服务）
            domain = urlparse(url).netloc
            if domain not in self.allowed_short_domains:
                # 检查链接可访问性
                try:
                    response = requests.head(url, timeout=5)
                    if response.status_code >= 400:  # 只有明显的错误状态码才拒绝
                        return f"链接无法访问：{url}"
                except requests.RequestException:
                    pass  # 忽略连接错误
            
            # 检查下载链接（放宽限制）
            if self._is_dangerous_download_link(url):
                return f"链接涉及危险下载：{url}"
        return ""

    def _is_dangerous_download_link(self, url: str) -> bool:
        """检查是否为危险下载链接（只检查明显的可执行文件）"""
        dangerous_extensions = ['.exe', '.msi', '.bat', '.sh', '.apk']
        return any(url.lower().endswith(ext) for ext in dangerous_extensions)

# 测试用例
if __name__ == "__main__":
    validator = SMSContentValidator()
    
    test_cases = [
        ("【重要通知】您的验证码是1234", True),
        ("【系统】【通知】请查收", True),
        ("点击 t.cn/xxx 查看详情", True),
        ("回复TD退订", True),
        ("限时优惠活动", True),
        ("正常★符号", True),
        ("下载APP了解更多", True),
        ("代开发票优惠", False),
        ("加V12345678", False),
        ("點擊查看", False),
    ]

    for content, expected in test_cases:
        result, reason = validator.validate_content(content)
        status = "通过" if result else "拒绝"
        print(f"内容：{content[:20]:<20} 预期：{expected}\t实际：{status}\t原因：{reason}")