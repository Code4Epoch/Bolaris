# -*- coding: utf-8 -*- #
# ------------------------------------------------------------------
# File Name:        live_data_summary
# Author:           ydyjya
# Version:          1.1
# Created:          2021/7/9
# Description:      生成直播数据总结
# Function List:    live_summary()  --总结直播数据
# History:
#       <author>        <version>       <time>      <desc>
#       ydyjya          1.0             2021/7/9    create
#       ydyjya          1.1             2021/8/18   修改了风格，增加了部分功能
# ------------------------------------------------------------------
from live import tool_function as tf
from live import processing_word as mw
from live import make_chart as mc
import pymysql


class live_summary(object):
    """
    针对单场直播获取直播数据可视化，并将数据转储到mysql数据库中
    """
    def __init__(self, my_room_id, my_live_date, my_live_road, my_live_type):

        self.live_date = my_live_date
        self.room_id = my_room_id
        self.live_road = my_live_road
        self.live_type = my_live_type

        self.config = tf.get_config("./config/live_data_summary/live_data_summary_mysql_config.json")

        self.medal_list = self.config['medal_room_id']

        self.uid_list = self.config['target_id']

        # mysql配置
        self.host = self.config['mysql_config']['host']
        self.port = self.config['mysql_config']['port']
        self.user = self.config['mysql_config']['user']
        self.password = self.config['mysql_config']['password']
        self.db = self.config['mysql_config']['db']
        try:
            self.mysql_conn = pymysql.connect(host=self.host, port=self.port,
                                              user=self.user, password=self.password, db=self.db)

        except Exception as e:
            print("connect failed")
            raise e

        self.dm_sql_road = self.live_road + "_dm"
        self.rq_sql_road = self.live_road + "_rq"
        self.fans_sql_road = self.live_road + "_fans"
        self.everyday_stats_sql_road = self.live_road + "_stats"

        self.line_color = self.config['line_color']

    def get_everyday_live_stats(self):
        """
        本函数的功能是将data处理为各种形式以供分析
        1.live_data_group_by_id:直播时段的用户数据
            类型：字典{key:uid, value:[(message1),(message2),......]}
            作用：用于统计用户的观看时长、发言、互动送礼等信息
        2.not_live_data_group_by_id:非直播时段的用户数据
            类型：字典{key:uid, value:[(message1),(message2),......]}
            作用：用于统计用户的观看时长、发言、互动送礼等信息
        3.live_data_group_by_type:直播时段不同类型消息的数据
            类型：字典{key:msg_type, value:[(message1),(message2),......]}
            作用：用于统计不同类型的消息
        4.not_live_data_group_by_type:直播时段不同类型消息的数据
            类型：字典{key:msg_type, value:[(message1),(message2),......]}
            作用：用于统计不同类型的消息
        """
        cur = self.mysql_conn.cursor()
        cur.execute("SELECT * FROM %s ORDER BY time_stamp asc" % self.dm_sql_road)
        all_data = list(cur.fetchall())
        live_data_group_by_id = {}
        not_live_data_group_by_id = {}
        live_data_group_by_type = {}
        not_live_data_group_by_type = {}
        live_flag = 'not_live'
        default_time = 0
        end_time = 0
        for i in all_data.__iter__():
            if i[0] != 'start' and i[0] != 'end':
                user_key = (i[0], )
                if live_flag == 'not_live':
                    if user_key not in not_live_data_group_by_id:
                        not_live_data_group_by_id[user_key] = [i]
                    else:
                        not_live_data_group_by_id[user_key].append(i)

                    if i[4] not in not_live_data_group_by_type:
                        not_live_data_group_by_type[i[4]] = [i]
                    else:
                        not_live_data_group_by_type[i[4]].append(i)
                elif live_flag == 'live':
                    if user_key not in live_data_group_by_id:
                        live_data_group_by_id[user_key] = [i]
                    else:
                        live_data_group_by_id[user_key].append(i)

                    if i[4] not in live_data_group_by_type:
                        live_data_group_by_type[i[4]] = [i]
                    else:
                        live_data_group_by_type[i[4]].append(i)
            elif i[0] == 'start':
                live_flag = 'live'
                default_time = i[5]
            elif i[0] == 'end':
                live_flag = 'not_live'
                end_time = i[5]

        #  1.生成直播小结、营收饼图
        user_stats, user_data = self.__everyday_live_stats(default_time, end_time, live_data_group_by_id)

        # 2.生成词频图 词云图
        self.__wordfreq_wordcloud(live_data_group_by_type)

        # 3.生成舰长图、礼物图、粉丝图、进入图、营收图、同接图、sc图、弹幕图
        self.__make_stats_picture(all_data)

        # 4.生成直播饼图
        self.__make_revenue_picture(user_stats)

        # 5.存储fans数据到mysql
        # self.__fans_stats2sql(user_data, live_data_group_by_id)

    # 直播小结功能
    def __everyday_live_stats(self, my_default_time, my_end_time, my_live_data_group_by_id):
        """

        :param my_end_time: 完播时间
        :param my_default_time: 开播时间
        :param my_live_data_group_by_id: 根据uid分组的直播数据
        :return: 输出直播小结
        """
        every_day_table_name = "every_day_stats"
        self.__create_everyday_sql(every_day_table_name)
        user_data = tf.compute_user_data(my_default_time, my_live_data_group_by_id, self.medal_list, self.uid_list)
        user_stats, time_stats = tf.get_user_stats_data(user_data)
        user_stats = self.__get_revenue(user_stats)
        self.__input_stats_sql(user_stats, time_stats, every_day_table_name, my_default_time, my_end_time)
        mc.make_excel(self.mysql_conn, "./model/everyday_stats_excel.xls", self.live_road)
        # TODO(ydyjya):改成图表形式
        return user_stats, user_data

    # 根据格式自动创造一个弹幕数据表
    def __create_everyday_sql(self, table_name):
        """

        :param table_name: 表名
        :return: 创造一张everyday——stats表
        """
        create_sql = "CREATE TABLE IF NOT EXISTS `%s` (" \
                     "`live` varchar(255) primary key not null, " \
                     "`gift` int not null, " \
                     "`avg_gift` float not null, " \
                     "`danmu` int not null, " \
                     "`avg_danmu` float not null, " \
                     "`sc` int not null, " \
                     "`guard` int not null, " \
                     "`entry` int not null, " \
                     "`avg_watch_time` float not null, " \
                     "`avg_react_watch_time` float not null, " \
                     "`entry_num` int not null, " \
                     "`medal_num` int not null, " \
                     "`react_num` int not null, " \
                     "`medal_0_num` int not null, " \
                     "`medal_0_avg_react` float not null, " \
                     "`medal_0_avg_danmu` float not null," \
                     "`medal_1_5_num` int not null, " \
                     "`medal_1_5_avg_react` float not null, " \
                     "`medal_1_5_avg_danmu` float not null," \
                     "`medal_6_10_num` int not null, " \
                     "`medal_6_10_avg_react` float not null, " \
                     "`medal_6_10_avg_danmu` float not null," \
                     "`medal_11_20_num` int not null, " \
                     "`medal_11_20_avg_react` float not null, " \
                     "`medal_11_20_avg_danmu` float not null," \
                     "`medal_21_num` int not null, " \
                     "`medal_21_avg_react` float not null, " \
                     "`medal_21_avg_danmu` float not null," \
                     "`revenue` float not null," \
                     "`sc_revenue` float not null," \
                     "`gift_revenue` float not null," \
                     "`guard_revenue` float not null," \
                     "`_10revenue` float not null," \
                     "`_10_100revenue` float not null," \
                     "`_100revenue` float not null," \
                     "`avg_revenue` float not null," \
                     "`live_type` varchar(30) not null," \
                     "`live_long` float not null)" \
                     "CHARSET=utf8" % table_name
        self.mysql_conn.cursor().execute(create_sql)

    # 格式化每日数据到数据库
    def __input_stats_sql(self, user_stats, time_stats, table_name, my_start_time, my_end_time):
        """


        :param user_stats: 用户统计
        :param time_stats: 直播间观看时长统计
        :param table_name: 表名
        :return: 存入sql
        """
        gift = user_stats['all']['gift']
        avg_gift = user_stats['all']['gift'] / user_stats['all']['num']
        danmu = user_stats['all']['danmu']
        avg_danmu = user_stats['all']['danmu'] / user_stats['all']['num']
        sc = user_stats['all']['sc']
        guard = user_stats['all']['guard']
        entry = user_stats['all']['entry']
        avg_watch_time = time_stats['entry'] / time_stats['entry_num']
        avg_react_watch_time = time_stats['react'] / time_stats['react_num']
        entry_num = time_stats['entry_num']
        medal_num = user_stats['all']['num'] - user_stats['medal_0']['num']
        react_num = time_stats['react_num']
        medal_0_num = user_stats['medal_0']['num']
        medal_0_avg_react = user_stats['medal_0']['react'] / medal_0_num
        medal_0_avg_danmu = user_stats['medal_0']['danmu'] / medal_0_num
        medal_1_5_num = user_stats['medal_1_5']['num']
        medal_1_5_avg_react = user_stats['medal_1_5']['react'] / medal_1_5_num
        medal_1_5_avg_danmu = user_stats['medal_1_5']['danmu'] / medal_1_5_num
        medal_6_10_num = user_stats['medal_6_10']['num']
        medal_6_10_avg_react = user_stats['medal_6_10']['react'] / medal_6_10_num
        medal_6_10_avg_danmu = user_stats['medal_6_10']['danmu'] / medal_6_10_num
        medal_11_20_num = user_stats['medal_11_20']['num']
        medal_11_20_avg_react = user_stats['medal_11_20']['react'] / medal_11_20_num
        medal_11_20_avg_danmu = user_stats['medal_11_20']['danmu'] / medal_11_20_num
        medal_21_num = user_stats['medal_21']['num']
        medal_21_avg_react = user_stats['medal_21']['react'] / medal_21_num
        medal_21_avg_danmu = user_stats['medal_21']['danmu'] / medal_21_num
        revenue = user_stats['all']['revenue']['gift_type']['sc'] + user_stats['all']['revenue']['gift_type']['guard'] \
                  + user_stats['all']['revenue']['gift_type']['gift']
        sc_revenue = user_stats['all']['revenue']['gift_type']['sc']
        guard_revenue = user_stats['all']['revenue']['gift_type']['guard']
        gift_revenue = user_stats['all']['revenue']['gift_type']['gift']
        _10_revenue = user_stats['all']['revenue']['gift_price']['<10revenue']
        _10_100_revenue = user_stats['all']['revenue']['gift_price']['>=10&<100revenue']
        _100_revenue = user_stats['all']['revenue']['gift_price']['>100revenue']
        avg_revenue = revenue / entry_num
        live_time = (my_end_time - my_start_time).seconds / 60

        insert_sql = "insert into " + table_name + "(live, gift, avg_gift, danmu, avg_danmu, sc, " \
                                                   "guard, entry, avg_watch_time, " \
                                                   "avg_react_watch_time, entry_num, react_num, " \
                                                   "medal_num, " \
                                                   "medal_0_num, medal_0_avg_react, " \
                                                   "medal_0_avg_danmu," \
                                                   "medal_1_5_num, medal_1_5_avg_react, " \
                                                   "medal_1_5_avg_danmu," \
                                                   "medal_6_10_num, medal_6_10_avg_react, " \
                                                   "medal_6_10_avg_danmu," \
                                                   "medal_11_20_num, medal_11_20_avg_react, " \
                                                   "medal_11_20_avg_danmu," \
                                                   "medal_21_num, medal_21_avg_react, " \
                                                   "medal_21_avg_danmu, revenue,sc_revenue,gift_revenue," \
                                                   "guard_revenue, _10revenue, _10_100revenue, _100revenue, " \
                                                   "avg_revenue, live_type, live_long) values('%s','%d','%f','%d'," \
                                                   "'%f','%d','%d','%d','%f','%f','%d','%d','%d'," \
                                                   "'%d', '%f', '%f','%d','%f','%f'" \
                                                   ",'%d','%f','%f','%d','%f','%f','%d','%f'," \
                                                   "'%f','%f','%f','%f','%f','%f','%f','%f','%f', '%s', '%f')" % (
                         self.live_road, gift, avg_gift, danmu, avg_danmu, sc, guard, entry, avg_watch_time,
                         avg_react_watch_time, entry_num, react_num, medal_num, medal_0_num, medal_0_avg_react,
                         medal_0_avg_danmu, medal_1_5_num, medal_1_5_avg_react, medal_1_5_avg_danmu, medal_6_10_num,
                         medal_6_10_avg_react, medal_6_10_avg_danmu, medal_11_20_num, medal_11_20_avg_react,
                         medal_11_20_avg_danmu, medal_21_num, medal_21_avg_react, medal_21_avg_danmu, revenue,
                         sc_revenue, gift_revenue, guard_revenue, _10_revenue, _10_100_revenue, _100_revenue,
                         avg_revenue, self.live_type, live_time)
        try:
            self.mysql_conn.cursor().execute(insert_sql)
            self.mysql_conn.commit()
        except Exception:
            print(insert_sql)
            print("commit failed")

    # 获取营收数据存入字典
    def __get_revenue(self, user_stats):
        """

        @param user_stats: 用户统计字典，最后一列有营收数据
        @return: user_stats, 将营收数据加入到user_stats中
        """
        sql = "select * from %s where msg_type = '%s' or msg_type = '%s' " \
              "or msg_type = '%s' or msg_type = '' " % (self.dm_sql_road, 'gift', 'sc', 'guard')
        cur = self.mysql_conn.cursor()
        cur.execute(sql)
        gift_data = cur.fetchall()
        revenue_data = {'gift_type': {'sc': 0, 'guard': 0, 'gift': 0},
                        'gift_price': {'<10revenue': 0, '>=10&<100revenue': 0, '>100revenue': 0}}
        start_flg = 0
        gift_dict = tf.read_bilibili_gift_price("./config/live_data_summary/gift_price.json")
        for gift_msg in gift_data:
            if start_flg == 0 and gift_msg[0] != 'start':
                continue
            elif start_flg == 0 and gift_msg[0] == 'start':
                start_flg = 1
            elif start_flg == 1 and gift_msg[0] != 'end':
                gift_price = 0
                gift_type = 'default'
                if gift_msg[4] == 'sc':
                    gift_price = gift_msg[-3]
                    gift_type = 'sc'
                elif gift_msg[4] == 'gift':
                    temp_gift = gift_msg[6].split(sep=' * ')
                    gift_type = 'gift'
                    if temp_gift[0] == '小心心' or temp_gift[0] == '辣条':
                        pass
                    else:
                        gift_num = 0
                        try:
                            gift_num = int(temp_gift[1])
                        except Exception:
                            gift_num = 1
                        try:
                            gift_price = float(gift_dict[temp_gift[0]])
                        except Exception:
                            gift_price = 0
                        try:
                            temp_price = gift_price * gift_num
                        except Exception:
                            temp_price = 0
                        if temp_price == 0:
                            continue
                        else:
                            gift_price = temp_price
                elif gift_msg[4] == 'guard':
                    gift_type = 'guard'
                    if gift_msg[-2] == 10003:
                        gift_price = 138
                    elif gift_msg[-2] == 10002:
                        gift_price = 1998
                    elif gift_msg[-2] == 10001:
                        gift_price = 19998
                revenue_data['gift_type'][gift_type] += gift_price
                if gift_price < 10:
                    revenue_data['gift_price']['<10revenue'] += gift_price
                elif gift_price < 100:
                    revenue_data['gift_price']['>=10&<100revenue'] += gift_price
                else:
                    revenue_data['gift_price']['>100revenue'] += gift_price
        user_stats['all']['revenue'] = revenue_data
        return user_stats

    # 生成各种图片
    def __make_stats_picture(self, my_all_data):
        """
        :param my_all_data:所有数据
        :return: 输出图片
        """
        stats_list = mc.get_min_avg_data(my_all_data)
        new_stats_list = {'gift': [], 'danmu': [], 'sc': [], 'guard': [],
                          'entry': [], 'revenue': [], 'new_fans': [], 'new_medal_fans': [], 'simu_interact': []}
        for min_stats in stats_list.__iter__():
            for my_type, num in min_stats.items():
                new_stats_list[my_type].append(num)
        # 礼物图   1mins
        mc.make_min_picture(new_stats_list['gift'], 1, '送礼人次', self.live_road, 1, self.line_color[self.room_id])
        # mp.new_make_min_picture(new_stats_list['gift'], 1, '送礼人次', self.live_road, 1, self.line_color[self.room_id])
        # 弹幕图   1mins
        mc.make_min_picture(new_stats_list['danmu'], 1, '弹幕数量', self.live_road, 1, self.line_color[self.room_id])
        # sc图    3mins
        sc_data = mc.trans_mins_sum(1, 3, new_stats_list['sc'])
        mc.make_min_picture(sc_data, 3, 'sc数量', self.live_road, 1, self.line_color[self.room_id])
        # guard图 3mins
        guard_data = mc.trans_mins_sum(1, 3, new_stats_list['guard'])
        mc.make_min_picture(guard_data, 3, '舰团数量', self.live_road, 1, self.line_color[self.room_id])
        # entry图 1mins
        mc.make_min_picture(new_stats_list['entry'], 1, '入场人次', self.live_road, 1, self.line_color[self.room_id])
        # 营收图   1mins
        mc.make_min_picture(new_stats_list['revenue'], 1, '营收', self.live_road, 1, self.line_color[self.room_id])
        # fans图  3mins
        new_fans_data = mc.trans_mins_sum(1, 3, new_stats_list['new_fans'])
        mc.make_min_picture(new_fans_data, 3, '新增粉丝', self.live_road, 1, self.line_color[self.room_id])
        # 粉丝团图 3mins
        new_medal_fans_data = mc.trans_mins_sum(1, 3, new_stats_list['new_medal_fans'])
        mc.make_min_picture(new_medal_fans_data, 3, '新增粉丝团', self.live_road, 1, self.line_color[self.room_id])
        # 同接图   1mins
        mc.make_min_picture(new_stats_list['simu_interact'], 1,
                            '10分钟同接', self.live_road, 0, self.line_color[self.room_id])

    # 生成营收饼图，收入分布，营收数据存入每日统计数据库
    def __make_revenue_picture(self, my_user_stats):
        """
        :param my_user_stats:user统计字典
        :return: 输出图片
        """
        revenue_type_dict = my_user_stats['all']['revenue']['gift_type']
        revenue_price_dict = my_user_stats['all']['revenue']['gift_price']
        mc.make_revenue_pie(revenue_price_dict, "按金额分", self.live_road)
        mc.make_revenue_pie(revenue_type_dict, "按类型分", self.live_road)

    # 根据格式自动创造一个弹幕数据表
    def __create_fans_table(self, table_name):
        """

        :param table_name: 表名
        :return: 建表
        """
        create_sql = "CREATE TABLE IF NOT EXISTS `%s` (" \
                     "`uid` varchar(255) primary key," \
                     "`watch_time` float not null," \
                     "`interact_times` int not null," \
                     "`danmu_times` int not null," \
                     "`gift_times` int not null," \
                     "`sc_times` int not null," \
                     "`guard_times` int not null," \
                     "`pay` float not null," \
                     "`medal_id` int not null," \
                     "`medal_level` int not null)" \
                     "CHARSET=utf8" % table_name
        try:
            self.mysql_conn.cursor().execute(create_sql)
        except Exception:
            print(create_sql)

    # 粉丝数据存入mysql
    def __fans_stats2sql(self, my_user_stats, my_live_data_group_by_id):
        """

        @param my_user_stats: user统计
        @param my_live_data_group_by_id: uid分组数据
        @return:存入数据库fans表中
        """
        self.__create_fans_table(self.fans_sql_road)

        sql_model = "insert into %s " + self.config['mysql_config']['sql_sentence']['fans_header'] \
                    + " " + self.config['mysql_config']['sql_sentence']['fans_values']

        pay_dict = {}
        gift_dict = tf.read_bilibili_gift_price("./config/live_data_summary/gift_price.json")
        for user_key, msg_list in my_live_data_group_by_id.items():
            pay_key = user_key[0]
            pay = 0
            for msg in msg_list:
                gift_price = 0
                if msg[4] == 'sc':
                    gift_price = msg[-3]
                elif msg[4] == 'gift':
                    temp_gift = msg[6].split(sep=' * ')
                    if temp_gift[0] == '小心心' or temp_gift[0] == '辣条':
                        continue
                    try:
                        gift_num = int(temp_gift[1])
                    except Exception:
                        gift_num = 1
                    try:
                        gift_price = float(gift_dict[temp_gift[0]])
                    except Exception:
                        gift_price = 0
                    try:
                        temp_price = gift_price * gift_num
                    except Exception:
                        temp_price = 0
                    gift_price = temp_price
                elif msg[4] == 'guard':
                    if msg[-2] == 10003:
                        gift_price = 138
                    elif msg[-2] == 10002:
                        gift_price = 1998
                    elif msg[-2] == 10001:
                        gift_price = 19998
                pay += gift_price

            pay_dict[pay_key] = pay

        for user, msg in my_user_stats.items():
            uid = user[0]
            watch_time = msg['watch_time']
            danmu_times = msg['msg_times']['danmu']
            gift_times = msg['msg_times']['gift']
            sc_times = msg['msg_times']['sc']
            guard_times = msg['msg_times']['guard']
            medal_id = int(msg['medal']['id'])
            medal_level = int(msg['medal']['level'])
            interact_times = danmu_times + gift_times + sc_times + guard_times
            pay = pay_dict[uid]
            insert_sql = sql_model % (self.fans_sql_road, str(uid), watch_time, interact_times,
                                      danmu_times, gift_times, sc_times, guard_times, pay, medal_id, medal_level)

            try:
                with self.mysql_conn.cursor() as cur:
                    cur.execute(insert_sql)
                self.mysql_conn.commit()
            except Exception as e:
                self.mysql_conn.rollback()
                print("Commit Failed!\n%s" % insert_sql)

    # 词频、词云图生成
    def __wordfreq_wordcloud(self, my_live_data_group_by_type):
        """

        :param my_live_data_group_by_type: 根据类型分类的消息数据
        :return: 生成词频图和词云图
        """
        word_freq_dic, min_hot_word = mw.get_word_freq_dic(my_live_data_group_by_type)
        # TODO(ydyjya): 分钟热词待做
        word_freq_bar_num = 15
        word_freq_bar_dict = mw.customize_word_freq_dict(word_freq_dic, word_freq_bar_num)
        # mc.pc_make_word_freq_bar(word_freq_bar_dict, self.live_road)
        # 上面是自定义symbol格式的bar，但似乎效果不算很好
        mc.make_word_freq_bar(word_freq_bar_dict, self.live_road, self.line_color[self.room_id])
        word_cloud_num = 600
        word_cloud_dict = mw.customize_word_freq_dict(word_freq_dic, word_cloud_num)
        mc.make_wordcloud(word_cloud_dict, ('./image/wordcloud/%s' % self.room_id), self.live_road)



