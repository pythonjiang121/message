import re
import argparse
import sys

def contains_link(text: str):
    """
    使用正则表达式检查文本中是否包含链接，包括IP地址
    
    Args:
        text: 待检查的文本
        
    Returns:
        (是否包含链接, 链接数量, 匹配的链接列表)
    """
    # 定义链接匹配模式
    url_patterns = [
        # 标准URL格式
        r'(?:https?|ftp|file|ws|wss)://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*',
        
        # 带www的网址
        r'(?:www|wap|m)\.(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*',
        
        # 常见顶级域名格式
        r'(?:[-\w.]|(?:%[\da-fA-F]{2}))+\.(?:com|cn|net|org|gov|edu|io|app|top|me|tv|cc|shop|vip|ltd|store|online|tech|site|wang|cloud|link|live|work|game|fun|art|xin|ren|space|team|news|law|group|center|city|world|life|co|red|mobi|pro|info|name|biz|asia|tel|club|social|video|press|company|website|email|network|studio|design|software|blog|wiki|forum|run|zone|plus|cool|show|gold|today|market|business|company|zone|media|agency|directory|technology|solutions|international|enterprises|industries|management|consulting|services)(?:/[^\s]*)?',
        
        # 短链接格式
        r'(?:t|u|dwz|url|c|s|m|j|h5|v|w)\.(?:cn|com|me|ly|gl|gd|ink|run|app|fun|pub|pro|vip|cool|link|live|work|game|art|red|tel|club|show|gold|today)(?:/[-\w]+)+',
        
        # 特定平台短链接
        r'(?:tb\.cn|jd\.com|ele\.me|douyin\.com|weibo\.com|qq\.com|taobao\.com|tmall\.com|pinduoduo\.com|kuaishou\.com|bilibili\.com|youku\.com|iqiyi\.com|meituan\.com|dianping\.com|alipay\.com|weixin\.qq\.com)/[-\w/]+',
        
        # IPv4地址格式
        r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?::\d{1,5})?(?:/[^\s]*)?',
        
        # IPv6地址格式
        r'(?:(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9]))(?::\d{1,5})?(?:/[^\s]*)?',
        
        # 带端口的IP地址格式
        r'(?:https?://)?(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?):\d{1,5}(?:/[^\s]*)?'
    ]
    
    # 存储所有匹配的链接
    all_matches = []
    
    # 逐个应用正则表达式并收集匹配结果
    for i, pattern in enumerate(url_patterns):
        pattern_name = [
            "标准URL", "WWW网址", "常见域名", "短链接", 
            "平台短链接", "IPv4地址", "IPv6地址", "带端口IP"
        ][i]
        
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            for match in matches:
                all_matches.append((pattern_name, match))
    
    # 对匹配结果去重
    unique_matches = []
    seen = set()
    for pattern_name, match in all_matches:
        if match not in seen:
            unique_matches.append((pattern_name, match))
            seen.add(match)
    
    return len(unique_matches) > 0, len(unique_matches), unique_matches

def test_ip_address(text):
    """测试IP地址检测功能"""
    has_link, count, matches = contains_link(text)
    
    print(f"\n============= 测试结果 =============")
    print(f"输入文本: {text}")
    print(f"包含链接/IP: {'是' if has_link else '否'}")
    print(f"检测到的链接/IP数量: {count}")
    
    if matches:
        print("\n============= 匹配详情 =============")
        for i, (pattern_name, match) in enumerate(matches, 1):
            print(f"{i}. 类型: {pattern_name}")
            print(f"   匹配: {match}")
    
    return has_link, count, matches

def main():
    parser = argparse.ArgumentParser(description='测试IP地址和链接检测功能')
    parser.add_argument('--text', type=str, help='要测试的文本')
    parser.add_argument('--file', type=str, help='包含测试文本的文件')
    parser.add_argument('--sample', action='store_true', help='运行样例测试')
    
    args = parser.parse_args()
    
    if args.sample:
        # 运行示例测试用例
        samples = [
            "请访问我们的网站 http://example.com 获取更多信息",
            "【缪偲科技】您的验证码为：午夜激晴，韩，欧高清无吗118.145.211.233 ,有效期为 n 分钟,请确保是本人操作,不要把验证码泄露给其他人",
            # "连接到 192.168.1.1:8080 查看监控",
            # "IPv6地址: 2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            # "缩写IPv6: 2001:db8::1",
            # "混合地址: ::ffff:192.168.1.1",
            # "本地链路: fe80::1234%eth0",
            # "请通过 http://192.168.1.1:8080/login 登录管理界面",
            # "测试短信内容：请登录到 10.0.0.1 进行系统升级，或访问 https://example.com 查看详情",
            # "请在浏览器中访问 [::1]:8080 或 127.0.0.1 进行本地调试",
            # "私域IP测试: 192.168.0.1, 10.0.0.1, 172.16.0.1",
            # "特殊格式: http://[2001:db8::1]:8080/path"
        ]
        
        for i, sample in enumerate(samples, 1):
            print(f"\n\n======== 示例 {i} ========")
            test_ip_address(sample)
    
    elif args.text:
        # 测试单个文本
        test_ip_address(args.text)
    
    elif args.file:
        # 从文件读取测试文本
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read().strip()
                test_ip_address(text)
        except Exception as e:
            print(f"读取文件时出错: {str(e)}")
    
    else:
        # 交互模式
        print("请输入要测试的文本 (输入'exit'结束):")
        while True:
            text = input("> ")
            if text.lower() == 'exit':
                break
            test_ip_address(text)

if __name__ == "__main__":
    main()