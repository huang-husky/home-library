"""
中国图书馆分类法（中图法）数据
CLC - Chinese Library Classification

说明：
- 这里提供的是简化的中图法一级和二级分类
- 完整数据需要从官方渠道获取授权
- 本文件仅包含公开的一级和二级分类大纲

数据来源参考：
- 《中国图书馆分类法》（第五版）
- 国家图书馆公开资料

使用说明：
1. 本数据为教育/研究用途的简化版本
2. 生产环境使用需获取正式授权
3. 建议购买正版中图法数据
"""

# 一级分类（基本大类）
CLC_LEVEL1 = [
    {"code": "A", "name": "马克思主义、列宁主义、毛泽东思想、邓小平理论", "description": ""},
    {"code": "B", "name": "哲学、宗教", "description": ""},
    {"code": "C", "name": "社会科学总论", "description": ""},
    {"code": "D", "name": "政治、法律", "description": ""},
    {"code": "E", "name": "军事", "description": ""},
    {"code": "F", "name": "经济", "description": ""},
    {"code": "G", "name": "文化、科学、教育、体育", "description": ""},
    {"code": "H", "name": "语言、文字", "description": ""},
    {"code": "I", "name": "文学", "description": ""},
    {"code": "J", "name": "艺术", "description": ""},
    {"code": "K", "name": "历史、地理", "description": ""},
    {"code": "N", "name": "自然科学总论", "description": ""},
    {"code": "O", "name": "数理科学和化学", "description": ""},
    {"code": "P", "name": "天文学、地球科学", "description": ""},
    {"code": "Q", "name": "生物科学", "description": ""},
    {"code": "R", "name": "医药、卫生", "description": ""},
    {"code": "S", "name": "农业科学", "description": ""},
    {"code": "T", "name": "工业技术", "description": ""},
    {"code": "U", "name": "交通运输", "description": ""},
    {"code": "V", "name": "航空、航天", "description": ""},
    {"code": "X", "name": "环境科学、安全科学", "description": ""},
    {"code": "Z", "name": "综合性图书", "description": ""},
]

# 二级分类（部分常用类别）
CLC_LEVEL2 = [
    # === A 马克思主义 ===
    {"code": "A1", "name": "马克思、恩格斯著作", "parent": "A"},
    {"code": "A2", "name": "列宁著作", "parent": "A"},
    {"code": "A3", "name": "斯大林著作", "parent": "A"},
    {"code": "A4", "name": "毛泽东著作", "parent": "A"},
    {"code": "A49", "name": "邓小平著作", "parent": "A"},
    {"code": "A5", "name": "马克思、恩格斯、列宁、斯大林、毛泽东、邓小平著作汇编", "parent": "A"},
    {"code": "A7", "name": "马克思、恩格斯、列宁、斯大林、毛泽东、邓小平生平和传记", "parent": "A"},
    {"code": "A8", "name": "马克思主义、列宁主义、毛泽东思想、邓小平理论的学习和研究", "parent": "A"},

    # === B 哲学、宗教 ===
    {"code": "B0", "name": "哲学理论", "parent": "B"},
    {"code": "B1", "name": "世界哲学", "parent": "B"},
    {"code": "B2", "name": "中国哲学", "parent": "B"},
    {"code": "B3", "name": "亚洲哲学", "parent": "B"},
    {"code": "B4", "name": "非洲哲学", "parent": "B"},
    {"code": "B5", "name": "欧洲哲学", "parent": "B"},
    {"code": "B6", "name": "大洋洲哲学", "parent": "B"},
    {"code": "B7", "name": "美洲哲学", "parent": "B"},
    {"code": "B80", "name": "思维科学", "parent": "B"},
    {"code": "B81", "name": "逻辑学（论理学）", "parent": "B"},
    {"code": "B82", "name": "伦理学（道德哲学）", "parent": "B"},
    {"code": "B83", "name": "美学", "parent": "B"},
    {"code": "B84", "name": "心理学", "parent": "B"},
    {"code": "B9", "name": "宗教", "parent": "B"},

    # === C 社会科学总论 ===
    {"code": "C0", "name": "社会科学理论与方法论", "parent": "C"},
    {"code": "C1", "name": "社会科学概况、现状、进展", "parent": "C"},
    {"code": "C2", "name": "社会科学机构、团体、会议", "parent": "C"},
    {"code": "C3", "name": "社会科学研究方法", "parent": "C"},
    {"code": "C4", "name": "社会科学教育与普及", "parent": "C"},
    {"code": "C5", "name": "社会科学丛书、文集、连续性出版物", "parent": "C"},
    {"code": "C6", "name": "社会科学参考工具书", "parent": "C"},
    {"code": "C79", "name": "社会科学非书资料", "parent": "C"},
    {"code": "C8", "name": "统计学", "parent": "C"},
    {"code": "C91", "name": "社会学", "parent": "C"},
    {"code": "C92", "name": "人口学", "parent": "C"},
    {"code": "C93", "name": "管理学", "parent": "C"},
    {"code": "C94", "name": "系统科学", "parent": "C"},
    {"code": "C95", "name": "民族学、文化人类学", "parent": "C"},
    {"code": "C96", "name": "人才学", "parent": "C"},
    {"code": "C97", "name": "劳动科学", "parent": "C"},

    # === D 政治、法律 ===
    {"code": "D0", "name": "政治理论", "parent": "D"},
    {"code": "D1", "name": "国际共产主义运动", "parent": "D"},
    {"code": "D2", "name": "中国共产党", "parent": "D"},
    {"code": "D33/37", "name": "各国共产党", "parent": "D"},
    {"code": "D4", "name": "工人、农民、青年、妇女运动与组织", "parent": "D"},
    {"code": "D5", "name": "世界政治", "parent": "D"},
    {"code": "D6", "name": "中国政治", "parent": "D"},
    {"code": "D73/77", "name": "各国政治", "parent": "D"},
    {"code": "D8", "name": "外交、国际关系", "parent": "D"},
    {"code": "D9", "name": "法律", "parent": "D"},

    # === E 军事 ===
    {"code": "E0", "name": "军事理论", "parent": "E"},
    {"code": "E1", "name": "世界军事", "parent": "E"},
    {"code": "E2", "name": "中国军事", "parent": "E"},
    {"code": "E3/7", "name": "各国军事", "parent": "E"},
    {"code": "E8", "name": "战略学、战役学、战术学", "parent": "E"},
    {"code": "E9", "name": "军事技术", "parent": "E"},
    {"code": "E99", "name": "军事地形学、军事地理学", "parent": "E"},

    # === F 经济 ===
    {"code": "F0", "name": "经济学", "parent": "F"},
    {"code": "F1", "name": "世界各国经济概况、经济史、经济地理", "parent": "F"},
    {"code": "F2", "name": "经济计划与管理", "parent": "F"},
    {"code": "F3", "name": "农业经济", "parent": "F"},
    {"code": "F4", "name": "工业经济", "parent": "F"},
    {"code": "F49", "name": "信息产业经济（总论）", "parent": "F"},
    {"code": "F5", "name": "交通运输经济", "parent": "F"},
    {"code": "F59", "name": "旅游经济", "parent": "F"},
    {"code": "F6", "name": "邮电通信经济", "parent": "F"},
    {"code": "F7", "name": "贸易经济", "parent": "F"},
    {"code": "F8", "name": "财政、金融", "parent": "F"},

    # === G 文化、科学、教育、体育 ===
    {"code": "G0", "name": "文化理论", "parent": "G"},
    {"code": "G1", "name": "世界各国文化与文化事业", "parent": "G"},
    {"code": "G2", "name": "信息与知识传播", "parent": "G"},
    {"code": "G3", "name": "科学、科学研究", "parent": "G"},
    {"code": "G4", "name": "教育", "parent": "G"},
    {"code": "G8", "name": "体育", "parent": "G"},

    # === H 语言、文字 ===
    {"code": "H0", "name": "语言学", "parent": "H"},
    {"code": "H1", "name": "汉语", "parent": "H"},
    {"code": "H2", "name": "中国少数民族语言", "parent": "H"},
    {"code": "H3", "name": "常用外国语", "parent": "H"},
    {"code": "H4", "name": "汉藏语系", "parent": "H"},
    {"code": "H5", "name": "阿尔泰语系（突厥-蒙古-通古斯语系）", "parent": "H"},
    {"code": "H61", "name": "南亚语系（澳斯特罗-亚西亚语系）", "parent": "H"},
    {"code": "H62", "name": "南印语系（达罗毗荼语系、德拉维达语系）", "parent": "H"},
    {"code": "H63", "name": "南岛语系（马来亚-玻里尼西亚语系）", "parent": "H"},
    {"code": "H64", "name": "东北亚诸语言", "parent": "H"},
    {"code": "H65", "name": "高加索语系（伊比利亚-高加索语系）", "parent": "H"},
    {"code": "H66", "name": "乌拉尔语系（芬兰-乌戈尔语系）", "parent": "H"},
    {"code": "H67", "name": "闪-含语系（阿非罗-亚细亚语系）", "parent": "H"},
    {"code": "H7", "name": "印欧语系", "parent": "H"},
    {"code": "H81", "name": "非洲诸语言", "parent": "H"},
    {"code": "H83", "name": "美洲诸语言", "parent": "H"},
    {"code": "H84", "name": "大洋洲诸语言", "parent": "H"},
    {"code": "H9", "name": "国际辅助语", "parent": "H"},

    # === I 文学 ===
    {"code": "I0", "name": "文学理论", "parent": "I"},
    {"code": "I1", "name": "世界文学", "parent": "I"},
    {"code": "I2", "name": "中国文学", "parent": "I"},
    {"code": "I3/7", "name": "各国文学", "parent": "I"},

    # === J 艺术 ===
    {"code": "J0", "name": "艺术理论", "parent": "J"},
    {"code": "J1", "name": "世界各国艺术概况", "parent": "J"},
    {"code": "J19", "name": "专题艺术与现代边缘艺术", "parent": "J"},
    {"code": "J2", "name": "绘画", "parent": "J"},
    {"code": "J29", "name": "书法、篆刻", "parent": "J"},
    {"code": "J3", "name": "雕塑", "parent": "J"},
    {"code": "J4", "name": "摄影艺术", "parent": "J"},
    {"code": "J5", "name": "工艺美术", "parent": "J"},
    {"code": "J59", "name": "建筑艺术", "parent": "J"},
    {"code": "J6", "name": "音乐", "parent": "J"},
    {"code": "J7", "name": "舞蹈", "parent": "J"},
    {"code": "J8", "name": "戏剧艺术", "parent": "J"},
    {"code": "J9", "name": "电影、电视艺术", "parent": "J"},

    # === K 历史、地理 ===
    {"code": "K0", "name": "史学理论", "parent": "K"},
    {"code": "K1", "name": "世界史", "parent": "K"},
    {"code": "K2", "name": "中国史", "parent": "K"},
    {"code": "K3", "name": "亚洲史", "parent": "K"},
    {"code": "K4", "name": "非洲史", "parent": "K"},
    {"code": "K5", "name": "欧洲史", "parent": "K"},
    {"code": "K6", "name": "大洋洲史", "parent": "K"},
    {"code": "K7", "name": "美洲史", "parent": "K"},
    {"code": "K81", "name": "传记", "parent": "K"},
    {"code": "K85", "name": "文物考古", "parent": "K"},
    {"code": "K89", "name": "风俗习惯", "parent": "K"},
    {"code": "K9", "name": "地理", "parent": "K"},

    # === N 自然科学总论 ===
    {"code": "N0", "name": "自然科学理论与方法论", "parent": "N"},
    {"code": "N1", "name": "自然科学概况、现状、进展", "parent": "N"},
    {"code": "N2", "name": "自然科学机构、团体、会议", "parent": "N"},
    {"code": "N3", "name": "自然科学研究方法", "parent": "N"},
    {"code": "N4", "name": "自然科学教育与普及", "parent": "N"},
    {"code": "N5", "name": "自然科学丛书、文集、连续性出版物", "parent": "N"},
    {"code": "N6", "name": "自然科学参考工具书", "parent": "N"},
    {"code": "N79", "name": "自然科学非书资料", "parent": "N"},
    {"code": "N8", "name": "自然科学调查、考察", "parent": "N"},
    {"code": "N91", "name": "自然研究、自然历史", "parent": "N"},
    {"code": "N93", "name": "非线性科学", "parent": "N"},
    {"code": "N94", "name": "系统科学", "parent": "N"},
    {"code": "N99", "name": "情报学、情报工作", "parent": "N"},

    # === O 数理科学和化学 ===
    {"code": "O1", "name": "数学", "parent": "O"},
    {"code": "O3", "name": "力学", "parent": "O"},
    {"code": "O4", "name": "物理学", "parent": "O"},
    {"code": "O6", "name": "化学", "parent": "O"},
    {"code": "O7", "name": "晶体学", "parent": "O"},

    # === P 天文学、地球科学 ===
    {"code": "P1", "name": "天文学", "parent": "P"},
    {"code": "P2", "name": "测绘学", "parent": "P"},
    {"code": "P3", "name": "地球物理学", "parent": "P"},
    {"code": "P4", "name": "大气科学（气象学）", "parent": "P"},
    {"code": "P5", "name": "地质学", "parent": "P"},
    {"code": "P7", "name": "海洋学", "parent": "P"},
    {"code": "P9", "name": "自然地理学", "parent": "P"},

    # === Q 生物科学 ===
    {"code": "Q1", "name": "普通生物学", "parent": "Q"},
    {"code": "Q2", "name": "细胞生物学", "parent": "Q"},
    {"code": "Q3", "name": "遗传学", "parent": "Q"},
    {"code": "Q4", "name": "生理学", "parent": "Q"},
    {"code": "Q5", "name": "生物化学", "parent": "Q"},
    {"code": "Q6", "name": "生物物理学", "parent": "Q"},
    {"code": "Q7", "name": "分子生物学", "parent": "Q"},
    {"code": "Q81", "name": "生物工程学（生物技术）", "parent": "Q"},
    {"code": "Q89", "name": "环境生物学", "parent": "Q"},
    {"code": "Q91", "name": "古生物学", "parent": "Q"},
    {"code": "Q93", "name": "微生物学", "parent": "Q"},
    {"code": "Q94", "name": "植物学", "parent": "Q"},
    {"code": "Q95", "name": "动物学", "parent": "Q"},
    {"code": "Q96", "name": "昆虫学", "parent": "Q"},
    {"code": "Q98", "name": "人类学", "parent": "Q"},

    # === R 医药、卫生 ===
    {"code": "R1", "name": "预防医学、卫生学", "parent": "R"},
    {"code": "R2", "name": "中国医学", "parent": "R"},
    {"code": "R3", "name": "基础医学", "parent": "R"},
    {"code": "R4", "name": "临床医学", "parent": "R"},
    {"code": "R5", "name": "内科学", "parent": "R"},
    {"code": "R6", "name": "外科学", "parent": "R"},
    {"code": "R71", "name": "妇产科学", "parent": "R"},
    {"code": "R72", "name": "儿科学", "parent": "R"},
    {"code": "R73", "name": "肿瘤学", "parent": "R"},
    {"code": "R74", "name": "神经病学与精神病学", "parent": "R"},
    {"code": "R75", "name": "皮肤病学与性病学", "parent": "R"},
    {"code": "R76", "name": "耳鼻喉科学", "parent": "R"},
    {"code": "R77", "name": "眼科学", "parent": "R"},
    {"code": "R78", "name": "口腔科学", "parent": "R"},
    {"code": "R79", "name": "外国民族医学", "parent": "R"},
    {"code": "R8", "name": "特种医学", "parent": "R"},
    {"code": "R9", "name": "药学", "parent": "R"},

    # === S 农业科学 ===
    {"code": "S1", "name": "农业基础科学", "parent": "S"},
    {"code": "S2", "name": "农业工程", "parent": "S"},
    {"code": "S3", "name": "农学（农艺学）", "parent": "S"},
    {"code": "S4", "name": "植物保护", "parent": "S"},
    {"code": "S5", "name": "农作物", "parent": "S"},
    {"code": "S6", "name": "园艺", "parent": "S"},
    {"code": "S7", "name": "林业", "parent": "S"},
    {"code": "S8", "name": "畜牧、兽医、狩猎、蚕、蜂", "parent": "S"},
    {"code": "S9", "name": "水产、渔业", "parent": "S"},

    # === T 工业技术 ===
    {"code": "TB", "name": "一般工业技术", "parent": "T"},
    {"code": "TD", "name": "矿业工程", "parent": "T"},
    {"code": "TE", "name": "石油、天然气工业", "parent": "T"},
    {"code": "TF", "name": "冶金工业", "parent": "T"},
    {"code": "TG", "name": "金属学与金属工艺", "parent": "T"},
    {"code": "TH", "name": "机械、仪表工业", "parent": "T"},
    {"code": "TJ", "name": "武器工业", "parent": "T"},
    {"code": "TK", "name": "能源与动力工程", "parent": "T"},
    {"code": "TL", "name": "原子能技术", "parent": "T"},
    {"code": "TM", "name": "电工技术", "parent": "T"},
    {"code": "TN", "name": "电子技术、通信技术", "parent": "T"},
    {"code": "TP", "name": "自动化技术、计算机技术", "parent": "T"},
    {"code": "TQ", "name": "化学工业", "parent": "T"},
    {"code": "TS", "name": "轻工业、手工业、生活服务业", "parent": "T"},
    {"code": "TU", "name": "建筑科学", "parent": "T"},
    {"code": "TV", "name": "水利工程", "parent": "T"},

    # === U 交通运输 ===
    {"code": "U1", "name": "综合运输", "parent": "U"},
    {"code": "U2", "name": "铁路运输", "parent": "U"},
    {"code": "U4", "name": "公路运输", "parent": "U"},
    {"code": "U6", "name": "水路运输", "parent": "U"},
    {"code": "U8", "name": "航空运输", "parent": "U"},

    # === V 航空、航天 ===
    {"code": "V1", "name": "航空、航天技术的研究与探索", "parent": "V"},
    {"code": "V2", "name": "航空", "parent": "V"},
    {"code": "V4", "name": "航天（宇宙航行）", "parent": "V"},
    {"code": "V7", "name": "航空、航天医学", "parent": "V"},

    # === X 环境科学、安全科学 ===
    {"code": "X1", "name": "环境科学基础理论", "parent": "X"},
    {"code": "X2", "name": "社会与环境", "parent": "X"},
    {"code": "X3", "name": "环境保护管理", "parent": "X"},
    {"code": "X4", "name": "灾害及其防治", "parent": "X"},
    {"code": "X5", "name": "环境污染及其防治", "parent": "X"},
    {"code": "X7", "name": "废物处理与综合利用", "parent": "X"},
    {"code": "X8", "name": "环境质量评价与环境监测", "parent": "X"},
    {"code": "X9", "name": "安全科学", "parent": "X"},

    # === Z 综合性图书 ===
    {"code": "Z1", "name": "丛书", "parent": "Z"},
    {"code": "Z2", "name": "百科全书、类书", "parent": "Z"},
    {"code": "Z3", "name": "辞典", "parent": "Z"},
    {"code": "Z4", "name": "论文集、全集、选集、杂著", "parent": "Z"},
    {"code": "Z5", "name": "年鉴、年刊", "parent": "Z"},
    {"code": "Z6", "name": "期刊、连续性出版物", "parent": "Z"},
    {"code": "Z8", "name": "图书报刊目录、文摘、索引", "parent": "Z"},
]

# 常用三级分类（示例）
CLC_LEVEL3_COMMON = [
    # TP 自动化技术、计算机技术
    {"code": "TP3", "name": "计算技术、计算机技术", "parent": "TP"},
    {"code": "TP31", "name": "计算机软件", "parent": "TP3"},
    {"code": "TP311", "name": "程序设计、软件工程", "parent": "TP31"},
    {"code": "TP311.1", "name": "程序设计", "parent": "TP311"},
    {"code": "TP311.5", "name": "软件工程", "parent": "TP311"},
    {"code": "TP312", "name": "程序语言、算法语言", "parent": "TP31"},
    {"code": "TP316", "name": "操作系统", "parent": "TP31"},
    {"code": "TP317", "name": "程序包（应用软件）", "parent": "TP31"},
    {"code": "TP32", "name": "一般计算器和计算机", "parent": "TP3"},
    {"code": "TP33", "name": "电子数字计算机", "parent": "TP3"},
    {"code": "TP34", "name": "电子模拟计算机", "parent": "TP3"},
    {"code": "TP35", "name": "混合电子计算机", "parent": "TP3"},
    {"code": "TP36", "name": "微型计算机", "parent": "TP3"},
    {"code": "TP37", "name": "多媒体技术与多媒体计算机", "parent": "TP3"},
    {"code": "TP38", "name": "其他计算机", "parent": "TP3"},
    {"code": "TP39", "name": "计算机的应用", "parent": "TP3"},
    {"code": "TP391", "name": "信息处理（信息加工）", "parent": "TP39"},
    {"code": "TP391.4", "name": "模式识别与装置", "parent": "TP391"},
    {"code": "TP391.41", "name": "图像识别及其装置", "parent": "TP391.4"},
    {"code": "TP391.413", "name": "图像理解及其装置", "parent": "TP391.41"},
    {"code": "TP392", "name": "各种专用数据库", "parent": "TP39"},
    {"code": "TP393", "name": "计算机网络", "parent": "TP39"},
    {"code": "TP393.09", "name": "网络应用程序", "parent": "TP393"},
    {"code": "TP393.4", "name": "局域网（LAN）、城域网（MAN）", "parent": "TP393"},
    {"code": "TP393.41", "name": "以太网", "parent": "TP393.4"},
    {"code": "TP394", "name": "各种专用数据库", "parent": "TP39"},

    # I 文学
    {"code": "I247", "name": "当代作品（1949年~）", "parent": "I2"},
    {"code": "I247.5", "name": "当代长篇、中篇小说", "parent": "I247"},
    {"code": "I247.7", "name": "当代短篇小说", "parent": "I247"},
    {"code": "I266", "name": "当代散文", "parent": "I2"},
    {"code": "I287", "name": "当代儿童文学", "parent": "I2"},
    {"code": "I712", "name": "美国文学", "parent": "I7"},
    {"code": "I561", "name": "英国文学", "parent": "I7"},
    {"code": "I565", "name": "法国文学", "parent": "I7"},
    {"code": "I516", "name": "德国文学", "parent": "I7"},
    {"code": "I313", "name": "日本文学", "parent": "I7"},

    # F 经济
    {"code": "F270", "name": "企业经济理论和方法", "parent": "F27"},
    {"code": "F271", "name": "企业体制", "parent": "F27"},
    {"code": "F272", "name": "企业计划与经营决策", "parent": "F27"},
    {"code": "F273", "name": "企业生产管理", "parent": "F27"},
    {"code": "F274", "name": "企业营销管理", "parent": "F27"},
    {"code": "F275", "name": "企业财务管理", "parent": "F27"},
    {"code": "F276", "name": "各种企业经济", "parent": "F27"},
    {"code": "F276.6", "name": "公司经济", "parent": "F276"},
    {"code": "F279", "name": "世界各国企业经济", "parent": "F27"},
    {"code": "F830", "name": "金融、银行理论", "parent": "F83"},
    {"code": "F831", "name": "世界金融、银行", "parent": "F83"},
    {"code": "F832", "name": "中国金融、银行", "parent": "F83"},
    {"code": "F833/837", "name": "各国金融、银行", "parent": "F83"},

    # G 教育
    {"code": "G40", "name": "教育学", "parent": "G4"},
    {"code": "G41", "name": "思想政治教育、德育", "parent": "G4"},
    {"code": "G42", "name": "教学理论", "parent": "G4"},
    {"code": "G424", "name": "教学法和教学组织", "parent": "G42"},
    {"code": "G424.7", "name": "学绩管理和考试", "parent": "G424"},
    {"code": "G43", "name": "电化教育", "parent": "G4"},
    {"code": "G44", "name": "教育心理学", "parent": "G4"},
    {"code": "G45", "name": "教师与学生", "parent": "G4"},
    {"code": "G46", "name": "教育行政", "parent": "G4"},
    {"code": "G47", "name": "学校管理", "parent": "G4"},
    {"code": "G61", "name": "学前教育、幼儿教育", "parent": "G6"},
    {"code": "G62", "name": "初等教育", "parent": "G6"},
    {"code": "G623", "name": "各科教学法、教学参考书", "parent": "G62"},
    {"code": "G63", "name": "中等教育", "parent": "G6"},
    {"code": "G633", "name": "各科教学法、教学参考书", "parent": "G63"},
    {"code": "G64", "name": "高等教育", "parent": "G6"},
    {"code": "G642", "name": "教学过程", "parent": "G64"},
    {"code": "G642.4", "name": "教学实习", "parent": "G642"},
    {"code": "G642.47", "name": "学绩考试、考查", "parent": "G642"},
    {"code": "G649", "name": "世界各国高等教育概况", "parent": "G64"},

    # B 哲学、心理
    {"code": "B0", "name": "哲学理论", "parent": "B"},
    {"code": "B01", "name": "哲学基本问题", "parent": "B0"},
    {"code": "B02", "name": "辩证唯物主义", "parent": "B0"},
    {"code": "B021", "name": "物质论", "parent": "B02"},
    {"code": "B022", "name": "意识论", "parent": "B02"},
    {"code": "B023", "name": "认识论、反映论", "parent": "B02"},
    {"code": "B024", "name": "唯物辩证法", "parent": "B02"},
    {"code": "B03", "name": "历史唯物主义（唯物史观）", "parent": "B0"},
    {"code": "B08", "name": "哲学流派及其研究", "parent": "B0"},
    {"code": "B081", "name": "唯心主义", "parent": "B08"},
    {"code": "B082", "name": "唯物主义", "parent": "B08"},
    {"code": "B083", "name": "实证论、实在论", "parent": "B08"},
    {"code": "B084", "name": "经验论、先验论", "parent": "B08"},
    {"code": "B085", "name": "批判哲学", "parent": "B08"},
    {"code": "B086", "name": "存在主义（生存主义）", "parent": "B08"},
    {"code": "B087", "name": "实用主义", "parent": "B08"},
    {"code": "B089", "name": "其他哲学流派", "parent": "B08"},
    {"code": "B2", "name": "中国哲学", "parent": "B"},
    {"code": "B22", "name": "先秦哲学（~前221年）", "parent": "B2"},
    {"code": "B221", "name": "诸子前哲学", "parent": "B22"},
    {"code": "B222", "name": "儒家", "parent": "B22"},
    {"code": "B223", "name": "道家", "parent": "B22"},
    {"code": "B224", "name": "墨家", "parent": "B22"},
    {"code": "B225", "name": "名家", "parent": "B22"},
    {"code": "B226", "name": "法家", "parent": "B22"},
    {"code": "B227", "name": "阴阳家", "parent": "B22"},
    {"code": "B228", "name": "纵横家", "parent": "B22"},
    {"code": "B229", "name": "杂家", "parent": "B22"},
    {"code": "B234", "name": "汉代哲学（前206~220年）", "parent": "B2"},
    {"code": "B235", "name": "三国、晋、南北朝哲学（220~589年）", "parent": "B2"},
    {"code": "B24", "name": "隋、唐、五代哲学（581~960年）", "parent": "B2"},
    {"code": "B244", "name": "宋、元哲学（960~1368年）", "parent": "B2"},
    {"code": "B248", "name": "明代哲学（1368~1644年）", "parent": "B2"},
    {"code": "B249", "name": "清代哲学（1644~1840年）", "parent": "B2"},
    {"code": "B25", "name": "近代哲学（1840~1918年）", "parent": "B2"},
    {"code": "B26", "name": "现代哲学（1919年~）", "parent": "B2"},
    {"code": "B5", "name": "欧洲哲学", "parent": "B"},
    {"code": "B502", "name": "古代哲学", "parent": "B5"},
    {"code": "B503", "name": "中世纪哲学", "parent": "B5"},
    {"code": "B504", "name": "文艺复兴时期哲学", "parent": "B5"},
    {"code": "B505", "name": "十七~十八世纪早期资产阶级革命时期哲学", "parent": "B5"},
    {"code": "B506", "name": "十八世纪法国启蒙运动哲学", "parent": "B5"},
    {"code": "B507", "name": "十八~十九世纪德国古典哲学", "parent": "B5"},
    {"code": "B508", "name": "十九世纪俄国哲学", "parent": "B5"},
    {"code": "B509", "name": "马克思主义产生以后的西方哲学", "parent": "B5"},
    {"code": "B516", "name": "德国哲学", "parent": "B5"},
    {"code": "B516.2", "name": "康德（Kant, I. 1724-1804年）", "parent": "B516"},
    {"code": "B516.3", "name": "费希特（Fichte, J.G. 1762-1814年）", "parent": "B516"},
    {"code": "B516.31", "name": "黑格尔（Hegel, G.W.F. 1770-1831年）", "parent": "B516"},
    {"code": "B516.4", "name": "费尔巴哈（Feuerbach, L.A. 1804-1872年）", "parent": "B516"},
    {"code": "B516.5", "name": "马克思（Marx, K. 1818-1883年）", "parent": "B516"},
    {"code": "B516.6", "name": "恩格斯（Engels, F. 1820-1895年）", "parent": "B516"},
    {"code": "B516.7", "name": "尼采（Nietzsche, F.W. 1844-1900年）", "parent": "B516"},
    {"code": "B561", "name": "英国哲学", "parent": "B5"},
    {"code": "B565", "name": "法国哲学", "parent": "B5"},
    {"code": "B565.2", "name": "笛卡尔（Descartes, R. 1596-1650年）", "parent": "B565"},
    {"code": "B565.4", "name": "伏尔泰（Voltaire, 1694-1778年）", "parent": "B565"},
    {"code": "B565.5", "name": "卢梭（Rousseau, J.J. 1712-1778年）", "parent": "B565"},
    {"code": "B712", "name": "美国哲学", "parent": "B7"},
    {"code": "B84", "name": "心理学", "parent": "B"},
    {"code": "B841", "name": "心理学研究方法", "parent": "B84"},
    {"code": "B842", "name": "心理过程与心理状态", "parent": "B84"},
    {"code": "B842.1", "name": "认知", "parent": "B842"},
    {"code": "B842.2", "name": "情绪与情感", "parent": "B842"},
    {"code": "B842.3", "name": "意志", "parent": "B842"},
    {"code": "B842.5", "name": "智力测验", "parent": "B842"},
    {"code": "B842.6", "name": "性格测验", "parent": "B842"},
    {"code": "B842.7", "name": "神经心理与生理心理", "parent": "B842"},
    {"code": "B843", "name": "发生心理学", "parent": "B84"},
    {"code": "B844", "name": "发展心理学（人类心理学）", "parent": "B84"},
    {"code": "B844.1", "name": "儿童心理学", "parent": "B844"},
    {"code": "B844.2", "name": "青少年心理学", "parent": "B844"},
    {"code": "B844.3", "name": "成年人心理学", "parent": "B844"},
    {"code": "B844.4", "name": "老年人心理学", "parent": "B844"},
    {"code": "B845", "name": "生理心理学", "parent": "B84"},
    {"code": "B845.1", "name": "神经心理学", "parent": "B845"},
    {"code": "B845.6", "name": "感官生理学", "parent": "B845"},
    {"code": "B845.9", "name": "其他生理心理学", "parent": "B845"},
    {"code": "B846", "name": "变态心理学、病态心理学、超意识心理学", "parent": "B84"},
    {"code": "B848", "name": "个性心理学、人格心理学", "parent": "B84"},
    {"code": "B848.2", "name": "能力与才能", "parent": "B848"},
    {"code": "B848.3", "name": "智力", "parent": "B848"},
    {"code": "B848.4", "name": "性格、气质", "parent": "B848"},
    {"code": "B848.5", "name": "兴趣、态度", "parent": "B848"},
    {"code": "B848.6", "name": "爱好、癖好", "parent": "B848"},
    {"code": "B848.8", "name": "社会心理、群众心理", "parent": "B848"},
]


def get_all_categories():
    """获取所有分类数据"""
    all_cats = []

    # 一级分类
    for cat in CLC_LEVEL1:
        all_cats.append({
            "code": cat["code"],
            "name": cat["name"],
            "description": cat.get("description", ""),
            "parent": None,
            "level": 1,
        })

    # 二级分类
    for cat in CLC_LEVEL2:
        all_cats.append({
            "code": cat["code"],
            "name": cat["name"],
            "description": cat.get("description", ""),
            "parent": cat["parent"],
            "level": 2,
        })

    # 三级分类
    for cat in CLC_LEVEL3_COMMON:
        all_cats.append({
            "code": cat["code"],
            "name": cat["name"],
            "description": cat.get("description", ""),
            "parent": cat["parent"],
            "level": 3,
        })

    return all_cats
