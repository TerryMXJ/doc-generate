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
exclude_list = ["has return code directive", "has exception code directive", "has concept", "has terminology"]

def create_subgraph(G, sub_G, start_point, step):
    if step > 2:
        return
    in_relations = graph_data.get_all_in_relations(start_point)
    out_relations = graph_data.get_all_out_relations(start_point)
    node_list = list()
    for i in in_relations:
        if i[1] not in exclude_list:
            node_list.append(i[0])
    for i in out_relations:
        if i[1] not in exclude_list:
            node_list.append(i[2])
    for i in node_list:
        sub_G.add_edge(start_point, i)
        create_subgraph(G, sub_G, i, step+1)


def simrank_cal(sub_G, sp):
    result = simrank_similarity(sub_G, sp, max_iterations=5)
    sorted_result = sorted(result.items(), key=lambda d: d[1], reverse=True)
    return sorted_result


if __name__ == '__main__':
    kinds = ['class', 'method']
    G = nx.Graph(graph_data.graph)
    for kind in kinds:
        num = 0
        print("*************************" + kind + "***********************")
        nodes = graph_data.get_node_ids_by_label(kind)
        for i in nodes:
            num += 1
            origin_node: GraphData = graph_data.find_nodes_by_ids(i)[0]
            print("{}: start process {}".format(num, origin_node['properties']['qualified_name']))
            sub_G = nx.Graph()
            create_subgraph(G, sub_G, i, 1)
            sim_result = simrank_cal(sub_G, i)
            result = list()
            count = 0
            for j in sim_result:
                if j[0] == i: continue
                if count > 5: break
                node: NodeInfo = graph_data.find_nodes_by_ids(j[0])[0]
                if kind in node["labels"] and node['properties']['qualified_name'].find('.') != -1:
                    result.append(node['properties']['qualified_name'])
                    count += 1
            origin_node['properties']['simrank'] = result
            print("save simrank result: " + str(result))
    graph_data.save(graph_data_save_path)
    print("构建完成")