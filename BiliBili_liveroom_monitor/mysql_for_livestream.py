# -*- coding: utf-8 -*- #
# ------------------------------------------------------------------
# File Name:        mysql_for_livestream
# Author:           ydyjya
# Version:          0.3
# Created:          2022/1/23
# Description:      将直播流获取到的数据存储到数据库中
# Function List:    get_time()  --获取时间数组
# History:
#       <author>        <version>       <time>      <desc>
#       ydyjya          0.3             2022/1/23   create
# ------------------------------------------------------------------
import pymysql
import time


# 获取时间
def get_time():
    local_time = time.time()
    time_array = time.localtime(local_time)
    return time_array


class mysql_for_livestream(object):
    def __init__(self, config, room_id):

        self.config = config
        self.room_id = room_id
        self.mysql_conn = pymysql.connect(host=self.config['host'], port=self.config['port'], user=config['user'],
                                          password=self.config['password'], db=self.config['dbname'])

        self.insert_sql_pt1 = self.config['insert_pt1']
        self.insert_sql_pt2 = self.config['insert_pt2']
        self.insert_road = self.config['insert_road']

        if get_time().tm_mday < 10:
            self.now_day = "0%d" % get_time().tm_mday
        else:
            self.now_day = "%d" % get_time().tm_mday
        if get_time().tm_mon < 10:
            self.now_mon = "0%d" % get_time().tm_mon
        else:
            self.now_mon = "%d" % get_time().tm_mon

        self.table_name = self.insert_road % (get_time().tm_year, self.now_mon, self.now_day, self.room_id)
        self.__create_dm_sql(self.table_name)

    # 根据格式自动创造一个弹幕数据表
    def __create_dm_sql(self, table_name):
        create_sql = "CREATE TABLE IF NOT EXISTS `%s` (" \
                     "`uid` varchar(255) not null, " \
                     "`user_name` varchar(255) not null, " \
                     "`room_id_of_medal` varchar(255) not null, " \
                     "`level_of_medal` int not null, " \
                     "`msg_type` varchar(255) not null, " \
                     "`time_stamp` timestamp not null, " \
                     "`text` text not null, " \
                     "`ul` int not null, " \
                     "`sc_price` int not null, " \
                     "`gift_ID` int not null, " \
                     "`gift_price` float not null," \
                     "`fans_type` int not null)" \
                     "CHARSET=utf8" % table_name
        self.mysql_conn.cursor().execute(create_sql)

    def insert_data(self, paras):
        try:
            if paras[5][6:8] != self.now_day:

                if get_time().tm_mday < 10:
                    self.now_day = "0%d" % get_time().tm_mday
                else:
                    self.now_day = "%d" % get_time().tm_mday
                if get_time().tm_mon < 10:
                    self.now_mon = "0%d" % get_time().tm_mon
                else:
                    self.now_mon = "%d" % get_time().tm_mon

                self.table_name = self.insert_road % (
                    get_time().tm_year, self.now_mon, self.now_day, self.room_id)
                self.__create_dm_sql(self.table_name)
            self.mysql_conn.cursor().execute(self.insert_sql_pt1 % self.table_name + self.insert_sql_pt2, paras)
            self.mysql_conn.commit()
            # print('insert successful!')
        except Exception as e:
            print('Insert Failed!', e)
            print(self.insert_sql_pt1 % self.table_name + self.insert_sql_pt2 % paras)

    def insert_many(self):
        # TODO:建立一个timer或者counter然后用excutemany来减少i/o操作，目前还未想好，先丢在这里
        pass
