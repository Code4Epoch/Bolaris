# -*- coding: utf-8 -*- #
# ------------------------------------------------------------------
# File Name:        make_chart
# Author:           ydyjyal,lucien
# Version:          1.1
# Created:          2021/7/9
# Description:      pyplot、pyechart风格的制图
# Function List:    get_min_avg_data()          --将数据转换为分钟形式
#                   make_min_picture()          --matplot风格的分均图
#                   trans_mins_sum()            --变换数据的区分（几分钟做合并区间）
#                   make_word_freq_bar()        --matplot风格的高频词图
#                   pc_make_word_freq_bar()     --pyechart风格的高频词图，并且使用的是象形图，可以自定义symbol
#                   make_wordcloud()            --制作词云
#                   get_data()                  --从mysql获取数据
#                   make_excel()                --输出结果到model/excel（这里后续打算也换成图的形式，还在考虑形式）
#                   make_revenue_pie()          --制作营收环图
#                   make_muti_picture()         --制作多场直播对比图
#                   make_muti_radar_picture()   --制作多场直播的雷达图
#                   make_muti_pie()             --制作多场直播的统计饼图
# History:
#       <author>        <version>       <time>      <desc>
#       ydyjya,lucien   1.0             2021/7/9    create
#       ydyjya          1.1             2021/8/18   修改了部分函数的风格
# ------------------------------------------------------------------
import re
import os
import matplotlib.pyplot as plt
import wordcloud
import numpy as np
import xlrd
import xlwt
from xlutils.copy import copy
import live.tool_function as tf
from matplotlib.pyplot import MultipleLocator
from scipy.interpolate import make_interp_spline
from imageio import imread
from wordcloud import ImageColorGenerator
from pyecharts import options as opts
from pyecharts.render import make_snapshot
from pyecharts.charts import PictorialBar
from pyecharts.charts import Pie
from pyecharts.charts import Line
from pyecharts.charts import Radar
from snapshot_selenium import snapshot


def get_min_avg_data(my_data):
    """

    :param my_data: 该场直播的全部信息
    :return:
    """
    minute_msg_stats = {'gift': 0, 'danmu': 0, 'sc': 0, 'guard': 0, 'entry': 0, 'revenue': 0, 'new_fans': 0,
                        'new_medal_fans': 0, 'simu_interact': 0}
    latest_time = my_data[0][5]
    stats_list = []
    gift_dict = tf.read_bilibili_gift_price("./config/live_data_summary/gift_price.json")
    simu_interact = {}
    live_flag = 0

    for msg in my_data.__iter__():

        if live_flag == 0 and msg[0] != 'start':
            continue
        else:
            live_flag = 1

        now_msg_time = msg[5]

        if live_flag == 1 and msg[0] == 'end':
            # 更新同接
            delete_uid = []
            for uid, user_latest_time in simu_interact.items():
                if (now_msg_time - user_latest_time).seconds > 600:
                    delete_uid.append(uid)
            for uid in delete_uid.__iter__():
                simu_interact.pop(uid)
            minute_msg_stats['simu_interact'] = len(simu_interact)

            stats_list.append(minute_msg_stats)
            break

        if (now_msg_time - latest_time).seconds > 60:
            # 更新同接
            delete_uid = []

            for uid, user_latest_time in simu_interact.items():
                if (now_msg_time - user_latest_time).seconds > 600:
                    delete_uid.append(uid)
            for uid in delete_uid.__iter__():
                simu_interact.pop(uid)
            minute_msg_stats['simu_interact'] = len(simu_interact)

            stats_list.append(minute_msg_stats)
            latest_time = now_msg_time

            minute_msg_stats = {'gift': 0, 'danmu': 0, 'sc': 0, 'guard': 0, 'entry': 0, 'revenue': 0, 'new_fans': 0,
                                'new_medal_fans': 0, 'simu_interact': 0}

        msg_type = msg[4]
        msg_text = msg[6]
        if msg_type == 'gift' or msg_type == 'sc' or msg_type == 'danmu' or msg_type == 'guard':
            simu_interact[msg[0]] = now_msg_time

        if msg_type != 'fans_change' and msg_type != '':
            minute_msg_stats[msg_type] += 1
            if msg_type == 'gift':
                temp_gift = msg_text.split(sep=' * ')
                if temp_gift[0] == '小心心' or temp_gift[0] == '辣条':
                    pass
                else:
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
                    minute_msg_stats['revenue'] += float(temp_price)
            elif msg_type == 'sc':
                minute_msg_stats['revenue'] += float(msg[8])
            elif msg_type == 'guard':
                if msg[-2] == 10003:
                    minute_msg_stats['revenue'] += 138
                elif msg[-2] == 10002:
                    minute_msg_stats['revenue'] += 1998
                elif msg[-2] == 10001:
                    minute_msg_stats['revenue'] += 19998
        elif msg_type == 'fans_change':
            fans_change = re.findall(r'\d+', msg_text)
            minute_msg_stats['new_fans'] += int(fans_change[0])
            minute_msg_stats['new_medal_fans'] += int(fans_change[1])

    return stats_list


def make_min_picture(my_data, timescale, table_name, road, if_sum, color):
    """

    :param color: 绘图颜色
    :param if_sum: 是否求总和
    :param road: 存储路径
    :param table_name: y轴名称
    :param timescale: 时间刻度
    :param my_data: 要绘图的数据 list
    :return: nothing 输出图片
    """

    now_time = -10
    time_data = []
    trans_data = []
    for list_data in my_data:
        time_data.append(now_time)
        trans_data.append(list_data)
        now_time += timescale

    x = np.array(time_data)
    y = np.array(trans_data)
    y_max = np.max(y, axis=0)
    y_min = np.min(y, axis=0)
    if if_sum == 1:
        y_table_name = table_name + "合计:"
        if table_name == '营收':
            y_table_name += '%.2f元' % np.sum(y, axis=0)
        elif table_name == 'sc数量' or table_name == '新增粉丝' or table_name == '新增粉丝团' or table_name == '舰团数量':
            y_table_name += '%d个' % np.sum(y, axis=0)
        elif table_name == '弹幕数量':
            y_table_name += '%d条' % np.sum(y, axis=0)
        elif table_name == '送礼人次' or table_name == '入场人次':
            y_table_name += '%d次' % np.sum(y, axis=0)
    else:
        y_table_name = table_name + "折线图"
    plt.title(y_table_name)
    plt.xlabel('开播时长/1mins——时间区段：%dmins' % timescale)
    plt.ylabel(table_name)
    ax = plt.gca()

    x_major_locator = MultipleLocator(10)
    if y_max - y_min > 1000:
        temp = 100
    elif y_max - y_min > 100:
        temp = 10
    else:
        temp = 1

    y_locator = ((y_max - y_max % temp + temp) - (y_min - y_min % temp)) / 10
    y_major_locator = MultipleLocator(y_locator)

    ax.xaxis.set_major_locator(x_major_locator)
    ax.yaxis.set_major_locator(y_major_locator)

    plt.xlim(-5.5, len(x) * timescale)
    plt.ylim(y_min - y_min % temp, y_max - y_max % temp + temp)

    model = make_interp_spline(x, y)
    xs = np.linspace(np.min(x, axis=0), np.max(x, axis=0), 500)
    ys = model(xs)

    plt.fill_between(xs, 0, ys, facecolor=color, alpha=0.4)
    plt.plot(xs, ys, c=color)
    plt.grid(True)

    save_path = "./output/%s/" % road
    if os.path.exists(save_path) is False:
        os.makedirs(save_path)

    plt.savefig("./output/%s/%s_%s.jpg" % (road, table_name, road))
    plt.clf()
    return


def trans_mins_sum(before_mins, after_mins, my_data):
    """

    :param before_mins: 转换前的时间区分
    :param after_mins: 转换后的时间区分
    :param my_data: 要转换的数据 类型为list
    :return: 转换后的数据 类型为 list
    """
    if after_mins % before_mins != 0:
        print('不能整除，不能进行转换')
        raise Exception
    new_data = []
    times = after_mins / before_mins
    idx = 0
    temp_sum = 0
    for data in my_data:
        temp_sum += data
        idx += before_mins
        if idx == times:
            new_data.append(temp_sum)
            temp_sum = 0
            idx = 0
    return new_data


def make_word_freq_bar(my_word_freq_dict, road, color):
    """

    :param color: bar的颜色
    :param my_word_freq_dict: 词频字典
    :param road: 文件目录
    :return:
    """
    sorded_dict = sorted(my_word_freq_dict.items(), key=lambda x: x[1], reverse=True)
    x_label = []
    y_label = []
    for pair in sorded_dict.__iter__():
        x_label.append(pair[0])
        y_label.append(pair[1])
    x_label.reverse()
    y_label.reverse()
    for x, y in enumerate(y_label):
        plt.text(x, y + 100, '%s' % y, ha='center', va='bottom')
    plt.barh(y=x_label, width=y_label, color=color)
    plt.xticks(rotation=300)
    save_path = './output/%s/' % road
    if os.path.exists(save_path) is False:
        os.makedirs(save_path)
    plt.savefig(save_path + "词频统计%s.png" % road)
    plt.clf()


# pyechart风格的，不过效果似乎不太好
def pc_make_word_freq_bar(my_word_freq_dict, road):
    """
    :param my_word_freq_dict: 词频字典
    :param road: 文件目录
    :return:
    """
    sorded_dict = sorted(my_word_freq_dict.items(), key=lambda x: x[1], reverse=False)
    x_label = []
    y_label = []
    for pair in sorded_dict.__iter__():
        x_label.append(pair[0])
        y_label.append(pair[1])
    formatter = '个'
    pictorial_bar = PictorialBar(init_opts=opts.InitOpts(bg_color='rgb(255,255,255)'))
    pictorial_bar.add_xaxis(x_label)
    pictorial_bar.add_yaxis("",
                            y_label,
                            label_opts=opts.LabelOpts(position="right", formatter="{c}" + formatter, font_size=15),
                            symbol_repeat='fixed',
                            symbol_offset=[0, 0],
                            is_symbol_clip=True,
                            symbol='image://your_url',
                            symbol_size=[15, 15]
                            )
    pictorial_bar.reversal_axis()
    pictorial_bar.set_global_opts(
        xaxis_opts=opts.AxisOpts(is_show=False),
        yaxis_opts=opts.AxisOpts(
            axislabel_opts=opts.LabelOpts(font_size=15, interval=0),
            axistick_opts=opts.AxisTickOpts(is_show=False),
            axisline_opts=opts.AxisLineOpts(
                linestyle_opts=opts.LineStyleOpts(opacity=0))))
    pictorial_bar.render('')
    save_path = './output/%s/' % road
    make_snapshot(snapshot, pictorial_bar.render(), save_path + "pyecharts词频统计%s.png" % road)


def make_wordcloud(my_word_freq_dict, path, road):
    """

    :param my_word_freq_dict: 词频字典
    :param path: 寻图路径不带格式
    :param road: 存图路径 为日期和房间号
    :return:
    """
    img = imread('%s.jpg' % path)
    image_colors = ImageColorGenerator(img)
    mask_img = np.array(img)
    wc = wordcloud.WordCloud(font_path="C:\Windows\Fonts\msyh.ttc",
                             mask=mask_img,
                             width=1000,
                             height=700,
                             background_color=None,
                             mode="RGBA",
                             max_words=500)
    wc.generate_from_frequencies(my_word_freq_dict)
    plt.imshow(wc.recolor(color_func=image_colors))
    plt.clf()
    save_path = "./output/%s/" % road
    if os.path.exists(save_path) is False:
        os.makedirs(save_path)
    wc.to_file(save_path + "词云%s.png" % road)


def get_data(column_name, mysql_conn, live_road):
    """

    @param column_name: 列名
    @param mysql_conn: mysql连接
    @param live_road: 直播的路径
    @return: 列的数据
    """
    sql = 'SELECT %s FROM every_day_stats WHERE live = \'%s\'' % (column_name, live_road)
    cur = mysql_conn.cursor()
    cur.execute(sql)
    data = cur.fetchall()
    return data[0][0]


def make_excel(mysql_conn, excel_path, live_road):
    """

    @param mysql_conn: mysql连接名
    @param excel_path: excel的路径
    @param live_road: 直播表的的路径
    @return: 将数据写入excel中
    """
    rb = xlrd.open_workbook(excel_path, formatting_info=True)  # 打开weng.xls文件
    wb = copy(rb)  # 利用xlutils.copy下的copy函数复制
    ws = wb.get_sheet(0)  # 获取表单0

    style = xlwt.XFStyle()  # 初始化样式
    font = xlwt.Font()  # 为样式创建字体
    font.name = '华文新魏'
    font.height = 20 * 16
    alignment = xlwt.Alignment()
    alignment.horz = 0x02
    alignment.vert = 0x01

    style.font = font  # 设定样式
    style.alignment = alignment

    # 表1
    ws.write(9, 1, str(get_data('entry_num', mysql_conn, live_road)), style)  # 进场人数
    ws.write(11, 1, str(round(get_data('avg_watch_time', mysql_conn, live_road), 2)), style)  # 平均观看时长
    ws.write(13, 1, str(round((get_data('danmu', mysql_conn, live_road) +
                               get_data('gift', mysql_conn, live_road)) /
                              get_data('entry_num', mysql_conn, live_road), 2)), style)  # 平均互动:danmu+gift/entry
    ws.write(15, 1, str(round(get_data('avg_danmu', mysql_conn, live_road), 2)), style)  # 平均弹幕条数
    ws.write(9, 3, str(get_data('react_num', mysql_conn, live_road)), style)  # 互动人数
    ws.write(11, 3, str(round(get_data('avg_react_watch_time', mysql_conn, live_road), 2)), style)  # 互动观众平均观看时长
    ws.write(13, 3, str(round((get_data('danmu', mysql_conn, live_road)
                               + get_data('gift', mysql_conn, live_road))
                              / get_data('react_num', mysql_conn, live_road), 2)),
             style)  # 互动人数的平均互动数：danmu+gift/react_num
    ws.write(15, 3, str(round(get_data('danmu', mysql_conn, live_road)
                              / get_data('react_num', mysql_conn, live_road), 2)), style)  # 互动人数的平均弹幕数
    ws.write(17, 1, str(get_data('medal_num', mysql_conn, live_road)), style)  # asoul相关粉丝团人数
    ws.write(17, 3, str(round(get_data('medal_num', mysql_conn, live_road)
                              / get_data('entry_num', mysql_conn, live_road), 2)), style)  # 进场占比

    # 表2
    # 无粉丝牌
    ws.write(22, 1, str(get_data('medal_0_num', mysql_conn, live_road)), style)
    ws.write(22, 2, str(round(get_data('medal_0_avg_react', mysql_conn, live_road), 2)), style)
    ws.write(22, 3, str(round(get_data('medal_0_avg_danmu', mysql_conn, live_road), 2)), style)
    # 1-5粉丝牌
    ws.write(23, 1, str(get_data('medal_1_5_num', mysql_conn, live_road)), style)
    ws.write(23, 2, str(round(get_data('medal_1_5_avg_react', mysql_conn, live_road), 2)), style)
    ws.write(23, 3, str(round(get_data('medal_1_5_avg_danmu', mysql_conn, live_road), 2)), style)
    # 6-10粉丝牌
    ws.write(24, 1, str(get_data('medal_6_10_num', mysql_conn, live_road)), style)
    ws.write(24, 2, str(round(get_data('medal_6_10_avg_react', mysql_conn, live_road), 2)), style)
    ws.write(24, 3, str(round(get_data('medal_6_10_avg_danmu', mysql_conn, live_road), 2)), style)
    # 11-20粉丝牌
    ws.write(25, 1, str(get_data('medal_11_20_num', mysql_conn, live_road)), style)
    ws.write(25, 2, str(round(get_data('medal_11_20_avg_react', mysql_conn, live_road), 2)), style)
    ws.write(25, 3, str(round(get_data('medal_11_20_avg_danmu', mysql_conn, live_road), 2)), style)
    # 21以上粉丝牌
    ws.write(26, 1, str(get_data('medal_21_num', mysql_conn, live_road)), style)
    ws.write(26, 2, str(round(get_data('medal_21_avg_react', mysql_conn, live_road), 2)), style)
    ws.write(26, 3, str(round(get_data('medal_21_avg_danmu', mysql_conn, live_road), 2)), style)
    # 合计
    ws.write(27, 1, str(get_data('medal_0_num', mysql_conn, live_road)
                        + get_data('medal_1_5_num', mysql_conn, live_road)
                        + get_data('medal_6_10_num', mysql_conn, live_road)
                        + get_data('medal_11_20_num', mysql_conn, live_road)
                        + get_data('medal_21_num', mysql_conn, live_road)), style)
    # 粉丝团观众互动条数占比
    ws.write(28, 1, str(round((get_data('medal_1_5_num', mysql_conn, live_road)
                               * get_data('medal_1_5_avg_react', mysql_conn, live_road)
                               + get_data('medal_6_10_num', mysql_conn, live_road)
                               * get_data('medal_6_10_avg_react', mysql_conn, live_road)
                               + get_data('medal_11_20_num', mysql_conn, live_road)
                               * get_data('medal_11_20_avg_react', mysql_conn, live_road)
                               + get_data('medal_21_num', mysql_conn, live_road)
                               * get_data('medal_21_avg_react', mysql_conn, live_road))
                              / (get_data('danmu', mysql_conn, live_road)
                                  + get_data('gift', mysql_conn, live_road)), 2)), style)

    wb.save(excel_path)  # 保存文件


def make_revenue_pie(pie_dict, my_pie_name, road):
    """

    @param pie_dict: 绘制pie的字典{"营收类型":金额}
    @param my_pie_name: 表头名
    @param road: 路径
    @return: 绘制一张pie
    """
    color = {'22625025': ["#A9DCF9", "#9AC8E2", "#8BB4CB"],
             '22632424': ["#F18A80", "#DB7D74", "#C57068"],
             '22634198': ["#CAB7EF", "#B8A6D9", "#A695C3"],
             '22637261': ["#FEA8C2", "#E799B0", "#D08A9E"],
             '22625027': ["#60709E", "#576690", "#4E5C82"]}

    x_data = []
    translate_dict = tf.read_translate_dict('./config/live_data_summary/revenue_translate.json')
    for name, num in pie_dict.items():
        x_data.append(translate_dict[name] + ":%d元" % num)
    y_data = pie_dict.values()
    data_pair = [list(z) for z in zip(x_data, y_data)]
    pie_name = my_pie_name
    pie = Pie(init_opts=opts.InitOpts(bg_color='rgb(255,255,255)')).add(
        series_name=my_pie_name,
        # 系列数据项，格式为[(key1,value1),(key2,value2)]
        data_pair=data_pair,
        rosetype=None,
        # 饼图的半径，设置成默认百分比，相对于容器高宽中较小的一项的一半
        radius=["50%", "70%"],
        # 饼图的圆心，第一项是相对于容器的宽度，第二项是相对于容器的高度
        center=["50%", "50%"],
        # 标签配置项
        label_opts=opts.LabelOpts(is_show=False, position="center"),
    ).set_global_opts(
        # 设置标题
        title_opts=opts.TitleOpts(
            # 名字
            title=my_pie_name,
            # 组件距离容器左侧的位置
            pos_left="center",
            # 组件距离容器上方的像素值
            pos_top="20",
            # 设置标题颜色
            title_textstyle_opts=opts.TextStyleOpts(color="#000000"),
        ),
        # 图例配置项，参数 是否显示图里组件
        legend_opts=opts.LegendOpts(is_show=False),
    ).set_series_opts(
        tooltip_opts=opts.TooltipOpts(
            trigger="item", formatter="{a} <br/>{b}: {c} ({d}%)"
        ), label_opts=opts.LabelOpts(color="#000000"), )
    """pie.add_js_funcs(

        var img = new Image();
        img.setAttribute('crossorigin', 'anonymous');
        img.src = 'https://i0.hdslb.com/bfs/album/c0c440c5b9b83d29d01577ae5e0e3138fbf1b3ee.jpg';

    )"""
    color_pointer = road.split(sep='_')[3]
    pie.set_colors(color[color_pointer])
    make_snapshot(snapshot, pie.render(), "./output/%s/%s_%s.png" % (road, pie_name, road))


def make_muti_picture(my_x_data, my_y_data, table_name, road, color_dict, color_idx, live_type):
    """

    @param my_x_data: x_data ["name1", "name2", ......]
    @param my_y_data: y_data [num1, num2, ......]
    @param table_name: 表头
    @param road: 路径
    @param color_dict: 颜色字典
    @param color_idx: 用什么颜色
    @return: 绘制多次信息的饼图到路径中
    """
    time_data = []
    line_name_list = table_name.split(sep='&')
    idx = 0
    for live_id in my_x_data:
        time_str = live_id.split(sep='_')
        new_time = "%s" % live_type[idx]
        time_data.append(new_time)
        idx += 1
    line = (Line(init_opts=opts.InitOpts(bg_color='rgb(255,255,255)')).
            add_xaxis(time_data))
    line_name = "%s折线图" % table_name
    '''line.add_js_funcs(
        """
        let img = document.createElement("img"); img.setAttribute('crossorigin', 'anonymous');
        img.src = 'https://i0.hdslb.com/bfs/album/c0c440c5b9b83d29d01577ae5e0e3138fbf1b3ee.jpg';
        img.style.setProperty("opacity","0.1");
        """
    )'''
    color_list = list(color_dict.values())
    list_idx = 0
    for data in my_y_data:
        trans_data = []
        for record in data:
            trans_data.append(record)
        line.add_yaxis(series_name=line_name_list[list_idx], y_axis=trans_data,
                       color=color_list[color_idx], markline_opts=opts.
                       MarkLineOpts(data=[opts.MarkLineItem(type_='average', name='平均值')]))
        list_idx += 1
        color_idx += 1
        if color_idx == 5:
            color_idx = 0

    save_path = "./output/%s" % road
    if os.path.exists(save_path) is False:
        os.makedirs(save_path)
    make_snapshot(snapshot, line.render(), save_path + "/%s_%s.png" % (line_name, road))

    return color_idx


def make_muti_radar_picture(my_x_data, my_y_data, table_name, road, color_dict):
    """

    @param my_x_data: x_data ["name1", "name2", ......]
    @param my_y_data: y_data [num1, num2, ......]
    @param table_name: 表头
    @param road: 路径
    @param color_dict: 颜色字典
    @return: 绘制雷达图
    """
    time_data = []
    for live_id in my_x_data:
        time_str = live_id.split(sep='_')
        new_time = "%s-%s-%s" % (time_str[0], time_str[1], time_str[2])
        time_data.append(new_time)
    radar_item_list = table_name.split(sep='&')
    radar = Radar()
    y_max = np.max(np.array(my_y_data), axis=1)
    y_min = np.min(np.array(my_y_data), axis=1)
    '''radar.add_js_funcs(
        """
        var img = new Image(); img.setAttribute('crossorigin', 'anonymous');
        img.setAttribute('style','opacity:0.5');
        img.src = 'https://i0.hdslb.com/bfs/album/767cf83ba20a98f1b69ff76a937334affc5313e6.jpg';

        """
    )'''
    radar_name = "%s雷达图" % road
    schema = []
    color_list = list(color_dict.values())
    idx = 0
    for item in radar_item_list:
        schema.append(opts.RadarIndicatorItem(name=item, max_=y_max[idx], min_=2 * y_min[idx] - y_max[idx]))
        idx += 1
    radar.add_schema(schema)
    x_len = len(my_x_data)
    for i in range(0, x_len):
        values = []
        for item in my_y_data:
            values.append(item[i])
        radar.add(time_data[i], [values], color=color_list[i],
                  areastyle_opts=opts.AreaStyleOpts(color=color_list[i], opacity=0.3))
    radar.set_global_opts(title_opts=opts.TitleOpts(title=radar_name))
    save_path = "./output/%s" % road
    if os.path.exists(save_path) is False:
        os.makedirs(save_path)
    make_snapshot(snapshot, radar.render(), save_path + "/%s.png" % radar_name)

    return


def make_muti_pie(x_data, y_data, my_pie_name, road):
    """

    @param x_data: x_data ["name1", "name2", ......]
    @param y_data: y_data [num1, num2, ......]
    @param my_pie_name: 表头
    @param road: 路径
    @return: 绘制饼图到路径
    """
    data_pair = [list(z) for z in zip(x_data, y_data)]
    pie_name = my_pie_name
    pie = Pie(init_opts=opts.InitOpts(bg_color='rgb(255,255,255)')).add(
        series_name=my_pie_name,
        # 系列数据项，格式为[(key1,value1),(key2,value2)]
        data_pair=data_pair,
        rosetype=None,
        # 饼图的半径，设置成默认百分比，相对于容器高宽中较小的一项的一半
        radius="55%",
        # 饼图的圆心，第一项是相对于容器的宽度，第二项是相对于容器的高度
        center=["50%", "50%"],
        # 标签配置项
        label_opts=opts.LabelOpts(position="center"),
    ).set_global_opts(
        # 设置标题
        title_opts=opts.TitleOpts(
            # 名字
            title=my_pie_name,
            # 组件距离容器左侧的位置
            pos_left="center",
            # 组件距离容器上方的像素值
            pos_top="40",
            # 设置标题颜色
            title_textstyle_opts=opts.TextStyleOpts(color="#000"),
        ),
    ).set_series_opts(
        tooltip_opts=opts.TooltipOpts(
            trigger="item", formatter="{a} <br/>{b}: {c} ({d}%)"
        ), label_opts=opts.LabelOpts(color="#000000", formatter="{b}:{d}%"), )
    """pie.add_js_funcs(
        bg_color={"type": "pattern", "image": JsCode("img"), "repeat": "no-repeat"}
        let img = document.createElement("img"); img.setAttribute('crossorigin', 'anonymous');
        img.src = 'https://i0.hdslb.com/bfs/album/767cf83ba20a98f1b69ff76a937334affc5313e6.jpg';
        img.style.setProperty("opacity","0.1");

    )"""
    pie_name = pie_name.replace('\n', '')
    make_snapshot(snapshot, pie.render(), "./output/%s/%s_%s.png" % (road, pie_name, road))
