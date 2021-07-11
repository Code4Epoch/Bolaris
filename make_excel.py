"""
@author:lucien
@update_time:2021_7_9
"""

import xlrd
import xlwt
from xlutils.copy import copy  # 导入copy模块


def get_data(column_name, mysql_conn, live_road):
    sql = 'SELECT %s FROM every_day_stats WHERE live = \'%s\'' % (column_name, live_road)
    cur = mysql_conn.cursor()
    cur.execute(sql)
    data = cur.fetchall()
    return data[0][0]


def make_excel(mysql_conn, excel_path, live_road):
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
