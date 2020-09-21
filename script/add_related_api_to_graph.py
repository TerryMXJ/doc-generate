from project.utils.path_util import PathUtil
from sekg.graph.exporter.graph_data import GraphData, NodeInfo
import networkx as nx
from networkx.algorithms.similarity import simrank_similarity

'''
添加相关api
'''

pro_name = "jabref"
graph_data_path = PathUtil.graph_data(pro_name=pro_name, version="v3.9")
graph_data_save_path = PathUtil.graph_data(pro_name=pro_name, version="v3.10")

graph_data: GraphData = GraphData.load(graph_data_path)

# def find_adj_node_with_label(id, label):
#     result = []
#     for i in graph_data.get_all_in_relations(id):
#         if label in graph_data.find_nodes_by_ids(i[0])[0]["labels"]:
#             result.append(i[0])
#     for i in graph_data.get_all_in_relations(id):
#         if label in graph_data.find_nodes_by_ids(i[2])[0]["labels"]:
#             result.append(i[2])
#     return result


def create_subgraph(G, sub_G, start_point, step):
    if step > 2:
        return
    for n in G[start_point]:
        sub_G.add_edge(start_point, n)
        create_subgraph(G, sub_G, n, step+1)


def simrank_cal(sub_G, sp):
    result = simrank_similarity(sub_G, sp, max_iterations=5)
    sorted_result = sorted(result.items(), key=lambda d: d[1], reverse=True)
    return sorted_result


if __name__ == '__main__':
    kinds = ['class', 'method']
    G = nx.Graph(graph_data.graph)
    for kind in kinds:
        print("*************************" + kind + "***********************")
        nodes = graph_data.get_node_ids_by_label(kind)
        for i in nodes:
            origin_node: GraphData = graph_data.find_nodes_by_ids(i)[0]
            print("start process {}".format(origin_node['properties']['qualified_name']))
            sub_G = nx.Graph()
            create_subgraph(G, sub_G, i, 1)
            sim_result = simrank_cal(sub_G, i)
            result = list()
            count = 0
            for j in sim_result:
                if j[0] == i: continue
                if count > 5: break
                node: NodeInfo = graph_data.find_nodes_by_ids(j[0])[0]
                if kind in node["labels"]:
                    result.append(j[0])
                    count += 1
            origin_node['properties']['simrank'] = result
            print("save simrank result: " + str(result))
    graph_data.save(graph_data_save_path)
    print("构建完成")




    # G = nx.Graph(graph_data.graph)
    # sub_G = nx.Graph()
    # create_subgraph(G, sub_G, 1207, 1)
    # result = simrank_cal(sub_G, 1207)
    # for i in result:
    #     if i[0] == 1207: continue
    #     node: NodeInfo = graph_data.find_nodes_by_ids(i[0])[0]
    #     if "class" in node["labels"]:
    #         print(i[0])