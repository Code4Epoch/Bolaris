"""
@author:zzh、lucien
@update_time:2021_7_3
"""
import jieba
import wordcloud
import numpy as np
from wordcloud import WordCloud, ImageColorGenerator
from imageio import imread
import matplotlib.pyplot as plt
import os

jieba.load_userdict("./word_dict/asoul_word.txt")
# 用来正常显示中文标签
plt.rcParams['font.sans-serif'] = ['SimHei']
# 用来正常显示负号
plt.rcParams['axes.unicode_minus'] = False


def get_word_dictionary(path):
    """

    :param path: 停词词典的路径
    :return: 停词列表
    """
    with open("%s" % path, encoding='utf-8') as word_file:
        stop_word = word_file.read()
        stop_word_list = stop_word.split(sep=',')
        # print(stop_word_list)
    return stop_word_list


def get_synonym_words(path):
    """

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


def del_repeat_word(words):
    """

    :param words:原始句子
    :return: 去除了重复词的句子内词列表
    """
    result = jieba.cut(words)
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
        # print(temp_word_list)
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
    :return: 去除了投票词、停词、合并了同义词的词频字典
    """
    my_data = my_live_data_group_by_type['danmu']

    # 加载一些词典
    stop_word = get_word_dictionary('./word_dict/asoul_stop_word.txt')
    stop_word.append(',')
    vote_word = ['a', 'A', 'b', 'B', 'c', 'C', 'd', 'D', '1', '2', '3', '4']
    synonym_dict = get_synonym_words('./word_dict/asoul_synonym_word.txt')

    word_freq_dict = combine_synonym_word(my_data, synonym_dict)
    word_freq_dict = delete_stop_vote_word(word_freq_dict, stop_word, vote_word)

    return word_freq_dict


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
                             mode="RGBA")
    wc.generate_from_frequencies(my_word_freq_dict)
    plt.imshow(wc.recolor(color_func=image_colors))
    plt.clf()
    save_path = "./output/%s/" % road
    if os.path.exists(save_path) is False:
        os.makedirs(save_path)
    wc.to_file(save_path + "wordcloud.jpg")


def make_word_freq_bar(my_word_freq_dict, road):
    """

    :param my_word_freq_dict: 词频字典
    :param road: 文件目录
    :return:
    """
    plt.bar(my_word_freq_dict.keys(), my_word_freq_dict.values())
    plt.xticks(rotation=300)
    save_path = './output/%s/' % road
    if os.path.exists(save_path) is False:
        os.makedirs(save_path)
    plt.savefig(save_path + "word_freq.png")
    plt.clf()


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

