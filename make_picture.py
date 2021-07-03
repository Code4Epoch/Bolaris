import json
import re
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.pyplot import MultipleLocator

# 用来正常显示中文标签
plt.rcParams['font.sans-serif'] = ['SimHei']
# 用来正常显示负号
plt.rcParams['axes.unicode_minus'] = False


def read_bilibili_gift_price(path):
    """

    :param path: 文件路径
    :return: 礼物对应的价格
    """
    with open("%s" % path, encoding='utf-8') as gift_file:
        gift = gift_file.read()
        gift_dict = json.loads(gift)
    return gift_dict


def get_min_avg_data(my_data):
    """

    :param my_data: 该场直播的全部信息
    :return:
    """
    minute_msg_stats = {'gift': 0, 'danmu': 0, 'sc': 0, 'guard': 0, 'entry': 0, 'revenue': 0, 'new_fans': 0,
                        'new_medal_fans': 0, 'simu_interact': 0}
    latest_time = my_data[0][5]
    stats_list = []
    gift_dict = read_bilibili_gift_price("./live/gift_price.txt")
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
                        gift_num = temp_gift[1]
                    except Exception:
                        gift_num = 1
                    try:
                        gift_price = gift_dict[temp_gift[0]]
                    except Exception:
                        gift_price = 0
                    temp_price = gift_price * gift_num
                    minute_msg_stats['revenue'] += temp_price
            elif msg_type == 'sc':
                minute_msg_stats['revenue'] += msg[8]
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


def make_min_picture(my_data, timescale, table_name, road, if_sum):
    """

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
        elif table_name == 'sc数量' or table_name == '新增粉丝' or table_name == '新增粉丝团':
            y_table_name += '%d个' % np.sum(y, axis=0)
        elif table_name == '弹幕数量':
            y_table_name += '%d条' % np.sum(y, axis=0)
        elif table_name == '送礼人次' or table_name == '入场人次':
            y_table_name += '%d次' % np.sum(y, axis=0)
    else:
        y_table_name = table_name + "折线图"
    plt.title(y_table_name)
    plt.xlabel('开播时长/%dmins' % timescale)
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

    plt.plot(x, y, c="red")
    plt.grid(True)

    plt.savefig("./output/%s/%s.jpg" % (road, table_name))
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

