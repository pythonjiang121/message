import re  
import cpca
import pandas as pd
from typing import Tuple, Dict, List, Set
import json
import jieba.posseg as pseg
from zhconv import convert



class BusinessValidator:
    # 业务类型库
    BUSINESS_TYPE_LIBRARY: Dict[str, List[str]] = {
        "行业": ["行业-通知", "行业-物流"],
        "会销": ["会销-普通", "会销-金融"],
        "拉新": ["拉新-催收", "拉新-教育", "拉新-网贷", "拉新-展会", "拉新-医美", "拉新-pos机"]
    }

    # 关键词常量定义
 
    NAME_WHITELIST: Set[str] = {"您好", "本人"}
 
    # 添加中性签名列表
    NEUTRAL_SIGNATURES: Set[str] = {"温馨提示", "恭喜发财", "市燃气办", "企业福利", "特卖提示", "城中区两个责任专班", "云通信", "卖家精灵", "反诈提醒","广东商城",
                                    "保障房管理中心" , "通道消防" , "七天一洗" , "搜地"  , "指悦到家"  , "燃气公司"  , "紫维丰"  , "奢品特卖"}


    # 定义评分规则
    SCORE_RULES = {
        # 基础分数
        'BASE_SCORE': {
            '行业': {
                '行业-通知': 100,  
                '行业-物流': 100,   
            },
            '会销': {
                '会销-普通': 100,   
                '会销-金融': 100,   
            },
            '拉新': {
                '拉新-催收': 100,   
                '拉新-教育': 100,   
                '拉新-网贷': 100,   
                '拉新-展会': 100,   
                '拉新-医美': 100,   
                '拉新-pos机': 100   
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
                        'score': -20,  # 通知类每个地址特征扣2分
                        'max_deduction': -50  # 通知类最大扣分6分
                    },
                    '行业-物流': {
                        'score': -5,  # 物流类每个地址特征扣2分
                        'max_deduction': -10  # 物流类最大扣分6分
                    },  
                    '会销-普通': {
                        'score': -10,  # 会销普通类每个地址特征扣2分
                        'max_deduction': -50  # 会销普通类最大扣分6分
                    }
                }
            },


            # 涉黄扣分规则
            'PORNOGRAPHIC': {                
                'keywords': {'裸聊', '一夜情', '约炮', '援交', '小姐', '按摩', '特殊服务', '上门服务', '出台', '包夜', '兼职学生', '兼职妹', '兼职女' ,'足底'},
                'score': -100,  
                'max_deduction': -100,  
                'business_specific': {
                    '行业-通知': {
                        'score': -100,
                        'max_deduction': -100
                    },
                    '行业-物流': {
                        'score': -100,
                        'max_deduction': -100
                    },
                    '会销-普通': {
                        'score': -100,
                        'max_deduction': -100
                    },
                    '拉新-催收': {
                        'score': -100,
                        'max_deduction': -100
                    }
                }
            },


            #涉诈扣分规则
            'FRAUD': {
                'keywords': {'公司倒闭','资金盘', '跑路', '高额回报', '暴利项目', '快速致富', '投资理财', '理财项目', '理财产品',
                           '虚拟货币', '数字货币', '虚拟币', '比特币', '区块链', '挖矿', '中奖', '私彩'},
                'score': -100,
                'max_deduction': -100,
                'business_specific': {
                    '行业-通知': {
                        'score': -100,
                        'max_deduction': -100
                    },
                    '行业-物流': {
                        'score': -100,
                        'max_deduction': -100
                    },
                    '会销-普通': {
                        'score': -100,
                        'max_deduction': -100   
                    },
                    '拉新-催收': {
                        'score': -100,
                        'max_deduction': -100
                    }   
                }   
            },  




            # 营销内容扣分规则
            'MARKETING': { 
                'keywords': {
                    '抢购', '限量', '福利', '奖励', '领取', '权益', '购买','只需' ,'搜索',
                    '秒杀', '特供', '专享', '尊享', '特权', '免费', '超值', '多赚','优惠', '特惠', '红包',
                    '特价', '折扣', '促销', '活动', '尾款' ,'仅剩',' 限时' ,'倒计时' ,'咨询','详讯' ,'预约' ,'消费' ,'惊喜',
                    '大单' ,'错过' ,'特价' ,'大促' ,'爆品' ,'直降' ,'开抢' ,'售罄' ,'补贴' ,'大放送'
                },
                'business_specific': {
                    '行业-通知': {
                        'score': -50, 
                        'max_deduction': -80, 
                          
                    },
                    '行业-物流': {
                        'score': -15,  
                        'max_deduction': -30, 
                         
                    },
                    '会销-普通': {
                        'score': -5, 
                        'max_deduction': -10, 
  
                    }
                }
            },
            
            # 会员积分营销相关扣分规则
            'POINTS_MARKETING': {
                'keywords': {
                    '积分', '兑换', '领取', '会员', '回馈', '老客', '新客', '老带新',
                    '服务', '活动', '奖励', '赠送', '优惠券', '里程'
                },
                'score': -10,  
                'max_deduction': -30,  
                'business_specific': {
                    '行业-通知': {
                        'score': -50, 
                        'max_deduction': -50   
                    },
                    '行业-物流': {
                        'score': -15, 
                        'max_deduction': -30   
                    },
                    '会销-普通': {
                        'score': -50,  
                        'max_deduction': -60   
                    }
                }
            },
            
            # 积分到期相关扣分规则
            'POINTS_EXPIRY': {
                'keywords': {
                    '积分', '积分到期', '过期', '清零', '作废', '失效', 
                    '即将到期', '即将清零', '即将作废', '清理', '清空' ,'逾期' ,'期限' ,'限期'  
                },
                'score': -10,  
                'max_deduction': -20,  
                'business_specific': {
                    '行业-通知': {
                        'score': -50,  
                        'max_deduction': -50 
                    },
                    '行业-物流': {
                        'score': -15,  
                        'max_deduction': -30 
                    },
                    '会销-普通': {
                        'score': -50,  
                        'max_deduction': -60 
                    }
                }
            },
            

            # 行业通知催支付相关扣分规则
            'PAYMENT_REMINDER': {
                'keywords': {
                    '尾款','支付','有效期','逾期' ,'交纳' ,'交费' ,'缴费' ,'缴纳' ,'缴清'
                },
                'business_specific': {
                    '行业-通知': {
                        'score': -50,
                        'max_deduction': -50            
                    },
                    '行业-物流': {
                        'score': -0,
                        'max_deduction': -0
                    }   
                }
            },
            # 招生相关扣分规则
            'ADMISSIONS': {
                'keywords': {
                    '招生', '入学', '新生', '学费', '学籍', '入学考试',
                    '学历', '文凭', '证书', '毕业', '升学', '考证' 
                },
                'business_specific': {
                    '行业-通知': {
                        'score': -50,
                        'max_deduction': -50
                    },  
                    '行业-物流': {
                        'score': -50,
                        'max_deduction': -50
                    },
                    '会销-普通': {
                        'score': -50,
                        'max_deduction': -50
                    }
                }
            },   

            # 年报相关扣分规则
            'ANNUAL_REPORT': {
                'keywords': {
                    '年报', '年报申报', '年报公示' ,'年度企业报告'
                },
                'business_specific': {
                    '行业-通知': {
                        'score': -50,
                        'max_deduction': -50
                    },
                    '行业-物流': {
                        'score': -50,
                        'max_deduction': -50
                    },  
                    '会销-普通': {
                        'score': -50,
                        'max_deduction': -50
                    }   
                }
            },

            # 直播相关扣分规则
            'LIVE_STREAMING': {
                'keywords': {
                    '直播', '带货', '主播', '观看直播', '直播间', '连麦'
                },
                'score': -10,  # 增加扣分
                'max_deduction': -15,  # 增加最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -50,  # 增加通知类扣分
                        'max_deduction': -70  # 增加最大扣分
                    },
                    '行业-物流': {
                        'score': -50,  # 增加通知类扣分
                        'max_deduction': -70  # 增加最大扣分
                    },  
                    '会销-普通': {
                        'score': -50,  # 增加通知类扣分
                        'max_deduction': -70  # 增加最大扣分
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
                        'score': -50,  # 增加通知类扣分
                        'max_deduction': -50  # 增加最大扣分
                    },
                    '行业-物流': {
                        'score': -50,  # 增加通知类扣分
                        'max_deduction': -50  # 增加最大扣分
                    },  
                    '会销-普通': {
                        'score': -50,  # 增加通知类扣分
                        'max_deduction': -50  # 增加最大扣分
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
                        'score': -50,  # 增加通知类扣分
                        'max_deduction': -50  # 增加最大扣分
                    },
                    '行业-物流': {
                        'score': -50,  # 增加通知类扣分
                        'max_deduction': -50  # 增加最大扣分
                    },  
                    '会销-普通': {
                        'score': -30,  # 增加会销普通类扣分
                        'max_deduction': -30  # 增加最大扣分
                    }
                }
            },

            # 交友相关扣分规则
            'DATING': {
                'keywords': {
                    '交友', '相亲', '留言' ,'男友' ,'女友' ,'匹配'
                },
                'score': -50,  # 增加扣分
                'max_deduction': -50,  # 增加最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -50,  # 增加通知类扣分
                        'max_deduction': -50  # 增加最大扣分
                    },
                    '会销-普通': {
                        'score': -50,  # 增加通知类扣分
                        'max_deduction': -50  # 增加最大扣分
                    },
                    '拉新-催收': {
                        'score': -50,  # 增加通知类扣分
                        'max_deduction': -50  # 增加最大扣分
                    },
                }
            },

            # 征兵相关扣分规则
            'MILITARY': {
                'keywords': {
                    '征兵', '入伍', '兵役'  ,'当兵' ,'参军'
                },
                'score': -50,  # 增加扣分
                'max_deduction': -50,  # 增加最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -50,  # 增加通知类扣分
                        'max_deduction': -50  # 增加最大扣分
                    },
                    '行业-物流': {
                        'score': -50,  # 增加通知类扣分
                        'max_deduction': -50  # 增加最大扣分
                    },
                    '会销-普通': {
                        'score': -50,  # 增加通知类扣分
                        'max_deduction': -50  # 增加最大扣分
                    }   
                }
            },
            
            # 问卷调查扣分规则
            'SURVEY': {
                'keywords': {'问卷', '调查', '调研', '反馈', '评价'
                },
                'score': -10,  # 增加扣分
                'max_deduction': -30,  # 增加最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -15,  # 增加通知类扣分
                        'max_deduction': -30  # 增加最大扣分
                    },
                    '行业-物流': {
                        'score': -15,  # 增加通知类扣分
                        'max_deduction': -30  # 增加最大扣分
                    },
                    '会销-普通': {
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
                    '练习册', '习题', '老师', '干货' ,'口语课' ,'课时' ,'学堂'
                },
                'score': -10,  # 增加扣分
                'max_deduction': -30,  # 增加最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -50,  # 增加通知类扣分
                        'max_deduction': -50  # 增加最大扣分
                    },
                    '行业-物流': {
                        'score': -50,  # 增加通知类扣分
                        'max_deduction': -50  # 增加最大扣分
                    },  
                    '会销-普通': {
                        'score': -50,  # 增加通知类扣分
                        'max_deduction': -50  # 增加最大扣分
                    }
                }
            },
            
            # 展会相关扣分规则
            'EXHIBITION': {
                'keywords': {
                    '展会', '展览', '展示', '博览会', '交易会', '展位', 
                    '展销', '参展', '展馆', '展厅', '现场', '发布会',
                    '盛会', '观展', '展商', '展期', '邀请函', '邀请码'
                },
                'score': -15,  # 默认扣分
                'max_deduction': -30,  # 最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -20,  # 行业通知类扣分
                        'max_deduction': -40  # 最大扣分
                    },
                    '行业-物流': {
                        'score': -20,  # 行业通知类扣分
                        'max_deduction': -40  # 最大扣分
                    },
                    '会销-普通': {
                        'score': -25,  # 会销普通类扣分
                        'max_deduction': -50  # 最大扣分
                    }
                }
            },
            
            # 黄金珠宝相关扣分规则
            'JEWELRY': {
                'keywords': {
                    '黄金', '珠宝', '钻石', '玉石', '翡翠', '铂金', 
                    '首饰', '金条', '金币', '金银', '珍珠', '宝石',
                    '玛瑙', '水晶', '项链', '手链', '戒指', '耳饰',
                    '金饰', '银饰', '珠宝展', '金店', '珠宝店', '珠宝商',
                    '金价', '金融产品', '投资金', '投资产品'
                },
                'score': -20,  # 默认扣分
                'max_deduction': -40,  # 最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -20,  # 行业通知类扣分
                        'max_deduction': -40  # 最大扣分
                    },
                    '行业-物流': {
                        'score': -20,  # 行业通知类扣分
                        'max_deduction': -40  # 最大扣分
                    },
                    '会销-普通': {
                        'score': -50,  # 会销普通类扣分
                        'max_deduction': -50  # 最大扣分
                    }
                }
            },
            
            # 酒水相关扣分规则
            'LIQUOR': {
                'keywords': {
                    '白酒', '红酒', '葡萄酒', '洋酒', '啤酒', '鸡尾酒', 
                    '威士忌', '伏特加', '朗姆酒', '香槟', '品酒', '酒庄',
                    '酒厂', '酒吧', '酒会', '酒展', '酒类', '酿酒',
                    '酒精', '烈酒', '浓香', '窖藏', '陈酿', '贵州茅台',
                    '五粮液', '泸州老窖', '二锅头', '老白干', '黄酒', '米酒',
                    '精酿', '原浆', '整箱' ,'茅台'
                },
                'score': -20,  # 默认扣分
                'max_deduction': -40,  # 最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -20,  # 行业通知类扣分
                        'max_deduction': -40  # 最大扣分
                    },
                    '会销-普通': {
                        'score': -50,  # 会销普通类扣分
                        'max_deduction': -50  # 最大扣分
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
                    },
                    '行业-物流': {
                        'score': -15,  # 增加通知类扣分
                        'max_deduction': -30  # 增加最大扣分
                    },  
                    '会销-普通': {
                        'score': -50,  # 增加通知类扣分
                        'max_deduction': -50  # 增加最大扣分
                    }   
                }
            },
                        
            # 平台相关扣分规则
            'PLATFORM': {
                'keywords': {
                    '平台', '客服', '详询', '咨询', 
                    '热线', '服务', '详情', '链接', '网址', '网站', '登录', '注册'
                },
                'score': -5,  
                'max_deduction': -15,  
                'business_specific': {
                    '行业-通知': {
                        'score': -50,  
                        'max_deduction': -50   
                    },
                    '会销-普通': {
                        'score': -5,  
                        'max_deduction': -15  
                    },
                    '行业-物流': {
                        'score': -5,  
                        'max_deduction': -15  
                    }
                }
            },
            
            # 固定电话扣分规则
            'FIXED_PHONE': {
                'score': -30,  
                'max_deduction': -50,
                'business_specific': {
                    '会销-普通': {
                        'score': -80,  
                        'max_deduction': -80
                    },
                    '行业-物流': {
                        'score': -40,  
                        'max_deduction': -40
                    },
                    '行业-通知': {
                        'score': -50, 
                        'max_deduction': -100
                    },
                    '拉新-催收': {
                        'score': -40,  
                        'max_deduction': -40
                    }
                }
            },
            
            # 微信公众号相关扣分规则
            'WECHAT': {
                'keywords': {'微信', '公众号', '关注', '小程序', 'APP', 'app' ,'加微'},
                'score': -30, 
                'max_deduction': -60, 
                'business_specific': {
                    '行业-通知': {
                        'score': -20,  
                        'max_deduction': -40   
                    },
                    '会销-普通': {
                        'score': -30,  
                        'max_deduction': -60
                    },
                    '行业-物流': {
                        'score': -20,  
                        'max_deduction': -40   
                    }
                }
            },

            # # 链接相关扣分规则
            # 'LINK': {
            #     'score': -40,  
            #     'max_deduction': -60, 
            #     'business_specific': {
            #         '行业-通知': {
            #             'score': -50,  
            #             'max_deduction': -50  
            #         },
            #         '行业-物流': {
            #             'score': -50,  
            #             'max_deduction': -50  
            #         },
            #         '会销-普通': {
            #             'score': -80,  
            #             'max_deduction': -80  
            #         },
            #         '拉新-催收': {
            #             'score': -50, 
            #             'max_deduction': -50  
            #         },
            #     }
            # },
            
            
            # 医疗疾病扣分规则
            'MEDICAL': {
                'keywords': {
                    '医院', '诊所', '医生', '医师', '护士', '治疗', '手术', '住院', '门诊',
                    '科室', '专家', '主任', '教授', '大夫', '看病', '就医', '挂号', '预约',
                    '体检', '检查', '化验', '诊断', '处方', '药品', '药物', '中药', '西药',
                    '针剂', '注射', '输液', '康复', '理疗', '保健', '养生', '美容', '整形', '药业', '胆固醇', '心脑血管',
                    '医美', '微整', '植发', '牙科', '口腔', '眼科', '皮肤科', '内科', '外科', '献血', '血浆', '捐血',
                    '尿频', '内脏', '三高', '血糖', '免疫', '疫病'  ,'医保'  ,'麻风病' ,'红斑' ,'白斑'  ,'带状疱疹' ,'献浆' 

                },
                'score': -20,  # 默认扣分
                'max_deduction': -40,  # 最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -40,  # 行业通知类扣分
                        'max_deduction': -60  # 最大扣分
                    },
                    '行业-物流': {
                        'score': -20,  # 行业物流类扣分
                        'max_deduction': -40  # 最大扣分
                    },
                    '会销-普通': {
                        'score': -50,  # 会销普通类扣分
                        'max_deduction': -60  # 最大扣分
                    }
                }
            },
            
            # 游戏相关扣分规则
            'GAME': {
                'keywords': {
                    '游戏', '手游', '网游', '页游', '端游', '电竞', '对战', 'vip', '礼包',
                    '排位', '段位', '等级', '装备', '道具', '皮肤', '充值', '氪金', '抽卡',
                    '任务', '副本', '公会', '战队', '抽奖', '开黑', '代跑',  '试玩' ,'邀请好友' ,'新服', '霸业', '热血', '战斗'
                },
                'score': -15,  # 默认扣分
                'max_deduction': -30,  # 最大扣分
                'business_specific': {
                    '行业-通知': {
                        'score': -50,  # 行业通知类扣分
                        'max_deduction': -60  # 最大扣分
                    },
                    '行业-物流': {
                        'score': -50,  # 行业物流类扣分
                        'max_deduction': -60  # 最大扣分
                    },  
                    '会销-普通': {
                        'score': -40,  # 会销普通类扣分
                        'max_deduction': -80  # 最大扣分
                    }
                }
            },

            # 拉新-催收相关扣分规则
            'COLLECTION': {
                'keywords': {
                    '催收', '欠款', '欠费', '还款', '逾期', '违约', '拖欠', '账单',
                    '信用', '黑名单', '失信', '法律', '诉讼', '起诉', '法院', '传票',
                    '债务', '债权', '利息', '罚息', '滞纳金', '违约金', '保全', '强制',
                    '执行', '清偿', '催缴', '追讨', '追债', '讨债', '催债', '收债', 
                    '居住地', '合同地', '工作地', '户籍', '案底', '儿女', '户籍地', '登门', '邻亲', '居委', '骗贷', '无息', '免期', '本金', '延期', '减免'
                },
                'score': -30,  # 默认扣分
                'max_deduction': -60,  # 最大扣分
                'business_specific': {
                    '拉新-催收': {
                        'score': -40,  # 催收类扣分
                        'max_deduction': -80  # 最大扣分
                    }
                }
            }

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
            'APP_SIGNATURE': {
                'keywords': {'饿了么','旗舰店', '专卖店'},
                'score': 20,
                'max_bonus': 40
            },
            
            # 特定关键词签名加分
            'GOV_SIGNATURE': {
                'keywords': {'政府', '机关', '电力', '部委', '法院', '检察院','公安局', '中国' ,'监管局' ,'中共' ,'市委' ,'组织部' ,'监督管理局'},
                'score': 20,
                'max_bonus': 20
            },

        
        },
            

        
        # 及格分数线
        'PASS_SCORE': {
            '行业': {
                '行业-通知': 60,  
                '行业-物流': 60,  
            },
            '会销': {
                '会销-普通': 60,   
                '会销-金融': 60,  
            },
            '拉新': {
                '拉新-催收': 60,  
                '拉新-教育': 60,  
                '拉新-网贷': 60,  
                '拉新-展会': 60,  
                '拉新-医美': 60,  
                '拉新-pos机': 60 
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
            'deductions': [], #减分
            'bonuses': [], #加分
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

            # 对于会销-金融，使用会销-普通的规则
            if business_type == "会销-金融":
                return self._score_marketing("会销-普通", cleaned_content, cleaned_signature)
            else:            
                return self._score_marketing(business_type, cleaned_content, cleaned_signature)
        elif business_category == "拉新":
            # 对所有拉新类型都使用拉新-催收的规则进行评分
            return self._score_collection(business_type, cleaned_content, cleaned_signature)



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
        #加分扣分列表
        deductions = []
        #匹配关键词列表，作为扣分明细返回
        deduction_details = []
        
        # 检查涉黄关键词
        pornographic_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['PORNOGRAPHIC']['keywords'] if k in cleaned_content]
        pornographic_keywords_count = len(pornographic_keywords)
        if pornographic_keywords_count > 0:
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['PORNOGRAPHIC']['business_specific'][business_type]['score'] * pornographic_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['PORNOGRAPHIC']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"涉黄扣分: {deduction} (匹配词: {', '.join(pornographic_keywords) }, 匹配数量: {pornographic_keywords_count})")   
        
        # 检查涉诈关键词
        fraud_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['FRAUD']['keywords'] if k in cleaned_content]
        fraud_keywords_count = len(fraud_keywords)
        if fraud_keywords_count > 0:
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['FRAUD']['business_specific'][business_type]['score'] * fraud_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['FRAUD']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"涉诈扣分: {deduction} (匹配词: {', '.join(fraud_keywords) }, 匹配数量: {fraud_keywords_count})") 
        

        # 应用特定签名加分
        app_signature_keywords = [k for k in self.SCORE_RULES['BONUSES']['APP_SIGNATURE']['keywords'] if k in cleaned_signature]
        app_signature_keywords_count = len(app_signature_keywords)
        if app_signature_keywords_count > 0:
            bonus = min(self.SCORE_RULES['BONUSES']['APP_SIGNATURE']['score'] * app_signature_keywords_count, 
                        self.SCORE_RULES['BONUSES']['APP_SIGNATURE']['max_bonus'])
            deductions.append(bonus)  # 加分项           
            deduction_details.append(f"特定关键词签名加分: +{bonus} (匹配关键词: {', '.join(app_signature_keywords)})")
        
        
        # 应用特定关键词签名加
        gov_signature_keywords = [k for k in self.SCORE_RULES['BONUSES']['GOV_SIGNATURE']['keywords'] if k in cleaned_signature]
        gov_signature_keywords_count = len(gov_signature_keywords)
        if gov_signature_keywords_count > 0:  
            bonus = min(self.SCORE_RULES['BONUSES']['GOV_SIGNATURE']['score'] * gov_signature_keywords_count, 
                        self.SCORE_RULES['BONUSES']['GOV_SIGNATURE']['max_bonus'])
            deductions.append(bonus)  # 加分项           
            deduction_details.append(f"特定关键词签名加分: +{bonus} (匹配关键词: {', '.join(gov_signature_keywords)})")
            
        # 检查私人号码
        has_private_number, private_numbers = self._contains_private_number(cleaned_content)
        if has_private_number:
            # 对于零容忍项，直接返回失败
            # deduction_details.append(f"私人号码违规: 拒绝通过 (检测到: {', '.join(private_numbers)})")
            return False, f"审核不通过 (原因: 含有私人号码: {', '.join(private_numbers)}) (基础分: 100, 总分: 0)"

        # # 检测链接（提前检测以便后续共现规则使用）
        # has_link, link_count = self._contains_link(cleaned_content)
        # if has_link:
        #     link_deduction = self.SCORE_RULES['DEDUCTIONS']['LINK']['business_specific'][business_type]['score'] * link_count
        #     # 使用max确保不超过最大扣分限制
        #     link_deduction = max(link_deduction, self.SCORE_RULES['DEDUCTIONS']['LINK']['business_specific'][business_type]['max_deduction'])
        #     deductions.append(link_deduction)
        #     deduction_details.append(f"链接扣分: {link_deduction} (链接数量: {link_count})")

        # 检查固定电话
        has_fixed_phone, fixed_phone_count, fixed_phone_numbers = self._contains_fixed_phone(cleaned_content)
        if has_fixed_phone:
            # 计算扣分
            phone_deduction = self.SCORE_RULES['DEDUCTIONS']['FIXED_PHONE']['business_specific'][business_type]['score'] * fixed_phone_count
            # 使用max确保不超过最大扣分限制
            phone_deduction = max(phone_deduction, self.SCORE_RULES['DEDUCTIONS']['FIXED_PHONE']['business_specific'][business_type]['max_deduction'])            
            deductions.append(phone_deduction)
            deduction_details.append(f"固定电话扣分: {phone_deduction} (检测到: {', '.join(fixed_phone_numbers)})")
            
        # 检查营销关键词
        marketing_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['MARKETING']['keywords'] if k in cleaned_content]
        marketing_keywords_count = len(marketing_keywords)        
        if marketing_keywords_count > 0:      
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['MARKETING']['business_specific'][business_type]['score'] * marketing_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['MARKETING']['business_specific'][business_type]['max_deduction']
            )           
            deductions.append(deduction)
            deduction_details.append(f"\n营销关键词扣分: {deduction} (匹配词: {', '.join(marketing_keywords) }, 匹配数量: {marketing_keywords_count})")        


        # 检查积分营销关键词
        points_marketing_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['POINTS_MARKETING']['keywords'] if k in cleaned_content]
        points_marketing_keywords_count = len(points_marketing_keywords)
        if points_marketing_keywords_count > 0:
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['POINTS_MARKETING']['business_specific'][business_type]['score'] * points_marketing_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['POINTS_MARKETING']['business_specific'][business_type]['max_deduction']
            )          
            deductions.append(deduction)
            deduction_details.append(f"积分营销扣分: {deduction} (匹配词: {', '.join(points_marketing_keywords) }, 匹配数量: {points_marketing_keywords_count})")
        # print(deduction_details)

        # 检查积分到期关键词
        points_expiry_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['POINTS_EXPIRY']['keywords'] if k in cleaned_content]
        points_expiry_keywords_count = len(points_expiry_keywords)
        if points_expiry_keywords_count > 0:
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['POINTS_EXPIRY']['business_specific'][business_type]['score'] * points_expiry_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['POINTS_EXPIRY']['business_specific'][business_type]['max_deduction']
            )           
            deductions.append(deduction)
            deduction_details.append(f"积分到期扣分: {deduction} (匹配词: {', '.join(points_expiry_keywords) }, 匹配数量: {points_expiry_keywords_count})")
        

        # 检查招生相关关键词
        admissions_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['ADMISSIONS']['keywords'] if k in cleaned_content]
        admissions_keywords_count = len(admissions_keywords)
        if admissions_keywords_count > 0:
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['ADMISSIONS']['business_specific'][business_type]['score'] * admissions_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['ADMISSIONS']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"招生相关扣分: {deduction} (匹配词: {', '.join(admissions_keywords) }, 匹配数量: {admissions_keywords_count})")
        
        #年报关键词
        annual_report_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['ANNUAL_REPORT']['keywords'] if k in cleaned_content]
        annual_report_keywords_count = len(annual_report_keywords)
        if annual_report_keywords_count > 0:
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['ANNUAL_REPORT']['business_specific'][business_type]['score'] * annual_report_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['ANNUAL_REPORT']['business_specific'][business_type]['max_deduction']
            )   
            deductions.append(deduction)
            deduction_details.append(f"年报关键词扣分: {deduction} (匹配词: {', '.join(annual_report_keywords) }, 匹配数量: {annual_report_keywords_count})")

        # 检查平台关键词
        platform_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['PLATFORM']['keywords'] if k in cleaned_content]
        platform_keywords_count = len(platform_keywords)
        if platform_keywords_count > 0:
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['PLATFORM']['business_specific'][business_type]['score'] * platform_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['PLATFORM']['business_specific'][business_type]['max_deduction']
            )
            
            deductions.append(deduction)
            deduction_details.append(f"平台关键词扣分: {deduction} (匹配词: {', '.join(platform_keywords) }, 匹配数量: {platform_keywords_count})")

        # 行业通知检查催收关键词
        collection_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['PAYMENT_REMINDER']['keywords'] if k in cleaned_content]
        collection_keywords_count = len(collection_keywords)
        if collection_keywords_count > 0:
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['PAYMENT_REMINDER']['business_specific'][business_type]['score'] * collection_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['PAYMENT_REMINDER']['business_specific'][business_type]['max_deduction']
            )

            deductions.append(deduction)
            deduction_details.append(f"行业催支付关键词扣分: {deduction} (匹配词: {', '.join(collection_keywords) }, 匹配数量: {collection_keywords_count})")

               
        # 验证直播相关内容
        live_streaming_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['LIVE_STREAMING']['keywords'] if k in cleaned_content]
        live_streaming_keywords_count = len(live_streaming_keywords)
        if live_streaming_keywords_count > 0:
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['LIVE_STREAMING']['business_specific'][business_type]['score'] * live_streaming_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['LIVE_STREAMING']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"直播相关内容扣分: {deduction} (匹配词: {', '.join(live_streaming_keywords) }, 匹配数量: {live_streaming_keywords_count})")
                
        # 检查微信公众号关键词
        wechat_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['WECHAT']['keywords'] if k in cleaned_content]
        wechat_keywords_count = len(wechat_keywords)
        if wechat_keywords_count > 0:
            
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['WECHAT']['business_specific'][business_type]['score'] * wechat_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['WECHAT']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"微信公众号关键词扣分: {deduction} (匹配词: {', '.join(wechat_keywords) }, 匹配数量: {wechat_keywords_count})")
            
            
        # 检查招聘相关词
        recruitment_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['RECRUITMENT']['keywords'] if k in cleaned_content]
        recruitment_keywords_count = len(recruitment_keywords)
        if recruitment_keywords_count > 0:
            # 修正：使用max而非min来应用扣分上限
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['RECRUITMENT']['business_specific'][business_type]['score'] * recruitment_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['RECRUITMENT']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"招聘关键词扣分: {deduction} (匹配词: {', '.join(recruitment_keywords) }, 匹配数量: {recruitment_keywords_count})")

        # 检查会议相关词
        meeting_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['MEETING']['keywords'] if k in cleaned_content]
        meeting_keywords_count = len(meeting_keywords)
        if meeting_keywords_count > 0:
            # 修正：使用max而非min来应用扣分上限
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['MEETING']['business_specific'][business_type]['score'] * meeting_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['MEETING']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"会议关键词扣分: {deduction} (匹配词: {', '.join(meeting_keywords) }, 匹配数量: {meeting_keywords_count})")

        # 检查交友相关词
        dating_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['DATING']['keywords'] if k in cleaned_content]
        dating_keywords_count = len(dating_keywords)
        if dating_keywords_count > 0:
            # 修正：使用max而非min来应用扣分上限
            if business_type in self.SCORE_RULES['DEDUCTIONS']['DATING'].get('business_specific', {}):
                deduction = max(
                    self.SCORE_RULES['DEDUCTIONS']['DATING']['business_specific'][business_type]['score'] * dating_keywords_count,
                    self.SCORE_RULES['DEDUCTIONS']['DATING']['business_specific'][business_type]['max_deduction']
                )
            deductions.append(deduction)
            deduction_details.append(f"交友关键词扣分: {deduction} (匹配词: {', '.join(dating_keywords) }, 匹配数量: {dating_keywords_count})")    

        # 检查征兵相关词
        military_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['MILITARY']['keywords'] if k in cleaned_content]
        military_keywords_count = len(military_keywords)
        if military_keywords_count > 0:
            # 修正：使用max而非min来应用扣分上限
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['MILITARY']['business_specific'][business_type]['score'] * military_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['MILITARY']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"征兵关键词扣分: {deduction} (匹配词: {', '.join(military_keywords) }, 匹配数量: {military_keywords_count})")

        # 检查教育营销相关词
        education_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['EDUCATION']['keywords'] if k in cleaned_content]
        education_keywords_count = len(education_keywords)
        if education_keywords_count > 0:
            # 修正：使用max而非min来应用扣分上限
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['EDUCATION']['business_specific'][business_type]['score'] * education_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['EDUCATION']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"教育营销关键词扣分: {deduction} (匹配词: {', '.join(education_keywords) }, 匹配数量: {education_keywords_count})")
                    
        # 检查地址
        has_address, address_score, detected_addresses = self._contains_address(cleaned_content)
        if has_address:
            # 修正：使用max而非min来实现扣分上限
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['ADDRESS']['business_specific'][business_type]['score'] * address_score,
                self.SCORE_RULES['DEDUCTIONS']['ADDRESS']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            address_info = ", ".join(detected_addresses) if detected_addresses else f"地址特征分数: {address_score}"
            deduction_details.append(f"地址扣分: {deduction} ({address_info})")

        # 检查展会相关词
        exhibition_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['EXHIBITION']['keywords'] if k in cleaned_content]
        exhibition_keywords_count = len(exhibition_keywords)
        if exhibition_keywords_count > 0:
            # 使用max应用扣分上限
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['EXHIBITION']['business_specific'][business_type]['score'] * exhibition_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['EXHIBITION']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"展会关键词扣分: {deduction} (匹配词: {', '.join(exhibition_keywords) }, 匹配数量: {exhibition_keywords_count})")
        
        # 检查黄金珠宝相关词
        jewelry_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['JEWELRY']['keywords'] if k in cleaned_content]
        jewelry_keywords_count = len(jewelry_keywords)
        if jewelry_keywords_count > 0:
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['JEWELRY']['business_specific'][business_type]['score'] * jewelry_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['JEWELRY']['business_specific'][business_type]['max_deduction']
            )               
            deductions.append(deduction)
            deduction_details.append(f"黄金珠宝关键词扣分: {deduction} (匹配词: {', '.join(jewelry_keywords) }, 匹配数量: {jewelry_keywords_count})")
        
        # 检查酒水相关词
        liquor_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['LIQUOR']['keywords'] if k in cleaned_content]
        liquor_keywords_count = len(liquor_keywords)
        if liquor_keywords_count > 0:
            # 使用行业-通知的规则
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['LIQUOR']['business_specific'][business_type]['score'] * liquor_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['LIQUOR']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"酒水关键词扣分: {deduction} (匹配词: {', '.join(liquor_keywords) }, 匹配数量: {liquor_keywords_count})")

        # 检查医疗相关词
        medical_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['MEDICAL']['keywords'] if k in cleaned_content]
        medical_keywords_count = len(medical_keywords)
        if medical_keywords_count > 0:
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['MEDICAL']['business_specific'][business_type]['score'] * medical_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['MEDICAL']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"医疗关键词扣分: {deduction} (匹配词: {', '.join(medical_keywords) }, 匹配数量: {medical_keywords_count})")

        # 检查游戏相关词
        game_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['GAME']['keywords'] if k in cleaned_content]
        game_keywords_count = len(game_keywords)
        if game_keywords_count > 0:
            # 使用行业-通知规则如果适用
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['GAME']['business_specific'][business_type]['score'] * game_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['GAME']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"游戏关键词扣分: {deduction} (匹配词: {', '.join(game_keywords) }, 匹配数量: {game_keywords_count})")
           
        if business_type == "行业-物流":
            # 检查物流关键词并应用加分规则
            logistics_keywords = self.SCORE_RULES['BONUSES']['LOGISTICS']['keywords']
            logistics_keywords_count = len([k for k in logistics_keywords if k in cleaned_content])
            if logistics_keywords_count > 0:
                # 获取物流加分规则
                logistics_bonus = self.SCORE_RULES['BONUSES']['LOGISTICS']
                # 计算加分（每个匹配关键词加分）并应用上限
                bonus = max(
                    logistics_bonus['business_specific'][business_type]['score'] * logistics_keywords_count,
                    logistics_bonus['business_specific'][business_type]['max_bonus']
                )
                deductions.append(bonus)  # 加分项
                deduction_details.append(f"物流关键词加分: +{bonus} (匹配词: {', '.join(logistics_keywords) }, 匹配数量: {logistics_keywords_count})")
            else:
                # 如果没有物流关键词，则扣分
                deduction = -30
                deductions.append(deduction)
                deduction_details.append("缺少物流关键词扣分: -30")

                          
        # 累加所有扣分项
        total_deductions = sum(deductions)  
        final_score = base_score + total_deductions
      
        # 更新评分详情
        self.score_details['deduction_details'] = deduction_details
        self.score_details['final_score'] = final_score
        self.score_details['base_score'] = base_score

        # 判断是否通过
        passed = final_score >= self.SCORE_RULES['PASS_SCORE']['行业'][business_type]
        if passed:
            reasons = [
                f"基础分: {base_score}",
                f"总分: {final_score}",
                f"扣分明细: {'; '.join(deduction_details)}"
            ]
            return True, f"审核通过 ({', '.join(reasons)})"
        else:
            reasons = [
                f"基础分: {base_score}",
                f"总分: {final_score}",
                f"扣分明细:{', '.join(deduction_details)}"  
            ]
            return False, f"审核不通过 ({', '.join(reasons)})"



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
        

         # 检查涉黄关键词
        pornographic_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['PORNOGRAPHIC']['keywords'] if k in cleaned_content]
        pornographic_keywords_count = len(pornographic_keywords)
        if pornographic_keywords_count > 0:
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['PORNOGRAPHIC']['business_specific'][business_type]['score'] * pornographic_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['PORNOGRAPHIC']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"涉黄扣分: {deduction} (匹配词: {', '.join(pornographic_keywords) }, 匹配数量: {pornographic_keywords_count})")   
        
        # 检查涉诈关键词
        fraud_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['FRAUD']['keywords'] if k in cleaned_content]
        fraud_keywords_count = len(fraud_keywords)
        if fraud_keywords_count > 0:
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['FRAUD']['business_specific'][business_type]['score'] * fraud_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['FRAUD']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"涉诈扣分: {deduction} (匹配词: {', '.join(fraud_keywords) }, 匹配数量: {fraud_keywords_count})") 
        

        # 应用特定签名加分
        app_signature_keywords = [k for k in self.SCORE_RULES['BONUSES']['APP_SIGNATURE']['keywords'] if k in cleaned_signature]
        app_signature_keywords_count = len(app_signature_keywords)
        if app_signature_keywords_count > 0:
            bonus = min(self.SCORE_RULES['BONUSES']['APP_SIGNATURE']['score'] * app_signature_keywords_count, 
                        self.SCORE_RULES['BONUSES']['APP_SIGNATURE']['max_bonus'])
            deductions.append(bonus)  # 加分项           
            deduction_details.append(f"特定关键词签名加分: +{bonus} (匹配关键词: {', '.join(app_signature_keywords)})")
        
        
        # 应用特定关键词签名加
        gov_signature_keywords = [k for k in self.SCORE_RULES['BONUSES']['GOV_SIGNATURE']['keywords'] if k in cleaned_signature]
        gov_signature_keywords_count = len(gov_signature_keywords)
        if gov_signature_keywords_count > 0:  
            bonus = min(self.SCORE_RULES['BONUSES']['GOV_SIGNATURE']['score'] * gov_signature_keywords_count, 
                        self.SCORE_RULES['BONUSES']['GOV_SIGNATURE']['max_bonus'])
            deductions.append(bonus)  # 加分项           
            deduction_details.append(f"特定关键词签名加分: +{bonus} (匹配关键词: {', '.join(gov_signature_keywords)})")
            
        # 检查私人号码
        has_private_number, private_numbers = self._contains_private_number(cleaned_content)
        if has_private_number:
            # 对于零容忍项，直接返回失败
            # deduction_details.append(f"私人号码违规: 拒绝通过 (检测到: {', '.join(private_numbers)})")
            return False, f"审核不通过 (原因: 含有私人号码: {', '.join(private_numbers)}) (基础分: 100, 总分: 0)"

        # # 检测链接（提前检测以便后续共现规则使用）
        # has_link, link_count = self._contains_link(cleaned_content)
        # if has_link:
        #     link_deduction = self.SCORE_RULES['DEDUCTIONS']['LINK']['business_specific'][business_type]['score'] * link_count
        #     # 使用max确保不超过最大扣分限制
        #     link_deduction = max(link_deduction, self.SCORE_RULES['DEDUCTIONS']['LINK']['business_specific'][business_type]['max_deduction'])
        #     deductions.append(link_deduction)
        #     deduction_details.append(f"链接扣分: {link_deduction} (链接数量: {link_count})")

        # 检查固定电话
        has_fixed_phone, fixed_phone_count, fixed_phone_numbers = self._contains_fixed_phone(cleaned_content)
        if has_fixed_phone:
            # 计算扣分
            phone_deduction = self.SCORE_RULES['DEDUCTIONS']['FIXED_PHONE']['business_specific'][business_type]['score'] * fixed_phone_count
            # 使用max确保不超过最大扣分限制
            phone_deduction = max(phone_deduction, self.SCORE_RULES['DEDUCTIONS']['FIXED_PHONE']['business_specific'][business_type]['max_deduction'])            
            deductions.append(phone_deduction)
            deduction_details.append(f"固定电话扣分: {phone_deduction} (检测到: {', '.join(fixed_phone_numbers)})")
        
        
        # # 检查营销关键词
        # marketing_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['MARKETING']['keywords'] if k in cleaned_content]
        # marketing_keywords_count = len(marketing_keywords)        
        # if marketing_keywords_count > 0:      
        #     deduction = max(
        #         self.SCORE_RULES['DEDUCTIONS']['MARKETING']['business_specific'][business_type]['score'] * marketing_keywords_count,
        #         self.SCORE_RULES['DEDUCTIONS']['MARKETING']['business_specific'][business_type]['max_deduction']
        #     )           
        #     deductions.append(deduction)
        #     deduction_details.append(f"\n营销关键词扣分: {deduction} (匹配词: {', '.join(marketing_keywords) }, 匹配数量: {marketing_keywords_count})")        


        # 检查会员积分营销关键词
        points_marketing_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['POINTS_MARKETING']['keywords'] if k in cleaned_content]
        points_marketing_keywords_count = len(points_marketing_keywords)
        if points_marketing_keywords_count > 0:
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['POINTS_MARKETING']['business_specific'][business_type]['score'] * points_marketing_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['POINTS_MARKETING']['business_specific'][business_type]['max_deduction']
            )          
            deductions.append(deduction)
            deduction_details.append(f"会员积分营销扣分: {deduction} (匹配词: {', '.join(points_marketing_keywords) }, 匹配数量: {points_marketing_keywords_count})")
        # print(deduction_details)

        # 检查积分到期关键词
        points_expiry_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['POINTS_EXPIRY']['keywords'] if k in cleaned_content]
        points_expiry_keywords_count = len(points_expiry_keywords)
        if points_expiry_keywords_count > 0:
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['POINTS_EXPIRY']['business_specific'][business_type]['score'] * points_expiry_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['POINTS_EXPIRY']['business_specific'][business_type]['max_deduction']
            )           
            deductions.append(deduction)
            deduction_details.append(f"积分到期扣分: {deduction} (匹配词: {', '.join(points_expiry_keywords) }, 匹配数量: {points_expiry_keywords_count})")
        
        
        # 检查招生相关关键词
        admissions_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['ADMISSIONS']['keywords'] if k in cleaned_content]
        admissions_keywords_count = len(admissions_keywords)
        if admissions_keywords_count > 0:
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['ADMISSIONS']['business_specific'][business_type]['score'] * admissions_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['ADMISSIONS']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"招生相关扣分: {deduction} (匹配词: {', '.join(admissions_keywords) }, 匹配数量: {admissions_keywords_count})")
        
        #年报关键词
        annual_report_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['ANNUAL_REPORT']['keywords'] if k in cleaned_content]
        annual_report_keywords_count = len(annual_report_keywords)
        if annual_report_keywords_count > 0:
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['ANNUAL_REPORT']['business_specific'][business_type]['score'] * annual_report_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['ANNUAL_REPORT']['business_specific'][business_type]['max_deduction']
            )   
            deductions.append(deduction)
            deduction_details.append(f"年报关键词扣分: {deduction} (匹配词: {', '.join(annual_report_keywords) }, 匹配数量: {annual_report_keywords_count})")

        # 检查平台关键词
        platform_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['PLATFORM']['keywords'] if k in cleaned_content]
        platform_keywords_count = len(platform_keywords)
        if platform_keywords_count > 0:
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['PLATFORM']['business_specific'][business_type]['score'] * platform_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['PLATFORM']['business_specific'][business_type]['max_deduction']
            )
            
            deductions.append(deduction)
            deduction_details.append(f"平台关键词扣分: {deduction} (匹配词: {', '.join(platform_keywords) }, 匹配数量: {platform_keywords_count})")

               
        # 验证直播相关内容
        live_streaming_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['LIVE_STREAMING']['keywords'] if k in cleaned_content]
        live_streaming_keywords_count = len(live_streaming_keywords)
        if live_streaming_keywords_count > 0:
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['LIVE_STREAMING']['business_specific'][business_type]['score'] * live_streaming_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['LIVE_STREAMING']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"直播相关内容扣分: {deduction} (匹配词: {', '.join(live_streaming_keywords) }, 匹配数量: {live_streaming_keywords_count})")
                
        # 检查微信公众号关键词
        wechat_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['WECHAT']['keywords'] if k in cleaned_content]
        wechat_keywords_count = len(wechat_keywords)
        if wechat_keywords_count > 0:
            
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['WECHAT']['business_specific'][business_type]['score'] * wechat_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['WECHAT']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"微信公众号关键词扣分: {deduction} (匹配词: {', '.join(wechat_keywords) }, 匹配数量: {wechat_keywords_count})")
            
            
        # 检查招聘相关词
        recruitment_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['RECRUITMENT']['keywords'] if k in cleaned_content]
        recruitment_keywords_count = len(recruitment_keywords)
        if recruitment_keywords_count > 0:
            # 修正：使用max而非min来应用扣分上限
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['RECRUITMENT']['business_specific'][business_type]['score'] * recruitment_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['RECRUITMENT']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"招聘关键词扣分: {deduction} (匹配词: {', '.join(recruitment_keywords) }, 匹配数量: {recruitment_keywords_count})")

        # 检查会议相关词
        meeting_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['MEETING']['keywords'] if k in cleaned_content]
        meeting_keywords_count = len(meeting_keywords)
        if meeting_keywords_count > 0:
            # 修正：使用max而非min来应用扣分上限
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['MEETING']['business_specific'][business_type]['score'] * meeting_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['MEETING']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"会议关键词扣分: {deduction} (匹配词: {', '.join(meeting_keywords) }, 匹配数量: {meeting_keywords_count})")

        # 检查交友相关词
        dating_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['DATING']['keywords'] if k in cleaned_content]
        dating_keywords_count = len(dating_keywords)
        if dating_keywords_count > 0:
            # 修正：使用max而非min来应用扣分上限
            if business_type in self.SCORE_RULES['DEDUCTIONS']['DATING'].get('business_specific', {}):
                deduction = max(
                    self.SCORE_RULES['DEDUCTIONS']['DATING']['business_specific'][business_type]['score'] * dating_keywords_count,
                    self.SCORE_RULES['DEDUCTIONS']['DATING']['business_specific'][business_type]['max_deduction']
                )
            deductions.append(deduction)
            deduction_details.append(f"交友关键词扣分: {deduction} (匹配词: {', '.join(dating_keywords) }, 匹配数量: {dating_keywords_count})")    

        # 检查征兵相关词
        military_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['MILITARY']['keywords'] if k in cleaned_content]
        military_keywords_count = len(military_keywords)
        if military_keywords_count > 0:
            # 修正：使用max而非min来应用扣分上限
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['MILITARY']['business_specific'][business_type]['score'] * military_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['MILITARY']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"征兵关键词扣分: {deduction} (匹配词: {', '.join(military_keywords) }, 匹配数量: {military_keywords_count})")

        # 检查教育营销相关词
        education_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['EDUCATION']['keywords'] if k in cleaned_content]
        education_keywords_count = len(education_keywords)
        if education_keywords_count > 0:
            # 修正：使用max而非min来应用扣分上限
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['EDUCATION']['business_specific'][business_type]['score'] * education_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['EDUCATION']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"教育营销关键词扣分: {deduction} (匹配词: {', '.join(education_keywords) }, 匹配数量: {education_keywords_count})")
                    
        # 检查地址
        has_address, address_score, detected_addresses = self._contains_address(cleaned_content)
        if has_address:
            # 修正：使用max而非min来实现扣分上限
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['ADDRESS']['business_specific'][business_type]['score'] * address_score,
                self.SCORE_RULES['DEDUCTIONS']['ADDRESS']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            address_info = ", ".join(detected_addresses) if detected_addresses else f"地址特征分数: {address_score}"
            deduction_details.append(f"地址扣分: {deduction} ({address_info})")

        # 检查展会相关词
        exhibition_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['EXHIBITION']['keywords'] if k in cleaned_content]
        exhibition_keywords_count = len(exhibition_keywords)
        if exhibition_keywords_count > 0:
            # 使用max应用扣分上限
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['EXHIBITION']['business_specific'][business_type]['score'] * exhibition_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['EXHIBITION']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"展会关键词扣分: {deduction} (匹配词: {', '.join(exhibition_keywords) }, 匹配数量: {exhibition_keywords_count})")
        
        # 检查黄金珠宝相关词
        jewelry_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['JEWELRY']['keywords'] if k in cleaned_content]
        jewelry_keywords_count = len(jewelry_keywords)
        if jewelry_keywords_count > 0:
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['JEWELRY']['business_specific'][business_type]['score'] * jewelry_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['JEWELRY']['business_specific'][business_type]['max_deduction']
            )               
            deductions.append(deduction)
            deduction_details.append(f"黄金珠宝关键词扣分: {deduction} (匹配词: {', '.join(jewelry_keywords) }, 匹配数量: {jewelry_keywords_count})")
        
        # 检查酒水相关词
        liquor_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['LIQUOR']['keywords'] if k in cleaned_content]
        liquor_keywords_count = len(liquor_keywords)
        if liquor_keywords_count > 0:
            # 使用行业-通知的规则
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['LIQUOR']['business_specific'][business_type]['score'] * liquor_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['LIQUOR']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"酒水关键词扣分: {deduction} (匹配词: {', '.join(liquor_keywords) }, 匹配数量: {liquor_keywords_count})")

        # 检查医疗相关词
        medical_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['MEDICAL']['keywords'] if k in cleaned_content]
        medical_keywords_count = len(medical_keywords)
        if medical_keywords_count > 0:
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['MEDICAL']['business_specific'][business_type]['score'] * medical_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['MEDICAL']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"医疗关键词扣分: {deduction} (匹配词: {', '.join(medical_keywords) }, 匹配数量: {medical_keywords_count})")

        # 检查游戏相关词
        game_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['GAME']['keywords'] if k in cleaned_content]
        game_keywords_count = len(game_keywords)
        if game_keywords_count > 0:
            # 使用行业-通知规则如果适用
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['GAME']['business_specific'][business_type]['score'] * game_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['GAME']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"游戏关键词扣分: {deduction} (匹配词: {', '.join(game_keywords) }, 匹配数量: {game_keywords_count})")
           
        if business_type == "行业-物流":
            # 检查物流关键词并应用加分规则
            logistics_keywords = self.SCORE_RULES['BONUSES']['LOGISTICS']['keywords']
            logistics_keywords_count = len([k for k in logistics_keywords if k in cleaned_content])
            if logistics_keywords_count > 0:
                # 获取物流加分规则
                logistics_bonus = self.SCORE_RULES['BONUSES']['LOGISTICS']
                # 计算加分（每个匹配关键词加分）并应用上限
                bonus = max(
                    logistics_bonus['business_specific'][business_type]['score'] * logistics_keywords_count,
                    logistics_bonus['business_specific'][business_type]['max_bonus']
                )
                deductions.append(bonus)  # 加分项
                deduction_details.append(f"物流关键词加分: +{bonus} (匹配词: {', '.join(logistics_keywords) }, 匹配数量: {logistics_keywords_count})")
            else:
                # 如果没有物流关键词，则扣分
                deduction = -30
                deductions.append(deduction)
                deduction_details.append("缺少物流关键词扣分: -30")

                          
        # 累加所有扣分项
        total_deductions = sum(deductions)  
        final_score = base_score + total_deductions
      
        # 更新评分详情
        self.score_details['deduction_details'] = deduction_details
        self.score_details['final_score'] = final_score
        self.score_details['base_score'] = base_score

        # 判断是否通过
        passed = final_score >= self.SCORE_RULES['PASS_SCORE']['会销'][business_type]
        if passed:
            reasons = [
                f"基础分: {base_score}",
                f"总分: {final_score}",
                f"扣分明细: {'; '.join(deduction_details)}"
            ]
            return True, f"审核通过 ({', '.join(reasons)})"
        else:
            reasons = [
                f"基础分: {base_score}",
                f"总分: {final_score}",
                f"扣分明细:{', '.join(deduction_details)}"  
            ]
            return False, f"审核不通过 ({', '.join(reasons)})"

    def _score_collection(self, business_type: str, cleaned_content: str, cleaned_signature: str) -> Tuple[bool, str]:
        """
        催收类短信的评分实现
        
        Args:
            cleaned_content: 已清理的短信内容
            
        Returns:
            Tuple[bool, str]: (是否通过验证, 验证结果说明)
        """
        # 基础分数
        base_score = self.SCORE_RULES['BASE_SCORE']['拉新']['拉新-催收']
        business_type = '拉新-催收'  # 这里确定业务类型
        
        # 收集扣分项而非直接累加
        deductions = []
        deduction_details = []
        
        # 检查私人号码
        has_private_number, private_numbers = self._contains_private_number(cleaned_content)
        if has_private_number:
            return False, f"审核不通过 (原因: 含有私人号码: {', '.join(private_numbers)}) (基础分: 100, 总分: 0)"

        # # 检测链接（提前检测以便后续共现规则使用）
        # has_link, link_count = self._contains_link(cleaned_content)
        # if has_link:
        #     link_deduction = self.SCORE_RULES['DEDUCTIONS']['LINK']['business_specific'][business_type]['score'] * link_count
        #     # 使用max确保不超过最大扣分限制
        #     link_deduction = max(link_deduction, self.SCORE_RULES['DEDUCTIONS']['LINK']['business_specific'][business_type]['max_deduction'])
        #     deductions.append(link_deduction)
        #     deduction_details.append(f"链接扣分: {link_deduction} (链接数量: {link_count})")

        # 检查固定电话
        has_fixed_phone, fixed_phone_count, fixed_phone_numbers = self._contains_fixed_phone(cleaned_content)
        if has_fixed_phone:
            # 计算扣分
            phone_deduction = self.SCORE_RULES['DEDUCTIONS']['FIXED_PHONE']['business_specific'][business_type]['score'] * fixed_phone_count
            # 使用max确保不超过最大扣分限制
            phone_deduction = max(phone_deduction, self.SCORE_RULES['DEDUCTIONS']['FIXED_PHONE']['business_specific'][business_type]['max_deduction'])            
            deductions.append(phone_deduction)
            deduction_details.append(f"固定电话扣分: {phone_deduction} (检测到: {', '.join(fixed_phone_numbers)})")


        # 检查催收关键词
        collection_keywords = [k for k in self.SCORE_RULES['DEDUCTIONS']['COLLECTION']['keywords'] if k in cleaned_content]
        collection_keywords_count = len(collection_keywords)
        if collection_keywords_count > 0:
            deduction = max(
                self.SCORE_RULES['DEDUCTIONS']['COLLECTION']['business_specific'][business_type]['score'] * collection_keywords_count,
                self.SCORE_RULES['DEDUCTIONS']['COLLECTION']['business_specific'][business_type]['max_deduction']
            )
            deductions.append(deduction)
            deduction_details.append(f"\n催收关键词扣分: {deduction} (匹配词: {', '.join(collection_keywords)}, 匹配数量: {collection_keywords_count})")


        # 累加所有扣分项
        total_deductions = sum(deductions)  
        final_score = base_score + total_deductions
        # 更新评分详情
        self.score_details['deductions'] = deduction_details
        self.score_details['final_score'] = final_score
        self.score_details['base_score'] = base_score
        
        # 判断是否通过
        passed = final_score >= self.SCORE_RULES['PASS_SCORE']['拉新'][business_type]
        if passed:
            reasons = [
                f"基础分: {base_score}",
                f"总分: {final_score:.2f}",
                f"扣分明细: {'; '.join(deduction_details)}"
            ]
            return True, f"审核通过 (原因: {', '.join(reasons)})"
        else:
            reasons = [
                f"基础分: {base_score}",
                f"总分: {final_score}",
                f"扣分明细:{', '.join(deduction_details)}"  
            ]
            return False, f"审核不通过 (原因: {', '.join(reasons)})"




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
        # 繁体字转换为简体字
        content = convert(content, 'zh-hans')  # 将繁体字转换为简体字
        # 2. 空白字符处理
        content = re.sub(r'[\s\u3000]+', '', content)  # 替换所有类型的空格
        content = re.sub(r'[\n\r]+', '', content)      # 替换所有换行符
        
        # 3. 标点符号处理
        content = re.sub(r'[-‐‑‒–—―]+', '', content)   # 替换所有类型的破折号
        content = re.sub(r'["""''′`´]+', '', content)  # 替换所有类型的引号
        content = re.sub(r'[()（）[\]【】{}「」『』]+', '', content)  # 替换所有类型的括号

        # 4. 重复标点处理
        content = re.sub(r'[,。，、!！?？~～]+', lambda m: m.group()[0], content)
         
       
        return content


    def _contains_address(self, text: str) -> Tuple[bool, int, List[str]]:
        """
        使用cpca库检测文本中是否包含详细地址
        
        Args:
            text: 待检查的文本
            
        Returns:
            Tuple[bool, int, List[str]]: (是否包含地址, 地址特征数量, 检测到的地址列表)
        """

        #使用结巴分词进行词性标注，处理易误识别的地名
        #只保留名词(n)、地名(ns)、数字(m)和量词(q)，过滤掉其他词性的词语
        words_pos = pseg.cut(text)
        processed_parts = []
        for word, flag in words_pos:  
            if flag.startswith('n') or flag == 'ns':
                processed_parts.append(word)
            elif flag == 'm' or flag == 'q':
                processed_parts.append(word)
        
        text = ''.join(processed_parts)


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
        

    def _contains_private_number(self, text: str) -> Tuple[bool, List[str]]:
        """
        检查文本中是否包含私人手机号码
        
        Args:
            text: 待检查的文本
            
        Returns:
            Tuple[bool, List[str]]: (是否包含私人号码, 匹配到的号码列表)
        """
        pattern = r'1[3-9]\d{9}|1[3-9]\d{4}[ -]\d{4}|1[3-9][ -]\d{4}[ -]\d{4}'
        matches = re.findall(pattern, text)
        return bool(matches), matches

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
    
    # def _contains_link(self, text: str) -> Tuple[bool, int]:
    #     """
    #     使用正则表达式检查文本中是否包含链接
        
    #     Args:
    #         text: 待检查的文本
            
    #     Returns:
    #         Tuple[bool, int]: (是否包含链接, 链接数量)
    #     """
    #     # 定义链接匹配模式
    #     url_patterns = [
    #         # 标准URL格式（支持更多协议）
    #         r'(?:https?|ftp|file|ws|wss)://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*',
            
    #         # 带www的网址（支持更多子域名）
    #         r'(?:www|wap|m)\.(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*',
            
    #         # 常见顶级域名格式（扩展域名列表）
    #         r'(?:[-\w.]|(?:%[\da-fA-F]{2}))+\.(?:com|cn|net|org|gov|edu|io|app|xy≠|top|me|tv|cc|shop|vip|ltd|store|online|tech|site|wang|cloud|link|live|work|game|fun|art|xin|ren|space|team|news|law|group|center|city|world|life|co|red|mobi|pro|info|name|biz|asia|tel|club|social|video|press|company|website|email|network|studio|design|software|blog|wiki|forum|run|zone|plus|cool|show|gold|today|market|business|company|zone|media|agency|directory|technology|solutions|international|enterprises|industries|management|consulting|services)(?:/[^\s]*)?',
            
    #         # 短链接格式（扩展常见短链接服务）
    #         r'(?:t|u|dwz|url|c|s|m|j|h5|v|w)\.(?:cn|com|me|ly|gl|gd|ink|run|app|fun|pub|pro|vip|cool|link|live|work|game|art|red|tel|club|show|gold|today)(?:/[-\w]+)+',
            
    #         # 特定平台短链接，包括淘宝、京东、饿了么、抖音、微博等
    #         r'(?:tb\.cn|jd\.com|ele\.me|douyin\.com|weibo\.com|qq\.com|taobao\.com|tmall\.com|pinduoduo\.com|kuaishou\.com|bilibili\.com|youku\.com|iqiyi\.com|meituan\.com|dianping\.com|alipay\.com|weixin\.qq\.com)/[-\w/]+',
            
    #         # IPv4地址格式
    #         r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?::\d{1,5})?(?:/[^\s]*)?',
            
    #         # IPv6地址格式
    #         r'(?:(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9]))(?::\d{1,5})?(?:/[^\s]*)?',
            
    #         # 带端口的IP地址格式
    #         r'(?:https?://)?(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?):\d{1,5}(?:/[^\s]*)?'
    #     ]
        
    #     # 合并所有模式
    #     combined_pattern = '|'.join(f'({pattern})' for pattern in url_patterns)
        
    #     # 查找所有匹配项
    #     matches = re.findall(combined_pattern, text, re.IGNORECASE)
        
    #     # 计算匹配数量（matches是一个元组列表，每个元组包含所有捕获组）
    #     link_count = sum(1 for match in matches if any(match))
        
    #     return link_count > 0, link_count

    def _contains_fixed_phone(self, text: str) -> Tuple[bool, int, List[str]]:
        """
        检查文本中是否包含固定电话号码
        
        Args:
            text: 待检查的文本
            
        Returns:
            Tuple[bool, int, List[str]]: (是否包含固定电话, 固定电话数量, 匹配到的电话号码列表)
        """
        # 匹配固定电话模式
        patterns = [
            r'\d{3,4}-\d{7,8}',  # 区号-号码格式
            r'\d{5,6}',          # 5-6位号码
            r'\d{7,8}',          # 纯7-8位号码
            r'\d{3,4}\s*\d{7,8}' # 区号和号码之间有空格
        ]
        
        # 合并所有模式
        combined_pattern = '|'.join(f'({pattern})' for pattern in patterns)
        
        # 查找所有匹配项
        matches = re.findall(combined_pattern, text)
        
        # 提取匹配到的电话号码
        phone_numbers = []
        for match in matches:
            # findall返回的是元组，需要找出非空元素
            for group in match:
                if group:
                    phone_numbers.append(group)
                    break
        
        # 计算匹配数量
        phone_count = len(phone_numbers)
        
        return phone_count > 0, phone_count, phone_numbers

    def _is_neutral_signature(self, cleaned_signature: str) -> bool:
        """
        检查签名是否为中性签名
        
        Args:
            signature: 短信签名
            
        Returns:
            bool: 是否为中性签名
        """
        return cleaned_signature in self.NEUTRAL_SIGNATURES

    
# # 定义有效的客户类型
# 客户类型 = ["云平台", "直客", "类直客", "渠道"]

# def validate_account_type(account_type: str) -> Tuple[bool, str]:
#     """
#     验证客户类型是否有效
    
#     Args:
#         account_type: 客户类型（如"云平台"、"直客"等）
        
#     Returns:
#         Tuple[bool, str]: (是否通过验证, 验证结果说明)
#     """
    
#     # 直客类型直接放行
#     if account_type == "直客":
#         return True, "直客类型直接通过"
        
#     return True, "客户类型有效"

def validate_business(business_type: str, content: str, signature: str, account_type: str = None) -> Tuple[bool, str]:
    """
    外部调用的主要入口函数，用于验证短信的业务类型是否合规
    """
    # # 1. 首先验证客户类型
    # account_valid, account_reason = validate_account_type(account_type)
    # if not account_valid:
    #     return False, account_reason
        
    # # 2. 如果是直客，直接返回通过
    # if account_type == "直客":
    #     return True, "直客类型直接通过"
    
    # 3. 检测双签名（多个【】）
    
    # 3.1 检测中文中括号对
    chinese_left_brackets = content.count('[')
    chinese_right_brackets = content.count(']')   
    if chinese_left_brackets > 0 or chinese_right_brackets > 0 :
        return False, "不允许使用中括号，(基础分: 0, 总分: 0)"
    
    half_left_brackets = content.count('「')
    half_right_brackets = content.count('」')   
    if half_left_brackets > 0 or half_right_brackets > 0 :
        return False, "不允许使用半角中括号，(基础分: 0, 总分: 0)"
    # 3.2 检测多个签名（多对【】）
    left_brackets = content.count('【')
    right_brackets = content.count('】')
    if left_brackets > 1 or right_brackets > 1:
        return False, "不允许多个签名，(基础分: 100, 总分: 0)"
    
    # 4. 清理内容和签名
    validator = BusinessValidator()
    cleaned_content = validator._clean_content(content)
    cleaned_signature = validator._clean_content(signature)
    
    # 5. 检查是否为中性签名，中性签名可直接失败
    if validator._is_neutral_signature(cleaned_signature):
        return False, "中性签名直接失败，(基础分: 100, 总分: 0)"
    
    # 6. 进行业务验证
    return validator._validate_business_internal(business_type, cleaned_content, cleaned_signature, account_type)
