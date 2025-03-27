import unittest
from business import BusinessValidator

class TestNameDetection(unittest.TestCase):
    def setUp(self):
        self.validator = BusinessValidator()

    def test_standard_chinese_name(self):
        """测试标准中文姓名"""
        text = "【】王大力"
        self.assertTrue(self.validator._find_chinese_names(text))

    def test_name_with_punctuation(self):
        """测试带标点符号的姓名"""
        text = "王大力，"
        self.assertTrue(self.validator._find_chinese_names(text))

    def test_name_in_sentence(self):
        """测试句子中的姓名"""
        text = "尊敬的张三先生您好"
        self.assertTrue(self.validator._find_chinese_names(text))

    def test_multiple_names(self):
        """测试多个姓名"""
        text = "李四和王五"
        self.assertTrue(self.validator._find_chinese_names(text))

    def test_name_with_title(self):
        """测试带称谓的姓名"""
        text = "张老师"
        self.assertFalse(self.validator._find_chinese_names(text))

    def test_name_with_company(self):
        """测试公司名中的姓名"""
        text = "阿里巴巴"
        self.assertFalse(self.validator._find_chinese_names(text))

    def test_name_with_brand(self):
        """测试品牌名中的姓名"""
        text = "华为"
        self.assertFalse(self.validator._find_chinese_names(text))

    def test_name_with_place(self):
        """测试地名中的姓名"""
        text = "北京"
        self.assertFalse(self.validator._find_chinese_names(text))

    def test_name_with_product(self):
        """测试产品名中的姓名"""
        text = "小米手机"
        self.assertFalse(self.validator._find_chinese_names(text))

    def test_name_with_organization(self):
        """测试组织名中的姓名"""
        text = "腾讯科技"
        self.assertFalse(self.validator._find_chinese_names(text))

    def test_name_with_website(self):
        """测试网站名中的姓名"""
        text = "百度搜索"
        self.assertFalse(self.validator._find_chinese_names(text))

    def test_name_with_common_words(self):
        """测试常见词中的姓名"""
        text = "人民"
        self.assertFalse(self.validator._find_chinese_names(text))

    def test_name_with_foreign_name(self):
        """测试外国名字"""
        text = "John Smith"
        self.assertFalse(self.validator._find_chinese_names(text))

    def test_name_with_mixed_content(self):
        """测试混合内容中的姓名"""
        text = "【ELLASSAY】亲爱的会员，在新的一个月，我们迎来了专属于您的生日月。衷心祝您生日快乐，生活幸福美满！"
        self.assertFalse(self.validator._find_chinese_names(text))

    def test_name_with_short_name(self):
        """测试短名字"""
        text = "王"
        self.assertFalse(self.validator._find_chinese_names(text))

    def test_name_with_long_name(self):
        """测试长名字"""
        text = "王大力大力"
        self.assertFalse(self.validator._find_chinese_names(text))

    def test_name_with_special_characters(self):
        """测试特殊字符中的姓名"""
        text = "王@大力"
        self.assertTrue(self.validator._find_chinese_names(text))

    def test_name_with_numbers(self):
        """测试数字中的姓名"""
        text = "王123大力"
        self.assertTrue(self.validator._find_chinese_names(text))

    def test_name_with_spaces(self):
        """测试空格中的姓名"""
        text = "王 大力"
        self.assertTrue(self.validator._find_chinese_names(text))

    def test_name_with_emojis(self):
        """测试表情符号中的姓名"""
        text = "王😊大力"
        self.assertTrue(self.validator._find_chinese_names(text))

    def test_empty_text(self):
        """测试空文本"""
        text = ""
        self.assertFalse(self.validator._find_chinese_names(text))

    def test_none_text(self):
        """测试None文本"""
        text = None
        self.assertFalse(self.validator._find_chinese_names(text))

if __name__ == '__main__':
    unittest.main() 