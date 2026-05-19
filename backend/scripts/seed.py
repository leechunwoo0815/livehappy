"""Comprehensive test data seeder for LiveHappy platform.
Run: docker exec livehappy-backend python /app/scripts/seed.py
"""

import asyncio
import os
import uuid
from datetime import date, timedelta
from decimal import Decimal
from random import choice, randint

import bcrypt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DB_URL = "postgresql+asyncpg://stayhub:devpassword@postgres:5432/stayhub"


# ── Users ──────────────────────────────────────────────────────────
USERS = [
    # (username, email, password, role, score, bio, phone, nickname)
    (
        "admin",
        "admin@test.com",
        "admin123",
        "admin",
        9999,
        "平台超级管理员",
        "13800000001",
        "管理员",
    ),
    (
        "张明",
        "zhangming@test.com",
        "test123",
        "host",
        850,
        "资深房东，经营精品民宿5年",
        "13800000002",
        "张明",
    ),
    (
        "李华",
        "lihua@test.com",
        "test123",
        "host",
        920,
        "酒店管理专业，爱好旅行",
        "13800000003",
        "李华",
    ),
    (
        "王芳",
        "wangfang@test.com",
        "test123",
        "host",
        780,
        "设计师出身，专注特色民宿",
        "13800000004",
        "王芳",
    ),
    (
        "赵强",
        "zhaoqiang@test.com",
        "test123",
        "host",
        650,
        "退役厨师，经营美食主题民宿",
        "13800000005",
        "赵强",
    ),
    (
        "陈静",
        "chenjing@test.com",
        "test123",
        "host",
        890,
        "摄影师，房源照片都是自己拍的",
        "13800000006",
        "陈静",
    ),
    (
        "刘洋",
        "liuyang@test.com",
        "test123",
        "user",
        320,
        "背包客，走遍全国各地",
        "13800000007",
        "刘洋",
    ),
    (
        "孙丽",
        "sunli@test.com",
        "test123",
        "user",
        180,
        "白领，周末喜欢短途旅行",
        "13800000008",
        "孙丽",
    ),
    (
        "周伟",
        "zhouwei@test.com",
        "test123",
        "user",
        450,
        "程序员，远程办公到处旅居",
        "13800000009",
        "周伟",
    ),
    (
        "吴婷",
        "wuting@test.com",
        "test123",
        "user",
        280,
        "大学生，穷游爱好者",
        "13800000010",
        "吴婷",
    ),
    (
        "郑浩",
        "zhenghao@test.com",
        "test123",
        "user",
        150,
        "新手上路，请多关照",
        "13800000011",
        "郑浩",
    ),
    (
        "黄雨",
        "huangyu@test.com",
        "test123",
        "user",
        600,
        "旅行博主，分享真实住宿体验",
        "13800000012",
        "黄雨",
    ),
    (
        "林雪",
        "linxue@test.com",
        "test123",
        "user",
        390,
        "自由职业者，边工作边旅行",
        "13800000013",
        "林雪",
    ),
    (
        "何峰",
        "hefeng@test.com",
        "test123",
        "user",
        210,
        "退休教师，游山玩水",
        "13800000014",
        "何峰",
    ),
]

# ── Listings ───────────────────────────────────────────────────────
LISTINGS = [
    # (host_username, title, city, description, price, max_guests, bedrooms, bathrooms, status)
    (
        "张明",
        "西湖畔·湖景精品大床房",
        "杭州",
        "位于西湖核心景区，步行3分钟到断桥残雪。房间落地窗正对西湖，清晨看日出，傍晚赏夕阳。配备智能家居、高清投影、舒适大床。",
        588,
        2,
        1,
        1,
        "approved",
    ),
    (
        "张明",
        "龙井茶园·禅意山景房",
        "杭州",
        "隐匿在龙井茶园中的禅意空间，四周茶山环绕，空气清新。房间配有茶具和明前龙井，可品茶赏景。含双人早餐和茶园导览。",
        428,
        2,
        1,
        1,
        "approved",
    ),
    (
        "张明",
        "钱江新城·现代 loft",
        "杭州",
        "位于钱江新城CBD，200平 loft 空间，落地窗俯瞰钱塘江。配备开放式厨房、按摩浴缸、智能家居。适合商务出差或家庭出游。",
        888,
        4,
        2,
        2,
        "approved",
    ),
    (
        "李华",
        "故宫旁·胡同四合院雅居",
        "北京",
        "位于南锣鼓巷核心区，正宗北京四合院改造。朱门灰瓦，院内石榴树、金鱼缸。步行10分钟到故宫、景山公园。含老北京炸酱面早餐。",
        1288,
        4,
        2,
        1,
        "approved",
    ),
    (
        "李华",
        "三里屯·潮流设计师公寓",
        "北京",
        "设计师精心打造的 loft 空间，工业风与现代简约的完美结合。位于三里屯太古里旁，下楼就是网红餐厅和酒吧街。",
        698,
        2,
        1,
        1,
        "approved",
    ),
    (
        "李华",
        "长城脚下·山野木屋",
        "北京",
        "慕田峪长城脚下的独栋木屋，被原始森林环绕。有壁炉、露天温泉、星空观测台。含私厨定制晚餐和长城向导服务。",
        1688,
        6,
        3,
        2,
        "approved",
    ),
    (
        "王芳",
        "外滩景观·老洋房套房",
        "上海",
        "百年历史老洋房，保留原汁原味的 Art Deco 风格。推窗即见外滩万国建筑群和陆家嘴天际线。步行5分钟到南京路步行街。",
        988,
        3,
        2,
        1,
        "approved",
    ),
    (
        "王芳",
        "迪士尼旁·童话主题民宿",
        "上海",
        "距迪士尼乐园仅10分钟车程，整栋别墅带花园。每个房间都有不同的童话主题，适合家庭和亲子游。含迪士尼接送和儿童早餐。",
        788,
        6,
        3,
        2,
        "approved",
    ),
    (
        "王芳",
        "武康路·法式风情公寓",
        "上海",
        "武康路历史建筑中的法式公寓，原木地板、复古家具、落地窗。楼下是网红 café 和买手店，适合文艺青年。",
        558,
        2,
        1,
        1,
        "approved",
    ),
    (
        "赵强",
        "宽窄巷子·川味美食民宿",
        "成都",
        "宽窄巷子景区内的特色民宿，配备私人火锅厨房。房东是退役大厨，可预约川菜教学体验。赠送麻辣伴手礼一份。",
        458,
        4,
        2,
        1,
        "approved",
    ),
    (
        "赵强",
        "熊猫基地旁·亲子花园房",
        "成都",
        "距大熊猫繁育研究基地15分钟车程。独栋花园别墅，有儿童游乐区、宠物乐园和烧烤区。含熊猫玩偶和基地门票优惠。",
        628,
        6,
        3,
        2,
        "approved",
    ),
    (
        "赵强",
        "锦里古街·庭院套房",
        "成都",
        "锦里古街深处的静谧庭院，闹中取静。房间配有蜀绣装饰和智能马桶。可体验盖碗茶和变脸表演。",
        388,
        2,
        1,
        1,
        "approved",
    ),
    (
        "陈静",
        "秦始皇陵旁·秦风民宿",
        "西安",
        "距兵马俑博物馆仅5公里，以秦文化为主题的特色民宿。房间有仿秦壁画和陶俑装饰。含兵马俑门票预约和讲解服务。",
        358,
        2,
        1,
        1,
        "approved",
    ),
    (
        "陈静",
        "钟楼夜景·古城墙观景房",
        "西安",
        "位于西安古城墙内，顶楼露台可俯瞰钟楼和南门城墙。回民街步行3分钟，羊肉泡馍、凉皮应有尽有。",
        428,
        2,
        1,
        1,
        "approved",
    ),
    (
        "陈静",
        "大雁塔旁·唐风雅舍",
        "西安",
        "大唐不夜城核心区，唐风装修。汉服体验、唐诗抄写等文化活动免费参与。夜间可观大雁塔北广场音乐喷泉。",
        498,
        3,
        1,
        1,
        "approved",
    ),
    (
        "张明",
        "束河古镇·雪山观景客栈",
        "丽江",
        "束河古镇制高点，每个房间都能看到玉龙雪山。纳西族传统木结构建筑，庭院种满格桑花。含丽江古城接送。",
        468,
        2,
        1,
        1,
        "approved",
    ),
    (
        "张明",
        "泸沽湖畔·摩梭风情木屋",
        "丽江",
        "泸沽湖边的原生态木屋，推窗即湖景。体验摩梭族走婚文化、猪槽船游湖、篝火晚会。含早晚餐和环湖向导。",
        688,
        2,
        1,
        1,
        "approved",
    ),
    (
        "李华",
        "亚龙湾·海景度假别墅",
        "三亚",
        "亚龙湾一线海景别墅，私人泳池、椰林花园。步行2分钟到沙滩。含潜水体验和海鲜 BBQ 一次。",
        1688,
        8,
        4,
        3,
        "approved",
    ),
    (
        "李华",
        "海棠湾·无边泳池套房",
        "三亚",
        "海棠湾网红酒店式公寓，60平大套房带观海阳台。顶层无边泳池，俯瞰蜈支洲岛。含免税店95折券。",
        988,
        3,
        1,
        1,
        "approved",
    ),
    (
        "王芳",
        "鼓浪屿·百年别墅花园房",
        "厦门",
        "鼓浪屿上的百年华侨别墅，花园里种满三角梅和鸡蛋花。步行3分钟到海边。含钢琴博物馆门票和手绘地图。",
        558,
        2,
        1,
        1,
        "approved",
    ),
    (
        "王芳",
        "环岛路·海景文艺民宿",
        "厦门",
        "曾厝垵文创村的海景民宿，清新文艺风格。顶楼天台可看日落和星空。提供环岛路骑行自行车。",
        368,
        2,
        1,
        1,
        "approved",
    ),
    (
        "赵强",
        "八大关·欧式别墅套房",
        "青岛",
        "八大关风景区的德式老别墅，保留原装壁炉和彩色玻璃。步行5分钟到第二海水浴场。含啤酒博物馆门票。",
        628,
        4,
        2,
        1,
        "approved",
    ),
    (
        "赵强",
        "崂山脚下·茶园山居",
        "青岛",
        "崂山半山腰的茶园民宿，可体验采茶制茶。房间有山景落地窗和私人泡池。含崂山景区门票和登山向导。",
        538,
        2,
        1,
        1,
        "approved",
    ),
    (
        "陈静",
        "中山陵旁·民国公馆",
        "南京",
        "紫金山脚下的民国时期公馆，保留了原汁原味的中西合璧建筑风格。步行10分钟到中山陵、明孝陵。含南京特色早餐。",
        588,
        4,
        2,
        1,
        "approved",
    ),
    (
        "陈静",
        "夫子庙·秦淮河景房",
        "南京",
        "夫子庙秦淮河畔，推窗即见画舫游船。夜游秦淮、品尝鸭血粉丝汤和盐水鸭。含南京博物院预约服务。",
        428,
        2,
        1,
        1,
        "approved",
    ),
    (
        "张明",
        "洪崖洞旁·江景 loft",
        "重庆",
        "位于洪崖洞和解放碑之间，高空江景 loft。落地窗俯瞰长江和渝中半岛夜景。含火锅推荐清单和轻轨票。",
        498,
        4,
        2,
        1,
        "approved",
    ),
    (
        "李华",
        "大理古城·苍山洱海别墅",
        "大理",
        "大理古城南门旁的别墅，苍山洱海尽收眼底。庭院有无边水池和观景平台。含环洱海旅拍一次。",
        788,
        4,
        2,
        2,
        "approved",
    ),
    (
        "王芳",
        "喜洲古镇·白族民居",
        "大理",
        "喜洲古镇的白族传统三坊一照壁民居，由老宅改造。体验扎染、破酥粑粑制作。含洱海骑行路线图。",
        358,
        2,
        1,
        1,
        "approved",
    ),
    (
        "赵强",
        "漓江畔·山水画境民宿",
        "桂林",
        "阳朔遇龙河畔的山水民宿，落地窗外即是漓江山水。含竹筏漂流体验一次和印象刘三姐门票。",
        558,
        2,
        1,
        1,
        "approved",
    ),
    (
        "陈静",
        "西街·国际青年旅舍",
        "桂林",
        "阳朔西街旁的精品青旅，也有独立大床房。公共区域有台球桌和酒吧，适合结交各国朋友。含西街啤酒鱼推荐。",
        128,
        1,
        1,
        1,
        "approved",
    ),
    (
        "张明",
        "拙政园旁·苏式园林民宿",
        "苏州",
        "拙政园附近的苏式园林民宿，小桥流水、亭台楼阁。房间有雕花大床和刺绣床品。含苏州评弹体验券。",
        628,
        2,
        1,
        1,
        "approved",
    ),
    (
        "李华",
        "金鸡湖畔·现代湖景公寓",
        "苏州",
        "金鸡湖畔的高端湖景公寓，毗邻苏州中心和诚品书店。现代简约装修，配备全屋智能家居。",
        528,
        2,
        1,
        1,
        "approved",
    ),
    (
        "王芳",
        "橘子洲头·湘江夜景房",
        "长沙",
        "橘子洲头旁的高层公寓，正对岳麓山和湘江。房间有巨幅玻璃窗适合看夜景。含茶颜悦色券和文和友免排队券。",
        398,
        2,
        1,
        1,
        "approved",
    ),
    (
        "赵强",
        "五一广场·国金中心公寓",
        "长沙",
        "五一广场核心区，毗邻 IFS 国金中心。步行可达太平老街、坡子街。房间有 PS5 和投影仪。",
        468,
        3,
        1,
        1,
        "approved",
    ),
    (
        "陈静",
        "广州塔下·珠江夜景公寓",
        "广州",
        "广州塔旁的高层公寓，夜景一览无余。含广州塔观光门票优惠、珠江夜游船票。楼下就是 APM 线。",
        628,
        2,
        1,
        1,
        "approved",
    ),
    (
        "张明",
        "沙面·欧式复古套房",
        "广州",
        "沙面岛的欧式复古套房，保留民国时期建筑风格。周边多国领事馆旧址，适合拍照打卡。含早茶推荐和粤语体验课。",
        488,
        2,
        1,
        1,
        "approved",
    ),
    (
        "李华",
        "世界之窗旁·主题公寓",
        "深圳",
        "华侨城创意园内的设计师公寓，近世界之窗和欢乐谷。工业风装修，配备 Marshall 音箱和复古游戏机。",
        458,
        2,
        1,
        1,
        "approved",
    ),
    (
        "王芳",
        "中央大街·俄式风情房",
        "哈尔滨",
        "中央大街旁的俄式老建筑，保留百年木质楼梯和雕花天花板。步行5分钟到圣索菲亚大教堂。含马迭尔冰棍券和红肠礼盒。",
        358,
        2,
        1,
        1,
        "approved",
    ),
    (
        "赵强",
        "冰雪大世界·暖冬套房",
        "哈尔滨",
        "冰雪大世界附近的暖冬套房，地暖+壁炉双重供暖。含冰雪大世界门票和防寒装备租赁。",
        528,
        4,
        2,
        1,
        "approved",
    ),
    (
        "陈静",
        "大巴扎旁·维吾尔风情民宿",
        "乌鲁木齐",
        "国际大巴扎旁的维吾尔族特色民宿，房间有艾德莱斯绸装饰和手工地毯。含烤包子、大盘鸡推荐和天山天池拼团游。",
        328,
        2,
        1,
        1,
        "approved",
    ),
    (
        "张明",
        "八廓街·藏式阳光房",
        "拉萨",
        "八廓街附近的藏式民宿，阳光房可眺望布达拉宫。提供红景天茶和氧气瓶。含大昭寺门票和藏服体验。",
        488,
        2,
        1,
        1,
        "approved",
    ),
    (
        "张明",
        "嘉峪关·丝路驿站",
        "嘉峪关",
        "长城西端起点的丝路主题民宿。房间有驼铃、壁画等元素。含关城门票和沙漠露营体验。",
        298,
        2,
        1,
        1,
        "approved",
    ),
]

# ── Booking / Review content ──────────────────────────────────────
CHECKIN_DATES = [date(2026, 5, d) for d in range(1, 16)]
CHECKIN_DATES += [date(2026, 4, d) for d in range(1, 31)]
CHECKIN_DATES += [date(2026, 3, d) for d in range(1, 31)]
CHECKIN_DATES += [date(2026, 6, d) for d in range(1, 16)]

REVIEW_TEXTS = [
    "非常满意这次住宿！房间干净整洁，房东热情周到，位置也很方便。下次还会再来。",
    "超出预期！比照片上看起来还要好，细节做得很好。强烈推荐。",
    "环境很好，安静舒适。特别喜欢房子的装修风格，很有品味。",
    "房东非常友好，提前给我们发了详细的入住指南和周边推荐。体验很棒！",
    "性价比很高，这个价格能住到这样的房子真的很值。设施齐全，卫生状况良好。",
    "位置绝佳，出行方便。房间温馨舒适，床品很舒服，睡得很好。",
    "很有特色的民宿，和酒店完全不同的体验。下次来还会选择这里。",
    "整体不错，但还有一些细节可以改进。比如隔音效果一般，建议带上耳塞。",
    "完美的住宿体验！从入住到退房都很顺利。房东还送了欢迎水果，很贴心。",
    "房间比想象中小一点，但布置得很温馨。周边吃的很多，很方便。",
    "设施齐全，厨房用具很全，自己做了顿饭。像家一样的感觉。",
    "风景太美了！推窗就是美景，拍照根本停不下来。房东推荐的餐厅也很好吃。",
    "交通方便，离地铁站步行5分钟。适合来旅游的游客。",
    "卫生情况非常好，一尘不染。疫情期间住得很放心。",
    "房东很细心，准备了零食和饮料。房间也很暖和，冬天住很舒适。",
    "唯一不满的是热水不太稳定，其他都很好。希望改进。",
]

HOST_REPLIES = [
    "感谢您的入住和好评！欢迎下次再来！😊",
    "谢谢您的反馈，我们会继续努力做得更好！",
    "很高兴您喜欢这里，期待您的再次光临！",
    "感谢您的宝贵意见，我们已记录并会尽快改进。",
    "欢迎下次带家人朋友一起来！",
]

NOTE_TITLES = [
    "杭州三日慢游记：西湖边的慢生活",
    "北京胡同里的隐秘角落",
    "上海武康路漫步指南",
    "成都美食地图：从早吃到晚",
    "西安古城墙骑行攻略",
    "丽江：在束河晒太阳的日子",
    "三亚潜水初体验",
    "厦门鼓浪屿的文艺时光",
    "青岛啤酒节全记录",
    "南京：六朝古都的秋日漫步",
    "重庆火锅挑战之旅",
    "大理洱海骑行日记",
    "阳朔山水甲天下",
    "苏州园林里的江南梦",
    "长沙：不夜城的美食之旅",
    "广州早茶文化体验",
    "哈尔滨冰雪奇缘",
    "西藏：离天堂最近的地方",
    "嘉峪关长城徒步",
    "新疆大盘鸡和葡萄干的故事",
]

NOTE_CONTENTS = [
    '这次旅行选择了"开心住"平台上的民宿，体验非常棒！第一天抵达杭州已是傍晚，房东特意在路口等候，还帮忙提行李。房间比照片上还要美，正对西湖的落地窗让人瞬间爱上这座城市。\n\n第二天一早被鸟鸣唤醒，拉开窗帘就是西湖晨雾。在湖边跑了步，然后去楼外楼吃了西湖醋鱼。下午在龙井村喝茶，和茶农聊了一下午。\n\n第三天去了灵隐寺和法喜寺，感受千年古刹的宁静。傍晚在断桥边看日落，完美结束了这次旅程。强烈推荐杭州的这家民宿，房东人超好！',
    "北京的魅力不仅在于故宫长城，更藏在那些不起眼的胡同里。这次住在南锣鼓巷的一家四合院民宿，推开朱红大门，仿佛穿越回了老北京。\n\n清晨在胡同里遛弯，看大爷下棋、大妈遛狗。中午找了家胡同里的炸酱面馆，味道正宗。下午逛了逛胡同里的独立书店和手作店，每家都有自己的故事。\n\n晚上在屋顶露台吹着晚风，看着远处CBD的灯火，这种古今交融的感觉真的很奇妙。",
    "武康路是我在上海最爱的一条路。这次特意选了武康路上的法式公寓，推窗就能看到武康大楼。\n\n上午沿着武康路一路走到安福路，沿途探访了多家买手店和咖啡厅。中午在RAC吃了可丽饼，排队半小时但值得。下午去了上海图书馆和巴金故居。\n\n晚上在公寓里煮了杯咖啡，看着窗外的梧桐树影摇曳，这才是上海的正确打开方式。",
    "成都，一座来了就不想走的城市。这次住在宽窄巷子旁边，下楼就是各种美食。\n\n第一天：早餐龙抄手，午餐钵钵鸡，晚餐火锅（大龙燚），宵夜串串。第二天：早餐担担面，午餐夫妻肺片，晚餐烤鱼，宵夜兔头。第三天：早餐豆花，午餐冒菜，晚餐川菜馆，宵夜冰粉。\n\n除了吃，还去了熊猫基地看国宝，在人民公园喝盖碗茶掏耳朵。成都的慢生活，真的让人上瘾。",
    "在西安，最推荐做的事情就是骑自行车上古城墙。租车45块钱，可以骑一整天。\n\n从南门上去，先往东骑到长乐门，沿途可以看到老城区和现代城市的对比。然后往北到安远门，这段城墙保存得最好。\n\n傍晚时分骑到西门，正好看日落。夕阳洒在城墙上，整个城市都镀上了一层金色。下来后在回民街吃了碗羊肉泡馍，完美的一天。",
    "束河古镇比大研古镇安静得多，更适合发发呆、晒晒太阳。\n\n民宿的院子里种满了格桑花，坐在摇椅上就能看到玉龙雪山。白天在古镇里闲逛，找家咖啡馆写作。傍晚去四方街看纳西族老奶奶跳舞。\n\n第三天去了玉龙雪山，虽然有点高原反应，但看到山顶的雪景一切都值了。下山后泡了个天然温泉，浑身舒畅。",
    "第一次潜水选择了三亚的蜈支洲岛。教练非常耐心，从理论到实践一步步指导。\n\n下水的那一刻有点紧张，但看到海底的珊瑚和彩色的鱼群，瞬间就放松了。还看到了海龟和小丑鱼，就像走进了《海底总动员》。\n\n除了潜水，还体验了摩托艇和拖拽伞。晚上在民宿的露台上 BBQ，和来自天南地北的旅客聊天，太快乐了。",
]

COMMENT_TEXTS = [
    "写得太棒了！我也想去！",
    "照片拍得好美，请问是什么相机？",
    "收藏了，下次旅行就按你的路线走！",
    "同款民宿！我上次住也很满意。",
    "请问这家民宿怎么预订？",
    "好详细的攻略，感谢分享！",
    "楼主会玩，下次带上我 😄",
    "这个城市我也去过，真的值得推荐。",
    "请问需要提前多久预订？",
    "写得很有画面感，身临其境。",
]


async def run_seed(db_url: str | None = None):
    engine = create_async_engine(db_url or DB_URL, echo=False)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        print("🌱 Clearing existing data...")
        tables = [
            "chat_messages",
            "note_comments",
            "note_likes",
            "user_follows",
            "notes",
            "reviews",
            "payments",
            "bookings",
            "messages",
            "conversations",
            "listing_photos",
            "listings",
            "users",
        ]
        for t in tables:
            await db.execute(text(f"TRUNCATE TABLE {t} CASCADE"))
        await db.commit()

        print("🌱 Seeding database...")

        # ── Users ──
        user_map = {}  # username -> user record
        user_ids = []  # all user ids
        host_ids = []  # host user ids
        user_ids_for_regular = []  # non-host, non-admin user ids
        admin_id = None

        for username, email, pw, role, score, bio, phone, nickname in USERS:
            uid = str(uuid.uuid4())
            pw_hash = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
            await db.execute(
                text("""
                INSERT INTO users (id, username, email, password_hash, role, score, bio, is_active, phone, nickname, created_at, updated_at)
                VALUES (:id, :username, :email, :pw_hash, :role, :score, :bio, TRUE, :phone, :nickname, NOW(), NOW())
            """),
                {
                    "id": uid,
                    "username": username,
                    "email": email,
                    "pw_hash": pw_hash,
                    "role": role,
                    "score": score,
                    "bio": bio,
                    "phone": phone,
                    "nickname": nickname,
                },
            )
            user_map[username] = {"id": uid, "role": role}
            user_ids.append(uid)
            if role == "host":
                host_ids.append(uid)
            elif role == "user":
                user_ids_for_regular.append(uid)
            elif role == "admin":
                admin_id = uid

        print(f"  ✅ Created {len(USERS)} users")

        # ── Listings ──
        listing_ids = []
        for host_name, title, city, desc, price, guests, beds, baths, status in LISTINGS:
            lid = str(uuid.uuid4())
            host = user_map[host_name]
            await db.execute(
                text("""
                INSERT INTO listings (id, host_id, title, description, city, price_per_night,
                    max_guests, bedrooms, bathrooms, status, is_active, created_at, updated_at)
                VALUES (:id, :host_id, :title, :desc, :city, :price,
                    :guests, :beds, :baths, :status, TRUE, NOW(), NOW())
            """),
                {
                    "id": lid,
                    "host_id": host["id"],
                    "title": title,
                    "desc": desc,
                    "city": city,
                    "price": Decimal(str(price)),
                    "guests": guests,
                    "beds": beds,
                    "baths": baths,
                    "status": status,
                },
            )
            listing_ids.append(lid)

            # Add cover images
            idx = len(listing_ids)
            colors = [
                "667eea",
                "764ba2",
                "f093fb",
                "4facfe",
                "43e97b",
                "fa709a",
                "f6d365",
                "a18cd1",
                "fbc2eb",
                "84fab0",
            ]
            bg = colors[idx % len(colors)]
            photo_urls = [
                f"https://placehold.co/800x600/{bg}/ffffff?text=Room+{idx}{_}"
                for _ in range(randint(1, 3))
            ]
            for i, url in enumerate(photo_urls):
                pid = str(uuid.uuid4())
                await db.execute(
                    text("""
                    INSERT INTO listing_photos (id, listing_id, url, is_primary, sort_order)
                    VALUES (:id, :lid, :url, :is_primary, :sort)
                """),
                    {"id": pid, "lid": lid, "url": url, "is_primary": i == 0, "sort": i},
                )

        print(f"  ✅ Created {len(LISTINGS)} listings with photos")

        # ── Bookings ──
        bk_ids = []
        for i in range(60):
            bk_id = str(uuid.uuid4())
            listing = choice(listing_ids)
            guest = choice(user_ids_for_regular)
            # Find this listing's host
            host_res = await db.execute(
                text("SELECT host_id FROM listings WHERE id = :id"), {"id": listing}
            )
            host_row = host_res.fetchone()
            if not host_row:
                continue
            host = host_row[0]

            ci = choice(CHECKIN_DATES)
            co = ci + timedelta(days=randint(1, 5))
            guests_n = randint(1, 4)
            price_res = await db.execute(
                text("SELECT price_per_night FROM listings WHERE id = :id"), {"id": listing}
            )
            price_row = price_res.fetchone()
            if not price_row:
                continue
            ppn = Decimal(str(price_row[0]))
            nights = (co - ci).days
            total = ppn * Decimal(nights)

            # Mix statuses: mostly confirmed/completed, some cancelled
            status_weight = randint(1, 10)
            if status_weight <= 5:
                bk_status = "confirmed"
            elif status_weight <= 8:
                bk_status = "completed"
            elif status_weight <= 9:
                bk_status = "cancelled"
            else:
                bk_status = "pending"

            paid_at = None
            cancelled_at = None
            cancel_reason = None
            if bk_status in ("confirmed", "completed"):
                paid_at = ci - timedelta(days=randint(1, 7))
            elif bk_status == "cancelled":
                cancelled_at = ci - timedelta(days=randint(1, 3))
                cancel_reason = choice(
                    ["行程有变", "天气原因", "个人原因", "重复预订了", "临时有事"]
                )

            await db.execute(
                text("""
                INSERT INTO bookings (id, listing_id, guest_id, host_id, check_in, check_out,
                    guests, total_price, status, paid_at, cancelled_at, cancel_reason,
                    created_at, updated_at)
                VALUES (:id, :lid, :guest, :host, :ci, :co, :guests, :total, :status,
                    :paid_at, :cancelled_at, :cancel_reason, NOW(), NOW())
            """),
                {
                    "id": bk_id,
                    "lid": listing,
                    "guest": guest,
                    "host": host,
                    "ci": ci,
                    "co": co,
                    "guests": guests_n,
                    "total": total,
                    "status": bk_status,
                    "paid_at": paid_at,
                    "cancelled_at": cancelled_at,
                    "cancel_reason": cancel_reason,
                },
            )
            bk_ids.append(bk_id)

        print(f"  ✅ Created {len(bk_ids)} bookings")

        # ── Reviews (for confirmed/completed bookings) ──
        review_count = 0
        for bk_id in bk_ids:
            if randint(1, 10) > 7:  # ~30% get reviews
                continue
            bk_res = await db.execute(
                text("SELECT listing_id, guest_id, status FROM bookings WHERE id = :id"),
                {"id": bk_id},
            )
            bk_row = bk_res.fetchone()
            if not bk_row or bk_row[2] not in ("confirmed", "completed"):
                continue
            rev_id = str(uuid.uuid4())
            rating = randint(3, 5)
            content = choice(REVIEW_TEXTS)
            reply = choice(HOST_REPLIES) if randint(1, 10) > 3 else None
            await db.execute(
                text("""
                INSERT INTO reviews (id, listing_id, booking_id, user_id, rating, content, reply, created_at, updated_at)
                VALUES (:id, :lid, :bk_id, :uid, :rating, :content, :reply, NOW(), NOW())
            """),
                {
                    "id": rev_id,
                    "lid": bk_row[0],
                    "bk_id": bk_id,
                    "uid": bk_row[1],
                    "rating": rating,
                    "content": content,
                    "reply": reply,
                },
            )
            review_count += 1

        print(f"  ✅ Created {review_count} reviews")

        # ── Social Notes ──
        note_ids = []
        for title, content in zip(NOTE_TITLES, NOTE_CONTENTS):
            nid = str(uuid.uuid4())
            author = choice(user_ids)
            likes = randint(0, 50)
            comments = randint(0, 15)
            await db.execute(
                text("""
                INSERT INTO notes (id, user_id, title, content, likes_count, comments_count, created_at, updated_at)
                VALUES (:id, :uid, :title, :content, :likes, :comments, NOW(), NOW())
            """),
                {
                    "id": nid,
                    "uid": author,
                    "title": title,
                    "content": content,
                    "likes": likes,
                    "comments": comments,
                },
            )
            note_ids.append(nid)

        # Note likes
        like_count = 0
        for nid in note_ids:
            nlikes = randint(0, 8)
            pool = user_ids[:10]
            for i in range(min(nlikes, len(pool))):
                liker = pool[i]
                try:
                    like_id = str(uuid.uuid4())
                    await db.execute(
                        text("""
                        INSERT INTO note_likes (id, note_id, user_id, created_at)
                        VALUES (:id, :nid, :uid, NOW())
                    """),
                        {"id": like_id, "nid": nid, "uid": liker},
                    )
                    like_count += 1
                except Exception:
                    pass

        # Note comments
        comment_count = 0
        for nid in note_ids:
            c_count = randint(0, 8)
            for _ in range(c_count):
                cid = str(uuid.uuid4())
                commenter = choice(user_ids)
                text_c = choice(COMMENT_TEXTS)
                await db.execute(
                    text("""
                    INSERT INTO note_comments (id, note_id, user_id, content, created_at, updated_at)
                    VALUES (:id, :nid, :uid, :content, NOW(), NOW())
                """),
                    {"id": cid, "nid": nid, "uid": commenter, "content": text_c},
                )
                comment_count += 1

        print(f"  ✅ Created {len(note_ids)} social notes with {comment_count} comments")

        # ── Conversations & Messages ──
        conv_count = 0
        msg_count = 0
        for guest_id in user_ids_for_regular[:6]:  # first 6 regular users have conversations
            for host_id in host_ids[:3]:  # with first 3 hosts
                conv_id = str(uuid.uuid4())
                p1, p2 = sorted([guest_id, host_id])  # consistent ordering
                await db.execute(
                    text("""
                    INSERT INTO conversations (id, participant_one, participant_two, last_message, unread_count_one, unread_count_two, created_at, updated_at)
                    VALUES (:id, :p1, :p2, '', 0, 0, NOW(), NOW())
                """),
                    {"id": conv_id, "p1": p1, "p2": p2},
                )
                conv_count += 1

                # Some messages
                for m in range(randint(1, 5)):
                    mid = str(uuid.uuid4())
                    sender = choice([guest_id, host_id])
                    msg_text = choice(
                        [
                            "你好，请问这个房间还有空吗？",
                            "有的，您想预订什么时间？",
                            "我想预订5月1日到5月3日。",
                            "好的，已经为您保留，请尽快下单。",
                            "请问可以带宠物吗？",
                            "不好意思，我们暂不接受宠物入住。",
                            "好的，谢谢！我马上下单。",
                            "请问有接机服务吗？",
                            "我们可以提供付费接机服务，100元/次。",
                            "请问附近有什么好吃的推荐吗？",
                            "楼下右转有家火锅店特别好吃！",
                            "可以提前入住吗？",
                            "如果房间空着可以提前，我提前通知您。",
                            "请问有停车位吗？",
                            "有的，免费停车位。",
                        ]
                    )
                    is_read = m < randint(1, 4)
                    await db.execute(
                        text("""
                        INSERT INTO messages (id, conversation_id, sender_id, content, is_read, created_at, updated_at)
                        VALUES (:id, :cid, :sender, :content, :is_read, NOW(), NOW())
                    """),
                        {
                            "id": mid,
                            "cid": conv_id,
                            "sender": sender,
                            "content": msg_text,
                            "is_read": is_read,
                        },
                    )
                    msg_count += 1

                # Update conversation last_message and unread counts
                await db.execute(
                    text("""
                    UPDATE conversations SET last_message = :msg,
                        updated_at = NOW()
                    WHERE id = :id
                """),
                    {"msg": "好的，谢谢！我马上下单。", "id": conv_id},
                )

        print(f"  ✅ Created {conv_count} conversations with {msg_count} messages")

        # ── AI Chat history ──
        ai_count = 0
        for uid in user_ids[:5]:
            for _ in range(randint(1, 4)):
                cid = str(uuid.uuid4())
                role = choice(["user", "assistant"])
                content = (
                    choice(
                        [
                            "你好，帮我推荐北京的民宿",
                            "推荐几个杭州西湖边的酒店",
                            "成都哪里好玩？",
                            "我想去三亚度假，有什么推荐？",
                            "丽江和大理哪个更值得去？",
                            "预算500以内，北京有什么好的民宿？",
                            "带父母出游，推荐几个适合老人的地方",
                            "我想订一个带泳池的别墅",
                        ]
                    )
                    if role == "user"
                    else choice(
                        [
                            "为您推荐以下北京的精品民宿...",
                            "杭州西湖周边有以下优质选择...",
                            "成都有很多好玩的地方，推荐...",
                            "三亚是度假胜地，推荐以下...",
                            "丽江和大理各有特色...",
                        ]
                    )
                )
                await db.execute(
                    text("""
                    INSERT INTO chat_messages (id, user_id, content, role, created_at)
                    VALUES (:id, :uid, :content, :role, NOW())
                """),
                    {"id": cid, "uid": uid, "content": content, "role": role},
                )
                ai_count += 1

        print(f"  ✅ Created {ai_count} AI chat messages")

        await db.commit()
        print("\n🎉 Seeding complete!")
        print(f"   Users: {len(USERS)}")
        print(f"   Listings: {len(LISTINGS)}")
        print(f"   Bookings: {len(bk_ids)}")
        print(f"   Reviews: {review_count}")
        print(f"   Notes: {len(note_ids)}")
        print(f"   Comments: {comment_count}")
        print(f"   Conversations: {conv_count}")
        print(f"   Messages: {msg_count}")
        print(f"   AI chats: {ai_count}")

    await engine.dispose()


async def main():
    db_url = os.environ.get("DATABASE_URL")
    await run_seed(db_url)


if __name__ == "__main__":
    asyncio.run(main())
