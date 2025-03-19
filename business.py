import re
import json
import jieba.posseg as pseg
from typing import Tuple, Dict, List, Set
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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

    # 定义评分规则
    SCORE_RULES = {
        # 基础分数
        'BASE_SCORE': {
            '行业': {
                '行业-通知': 100,  # 保持通知类基础分
                '行业-物流': 95,   # 保持物流类基础分
            },
            '会销': {
                '会销-普通': 95,   # 保持会销类基础分
                '会销-金融': 95,   # 保持会销类基础分
            },
            '拉新': {
                '拉新-催收': 95,   # 保持催收类基础分
                '拉新-教育': 95,   # 保持教育类基础分
                '拉新-网贷': 95,   # 保持网贷类基础分
                '拉新-展会': 95,   # 保持展会类基础分
                '拉新-医美': 95,   # 保持医美类基础分
                '拉新-pos机': 95   # 保持pos机类基础分
            },
            'default': 95
        },
        
        # 扣分规则
        'DEDUCTIONS': {
            # 营销内容扣分规则
            'MARKETING': {
                'keywords': {
                    '优惠', '特惠', '红包', '亲爱的', 'app', 'App', 'APP',
                    '限时', '特价', '折扣', '促销', '活动'
                },
                'score': -2,  # 进一步降低扣分
                'max_deduction': -10,  # 进一步降低最大扣分
                'strong_keywords': {
                    '抢购', '限量', '福利', '奖励', '领取', '权益', '抢',
                    '秒杀', '特供', '专享', '尊享', '特权'
                },
                'strong_score': -5,  # 进一步降低强关键词扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -1,  # 进一步降低通知类营销内容扣分 
                        'max_deduction': -3,  # 进一步降低最大扣分
                        'strong_score': -2    # 进一步降低强关键词扣分
                    }
                }
            },
            
            # 积分营销相关扣分规则
            'POINTS_MARKETING': {
                'keywords': {
                    '积分', '兑换', '+', '元', '领取', '使用', '会员',
                    '服务', '活动', '奖励', '赠送', '优惠券'
                },
                'score': -3,  # 进一步降低扣分
                'max_deduction': -10,  # 进一步降低最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -1,  # 进一步降低通知类扣分
                        'max_deduction': -3   # 进一步降低最大扣分
                    }
                }
            },
            
            # 积分到期相关扣分规则
            'POINTS_EXPIRY': {
                'keywords': {
                    '积分', '到期', '过期', '清零', '作废', '失效',
                    '即将到期', '即将清零', '即将作废', '清理', '清空'
                },
                'score': -5,  # 进一步降低扣分
                'max_deduction': -10,  # 进一步降低最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -2,  # 进一步降低通知类扣分
                        'max_deduction': -5  # 进一步降低最大扣分
                    }
                }
            },
            
            # 问卷调查扣分规则
            'SURVEY': {
                'keywords': {'问卷', '调查', '调研', '反馈', '评价'},
                'score': -5,  # 进一步降低扣分
                'max_deduction': -10,  # 进一步降低最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -2,  # 进一步降低通知类扣分
                        'max_deduction': -5  # 进一步降低最大扣分
                    }
                }
            },
            
            # 教育营销扣分规则
            'EDUCATION': {
                'keywords': {
                    '课程', '讲解', '培训', '上课', '教育', '考试',
                    '学习', '辅导', '补习', '讲座', '公开课'
                },
                'score': -4,  # 进一步降低扣分
                'weak_keywords': {'练习册', '作业', '习题'},
                'weak_score': -2,  # 进一步降低弱关键词扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -1,  # 进一步降低通知类扣分
                        'weak_score': -1  # 进一步降低弱关键词扣分
                    }
                }
            },
            
            # 就业招聘扣分规则
            'EMPLOYMENT': {
                'keywords': {
                    '零工', '就业', '招聘', '应聘', '求职', '面试',
                    '简历', '岗位', '职位', '入职', '工作', '薪资'
                },
                'score': -5,  # 进一步降低扣分
                'max_deduction': -15,  # 进一步降低最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -2,  # 进一步降低通知类扣分
                        'max_deduction': -5  # 进一步降低最大扣分
                    }
                }
            },
            
            # 时间相关扣分规则
            'TIME_RELATED': {
                'keywords': {
                    '截止', '限时', '倒计时', '最后', '即将',
                    '过期', '到期', '结束', '开始', '期间'
                },
                'score': -2,  # 进一步降低扣分
                'max_deduction': -5,  # 进一步降低最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -1,  # 进一步降低通知类扣分
                        'max_deduction': -2   # 进一步降低最大扣分
                    }
                }
            },
            
            # 平台相关扣分规则
            'PLATFORM': {
                'keywords': {
                    '平台', '客服', '详询', '咨询', '联系',
                    '电话', '热线', '服务', '支持', '帮助'
                },
                'score': -2,  # 进一步降低扣分
                'max_deduction': -5,  # 进一步降低最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -1,  # 进一步降低通知类扣分
                        'max_deduction': -2   # 进一步降低最大扣分
                    }
                }
            },
            
            # 微信公众号相关扣分规则
            'WECHAT': {
                'keywords': {'微信', '公众号', '关注', '小程序'},
                'score': -2,  # 进一步降低扣分
                'max_deduction': -5,  # 进一步降低最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -1,  # 进一步降低通知类扣分
                        'max_deduction': -2   # 进一步降低最大扣分
                    },
                    '会销-普通': {
                        'score': -3,  # 降低会销类扣分
                        'max_deduction': -5
                    }
                }
            },
        },
        
        # 加分规则
        'BONUSES': {
            # 物流内容加分
            'LOGISTICS': {
                'keywords': {
                    '快递', '物流', '派送', '配送', '运输',
                    '包裹', '签收', '取件', '收件', '发件'
                },
                'score': 15,  # 保持加分
                'max_bonus': 25,  # 保持最大加分
                'business_specific': {
                    '行业-物流': {
                        'score': 20,  # 保持物流类加分
                        'max_bonus': 30
                    }
                }
            },
            
            # 安全提示加分
            'SAFETY': {
                'keywords': {
                    '安全为先', '安全距离', '注意安全',
                    '安全提示', '安全提醒', '安全防范', 
                    '谨防诈骗', '谨防泄露', '谨防受骗', '谨防'
                },
                'score': 15,  # 保持加分
                'max_bonus': 25,  # 保持最大加分
                'business_specific': {
                    '行业-通知': {
                        'score': 20,  # 保持通知类加分
                        'max_bonus': 35
                    }
                }
            },
            
            # 服务通知加分
            'SERVICE_NOTICE': {
                'keywords': {
                    '温馨提示', '服务通知', '业务提醒', '温馨提醒',
                    '系统通知', '服务升级', '系统维护', '官方信息',
                    '提醒您', '通知您', '告知您', '提示您', '敬请留意',
                    '敬请关注', '敬请谅解', '请知悉', '特此通知'
                },
                'score': 15,  # 保持加分
                'max_bonus': 25,  # 保持最大加分
                'business_specific': {
                    '行业-通知': {
                        'score': 20,  # 保持通知类加分
                        'max_bonus': 30
                    }
                }
            },
            
            # 会员服务加分
            'MEMBERSHIP': {
                'keywords': {
                    '会员服务', '尊敬的会员', '尊敬的客户', '会员权益',
                    '会员专享', '会员福利', '尊敬的用户'
                },
                'score': 10,  # 保持加分
                'max_bonus': 20,  # 保持最大加分
                'business_specific': {
                    '会销-普通': {
                        'score': 15,  # 保持会销类加分
                        'max_bonus': 25
                    }
                }
            },
            
            # 通知类特征加分
            'NOTIFICATION': {
                'keywords': {
                    '通知', '提醒', '告知', '提示', '公告', 
                    '通告', '提醒您', '通知您', '告知您', '请您知悉',
                    '请注意', '请留意', '请查收', '请确认', '请及时'
                },
                'score': 10,  # 保持加分
                'max_bonus': 20,  # 保持最大加分
                'business_specific': {
                    '行业-通知': {
                        'score': 15,  # 保持通知类加分
                        'max_bonus': 25
                    }
                }
            },
            
            # 官方特征加分
            'OFFICIAL': {
                'keywords': {
                    '官方', '政府', '机构', '公司', '单位', 
                    '部门', '官网', '官方网站', '官方客服', '官方公告'
                },
                'score': 8,  # 保持加分
                'max_bonus': 15,  # 保持最大加分
                'business_specific': {
                    '行业-通知': {
                        'score': 10,  # 保持通知类加分
                        'max_bonus': 20
                    }
                }
            }
        },
        
        # 直接否决规则（零容忍）
        'ZERO_TOLERANCE': {
            'PRIVATE_NUMBER': -100,  # 出现私人号码
            'ILLEGAL_CONTENT': -100,  # 非法内容
            'GAMBLING': -100,  # 赌博内容
            'FRAUD': -100,  # 诈骗内容
        },
        
        # 及格分数线
        'PASS_SCORE': {
            '行业': {
                '行业-通知': 40,  # 进一步降低通过分数
                '行业-物流': 45,  # 进一步降低通过分数
            },
            '会销': {
                '会销-普通': 45,  # 进一步降低通过分数
                '会销-金融': 45,  # 进一步降低通过分数
            },
            '拉新': {
                '拉新-催收': 40,  # 进一步降低通过分数
                '拉新-教育': 45,  # 进一步降低通过分数
                '拉新-网贷': 45,  # 进一步降低通过分数
                '拉新-展会': 45,  # 进一步降低通过分数
                '拉新-医美': 45,  # 进一步降低通过分数
                '拉新-pos机': 45  # 进一步降低通过分数
            },
            'default': 45  # 进一步降低默认通过分数
        },
    }

    def __init__(self):
        """初始化验证器"""
        try:
            with open('surnames.json', 'r', encoding='utf-8') as f:
                self.surnames = set(json.load(f))
        except Exception as e:
            print(f"Warning: Could not load surnames.json: {e}")
            self.surnames = set()
        self.current_account_type = None
        self.score_details = {}  # 用于存储评分详情
        
        # 初始化TF-IDF向量化器
        self.vectorizer = TfidfVectorizer(
            analyzer='char',
            ngram_range=(2, 3),
            min_df=2,
            max_features=1000
        )
        
        # 初始化关键词权重
        self.keyword_weights = self._initialize_keyword_weights()
        
        # 初始化上下文分析器
        self.context_patterns = self._initialize_context_patterns()

    def _initialize_keyword_weights(self) -> Dict[str, float]:
        """初始化关键词权重"""
        weights = {
            # 通知类关键词权重
            '通知': 1.5,
            '提醒': 1.3,
            '告知': 1.2,
            '提示': 1.1,
            '客服': 0.9,  # 进一步降低客服相关词权重
            '咨询': 0.9,  # 进一步降低咨询相关词权重
            '详询': 0.9,  # 进一步降低详询相关词权重
            
            # 营销类关键词权重
            '优惠': 0.8,  # 进一步降低营销词权重
            '特惠': 0.8,
            '红包': 0.7,
            '权益': 0.8,  # 进一步降低权益相关词权重
            '会员': 0.8,  # 进一步降低会员相关词权重
            
            # 安全类关键词权重
            '谨防': 1.4,
            '安全': 1.3,
            '防范': 1.2,
            
            # 服务类关键词权重
            '服务': 1.1,  # 进一步降低服务相关词权重
            '支持': 1.0,
            '帮助': 1.0,
            
            # 时间类关键词权重
            '截止': 0.8,
            '限时': 0.7,
            '倒计时': 0.7,
            
            # 平台类关键词权重
            '平台': 0.7,
            '热线': 0.7,
            
            # 会员服务类关键词权重
            '里程': 1.1,  # 进一步降低里程相关词权重
            '积分': 1.1,  # 进一步降低积分相关词权重
            '专享': 1.1,  # 进一步降低专享相关词权重
            '尊享': 1.1,  # 进一步降低尊享相关词权重
        }
        return weights

    def _initialize_context_patterns(self) -> List[Tuple[str, float]]:
        """初始化上下文分析模式"""
        patterns = [
            # 通知类上下文模式
            (r'尊敬的.*?：', 1.5),
            (r'温馨提示.*?：', 1.4),
            (r'系统通知.*?：', 1.3),
            (r'服务通知.*?：', 1.3),
            (r'客服通知.*?：', 1.2),
            
            # 营销类上下文模式
            (r'限时特惠.*?：', 0.8),  # 进一步降低营销类权重
            (r'活动预告.*?：', 0.8),
            (r'会员福利.*?：', 0.8),
            (r'专享权益.*?：', 0.8),
            
            # 安全类上下文模式
            (r'安全提示.*?：', 1.4),
            (r'谨防诈骗.*?：', 1.4),
            (r'安全提醒.*?：', 1.3),
            
            # 会员服务类上下文模式
            (r'尊敬的会员.*?：', 1.1),  # 进一步降低会员服务权重
            (r'会员服务.*?：', 1.1),
            (r'积分通知.*?：', 1.1),
        ]
        return patterns

    def _analyze_context(self, content: str) -> float:
        """分析文本上下文"""
        context_score = 0.0
        for pattern, weight in self.context_patterns:
            if re.search(pattern, content):
                context_score += weight
        return context_score

    def _calculate_keyword_score(self, content: str) -> float:
        """计算关键词得分"""
        keyword_score = 0.0
        for keyword, weight in self.keyword_weights.items():
            if keyword in content:
                # 计算关键词出现次数
                count = content.count(keyword)
                # 根据出现次数调整权重
                adjusted_weight = weight * (1 + 0.1 * count)
                keyword_score += adjusted_weight
        return keyword_score

    def _calculate_similarity_score(self, content: str, business_type: str) -> float:
        """计算与业务类型的相似度得分"""
        # 获取业务类型的标准文本
        standard_texts = {
            '行业-通知': '系统通知 温馨提示 安全提醒 服务通知 客服咨询 客户服务 温馨提醒 官方信息 业务提醒 系统维护 服务升级',
            '行业-物流': '快递 物流 派送 配送 运输 包裹 签收 取件 收件 发件 寄件 送货 揽收 仓储 仓库 货运 提货 站点',
            '会销-普通': '会员服务 积分权益 优惠活动 专享服务 会员专享 尊享权益 会员福利 会员权益 会员专享 会员服务 积分通知',
            '会销-金融': '保险 理财 投资 基金 股票 金融服务 理财产品 投资理财 保险服务 保险产品 保险保障',
            '拉新-教育': '课程 学习 教育 培训 考试 辅导 补习 讲座 公开课 练习册 作业 习题 学习资料 教育课程',
            '拉新-网贷': '贷款 借款 信用 额度 分期 借呗 网贷 借款服务 信用贷款 分期付款 借款额度',
            '拉新-催收': '欠款 还款 催收 逾期 提醒 账单 还款提醒 欠款提醒 逾期提醒 账单提醒 还款通知'
        }
        
        if business_type not in standard_texts:
            return 0.0
            
        # 计算TF-IDF向量
        try:
            vectors = self.vectorizer.fit_transform([content, standard_texts[business_type]])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            return similarity
        except:
            return 0.0

    def _clean_content(self, content: str) -> str:
        """
        清理短信内容格式
        
        Args:
            content: 原始短信内容
            
        Returns:
            str: 清理后的内容
        """
        # 转换为小写
        content = content.lower()
        
        # 替换所有类型的空格（包括全角空格）
        content = re.sub(r'[\s\u3000]+', '', content)
        
        # 替换所有类型的破折号和连接符
        content = re.sub(r'[-‐‑‒–—―]+', '', content)
        
        # 替换所有换行符
        content = re.sub(r'[\n\r]+', '', content)
        
        # 替换所有类型的引号
        content = re.sub(r'["""''′`´]+', '', content)
        
        # 替换所有类型的括号
        content = re.sub(r'[()（）[\]【】{}「」『』]+', '', content)
        
        # 替换重复的标点符号
        content = re.sub(r'[,.。，、!！?？~～]+', lambda m: m.group()[0], content)
        
        # 替换装饰性字符
        content = re.sub(r'[★☆✦✧✩✪✫✬✭✮✯✰⭐️]+', '⭐', content)
        
        return content

    def validate_business(self, business_type: str, content: str, signature: str, account_type: str = None) -> Tuple[bool, str]:
        """
        使用评分制验证业务类型
        """
        self.current_account_type = account_type
        
        # 清理内容和签名格式
        content = self._clean_content(content)
        signature = self._clean_content(signature)
        
        # 重置评分详情
        self.score_details = {
            'base_score': self.SCORE_RULES['BASE_SCORE']['default'],
            'deductions': [],
            'bonuses': [],
            'final_score': self.SCORE_RULES['BASE_SCORE']['default']
        }

        # 获取业务类别
        business_category = self._get_business_category(business_type)
        if not business_category:
            return False, "未知的业务类型"

        # 根据业务类别进行评分
        if business_category == "行业":
            return self._score_industry(business_type, content, signature)
        elif business_category == "会销":
            return self._score_marketing(business_type, content, signature)
        elif business_category == "拉新" and business_type == "拉新-催收":
            return self._score_collection(content)

        return True, "审核通过"

    def _score_industry(self, business_type: str, content: str, signature: str) -> Tuple[bool, str]:
        """使用增强的评分系统验证行业类短信"""
        # 基础分数
        base_score = self.SCORE_RULES['BASE_SCORE']['行业'][business_type]
        
        # 计算上下文得分
        context_score = self._analyze_context(content)
        
        # 计算关键词得分
        keyword_score = self._calculate_keyword_score(content)
        
        # 计算相似度得分
        similarity_score = self._calculate_similarity_score(content, business_type)
        
        # 综合评分
        final_score = base_score + (context_score * 5) + (keyword_score * 10) + (similarity_score * 20)
        
        # 应用业务特定规则
        if business_type == "行业-通知":
            # 签名验证
            if any(keyword in signature for keyword in self.STORE_KEYWORDS):
                final_score -= 10
                
            # 验证直播相关内容
            if any(keyword in content for keyword in self.LIVE_STREAMING_KEYWORDS):
                final_score -= 10
                
            # 检查公众号关键词
            wechat_matches = sum(1 for keyword in self.WECHAT_KEYWORDS if keyword in content)
            if wechat_matches >= 2:
                final_score -= 5
            elif wechat_matches == 1:
                final_score -= 2
                
        elif business_type == "行业-物流":
            if not any(keyword in content for keyword in self.LOGISTICS_KEYWORDS):
                final_score -= 30
                
        # 零容忍检查
        if self._contains_private_number(content):
            final_score += self.SCORE_RULES['ZERO_TOLERANCE']['PRIVATE_NUMBER']
            
        # 更新评分详情
        self.score_details['final_score'] = final_score
        self.score_details['context_score'] = context_score
        self.score_details['keyword_score'] = keyword_score
        self.score_details['similarity_score'] = similarity_score
        
        # 判断是否通过
        passed = final_score >= self.SCORE_RULES['PASS_SCORE']['行业'][business_type]
        if passed:
            reasons = [
                f"基础分: {base_score}",
                f"上下文得分: {context_score:.2f}",
                f"关键词得分: {keyword_score:.2f}",
                f"相似度得分: {similarity_score:.2f}",
                f"最终得分: {final_score:.2f}"
            ]
            return True, f"审核通过 (原因: {', '.join(reasons)})"
        else:
            return False, f"审核不通过 (总分: {final_score:.2f})"

    def _score_marketing(self, business_type: str, content: str, signature: str) -> Tuple[bool, str]:
        """使用增强的评分系统验证会销类短信"""
        # 基础分数
        base_score = self.SCORE_RULES['BASE_SCORE']['会销'][business_type]
        
        # 计算上下文得分
        context_score = self._analyze_context(content)
        
        # 计算关键词得分
        keyword_score = self._calculate_keyword_score(content)
        
        # 计算相似度得分
        similarity_score = self._calculate_similarity_score(content, business_type)
        
        # 综合评分
        final_score = base_score + (context_score * 5) + (keyword_score * 10) + (similarity_score * 20)
        
        # 检查私人号码
        if self._contains_private_number(content):
            final_score += self.SCORE_RULES['ZERO_TOLERANCE']['PRIVATE_NUMBER']
            return False, "会销类短信不允许包含私人号码"
            
        # 会销-普通特殊验证
        if business_type == "会销-普通":
            # 检查活动类特征词
            activity_keywords = {'活动', '新品', '新春', '活动预告', '会员福利', 
                               '权益提醒', '专享', '会员专享', '限时', '尊享'}
            activity_matches = sum(1 for keyword in activity_keywords if keyword in content)
            if activity_matches > 0:
                final_score += 5 * activity_matches
                
            # 检查会员服务相关词
            membership_keywords = {'尊敬的会员', '尊敬的客户', '尊敬的用户'}
            membership_matches = sum(1 for keyword in membership_keywords if keyword in content)
            if membership_matches > 0:
                final_score += 5 * membership_matches
                
            # 检查微信公众号关键词
            wechat_matches = sum(1 for keyword in self.WECHAT_KEYWORDS if keyword in content)
            if wechat_matches >= 2:
                final_score -= 20
            elif wechat_matches == 1:
                final_score -= 10
                
        # 更新评分详情
        self.score_details['final_score'] = final_score
        self.score_details['context_score'] = context_score
        self.score_details['keyword_score'] = keyword_score
        self.score_details['similarity_score'] = similarity_score
        
        # 判断是否通过
        passed = final_score >= self.SCORE_RULES['PASS_SCORE']['会销'][business_type]
        if passed:
            reasons = [
                f"基础分: {base_score}",
                f"上下文得分: {context_score:.2f}",
                f"关键词得分: {keyword_score:.2f}",
                f"相似度得分: {similarity_score:.2f}",
                f"最终得分: {final_score:.2f}"
            ]
            return True, f"审核通过 (原因: {', '.join(reasons)})"
        else:
            return False, f"审核不通过 (总分: {final_score:.2f})"

    def _score_collection(self, content: str) -> Tuple[bool, str]:
        """使用增强的评分系统验证催收类短信"""
        # 基础分数
        base_score = self.SCORE_RULES['BASE_SCORE']['拉新']['拉新-催收']
        
        # 计算上下文得分
        context_score = self._analyze_context(content)
        
        # 计算关键词得分
        keyword_score = self._calculate_keyword_score(content)
        
        # 计算相似度得分
        similarity_score = self._calculate_similarity_score(content, "拉新-催收")
        
        # 综合评分
        final_score = base_score + (context_score * 5) + (keyword_score * 10) + (similarity_score * 20)
        
        # 检查私人号码
        if self._contains_private_number(content):
            final_score += self.SCORE_RULES['ZERO_TOLERANCE']['PRIVATE_NUMBER']
            return False, "催收类短信不允许包含私人号码"
            
        # 检查威胁性语言
        threat_keywords = {'起诉', '法院', '律师', '强制执行', '拘留', '坐牢'}
        threat_matches = sum(1 for keyword in threat_keywords if keyword in content)
        if threat_matches > 0:
            final_score -= 10 * threat_matches
            
        # 检查骚扰性语言
        harassment_keywords = {'骚扰', '轰炸', '轰炸机', '轰炸你', '轰炸你全家'}
        harassment_matches = sum(1 for keyword in harassment_keywords if keyword in content)
        if harassment_matches > 0:
            final_score -= 15 * harassment_matches
            
        # 更新评分详情
        self.score_details['final_score'] = final_score
        self.score_details['context_score'] = context_score
        self.score_details['keyword_score'] = keyword_score
        self.score_details['similarity_score'] = similarity_score
        
        # 判断是否通过
        passed = final_score >= self.SCORE_RULES['PASS_SCORE']['拉新']['拉新-催收']
        if passed:
            reasons = [
                f"基础分: {base_score}",
                f"上下文得分: {context_score:.2f}",
                f"关键词得分: {keyword_score:.2f}",
                f"相似度得分: {similarity_score:.2f}",
                f"最终得分: {final_score:.2f}"
            ]
            return True, f"审核通过 (原因: {', '.join(reasons)})"
        else:
            return False, f"审核不通过 (总分: {final_score:.2f})"

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

    def _get_business_category(self, business_type: str) -> str:
        """获取业务类别"""
        for category, types in self.BUSINESS_TYPE_LIBRARY.items():
            if business_type in types:
                return category
        return ""

def validate_business(business_type: str, content: str, signature: str, account_type: str = None) -> Tuple[bool, str]:
    """
    验证业务类型是否符合规则的便捷函数
    
    Args:
        business_type: 客户业务类型
        content: 短信内容
        signature: 短信签名
        account_type: 客户类型
        
    Returns:
        (是否通过, 原因说明)
    """
    validator = BusinessValidator()
    return validator.validate_business(business_type, content, signature, account_type)

# 定义有效的客户类型
客户类型 = ["云平台", "直客", "类直客", "渠道"]

def validate_account_type(account_type: str) -> Tuple[bool, str]:
    """
    验证客户类型
    
    Args:
        account_type: 客户类型
        
    Returns:
        Tuple[bool, str]: (是否通过验证, 验证结果说明)
    """
    # 检查是否为有效的客户类型
    if account_type not in 客户类型:
        return False, f"无效的客户类型，有效类型为: {', '.join(客户类型)}"
    
    # 直客类型直接放行
    if account_type == "直客":
        return True, "直客类型直接通过"
        
    return True, "客户类型有效"

