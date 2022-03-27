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
import json
import os

from PIL import Image

from pyecharts import options as opts
from pyecharts.charts import Bar
from pyecharts.charts import PictorialBar
from pyecharts.charts import Pie
from pyecharts.charts import Line
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType
from pyecharts.render import make_snapshot
from snapshot_pyppeteer import snapshot as ss1

img_load = \
    "var img = new Image();img.src = './src/%s/%s';"


class summary_chart_maker(object):

    def __init__(self, data, order_data, word_freq, room_id, live_type):
        self.room_id = room_id
        self.live_type = live_type
        self.data = data
        self.order_data = order_data
        self.word_freq = word_freq
        self.__read_config()
        self.bar_bg_x, self.bar_bg_y = self.load_background_opacity("background.png", 50)
        self.pie_bg_x, self.pie_bg_y = self.load_background_opacity("pie_background.png", 0)
        self.bar_bg_load = img_load % (self.room_id, "background_opacity.png")
        self.pie_bg_load = img_load % (self.room_id, "pie_background.png")

    def load_background_opacity(self, file_name, opacity):
        path = "./src/%s/%s" % (self.room_id, file_name)
        img = Image.open(path)
        img = img.convert('RGBA')
        x, y = img.size
        if opacity == 0:
            return x, y
        for i in range(x):
            for k in range(y):
                color = img.getpixel((i, k))
                color = color[:-1] + (opacity,)
                img.putpixel((i, k), color)
        new_path = path.split(".png")[0] + "_opacity.png"
        img.save(new_path)
        return x, y

    def make_chart(self):
        # 1-参与-未参与互动观众数据对比
        self.__interactor_audience_compare()
        # 2-观众/粉丝团数据构成
        self.__medal_audience_compare()
        # 3-词频图
        self.__word_freq_pictorial_bar()
        # 5-类型营收饼图
        self.__revenue_type_pie(["礼物营收", "醒目留言营收", "舰团营收"])
        # 6-金额营收饼图
        self.__revenue_price_pie(["10元以下", "10-100元", "100元以上"])
        # 7-时序营收热力图
        self.__ordered_data_hot_line("时序营收热力图", 7, "min_revenue")
        # 8-时序弹幕热力图
        self.__ordered_data_hot_line("时序弹幕热力图", 8, "danmu")
        # 9-时序人气热力图
        self.__ordered_data_hot_line("时序人气热力图", 9, "renqi")
        # 10-时序高能榜热力图
        self.__ordered_data_hot_line("时序高能榜热力图", 10, "hot_rank")
        # 11-sc热力图
        self.__ordered_data_hot_line("时序sc热力图", 11, "sc_data")
        # 12-舰团热力图
        self.__ordered_data_hot_line("时序舰团热力图", 12, "guard_data")
        # 13-时序同接图
        self.__ordered_data_hot_line("时序同接图", 13, "simu_interact")
        # 14-时序涨粉热力图
        self.__ordered_data_hot_line("时序涨粉累加图", 14, "fans_change")
        # 15-时序分区排名图
        self.__ordered_data_hot_line("时序分区排名图", 15, "rank_num")
        # 16-时序观看人数图
        self.__ordered_data_hot_line("时序观看人数累加图", 16, "watched")
        # 17-粉丝交叉图
        self.cross_medal_pie()

    def __read_config(self):
        with open("./src/%s/config.json" % self.room_id, encoding="utf-8") as config:
            config = json.loads(config.read())
        self.username = config["user_name"]
        self.theme_color = config["theme_color"]
        self.series_color = config['series_color']

    def __interactor_audience_compare(self):
        ops = opts.InitOpts(
            width="%dpx" % self.bar_bg_x,
            height="%dpx" % self.bar_bg_y,
            bg_color={"type": "pattern", "image": JsCode("img"), "repeat": "no-repeat"},
            theme=ThemeType.LIGHT)
        pic = (
            Bar(init_opts=ops)
                .add_xaxis(['估测观看时长（单位:小时）', '人均互动条数(单位:条)', '人均弹幕条数(单位:条)'])
                .add_yaxis("参与互动的观众",
                           [round(self.data["interactor_avg_watch_time"] / 3600, 3),
                            round(self.data["interactor_avg_danmu"], 2),
                            round(self.data["interactor_avg_interact"], 2)])
                .add_yaxis("所有观众",
                           [round(self.data["watch_time"] / 3600, 3),
                            round(self.data["avg_danmu"], 2),
                            round(self.data["avg_interact"], 2)])
                .set_global_opts(title_opts=opts.TitleOpts(title="参与互动/未参与互动观众对比",
                                                           pos_left="30%",
                                                           title_textstyle_opts=opts.series_options.TextStyleOpts(
                                                               color=self.theme_color,
                                                               font_size=45,
                                                               font_weight='bold'),
                                                           ),
                                 xaxis_opts=opts.AxisOpts(axislabel_opts=
                                                          opts.LabelOpts(font_size=20, color="auto",
                                                                         font_weight='bold')),
                                 yaxis_opts=opts.AxisOpts(axistick_opts=opts.AxisTickOpts(is_show=True),
                                                          splitline_opts=opts.SplitLineOpts(is_show=True)),
                                 legend_opts=opts.LegendOpts(item_width=50, item_height=28, pos_top="4%",
                                                             textstyle_opts=opts.TextStyleOpts(
                                                                 color="black",
                                                                 font_size=20,
                                                                 font_weight='bold'
                                                             )))

                .set_series_opts(label_opts=opts.LabelOpts(font_size=40, font_weight='bold', color="black"))
        )
        pic.add_js_funcs(self.bar_bg_load)
        save_path = "./output/%s" % self.live_type
        if os.path.exists(save_path) is False:
            os.makedirs(save_path)
        make_snapshot(ss1, pic.render(), save_path + "/1-参与-未参与互动观众数据对比.png", pixel_ratio=1)

    def __medal_audience_compare(self):
        ops = opts.InitOpts(
            width="%dpx" % self.bar_bg_x,
            height="%dpx" % self.bar_bg_y,
            bg_color={"type": "pattern", "image": JsCode("img"), "repeat": "no-repeat"},
            theme=ThemeType.LIGHT)
        watch_num = self.data["_0_medal"] + self.data["_1_5_medal"] + self.data["_6_10_medal"] + \
                    self.data["_11_20_medal"] + self.data["_21_medal"]
        pic = (
            Bar(init_opts=ops)
                .add_xaxis(['未获取粉丝牌的观众', '粉丝牌1-5级的观众',
                            '粉丝牌6-10级的观众', '粉丝牌11-20级的观众', '粉丝牌21级以上的观众'])
                .add_yaxis("观众人数", [self.data["_0_medal"], self.data["_1_5_medal"], self.data["_6_10_medal"],
                                    self.data["_11_20_medal"], self.data["_21_medal"]])
                .add_yaxis("弹幕条数", [self.data["_0_medal_danmu_num"], self.data["_1_5_medal_danmu_num"],
                                    self.data["_6_10_medal_danmu_num"], self.data["_11_20_medal_danmu_num"],
                                    self.data["_21_medal_danmu_num"]])
                .add_yaxis("互动条数", [self.data["_0_medal_interact_num"], self.data["_1_5_medal_interact_num"],
                                    self.data["_6_10_medal_interact_num"], self.data["_11_20_medal_interact_num"],
                                    self.data["_21_medal_interact_num"]])
                .set_global_opts(title_opts=opts.TitleOpts(title="%s    观众人数:%d" % ("观众/粉丝团数据构成", watch_num),
                                                           pos_left="25%",
                                                           title_textstyle_opts=opts.series_options.TextStyleOpts(
                                                               color=self.theme_color,
                                                               font_size=35,
                                                               font_weight='bold'),
                                                           ),
                                 xaxis_opts=opts.AxisOpts(axislabel_opts=
                                                          opts.LabelOpts(font_size=15, color="auto",
                                                                         font_weight='bold')),
                                 yaxis_opts=opts.AxisOpts(axistick_opts=opts.AxisTickOpts(is_show=True),
                                                          splitline_opts=opts.SplitLineOpts(is_show=True)),
                                 legend_opts=opts.LegendOpts(item_width=50, item_height=28, pos_top="4%",
                                                             textstyle_opts=opts.TextStyleOpts(
                                                                 color="black",
                                                                 font_size=20,
                                                                 font_weight='bold'
                                                             )))

                .set_series_opts(label_opts=opts.LabelOpts(font_size=25, font_weight='bold', color="black"))
        )
        pic.add_js_funcs(self.bar_bg_load)
        save_path = "./output/%s" % self.live_type
        if os.path.exists(save_path) is False:
            os.makedirs(save_path)
        make_snapshot(ss1, pic.render(), save_path + "/2-观众-粉丝团数据构成.png", pixel_ratio=1)

    def __word_freq_pictorial_bar(self):
        _10_data = sorted(self.word_freq.items(), key=lambda x: x[1], reverse=True)
        x_data = []
        y_data = []
        for i in range(16):
            x_data.append(_10_data[15 - i][0])
            y_data.append(_10_data[15 - i][1])
        ops = opts.InitOpts(
            width="%dpx" % self.bar_bg_x,
            height="%dpx" % self.bar_bg_y,
            bg_color={"type": "pattern", "image": JsCode("img"), "repeat": "no-repeat"}
        )
        """pic = (
            PictorialBar(init_opts=ops)
                .add_yaxis("test", y_axis=y_data,
                           symbol='image://./src/%s/pictorial_symbol.png' % self.room_id,
                           symbol_repeat="true",
                           is_symbol_clip=True,
                           symbol_size=[50, 50],
                           label_opts=opts.LabelOpts(is_show=False))
                .add_xaxis(xaxis_data=x_data)
                .reversal_axis()
                .set_global_opts(yaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=15,
                                                                                        font_size=20,
                                                                                        color="black",
                                                                                        font_weight='bold')
                                                          ),
                                 legend_opts=opts.LegendOpts(is_show=False),
                                 title_opts=opts.TitleOpts(title="%s" % self.live_type,
                                                           pos_left="10%",
                                                           title_textstyle_opts=opts.series_options.TextStyleOpts(
                                                               color=self.theme_color,
                                                               font_size=35,
                                                               font_weight='bold'),
                                                           subtitle_textstyle_opts=opts.series_options.TextStyleOpts(
                                                               font_size=25,
                                                               font_weight='bold'
                                                           ), subtitle="✨热词速递✨")
                                 )
        )"""
        pic = (
            Bar(init_opts=ops)
                .add_yaxis("test", y_axis=y_data,
                           label_opts=opts.LabelOpts(is_show=False))
                .add_xaxis(xaxis_data=x_data)
                .reversal_axis()
                .set_global_opts(yaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=15,
                                                                                        font_size=25,
                                                                                        color="black",
                                                                                        font_weight='bold')
                                                          ),
                                 xaxis_opts=opts.AxisOpts(axistick_opts=opts.AxisTickOpts(is_align_with_label=True,
                                                                                          is_show=True)),
                                 legend_opts=opts.LegendOpts(is_show=False),
                                 title_opts=opts.TitleOpts(title="✨热词速递✨",
                                                           pos_left="10%",
                                                           title_textstyle_opts=opts.series_options.TextStyleOpts(
                                                               color=self.theme_color,
                                                               font_size=45,
                                                               font_weight='bold'),
                                                           )
                                 )
        )
        pic.add_js_funcs(self.bar_bg_load)
        pic.set_colors(self.theme_color)
        save_path = "./output/%s" % self.live_type
        if os.path.exists(save_path) is False:
            os.makedirs(save_path)
        make_snapshot(ss1, pic.render(), save_path + "/3-直播热词词频.png", pixel_ratio=1)

    def __revenue_type_pie(self, name_list):
        ops = opts.InitOpts(
            width="%dpx" % self.pie_bg_x,
            height="%dpx" % self.pie_bg_y,
            bg_color={"type": "pattern", "image": JsCode("img"), "repeat": "no-repeat"})
        # revenue_sum = round(self.data["gift_revenue"], 2) + round(self.data['sc_revenue'], 2) + round(self.data["guard_revenue"], 2)
        pie = \
            Pie(init_opts=ops) \
                .add(" ",
                     [list(z) for z in zip(name_list, [round(self.data["gift_revenue"], 2),
                                                       round(self.data['sc_revenue'], 2),
                                                       round(self.data["guard_revenue"], 2)])],
                     radius=["45%", "65%"],
                     center=["51%", "52%"],
                     ) \
                .set_global_opts(title_opts=opts.TitleOpts(title="营收类型构成",
                                                           pos_left="35%",
                                                           title_textstyle_opts=opts.series_options.TextStyleOpts(
                                                               color=self.theme_color,
                                                               font_size=55,
                                                               font_weight='bold'),
                                                           ),
                                 legend_opts=opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="2%",
                                                             item_width=50, item_height=28,
                                                             textstyle_opts=opts.TextStyleOpts(
                                                                 color="black",
                                                                 font_size=20,
                                                                 font_weight='bold'),
                                                             )) \
                .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}", font_size=22, font_weight='bold'))
        pie.add_js_funcs(self.pie_bg_load)
        pie.set_colors(self.series_color)
        save_path = "./output/%s" % self.live_type
        if os.path.exists(save_path) is False:
            os.makedirs(save_path)
        make_snapshot(ss1, pie.render(), save_path + "/5-营收类型构成.png", pixel_ratio=1)

    def __revenue_price_pie(self, name_list):
        ops = opts.InitOpts(
            width="%dpx" % self.pie_bg_x,
            height="%dpx" % self.pie_bg_y,
            bg_color={"type": "pattern", "image": JsCode("img"), "repeat": "no-repeat"})
        """revenue_sum = round(self.order_data["revenue"]["_10_revenue"], 2) + \
                      round(self.order_data["revenue"]["_10_100_revenue"], 2) + \
                      round(self.order_data["revenue"]["_100_revenue"], 2)"""
        pie = \
            Pie(init_opts=ops) \
                .add(" ",
                     [list(z) for z in zip(name_list, [round(self.order_data["revenue"]["_10_revenue"], 2),
                                                       round(self.order_data["revenue"]["_10_100_revenue"], 2),
                                                       round(self.order_data["revenue"]["_100_revenue"], 2)])],
                     radius=["45%", "65%"],
                     center=["51%", "52%"],
                     ) \
                .set_global_opts(title_opts=opts.TitleOpts(title="营收金额构成",
                                                           pos_left="35%",
                                                           title_textstyle_opts=opts.series_options.TextStyleOpts(
                                                               color=self.theme_color,
                                                               font_size=55,
                                                               font_weight='bold'),
                                                           ),
                                 legend_opts=opts.LegendOpts(orient="vertical", pos_top="13%", pos_left="2%",
                                                             item_width=50, item_height=28,
                                                             textstyle_opts=opts.TextStyleOpts(
                                                                 color="black",
                                                                 font_size=20,
                                                                 font_weight='bold'),
                                                             )) \
                .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}", font_size=22, font_weight='bold'))
        pie.add_js_funcs(self.pie_bg_load)
        pie.set_colors(self.series_color)
        save_path = "./output/%s" % self.live_type
        if os.path.exists(save_path) is False:
            os.makedirs(save_path)
        make_snapshot(ss1, pie.render(), save_path + "/6-营收金额构成.png", pixel_ratio=1)

    def __ordered_data_hot_line(self, line_name, num, data_name):
        data_sum = ""
        if data_name == "danmu" or data_name == "min_revenue" or data_name == "sc_data" or data_name == "guard_data":
            units = {"danmu": "条", "sc_data": "条", "min_revenue": "元", "guard_data": "舰团"}
            x_data = []
            y_data = []
            for x, y in self.order_data[data_name]:
                x_data.append(int(y))
                y_data.append(int(x))
            data_sum = "合计:%d %s" % (sum(y_data), units[data_name])
        elif data_name == "renqi" or data_name == "hot_rank" or data_name == "fans_change" or data_name == "watched":
            x_data = []
            y_data = []
            for x, y in self.order_data[data_name]:
                x_data.append(int(y))
                y_data.append(int(x))
            if data_name == "fans_change":
                x_data.pop(0)
                y_data.pop(0)
        elif data_name == "simu_interact":
            x_data = []
            y_data = []
            for x, y in self.order_data[data_name]:
                x_data.append(int(x))
                y_data.append(int(y))
        else:
            try:
                for i in self.order_data[data_name]:
                    print(i)
            except TypeError:
                return
            return

        ops = opts.InitOpts(
            width="%dpx" % self.bar_bg_x,
            height="%dpx" % self.bar_bg_y,
            bg_color={"type": "pattern", "image": JsCode("img"), "repeat": "no-repeat"})
        line = Line(init_opts=ops) \
            .add_xaxis(x_data) \
            .add_yaxis("test", y_data, is_smooth=True). \
            set_series_opts(
            areastyle_opts=opts.AreaStyleOpts(opacity=0.5),
            label_opts=opts.LabelOpts(is_show=False),
            markline_opts=opts.MarkLineOpts(
                data=[
                    opts.MarkLineItem(type_="max", name="最大值"),
                ],
                label_opts=opts.LabelOpts(font_size=30, color="auto", font_weight='bold'))
        ) \
            .set_global_opts(legend_opts=opts.LegendOpts(is_show=False),
                             title_opts=opts.TitleOpts(title="%s   %s" % (line_name, data_sum),
                                                       pos_left="10%",
                                                       title_textstyle_opts=opts.series_options.TextStyleOpts(
                                                           color=self.theme_color,
                                                           font_size=45,
                                                           font_weight='bold'),
                                                       ),
                             xaxis_opts=opts.AxisOpts(axislabel_opts=
                                                      opts.LabelOpts(font_size=25, color="auto",
                                                                     font_weight='bold'),
                                                      axistick_opts=opts.AxisTickOpts(is_align_with_label=True,
                                                                                      is_show=True),
                                                      is_scale=False,
                                                      boundary_gap=False,
                                                      name="单位：分钟",
                                                      name_location='end',
                                                      splitline_opts=opts.SplitLineOpts(is_show=True),
                                                      ),
                             yaxis_opts=opts.AxisOpts(axistick_opts=opts.AxisTickOpts(is_show=True),
                                                      splitline_opts=opts.SplitLineOpts(is_show=True),
                                                      axislabel_opts=opts.LabelOpts(font_size=20, color="auto",
                                                                                    font_weight='bold')
                                                      )
                             )
        line.add_js_funcs(self.bar_bg_load)
        line.set_colors(self.theme_color)
        save_path = "./output/%s" % self.live_type
        if os.path.exists(save_path) is False:
            os.makedirs(save_path)
        make_snapshot(ss1, line.render(), save_path + "/%d-%s.png" % (num, line_name), pixel_ratio=1)

    def cross_medal_pie(self):
        for k, v in self.order_data["medal_cross"].items():
            if v > 5:
                print(k, v)
