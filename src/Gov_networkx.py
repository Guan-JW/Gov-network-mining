import utils as ut
import argparse
import networkx as nx
import community.community_louvain  # python-louvain
from collections import defaultdict
import json
from copy import deepcopy
import queue
import os


def graph_validation(relation_path):
    print('TASK 1 图的验证')
    relation = ut.read_json(relation_path)
    while True:
        input_query = input('输入姓名（输入quit退出）>>> ')
        if input_query == 'quit':
            break
        else:
            if input_query not in relation:
                print('抱歉，数据中不包含关于' + input_query + '的信息')
            else:
                personal_relation = relation[input_query]
                personal_relation = sorted(personal_relation.items(), key=lambda x: x[1], reverse=True)
                counter = 0
                for h in personal_relation:
                    if h[0] == input_query:
                        continue
                    print(str(counter + 1) + '.:  ' + h[0] + '  ' + str(h[1]))
                    counter += 1
                    if counter == 10:
                        break
        print('\n')


def graph_statistics(G):
    con_com = list(nx.connected_components(G))
    con_com_sorted = sorted(con_com, key=lambda x: len(x), reverse=True)
    print('TASK 2 图的统计信息')
    print('结点数：      ', len(G.nodes))
    print('边数：        ', len(G.edges))
    print('连通分支数：  ', len(con_com_sorted))
    print('最大连通分支节点数：', len(con_com_sorted[0]))


def cal_pagerank(G,result_dir):
    print('正在计算PageRank...')
    page_rank = nx.pagerank(G, alpha=0.85)
    page_rank = sorted(page_rank.items(), key=lambda x: x[1], reverse=True)
    print('TASK 3 PageRank')

    for i,item in enumerate(page_rank):
        print(str(i+1)+".:  " + page_rank[i][0] + '  ' + str(page_rank[i][1]))
        if i>=9:
            break
    json_pagerank = json.dumps(page_rank, ensure_ascii=False, indent=2)
    with open(result_dir + '/pagerank_networkx.json', 'w') as json_file:
        json_file.write(json_pagerank)
    print('文件保存成功')

def pagerank(path):
    page_rank = ut.read_json(path)
    print('TASK 3 PageRank')
    for i,item in enumerate(page_rank):
        print(str(i+1)+".:  " + page_rank[i][0] + '  ' + str(page_rank[i][1]))
        if i>=9:
            break


def cal_louvain_community(G, result_dir):
    print('正在划分社区...')
    partition = community.community_louvain.best_partition(G)  # Louvain算法划分社区
    comm_dict = defaultdict(list)
    for person in partition:
        comm_dict[partition[person]].append(person)
    json_community = json.dumps(comm_dict, ensure_ascii=False, indent=2)
    with open(result_dir + '/community_networkx.json', 'w') as json_file:
        json_file.write(json_community)


def cal_cluster_coef(G, result_dir):
    print('正在计算聚集系数...')
    cluster_coef = nx.clustering(G)
    cluster_coef = sorted(cluster_coef.items(), key=lambda x: x[1], reverse=True)
    print('Task 5 聚集系数')
    for i, item in enumerate(cluster_coef):
        print(str(i+1)+".:  " + cluster_coef[i][0] + '  ' + str(cluster_coef[i][1]))
        if i>=9:
            break
    json_cluster = json.dumps(cluster_coef, ensure_ascii=False, indent=2)
    with open(result_dir + '/clustering_coef_networkx.json', 'w') as json_file:
        json_file.write(json_cluster)


def cluster_coef(path):
    cluster_coef = ut.read_json(path)
    print('Task 5 聚集系数')
    for i, item in enumerate(cluster_coef):
        print(str(i + 1) + ".:  " + cluster_coef[i][0] + '  ' + str(cluster_coef[i][1]))
        if i >= 9:
            break

# Yen's algorithm for K-shortest paths in an edge-weighted graph G (undirected
# or directed)

# Cost/weight of path p in graph G
def pweight(G, p):
    w = 0
    for i in range(len(p) - 1): w += G[p[i]][p[i + 1]]['weight']
    return w


# Copy edge (a,z) of G, remove it, and return the copy.
# This can become expensive!
def cprm(G, a, z):
    ec = deepcopy(G[a][z])
    G.remove_edge(a, z)
    return (a, z, ec)


# Copy node n of G, remove it, and return the copy.
# This can become expensive!
def cprmnode(G, n):
    ec = deepcopy(G[n])
    G.remove_node(n)
    return (n, ec)


# K shortest paths in G from 'source' to 'target'
def yen(G, source, target, K):
    # First shortest path from the source to the target
    (c, p) = nx.single_source_dijkstra(G, source, target)
    A = [p]
    A_cost = [c]
    B = queue.PriorityQueue()

    for k in range(1, K):

        for i in range(len(A[k - 1]) - 1):
            # Spur node ranges over the (k-1)-shortest path minus its last node:
            sn = A[k - 1][i]
            # Root path: from the source to the spur node of the (k-1)-shortest path
            rp = A[k - 1][:i]
            # We store the removed edges
            removed_edges = []
            removed_root_edges = []
            removed_root_nodes = []
            # Remove the root paths
            for j in range(len(rp) - 1):

                extra_edges = []
                extra_edges = G.edges(rp[j])

                for eg in list(extra_edges):
                    src = eg[0]
                    tgt = eg[1]
                    removed_root_edges.append(cprm(G, src, tgt))
                removed_root_nodes.append(cprmnode(G, rp[j]))

            if len(rp) > 0 and sn != target:
                extra_edges = []
                extra_edges = G.edges(rp[len(rp) - 1])
                for eg in list(extra_edges):
                    src = eg[0]
                    tgt = eg[1]
                    removed_root_edges.append(cprm(G, src, tgt))

                removed_root_nodes.append(cprmnode(G, rp[len(rp) - 1]))

            # Remove the edges that are part of the already-found k-shortest paths
            # which share the same extended root path
            erp = A[k - 1][:i + 1]  # extended root path
            for p in A:
                if erp == p[:i + 1] and G.has_edge(p[i], p[i + 1]):
                    removed_edges.append(cprm(G, p[i], p[i + 1]))
            # The spur path
            DONE = 0
            try:
                (csp, sp) = nx.single_source_dijkstra(G, sn, target)
                sp = sp
                csp = csp
            except:
                # there is no spur path if sn is not connected to the target
                sp = []
                csp = None
                DONE = 1
                # return (A, A_cost)
            if len(sp) > 0:
                # The potential k-th shortest path (the root path may be empty)
                pk = rp + sp

                for nd in removed_root_nodes:
                    G.add_node(nd[0])

                for re in removed_root_edges:
                    G.add_edge(re[0], re[1], weight=re[2]['weight'])
                cpk = pweight(G, pk)
                # Add the potential k-shortest path to the heap
                B.put((cpk, pk))
            # Add back the edges that were removed
            if len(sp) == 0:
                for nd in removed_root_nodes:
                    G.add_node(nd[0])

                for re in removed_root_edges:
                    G.add_edge(re[0], re[1], weight=re[2]['weight'])
            for re in removed_edges:
                G.add_edge(re[0], re[1], weight=re[2]['weight'])
            for nd in removed_root_nodes:
                G.add_node(nd[0])

        if B.empty():
            print('There are only' + str(k) + 'shortest paths for this pair')
            break
        # The shortest path in B that is not already in A is the new k-th shortest path
        while not B.empty():
            cost, path = B.get()
            if path not in A:
                A.append(path)
                A_cost.append(cost)
                break

    return (A, A_cost)


def k_best_route(G):
    print('Task 6 小世界验证，输出10条最优路径')
    while True:
        # k_shortest_paths_file=open('%d_SPs_btw_%s_%s.csv' %(k,src,tgt),'w');
        # k_shortest_paths_file.write('Source,Target,kth-path,Distance,,,SHORTEST PATH,,,,,\n');
        # k_shortest_paths_file.write('%s,%s,' %(src,tgt));
        print("初始化图...")
        G_copy = deepcopy(G)
        input_src = input("请输入源节点(输入quit输出): ")
        if input_src == 'quit':
            break
        input_dst = input("请输入目标节点(输入quit输出): ")
        if input_dst == 'quit':
            break

        print("Calculating...")
        k_path, path_costs = yen(G_copy, input_src, input_dst, 10)
        if len(k_path) < 0:
            print("抱歉, " + input_src + "和" + input_dst + '之间不存在路径')
        else:
            print('{:<10}{:<10}'.format('10-path', 'Path'))
            for i, path in enumerate(k_path):
                print('{:<10}'.format(str(i + 1)), end="")
                for k, node in enumerate(path):
                    if k == len(path) - 1:
                        print(node)
                    else:
                        print(node + ' - ', end="")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Gov news analysis with networkx')
    parser.add_argument('-d', '--json_path', type=str, default='../data/data_Json/relation_filtered.json', help='relation文件路径')
    parser.add_argument('-n', '--result_dir', type=str, default='../data/data_Json', help='结果保存目录')
    parser.add_argument('-v','--validation', action="store_true", help='图的验证，输入一个人名查询与其关系最强的10个邻居')
    parser.add_argument('-s', '--statistics', action="store_true", help='图的统计，图的节点个数，边数，连通分量个数，最大连通分量的大小')
    parser.add_argument('-p', '--pagerank', action="store_true", help='获取影响力：读取文件并输出PageRank分值Top 10')
    parser.add_argument('-f', '--clustering_coef', action="store_true", help='获取聚集系数：读取文件并输出聚集系数Top 10')
    parser.add_argument('-cp', '--cal_pagerank', action="store_true", help='影响力计算：使用PageRank算法计算每个人的影响力大小，并给出影响力最大的前20个人')
    parser.add_argument('-cc', '--cal_community', action="store_true", help='社区挖掘')
    parser.add_argument('-cf', '--cal_clustering_coef', action="store_true", help='节点的聚集系数计算：计算聚集系数最大的10个人')
    parser.add_argument('-w', '--small_world', action="store_true", help='小世界理论验证：输入初始节点和终点，计算10个最优路径')
    args = parser.parse_args()
    if args.validation or args.statistics or args.small_world or args.cal_pagerank or args.cal_community or args.cal_clustering_coef:
        if os.path.exists(args.json_path):
            relation_path = args.json_path
            print('\n正在建立 Networkx 网络...')
            G = ut.create_networkx_graph(relation_path)
            print('Networkx 网络建立完成')

            if args.validation:
                graph_validation(relation_path)

            if args.statistics:
                graph_statistics(G)

            if args.cal_pagerank:
                if not os.path.exists(args.result_dir):
                    os.mkdir(args.result_dir)
                cal_pagerank(G, args.result_dir)

            if args.cal_community:
                if not os.path.exists(args.result_dir):
                    os.mkdir(args.result_dir)
                cal_louvain_community(G, args.result_dir)

            if args.cal_clustering_coef:
                if not os.path.exists(args.result_dir):
                    os.mkdir(args.result_dir)
                cal_cluster_coef(G, args.result_dir)

            if args.small_world:
                k_best_route(G)
        else:
            print('抱歉，该文件不存在')
    else:
        if args.pagerank:
            path = args.result_dir + '/pagerank_networkx.json'
            if not os.path.exists(path):
                print('抱歉，不存在PageRank文件')
            else:
                pagerank(path)
        if args.clustering_coef:
            path = args.result_dir + './clustering_coef_networkx.json'
            if not os.path.exists(path):
                print('抱歉，不存在聚集系数文件')
            else:
                cluster_coef(path)