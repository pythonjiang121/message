import re
import json
import jieba.posseg as pseg
from typing import Tuple, Dict, List, Set

class BusinessValidator:
    # 业务类型库
    BUSINESS_TYPE_LIBRARY: Dict[str, List[str]] = {
        "行业": ["行业-通知", "行业-物流"],
        "会销": ["会销-普通", "会销-金融"],
        "拉新": ["拉新-催收", "拉新-教育", "拉新-网贷", "拉新-展会", "拉新-医美", "拉新-pos机"]
    }

    # 关键词常量定义
    STORE_KEYWORDS: Set[str] = {"旗舰店", "专卖店"}
    INSURANCE_KEYWORDS: Set[str] = {"保险", "寿险", "车险", "意外险", "养老险", "医疗险", "财险"}
    MARKETING_KEYWORDS: Set[str] = {
        "优惠", "特惠", "红包", "权益", "购买", "付款",  "交纳", 
        "积分", "抢购", "充值", "首冲", "购票", "尾款", 
        "缴纳", "嘉宾", "预售", "现金", "限量","福利", "过期", "缴费"
    }
    SURVEY_KEYWORDS: Set[str] = {"问卷", "调查", "调研", "邀请",  }
    REAL_ESTATE_KEYWORDS: Set[str] = {
        "房产", "地产", "楼盘", "房源", "售楼", "公寓",  "别墅",
        "商铺", "写字楼", "购房", "房贷", "买房", "卖房", "租房",
        "房价", "面积", "户型", "地段", "学区房", "精装修", "毛坯"
    }
    JEWELRY_KEYWORDS: Set[str] = {"黄金", "珠宝"}
    EDUCATION_KEYWORDS: Set[str] = {"课程", "讲解", "考前" , "练习册" }
    ENROLLMENT_KEYWORDS: Set[str] = {
        "招生", "入学", "报考", "入学考试", "办学",
        "招收", "招收学生", "新生", "入学通知", "留学"
    }
    ANNUAL_PENALTY_KEYWORDS: Set[str] = {
        "年报", "年度报告", "年检", "罚款", "处罚", "违规处理",
        "违章处理", "缴纳罚款", "行政处罚"
    }
    GAME_KEYWORDS: Set[str] = {"游戏", "游戏币", "游戏充值"}
    MEDICAL_KEYWORDS: Set[str] = {"义诊", "会诊", "疾病", "复诊"}
    RACING_PIGEON_KEYWORDS: Set[str] = {"赛鸽", "开笼"}
    LOTTERY_KEYWORDS: Set[str] = {"抽奖", "开奖"}
    BIDDING_KEYWORDS: Set[str] = {
        "招标", "投标", "标书", "中标", "竞标", "招投标", "投标人",
        "招标人", "标段", "投标书", "招标书", "开标", "评标",
        "招标文件", "投标文件"
    }
    BLOOD_DONATION_KEYWORDS: Set[str] = {
        "献血", "献浆", "血浆", "无偿献血", "志愿献血", "捐血",
        "捐献血浆", "血液", "浆站", "献血站"
    }
    LOGISTICS_KEYWORDS: Set[str] = {
        "快递", "物流", "派送", "配送", "运单", "包裹", "签收", "取件",
        "收件", "发件", "寄件", "运输", "送货", "揽收", "仓储", "仓库",
        "货运", "提货", "站点"
    }
    EXHIBITION_KEYWORDS: Set[str] = {
        "展会", "展览", "展销", "展位", "展台", "展馆", "展区", "展期",
        "参展", "观展", "博览会", "交易会", "展销会", "展示会", "展览馆",
        "家博会", "博览"
    }
    WECHAT_KEYWORDS: Set[str] = {"微信", "公众号", "关注", "小程序"}
    NAME_WHITELIST: Set[str] = {"您好", "本人"}

    # 新增征兵相关词
    MILITARY_RECRUITMENT_KEYWORDS: Set[str] = {
        "征兵", "入伍"
    }

    # 新增交友相关词
    DATING_KEYWORDS: Set[str] = {
        "交友", "相亲", "留言"
    }

    # 新增招聘相关词
    RECRUITMENT_KEYWORDS: Set[str] = {
        "招聘", "应聘", "求职", "面试", "简历", "岗位", "职位",
        "用工", "聘用", "招工", "用人", "入职", "应届生",
        "社招", "校招", "人才", "求贤", "职场"
    }

    # 新增参会邀请相关词
    MEETING_INVITATION_KEYWORDS: Set[str] = {
        "参会", "会议", "论坛", "峰会", "研讨会", "座谈会",
        "年会", "发布会", "见面会", "交流会", "答谢会", "分享会", "学会"
    }
    #会销类检测积分到期，积分清零，积分兑换，积分过期，积分作废，积分即将到期，积分即将清零，积分即将作废，积分失效
    # 积分相关词
    POINTS_KEYWORDS: Set[str] = {"积分"}
    
    # 到期/清零相关词
    POINTS_ACTION_KEYWORDS: Set[str] = {
        "到期", "清零", "兑换", "过期", "作废", "失效",
        "即将到期", "即将清零", "即将作废", "清理", "清空"
    }

    # 新增下载和客服相关关键词
    CUSTOMER_SERVICE_KEYWORDS: Set[str] = {  "微信搜索", "详询客服", "咨询客服", "联系客服", "添加客服"}

    # 新增直播相关关键词
    LIVE_STREAMING_KEYWORDS: Set[str] = {"直播", "带货", "主播", "观看直播", "直播间", "连麦"}

    def __init__(self):
        """初始化验证器，加载姓氏数据"""
        try:
            with open('surnames.json', 'r', encoding='utf-8') as f:
                self.surnames = set(json.load(f))
        except Exception as e:
            print(f"Warning: Could not load surnames.json: {e}")
            self.surnames = set()

    def validate_business(self, business_type: str, content: str, signature: str) -> Tuple[bool, str]:
        """
        验证业务类型是否符合规则
        
        Args:
            business_type: 客户业务类型
            content: 短信内容
            signature: 短信签名
            
        Returns:
            (是否通过, 原因说明)
        """
        content = content.lower().replace(" ", "").replace("-", "")
        signature = signature.lower()

        # 获取业务类别
        business_category = self._get_business_category(business_type)
        if not business_category:
            return False, "未知的业务类型"

        # 根据业务类别进行验证
        if business_category == "行业":
            return self._validate_industry(business_type, content, signature)
        elif business_category == "会销":
            return self._validate_marketing(business_type, content, signature)
        elif business_category == "拉新" and business_type == "拉新-催收":
            return self._validate_collection(content)

        return True, "审核通过"

    def _get_business_category(self, business_type: str) -> str:
        """获取业务类别"""
        for category, types in self.BUSINESS_TYPE_LIBRARY.items():
            if business_type in types:
                return category
        return ""

    def _validate_industry(self, business_type: str, content: str, signature: str) -> Tuple[bool, str]:
        """验证行业类短信"""

        # 行业-通知特殊验证
        if business_type == "行业-通知":
            if any(keyword in signature for keyword in self.STORE_KEYWORDS):
                return False, "行业-通知类短信的签名不允许包含旗舰店、专卖店等商业字样，需要人工审核"
            
            if any(keyword in signature for keyword in self.JEWELRY_KEYWORDS):
                return False, "行业-通知类短信的签名不允许包含黄金珠宝相关字样"

            # 验证直播相关内容
            if any(keyword in content for keyword in self.LIVE_STREAMING_KEYWORDS):
                return False, "行业-通知类短信不允许包含直播相关内容"

        # 验证物流类型
        if business_type == "行业-物流":
            if not any(keyword in content for keyword in self.LOGISTICS_KEYWORDS):
                return False, "行业-物流类短信必须包含物流相关内容"

        # 通用验证
        for keywords, error_msg in [
            (self.MARKETING_KEYWORDS, "行业类短信不允许包含营销内容"),
            (self.SURVEY_KEYWORDS, "行业类短信不允许包含问卷调查内容"),
            (self.JEWELRY_KEYWORDS, "行业类短信不允许包含黄金珠宝相关内容"),
            (self.EDUCATION_KEYWORDS, "行业类短信不允许包含教育营销相关内容"),
            (self.ENROLLMENT_KEYWORDS, "行业类短信不允许包含招生相关内容"),
            (self.ANNUAL_PENALTY_KEYWORDS, "行业类短信不允许包含年报或罚款相关内容"),
            (self.MEDICAL_KEYWORDS, "行业类短信不允许包含医疗拉新相关内容"),
            (self.RACING_PIGEON_KEYWORDS, "行业类短信不允许包含赛鸽相关内容"),
            (self.LOTTERY_KEYWORDS, "行业类短信不允许包含抽奖相关内容"),
            (self.BIDDING_KEYWORDS, "行业类短信不允许包含招标投标相关内容"),
            (self.BLOOD_DONATION_KEYWORDS, "行业类短信不允许包含献血献浆相关内容"),
            (self.EXHIBITION_KEYWORDS, "行业类短信不允许包含展会相关内容"),
            (self.MILITARY_RECRUITMENT_KEYWORDS, "行业类短信不允许包含征兵相关内容"),
            (self.REAL_ESTATE_KEYWORDS, "行业类短信不允许包含房地产相关内容"),
            (self.RECRUITMENT_KEYWORDS, "行业类短信不允许包含招聘相关内容")
        ]:
            if any(keyword in content for keyword in keywords):
                return False, error_msg

        
            # 验证私人号码
            if self._contains_private_number(content):
                return False, "行业-通知类短信不允许包含私人号码"

        return True, "审核通过"

    def _validate_marketing(self, business_type: str, content: str, signature: str) -> Tuple[bool, str]:
        """验证会销类短信"""
        # 验证私人号码
        if self._contains_private_number(content):
            return False, "会销类短信不允许包含私人号码"

        # 验证积分到期相关内容
        #if any(point_word in content for point_word in self.POINTS_KEYWORDS) and \
        #   any(action_word in content for action_word in self.POINTS_ACTION_KEYWORDS):
        #    return False, "会销类短信不允许包含积分到期或清零相关内容"

        # 验证抽奖相关内容
        if any(keyword in content for keyword in self.LOTTERY_KEYWORDS):
            return False, "会销类短信不允许包含抽奖相关内容"

        # 会销-普通特殊验证
        if business_type == "会销-普通":
            # 验证客服相关内容
            if any(keyword in content for keyword in self.CUSTOMER_SERVICE_KEYWORDS):
                return False, "会销-普通类短信不允许添加客服相关内容"

            if any(keyword in content for keyword in self.GAME_KEYWORDS):
                return False, "会销-普通类短信不允许包含游戏相关内容"

            if any(keyword in content for keyword in self.DATING_KEYWORDS):
                return False, "会销-普通类短信不允许包含交友相关内容"

            if any(keyword in signature for keyword in self.INSURANCE_KEYWORDS):
                return False, "会销-普通类短信的签名不允许包含保险相关字样"

            if any(keyword in signature for keyword in self.JEWELRY_KEYWORDS):
                return False, "会销-普通类短信的签名不允许包含黄金珠宝相关字样"

        # 通用验证
        for keywords, error_msg in [
            (self.REAL_ESTATE_KEYWORDS, "会销类短信不允许包含房地产相关内容"),
            (self.EXHIBITION_KEYWORDS, "会销类短信不允许包含展会相关内容"),
            (self.EDUCATION_KEYWORDS, "会销类短信不允许包含教育营销相关内容"),
            (self.MEDICAL_KEYWORDS, "会销类短信不允许包含医疗拉新相关内容"),
            (self.JEWELRY_KEYWORDS, "会销类短信不允许包含黄金珠宝相关内容"),
            (self.MEETING_INVITATION_KEYWORDS, "会销类短信不允许包含参会邀请相关内容")
        ]:
            if any(keyword in content for keyword in keywords):
                return False, error_msg

        # 验证公众号关键词
        if all(keyword in content for keyword in self.WECHAT_KEYWORDS):
            return False, "会销类短信不允许包含关注公众号相关内容"

        return True, "审核通过"

    def _validate_collection(self, content: str) -> Tuple[bool, str]:
        """验证催收类短信"""
        if self._find_chinese_names(content):
            return False, "催收类短信不允许包含姓名"
        return True, "审核通过"

    def _contains_private_number(self, text: str) -> bool:
        """检查是否包含私人号码"""
        pattern = r'1[3-9]\d{9}|1[3-9]\d{4}[ -]\d{4}|1[3-9][ -]\d{4}[ -]\d{4}'
        return bool(re.search(pattern, text))

    def _find_chinese_names(self, text: str) -> bool:
        """
        查找中文姓名（使用Jieba分词+规则过滤）
        
        Args:
            text: 待检查的文本
            
        Returns:
            bool: 如果找到中文姓名返回False，否则返回True
        """
        # 移除白名单词（避免误判，例如"公司名"中的"王"）
        for word in self.NAME_WHITELIST:
            text = text.replace(word, "")
        
        # 使用Jieba分词并标注词性（'nr'为人名）
        words = list(pseg.cut(text))
        
        # 遍历分词结果查找人名
        for i, pair in enumerate(words):
            word, flag = pair.word, pair.flag
            if flag == 'nr':  # 初步筛选人名
                # 移除可能的标点或空格干扰
                clean_name = re.sub(r'[^\u4e00-\u9fa5]', '', word)
                
                # 基本长度和姓氏检查
                if not (2 <= len(clean_name) <= 4 and clean_name[0] in self.surnames):
                    continue
                               
                return True  # 找到符合条件的姓名
        
        return False  # 未找到符合条件的姓名

def validate_business(business_type: str, content: str, signature: str) -> Tuple[bool, str]:
    """
    验证业务类型是否符合规则的便捷函数
    
    Args:
        business_type: 客户业务类型
        content: 短信内容
        signature: 短信签名
        
    Returns:
        (是否通过, 原因说明)
    """
    validator = BusinessValidator()
    return validator.validate_business(business_type, content, signature)

