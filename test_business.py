import unittest
from business import BusinessValidator, validate_business

class TestBusinessValidator(unittest.TestCase):
    def setUp(self):
        self.validator = BusinessValidator()

    def test_business_validation(self):
        """测试业务验证功能"""
        print("\n=== 短信审核测试开始 ===\n")
        
        # 测试用例1：会销-普通类型
        content1 = "【香蜜闺秀】生日快乐~2月到店免费领棉柔巾1包，还有10元无门槛文胸券！新品文胸买1送1！领>i.smdx.net/wfzmj 拒收请回复R"
        signature1 = "香蜜闺秀"
        business_type1 = "会销-普通"
        account_type1 = "云平台"
        
        print(f"测试用例1 - 会销-普通类型:")
        print(f"短信内容: {content1}")
        print(f"短信签名: {signature1}")
        print(f"业务类型: {business_type1}")
        print(f"账户类型: {account_type1}")
        result1, msg1 = validate_business(business_type1, content1, signature1, account_type1)
        print(f"审核结果: {msg1}\n")

        # 测试用例2：行业-通知类型（包含地址和链接）
        content2 = "您的快递已到达北京市海淀区中关村科技园区，详情请访问 www.example.com"
        signature2 = "顺丰速运"
        business_type2 = "行业-通知"
        account_type2 = "云平台"
        
        print(f"测试用例2 - 行业-通知类型:")
        print(f"短信内容: {content2}")
        print(f"短信签名: {signature2}")
        print(f"业务类型: {business_type2}")
        print(f"账户类型: {account_type2}")
        result2, msg2 = validate_business(business_type2, content2, signature2, account_type2)
        print(f"审核结果: {msg2}\n")

        # 测试用例3：行业-物流类型（包含物流关键词）
        content3 = "您的快递已到达上海市浦东新区，物流信息请访问 www.example.com"
        signature3 = "中通快递"
        business_type3 = "行业-物流"
        account_type3 = "云平台"
        
        print(f"测试用例3 - 行业-物流类型:")
        print(f"短信内容: {content3}")
        print(f"短信签名: {signature3}")
        print(f"业务类型: {business_type3}")
        print(f"账户类型: {account_type3}")
        result3, msg3 = validate_business(business_type3, content3, signature3, account_type3)
        print(f"审核结果: {msg3}\n")

        # 测试用例4：直客类型
        content4 = "您的订单已发货，请查收"
        signature4 = "测试签名"
        business_type4 = "行业-通知"
        account_type4 = "直客"
        
        print(f"测试用例4 - 直客类型:")
        print(f"短信内容: {content4}")
        print(f"短信签名: {signature4}")
        print(f"业务类型: {business_type4}")
        print(f"账户类型: {account_type4}")
        result4, msg4 = validate_business(business_type4, content4, signature4, account_type4)
        print(f"审核结果: {msg4}\n")

        # 测试用例5：行业-通知类型（多个地址和链接）
        content5 = """
        活动地址1：北京市朝阳区三里屯
        活动地址2：上海市浦东新区陆家嘴
        详情请访问：www.example1.com
        更多信息：www.example2.com
        """
        signature5 = "测试签名"
        business_type5 = "行业-通知"
        account_type5 = "云平台"
        
        print(f"测试用例5 - 行业-通知类型(多地址链接):")
        print(f"短信内容: {content5}")
        print(f"短信签名: {signature5}")
        print(f"业务类型: {business_type5}")
        print(f"账户类型: {account_type5}")
        result5, msg5 = validate_business(business_type5, content5, signature5, account_type5)
        print(f"审核结果: {msg5}\n")
        
        print("=== 短信审核测试结束 ===\n")

if __name__ == '__main__':
    unittest.main() 