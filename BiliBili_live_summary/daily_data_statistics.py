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
from BiliBili_live_summary import global_var


class daily_data_statistics(object):

    def __init__(self, data, org_config):
        self.data = data
        self.org_config = org_config
        self.audience_send_msg = self.__get_audience_msg()
        self.live_long = self.__get_time()
        # 时间序列数据、观众序列数据、粉丝牌序列数据
        self.ordered_data = {"audience": self.__get_audience(), "live_long": self.live_long,
                             "revenue": self.__get_revenue(), "renqi": self.__get_renqi(),
                             "hot_rank": self.__get_hot_rank(), "fans_change": self.__get_fans_change(),
                             "rank_num": self.__get_rank_num(), "medal_cross": self.__get_medal_cross(),
                             "danmu": self.__get_danmu_num(), "min_revenue": self.__revenue_time_data(),
                             "simu_interact": self.__get_simu_interact(), "watched": self.__get_watched_changed(),
                             "sc_data": self.__get_sc_data(), "guard_data": self.__get_guard_data()}

    def get_statistics(self):
        stat_dict = self.__get_audience_statistics()

        # 进场人数
        stat_dict["audience_num"] = len(self.ordered_data["audience"])

        # 涨粉
        stat_dict["fans_change"] = \
            int(self.ordered_data["fans_change"][-1][0]) - int(self.ordered_data["fans_change"][0][0])
        # 涨粉丝团
        stat_dict["medal_change"] = int(self.ordered_data["fans_change"][-1][1]) - \
                                    int(self.ordered_data["fans_change"][0][1])

        # 总营收
        stat_dict["sum_revenue"] = self.ordered_data["revenue"]["sum"]
        # 礼物营收
        stat_dict["gift_revenue"] = self.ordered_data["revenue"]["gift_sum"]
        # sc营收
        stat_dict["sc_revenue"] = self.ordered_data["revenue"]["sc_sum"]
        # 舰团营收
        stat_dict["guard_revenue"] = self.ordered_data["revenue"]["guard_sum"]
        # 人均付费
        stat_dict["avg_revenue"] = self.ordered_data["revenue"]["sum"] / stat_dict["audience_num"]
        # 送礼人次
        stat_dict["gift_num"] = len(self.data["gift"])

        # 直播时长
        stat_dict["live_long"] = "%dh %dm %ds:%ds" % \
                                 (self.live_long[0], self.live_long[1], self.live_long[2], self.live_long[3])

        # 总弹幕数
        stat_dict["danmu_num"] = len(self.data["danmu"])
        # 舰长数
        stat_dict["guard_num"] = len(self.data["guard"])
        try:
            # sc数
            stat_dict["sc_num"] = len(self.data["sc"])
        except KeyError:
            stat_dict["sc_num"] = 0
        # 总互动数
        stat_dict["interact_num"] = len(self.data["danmu"]) + stat_dict["sc_num"] + len(self.data["guard"]) + len(
            self.data["gift"])

        # 平均弹幕数
        stat_dict["avg_danmu"] = stat_dict["danmu_num"] / stat_dict["audience_num"]
        # 平均互动数
        stat_dict["avg_interact"] = stat_dict["interact_num"] / stat_dict["audience_num"]
        # 观众的平均观看时长
        stat_dict['watch_time'] = stat_dict['watch_time'] / stat_dict["audience_num"]

        # 参与互动的观众的平均弹幕数
        stat_dict["interactor_avg_danmu"] = stat_dict["danmu_num"] / stat_dict["interact_audience"]
        # 参与互动的观众的平均互动数
        stat_dict["interactor_avg_interact"] = stat_dict["interact_num"] / stat_dict["interact_audience"]
        # 参与互动的观众的平均观看时长
        stat_dict["interactor_avg_watch_time"] = stat_dict["interactor_avg_watch_time"] / stat_dict["interact_audience"]

        return stat_dict, self.ordered_data

    def __get_time(self):
        self.start_time = self.data["start_time"]
        self.end_time = self.data["end_time"]
        live_long = (int((self.end_time - self.start_time).seconds / 3600),
                     int((self.end_time - self.start_time).seconds / 60) % 60,
                     ((self.end_time - self.start_time).seconds % 60), (self.end_time - self.start_time).seconds)
        return live_long

    def __get_revenue(self):
        revenue = {"sum": 0, "gift_sum": 0, "sc_sum": 0, "guard_sum": 0,
                   "gift": [], "sc": [], "guard": [], "_10_revenue": 0, "_10_100_revenue": 0, "_100_revenue": 0}
        for gift in self.data["gift"]:
            if gift[global_var.GIFT_PRICE] > 0.01:
                revenue["sum"] += gift[global_var.GIFT_PRICE]
                revenue["gift_sum"] += gift[global_var.GIFT_PRICE]
                revenue["gift"].append((gift[global_var.GIFT_PRICE],
                                        (gift[global_var.TIME_STAMP] - self.start_time).seconds))
            if gift[global_var.GIFT_PRICE] <= 10:
                revenue["_10_revenue"] += gift[global_var.GIFT_PRICE]
            elif gift[global_var.GIFT_PRICE] <= 100:
                revenue["_10_100_revenue"] += gift[global_var.GIFT_PRICE]
            else:
                revenue["_100_revenue"] += gift[global_var.GIFT_PRICE]
        try:
            for gift in self.data["guard"]:

                revenue["sum"] += gift[global_var.GIFT_PRICE]
                revenue["guard_sum"] += gift[global_var.GIFT_PRICE]
                revenue["guard"].append((gift[global_var.GIFT_PRICE],
                                         (gift[global_var.TIME_STAMP] - self.start_time).seconds))
                if gift[global_var.GIFT_PRICE] <= 10:
                    revenue["_10_revenue"] += gift[global_var.GIFT_PRICE]
                elif gift[global_var.GIFT_PRICE] <= 100:
                    revenue["_10_100_revenue"] += gift[global_var.GIFT_PRICE]
                else:
                    revenue["_100_revenue"] += gift[global_var.GIFT_PRICE]
        except KeyError:
            pass
        try:
            for gift in self.data["sc"]:
                revenue["sum"] += gift[global_var.GIFT_PRICE]
                revenue["sc_sum"] += gift[global_var.GIFT_PRICE]
                revenue["sc"].append((gift[global_var.GIFT_PRICE], (gift[global_var.TIME_STAMP] - self.start_time).seconds))
                if gift[global_var.GIFT_PRICE] <= 10:
                    revenue["_10_revenue"] += gift[global_var.GIFT_PRICE]
                elif gift[global_var.GIFT_PRICE] <= 100:
                    revenue["_10_100_revenue"] += gift[global_var.GIFT_PRICE]
                else:
                    revenue["_100_revenue"] += gift[global_var.GIFT_PRICE]
        except KeyError:
            pass
        return revenue

    def __get_renqi(self):
        renqi = []
        for msg in self.data["renqi"]:
            renqi.append((msg[global_var.TEXT].split(":")[1], (msg[global_var.TIME_STAMP] - self.start_time).seconds))
        ordered_renqi = []
        for msg in renqi:
            time = int(msg[1] / 60)
            if len(ordered_renqi) <= time:
                ordered_renqi.append([0, time, 0])
            ordered_renqi[time][0] += 1
            ordered_renqi[time][2] += int(msg[0])
        data = []
        for i in ordered_renqi:
            data.append([i[2] / i[0], i[1]])
        return data

    def __get_watched_changed(self):
        watched = []
        for msg in self.data["watched_change"]:
            watched.append((msg[global_var.TEXT].split(":")[1], (msg[global_var.TIME_STAMP] - self.start_time).seconds))
        ordered_watched = []
        max_num = None
        for msg in watched:
            time = int(msg[1] / 60)
            if len(ordered_watched) <= time:
                ordered_watched.append([0, time, 0])
            ordered_watched[time][0] += 1
            ordered_watched[time][2] += int(msg[0])
            max_num = int(msg[0])
        data = []

        for i in ordered_watched:
            data.append([i[2] / i[0], i[1]])
        data[-1][0] = max_num
        return data

    def __get_hot_rank(self):
        hot_rank = []
        for msg in self.data["watch_num"]:
            hot_rank.append((msg[global_var.TEXT].split(":")[1],
                             (msg[global_var.TIME_STAMP] - self.start_time).seconds))
        ordered_hot_rank = []

        for msg in hot_rank:
            time = int(msg[1] / 60)
            length = len(ordered_hot_rank)
            for i in range(length, time + 1):
                ordered_hot_rank.append([0, i, 0])
            ordered_hot_rank[time][0] += 1
            ordered_hot_rank[time][2] += int(msg[0])
        data = []
        for i in ordered_hot_rank:
            if i[0] != 0:
                data.append([i[2] / i[0], i[1]])
            else:
                data.append(data[-1])
        return data

    def __get_fans_change(self):
        fans_change = []
        for msg in self.data["fans_change"]:
            temp = msg[global_var.TEXT].split(":")
            fans_change.append((temp[1].split("，")[0], temp[2], (msg[global_var.TIME_STAMP] - self.start_time).seconds))
        fans_start = int(fans_change[0][0])

        ordered_fans_change = []

        ordered_fans_change.append([1, 0, 0])
        for msg in fans_change:
            time = int(int(msg[2]) / 60)
            length = len(ordered_fans_change)
            for i in range(length, time + 1):
                ordered_fans_change.append([0, i, 0])
            ordered_fans_change[time][0] += 1
            ordered_fans_change[time][2] += int(msg[0])
        data = []
        for i in ordered_fans_change:
            if i[0] != 0:
                data.append([i[2] / i[0] - fans_start, i[1]])
            else:
                data.append(data[-1])
        return data

    def __get_rank_num(self):
        rank_num = []
        try:
            for msg in self.data["rank_num"]:
                temp = msg[global_var.TEXT].split(":")
                rank_num.append((temp[1].split(",")[0], temp[2], (msg[global_var.TIME_STAMP] - self.start_time).seconds))
        except KeyError:
            return None
        return rank_num

    def __get_audience_msg(self):
        audience = {}
        for msg in self.data["entry"]:
            if msg[global_var.UID] not in audience:
                audience[msg[global_var.UID]] = [msg]
            else:
                audience[msg[global_var.UID]].append(msg)
        for msg in self.data["danmu"]:
            if msg[global_var.UID] not in audience:
                audience[msg[global_var.UID]] = [msg]
            else:
                audience[msg[global_var.UID]].append(msg)
        try:
            for msg in self.data["sc"]:
                if msg[global_var.UID] not in audience:
                    audience[msg[global_var.UID]] = [msg]
                else:
                    audience[msg[global_var.UID]].append(msg)
        except KeyError:
            print("本场没有sc捏")
        try:

            for msg in self.data["gift"]:
                if msg[global_var.UID] not in audience:
                    audience[msg[global_var.UID]] = [msg]
                else:
                    audience[msg[global_var.UID]].append(msg)
        except KeyError:
            print("本场没有礼物捏")
        try:
            for msg in self.data["guard"]:
                if msg[global_var.UID] not in audience:
                    audience[msg[global_var.UID]] = [msg]
                else:
                    audience[msg[global_var.UID]].append(msg)
        except KeyError:
            print("本场没有舰长捏")
        for uid, msg_list in audience.items():
            msg_list.sort(key=lambda v: v[global_var.TIME_STAMP])
        return audience

    def __get_medal_cross(self):
        medal_statistics = {}
        for uid, msg_list in self.audience_send_msg.items():
            acc_list = []
            for msg in msg_list:
                medal = msg[global_var.ROOM_ID_OF_MEDAL]
                if medal not in acc_list:
                    acc_list.append(medal)
                    if medal in medal_statistics:
                        medal_statistics[medal] += 1
                    else:
                        medal_statistics[medal] = 1

        return medal_statistics

    def __get_audience(self):
        audience_statistics = {}
        for uid, msg_list in self.audience_send_msg.items():
            audience_statistics[uid] = {"danmu": 0, "interact": 0, "sc": 0, "guard": 0, "entry": 0,
                                        "gift": 0, "watch_time": 0, "pay": 0, "medal_level": 0}

            status = 'start'
            user_latest_time = self.start_time

            for msg in msg_list:

                # 判断粉丝勋章
                temp_medal = msg[global_var.ROOM_ID_OF_MEDAL]
                if temp_medal in self.org_config["org_room_id_list"] or temp_medal in self.org_config['org_uid_list']:
                    if audience_statistics[uid]["medal_level"] < msg[global_var.LEVEL_OF_MEDAL]:
                        medal_level = msg[global_var.LEVEL_OF_MEDAL]
                        audience_statistics[uid]["medal_level"] = medal_level

                # 消息记数
                audience_statistics[uid][msg[global_var.MSG_TYPE]] += 1

                # 付费记数
                pay = msg[global_var.GIFT_PRICE]
                if pay > 0.01:
                    audience_statistics[uid]["pay"] += pay

                # 观看时间估算
                msg_type = msg[global_var.MSG_TYPE]

                if status == 'start':
                    # 确定首次最近出现在直播间的时间

                    if msg_type == "entry":
                        # 如果首条消息是进入消息，记录entry时间为首次进入时间
                        user_latest_time = msg[global_var.TIME_STAMP]
                        status = 'entry'

                    else:
                        # 如果首条消息是互动类消息（上舰、送礼物、弹幕、sc）,那就估测观众在未开播时已经进入了直播间，首次进入时间记作开播时间
                        status = 'interact'

                elif status == 'entry' and msg_type == "entry":
                    # 如果上一次是入场消息，且本次是入场消息,则为上次记录300s观看时间（b站两次入场消息触发最低间隔600s)
                    audience_statistics[uid]["watch_time"] += 300
                    user_latest_time = msg[global_var.TIME_STAMP]
                    status = "entry"

                elif status == 'entry' and msg_type != "entry":
                    # 如果上一次是入场消息，且本次消息是互动消息，则全额记录两次之间的时间
                    audience_statistics[uid]["watch_time"] += (msg[global_var.TIME_STAMP] - user_latest_time).seconds
                    status = "interact"
                    user_latest_time = msg[global_var.TIME_STAMP]

                elif status == "interact" and msg_type == 'entry':
                    # 如果上一次是互动消息，本次是入场消息，则估测为刷新直播间，全额记录
                    audience_statistics[uid]["watch_time"] += (msg[global_var.TIME_STAMP] - user_latest_time).seconds
                    status = "entry"
                    user_latest_time = msg[global_var.TIME_STAMP]

                elif status == "interact" and msg_type != "entry":
                    # 如果两次全都是互动消息，默认观众一直在直播间，全额记录
                    audience_statistics[uid]["watch_time"] += (msg[global_var.TIME_STAMP] - user_latest_time).seconds
                    status = "entry"
                    user_latest_time = msg[global_var.TIME_STAMP]

            # 估算观看时长
            if status == "interact":
                # 如果观众在本直播间最后一次是互动消息，则认为他后续又观看了1/10直播长度或直到直播结束（小于1/10直播时间长度）
                add_time = self.live_long[3] / 10
            else:
                # 如果观众在本直播间最后一次是入场消息，则认为他后续又观看了300s或直到直播结束
                add_time = 300
            delta_time = (self.end_time - msg_list[-1][global_var.TIME_STAMP]).seconds
            if add_time < delta_time:
                audience_statistics[uid]["watch_time"] += add_time
            else:
                audience_statistics[uid]["watch_time"] += delta_time

            audience_statistics[uid]["interact"] = audience_statistics[uid]["danmu"] + audience_statistics[uid]["gift"] \
                                                   + audience_statistics[uid]["sc"] + audience_statistics[uid]["guard"]

        return audience_statistics

    def __get_audience_statistics(self):
        # 互动人数
        interact_num = 0
        # 参与互动观众的平均观看时长
        interact_watch_sum = 0
        # 观看时长
        watch_time = 0

        # 非粉丝数，非粉丝互动数
        _0_medal = 0
        # 非粉丝团互动人数
        _0_medal_interact = 0
        # 非粉丝团互动条数
        _0_medal_interact_num = 0
        # 非粉丝团弹幕条数
        _0_medal_danmu_num = 0

        # 1-5级粉丝人数
        _1_5_medal = 0
        # 1-5级互动人数
        _1_5_medal_interact = 0
        # 1-5级互动条数
        _1_5_medal_interact_num = 0
        # 1-5级弹幕条数
        _1_5_medal_danmu_num = 0

        # 6-10级粉丝人数
        _6_10_medal = 0
        # 6-10级互动人数
        _6_10_medal_interact = 0
        # 6-10级互动条数
        _6_10_medal_interact_num = 0
        # 6-10级弹幕条数
        _6_10_medal_danmu_num = 0

        # 11-20级粉丝人数
        _11_20_medal = 0
        # 11-20级互动人数
        _11_20_medal_interact = 0
        # 11-20级互动条数
        _11_20_medal_interact_num = 0
        # 11-20级弹幕条数
        _11_20_medal_danmu_num = 0

        # 21级以上粉丝人数
        _21_medal = 0
        # 21级以上互动人数
        _21_medal_interact = 0
        # 21级以上互动条数
        _21_medal_interact_num = 0
        # 21级以上弹幕条数
        _21_medal_danmu_num = 0

        for uid, data in self.ordered_data["audience"].items():
            watch_time += data["watch_time"]
            if data["interact"] > 0:
                interact_num += 1
                interact_watch_sum += data["watch_time"]
            if data["medal_level"] == 0:
                _0_medal += 1
                _0_medal_interact_num += data["interact"]
                _0_medal_danmu_num += data["danmu"]
            elif data["medal_level"] < 6:
                _1_5_medal += 1
                _1_5_medal_interact_num += data["interact"]
                _1_5_medal_danmu_num += data["danmu"]

            elif data["medal_level"] < 11:
                _6_10_medal += 1
                _6_10_medal_interact_num += data["interact"]
                _6_10_medal_danmu_num += data["danmu"]

            elif data["medal_level"] < 21:
                _11_20_medal += 1
                _11_20_medal_interact_num += data["interact"]
                _11_20_medal_danmu_num += data["danmu"]

            else:
                _21_medal += 1
                _21_medal_interact_num += data["interact"]
                _21_medal_danmu_num += data["danmu"]

        return {"interact_audience": interact_num, "interactor_avg_watch_time": interact_watch_sum,
                "watch_time": watch_time,
                "_0_medal_interact_num": _0_medal_interact_num, "_0_medal_danmu_num": _0_medal_danmu_num,
                "_0_medal": _0_medal,
                "_1_5_medal_interact_num": _1_5_medal_interact_num, "_1_5_medal_danmu_num": _1_5_medal_danmu_num,
                "_1_5_medal": _1_5_medal,
                "_6_10_medal_interact_num": _6_10_medal_interact_num, "_6_10_medal_danmu_num": _6_10_medal_danmu_num,
                "_6_10_medal": _6_10_medal,
                "_11_20_medal_interact_num": _11_20_medal_interact_num,
                "_11_20_medal_danmu_num": _11_20_medal_danmu_num,
                "_11_20_medal": _11_20_medal,
                "_21_medal_interact_num": _21_medal_interact_num, "_21_medal_danmu_num": _21_medal_danmu_num,
                "_21_medal": _21_medal}

    def __get_danmu_num(self):
        data = []
        for msg in self.data["danmu"]:
            time = int((msg[global_var.TIME_STAMP] - self.start_time).seconds / 60)
            while len(data) <= time:
                data.append([0, len(data)])
            data[time][0] += 1
        return data

    def __get_simu_interact(self):
        simu_min_list = {}
        for uid, msg in self.audience_send_msg.items():
            user_in = []
            for i in msg.__iter__():
                if i[global_var.MSG_TYPE] == "entry":
                    continue
                else:
                    time = int((i[global_var.TIME_STAMP] - self.start_time).seconds / 60)
                    for j in range(10):
                        if time + j in user_in:
                            continue
                        else:
                            if time + j in simu_min_list:
                                simu_min_list[time + j] += 1
                            else:
                                simu_min_list[time + j] = 1
                            user_in.append(time + j)
        simu_min_list = sorted(simu_min_list.items(), key=lambda x: x[0])
        for time in range(10):
            simu_min_list.pop(-1)
        return simu_min_list

    def __revenue_time_data(self):
        min_revenue = []
        for msg in self.data["gift"]:
            time = int((msg[global_var.TIME_STAMP] - self.start_time).seconds / 60)
            while len(min_revenue) <= time:
                min_revenue.append([0, len(min_revenue)])
            min_revenue[time][0] += msg[global_var.GIFT_PRICE]
        try:
            for msg in self.data["sc"]:
                time = int((msg[global_var.TIME_STAMP] - self.start_time).seconds / 60)
                if len(min_revenue) <= time:
                    min_revenue.append([0, time])
                min_revenue[time][0] += msg[global_var.GIFT_PRICE]
        except KeyError:
            pass

        try:
            for msg in self.data["guard"]:
                time = int((msg[global_var.TIME_STAMP] - self.start_time).seconds / 60)
                if len(min_revenue) <= time:
                    min_revenue.append([0, time])
                min_revenue[time][0] += msg[global_var.GIFT_PRICE]
        except KeyError:
            pass

        return min_revenue

    def __get_sc_data(self):
        sc_data = []
        try:
            for msg in self.data["sc"]:
                time = int((msg[global_var.TIME_STAMP] - self.start_time).seconds / 60)
                while len(sc_data) <= time:
                    sc_data.append([0, len(sc_data)])
                sc_data[time][0] += 1
        except KeyError:
            pass
        return sc_data

    def __get_guard_data(self):
        guard_data = []
        try:
            for msg in self.data["guard"]:
                time = int((msg[global_var.TIME_STAMP] - self.start_time).seconds / 60)
                while len(guard_data) <= time:
                    guard_data.append([0, len(guard_data)])
                if msg[global_var.GIFT_PRICE] > 1:
                    guard_data[time][0] += 1
        except KeyError:
            pass
        return guard_data