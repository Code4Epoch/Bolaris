"""
@author:zzh
@update_time:2021_7_9
"""
import live_function as lf
import re
import os
import matplotlib.pyplot as plt
import wordcloud
import numpy as np
from matplotlib.pyplot import MultipleLocator
from pyecharts.charts import Pie
from pyecharts import options as opts
from pyecharts.render import make_snapshot
from pyecharts.charts import PictorialBar
from scipy.interpolate import make_interp_spline
from snapshot_selenium import snapshot
from wordcloud import ImageColorGenerator
from imageio import imread



# 用来正常显示中文标签
plt.rcParams['font.sans-serif'] = ['SimHei']
# 用来正常显示负号
plt.rcParams['axes.unicode_minus'] = False


def get_min_avg_data(my_data):
    """

    :param my_data: 该场直播的全部信息
    :return:
    """
    minute_msg_stats = {'gift': 0, 'danmu': 0, 'sc': 0, 'guard': 0, 'entry': 0, 'revenue': 0, 'new_fans': 0,
                        'new_medal_fans': 0, 'simu_interact': 0}
    latest_time = my_data[0][5]
    stats_list = []
    gift_dict = lf.read_bilibili_gift_price("live/gift_price.json")
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

    plt.savefig("./output/%s/%s_%s.jpg" % (road, table_name, road))
    plt.clf()
    return


def new_make_min_picture(my_data, timescale, table_name, road, if_sum, color):
    """

    :param if_sum: 是否求总和
    :param road: 存储路径
    :param table_name: y轴名称
    :param timescale: 时间刻度
    :param my_data: 要绘图的数据 list
    :return: nothing 输出pyechart风格图片
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

    plt.savefig("./output/%s/new_%s_%s.jpg" % (road, table_name, road))
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


def make_revenue_pie(pie_dict, my_pie_name, road):
    x_data = []
    translate_dict = lf.read_translate_dict('./live/revenue_translate.json')
    for name, num in pie_dict.items():
        x_data.append(translate_dict[name] + ":%d元" % num)
    y_data = pie_dict.values()
    data_pair = [list(z) for z in zip(x_data, y_data)]
    pie_name = my_pie_name
    pie = Pie(init_opts=opts.InitOpts(bg_color="#2c343c")).add(
        series_name=my_pie_name,
        # 系列数据项，格式为[(key1,value1),(key2,value2)]
        data_pair=data_pair,
        rosetype=None,
        # 饼图的半径，设置成默认百分比，相对于容器高宽中较小的一项的一半
        radius="55%",
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
            title_textstyle_opts=opts.TextStyleOpts(color="#fff"),
        ),
        # 图例配置项，参数 是否显示图里组件
        legend_opts=opts.LegendOpts(is_show=False),
    ).set_series_opts(
        tooltip_opts=opts.TooltipOpts(
            trigger="item", formatter="{a} <br/>{b}: {c} ({d}%)"
        ), label_opts=opts.LabelOpts(color="rgba(255, 255, 255, 0.3)"), )
    make_snapshot(snapshot, pie.render(), "./output/%s/%s_%s.png" % (road, pie_name, road))


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
        plt.text(x, y+100, '%s' % y, ha='center', va='bottom')
    plt.barh(y=x_label, width=y_label, color=color)
    plt.xticks(rotation=300)
    save_path = './output/%s/' % road
    if os.path.exists(save_path) is False:
        os.makedirs(save_path)
    plt.savefig(save_path + "词频统计%s.png" % road)
    plt.clf()


def pc_make_word_freq_bar(my_word_freq_dict, road):

    label = list(my_word_freq_dict.keys())
    values = list(my_word_freq_dict.values())
    formatter = '个'
    pictorial_bar = PictorialBar()
    pictorial_bar.add_xaxis(label)
    pictorial_bar.add_yaxis("",
                            values,
                            label_opts=opts.LabelOpts(position="right", formatter="{c}" + formatter, font_size=18),
                            symbol_size=50,
                            symbol_repeat='fixed',
                            symbol_offset=[0, 0],
                            is_symbol_clip=True,
                            symbol='path://M31.78125,66.40625Q,24.171875,66.40625,20.328125,58.90625,Q,16.5,'
                                   '51.421875,16.5,36.375,Q,16.5,21.390625,20.328125,13.890625,Q,24.171875,6.390625,'
                                   '31.78125,6.390625,Q,39.453125,6.390625,43.28125,13.890625,Q,47.125,21.390625,'
                                   '47.125,36.375,Q,47.125,51.421875,43.28125,58.90625,Q,39.453125,66.40625,31.78125,'
                                   '66.40625,z M31.78125,74.21875,Q,44.046875,74.21875,50.515625,64.515625,Q,'
                                   '56.984375,54.828125,56.984375,36.375,Q,56.984375,17.96875,50.515625,8.265625,Q,'
                                   '44.046875,-1.421875,31.78125,-1.421875,Q,19.53125,-1.421875,13.0625,8.265625,Q,'
                                   '6.59375,17.96875,6.59375,36.375,Q,6.59375,54.828125,13.0625,64.515625,Q,19.53125,'
                                   '74.21875,31.78125,74.21875,z M10.796875,72.90625,L,49.515625,72.90625,L,'
                                   '49.515625,64.59375,L,19.828125,64.59375,L,19.828125,46.734375,Q,21.96875,'
                                   '47.46875,24.109375,47.828125,Q,26.265625,48.1875,28.421875,48.1875,Q,40.625,'
                                   '48.1875,47.75,41.5,Q,54.890625,34.8125,54.890625,23.390625,Q,54.890625,11.625,'
                                   '47.5625,5.09375,Q,40.234375,-1.421875,26.90625,-1.421875,Q,22.3125,-1.421875,'
                                   '17.546875,-0.640625,Q,12.796875,0.140625,7.71875,1.703125,L,7.71875,11.625,Q,'
                                   '12.109375,9.234375,16.796875,8.0625,Q,21.484375,6.890625,26.703125,6.890625,Q,'
                                   '35.15625,6.890625,40.078125,11.328125,Q,45.015625,15.765625,45.015625,23.390625,'
                                   'Q,45.015625,31,40.078125,35.4375,Q,35.15625,39.890625,26.703125,39.890625,Q,'
                                   '22.75,39.890625,18.8125,39.015625,Q,14.890625,38.140625,10.796875,36.28125,'
                                   'zM10.796875,72.90625,L,49.515625,72.90625,L,49.515625,64.59375,L,19.828125,'
                                   '64.59375,L,19.828125,46.734375,Q,21.96875,47.46875,24.109375,47.828125,Q,'
                                   '26.265625,48.1875,28.421875,48.1875,Q,40.625,48.1875,47.75,41.5,Q,54.890625,'
                                   '34.8125,54.890625,23.390625,Q,54.890625,11.625,47.5625,5.09375,Q,40.234375,'
                                   '-1.421875,26.90625,-1.421875,Q,22.3125,-1.421875,17.546875,-0.640625,Q,12.796875,'
                                   '0.140625,7.71875,1.703125,L,7.71875,11.625,Q,12.109375,9.234375,16.796875,8.0625,'
                                   'Q,21.484375,6.890625,26.703125,6.890625,Q,35.15625,6.890625,40.078125,11.328125,'
                                   'Q,45.015625,15.765625,45.015625,23.390625,Q,45.015625,31,40.078125,35.4375,Q,'
                                   '35.15625,39.890625,26.703125,39.890625,Q,22.75,39.890625,18.8125,39.015625,Q,'
                                   '14.890625,38.140625,10.796875,36.28125,z '
                            )
    pictorial_bar.reversal_axis()
    pictorial_bar.set_global_opts(
        xaxis_opts=opts.AxisOpts(is_show=False),
        yaxis_opts=opts.AxisOpts(
            axislabel_opts=opts.LabelOpts(font_size=18),
            axistick_opts=opts.AxisTickOpts(is_show=False),
            axisline_opts=opts.AxisLineOpts(
                linestyle_opts=opts.LineStyleOpts(opacity=0))))
    pictorial_bar.render()
    save_path = './output/%s/' % road
    make_snapshot(snapshot, pictorial_bar.render(), save_path + "pyecharts词频统计%s.png" % road)

