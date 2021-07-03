"""
@author:zzh
@update_time:2021_7_3
"""
import pymysql
import live_function as lf
import live_cut_word as lcw
import make_picture as mp


class live_analysis:

    def __init__(self, room_id, live_date, live_road):
        # 配置属性
        self.live_date = live_date
        self.room_id = room_id
        self.live_road = live_road

        self.config = lf.get_config("./live/config.txt")
        if len(self.config['medal_room_id']) > 1:
            self.live_monitor_type = 'muti'
            self.medal_list = self.config['medal_room_id']
        elif len(self.config['medal_room_id']) == 1:
            self.live_monitor_type = 'single'
            if self.config['medal_room_id'][0] != room_id:
                print('config error')
                raise ValueError
            else:
                self.medal_list = {'self': room_id}
        else:
            print('medal_list is empty!')
            raise ValueError

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
        for i in all_data.__iter__():
            # print(i)
            if i[0] != 'start' and i[0] != 'end':
                user_key = (i[0], i[1])
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

        #  1.生成直播小结
        self.__everyday_live_stats(default_time, live_data_group_by_id)

        # 2.生成词频图 词云图
        self.__wordfreq_wordcloud(live_data_group_by_type)

        # 3.生成舰长图、礼物图、粉丝图、进入图、营收图、同接图、sc图、弹幕图
        self.__make_stats_picture(all_data)

    # 生成各种图片
    def __make_stats_picture(self, my_all_data):
        """
        :param my_all_data:所有数据
        :return: 输出图片
        """
        stats_list = mp.get_min_avg_data(my_all_data)
        new_stats_list = {'gift': [], 'danmu': [], 'sc': [], 'guard': [],
                          'entry': [], 'revenue': [], 'new_fans': [], 'new_medal_fans': [], 'simu_interact': []}
        for min_stats in stats_list.__iter__():
            for my_type, num in min_stats.items():
                new_stats_list[my_type].append(num)
        # 礼物图   1mins
        mp.make_min_picture(new_stats_list['gift'], 1, '送礼人次', self.live_road, 1)
        # 弹幕图   1mins
        mp.make_min_picture(new_stats_list['danmu'], 1, '弹幕数量', self.live_road, 1)
        # sc图    3mins
        sc_data = mp.trans_mins_sum(1, 3, new_stats_list['sc'])
        mp.make_min_picture(sc_data, 3, 'sc数量', self.live_road, 1)
        # guard图 3mins
        guard_data = mp.trans_mins_sum(1, 3, new_stats_list['guard'])
        mp.make_min_picture(guard_data, 3, '舰团数量', self.live_road, 1)
        # entry图 1mins
        mp.make_min_picture(new_stats_list['entry'], 1, '入场人次', self.live_road, 1)
        # 营收图   1mins
        mp.make_min_picture(new_stats_list['revenue'], 1, '营收', self.live_road, 1)
        # fans图  3mins
        new_fans_data = mp.trans_mins_sum(1, 3, new_stats_list['new_fans'])
        mp.make_min_picture(new_fans_data, 3, '新增粉丝', self.live_road, 1)
        # 粉丝团图 3mins
        new_medal_fans_data = mp.trans_mins_sum(1, 3, new_stats_list['new_medal_fans'])
        mp.make_min_picture(new_medal_fans_data, 3, '新增粉丝团', self.live_road, 1)
        # 同接图   1mins
        mp.make_min_picture(new_stats_list['simu_interact'], 1, '10分钟同接', self.live_road, 0)

    # 词频、词云图生成
    def __wordfreq_wordcloud(self, my_live_data_group_by_type):
        """

        :param my_live_data_group_by_type: 根据类型分类的消息数据
        :return: 生成词频图和词云图
        """
        word_freq_dic = lcw.get_word_freq_dic(my_live_data_group_by_type)
        word_freq_bar_num = 20
        word_freq_bar_dict = lcw.customize_word_freq_dict(word_freq_dic, word_freq_bar_num)
        lcw.make_word_freq_bar(word_freq_bar_dict, self.live_road)
        word_cloud_num = 600
        word_cloud_dict = lcw.customize_word_freq_dict(word_freq_dic, word_cloud_num)
        lcw.make_wordcloud(word_cloud_dict, ('./image/wordcloud/%s' % self.room_id), self.live_road)

    # 直播小结功能
    def __everyday_live_stats(self, my_default_time, my_live_data_group_by_id):
        """

        :param my_default_time: 开播时间
        :param my_live_data_group_by_id: 根据uid分组的直播数据
        :return: 输出直播小结
        """
        every_day_table_name = "every_day_stats"
        self.__create_everyday_sql(every_day_table_name)
        user_data = compute_user_data(my_default_time, my_live_data_group_by_id, self.medal_list, self.uid_list)
        user_stats, time_stats = get_user_stats_data(user_data)
        self.__input_stats_sql(user_stats, time_stats, every_day_table_name)

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
                     "`medal_21_avg_danmu` float not null)" \
                     "CHARSET=utf8" % table_name
        self.mysql_conn.cursor().execute(create_sql)

    # 格式化每日数据到数据库
    def __input_stats_sql(self, user_stats, time_stats, table_name):
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
        medal_1_5_num = user_stats['medal_0']['num']
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
                                                             "medal_21_avg_danmu) values('%s','%d','%f','%d'," \
                                                             "'%f','%d','%d','%d','%f','%f','%d','%d','%d'," \
                                                             "'%d', '%f', '%f'," \
                                                             "'%d','%f','%f','%d','%f','%f','%d','%f','%f'," \
                                                             "'%d','%f','%f')" % (
                         self.live_road, gift, avg_gift, danmu, avg_danmu, sc, guard, entry, avg_watch_time,
                         avg_react_watch_time, entry_num, react_num, medal_num, medal_0_num, medal_0_avg_react,
                         medal_0_avg_danmu, medal_1_5_num, medal_1_5_avg_react, medal_1_5_avg_danmu, medal_6_10_num,
                         medal_6_10_avg_react, medal_6_10_avg_danmu, medal_11_20_num, medal_11_20_avg_react,
                         medal_11_20_avg_danmu, medal_21_num, medal_21_avg_react, medal_21_avg_danmu)
        self.mysql_conn.cursor().execute(insert_sql)
        self.mysql_conn.commit()


def compute_user_data(my_default_time, my_data, my_medal_list, my_uid_list):
    """
    :param my_uid_list: uid字典
    :param my_medal_list:room_id字典
    :param my_default_time: 默认的起始时间
    :param my_data: 观众的观看记录
    :return: 原字典，但value（a list）的-1处为观看时长
    """

    uid2room = {}
    for k in my_medal_list.keys():
        uid2room[my_uid_list[k]] = my_medal_list[k]

    for k, v in my_data.items():
        watch_time = 0
        status = 'start'
        """
        status:
            start:开始状态
            entry:上一次是entry消息
            react:上一次是非entry消息
        """
        user_default_time = my_default_time

        user_msg_times_dic = {'gift': 0, 'danmu': 0, 'sc': 0, 'guard': 0, 'entry': 0, 'react': 0}

        target_medal = {'id': 0, 'level': 0}

        user_data = {}

        for record in v:
            if record[4] == 'entry' and status == 'start':
                user_default_time = record[5]
                status = 'entry'
                user_msg_times_dic['entry'] += 1
            elif record[4] == 'entry' and (status == 'entry' or status == 'react'):
                watch_time += 300
                user_default_time = record[5]
                status = 'entry'
                user_msg_times_dic['entry'] += 1
            elif record[4] != 'entry':
                watch_time += (record[5] - user_default_time).seconds
                user_default_time = record[5]
                status = 'react'
                if record[4] == 'danmu':
                    user_msg_times_dic['danmu'] += 1
                elif record[4] == 'gift':
                    user_msg_times_dic['gift'] += 1
                elif record[4] == 'guard':
                    user_msg_times_dic['guard'] += 1
                elif record[4] == 'sc':
                    user_msg_times_dic['sc'] += 1
                user_msg_times_dic['react'] += 1
            if record[2] in my_medal_list.values() or record[2] in my_uid_list.values():
                if record[3] > target_medal['level']:
                    target_medal['id'] = record[2]
                    target_medal['level'] = record[3]
                    if target_medal['id'] not in my_medal_list.values():
                        target_medal['id'] = uid2room[target_medal['id']]

        user_data['msg_times'] = user_msg_times_dic
        user_data['watch_time'] = watch_time / 60
        user_data['medal'] = target_medal

        my_data[k] = user_data

    return my_data


def get_user_stats_data(my_data):
    """
    :param my_data: user直播统计字典
    :return: no return 但会输出图片和存数据库
    """
    watch_time = {'entry': 0, 'react': 0, 'entry_num': 0, 'react_num': 0}
    medal_sum = {'medal_0': {}, 'medal_1_5': {}, 'medal_6_10': {}, 'medal_11_20': {}, 'medal_21': {}, 'all': {}}
    for k, v in medal_sum.items():
        medal_sum[k] = {'gift': 0, 'danmu': 0, 'sc': 0, 'guard': 0, 'entry': 0, 'react': 0, 'num': 0}
    for k, v in my_data.items():
        watch_time['entry'] += v['watch_time']
        watch_time['entry_num'] += 1
        if v['msg_times']['react'] > 0:
            watch_time['react'] += v['watch_time']
            watch_time['react_num'] += 1
        if v['medal']['level'] == 0:
            for my_type in v['msg_times'].keys():
                medal_sum['medal_0'][my_type] += v['msg_times'][my_type]
            medal_sum['medal_0']['num'] += 1
        elif v['medal']['level'] < 6:
            for my_type in v['msg_times'].keys():
                medal_sum['medal_1_5'][my_type] += v['msg_times'][my_type]
            medal_sum['medal_1_5']['num'] += 1
        elif v['medal']['level'] < 11:
            for my_type in v['msg_times'].keys():
                medal_sum['medal_6_10'][my_type] += v['msg_times'][my_type]
            medal_sum['medal_6_10']['num'] += 1
        elif v['medal']['level'] < 21:
            for my_type in v['msg_times'].keys():
                medal_sum['medal_11_20'][my_type] += v['msg_times'][my_type]
            medal_sum['medal_11_20']['num'] += 1
        else:
            for my_type in v['msg_times'].keys():
                medal_sum['medal_21'][my_type] += v['msg_times'][my_type]
            medal_sum['medal_21']['num'] += 1
        for my_type in v['msg_times'].keys():
            medal_sum['all'][my_type] += v['msg_times'][my_type]
        medal_sum['all']['num'] += 1
    return medal_sum, watch_time


room_id, live_date, live_road = lf.get_arg()
live = live_analysis(room_id=room_id, live_date=live_date, live_road=live_road)
live.get_everyday_live_stats()
