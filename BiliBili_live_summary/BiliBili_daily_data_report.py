# -*- coding: utf-8 -*- #
# ------------------------------------------------------------------
# File Name:        BiliBili_daily_data_report
# Author:           ydyjya
# Version:          0.3
# Created:          2022/1/24
# Description:      生成每日的直播数据总结
# Function List:               
# History:
#       <author>        <version>       <time>      <desc>
#       ydyjya          0.1             2021/7/9    create
#       ydyjya          0.2             2021/8/18   修改了风格，增加了部分功能
#       ydyjya          0.3             2022/1/24   解耦函数，修改风格
# ------------------------------------------------------------------
import json

from Bolaris_Exception import loader_config_error
from BiliBili_live_summary import data_loader
from BiliBili_live_summary import wordcloud_maker
from BiliBili_live_summary import daily_data_statistics
from BiliBili_live_summary import chart_maker
from BiliBili_live_summary import mysql_statistics


def read_para(path):
    # 读取本目录下的参数文件
    with open("./%s.json" % path, encoding='utf-8') as config:
        para = json.loads(config.read())

    return para



class BiliBili_daily_data_generator(object):
    def __init__(self, config):
        self.config = config

        self.room_id, self.live_road, self.live_type = self.__get_args()
        self.my_data_loader = data_loader.daily_data_loader(read_para("mysql_config"), self.config, self.live_road)

    def generate(self):

        data = self.my_data_loader.data_set
        try:
            word_freq = wordcloud_maker.word_reader(data["danmu"], "jieba", cust_dict=True).get_word_freq()
            wordcloud_maker.make_wordcloud(word_freq, self.room_id, self.live_type)
        except TypeError:
            print("似乎当前时段没有弹幕捏~")
            if input("继续输入1，停止输入其他") == 1:
                word_freq = {"无词汇": 0}
            else:
                exit(0)
        statistics, data = daily_data_statistics.daily_data_statistics(data, read_para("medal_config")).get_statistics()
        my_chart_maker = chart_maker.summary_chart_maker(statistics, data, word_freq,
                                                         room_id=self.room_id, live_type=self.live_type)
        my_chart_maker.make_chart()

        mysql_store = mysql_statistics.daily_mysql_store(read_para("mysql_config"), stats_data=statistics,
                                                         data=data, live_road=self.live_road, live_type=self.live_type)
        mysql_store.daily_stats_store()

    def __get_args(self):
        print("请输入房间号:")
        # room_id = "22634198"
        room_id = input()
        if self.config['read_type'] == "default":
            print("请输入日期:\n格式为202x_xx_xx")
            # live_date = "2022_03_12"
            live_date = input()
            live_road = "%s_%s_dm" % (live_date, room_id)
            if self.config['live_mark'] == "on":
                print("请输入直播类型备注:")
                # live_type = "A-SOUL小剧场"
                live_type = input()
                return room_id, live_road, live_date + live_type
            return room_id, live_road, "room_id:%s,日期为%s的直播" % (room_id, live_date)
        elif self.config['read_type'] == "customization":
            print("请输入时段:\n格式为202x_xx_xx-00:00:00/202x_xx_xx-23:59:59")
            # live_date = "2022_01_27-18:55:00/2022_01_28-8:00:00"
            live_date = input()
            live_road = "%s/_%s_dm" % (live_date, room_id)
            if self.config['live_mark'] == "on":
                print("请输入直播类型备注:")
                # live_type = "贝拉单人直播"
                live_type = input()
                return room_id, live_road, live_date + live_type
            return room_id, live_date, "room_id:%s,日期为%s的直播" % (room_id, live_date)
        else:
            raise loader_config_error("请确定读取方式为默认方式（default）或自定义方式(customization)")



