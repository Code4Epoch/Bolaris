# -*- coding: utf-8 -*- #
# ------------------------------------------------------------------
# File Name:        
# Author:           
# Version:          
# Created:          
# Description:      
# Function List:               
# History:
#       <author>        <version>       <time>      <desc>
# ------------------------------------------------------------------
import pymysql


class daily_mysql_store(object):

    def __init__(self, config, stats_data, data, live_road, live_type):
        self.config = config
        self.stats_data = stats_data
        self.data = data
        self.live_road = live_road
        self.live_type = live_type
        self.mysql_conn = pymysql.connect(host=self.config['host'], port=self.config['port'], user=config['user'],
                                          password=self.config['password'], db=self.config['dbname'])
        self.__create_everyday_sql()

    def daily_stats_store(self):
        gift = self.stats_data["gift_num"]
        danmu = self.stats_data["danmu_num"]
        avg_danmu = self.stats_data["avg_danmu"]
        sc = self.stats_data["sc_num"]
        guard = self.stats_data["guard_num"]
        avg_watch_time = self.stats_data["watch_time"]
        avg_react_watch_time = self.stats_data["interactor_avg_watch_time"]
        entry_num = self.stats_data["audience_num"]
        medal_num = self.stats_data["audience_num"] - self.stats_data["_0_medal"]
        react_num = self.stats_data["interact_num"]
        medal_0_num = self.stats_data["_0_medal"]
        medal_0_avg_react = self.stats_data["_0_medal_interact_num"] / medal_0_num
        medal_0_avg_danmu = self.stats_data["_0_medal_danmu_num"] / medal_0_num
        medal_1_5_num = self.stats_data["_1_5_medal"]
        medal_1_5_avg_react = self.stats_data["_1_5_medal_interact_num"] / medal_1_5_num
        medal_1_5_avg_danmu = self.stats_data["_1_5_medal_danmu_num"] / medal_1_5_num
        medal_6_10_num = self.stats_data["_6_10_medal"]
        medal_6_10_avg_react = self.stats_data["_6_10_medal_interact_num"] / medal_6_10_num
        medal_6_10_avg_danmu = self.stats_data["_6_10_medal_danmu_num"] / medal_6_10_num
        medal_11_20_num = self.stats_data["_11_20_medal"]
        medal_11_20_avg_react = self.stats_data["_11_20_medal_interact_num"] / medal_11_20_num
        medal_11_20_avg_danmu = self.stats_data["_11_20_medal_danmu_num"] / medal_11_20_num
        medal_21_num = self.stats_data["_21_medal"]
        medal_21_avg_react = self.stats_data["_21_medal_interact_num"] / medal_21_num
        medal_21_avg_danmu = self.stats_data["_21_medal_danmu_num"] / medal_21_num
        revenue = self.stats_data["sum_revenue"]
        sc_revenue = self.stats_data["sc_revenue"]
        guard_revenue = self.stats_data["guard_revenue"]
        gift_revenue = self.stats_data["gift_revenue"]
        avg_revenue = revenue / entry_num
        live_time = self.stats_data["live_long"].split(":")[-1]

        max_renqi = self.__find_ordered_max(0, self.data['renqi'])
        max_watched = self.__find_ordered_max(0, self.data["watched"])
        max_simu_interact = self.__find_ordered_max(1, self.data['simu_interact'])
        max_min_danmu = self.__find_ordered_max(0, self.data['danmu'])

        insert_sql = self.config["stats_sql"]
        paras = (self.live_road.split("_dm")[0], max_renqi, max_watched, max_simu_interact, max_min_danmu, gift, danmu,
                 round(avg_danmu, 2), sc, guard, round(avg_watch_time, 2),
                 round(avg_react_watch_time,2), entry_num, react_num, medal_num, medal_0_num,
                 round(medal_0_avg_react, 2),
                 round(medal_0_avg_danmu, 2), medal_1_5_num, round(medal_1_5_avg_react, 2),
                 round(medal_1_5_avg_danmu, 2), medal_6_10_num, round(medal_6_10_avg_react, 2),
                 round(medal_6_10_avg_danmu, 2), medal_11_20_num, round(medal_11_20_avg_react, 2),
                 round(medal_11_20_avg_danmu, 2), medal_21_num, round(medal_21_avg_react, 2),
                 round(medal_21_avg_danmu, 2), round(revenue, 2),
                 round(sc_revenue, 2), round(gift_revenue, 2), round(guard_revenue, 2),
                 round(avg_revenue, 2), self.live_type, live_time)

        try:
            self.mysql_conn.cursor().execute(insert_sql, paras)
            self.mysql_conn.commit()
        except Exception as e:
            print(insert_sql % paras)
            print("commit failed", e)

    # 根据格式自动创造一个弹幕数据表
    def __create_everyday_sql(self):
        """

        :return: 创造一张everyday——stats表
        """
        create_sql = self.config['create_sql']
        try:
            self.mysql_conn.cursor().execute(create_sql)
            self.mysql_conn.commit()
        except Exception as e:
            print(create_sql)
            print("commit failed", e)

    @staticmethod
    def __find_ordered_max(place, data):
        my_max = 0
        for i in data:
            if i[place] > my_max:
                my_max = i[place]
        return my_max
