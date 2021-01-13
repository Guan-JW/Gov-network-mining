import csv
import numpy as np
import jieba.posseg as jp
import matplotlib
import json
import networkx as nx
from py2neo import Graph, Node, Relationship, NodeMatcher
import argparse
import os


def load_data(filename, save_dir):
    '''
    结巴分词
    对其中的新闻标题和正文内容进行分词并抽取其中包含的人名、机构名和地名
    共29699条
    :param filename: 新闻文件路径
    :return: NULL
    '''
    human_relation = {}
    organs = {}
    places = {}
    human = {}
    with open(filename, encoding="utf-8") as f:
        data = csv.reader(f, delimiter='\t')
        for i, row in enumerate(data):
            # print(i)
            human_name = set()
            organ_name = set()
            place_name = set()
            if i == 0:  # skip the first row
                continue
            for index in range(3, 5):  # 3-title, 4-text
                for word, flag in jp.lcut(row[index]):
                    if flag in ('nr', 'nrfg', 'nrt'):  # 人名
                        human_name.add(word)
                    elif flag == 'ns':  # 地名
                        place_name.add(word)
                    elif flag == 'nt':  # 机构名
                        organ_name.add(word)

            # 统计关系
            for h1 in human_name:
                if h1 not in human.keys():
                    human[h1] = 1
                else:
                    human[h1] += 1
                if h1 not in human_relation.keys():
                    human_relation[h1] = {}
                for h2 in human_name:
                    if h2 not in human_relation[h1].keys():
                        human_relation[h1][h2] = 1
                    else:
                        human_relation[h1][h2] += 1
            # 统计地名
            for place in place_name:
                if place not in places.keys():
                    places[place] = 1
                else:
                    places[place] += 1
            # 统计机构
            for organ in organ_name:
                if organ not in organs.keys():
                    organs[organ] = 1
                else:
                    organs[organ] += 1

    # print(human_relation)
    # dump files
    json_relation = json.dumps(human_relation, ensure_ascii=False, indent=2)
    json_place = json.dumps(places, ensure_ascii=False, indent=2)
    json_organ = json.dumps(organs, ensure_ascii=False, indent=2)
    json_human = json.dumps(human, ensure_ascii=False, indent=2)
    with open(save_dir + '/relation.json', 'w') as json_file:
        json_file.write(json_relation)
    with open(save_dir + '/places.json', 'w') as json_file:
        json_file.write(json_place)
    with open(save_dir + '/organs.json', 'w') as json_file:
        json_file.write(json_organ)
    with open(save_dir + '/human.json', 'w') as json_file:
        json_file.write(json_human)


def read_json(filename):
    with open(filename, 'r') as f:
        dict_data = json.load(f)
        return dict_data


def read_utf_json(filename):
    with open(filename, 'rb') as f:
        dict_data = json.load(f)
        return dict_data


def sort_files(filename):
    '''
    实体按出现次数排序
    :param filename: 文件路径
    :return: NULL
    '''
    data  = read_json(filename)
    data_sorted = sorted(data.items(), key=lambda x: x[1], reverse=True)
    json_human_sorted = json.dumps(data_sorted, ensure_ascii=False, indent=2)
    save_path = filename.split('/')[1].split('.')[0] + '_sorted.json'   # 生成保存路径
    # print(save_path)
    # print(data_sorted[:5])
    with open(save_path, 'w') as json_file:
        json_file.write(json_human_sorted)


def filter(source_path, target_path, source_relation_path, target_relation_path):
    '''
    过滤单字姓名 及 过滤关系
    :param source_path: 姓名 源文件路径
    :param target_path: 过滤后的姓名 目标保存路径
    :param source_relation_path: 关系 源文件路径
    :param target_relation_path: 过滤后的关系 目标保存路径
    :return: NULL
    '''
    human_filtered = read_json(source_path)
    human_filtered_set = set()
    human_filtered_list = []
    for h in human_filtered:
        if len(h[0]) != 1:  # 删除长度为1的名字
            human_filtered_list.append(h)
            human_filtered_set.add(h[0])
    json_human_sorted = json.dumps(human_filtered_list, ensure_ascii=False, indent=2)
    with open(target_path, 'w') as json_file:
        json_file.write(json_human_sorted)

    # 过滤关系，删除不在姓名集合中的关系
    relation = read_json(source_relation_path)
    relation_filtered = {}
    for i in relation.keys():
        if i in human_filtered_set:
            relation_filtered[i] = {}
            for j in relation[i]:
                if j in human_filtered_set:
                    relation_filtered[i][j] = relation[i][j]
    json_relation_filtered = json.dumps(relation_filtered, ensure_ascii=False, indent=2)
    with open(target_relation_path, 'w') as json_file:
        json_file.write(json_relation_filtered)


def create_neo4j_graph(human_path, relation_path, graph):
    '''
    创建neo4j图数据库
    :param human_path: 人名文件路径
    :param relation_path: 关系路径
    :return: NULL
    '''
    print('正在清空原始数据...')
    cmd = 'match (n) detach delete n'   # 清空已有数据
    graph.run(cmd)
    human_filtered = read_json(human_path)
    relation = read_json(relation_path)
    # 创建节点
    print('正在导入节点...')
    for h in human_filtered:
        a = Node('Person', name=h[0])
        graph.create(a)
    # 创建边
    print('正在导入关系...')
    for h1 in relation.keys():
        for h2 in relation[h1].keys():
            if h1 == h2:
                continue
            cmd = "MATCH (n1:Person {name: '" + h1 + "'}) MATCH (n2:Person {name: '" + h2 + "'}) MERGE (n2)-[r:`co-occur`]->(n2) SET r.weight = " + str(
                relation[h1][h2])
            graph.run(cmd)
    print('数据库创建成功')


def create_networkx_graph(relation_path):
    relation = read_json(relation_path)
    G = nx.Graph()
    for h1 in relation.keys():
        for h2 in relation[h1].keys():
            if h1 == h2:
                continue
            G.add_edge(h1, h2, weight=relation[h1][h2])
    return G


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Data preprocessing')
    parser.add_argument('-d','--save_dir', type=str,
                        default='../data/new_data_Json', help='预处理结果保存目录')

    args = parser.parse_args()
    if not os.path.exists(args.save_dir):
        os.mkdir(args.save_dir)

    # 读取数据，jieba分词抽取实体
    filename = '../gov_news/gov_news.txt'
    load_data(filename, args.save_dir)
    #
    # 排序
    filename1 = args.save_dir + '/human.json'
    sort_files(filename1)
    filename2 = args.save_dir + '/places.json'
    sort_files(filename2)
    filename3 = args.save_dir + '/organs.json'
    sort_files(filename3)
    #
    # 过滤长度为1的人名
    source_path = args.save_dir + '/human_sorted1.json'
    target_path = args.save_dir + '/human_sorted2.json'
    relation_path = args.save_dir + '/relation.json'
    target_relation_path = args.save_dir + '/relation_filtered.json'
    filter(source_path, target_path, relation_path, target_relation_path)

