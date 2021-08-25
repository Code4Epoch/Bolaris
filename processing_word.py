# -*- coding: utf-8 -*- #
# ------------------------------------------------------------------
# File Name:        processing_word
# Author:           ydyjya、lucien
# Version:          1.1
# Created:          2021/7/9
# Description:      根据弹幕数据制作词云
# Function List:    hard_word_dictionary()      --将不想分开的词加入进去
#                   load_stop_word()            --加载停词
#                   get_synonym_words()         --加载同义词词典
#                   get_word_dictionary()       --加载所有词典,返回停词列表、同义词字典
#                   del_repeat_word()           --弹幕原始句子切词，并删除重复词汇
#                   combine_synonym_word()      --合并同义词
#                   delete_stop_vote_word()     --删除同义词和投票词
#                   customize_word_freq_dict()  --超过阈值的词筛出来
# History:
#       <author>        <version>       <time>      <desc>
#       ydyjya,lucien   1.0             2021/7/9    create、并制作了初版的词云
#       ydyjya          1.1             2021/8/18   修改了词频图、词云图的部分格式
# ------------------------------------------------------------------
import jieba
import matplotlib.pyplot as plt


# 用来正常显示中文标签设置字体为黑体
plt.rcParams['font.sans-serif'] = ['SimHei']
# 用来正常显示负号
plt.rcParams['axes.unicode_minus'] = False


def hard_word_dictionary(path):
    """
    强分词
    :param path: 硬分词词典的路径
    :return: 读取硬分词词典到结巴中
    """
    with open("%s" % path, encoding='utf-8') as word_file:
        hard_word = word_file.read()
        word_list = hard_word.split(sep=',')
    for word in word_list:
        jieba.suggest_freq(word, tune=True)


def load_stop_word(path):
    """
    加载停词
    :param path: 停词路径
    :return: 停词列表
    """
    with open("%s" % path, encoding='utf-8') as word_file:
        stop_word = word_file.read()
        stop_word_list = stop_word.split(sep=',')
    return stop_word_list


def get_synonym_words(path):
    """
    加载同义词词典
    :param path: 同义词词典的路径
    :return: 同义词词典
    """
    combine_dict = {}
    for line in open("%s" % path, 'r', encoding='utf-8'):
        seperate_word = line.strip().split("\t")
        num = len(seperate_word)
        for i in range(1, num):
            combine_dict[seperate_word[i]] = seperate_word[0]
    return combine_dict


def get_word_dictionary():
    """
    加载词典
    :param path: 停词词典的路径
    :return: 停词列表
    """
    jieba.load_userdict("./word_dict/asoul_word.txt")
    hard_word_dictionary("./word_dict/hard_word.txt")
    stop_word_list = load_stop_word("./word_dict/asoul_stop_word.txt")
    synonym_word_dict = get_synonym_words("./word_dict/asoul_synonym_word.txt")
    return stop_word_list, synonym_word_dict


def del_repeat_word(sentence):
    """

    :param sentence:原始句子
    :return: 去除了重复词的句子内词列表
    """
    # 下面这行是针对voice_dm特制的，但似乎b站又不打算加上这个功能了，观望
    my_words = sentence.split(';data_group;')[0]
    result = jieba.cut(my_words)
    new_words = []
    for r in result:
        if r not in new_words:
            new_words.append(r)
    # 返回一个去除了重复词的列表
    return new_words


def combine_synonym_word(my_msg_data, my_synonym_dict):
    """

    :param my_msg_data: 消息数据
    :param my_synonym_dict: 同义词词典
    :return: 合并了同义词的词频字典
    """
    word_count_dict = {}
    for msg in my_msg_data:
        temp_word_list = del_repeat_word(msg[6])
        delete_word = []
        for word in temp_word_list:
            if word in my_synonym_dict:
                delete_word.append(word)
        for word in delete_word:
            temp_word_list.remove(word)
            if my_synonym_dict[word] not in temp_word_list:
                temp_word_list.append(my_synonym_dict[word])
        for word in temp_word_list:
            if word not in word_count_dict:
                word_count_dict[word] = 1
            else:
                word_count_dict[word] += 1
    return word_count_dict


def delete_stop_vote_word(my_word_freq_dict, my_vote_word_dict, my_stop_word_dict):
    """

    :param my_word_freq_dict: 原词频字典
    :param my_vote_word_dict: 投票词字典
    :param my_stop_word_dict: 停词字典
    :return: 去除了停词和投票词的词频字典
    """
    delete_word = []
    for word in my_word_freq_dict:
        if word in my_vote_word_dict or word in my_stop_word_dict:
            delete_word.append(word)
    for word in delete_word:
        my_word_freq_dict.pop(word)
    return my_word_freq_dict


def get_word_freq_dic(my_live_data_group_by_type):
    """

    :param my_live_data_group_by_type: 按类型分类的消息字典
    :return: 去除了投票词、停词、合并了同义词的词频字典, 以及分钟热词
    """
    my_data = my_live_data_group_by_type['danmu']

    # 加载一些词典
    stop_word, synonym_dict = get_word_dictionary()
    stop_word.append(',')
    vote_word = ['a', 'A', 'b', 'B', 'c', 'C', 'd', 'D', '1', '2', '3', '4']
    latest_time = my_data[0][5]
    min_hot_word_dict_list = []
    temp_msg_list = []
    for msg in my_data.__iter__():
        now_msg_time = msg[5]
        if (now_msg_time - latest_time).seconds > 60:
            latest_time = now_msg_time
            temp_word_freq_dict = combine_synonym_word(temp_msg_list, synonym_dict)
            temp_word_freq_dict = delete_stop_vote_word(temp_word_freq_dict, stop_word, vote_word)
            min_hot_word_dict_list.append(temp_word_freq_dict)
            temp_msg_list = []
        else:
            temp_msg_list.append(msg)

    word_freq_dict = combine_synonym_word(my_data, synonym_dict)
    word_freq_dict = delete_stop_vote_word(word_freq_dict, stop_word, vote_word)

    return word_freq_dict, min_hot_word_dict_list


def customize_word_freq_dict(my_word_freq_dict, my_word_num):
    """

    :param my_word_freq_dict: 原字典
    :param my_word_num: 前多少个词保留
    :return: 新词典
    """
    dict_order = sorted(my_word_freq_dict.items(), key=lambda x: x[1], reverse=True)
    min_num = dict_order[my_word_num][1]
    new_dict = {}
    for word, count in my_word_freq_dict.items():
        if count >= min_num:
            new_dict[word] = count

    return new_dict
