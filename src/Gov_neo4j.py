import utils as ut
from py2neo import Graph, Node, Relationship, NodeMatcher, RelationshipMatcher
import argparse
import json
# from igraph import Graph as IGraph
import os


##连接neo4j数据库，输入地址、用户名、密码
# graph = Graph('http://localhost:7474', username='neo4j', password='312300Gjw')


def cal_pagerank(graph):
    print('正在计算PageRank...')
    cmd = '''MATCH (n:Person) WITH collect(n) as nodes CALL apoc.algo.pageRank(nodes) YIELD node,score 
    MATCH (c:Person) WHERE c.name = node.name
    SET c.pagerank = score
    '''
    graph.run(cmd)
    print('成功设置为节点属性')


def get_pagerank(graph, result_dir):
    cmd = '''MATCH(n:Person) return n.name as name,n.pagerank as pagerank order by n.pagerank desc'''
    data = graph.run(cmd).data()
    print('Task 3 Top 10 Pagerank')
    for i, d in enumerate(data):
        print(str(i+1)+".:  " + d['name'] + '  ' + str(d['pagerank']))
        if i>=9:
            break
    json_pagerank = json.dumps(data, ensure_ascii=False, indent=2)
    with open(result_dir + '/pagerank_neo4j.json', 'w') as json_file:
        json_file.write(json_pagerank)


def cal_betweenness(graph, result_dir):
    print('正在计算Betweenness centrality...')
    cmd = "call algo.betweenness.stream('Person','co-occur',{direcrion:'out'}) yield nodeId,centrality return algo.getNodeById(nodeId).name as name,centrality order by centrality desc"
    data = graph.run(cmd).data()
    write_clusters_query = '''
        UNWIND {nodes} AS n
        MATCH(c:Person) Where c.name=n.name
        set c.betweenness=n.centrality
        '''
    graph.run(write_clusters_query, nodes=data)
    print('成功设置为节点属性')
    # 写入文件
    json_betweeness = json.dumps(data, ensure_ascii=False, indent=2)
    with open(result_dir + '/betweeness_neo4j.json', 'w') as json_file:
        json_file.write(json_betweeness)


def get_betweenness(graph):
    cmd = '''MATCH(n:Person) return n.name as name,n.betweenness as betweenness order by n.betweenness desc'''
    data = graph.run(cmd).data()
    print('Task 4 Top 10 Betweenness centrality')
    for i, d in enumerate(data):
        print(str(i + 1) + ".:  " + d['name'] + '  ' + str(d['betweenness']))
        if i >= 9:
            break


def cal_louvain_community(graph):
    print('正在划分社区...')
    cmd = '''CALL algo.louvain.stream('Person', 'co-occur', {
     graph: 'huge',
     direction: 'BOTH'
    }) YIELD nodeId, community, communities
    RETURN algo.asNode(nodeId).name as name, community
    ORDER BY name ASC'''
    data = graph.run(cmd).data()
    write_clusters_query = '''
    UNWIND {nodes} AS n
    MATCH(c:Person) Where c.name=n.name
    set c.community=toInt(n.community)
    '''
    graph.run(write_clusters_query, nodes=data)
    print('成功设置为节点属性')



def get_louvain_community(graph,result_dir):
    cmd = '''MATCH (c:Person)
    WITH c.community AS cluster, collect(c.name) AS  members
    RETURN cluster, members ORDER BY cluster ASC'''
    community = graph.run(cmd).data()
    community_json = json.dumps(community, ensure_ascii=False, indent=2)
    with open(result_dir + '/community_neo4j.json', 'w') as json_file:
        json_file.write(community_json)


if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Gov news analysis with Neo4j')
    # parser.add_argument('-u', '--url', help="neo4j数据库url", type = str, default = 'http://localhost:7474')
    # parser.add_argument('-n', '--name', help="neo4j数据库用户名", type = str, default = 'neo4j')
    # parser.add_argument('-p', '--password', help="neo4j数据库密码", type = str, default = 'neo4j')
    parser.add_argument('-d', '--json_path', type=str, default='../data/data_Json/relation_filtered.json',
                        help='relation文件路径')
    parser.add_argument('-n', '--result_dir', type=str, default='../data/data_Json', help='结果保存目录')

    parser.add_argument('-c', '--create_graph', action="store_true", help="创建neo4j数据")
    parser.add_argument('-cpr', '--calculate_pagerank', action="store_true", help='影响力计算：计算pagerank影响力，并更新neo4j数据库数据')
    parser.add_argument('-pr', '--pagerank', action="store_true", help='获取影响力：使用PageRank算法计算每个人的影响力大小，并给出影响力最大的前20个人')
    parser.add_argument('-cbc', '--calculate_betweeness_centrality', action="store_true", help='中介中心性计算：计算并设置neo4j节点中介中心性属性')
    parser.add_argument('-bc', '--betweeness_centrality', action="store_true", help='获取中介中心性：返回最大的10个中介中心性')
    parser.add_argument('-cl', '--calculate_louvain', action="store_true", help='社区挖掘：挖掘该社交网络中的社区')
    parser.add_argument('-l', '--louvain', action="store_true", help='获取社区')

    args = parser.parse_args()

    ##连接neo4j数据库，输入地址、用户名、密码
    if args.create_graph or args.calculate_pagerank or args.calculate_betweeness_centrality or args.calculate_louvain:
        try:
            url  = input('请输入Neo4j数据库地址 >>> ')
            name = input('请输入登录名          >>> ')
            password = input('请输入密码            >>> ')
            # graph = Graph(url, username=name, password=password)
            print('数据库连接成功')
            print('\n')
            # graph = Graph('http://localhost:7474', username='neo4j', password='312300Gjw')
        except:
            print('无法正常连接Neo4j，请检查Neo4j是否正确打开')
            exit(1)

    # graph = Graph(args.url, username=args.name, password=args.password)
    # print(graph)
    if args.create_graph:
        if not os.path.exists(args.json_path):
            print('关系文件路径错误，无法无法创建数据库')
            exit(1)
    if args.calculate_pagerank or args.calculate_betweeness_centrality or args.calculate_louvain:
        if not os.path.exists(args.result_dir):
            os.mkdir(args.result_dir)
    human_path = args.result_dir + '/human_sorted2.json'
    relation_path = args.result_dir + '/relation_filtered.json'
    if args.create_graph:
        ut.create_neo4j_graph(human_path, relation_path, graph)
    if args.calculate_pagerank:
        cal_pagerank(graph)
    if args.pagerank:
        get_pagerank(graph, args.result_dir)

    if args.calculate_betweeness_centrality:
        cal_betweenness(graph, args.result_dir)
    if args.betweeness_centrality:
        get_betweenness(graph)

    if args.calculate_louvain:
        cal_louvain_community(graph)
    if args.louvain:
        get_louvain_community(graph, args.result_dir)

