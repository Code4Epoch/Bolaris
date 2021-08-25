# -*- coding: utf-8 -*- #
# ------------------------------------------------------------------
# File Name:        muti_live_summary
# Author:           ydyjya
# Version:          1.0
# Created:          2021/7/14
# Description:      多场直播的综合制图
# Function List:    muti_live_summary() --多场直播的对比
# History:
#       <author>        <version>       <time>      <desc>
#       ydyjya          1.0             2021/7/14   create
# ------------------------------------------------------------------
from live import tool_function as tf
from live import make_chart as mc
import pymysql


class muti_live_summary:

    def __init__(self, live_id_list, theme):
        # 获取要综合分析的直播列表
        self.live_id_list = live_id_list
        self.live_num = len(live_id_list)
        self.title = theme
        self.config = tf.get_config("./config/live_data_summary/live_data_summary_mysql_config.json")

        # mysql配置
        self.host = self.config['mysql_config']['host']
        self.port = self.config['mysql_config']['port']
        self.user = self.config['mysql_config']['user']
        self.password = self.config['mysql_config']['password']
        self.db = self.config['mysql_config']['db']

        self.line_color = self.config['line_color']

        try:
            self.mysql_conn = pymysql.connect(host=self.host, port=self.port,
                                              user=self.user, password=self.password, db=self.db)
        except Exception as e:
            print("connect failed")
            raise e

        self.live_data = self.__get_data()

    def get_muit_live_report(self):
        """

        @return: 全部功能的执行
        """
        self.__make_picture(self.live_data)
        self.__create_muti_analysis_table()
        fans_data = self.__distinct_fans_data()
        self.__fans_data2sql(fans_data)
        self.__fans_data_stats()

    def __get_data(self):
        """

        @return: 从数据库中读取数据，返回data_dict{uid:[各种信息]}
        """
        data = []
        sql = "select * from every_day_stats where live = '%s'"
        for live_id in self.live_id_list:
            with self.mysql_conn.cursor() as cursor:
                cursor.execute(sql % live_id)
            live_record = cursor.fetchone()
            data.append(live_record)
        with self.mysql_conn.cursor() as cursor:
            cursor.execute("select column_name from Information_schema.columns where table_Name = 'every_day_stats'")
        columns_name = cursor.fetchall()
        data_dict = {}
        idx = 0
        max_length = len(data[0])
        for column_name in columns_name:
            temp_data_list = []
            for record in data:
                temp_data_list.append(record[idx])
            data_dict[column_name[0]] = temp_data_list
            idx += 1
            if idx >= max_length:
                break
        return data_dict

    def __make_picture(self, my_data):
        """

        @param my_data: 根据__get_data函数获得的data数据
        @return: 作图
        """
        key = my_data['live']
        live_type = my_data['live_type']
        my_data.pop('live')
        my_data.pop('live_type')

        min_danmu = []
        live_long = my_data['live_long']
        danmu = my_data['danmu']
        for i in range(0, len(live_long)):
            min_danmu.append(int(danmu[i] / live_long[i]))
        color_idx = 0
        color_idx = mc.make_muti_picture(key, [min_danmu], '分均弹幕', self.title, self.line_color, color_idx, live_type)

        color_idx = mc.make_muti_picture(key, [my_data['avg_danmu']], '人均弹幕', self.title,
                                         self.line_color, color_idx, live_type)

        color_idx = mc.make_muti_picture(key, [my_data['entry'], my_data['medal_num'], my_data['react_num']],
                                         '入场人数&入场粉丝团人数&互动人数', self.title, self.line_color, color_idx, live_type)

        mc.make_muti_radar_picture(key, [min_danmu, my_data['avg_danmu'], my_data['entry'], my_data['medal_num'],
                                         my_data['react_num']], '分均弹幕&人均弹幕&入场人数&入场粉丝团人数&互动人数', self.title,
                                   self.line_color)

    def __distinct_fans_data(self):
        """

        @return: 获得粉丝信息{uid:[各种信息]}
        """
        live_long_list = self.live_data['live_long']
        sql = "select * from %s_fans"
        fans_dict = {}
        idx = 0
        for live_id in self.live_id_list:
            with self.mysql_conn.cursor() as cursor:
                cursor.execute(sql % live_id)
            live_records = cursor.fetchall()
            for fans_record in live_records:
                uid = fans_record[0]
                watch_time = float(fans_record[1])
                interact_times = int(fans_record[2])
                danmu_times = int(fans_record[3])
                gift_times = int(fans_record[4])
                sc_times = int(fans_record[5])
                guard_times = int(fans_record[6])
                pay = float(fans_record[7])
                medal_id = fans_record[8]
                medal_level = int(fans_record[9])
                if uid == 0:
                    continue
                if uid not in fans_dict:
                    fans_dict[uid] = {'watch_time': watch_time, 'interact_times': interact_times,
                                      'danmu_times': danmu_times, 'gift_times': gift_times, 'sc_times': sc_times,
                                      'guard_times': guard_times, 'pay': pay, 'medal_id': medal_id,
                                      'medal_level': medal_level, 'attend': 1}
                    # 是否全勤
                    if watch_time >= live_long_list[idx] - 15:
                        fans_dict[uid]['full_att'] = 1
                    else:
                        fans_dict[uid]['full_att'] = 0
                    # 是否偶然进入
                    if watch_time == 0:
                        fans_dict[uid]['accidental'] = 1
                    else:
                        fans_dict[uid]['accidental'] = 0
                else:
                    fans_dict[uid]['watch_time'] += watch_time
                    fans_dict[uid]['interact_times'] += interact_times
                    fans_dict[uid]['danmu_times'] += danmu_times
                    fans_dict[uid]['gift_times'] += gift_times
                    fans_dict[uid]['sc_times'] += sc_times
                    fans_dict[uid]['guard_times'] += guard_times
                    fans_dict[uid]['pay'] += pay
                    fans_dict[uid]['attend'] += 1
                    # 是否全勤
                    if watch_time >= live_long_list[idx] - 15:
                        fans_dict[uid]['full_att'] += 1
                    # 是否偶然进入
                    if watch_time == 0:
                        fans_dict[uid]['accidental'] += 1
                    # 取最高粉丝牌
                    if medal_level > fans_dict[uid]['medal_level']:
                        fans_dict[uid]['medal_id'] = medal_id
                        fans_dict[uid]['medal_level'] = medal_level
            idx += 1
        return fans_dict

    def __create_muti_analysis_table(self):
        create_sql = "create table if not exists `%s` (" \
                     "`uid` varchar(255) primary key not null," \
                     "`watch_time` float not null," \
                     "`interact_times` int not null," \
                     "`danmu_times` int not null," \
                     "`gift_times` int not null," \
                     "`sc_times` int not null," \
                     "`guard_times` int not null," \
                     "`pay` float not null," \
                     "`medal_id` varchar(255) not null," \
                     "`medal_level` int not null," \
                     "`attend` int not null," \
                     "`full_att` int not null," \
                     "`accidental` int not null)" \
                     "CHARSET=utf8" % (self.title + "_fans")
        self.mysql_conn.cursor().execute(create_sql)

    def __fans_data2sql(self, my_fans_data):
        """

        @param my_fans_data: fans_dict{uid:[各种信息]}
        @return: 存入数据库
        """
        sql = "insert into %s_fans "
        header = '(uid, watch_time, interact_times, danmu_times, gift_times, sc_times, guard_times, pay, medal_id, ' \
                 'medal_level, attend, full_att, accidental) '
        values = 'VALUES(%s, %.2f, %d, %d, %d, %d, %d, %.2f, %s, %d, %d, %d, %d)'
        sql_model = sql + header + values
        for my_uid, value in my_fans_data.items():
            uid = my_uid
            watch_time = value['watch_time']
            interact_times = value['interact_times']
            danmu_times = value['danmu_times']
            gift_times = value['gift_times']
            sc_times = value['sc_times']
            guard_times = value['guard_times']
            pay = value['pay']
            medal_id = value['medal_id']
            medal_level = value['medal_level']
            attend = value['attend']
            full_att = value['full_att']
            accidental = value['accidental']
            insert_sql = sql_model % (
                self.title, uid, watch_time, interact_times, danmu_times, gift_times, sc_times, guard_times,
                pay, medal_id, medal_level, attend, full_att, accidental)
            try:
                with self.mysql_conn.cursor() as cur:
                    cur.execute(insert_sql)
                self.mysql_conn.commit()
            except Exception as e:
                self.mysql_conn.rollback()
                print("Commit Failed!\n%s" % insert_sql)

    def __fans_data_stats(self):
        """

        @return: 粉丝相关的图
        """
        table_name = self.title + "_fans"
        cur = self.mysql_conn.cursor()

        self.__fans_att_pie(table_name=table_name, cur=cur)

        self.__fans_medal_pie(table_name=table_name, cur=cur)

        self.__fans_pay_pie(table_name=table_name, cur=cur)

        self.__fans_interact_pie(table_name=table_name, cur=cur)

    def __fans_att_pie(self, table_name, cur):
        """

        @param table_name: 表头
        @param cur: cursor
        @return: 粉丝参与类型构成饼图
        """
        get_all_num_sql = "select count(*) from %s" % table_name
        cur.execute(get_all_num_sql)
        all_num = cur.fetchone()

        get_acc_sql = "select count(*) from %s where accidental = 1 and attend = 1 and medal_id = 0" % table_name

        cur.execute(get_acc_sql)
        acc_data = cur.fetchone()

        ger_full_att_sql = "select count(*) from %s where attend = %d" % (table_name, self.live_num)
        cur.execute(ger_full_att_sql)
        full_att_data = cur.fetchone()

        other_num = all_num[0] - acc_data[0] - full_att_data[0]
        entry_x = ["纯路人", "❤全勤民❤", "其他观众"]
        entry_y = [acc_data, full_att_data, other_num]
        mc.make_muti_pie(entry_x, entry_y, '观众构成', self.title)

    def __fans_medal_pie(self, table_name, cur):
        """

        @param table_name: 表头
        @param cur: cursor
        @return: 粉丝牌构成粉丝图
        """
        get_no_medal_sql = "select count(*) from %s where medal_id = 0" % table_name
        cur.execute(get_no_medal_sql)
        no_medal_num = cur.fetchone()

        get_1_5_medal_sql = "select count(*) from %s where medal_level <= 5 and medal_level > 0 " % table_name
        cur.execute(get_1_5_medal_sql)
        _1_5_medal_num = cur.fetchone()

        get_6_10_medal_sql = "select count(*) from %s where medal_level <= 10 and medal_level > 5 " % table_name
        cur.execute(get_6_10_medal_sql)
        _6_10_medal_num = cur.fetchone()

        get_11_20_medal_sql = "select count(*) from %s where medal_level <= 20 and medal_level > 10 " % table_name
        cur.execute(get_11_20_medal_sql)
        _11_20_medal_num = cur.fetchone()

        get_21_medal_sql = "select count(*) from %s where medal_level > 20 " % table_name
        cur.execute(get_21_medal_sql)
        _21_medal_num = cur.fetchone()

        medal_y = [no_medal_num, _1_5_medal_num, _6_10_medal_num, _11_20_medal_num, _21_medal_num]
        medal_x = ['无粉丝牌', '1到5级粉丝牌', '6到10级粉丝牌', '11到20级粉丝牌', '21级以上粉丝牌']
        mc.make_muti_pie(medal_x, medal_y, '粉丝牌构成', self.title)

    def __fans_pay_pie(self, table_name, cur):
        """

        @param table_name: 表头
        @param cur: cursor
        @return: 粉丝付费饼图
        """
        get_all_num_sql = "select count(*) from %s" % table_name
        cur.execute(get_all_num_sql)
        all_num = cur.fetchone()[0]

        get_pay_num_sql = "select count(*) from %s where pay > 0" % table_name
        cur.execute(get_pay_num_sql)
        get_pay_num = cur.fetchone()[0]

        pay_ratio = get_pay_num / all_num

        _10_yuan_num_sql = "select count(*) from %s where pay > 0 and pay < 10" % table_name
        cur.execute(_10_yuan_num_sql)
        _10_yuan_num = cur.fetchone()

        _10_100_yuan_num_sql = "select count(*) from %s where pay >= 10 and pay < 100" % table_name
        cur.execute(_10_100_yuan_num_sql)
        _10_100_yuan_num = cur.fetchone()

        _100_300_yuan_num_sql = "select count(*) from %s where pay >= 100 and pay < 300" % table_name
        cur.execute(_100_300_yuan_num_sql)
        _100_300_yuan_num = cur.fetchone()

        _300_1000_yuan_num_sql = "select count(*) from %s where pay >= 300 and pay < 1000" % table_name
        cur.execute(_300_1000_yuan_num_sql)
        _300_1000_yuan_num = cur.fetchone()

        _1000_yuan_num_sql = "select count(*) from %s where pay >= 1000" % table_name
        cur.execute(_1000_yuan_num_sql)
        _1000_yuan_num = cur.fetchone()

        pay_x = ['10元以下', '10元以上100元以下（含10元）',
                 "100元以上300元以下（含100元）", "300元以上1000元以下（含300元）", "1000元以上"]
        pay_y = [_10_yuan_num, _10_100_yuan_num, _100_300_yuan_num, _300_1000_yuan_num, _1000_yuan_num]
        mc.make_muti_pie(pay_x, pay_y, "总付费人数：%s\n付费率：%.4f" % (get_pay_num, pay_ratio), self.title)

    def __fans_interact_pie(self, table_name, cur):
        """

        @param table_name: 表头
        @param cur: cursor
        @return: 粉丝互动情况饼图
        """
        get_all_num_sql = "select count(*) from %s" % table_name
        cur.execute(get_all_num_sql)
        all_num = cur.fetchone()[0]

        get_no_interact_sql = "select count(*) from %s where interact_times = 0" % table_name
        cur.execute(get_no_interact_sql)
        no_interact_num = cur.fetchone()

        interact_num = all_num - no_interact_num[0]
        interact_ratio = (all_num - no_interact_num[0]) / all_num

        get_1_5_interact_sql = "select count(*) from %s where interact_times > 0 and interact_times <= 5" % table_name
        cur.execute(get_1_5_interact_sql)
        _1_5_interact_num = cur.fetchone()

        get_5_20_interact_sql = "select count(*) from %s where interact_times > 5 and interact_times <= 20" % table_name
        cur.execute(get_5_20_interact_sql)
        _5_20_interact_num = cur.fetchone()

        get_20_50_interact_sql = "select count(*) from %s where interact_times > 20 and " \
                                 "interact_times <= 50" % table_name
        cur.execute(get_20_50_interact_sql)
        _20_50_interact_num = cur.fetchone()

        get_50_100_interact_sql = "select count(*) from %s where interact_times > 50 and " \
                                  "interact_times <= 100" % table_name
        cur.execute(get_50_100_interact_sql)
        _50_100_interact_num = cur.fetchone()

        get_100_500_interact_sql = "select count(*) from %s where interact_times > 100 and " \
                                   "interact_times <= 500" % table_name
        cur.execute(get_100_500_interact_sql)
        _100_500_interact_num = cur.fetchone()

        get_500_interact_sql = "select count(*) from %s where interact_times > 100 and " \
                               "interact_times > 500" % table_name
        cur.execute(get_500_interact_sql)
        _500_interact_num = cur.fetchone()

        interact_x = ['未参加互动', '1到5次互动（含5次）', "5到20次互动（含20次）", "20到50次互动（含50次）",
                      "50到100次互动（含100次）", " 100到500次互动（含500次）", "500次以上互动"]
        interact_y = [no_interact_num, _1_5_interact_num, _5_20_interact_num, _20_50_interact_num, _50_100_interact_num,
                      _100_500_interact_num, _500_interact_num]
        mc.make_muti_pie(interact_x, interact_y,
                         "总互动人数（去重）：%d\n互动率：%.4f" % (interact_num, interact_ratio), self.title)


live_str, theme = tf.get_live_id_theme()
muti_report = muti_live_summary(live_str, theme)
muti_report.get_muit_live_report()