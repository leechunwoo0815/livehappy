# ruff: noqa: E501, PLR0912, PLR0915, N806, B007, B905, F841
"""Comprehensive seed data for LiveHappy platform.
Simulates real user registration, listing publishing, booking, payment, review, and social flows.

Run via API: POST /api/admin/seed
Run directly: DATABASE_URL=... python backend/scripts/seed.py
"""

import asyncio
import os
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from random import choice, randint, sample, shuffle

import bcrypt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DB_URL = "postgresql+asyncpg://stayhub:devpassword@postgres:5432/stayhub"
PLATFORM_FEE_RATE = Decimal("0.10")
TODAY = date.today()


def _uid():
    return str(uuid.uuid4())


def _past_date(min_days, max_days):
    return TODAY - timedelta(days=randint(min_days, max_days))


def _future_date(min_days, max_days):
    return TODAY + timedelta(days=randint(min_days, max_days))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATA POOLS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

USERS = [
    # (username, email, password, role, score, bio, phone, nickname, avatar)
    ("admin", "admin@livehappy.com", "admin123", "admin", 9999, "平台超级管理员", "13800000001", "管理员", "https://api.dicebear.com/7.x/initials/svg?seed=Admin"),
    ("张明", "zhangming@livehappy.com", "host123", "host", 850, "资深房东，经营精品民宿5年，好评率99%", "13800000002", "张明", "https://api.dicebear.com/7.x/initials/svg?seed=ZM"),
    ("李华", "lihua@livehappy.com", "host123", "host", 920, "酒店管理专业出身，热爱分享旅途中的好住处", "13800000003", "李华", "https://api.dicebear.com/7.x/initials/svg?seed=LH"),
    ("王芳", "wangfang@livehappy.com", "host123", "host", 780, "室内设计师，每间房都亲自设计", "13800000004", "王芳", "https://api.dicebear.com/7.x/initials/svg?seed=WF"),
    ("赵强", "zhaoqiang@livehappy.com", "host123", "host", 650, "退役大厨，经营美食主题民宿", "13800000005", "赵强", "https://api.dicebear.com/7.x/initials/svg?seed=ZQ"),
    ("陈静", "chenjing@livehappy.com", "host123", "host", 890, "摄影师出身，房源照片都是自己拍的", "13800000006", "陈静", "https://api.dicebear.com/7.x/initials/svg?seed=CJ"),
    ("林峰", "linfeng@livehappy.com", "host123", "host", 710, "旅行达人转行做房东，懂旅客需求", "13800000015", "林峰", "https://api.dicebear.com/7.x/initials/svg?seed=LF"),
    ("刘洋", "liuyang@livehappy.com", "user123", "user", 320, "背包客，走遍全国各地", "13800000007", "刘洋", "https://api.dicebear.com/7.x/initials/svg?seed=LY"),
    ("孙丽", "sunli@livehappy.com", "user123", "user", 180, "白领，周末喜欢短途旅行", "13800000008", "孙丽", "https://api.dicebear.com/7.x/initials/svg?seed=SL"),
    ("周伟", "zhouwei@livehappy.com", "user123", "user", 450, "程序员，远程办公到处旅居", "13800000009", "周伟", "https://api.dicebear.com/7.x/initials/svg?seed=ZW"),
    ("吴婷", "wuting@livehappy.com", "user123", "user", 280, "大学生，穷游爱好者", "13800000010", "吴婷", "https://api.dicebear.com/7.x/initials/svg?seed=WT"),
    ("郑浩", "zhenghao@livehappy.com", "user123", "user", 150, "新手上路，请多关照", "13800000011", "郑浩", "https://api.dicebear.com/7.x/initials/svg?seed=ZH"),
    ("黄雨", "huangyu@livehappy.com", "user123", "user", 600, "旅行博主，专注真实住宿体验分享", "13800000012", "黄雨", "https://api.dicebear.com/7.x/initials/svg?seed=HY"),
    ("林雪", "linxue@livehappy.com", "user123", "user", 390, "自由职业者，边工作边旅行", "13800000013", "林雪", "https://api.dicebear.com/7.x/initials/svg?seed=LX"),
    ("何峰", "hefeng@livehappy.com", "user123", "user", 210, "退休教师，游山玩水", "13800000014", "何峰", "https://api.dicebear.com/7.x/initials/svg?seed=HF"),
    ("杨帆", "yangfan@livehappy.com", "user123", "user", 340, "产品经理，假期必旅行", "13800000016", "杨帆", "https://api.dicebear.com/7.x/initials/svg?seed=YF"),
    ("徐萌", "xumeng@livehappy.com", "user123", "user", 520, "小红书旅行博主，粉丝5万", "13800000017", "徐萌", "https://api.dicebear.com/7.x/initials/svg?seed=XM"),
    ("高远", "gaoyuan@livehappy.com", "user123", "user", 180, "新注册用户，期待第一次旅行", "13800000018", "高远", "https://api.dicebear.com/7.x/initials/svg?seed=GY"),
    ("马琳", "malin@livehappy.com", "user123", "user", 410, "自由摄影师，到处采风", "13800000019", "马琳", "https://api.dicebear.com/7.x/initials/svg?seed=ML"),
    ("罗晨", "luochen@livehappy.com", "user123", "user", 290, "创业者，出差旅行两不误", "13800000020", "罗晨", "https://api.dicebear.com/7.x/initials/svg?seed=LC"),
]

# (host_username, title, city, address, lat, lng, description, price, max_guests, bedrooms, bathrooms, status)
LISTINGS = [
    # ── 杭州 (4) ──
    ("张明", "西湖畔·湖景精品大床房", "杭州", "杭州市西湖区北山路68号", 30.2590, 120.1485, "位于西湖核心景区，步行3分钟到断桥残雪。房间落地窗正对西湖，清晨看日出，傍晚赏夕阳。配备智能家居、高清投影、舒适大床。", 588, 2, 1, 1, "approved"),
    ("张明", "龙井茶园·禅意山景房", "杭州", "杭州市西湖区龙井路128号", 30.2220, 120.1105, "隐匿在龙井茶园中的禅意空间，四周茶山环绕，空气清新。房间配有茶具和明前龙井，可品茶赏景。含双人早餐和茶园导览。", 428, 2, 1, 1, "approved"),
    ("李华", "钱江新城·现代 loft", "杭州", "杭州市江干区钱江路388号", 30.2490, 120.2115, "位于钱江新城CBD，200平loft空间，落地窗俯瞰钱塘江。配备开放式厨房、按摩浴缸、智能家居。", 888, 4, 2, 2, "approved"),
    ("王芳", "灵隐寺旁·禅修小院", "杭州", "杭州市西湖区灵隐路88号", 30.2450, 120.1005, "灵隐寺旁的古朴小院，晨钟暮鼓，适合静心。院内有竹林和鱼池。", 358, 2, 1, 1, "pending"),
    # ── 北京 (4) ──
    ("李华", "故宫旁·胡同四合院雅居", "北京", "北京市东城区南锣鼓巷52号", 39.9385, 116.4035, "正宗北京四合院改造，朱门灰瓦，院内石榴树、金鱼缸。步行10分钟到故宫。含老北京炸酱面早餐。", 1288, 4, 2, 1, "approved"),
    ("李华", "三里屯·潮流设计师公寓", "北京", "北京市朝阳区三里屯路19号", 39.9362, 116.4537, "设计师精心打造的loft空间，工业风与现代简约的完美结合。位于太古里旁。", 698, 2, 1, 1, "approved"),
    ("李华", "长城脚下·山野木屋", "北京", "北京市怀柔区慕田峪路12号", 40.4320, 116.5708, "慕田峪长城脚下的独栋木屋，被原始森林环绕。有壁炉、露天温泉、星空观测台。", 1688, 6, 3, 2, "approved"),
    ("张明", "国贸CBD·商务行政套房", "北京", "北京市朝阳区建国门外大街1号", 39.9088, 116.4605, "国贸CBD核心区高端商务公寓，适合出差商旅。", 788, 2, 1, 1, "pending"),
    # ── 上海 (4) ──
    ("王芳", "外滩景观·老洋房套房", "上海", "上海市黄浦区中山东一路12号", 31.2400, 121.4900, "百年历史老洋房，推窗即见外滩万国建筑群。步行5分钟到南京路。", 988, 3, 2, 1, "approved"),
    ("王芳", "迪士尼旁·童话主题民宿", "上海", "上海市浦东新区川沙镇88号", 31.1435, 121.6710, "距迪士尼乐园仅10分钟车程，整栋别墅带花园。每个房间都有童话主题。", 788, 6, 3, 2, "approved"),
    ("王芳", "武康路·法式风情公寓", "上海", "上海市徐汇区武康路376号", 31.2085, 121.4365, "武康路历史建筑中的法式公寓，原木地板、复古家具。楼下是网红café。", 558, 2, 1, 1, "approved"),
    ("陈静", "陆家嘴·天际线江景房", "上海", "上海市浦东新区陆家嘴环路958号", 31.2355, 121.5015, "陆家嘴核心地段，50层高空江景。东方明珠和黄浦江尽收眼底。", 1088, 2, 1, 1, "rejected"),
    # ── 成都 (4) ──
    ("赵强", "宽窄巷子·川味美食民宿", "成都", "成都市青羊区宽窄巷子22号", 30.6700, 104.0525, "宽窄巷子景区内，配备私人火锅厨房。房东是退役大厨，可预约川菜教学。", 458, 4, 2, 1, "approved"),
    ("赵强", "熊猫基地旁·亲子花园房", "成都", "成都市成华区熊猫大道168号", 30.7340, 104.1425, "距大熊猫繁育研究基地15分钟车程。独栋花园别墅，有儿童游乐区。", 628, 6, 3, 2, "approved"),
    ("赵强", "锦里古街·庭院套房", "成都", "成都市武侯区锦里古街15号", 30.6465, 104.0465, "锦里古街深处的静谧庭院，闹中取静。可体验盖碗茶和变脸表演。", 388, 2, 1, 1, "approved"),
    ("林峰", "春熙路·潮流胶囊公寓", "成都", "成都市锦江区春熙路88号", 30.6580, 104.0815, "春熙路核心地段，适合独行侠。", 168, 1, 1, 1, "pending"),
    # ── 西安 (3) ──
    ("陈静", "秦始皇陵旁·秦风民宿", "西安", "西安市临潼区秦陵路18号", 34.3840, 109.2785, "距兵马俑博物馆仅5公里，秦文化主题。含兵马俑门票预约和讲解服务。", 358, 2, 1, 1, "approved"),
    ("陈静", "钟楼夜景·古城墙观景房", "西安", "西安市碑林区南大街68号", 34.2585, 108.9425, "古城墙内，顶楼露台可俯瞰钟楼。回民街步行3分钟。", 428, 2, 1, 1, "approved"),
    ("陈静", "大雁塔旁·唐风雅舍", "西安", "西安市雁塔区慈恩路66号", 34.2185, 108.9635, "大唐不夜城核心区，唐风装修。汉服体验免费参与。", 498, 3, 1, 1, "approved"),
    # ── 三亚 (3) ──
    ("李华", "亚龙湾·海景度假别墅", "三亚", "三亚市吉阳区亚龙湾路88号", 18.2020, 109.6035, "一线海景别墅，私人泳池、椰林花园。步行2分钟到沙滩。含潜水体验。", 1688, 8, 4, 3, "approved"),
    ("李华", "海棠湾·无边泳池套房", "三亚", "三亚市海棠区海棠湾路128号", 18.3100, 109.7205, "网红酒店式公寓，60平大套房带观海阳台。顶层无边泳池。", 988, 3, 1, 1, "approved"),
    ("张明", "大东海·阳光海景房", "三亚", "三亚市吉阳区大东海路28号", 18.2140, 109.5125, "大东海核心地段，出门就是海滩。适合情侣和家庭。", 568, 2, 1, 1, "approved"),
    # ── 丽江 (2) ──
    ("张明", "束河古镇·雪山观景客栈", "丽江", "丽江市古城区束河古镇茶马路8号", 26.8890, 100.2145, "束河古镇制高点，每个房间都能看到玉龙雪山。纳西族传统建筑。", 468, 2, 1, 1, "approved"),
    ("张明", "泸沽湖畔·摩梭风情木屋", "丽江", "丽江市宁蒗县泸沽湖镇12号", 27.7130, 100.7845, "泸沽湖边的原生态木屋，推窗即湖景。体验摩梭族文化。", 688, 2, 1, 1, "approved"),
    # ── 厦门 (2) ──
    ("王芳", "鼓浪屿·百年别墅花园房", "厦门", "厦门市思明区鼓浪屿安海路18号", 24.4430, 118.0645, "百年华侨别墅，花园里种满三角梅和鸡蛋花。步行3分钟到海边。", 558, 2, 1, 1, "approved"),
    ("王芳", "环岛路·海景文艺民宿", "厦门", "厦门市思明区曾厝垵文创村88号", 24.4335, 118.1090, "曾厝垵文创村的海景民宿，清新文艺风格。顶楼天台可看日落。", 368, 2, 1, 1, "approved"),
    # ── 大理 (2) ──
    ("李华", "大理古城·苍山洱海别墅", "大理", "大理市大理古城南门文献路88号", 25.5915, 100.2285, "苍山洱海尽收眼底。庭院有无边水池和观景平台。含环洱海旅拍。", 788, 4, 2, 2, "approved"),
    ("王芳", "喜洲古镇·白族民居", "大理", "大理市喜洲镇四方街22号", 25.8210, 100.1185, "白族传统三坊一照壁民居，由老宅改造。体验扎染和破酥粑粑。", 358, 2, 1, 1, "approved"),
    # ── 其他城市 (各1-2个) ──
    ("赵强", "八大关·欧式别墅套房", "青岛", "青岛市市南区八大关太平角路8号", 36.0555, 120.3385, "德式老别墅，保留原装壁炉和彩色玻璃。步行5分钟到海水浴场。", 628, 4, 2, 1, "approved"),
    ("陈静", "中山陵旁·民国公馆", "南京", "南京市玄武区中山陵景区路68号", 32.0515, 118.8525, "紫金山脚下的民国时期公馆，步行10分钟到中山陵。", 588, 4, 2, 1, "approved"),
    ("陈静", "夫子庙·秦淮河景房", "南京", "南京市秦淮区贡院街88号", 32.0215, 118.7895, "秦淮河畔，推窗即见画舫游船。夜游秦淮绝佳。", 428, 2, 1, 1, "approved"),
    ("张明", "洪崖洞旁·江景 loft", "重庆", "重庆市渝中区嘉滨路88号", 29.5630, 106.5725, "洪崖洞和解放碑之间，高空江景loft。俯瞰长江和渝中半岛夜景。", 498, 4, 2, 1, "approved"),
    ("赵强", "漓江畔·山水画境民宿", "桂林", "桂林市阳朔县遇龙河景区路18号", 24.7785, 110.4935, "遇龙河畔的山水民宿，落地窗外即是漓江山水。含竹筏漂流。", 558, 2, 1, 1, "approved"),
    ("张明", "拙政园旁·苏式园林民宿", "苏州", "苏州市姑苏区东北街168号", 31.3255, 120.6295, "拙政园附近的苏式园林民宿，小桥流水、亭台楼阁。", 628, 2, 1, 1, "approved"),
    ("王芳", "橘子洲头·湘江夜景房", "长沙", "长沙市岳麓区橘子洲大桥旁88号", 28.1865, 112.9525, "橘子洲头旁的高层公寓，正对岳麓山和湘江。含茶颜悦色券。", 398, 2, 1, 1, "approved"),
    ("陈静", "广州塔下·珠江夜景公寓", "广州", "广州市海珠区阅江西路222号", 23.1085, 113.3245, "广州塔旁的高层公寓，夜景一览无余。含广州塔观光门票优惠。", 628, 2, 1, 1, "approved"),
    ("李华", "世界之窗旁·主题公寓", "深圳", "深圳市南山区深南大道9038号", 22.5335, 113.9745, "华侨城创意园内，近世界之窗和欢乐谷。工业风装修。", 458, 2, 1, 1, "approved"),
    ("王芳", "中央大街·俄式风情房", "哈尔滨", "哈尔滨市道里区中央大街128号", 45.7730, 126.6185, "俄式老建筑，百年木质楼梯和雕花天花板。步行5分钟到圣索菲亚。", 358, 2, 1, 1, "approved"),
    ("赵强", "冰雪大世界·暖冬套房", "哈尔滨", "哈尔滨市松北区冰雪大世界路88号", 45.7915, 126.5575, "冰雪大世界附近，地暖+壁炉双重供暖。含冰雪大世界门票。", 528, 4, 2, 1, "approved"),
    ("陈静", "八廓街·藏式阳光房", "拉萨", "拉萨市城关区八廓街38号", 29.6525, 91.1315, "八廓街附近的藏式民宿，阳光房可眺望布达拉宫。提供红景天茶。", 488, 2, 1, 1, "approved"),
    ("张明", "嘉峪关·丝路驿站", "嘉峪关", "嘉峪关市雄关区丝路路8号", 39.8120, 98.2345, "长城西端起点的丝路主题民宿。含关城门票和沙漠露营体验。", 298, 2, 1, 1, "approved"),
    ("林峰", "西湖音乐喷泉旁·观景公寓", "杭州", "杭州市上城区湖滨路58号", 30.2480, 120.1625, "正对音乐喷泉，夜景绝佳。步行到西湖2分钟。", 468, 2, 1, 1, "approved"),
    ("林峰", "外滩源·设计师精品酒店", "上海", "上海市黄浦区圆明园路88号", 31.2380, 121.4865, "外滩源头的设计师酒店，每间房都有独立主题。", 758, 2, 1, 1, "approved"),
    ("林峰", "太古里·成都潮流公寓", "成都", "成都市锦江区中纱帽街8号", 30.6555, 104.0835, "太古里正上方，出门就是潮牌店和网红餐厅。适合年轻人。", 398, 2, 1, 1, "approved"),
    # ── 待审核/已拒绝/已下架（真实场景） ──
    ("赵强", "平遥古城·晋商大院", "晋中", "晋中市平遥县古城内南大街88号", 37.1950, 112.1755, "平遥古城内的晋商大院，保留明清建筑风格。", 328, 3, 1, 1, "pending"),
    ("陈静", "凤凰古城·沱江边吊脚楼", "湘西", "湘西州凤凰县沱江镇回龙阁8号", 27.9485, 109.5995, "沱江边的吊脚楼民宿，推开窗就是古城夜景。", 288, 2, 1, 1, "pending"),
    ("张明", "黄山脚下·云海观景民宿", "黄山", "黄山市黄山区汤口镇168号", 30.1335, 118.1715, "黄山南大门旁，清晨可观云海。含登山向导。", 398, 2, 1, 1, "pending"),
    ("王芳", "景德镇·陶瓷文化民宿", "景德镇", "景德镇市珠山区陶溪川路88号", 29.2930, 117.2065, "陶溪川旁的陶瓷主题民宿，可体验制陶。", 258, 2, 1, 1, "rejected"),
    ("李华", "九寨沟·藏羌风情木屋", "阿坝", "阿坝州九寨沟县漳扎镇88号", 33.2550, 103.9185, "九寨沟景区旁的藏羌风格木屋。", 588, 4, 2, 1, "rejected"),
    ("林峰", "婺源·油菜花田景观房", "上饶", "上饶市婺源县江岭景区路8号", 29.2485, 117.8595, "春季油菜花田环绕，推开窗就是金色花海。", 298, 2, 1, 1, "rejected"),
    ("赵强", "已下架的旧房源", "测试城", "测试路1号", 30.0, 120.0, "这是一个已下架的房源，不应在搜索中出现。", 99, 1, 1, 1, "approved"),
]

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
    "房东很细心，准备了零食和饮料。房间也很暖和，冬天住很舒适。",
    "唯一不满的是热水不太稳定，其他都很好。希望房东能改进一下。",
    "第二次入住了，一如既往的好。已经推荐给朋友了。",
    "住了三晚，每天都不想退房。真的太舒服了！",
    "带父母来的，老人家很满意。环境安静，适合休息。",
    "价格略高，但考虑到地段和装修品质，可以接受。",
    "WiFi信号不太好，其他方面都很棒。适合来旅游不适合办公。",
]

HOST_REPLIES = [
    "感谢您的入住和好评！欢迎下次再来！",
    "谢谢您的反馈，我们会继续努力做得更好！",
    "很高兴您喜欢这里，期待您的再次光临！",
    "感谢您的宝贵意见，我们已记录并会尽快改进。",
    "欢迎下次带家人朋友一起来！我们会准备更多惊喜。",
    "谢谢认可！我们的床品都是定制的，就是为了让大家睡好觉。",
    "感谢反馈！热水问题已经联系维修师傅处理了，下次来一定给您更好的体验。",
]

NOTE_TITLES = [
    "杭州三日慢游记：西湖边的慢生活", "北京胡同里的隐秘角落", "上海武康路漫步指南",
    "成都美食地图：从早吃到晚", "西安古城墙骑行攻略", "丽江：在束河晒太阳的日子",
    "三亚潜水初体验", "厦门鼓浪屿的文艺时光", "青岛啤酒节全记录",
    "南京：六朝古都的秋日漫步", "重庆火锅挑战之旅", "大理洱海骑行日记",
    "阳朔山水甲天下", "苏州园林里的江南梦", "长沙：不夜城的美食之旅",
    "广州早茶文化体验", "哈尔滨冰雪奇缘", "西藏：离天堂最近的地方",
    "嘉峪关长城徒步", "新疆大盘鸡和葡萄干的故事", "深圳周末两日游攻略",
    "平遥古城穿越之旅", "景德镇手作体验记", "婺源春天的金色花海",
    "黄山日出：值得凌晨四点起床的风景",
]

NOTE_CONTENTS = [
    '这次旅行选择了"开心住"平台上的民宿，体验非常棒！第一天抵达杭州已是傍晚，房东特意在路口等候，还帮忙提行李。房间比照片上还要美，正对西湖的落地窗让人瞬间爱上这座城市。\n\n第二天一早被鸟鸣唤醒，拉开窗帘就是西湖晨雾。在湖边跑了步，然后去楼外楼吃了西湖醋鱼。下午在龙井村喝茶，和茶农聊了一下午。\n\n第三天去了灵隐寺和法喜寺，感受千年古刹的宁静。傍晚在断桥边看日落，完美结束了这次旅程。',
    "北京的魅力不仅在于故宫长城，更藏在那些不起眼的胡同里。这次住在南锣鼓巷的一家四合院民宿，推开朱红大门，仿佛穿越回了老北京。\n\n清晨在胡同里遛弯，看大爷下棋、大妈遛狗。中午找了家胡同里的炸酱面馆，味道正宗。下午逛了逛胡同里的独立书店和手作店。\n\n晚上在屋顶露台吹着晚风，看着远处CBD的灯火，这种古今交融的感觉真的很奇妙。",
    "武康路是我在上海最爱的一条路。这次特意选了武康路上的法式公寓，推窗就能看到武康大楼。\n\n上午沿着武康路一路走到安福路，沿途探访了多家买手店和咖啡厅。中午在RAC吃了可丽饼，排队半小时但值得。\n\n晚上在公寓里煮了杯咖啡，看着窗外的梧桐树影摇曳，这才是上海的正确打开方式。",
    "成都，一座来了就不想走的城市。这次住在宽窄巷子旁边，下楼就是各种美食。\n\n第一天：早餐龙抄手，午餐钵钵鸡，晚餐火锅（大龙燚），宵夜串串。第二天：早餐担担面，午餐夫妻肺片，晚餐烤鱼，宵夜兔头。第三天：早餐豆花，午餐冒菜，晚餐川菜馆，宵夜冰粉。\n\n除了吃，还去了熊猫基地看国宝，在人民公园喝盖碗茶掏耳朵。",
    "在西安，最推荐做的事情就是骑自行车上古城墙。租车45块钱，可以骑一整天。\n\n从南门上去，先往东骑到长乐门，沿途可以看到老城区和现代城市的对比。然后往北到安远门。\n\n傍晚时分骑到西门，正好看日落。下来后在回民街吃了碗羊肉泡馍，完美的一天。",
    "束河古镇比大研古镇安静得多，更适合发发呆、晒晒太阳。\n\n民宿的院子里种满了格桑花，坐在摇椅上就能看到玉龙雪山。白天在古镇里闲逛，找家咖啡馆写作。\n\n第三天去了玉龙雪山，虽然有点高原反应，但看到山顶的雪景一切都值了。",
    "第一次潜水选择了三亚的蜈支洲岛。教练非常耐心，从理论到实践一步步指导。\n\n下水的那一刻有点紧张，但看到海底的珊瑚和彩色的鱼群，瞬间就放松了。还看到了海龟和小丑鱼。\n\n除了潜水，还体验了摩托艇和拖拽伞。晚上在民宿的露台上BBQ，太快乐了。",
]

COMMENT_TEXTS = [
    "写得太棒了！我也想去！", "照片拍得好美，请问是什么相机？", "收藏了，下次旅行就按你的路线走！",
    "同款民宿！我上次住也很满意。", "请问这家民宿怎么预订？", "好详细的攻略，感谢分享！",
    "楼主会玩，下次带上我", "这个城市我也去过，真的值得推荐。", "请问需要提前多久预订？",
    "写得很有画面感，身临其境。", "刚从那里回来，确实不错！", "种草了，周末就去！",
    "请问住了几晚？大概花费多少？", "房东人真的超好！", "这个地方我也住过，强烈推荐！",
]

MSG_TEMPLATES = [
    ["你好，请问{date}还有空房吗？", "有的，{date}有空房，您想住几晚？", "两晚可以吗？两个人住。", "没问题，我帮您保留，您尽快下单哦。", "好的谢谢，马上预订！"],
    ["请问可以带宠物吗？", "不好意思，我们目前暂不接受宠物入住哦。", "好的理解，那我再看看别的时间。", "欢迎下次再来！有什么问题随时问我。"],
    ["房东你好，我们明天到，怎么入住呢？", "您好！我会提前把门锁密码发给您，到了直接输入密码即可。门口有欢迎牌，很容易找到。", "好的，谢谢！附近有什么好吃的推荐吗？", "楼下的老王面馆很不错，步行3分钟还有个夜市，强烈推荐！", "太好了，期待明天的入住！"],
    ["请问有接机服务吗？", "有的，我们可以安排付费接机，100元/次，需要提前一天预约。", "好的，我预订了后天入住，到时候麻烦安排一下。", "没问题，您把航班信息发我就行。"],
    ["住了三天，体验非常好！", "谢谢！很高兴您喜欢，欢迎下次再来！", "已经推荐给朋友了，他们也很感兴趣。", "太感谢了！老客户再来可以打9折哦。"],
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN SEED LOGIC
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def run_seed(db_url: str | None = None):
    engine = create_async_engine(db_url or DB_URL, echo=False)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        print("🌱 清空现有数据...")
        tables = [
            "audit_logs", "notifications", "chat_messages",
            "listing_favorites", "note_comments", "note_likes", "user_follows",
            "notes", "reviews", "payments", "bookings",
            "messages", "conversations", "listing_photos", "listings", "users",
        ]
        for t in tables:
            await db.execute(text(f"TRUNCATE TABLE {t} CASCADE"))
        await db.commit()

        print("🌱 开始生成种子数据...")

        # ── 1. Users ──────────────────────────────────────────────
        user_map = {}       # username -> {id, role}
        all_user_ids = []
        host_ids = []
        guest_ids = []
        admin_id = None

        for username, email, pw, role, score, bio, phone, nickname, avatar in USERS:
            uid = _uid()
            pw_hash = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
            await db.execute(text("""
                INSERT INTO users (id, username, email, password_hash, role, score, bio, is_active, phone, nickname, avatar, last_login, created_at, updated_at)
                VALUES (:id, :username, :email, :pw_hash, :role, :score, :bio, TRUE, :phone, :nickname, :avatar, NOW() - INTERVAL '1 day' * :login_days, NOW() - INTERVAL '1 day' * :created_days, NOW())
            """), {
                "id": uid, "username": username, "email": email, "pw_hash": pw_hash,
                "role": role, "score": score, "bio": bio, "phone": phone, "nickname": nickname,
                "avatar": avatar, "login_days": randint(0, 30), "created_days": randint(30, 180),
            })
            user_map[username] = {"id": uid, "role": role}
            all_user_ids.append(uid)
            if role == "host":
                host_ids.append(uid)
            elif role == "user":
                guest_ids.append(uid)
            elif role == "admin":
                admin_id = uid
        print(f"  ✅ {len(USERS)} 个用户（1 管理员 + {len(host_ids)} 房东 + {len(guest_ids)} 旅客）")

        # ── 2. Listings ──────────────────────────────────────────
        listing_map = []  # [{id, host_id, title, city, price, max_guests, status}]
        for host_name, title, city, address, lat, lng, desc, price, guests, beds, baths, status in LISTINGS:
            lid = _uid()
            host = user_map[host_name]
            await db.execute(text("""
                INSERT INTO listings (id, host_id, title, description, city, address, latitude, longitude,
                    price_per_night, max_guests, bedrooms, bathrooms, status, is_active, cover_image, created_at, updated_at)
                VALUES (:id, :hid, :title, :desc, :city, :address, :lat, :lng,
                    :price, :guests, :beds, :baths, :status, :active, :cover, NOW() - INTERVAL '1 day' * :days, NOW())
            """), {
                "id": lid, "hid": host["id"], "title": title, "desc": desc, "city": city,
                "address": address, "lat": lat, "lng": lng, "price": Decimal(str(price)),
                "guests": guests, "beds": beds, "baths": baths, "status": status,
                "active": "下架" not in title, "cover": f"https://picsum.photos/seed/{lid[:8]}/800/600",
                "days": randint(10, 90),
            })
            listing_map.append({"id": lid, "host_id": host["id"], "title": title, "city": city,
                                "price": Decimal(str(price)), "max_guests": guests, "status": status})

            # Photos
            colors = ["667eea", "764ba2", "f093fb", "4facfe", "43e97b", "fa709a", "f6d365", "a18cd1"]
            for i in range(randint(1, 3)):
                pid = _uid()
                await db.execute(text("""
                    INSERT INTO listing_photos (id, listing_id, url, is_primary, sort_order, created_at, updated_at)
                    VALUES (:id, :lid, :url, :primary, :sort, NOW(), NOW())
                """), {
                    "id": pid, "lid": lid,
                    "url": f"https://picsum.photos/seed/{lid[:8]}{i}/800/600",
                    "primary": i == 0, "sort": i,
                })

        approved_listings = [l for l in listing_map if l["status"] == "approved" and "下架" not in l["title"]]
        print(f"  ✅ {len(LISTINGS)} 个房源（{len(approved_listings)} 已上架）")

        # ── 3. Bookings ──────────────────────────────────────────
        bookings = []  # {id, listing, guest_id, host_id, total, status}
        used_ranges = {}  # listing_id -> [(check_in, check_out, status)]

        for i in range(80):
            bk_id = _uid()
            listing = choice(approved_listings)
            guest = choice(guest_ids)
            ppn = listing["price"]

            # Pick non-overlapping dates
            for attempt in range(20):
                status_roll = randint(1, 10)
                if status_roll <= 4:  # 40% completed (past)
                    ci = _past_date(30, 90)
                    nights = randint(2, 5)
                    bk_status = "completed"
                elif status_roll <= 7:  # 30% confirmed (near future)
                    ci = _future_date(1, 15)
                    nights = randint(1, 4)
                    bk_status = "confirmed"
                elif status_roll <= 9:  # 20% pending (future)
                    ci = _future_date(16, 60)
                    nights = randint(1, 3)
                    bk_status = "pending"
                else:  # 10% cancelled (past)
                    ci = _past_date(10, 60)
                    nights = randint(1, 3)
                    bk_status = "cancelled"

                co = ci + timedelta(days=nights)
                active = bk_status in ("pending", "confirmed")
                overlap = False
                for (eci, eco, es) in used_ranges.get(listing["id"], []):
                    if active and es in ("pending", "confirmed") and ci < eco and co > eci:
                        overlap = True
                        break
                if not overlap:
                    break

            total = ppn * Decimal(nights)
            guests_n = randint(1, min(listing["max_guests"], 4))
            paid_at = None
            cancelled_at = None
            cancel_reason = None
            if bk_status in ("confirmed", "completed"):
                paid_at = datetime.combine(ci - timedelta(days=randint(1, 7)), datetime.min.time())
            elif bk_status == "cancelled":
                cancelled_at = datetime.combine(ci - timedelta(days=randint(1, 3)), datetime.min.time())
                cancel_reason = choice(["行程有变", "天气原因", "个人原因", "重复预订了", "临时有事", "航班取消"])

            await db.execute(text("""
                INSERT INTO bookings (id, listing_id, guest_id, host_id, check_in, check_out,
                    guests, total_price, status, paid_at, cancelled_at, cancel_reason, created_at, updated_at)
                VALUES (:id, :lid, :guest, :host, :ci, :co, :guests, :total, :status,
                    :paid_at, :cancelled_at, :cancel_reason, :created, NOW())
            """), {
                "id": bk_id, "lid": listing["id"], "guest": guest, "host": listing["host_id"],
                "ci": ci, "co": co, "guests": guests_n, "total": total, "status": bk_status,
                "paid_at": paid_at, "cancelled_at": cancelled_at, "cancel_reason": cancel_reason,
                "created": datetime.combine(ci - timedelta(days=randint(3, 14)), datetime.min.time()),
            })
            bookings.append({"id": bk_id, "listing_id": listing["id"], "guest_id": guest,
                             "host_id": listing["host_id"], "total": total, "status": bk_status, "ci": ci})
            used_ranges.setdefault(listing["id"], []).append((ci, co, bk_status))

        print(f"  ✅ {len(bookings)} 个预订")

        # ── 4. Payments ──────────────────────────────────────────
        payment_count = 0
        for bk in bookings:
            if bk["status"] in ("confirmed", "completed"):
                pid = _uid()
                amount = bk["total"]
                fee = (amount * PLATFORM_FEE_RATE).quantize(Decimal("0.01"))
                payout = amount - fee
                p_status = "paid"
                refunded_at = None
                await db.execute(text("""
                    INSERT INTO payments (id, booking_id, amount, platform_fee, host_payout, status, paid_at, refunded_at, created_at, updated_at)
                    VALUES (:id, :bid, :amount, :fee, :payout, :status, :paid_at, NULL, :created, NOW())
                """), {
                    "id": pid, "bid": bk["id"], "amount": amount, "fee": fee, "payout": payout,
                    "status": p_status, "paid_at": bk["ci"] - timedelta(days=randint(1, 5)),
                    "created": bk["ci"] - timedelta(days=randint(7, 14)),
                })
                payment_count += 1
            elif bk["status"] == "cancelled":
                # Cancelled bookings may have had a payment that was refunded
                if randint(1, 10) > 6:
                    pid = _uid()
                    await db.execute(text("""
                        INSERT INTO payments (id, booking_id, amount, platform_fee, host_payout, status, paid_at, refunded_at, created_at, updated_at)
                        VALUES (:id, :bid, 0, 0, 0, 'refunded', :paid_at, :refunded, :created, NOW())
                    """), {
                        "id": pid, "bid": bk["id"],
                        "paid_at": bk["ci"] - timedelta(days=randint(5, 10)),
                        "refunded": bk["ci"] - timedelta(days=randint(1, 3)),
                        "created": bk["ci"] - timedelta(days=randint(10, 14)),
                    })
                    payment_count += 1
        print(f"  ✅ {payment_count} 笔支付记录")

        # ── 5. Reviews ──────────────────────────────────────────
        review_count = 0
        review_ids = []
        for bk in bookings:
            if bk["status"] != "completed" or randint(1, 10) > 7:
                continue
            rev_id = _uid()
            rating = choice([5, 5, 5, 4, 4, 4, 3, 3, 2])  # weighted towards positive
            content = choice(REVIEW_TEXTS)
            reply = choice(HOST_REPLIES) if randint(1, 10) > 3 else None
            await db.execute(text("""
                INSERT INTO reviews (id, listing_id, booking_id, user_id, rating, content, reply, created_at, updated_at)
                VALUES (:id, :lid, :bid, :uid, :rating, :content, :reply, :created, NOW())
            """), {
                "id": rev_id, "lid": bk["listing_id"], "bid": bk["id"], "uid": bk["guest_id"],
                "rating": rating, "content": content, "reply": reply,
                "created": datetime.combine(bk["ci"] + timedelta(days=randint(0, 2)), datetime.min.time()),
            })
            review_ids.append({"id": rev_id, "listing_id": bk["listing_id"], "user_id": bk["guest_id"],
                               "host_id": bk["host_id"], "has_reply": reply is not None})
            review_count += 1
        print(f"  ✅ {review_count} 条评价")

        # ── 6. Notifications ──────────────────────────────────────
        notif_count = 0
        for bk in bookings:
            if bk["status"] == "confirmed":
                nid = _uid()
                await db.execute(text("""
                    INSERT INTO notifications (id, user_id, type, content, is_read, related_id, created_at, updated_at)
                    VALUES (:id, :uid, 'booking_confirmed', :content, :read, :rid, :created, NOW())
                """), {"id": nid, "uid": bk["guest_id"], "content": f"您的订单已确认，入住日期：{bk['ci']}",
                       "read": bk["ci"] < TODAY, "rid": bk["id"],
                       "created": bk["ci"] - timedelta(days=randint(3, 10))})
                notif_count += 1
            elif bk["status"] == "cancelled":
                nid = _uid()
                await db.execute(text("""
                    INSERT INTO notifications (id, user_id, type, content, is_read, related_id, created_at, updated_at)
                    VALUES (:id, :uid, 'booking_cancelled', :content, TRUE, :rid, :created, NOW())
                """), {"id": nid, "uid": bk["guest_id"], "content": f"您的订单已取消，入住日期：{bk['ci']}",
                       "rid": bk["id"], "created": bk["ci"] - timedelta(days=randint(1, 5))})
                notif_count += 1

        for rv in review_ids:
            # Notify host about new review
            nid = _uid()
            await db.execute(text("""
                INSERT INTO notifications (id, user_id, type, content, is_read, related_id, created_at, updated_at)
                VALUES (:id, :uid, 'new_review', '您收到一条新的评价', :read, :rid, NOW() - INTERVAL '1 day' * :days, NOW())
            """), {"id": nid, "uid": rv["host_id"], "read": True, "rid": rv["listing_id"], "days": randint(0, 30)})
            notif_count += 1
            # Notify guest about host reply
            if rv["has_reply"]:
                nid = _uid()
                await db.execute(text("""
                    INSERT INTO notifications (id, user_id, type, content, is_read, related_id, created_at, updated_at)
                    VALUES (:id, :uid, 'review_reply', '房东回复了您的评价', :read, :rid, NOW() - INTERVAL '1 day' * :days, NOW())
                """), {"id": nid, "uid": rv["user_id"], "read": randint(0, 1) == 0, "rid": rv["listing_id"], "days": randint(0, 20)})
                notif_count += 1
        print(f"  ✅ {notif_count} 条通知")

        # ── 7. Conversations & Messages ──────────────────────────
        conv_count = 0
        msg_count = 0
        for guest_id in guest_ids[:10]:
            hosts_pool = sample(host_ids, min(3, len(host_ids)))
            for host_id in hosts_pool:
                conv_id = _uid()
                p1, p2 = sorted([guest_id, host_id])
                template = choice(MSG_TEMPLATES)
                last_msg = template[-1]

                await db.execute(text("""
                    INSERT INTO conversations (id, participant_one, participant_two, last_message, unread_count_one, unread_count_two, created_at, updated_at)
                    VALUES (:id, :p1, :p2, :last, :u1, :u2, NOW() - INTERVAL '1 day' * :days, NOW())
                """), {"id": conv_id, "p1": p1, "p2": p2, "last": last_msg,
                       "u1": randint(0, 2), "u2": randint(0, 2), "days": randint(1, 30)})
                conv_count += 1

                for j, msg_text in enumerate(template):
                    mid = _uid()
                    sender = guest_id if j % 2 == 0 else host_id
                    await db.execute(text("""
                        INSERT INTO messages (id, conversation_id, sender_id, content, is_read, created_at, updated_at)
                        VALUES (:id, :cid, :sender, :content, :read, NOW() - INTERVAL '1 day' * :days, NOW())
                    """), {
                        "id": mid, "cid": conv_id, "sender": sender, "content": msg_text,
                        "read": j < len(template) - 1, "days": max(0, randint(0, 10) - j),
                    })
                    msg_count += 1
        print(f"  ✅ {conv_count} 个会话，{msg_count} 条消息")

        # ── 8. Social Notes ──────────────────────────────────────
        note_ids = []
        for idx, (title, content) in enumerate(zip(NOTE_TITLES, NOTE_CONTENTS)):
            nid = _uid()
            author = choice(all_user_ids)
            await db.execute(text("""
                INSERT INTO notes (id, user_id, title, content, likes_count, comments_count, created_at, updated_at)
                VALUES (:id, :uid, :title, :content, 0, 0, NOW() - INTERVAL '1 day' * :days, NOW())
            """), {"id": nid, "uid": author, "title": title, "content": content, "days": randint(1, 60)})
            note_ids.append(nid)

        # Likes
        like_count = 0
        for nid in note_ids:
            nlikes = randint(2, 12)
            likers = sample(all_user_ids, min(nlikes, len(all_user_ids)))
            for liker in likers:
                try:
                    lid = _uid()
                    await db.execute(text("""
                        INSERT INTO note_likes (id, note_id, user_id, created_at) VALUES (:id, :nid, :uid, NOW())
                    """), {"id": lid, "nid": nid, "uid": liker})
                    like_count += 1
                except Exception:
                    pass
            await db.execute(text("UPDATE notes SET likes_count = :c WHERE id = :id"),
                             {"c": min(nlikes, len(all_user_ids)), "id": nid})

        # Comments
        comment_count = 0
        for nid in note_ids:
            c_count = randint(1, 5)
            for _ in range(c_count):
                cid = _uid()
                await db.execute(text("""
                    INSERT INTO note_comments (id, note_id, user_id, content, created_at, updated_at)
                    VALUES (:id, :nid, :uid, :content, NOW(), NOW())
                """), {"id": cid, "nid": nid, "uid": choice(all_user_ids), "content": choice(COMMENT_TEXTS)})
                comment_count += 1
            await db.execute(text("UPDATE notes SET comments_count = :c WHERE id = :id"),
                             {"c": c_count, "id": nid})

        print(f"  ✅ {len(note_ids)} 篇旅记，{like_count} 个赞，{comment_count} 条评论")

        # ── 9. User Follows ──────────────────────────────────────
        follow_count = 0
        follow_pairs = set()
        for _ in range(40):
            f1, f2 = sample(all_user_ids, 2)
            if f1 == f2:
                continue
            pair = tuple(sorted([f1, f2]))
            if pair in follow_pairs:
                continue
            try:
                fid = _uid()
                await db.execute(text("""
                    INSERT INTO user_follows (id, follower_id, following_id, created_at, updated_at)
                    VALUES (:id, :f1, :f2, NOW(), NOW())
                """), {"id": fid, "f1": f1, "f2": f2})
                follow_pairs.add(pair)
                follow_count += 1
            except Exception:
                pass
        print(f"  ✅ {follow_count} 个关注关系")

        # ── 10. Listing Favorites ────────────────────────────────
        fav_count = 0
        fav_pairs = set()
        for guest in guest_ids:
            n_favs = randint(2, 6)
            fav_listings = sample(approved_listings, min(n_favs, len(approved_listings)))
            for lst in fav_listings:
                pair = (guest, lst["id"])
                if pair in fav_pairs:
                    continue
                try:
                    fid = _uid()
                    await db.execute(text("""
                        INSERT INTO listing_favorites (id, user_id, listing_id, created_at, updated_at)
                        VALUES (:id, :uid, :lid, NOW(), NOW())
                    """), {"id": fid, "uid": guest, "lid": lst["id"]})
                    fav_pairs.add(pair)
                    fav_count += 1
                except Exception:
                    pass
        print(f"  ✅ {fav_count} 个房源收藏")

        # ── 11. Audit Logs ───────────────────────────────────────
        audit_actions = [
            ("approve_listing", "listing", l["id"], f"审核通过房源「{l['title']}」")
            for l in listing_map if l["status"] == "approved"
        ]
        audit_actions += [
            ("approve_listing", "listing", l["id"], f"审核拒绝房源「{l['title']}」")
            for l in listing_map if l["status"] == "rejected"
        ]
        audit_actions += [
            ("change_role", "user", choice(guest_ids), "将用户角色从 user 改为 host"),
            ("ban_user", "user", choice(guest_ids), "封禁用户，原因：违规发布广告"),
            ("unban_user", "user", choice(guest_ids), "解封用户"),
            ("offline_listing", "listing", choice(approved_listings)["id"], "下架房源，原因：用户投诉"),
        ]

        audit_count = 0
        for action, target_type, target_id, detail in audit_actions:
            aid = _uid()
            await db.execute(text("""
                INSERT INTO audit_logs (id, admin_id, action, target_type, target_id, detail, created_at, updated_at)
                VALUES (:id, :aid, :action, :tt, :tid, :detail, NOW() - INTERVAL '1 day' * :days, NOW())
            """), {
                "id": aid, "aid": admin_id, "action": action, "tt": target_type, "tid": target_id,
                "detail": detail, "days": randint(0, 60),
            })
            audit_count += 1
        print(f"  ✅ {audit_count} 条审计日志")

        # ── 12. AI Chat Messages ─────────────────────────────────
        ai_count = 0
        ai_pairs = [
            ("你好，帮我推荐北京的民宿", "为您推荐以下北京的精品民宿：1. 故宫旁·胡同四合院雅居（¥1288/晚）— 正宗四合院体验；2. 三里屯·潮流设计师公寓（¥698/晚）— 潮流地段；3. 长城脚下·山野木屋（¥1688/晚）— 自然体验。您偏好哪种风格？"),
            ("杭州西湖附近有什么好的住处？", "杭州西湖附近推荐：1. 西湖畔·湖景精品大床房（¥588/晚）— 落地窗正对西湖；2. 龙井茶园·禅意山景房（¥428/晚）— 茶山环绕；3. 钱江新城·现代loft（¥888/晚）— 适合家庭。第一间离断桥最近，看日出很方便。"),
            ("成都三天怎么安排比较好？", "成都三天推荐行程：\n第一天：宽窄巷子→人民公园喝盖碗茶→春熙路太古里\n第二天：大熊猫繁育研究基地（建议早上8点到）→锦里古街→武侯祠\n第三天：都江堰/青城山一日游\n美食推荐：小龙坎火锅、龙抄手、担担面。住宿推荐宽窄巷子附近的民宿，出行很方便。"),
            ("三亚和厦门哪个更适合度假？", "两者各有特色：\n三亚：热带海滨，适合冬季避寒。亚龙湾和海棠湾水质最好，适合潜水和水上运动。\n厦门：文艺小清新，四季温暖。鼓浪屿、环岛路、曾厝垵各有风情，美食丰富。\n预算充足选三亚看海，喜欢文艺选厦门。建议都去！"),
        ]
        for uid in guest_ids[:4]:
            q, a = ai_pairs[guest_ids.index(uid) % len(ai_pairs)]
            for content, role in [(q, "user"), (a, "assistant")]:
                cid = _uid()
                await db.execute(text("""
                    INSERT INTO chat_messages (id, user_id, content, role, created_at)
                    VALUES (:id, :uid, :content, :role, NOW() - INTERVAL '1 hour' * :hours)
                """), {"id": cid, "uid": uid, "content": content, "role": role, "hours": randint(1, 48)})
                ai_count += 1
        print(f"  ✅ {ai_count} 条 AI 对话")

        await db.commit()

        # ── Summary ──
        print("\n" + "=" * 50)
        print("🎉 种子数据生成完成！")
        print("=" * 50)
        print(f"  👤 用户:     {len(USERS)}")
        print(f"  🏠 房源:     {len(LISTINGS)}")
        print(f"  📅 预订:     {len(bookings)}")
        print(f"  💰 支付:     {payment_count}")
        print(f"  ⭐ 评价:     {review_count}")
        print(f"  🔔 通知:     {notif_count}")
        print(f"  💬 会话:     {conv_count} ({msg_count} 条消息)")
        print(f"  📝 旅记:     {len(note_ids)} ({like_count} 赞, {comment_count} 评论)")
        print(f"  👥 关注:     {follow_count}")
        print(f"  ❤️  收藏:     {fav_count}")
        print(f"  📋 审计日志: {audit_count}")
        print(f"  🤖 AI对话:   {ai_count}")
        print("=" * 50)
        print("\n测试账号：")
        print("  管理员: admin@livehappy.com / admin123")
        print("  房东:   zhangming@livehappy.com / host123")
        print("  旅客:   liuyang@livehappy.com / user123")

    await engine.dispose()


async def main():
    db_url = os.environ.get("DATABASE_URL")
    await run_seed(db_url)


if __name__ == "__main__":
    asyncio.run(main())
