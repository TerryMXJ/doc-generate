from sekg.graph.exporter.graph_data import GraphData, NodeInfo
from project.utils.path_util import PathUtil

pro_name = 'jabref'
graph_data_path = PathUtil.graph_data(pro_name=pro_name, version="v3.10")
graph_data: GraphData = GraphData.load(graph_data_path)

if __name__ == '__main__':
    sim_name_map = dict()
    for i in range(1, 48545):
        node: NodeInfo = graph_data.find_nodes_by_ids(i)[0]
        if "qualified_name" not in node["properties"] or "class" not in node["labels"] or node["properties"]["qualified_name"].find(".") == -1:
            continue;
        qualified_name = node["properties"]["qualified_name"]
        simple_name = qualified_name[qualified_name.rfind('.')+1:]
        if simple_name == "BibEntry":
            print(qualified_name)
        sim_name_map[qualified_name] = qualified_name
        sim_name_map[simple_name] = qualified_name
    print("BibEntry" in sim_name_map)
    print(sim_name_map["BibEntry"])
    with open('../output/simple_name_map.txt', 'w') as f:
        f.write(str(sim_name_map))