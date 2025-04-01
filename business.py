import re  
import cpca
import pandas as pd
import math
from typing import Tuple, Dict, List, Set
import json
import jieba.posseg as pseg




class BusinessValidator:
    # 业务类型库
    BUSINESS_TYPE_LIBRARY: Dict[str, List[str]] = {
        "行业": ["行业-通知", "行业-物流"],
        "会销": ["会销-普通", "会销-金融"],
        "拉新": ["拉新-催收", "拉新-教育", "拉新-网贷", "拉新-展会", "拉新-医美", "拉新-pos机"]
    }

    # 关键词常量定义
    STORE_KEYWORDS: Set[str] = {"旗舰店", "专卖店"}
    WECHAT_KEYWORDS: Set[str] = {"微信", "公众号", "关注", "小程序"}
    NAME_WHITELIST: Set[str] = {"您好", "本人"}
    LIVE_STREAMING_KEYWORDS: Set[str] = {"直播", "带货", "主播", "观看直播", "直播间", "连麦"}
    # 添加中性签名列表
    NEUTRAL_SIGNATURES: Set[str] = {"温馨提示", "恭喜发财", "市燃气办"}


    # 定义评分规则
    SCORE_RULES = {
        # 基础分数
        'BASE_SCORE': {
            '行业': {
                '行业-通知': 100,  # 降低通知类基础分
                '行业-物流': 100,   # 保持物流类基础分
            },
            '会销': {
                '会销-普通': 130,   # 降低会销类基础分
                '会销-金融': 100,   # 降低会销类基础分
            },
            '拉新': {
                '拉新-催收': 100,   # 降低催收类基础分
                '拉新-教育': 100,   # 降低教育类基础分
                '拉新-网贷': 100,   # 降低网贷类基础分
                '拉新-展会': 100,   # 降低展会类基础分
                '拉新-医美': 100,   # 降低医美类基础分
                '拉新-pos机': 100   # 降低pos机类基础分
            },
            'default': 100
        },
        
        # 扣分规则
        'DEDUCTIONS': {
            # 地址相关扣分规则
            'ADDRESS': {
                'score': -5,  # 每个地址特征扣3分
                'max_deduction': -5,  # 最大扣分10分
                'business_specific': {
                    '行业-通知': {
                        'score': -5,  # 通知类每个地址特征扣2分
                        'max_deduction': -5  # 通知类最大扣分6分
                    },
                    '会销-普通': {
                        'score': -5,  # 会销普通类每个地址特征扣2分
                        'max_deduction': -5  # 会销普通类最大扣分6分
                    }
                }
            },
            
            # 营销内容扣分规则
            'MARKETING': {
                'keywords': {
                    '优惠', '特惠', '红包', '亲爱的', 'app', 'App', 'APP',
                    '特价', '折扣', '促销', '活动'
                },
                'score': -10,  # 优化：减轻营销关键词扣分（从-20改为-10）
                'max_deduction': -20,  # 优化：减轻最大扣分（从-40改为-20）
                'strong_keywords': {
                    '抢购', '限量', '福利', '奖励', '领取', '权益', '抢',
                    '秒杀', '特供', '专享', '尊享', '特权', '免费', '报名', '超值', '多赚','详情'
                    '参加', '参与', '领取', '抢', '限时', '倒计时' ,'缴费', '尊敬' ,'咨询', '电话', '详讯' ,'预约' ,'消费' ,'惊喜'
                },
                'strong_score': -20,  # 增加强关键词扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -15,  # 优化：减轻通知类营销内容扣分（从-30改为-15）
                        'max_deduction': -30,  # 优化：减轻最大扣分（从-60改为-30）
                        'strong_score': -15    # 优化：减轻强关键词扣分（从-30改为-15）
                    },
                    '会销-普通': {
                        'score': -5,  # 优化：针对会销普通大幅减轻营销扣分（比默认-10更低）
                        'max_deduction': -10,  # 优化：针对会销普通减轻最大扣分
                        'strong_score': -5     # 优化：针对会销普通大幅减轻强关键词扣分
                    }
                }
            },
            
            # 积分营销相关扣分规则
            'POINTS_MARKETING': {
                'keywords': {
                    '积分', '兑换', '+', '元', '领取', '使用', '会员',
                    '服务', '活动', '奖励', '赠送', '优惠券', '里程'
                },
                'score': -10,  # 优化：减轻积分营销扣分（从-20改为-10）
                'max_deduction': -30,  # 优化：减轻最大扣分（从-60改为-30）
                'business_specific': {
                    '行业-通知': {
                        'score': -15,  # 优化：减轻通知类扣分（从-30改为-15）
                        'max_deduction': -30   # 优化：减轻最大扣分（从-60改为-30）
                    },
                    '会销-普通': {
                        'score': -5,  # 优化：针对会销普通大幅减轻积分营销扣分
                        'max_deduction': -15   # 优化：针对会销普通减轻最大扣分
                    }
                }
            },
            
            # 积分到期相关扣分规则
            'POINTS_EXPIRY': {
                'keywords': {
                    '积分', '到期', '过期', '清零', '作废', '失效',
                    '即将到期', '即将清零', '即将作废', '清理', '清空' ,'逾期'
                },
                'score': -10,  # 优化：减轻积分到期扣分（从-20改为-10）
                'max_deduction': -20,  # 优化：减轻最大扣分（从-30改为-20）
                'business_specific': {
                    '行业-通知': {
                        'score': -15,  # 优化：减轻通知类扣分（从-30改为-15）
                        'max_deduction': -30  # 优化：减轻最大扣分（从-60改为-30）
                    },
                    '会销-普通': {
                        'score': -5,  # 优化：针对会销普通大幅减轻积分到期扣分
                        'max_deduction': -10  # 优化：针对会销普通减轻最大扣分
                    }
                }
            },
            
            # 招聘相关扣分规则
            'RECRUITMENT': {
                'keywords': {
                    '招聘', '应聘', '求职', '面试', '简历', '岗位', '职位',
                    '用工', '聘用', '招工', '用人', '入职', '应届生',
                    '社招', '校招', '人才', '求贤', '职场'
                },
                'score': -10,  # 增加扣分
                'max_deduction': -15,  # 增加最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -10,  # 增加通知类扣分
                        'max_deduction': -20  # 增加最大扣分
                    }
                }
            },

            # 会议相关扣分规则
            'MEETING': {
                'keywords': {
                    '参会', '会议', '论坛', '峰会', '研讨会', '座谈会',
                    '年会', '发布会', '见面会', '交流会', '答谢会', '分享会', '学会'
                },
                'score': -10,  # 增加扣分
                'max_deduction': -30,  # 增加最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -15,  # 增加通知类扣分
                        'max_deduction': -30  # 增加最大扣分
                    }
                }
            },

            # 交友相关扣分规则
            'DATING': {
                'keywords': {
                    '交友', '相亲', '留言'
                },
                'score': -15,  # 增加扣分
                'max_deduction': -30,  # 增加最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -15,  # 增加通知类扣分
                        'max_deduction': -30  # 增加最大扣分
                    }
                }
            },

            # 征兵相关扣分规则
            'MILITARY': {
                'keywords': {
                    '征兵', '入伍'
                },
                'score': -15,  # 增加扣分
                'max_deduction': -30,  # 增加最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -15,  # 增加通知类扣分
                        'max_deduction': -30  # 增加最大扣分
                    }
                }
            },
            
            # 问卷调查扣分规则
            'SURVEY': {
                'keywords': {'问卷', '调查', '调研', '反馈', '评价'},
                'score': -10,  # 增加扣分
                'max_deduction': -30,  # 增加最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -15,  # 增加通知类扣分
                        'max_deduction': -30  # 增加最大扣分
                    }
                }
            },
            
            # 教育营销扣分规则
            'EDUCATION': {
                'keywords': {
                    '课程', '讲解', '培训', '上课', '教育', '考试',
                    '学习', '辅导', '补习', '讲座', '公开课', '作业',
                    '练习册', '习题', '老师', '干货'
                },
                'score': -10,  # 增加扣分
                'max_deduction': -30,  # 增加最大扣分
                'weak_keywords': {'练习册', '作业', '习题', '老师', '干货'},
                'weak_score': -30,  # 增加弱关键词扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -15,  # 增加通知类扣分
                        'weak_score': -30,  # 增加弱关键词扣分
                        'max_deduction': -30  # 增加最大扣分
                    }
                }
            },
            
            # 就业招聘扣分规则
            'EMPLOYMENT': {
                'keywords': {
                    '零工', '就业', '招聘', '应聘', '求职', '面试',
                    '简历', '岗位', '职位', '入职', '工作', '薪资',
                    '人才', '求贤', '职场'
                },
                'score': -10,  # 增加扣分
                'max_deduction': -20,  # 增加最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -15,  # 增加通知类扣分
                        'max_deduction': -30  # 增加最大扣分
                    }
                }
            },
            
            # 时间相关扣分规则，未使用
            'TIME_RELATED': {
                'keywords': {
                    '截止', '限时', '倒计时', '最后', '即将',
                    '过期', '到期', '结束', '开始'
                    
                },
                'score': -10,  # 增加扣分
                'max_deduction': -20,  # 增加最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -15,  # 增加通知类扣分
                        'max_deduction': -30   # 增加最大扣分
                    }
                }
            },
            
            # 平台相关扣分规则
            'PLATFORM': {
                'keywords': {
                    '平台', '客服', '详询', '咨询', '联系',
                    '电话', '热线', '服务', '支持', '帮助',
                    '微信', '公众号', '小程序', 'APP', 'app',
                    '链接', '网址', '网站', '登录', '注册'
                },
                'score': -5,  # 优化：减轻平台关键词扣分（从-10改为-5）
                'max_deduction': -15,  # 优化：减轻最大扣分（从-30改为-15）
                'business_specific': {
                    '行业-通知': {
                        'score': -10,  # 优化：减轻通知类扣分（从-15改为-10）
                        'max_deduction': -20   # 优化：减轻最大扣分（从-30改为-20）
                    },
                    '会销-普通': {
                        'score': -5,  # 优化：减轻会销普通类平台关键词扣分（从-10改为-5）
                        'max_deduction': -15  # 优化：减轻最大扣分（从-30改为-15）
                    }
                }
            },
            
            # 固定电话扣分规则
            'FIXED_PHONE': {
                'score': -30,  # 从-50略微降低到-45
                'max_deduction': -50,
                'business_specific': {
                    '会销-普通': {
                        'score': -30,  # 略微降低
                        'max_deduction': -30
                    },
                    '行业-通知': {
                        'score': -45,  # 略微降低
                        'max_deduction': -50
                    },
                    '拉新-催收': {
                        'score': -45,  # 略微降低
                        'max_deduction': -50
                    }
                }
            },
            
            # 微信公众号相关扣分规则
            'WECHAT': {
                'keywords': {'微信', '公众号', '关注', '小程序', 'APP', 'app'},
                'score': -10,  # 增加扣分
                'max_deduction': -30,  # 增加最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -15,  # 增加通知类扣分
                        'max_deduction': -30   # 增加最大扣分
                    },
                    '会销-普通': {
                        'score': -15,  # 增加会销类扣分
                        'max_deduction': -30
                    }
                }
            },

            # 链接相关扣分规则
            'LINK': {
                'score': -10,  # 每个链接扣2分
                'max_deduction': -20,  # 最大扣分6分
                'business_specific': {
                    '行业-通知': {
                        'score': -20,  # 通知类每个链接扣1分
                        'max_deduction': -40  # 通知类最大扣分3分
                    },
                    '会销-普通': {
                        'score': -10,  # 会销普通类每个链接扣1分
                        'max_deduction': -20  # 会销普通类最大扣分3分
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
                'score': 10,
                'max_bonus': 20,
                'business_specific': {
                    '行业-物流': {
                        'score': 10,
                        'max_bonus': 20
                    }
                }
            },
            
            # 特定签名加分
            'SPECIAL_SIGNATURE': {
                'signatures': {'饿了么'},
                'score': 20,
                'max_bonus': 20
            },
            
            # 特定关键词签名加分
            'SPECIAL_KEYWORDS': {
                'keywords': {'政府', '机关', '电力', '部委', '公安', '法院', '检察院'},
                'score': 20,
                'max_bonus': 20
            }
        },
        
        # 直接否决规则（零容忍）
        'ZERO_TOLERANCE': {
            'PRIVATE_NUMBER': -100,  # 出现私人号码
        },
        
        # 及格分数线
        'PASS_SCORE': {
            '行业': {
                '行业-通知': 60,  # 提高通过分数
                '行业-物流': 60,  # 提高通过分数
            },
            '会销': {
                '会销-普通': 60,  # 提高通过分数
                '会销-金融': 60,  # 提高通过分数
            },
            '拉新': {
                '拉新-催收': 60,  # 提高通过分数
                '拉新-教育': 60,  # 提高通过分数
                '拉新-网贷': 60,  # 提高通过分数
                '拉新-展会': 60,  # 提高通过分数
                '拉新-医美': 60,  # 提高通过分数
                '拉新-pos机': 60  # 提高通过分数
            },
            'default': 60  # 提高默认通过分数
        },
    }

    def __init__(self):
        """
        初始化验证器，包括：
        1. 加载姓氏数据
        """
        try:
            with open('surnames.json', 'r', encoding='utf-8') as f:
                self.surnames = set(json.load(f))
        except Exception as e:
            print(f"Warning: Could not load surnames.json: {e}")
            self.surnames = set()
        self.current_account_type = None
        self.score_details = {}  # 用于存储评分详情
    

    def _clean_content(self, content: str) -> str:
        """
        清理文本内容，去除无关字符和格式化。这是所有文本处理的第一步。
        
        Args:
            content: 原始文本
            
        Returns:
            str: 清理后的文本
        """
        if not content:
            return ""
        
        # 1. 基础清理
        content = content.lower()  # 转换为小写
        
        # 2. 空白字符处理
        content = re.sub(r'[\s\u3000]+', '', content)  # 替换所有类型的空格
        content = re.sub(r'[\n\r]+', '', content)      # 替换所有换行符
        
        # 3. 标点符号处理
        content = re.sub(r'[-‐‑‒–—―]+', '', content)   # 替换所有类型的破折号
        content = re.sub(r'["""''′`´]+', '', content)  # 替换所有类型的引号
        content = re.sub(r'[()（）[\]【】{}「」『』]+', '', content)  # 替换所有类型的括号
        
        # 4. 重复标点处理
        content = re.sub(r'[,.。，、!！?？~～]+', lambda m: m.group()[0], content)
        
        # 5. 特殊字符处理
        content = re.sub(r'[★☆✦✧✩✪✫✬✭✮✯✰⭐️]+', '⭐', content)  # 统一星号表示
        
        return content

    def _validate_business_internal(self, business_type: str, cleaned_content: str, cleaned_signature: str, account_type: str = None) -> Tuple[bool, str]:
        """
        内部业务验证实现，使用评分制验证业务类型
        
        Args:
            business_type: 业务类型
            cleaned_content: 已清理的短信内容
            cleaned_signature: 已清理的短信签名
            account_type: 客户类型（可选）
            
        Returns:
            Tuple[bool, str]: (是否通过验证, 验证结果说明)
        """
        self.current_account_type = account_type
        
        # 初始化评分详情
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
            return self._score_industry(business_type, cleaned_content, cleaned_signature)
        elif business_category == "会销":
            return self._score_marketing(business_type, cleaned_content, cleaned_signature)
        elif business_category == "拉新" and business_type == "拉新-催收":
            return self._score_collection(cleaned_content)

        # 应用特定签名和关键词加分
        final_score = self.score_details['final_score']
        
        # 应用特定签名加分
        if cleaned_signature in self.SCORE_RULES['BONUSES']['SPECIAL_SIGNATURE']['signatures']:
            bonus = self.SCORE_RULES['BONUSES']['SPECIAL_SIGNATURE']['score']
            final_score += bonus
            self.score_details['bonuses'].append(f"特定签名加分: +{bonus}")
        
        # 应用特定关键词签名加分
        special_keywords = self.SCORE_RULES['BONUSES']['SPECIAL_KEYWORDS']['keywords']
        if any(keyword in cleaned_signature for keyword in special_keywords):
            bonus = self.SCORE_RULES['BONUSES']['SPECIAL_KEYWORDS']['score']
            final_score += bonus
            self.score_details['bonuses'].append(f"特定关键词签名加分: +{bonus}")
        
        # 更新最终得分
        self.score_details['final_score'] = final_score
        
        # 判断是否通过
        passed = final_score >= self.SCORE_RULES['PASS_SCORE']['default']
        if passed:
            reasons = [
                f"基础分: {self.score_details['base_score']}",
                f"最终得分: {final_score:.2f}"
            ]
            return True, f"审核通过 (原因: {', '.join(reasons)})"
        else:
            return False, f"审核不通过 (总分: {final_score:.2f})"

    def _contains_address(self, text: str) -> Tuple[bool, int, List[str]]:
        """
        使用cpca库检测文本中是否包含详细地址
        
        Args:
            text: 待检查的文本
            
        Returns:
            Tuple[bool, int, List[str]]: (是否包含地址, 地址特征数量, 检测到的地址列表)
        """
        # 使用cpca进行地址识别
        df = pd.DataFrame([text], columns=['地址'])
        df_with_addr = cpca.transform(df['地址'])
        
        # 只在地址列有内容时才判定为存在地址
        has_address = not df_with_addr['地址'].isna().all() and df_with_addr['地址'][0]
        
        # 提取检测到的地址
        detected_addresses = []
        if has_address:
            # 构建完整地址
            for i in range(len(df_with_addr)):
                addr_parts = []
                if not pd.isna(df_with_addr['省'][i]):
                    addr_parts.append(df_with_addr['省'][i])
                if not pd.isna(df_with_addr['市'][i]):
                    addr_parts.append(df_with_addr['市'][i])
                if not pd.isna(df_with_addr['区'][i]):
                    addr_parts.append(df_with_addr['区'][i])
                if not pd.isna(df_with_addr['地址'][i]):
                    addr_parts.append(df_with_addr['地址'][i])
                
                if addr_parts:
                    detected_addresses.append(''.join(addr_parts))
        
        # 计算地址特征分数
        addr_score = 0
        
        # 基于cpca检测结果
        if has_address:
            # 基础分数
            addr_score += 1
            
            # 检查地址完整度，每有一个组成部分增加1分
            if not df_with_addr['省'].isna().all():
                addr_score += 1
            if not df_with_addr['市'].isna().all():
                addr_score += 1
            if not df_with_addr['区'].isna().all():
                addr_score += 1
            if not df_with_addr['地址'].isna().all() and df_with_addr['地址'][0]:
                addr_score += 1
        
        return has_address, addr_score, detected_addresses

    def _score_industry(self, business_type: str, cleaned_content: str, cleaned_signature: str) -> Tuple[bool, str]:
        """
        行业类短信的评分实现
        
        Args:
            business_type: 业务类型
            cleaned_content: 已清理的短信内容
            cleaned_signature: 已清理的短信签名
            
        Returns:
            Tuple[bool, str]: (是否通过验证, 验证结果说明)
        """
        # 基础分数
        base_score = self.SCORE_RULES['BASE_SCORE']['行业'][business_type]
        
        # 收集扣分项而非直接累加
        deductions = []
        deduction_details = []
        
        # 检查私人号码
        if self._contains_private_number(cleaned_content):
            return False, "行业类短信不允许包含私人号码"

        # 检查固定电话
        has_fixed_phone, fixed_phone_count = self._contains_fixed_phone(cleaned_content)
        if has_fixed_phone:
            # 检查是否与其他规则共现
            other_rules_present = False
            
            # 检查是否与积分营销共现
            points_marketing_matches = sum(1 for keyword in self.SCORE_RULES['DEDUCTIONS']['POINTS_MARKETING']['keywords'] if keyword in cleaned_content)
            if points_marketing_matches > 0:
                other_rules_present = True
                
            # 检查是否与平台关键词共现
            platform_matches = sum(1 for keyword in self.SCORE_RULES['DEDUCTIONS']['PLATFORM']['keywords'] if keyword in cleaned_content)
            if platform_matches > 0:
                other_rules_present = True
                
            # 检查是否与强营销关键词共现
            strong_marketing_matches = sum(1 for keyword in self.SCORE_RULES['DEDUCTIONS']['MARKETING']['strong_keywords'] if keyword in cleaned_content)
            if strong_marketing_matches > 0:
                other_rules_present = True
            
            if business_type == "行业-通知" and other_rules_present:
                # 如果是行业-通知类型且与其他规则共现，降低扣分权重
                deduction = min(
                    -25 * fixed_phone_count,  # 从-35降低到-25
                    -50  # 最大扣分从-70降低到-50
                )
            elif business_type == "行业-通知":
                # 如果是行业-通知类型但没有与其他规则共现，适度降低扣分
                deduction = min(
                    -30 * fixed_phone_count,  # 从-35降低到-30
                    -60  # 最大扣分从-70降低到-60
                )
            else:
                # 其他业务类型保持原有扣分逻辑
                deduction = min(
                    self.SCORE_RULES['DEDUCTIONS']['FIXED_PHONE']['business_specific']['行业-通知']['score'] * fixed_phone_count,
                    self.SCORE_RULES['DEDUCTIONS']['FIXED_PHONE']['business_specific']['行业-通知']['max_deduction']
                )
            deductions.append(deduction)
            deduction_details.append(f"固定电话扣分: {deduction} (数量: {fixed_phone_count})")
            
        # 检测链接    
        has_link, link_count = self._contains_link(cleaned_content)
        if has_link:
            if business_type == "行业-通知":
                # 增加链接扣分力度
                deduction = min(
                    -25 * link_count,  # 从-20增加到-25
                    -50  # 最大扣分从-40增加到-50
                )
            else:
                deduction = min(
                    self.SCORE_RULES['DEDUCTIONS']['LINK']['business_specific']['行业-通知']['score'] * link_count,
                    self.SCORE_RULES['DEDUCTIONS']['LINK']['business_specific']['行业-通知']['max_deduction']
                )
            deductions.append(deduction)
            deduction_details.append(f"链接扣分: {deduction} (数量: {link_count})")

        # 检查营销关键词
        marketing_matches = sum(1 for keyword in self.SCORE_RULES['DEDUCTIONS']['MARKETING']['keywords'] if keyword in cleaned_content)
        if marketing_matches > 0 and business_type == "行业-通知":
            # 针对行业-通知类型降低营销关键词扣分
            deduction = -10 * marketing_matches  # 从-15降低到-10
            deduction = max(deduction, -20)  # 最大扣分限制从-30降低到-20
            deductions.append(deduction)
            deduction_details.append(f"营销关键词扣分: {deduction} (匹配数量: {marketing_matches})")
        elif marketing_matches > 0:
            deduction = self.SCORE_RULES['DEDUCTIONS']['MARKETING']['business_specific']['行业-通知']['score'] * marketing_matches
            deduction = max(deduction, self.SCORE_RULES['DEDUCTIONS']['MARKETING']['business_specific']['行业-通知']['max_deduction'])
            deductions.append(deduction)
            deduction_details.append(f"营销关键词扣分: {deduction} (匹配数量: {marketing_matches})")
            
        # 检查强营销关键词
        strong_marketing_matches = sum(1 for keyword in self.SCORE_RULES['DEDUCTIONS']['MARKETING']['strong_keywords'] if keyword in cleaned_content)
        if strong_marketing_matches > 0 and business_type == "行业-通知":
            # 针对行业-通知类型增加强营销关键词扣分
            deduction = -15 * strong_marketing_matches  # 从-10增加到-15
            deduction = max(deduction, -30)  # 最大扣分限制从-20增加到-30
            deductions.append(deduction)
            deduction_details.append(f"强营销关键词扣分: {deduction} (匹配数量: {strong_marketing_matches})")
        elif strong_marketing_matches > 0:
            deduction = self.SCORE_RULES['DEDUCTIONS']['MARKETING']['business_specific']['行业-通知']['strong_score'] * strong_marketing_matches
            deduction = max(deduction, self.SCORE_RULES['DEDUCTIONS']['MARKETING']['business_specific']['行业-通知']['max_deduction'])
            deductions.append(deduction)
            deduction_details.append(f"强营销关键词扣分: {deduction} (匹配数量: {strong_marketing_matches})")
            
        # 检查积分营销关键词
        points_marketing_matches = sum(1 for keyword in self.SCORE_RULES['DEDUCTIONS']['POINTS_MARKETING']['keywords'] if keyword in cleaned_content)
        if points_marketing_matches > 0 and business_type == "行业-通知":
            # 针对行业-通知类型增加积分营销扣分
            deduction = -15 * points_marketing_matches  # 从-10增加到-15
            deduction = max(deduction, -30)  # 最大扣分限制从-20增加到-30
            deductions.append(deduction)
            deduction_details.append(f"积分营销扣分: {deduction} (匹配数量: {points_marketing_matches})")
        elif points_marketing_matches > 0:
            deduction = self.SCORE_RULES['DEDUCTIONS']['POINTS_MARKETING']['business_specific']['行业-通知']['score'] * points_marketing_matches
            deduction = max(deduction, self.SCORE_RULES['DEDUCTIONS']['POINTS_MARKETING']['business_specific']['行业-通知']['max_deduction'])
            deductions.append(deduction)
            deduction_details.append(f"积分营销扣分: {deduction} (匹配数量: {points_marketing_matches})")
            
        # 检查积分到期关键词
        points_expiry_matches = sum(1 for keyword in self.SCORE_RULES['DEDUCTIONS']['POINTS_EXPIRY']['keywords'] if keyword in cleaned_content)
        if points_expiry_matches > 0:
            deduction = self.SCORE_RULES['DEDUCTIONS']['POINTS_EXPIRY']['business_specific']['行业-通知']['score'] * points_expiry_matches
            deduction = max(deduction, self.SCORE_RULES['DEDUCTIONS']['POINTS_EXPIRY']['business_specific']['行业-通知']['max_deduction'])
            deductions.append(deduction)
            deduction_details.append(f"积分到期扣分: {deduction} (匹配数量: {points_expiry_matches})")
        
        # 检查平台关键词
        platform_matches = sum(1 for keyword in self.SCORE_RULES['DEDUCTIONS']['PLATFORM']['keywords'] if keyword in cleaned_content)
        if platform_matches > 0:
            deduction = self.SCORE_RULES['DEDUCTIONS']['PLATFORM']['business_specific']['行业-通知']['score'] * platform_matches
            deduction = max(deduction, self.SCORE_RULES['DEDUCTIONS']['PLATFORM']['business_specific']['行业-通知']['max_deduction'])
            deductions.append(deduction)
            deduction_details.append(f"平台关键词扣分: {deduction} (匹配数量: {platform_matches})")
        
        # 检查就业招聘关键词
        employment_matches = sum(1 for keyword in self.SCORE_RULES['DEDUCTIONS']['EMPLOYMENT']['keywords'] if keyword in cleaned_content)
        if employment_matches > 0:
            deduction = min(
                self.SCORE_RULES['DEDUCTIONS']['EMPLOYMENT']['score'] * employment_matches,
                self.SCORE_RULES['DEDUCTIONS']['EMPLOYMENT']['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"就业招聘关键词扣分: {deduction} (匹配数量: {employment_matches})")
        
        # 检查问卷调查关键词
        survey_matches = sum(1 for keyword in self.SCORE_RULES['DEDUCTIONS']['SURVEY']['keywords'] if keyword in cleaned_content)
        if survey_matches > 0:
            # 使用业务特定规则
            if business_type in self.SCORE_RULES['DEDUCTIONS']['SURVEY']['business_specific']:
                specific_rule = self.SCORE_RULES['DEDUCTIONS']['SURVEY']['business_specific'][business_type]
                deduction = min(
                    specific_rule['score'] * survey_matches,
                    specific_rule['max_deduction']
                )
            else:
                deduction = min(
                    self.SCORE_RULES['DEDUCTIONS']['SURVEY']['score'] * survey_matches,
                    self.SCORE_RULES['DEDUCTIONS']['SURVEY']['max_deduction']
                )
            deductions.append(deduction)
            deduction_details.append(f"问卷调查关键词扣分: {deduction} (匹配数量: {survey_matches})")
        
        # 应用业务特定规则
        if business_type == "行业-通知":
                
            # 验证直播相关内容
            if any(keyword in cleaned_content for keyword in self.LIVE_STREAMING_KEYWORDS):
                deduction = -10
                deductions.append(deduction)
                deduction_details.append(f"直播相关内容扣分: {deduction}")
                
            # 检查公众号关键词
            wechat_matches = sum(1 for keyword in self.WECHAT_KEYWORDS if keyword in cleaned_content)
            if wechat_matches >= 2:
                deduction = -5
                deductions.append(deduction)
                deduction_details.append(f"公众号关键词扣分: {deduction} (匹配数量: {wechat_matches})")
            elif wechat_matches == 1:
                deduction = -2
                deductions.append(deduction)
                deduction_details.append(f"公众号关键词扣分: {deduction} (匹配数量: {wechat_matches})")

            # 检查招聘相关词
            recruitment_matches = sum(1 for keyword in self.SCORE_RULES['DEDUCTIONS']['RECRUITMENT']['keywords'] if keyword in cleaned_content)
            if recruitment_matches > 0:
                deduction = self.SCORE_RULES['DEDUCTIONS']['RECRUITMENT']['business_specific']['行业-通知']['score'] * recruitment_matches
                deductions.append(deduction)
                deduction_details.append(f"招聘关键词扣分: {deduction} (匹配数量: {recruitment_matches})")

            # 检查会议相关词
            meeting_matches = sum(1 for keyword in self.SCORE_RULES['DEDUCTIONS']['MEETING']['keywords'] if keyword in cleaned_content)
            if meeting_matches > 0:
                deduction = self.SCORE_RULES['DEDUCTIONS']['MEETING']['business_specific']['行业-通知']['score'] * meeting_matches
                deductions.append(deduction)
                deduction_details.append(f"会议关键词扣分: {deduction} (匹配数量: {meeting_matches})")

            # 检查交友相关词
            dating_matches = sum(1 for keyword in self.SCORE_RULES['DEDUCTIONS']['DATING']['keywords'] if keyword in cleaned_content)
            if dating_matches > 0:
                deduction = self.SCORE_RULES['DEDUCTIONS']['DATING']['business_specific']['行业-通知']['score'] * dating_matches
                deductions.append(deduction)
                deduction_details.append(f"交友关键词扣分: {deduction} (匹配数量: {dating_matches})")

            # 检查征兵相关词
            military_matches = sum(1 for keyword in self.SCORE_RULES['DEDUCTIONS']['MILITARY']['keywords'] if keyword in cleaned_content)
            if military_matches > 0:
                deduction = self.SCORE_RULES['DEDUCTIONS']['MILITARY']['business_specific']['行业-通知']['score'] * military_matches
                deductions.append(deduction)
                deduction_details.append(f"征兵关键词扣分: {deduction} (匹配数量: {military_matches})")

            # 检查教育营销相关词
            education_matches = sum(1 for keyword in self.SCORE_RULES['DEDUCTIONS']['EDUCATION']['keywords'] if keyword in cleaned_content)
            if education_matches > 0:
                deduction = self.SCORE_RULES['DEDUCTIONS']['EDUCATION']['business_specific']['行业-通知']['score'] * education_matches
                deductions.append(deduction)
                deduction_details.append(f"教育营销关键词扣分: {deduction} (匹配数量: {education_matches})")

            # 检查教育营销弱关键词
            weak_education_matches = sum(1 for keyword in self.SCORE_RULES['DEDUCTIONS']['EDUCATION']['weak_keywords'] if keyword in cleaned_content)
            if weak_education_matches > 0:
                deduction = self.SCORE_RULES['DEDUCTIONS']['EDUCATION']['business_specific']['行业-通知']['weak_score'] * weak_education_matches
                deductions.append(deduction)
                deduction_details.append(f"教育营销弱关键词扣分: {deduction} (匹配数量: {weak_education_matches})")
                        
            # 检查地址
            has_address, address_score, detected_addresses = self._contains_address(cleaned_content)
            if has_address:
                deduction = min(
                    self.SCORE_RULES['DEDUCTIONS']['ADDRESS']['business_specific']['行业-通知']['score'] * address_score,
                    self.SCORE_RULES['DEDUCTIONS']['ADDRESS']['business_specific']['行业-通知']['max_deduction']
                )
                deductions.append(deduction)
                address_info = ", ".join(detected_addresses) if detected_addresses else f"地址特征分数: {address_score}"
                deduction_details.append(f"地址扣分: {deduction} ({address_info})")
        
        elif business_type == "行业-物流":
            # 检查物流关键词并应用加分规则
            logistics_keywords = self.SCORE_RULES['BONUSES']['LOGISTICS']['keywords']
            logistics_matches = sum(1 for keyword in logistics_keywords if keyword in cleaned_content)
            if logistics_matches > 0:
                # 获取物流加分规则
                logistics_bonus = self.SCORE_RULES['BONUSES']['LOGISTICS']
                # 计算加分（每个匹配关键词加分）
                bonus = min(
                    logistics_bonus['business_specific']['行业-物流']['score'] * logistics_matches,
                    logistics_bonus['business_specific']['行业-物流']['max_bonus']
                )
                deductions.append(bonus)  # 加分项
                deduction_details.append(f"物流关键词加分: +{bonus} (匹配数量: {logistics_matches})")
            else:
                # 如果没有物流关键词，则扣分
                deduction = -30
                deductions.append(deduction)
                deduction_details.append("缺少物流关键词扣分: -30")
                
        # 应用非线性扣分计算
        # 区分正向加分和负向扣分
        positive_deductions = [d for d in deductions if d > 0]
        negative_deductions = [d for d in deductions if d < 0]
        
        # 非线性参数
        nonlinear_params = {
            '行业-通知': {'factor': 30, 'max_total_deduction': -70},  # 从-65增加到-70
            '行业-物流': {'factor': 30, 'max_total_deduction': -60},
        }
        
        params = nonlinear_params.get(business_type, {'factor': 30, 'max_total_deduction': -60})
        
        # 对负向扣分应用非线性计算
        if negative_deductions:
            nonlinear_deduction = self._apply_nonlinear_deduction(
                negative_deductions, 
                factor=params['factor'],
                max_total_deduction=params['max_total_deduction']
            )
        else:
            nonlinear_deduction = 0
            
        # 计算最终分数 = 基础分 + 非线性扣分 + 正向加分
        total_positive = sum(positive_deductions)
        final_score = base_score + nonlinear_deduction + total_positive
                
        # 更新评分详情
        self.score_details['deductions'] = deduction_details
        self.score_details['nonlinear_deduction'] = nonlinear_deduction
        self.score_details['final_score'] = final_score
        self.score_details['base_score'] = base_score
        
        # 判断是否通过
        passed = final_score >= self.SCORE_RULES['PASS_SCORE']['行业'][business_type]
        if passed:
            reasons = [
                f"基础分: {base_score}",
                f"最终得分: {final_score:.2f}"
            ]
            return True, f"审核通过 (原因: {', '.join(reasons)})"
        else:
            return False, f"审核不通过 (总分: {final_score:.2f})"

    def _score_marketing(self, business_type: str, cleaned_content: str, cleaned_signature: str) -> Tuple[bool, str]:
        """
        会销类短信的评分实现
        
        Args:
            business_type: 业务类型
            cleaned_content: 已清理的短信内容
            cleaned_signature: 已清理的短信签名
            
        Returns:
            Tuple[bool, str]: (是否通过验证, 验证结果说明)
        """
        # 基础分数
        base_score = self.SCORE_RULES['BASE_SCORE']['会销'][business_type]
        
        # 收集扣分项而非直接累加
        deductions = []
        deduction_details = []
        
        # 检查私人号码
        if self._contains_private_number(cleaned_content):
            return False, "会销类短信不允许包含私人号码"

        # 检查固定电话
        has_fixed_phone, fixed_phone_count = self._contains_fixed_phone(cleaned_content)
        if has_fixed_phone:
            deduction = min(
                self.SCORE_RULES['DEDUCTIONS']['FIXED_PHONE']['business_specific']['会销-普通']['score'] * fixed_phone_count,
                self.SCORE_RULES['DEDUCTIONS']['FIXED_PHONE']['business_specific']['会销-普通']['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"固定电话扣分: {deduction} (数量: {fixed_phone_count})")

        # 检测链接    
        has_link, link_count = self._contains_link(cleaned_content)
        if has_link:
            deduction = min(
                self.SCORE_RULES['DEDUCTIONS']['LINK']['business_specific']['会销-普通']['score'] * link_count,
                self.SCORE_RULES['DEDUCTIONS']['LINK']['business_specific']['会销-普通']['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"链接扣分: {deduction} (数量: {link_count})")

        # 检查营销关键词
        marketing_matches = sum(1 for keyword in self.SCORE_RULES['DEDUCTIONS']['MARKETING']['keywords'] if keyword in cleaned_content)
        if marketing_matches > 0 and business_type == "会销-普通":
            # 针对会销-普通类型增加营销关键词扣分
            deduction = -8 * marketing_matches  # 从-5增加到-8
            deduction = max(deduction, -15)  # 最大扣分从-10增加到-15
            deductions.append(deduction)
            deduction_details.append(f"营销关键词扣分: {deduction} (匹配数量: {marketing_matches})")
        elif marketing_matches > 0:
            deduction = self.SCORE_RULES['DEDUCTIONS']['MARKETING']['score'] * marketing_matches
            deduction = max(deduction, self.SCORE_RULES['DEDUCTIONS']['MARKETING']['max_deduction'])
            deductions.append(deduction)
            deduction_details.append(f"营销关键词扣分: {deduction} (匹配数量: {marketing_matches})")
            
        # 检查强营销关键词
        strong_marketing_matches = sum(1 for keyword in self.SCORE_RULES['DEDUCTIONS']['MARKETING']['strong_keywords'] if keyword in cleaned_content)
        if strong_marketing_matches > 0 and business_type == "会销-普通":
            # 针对会销-普通类型增加强营销关键词扣分
            deduction = -8 * strong_marketing_matches  # 从-5增加到-8
            deduction = max(deduction, -15)  # 最大扣分从-10增加到-15
            deductions.append(deduction)
            deduction_details.append(f"强营销关键词扣分: {deduction} (匹配数量: {strong_marketing_matches})")
        elif strong_marketing_matches > 0:
            deduction = self.SCORE_RULES['DEDUCTIONS']['MARKETING']['strong_score'] * strong_marketing_matches
            deduction = max(deduction, self.SCORE_RULES['DEDUCTIONS']['MARKETING']['max_deduction'])
            deductions.append(deduction)
            deduction_details.append(f"强营销关键词扣分: {deduction} (匹配数量: {strong_marketing_matches})")
            
        # 检查积分营销关键词
        points_marketing_matches = sum(1 for keyword in self.SCORE_RULES['DEDUCTIONS']['POINTS_MARKETING']['keywords'] if keyword in cleaned_content)
        if points_marketing_matches > 0 and business_type == "会销-普通":
            # 针对会销-普通类型增加积分营销扣分
            deduction = -8 * points_marketing_matches  # 从-5增加到-8
            deduction = max(deduction, -15)  # 最大扣分从-10增加到-15
            deductions.append(deduction)
            deduction_details.append(f"积分营销扣分: {deduction} (匹配数量: {points_marketing_matches})")
        elif points_marketing_matches > 0:
            deduction = self.SCORE_RULES['DEDUCTIONS']['POINTS_MARKETING']['score'] * points_marketing_matches
            deduction = max(deduction, self.SCORE_RULES['DEDUCTIONS']['POINTS_MARKETING']['max_deduction'])
            deductions.append(deduction)
            deduction_details.append(f"积分营销扣分: {deduction} (匹配数量: {points_marketing_matches})")
            
        # 检查积分到期关键词
        points_expiry_matches = sum(1 for keyword in self.SCORE_RULES['DEDUCTIONS']['POINTS_EXPIRY']['keywords'] if keyword in cleaned_content)
        if points_expiry_matches > 0:
            deduction = self.SCORE_RULES['DEDUCTIONS']['POINTS_EXPIRY']['score'] * points_expiry_matches
            deduction = max(deduction, self.SCORE_RULES['DEDUCTIONS']['POINTS_EXPIRY']['max_deduction'])
            deductions.append(deduction)
            deduction_details.append(f"积分到期扣分: {deduction} (匹配数量: {points_expiry_matches})")
        
        # 检查平台关键词
        platform_matches = sum(1 for keyword in self.SCORE_RULES['DEDUCTIONS']['PLATFORM']['keywords'] if keyword in cleaned_content)
        if platform_matches > 0:
            deduction = self.SCORE_RULES['DEDUCTIONS']['PLATFORM']['score'] * platform_matches
            deduction = max(deduction, self.SCORE_RULES['DEDUCTIONS']['PLATFORM']['max_deduction'])
            deductions.append(deduction)
            deduction_details.append(f"平台关键词扣分: {deduction} (匹配数量: {platform_matches})")
        
        # 会销-普通特殊验证
        if business_type == "会销-普通":
            # 检查活动类特征词
            activity_keywords = {'活动', '新品', '新春', '活动预告', '会员福利', 
                               '权益提醒', '专享', '会员专享', '限时', '尊享'}
            activity_matches = sum(1 for keyword in activity_keywords if keyword in cleaned_content)
            if activity_matches > 0:
                bonus = 5 * activity_matches
                deductions.append(bonus)  # 加分项
                deduction_details.append(f"活动特征词加分: +{bonus} (匹配数量: {activity_matches})")

            # 检查会员服务相关词
            membership_keywords = {'尊敬的会员', '尊敬的客户', '尊敬的用户'}
            membership_matches = sum(1 for keyword in membership_keywords if keyword in cleaned_content)
            if membership_matches > 0:
                bonus = 5 * membership_matches
                deductions.append(bonus)  # 加分项
                deduction_details.append(f"会员服务关键词加分: +{bonus} (匹配数量: {membership_matches})")
                
            # 检查微信公众号关键词
            wechat_matches = sum(1 for keyword in self.WECHAT_KEYWORDS if keyword in cleaned_content)
            if wechat_matches >= 2:
                deduction = -20
                deductions.append(deduction)
                deduction_details.append(f"微信公众号关键词扣分: {deduction} (匹配数量: {wechat_matches})")
            elif wechat_matches == 1:
                deduction = -10
                deductions.append(deduction)
                deduction_details.append(f"微信公众号关键词扣分: {deduction} (匹配数量: {wechat_matches})")
                
            # 检查地址
            has_address, address_score, detected_addresses = self._contains_address(cleaned_content)
            if has_address:
                deduction = min(
                    self.SCORE_RULES['DEDUCTIONS']['ADDRESS']['business_specific']['会销-普通']['score'] * address_score,
                    self.SCORE_RULES['DEDUCTIONS']['ADDRESS']['business_specific']['会销-普通']['max_deduction']
                )
                deductions.append(deduction)
                address_info = ", ".join(detected_addresses) if detected_addresses else f"地址特征分数: {address_score}"
                deduction_details.append(f"地址扣分: {deduction} ({address_info})")

        # 应用规则共现减免
        if has_fixed_phone and (has_link or points_marketing_matches > 0):
            # 固定电话与链接或积分营销共现时，应用减免系数
            reduction_factor = 0.7  # 减轻30%扣分
            # 找出固定电话扣分在列表中的位置
            phone_index = 0  # 通常是第一个，因为在上面代码中是第一个处理的
            if len(deductions) > phone_index and deductions[phone_index] < 0:  # 确保是扣分项且存在
                original_deduction = deductions[phone_index]
                deductions[phone_index] = original_deduction * reduction_factor
                deduction_details[phone_index] += f" (与其他规则共现减免: {int((1-reduction_factor)*100)}%)"
        
        # 应用非线性扣分计算
        # 区分正向加分和负向扣分
        positive_deductions = [d for d in deductions if d > 0]
        negative_deductions = [d for d in deductions if d < 0]
        
        # 非线性参数
        nonlinear_params = {
            '会销-普通': {'factor': 40, 'max_total_deduction': -60},
            '会销-金融': {'factor': 35, 'max_total_deduction': -65},
        }
        
        params = nonlinear_params.get(business_type, {'factor': 35, 'max_total_deduction': -65})
        
        # 对负向扣分应用非线性计算
        if negative_deductions:
            nonlinear_deduction = self._apply_nonlinear_deduction(
                negative_deductions, 
                factor=params['factor'],
                max_total_deduction=params['max_total_deduction']
            )
        else:
            nonlinear_deduction = 0
            
        # 计算最终分数 = 基础分 + 非线性扣分 + 正向加分
        total_positive = sum(positive_deductions)
        final_score = base_score + nonlinear_deduction + total_positive
        
        # 更新评分详情
        self.score_details['deductions'] = deduction_details
        self.score_details['nonlinear_deduction'] = nonlinear_deduction
        self.score_details['final_score'] = final_score
        self.score_details['base_score'] = base_score
        
        # 判断是否通过
        passed = final_score >= self.SCORE_RULES['PASS_SCORE']['会销'][business_type]
        if passed:
            reasons = [
                f"基础分: {base_score}",
                f"最终得分: {final_score:.2f}"
            ]
            return True, f"审核通过 (原因: {', '.join(reasons)})"
        else:
            return False, f"审核不通过 (总分: {final_score:.2f})"

    def _score_collection(self, cleaned_content: str) -> Tuple[bool, str]:
        """
        催收类短信的评分实现
        
        Args:
            cleaned_content: 已清理的短信内容
            
        Returns:
            Tuple[bool, str]: (是否通过验证, 验证结果说明)
        """
        # 基础分数
        base_score = self.SCORE_RULES['BASE_SCORE']['拉新']['拉新-催收']
        final_score = base_score
        
        # 检查私人号码
        if self._contains_private_number(cleaned_content):
            final_score += self.SCORE_RULES['ZERO_TOLERANCE']['PRIVATE_NUMBER']
            return False, "催收类短信不允许包含私人号码"

        # 检查私人姓名
        if self._find_chinese_names(cleaned_content):
            final_score += self.SCORE_RULES['ZERO_TOLERANCE']['PRIVATE_NUMBER']
            return False, "催收类短信不允许包含私人姓名"

        # 检查固定电话
        has_fixed_phone, fixed_phone_count = self._contains_fixed_phone(cleaned_content)
        if has_fixed_phone:
            deduction = min(
                self.SCORE_RULES['DEDUCTIONS']['FIXED_PHONE']['business_specific']['拉新-催收']['score'] * fixed_phone_count,
                self.SCORE_RULES['DEDUCTIONS']['FIXED_PHONE']['business_specific']['拉新-催收']['max_deduction']
            )
            final_score += deduction
            self.score_details['deductions'].append(f"固定电话扣分: {deduction} (数量: {fixed_phone_count})")

        has_link, link_count = self._contains_link(cleaned_content)
        if has_link:
            deduction = min(
                self.SCORE_RULES['DEDUCTIONS']['LINK']['business_specific']['拉新-催收']['score'] * link_count,
                self.SCORE_RULES['DEDUCTIONS']['LINK']['business_specific']['拉新-催收']['max_deduction']
            )
            final_score += deduction
        
        # 判断是否通过
        passed = final_score >= self.SCORE_RULES['PASS_SCORE']['拉新']['拉新-催收']
        if passed:
            reasons = [
                f"基础分: {base_score}",
                f"最终得分: {final_score:.2f}"
            ]
            return True, f"审核通过 (原因: {', '.join(reasons)})"
        else:
            return False, f"审核不通过 (总分: {final_score:.2f})"

    def _contains_private_number(self, text: str) -> bool:
        """
        检查文本中是否包含私人手机号码
        
        Args:
            text: 待检查的文本
            
        Returns:
            bool: 是否包含私人号码
        """
        pattern = r'1[3-9]\d{9}|1[3-9]\d{4}[ -]\d{4}|1[3-9][ -]\d{4}[ -]\d{4}'
        return bool(re.search(pattern, text))

    def _find_chinese_names(self, text: str) -> bool:
        """
        使用结巴分词检查文本中是否包含中文姓名
        
        Args:
            text: 待检查的文本
            
        Returns:
            bool: 是否包含中文姓名
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
        """
        根据业务类型获取其所属的业务类别
        
        Args:
            business_type: 具体的业务类型
            
        Returns:
            str: 业务类别（行业/会销/拉新）
        """
        for category, types in self.BUSINESS_TYPE_LIBRARY.items():
            if business_type in types:
                return category
        return ""
    
    def _contains_link(self, text: str) -> Tuple[bool, int]:
        """
        使用正则表达式检查文本中是否包含链接
        
        Args:
            text: 待检查的文本
            
        Returns:
            Tuple[bool, int]: (是否包含链接, 链接数量)
        """
        # 定义链接匹配模式
        url_patterns = [
            # 标准URL格式（支持更多协议）
            r'(?:https?|ftp|file|ws|wss)://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*',
            
            # 带www的网址（支持更多子域名）
            r'(?:www|wap|m)\.(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*',
            
            # 常见顶级域名格式（扩展域名列表）
            r'(?:[-\w.]|(?:%[\da-fA-F]{2}))+\.(?:com|cn|net|org|gov|edu|io|app|xyz|top|me|tv|cc|shop|vip|ltd|store|online|tech|site|wang|cloud|link|live|work|game|fun|art|xin|ren|space|team|news|law|group|center|city|world|life|co|red|mobi|pro|info|name|biz|asia|tel|club|social|video|press|company|website|email|network|studio|design|software|blog|wiki|forum|run|zone|plus|cool|show|gold|today|market|business|company|zone|media|agency|directory|technology|solutions|international|enterprises|industries|management|consulting|services)(?:/[^\s]*)?',
            
            # 短链接格式（扩展常见短链接服务）
            r'(?:t|u|dwz|url|c|s|m|j|h5|v|w)\.(?:cn|com|me|ly|gl|gd|ink|run|app|fun|pub|pro|vip|cool|link|live|work|game|art|red|tel|club|show|gold|today)(?:/[-\w]+)+',
            
            # 特定平台短链接，包括淘宝、京东、饿了么、抖音、微博等
            r'(?:tb\.cn|jd\.com|ele\.me|douyin\.com|weibo\.com|qq\.com|taobao\.com|tmall\.com|pinduoduo\.com|kuaishou\.com|bilibili\.com|youku\.com|iqiyi\.com|meituan\.com|dianping\.com|alipay\.com|weixin\.qq\.com)/[-\w/]+',
            
            # IP地址格式链接（支持IPv6）
            r'https?://(?:\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4})(?::\d+)?(?:/[^\s]*)?'
        ]
        
        # 合并所有模式
        combined_pattern = '|'.join(f'({pattern})' for pattern in url_patterns)
        
        # 查找所有匹配项
        matches = re.findall(combined_pattern, text, re.IGNORECASE)
        
        # 计算匹配数量（matches是一个元组列表，每个元组包含所有捕获组）
        link_count = sum(1 for match in matches if any(match))
        
        return link_count > 0, link_count

    def _contains_fixed_phone(self, text: str) -> Tuple[bool, int]:
        """
        检查文本中是否包含固定电话号码
        
        Args:
            text: 待检查的文本
            
        Returns:
            Tuple[bool, int]: (是否包含固定电话, 固定电话数量)
        """
        # 匹配固定电话模式
        patterns = [
            r'\d{3,4}-\d{7,8}',  # 区号-号码格式
            r'\d{7,8}',          # 纯7-8位号码
            r'\d{3,4}\s*\d{7,8}' # 区号和号码之间有空格
        ]
        
        # 合并所有模式
        combined_pattern = '|'.join(f'({pattern})' for pattern in patterns)
        
        # 查找所有匹配项
        matches = re.findall(combined_pattern, text)
        
        # 计算匹配数量
        phone_count = sum(1 for match in matches if any(match))
        
        return phone_count > 0, phone_count

    def _is_neutral_signature(self, cleaned_signature: str) -> bool:
        """
        检查签名是否为中性签名
        
        Args:
            signature: 短信签名
            
        Returns:
            bool: 是否为中性签名
        """
        return cleaned_signature in self.NEUTRAL_SIGNATURES

    def _apply_nonlinear_deduction(self, deductions: List[float], factor: float = 30, max_total_deduction: float = -60) -> float:
        """
        应用非线性扣分计算，使用对数函数减轻多个规则同时触发时的惩罚
        
        Args:
            deductions: 负值扣分列表
            factor: 非线性因子，控制曲线陡峭程度
            max_total_deduction: 最大总扣分限制
            
        Returns:
            float: 非线性计算后的总扣分
        """
        if not deductions:
            return 0
            
        # 计算线性扣分总和
        linear_sum = sum(deductions)
        
        # 确保线性扣分总和为负值
        if linear_sum >= 0:
            return linear_sum
            
        # 应用非线性函数: factor * ln(1 + |linear_sum|/factor)
        nonlinear_deduction = -factor * math.log(1 + abs(linear_sum) / factor)
        
        # 应用最大扣分限制
        return max(nonlinear_deduction, max_total_deduction)

# 定义有效的客户类型
客户类型 = ["云平台", "直客", "类直客", "渠道"]

def validate_account_type(account_type: str) -> Tuple[bool, str]:
    """
    验证客户类型是否有效
    
    Args:
        account_type: 客户类型（如"云平台"、"直客"等）
        
    Returns:
        Tuple[bool, str]: (是否通过验证, 验证结果说明)
    """
    
    # 直客类型直接放行
    if account_type == "直客":
        return True, "直客类型直接通过"
        
    return True, "客户类型有效"

def validate_business(business_type: str, content: str, signature: str, account_type: str = None) -> Tuple[bool, str]:
    """
    外部调用的主要入口函数，用于验证短信的业务类型是否合规
    """
    # 1. 首先验证客户类型
    account_valid, account_reason = validate_account_type(account_type)
    if not account_valid:
        return False, account_reason
        
    # 2. 如果是直客，直接返回通过
    if account_type == "直客":
        return True, "直客类型直接通过"
    
    # 3. 清理内容和签名
    validator = BusinessValidator()
    cleaned_content = validator._clean_content(content)
    cleaned_signature = validator._clean_content(signature)
    
    # 4. 检查是否为中性签名，中性签名可直接通过
    if validator._is_neutral_signature(cleaned_signature):
        return False, "中性签名直接不通过"
    
    # 5. 进行业务验证
    return validator._validate_business_internal(business_type, cleaned_content, cleaned_signature, account_type)

