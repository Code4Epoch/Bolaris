# -*- coding: utf-8 -*- #
# ------------------------------------------------------------------
# File Name:        data_loader
# Author:           ydyjya
# Version:          0.3
# Created:          2022/1/24
# Description:      从数据库中获取数据
# Function List:               
# History:
#       <author>        <version>       <time>      <desc>
#       ydyjya          0.3             2022/1/24   create
# ------------------------------------------------------------------
import pymysql
import datetime as dt1
from BiliBili_live_summary import global_var
from datetime import datetime as dt2


def next_day(now_sql_road):
    """
    本函数为合并多天数据的辅助函数
    :param now_sql_road:
    :return:
    """
    date_list = now_sql_road.split('_')
    stamp = dt2(int(date_list[0]), int(date_list[1]), int(date_list[2]))
    return (stamp + dt1.timedelta(days=+1)).strftime("%Y_%m_%d") + "_%s_dm" % date_list[3]


def get_interval(time_duration):
    """
    本函数为customization参数的辅助函数，用来获取merge_days
    :param time_duration:
    :return:
    """
    start, end = time_duration.split('/')[0], time_duration.split('/')[1]
    other_format = time_duration.split('/')[2]
    start = dt2.strptime(start.split('-')[0], '%Y_%m_%d')
    end = dt2.strptime(end.split('-')[0], '%Y_%m_%d')
    day_num = (end - start).days + 1
    return day_num, start.strftime("%Y_%m_%d") + other_format


class daily_data_loader(object):

    def __init__(self, sql_config, loader_config, sql_road):

        self.sql_config = sql_config
        self.loader_config = loader_config

        self.sql_road = sql_road
        self.mysql_conn = pymysql.connect(
            host=self.sql_config['host'], port=self.sql_config['port'], user=sql_config['user'],
            password=self.sql_config['password'], db=self.sql_config['dbname'])

        self.data_sql = self.sql_config['sel_sql_data']

        self.read_type = self.loader_config['read_type']
        self.merge_days = self.loader_config['merge_days']

        self.data_set = self.__data_reader()

    def __data_reader(self):
        data_set = []
        now_road = self.__get_road()
        for i in range(self.merge_days):
            print("reading table:%s" % now_road)
            try:
                with self.mysql_conn.cursor() as cur:
                    cur.execute(self.data_sql % now_road)
                    data_set.extend(cur.fetchall())
                now_road = next_day(now_road)
            except pymysql.err.ProgrammingError as e:
                print("table:%s not exist" % now_road)
                break
        data_set, start_time, end_time = self.__data_partition(data_set)
        data_set["start_time"] = start_time
        data_set["end_time"] = end_time
        return data_set

    def __get_road(self):
        """
        本函数根据read_type配置了合并间隔和路径参数并返回
        :return:
        """
        if self.read_type == "customization":
            self.merge_days, road = get_interval(self.sql_road)

        elif self.read_type == "default":
            road = self.sql_road

        else:
            road = self.sql_road

        return road

    def __data_partition(self, data_set):
        read_flag = False
        classified_data = {}
        start_time, end_time = None, None
        for msg in data_set:
            if read_flag is False:
                if self.read_type == "default" and msg[global_var.MSG_TYPE] == "start":
                    read_flag = True
                    start_time = msg[global_var.TIME_STAMP]
                elif self.read_type == "customization" \
                        and msg[global_var.TIME_STAMP] >= dt2.strptime(self.sql_road.split("/")[0], '%Y_%m_%d-%H:%M:%S'):
                    read_flag = True
                    start_time = msg[global_var.TIME_STAMP]
            elif read_flag is True:
                if msg[global_var.MSG_TYPE] in classified_data:
                    classified_data[msg[global_var.MSG_TYPE]].append(msg)
                else:
                    classified_data[msg[global_var.MSG_TYPE]] = [msg]
                if self.read_type == "default" and msg[global_var.MSG_TYPE] == "end":
                    end_time = msg[global_var.TIME_STAMP]
                    return classified_data, start_time, end_time
                elif self.read_type == "customization" and \
                        msg[global_var.TIME_STAMP] >= dt2.strptime(self.sql_road.split("/")[1], '%Y_%m_%d-%H:%M:%S'):
                    end_time = msg[global_var.TIME_STAMP]
                    return classified_data, start_time, end_time
