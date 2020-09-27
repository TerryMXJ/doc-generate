from sekg.graph.exporter.graph_data import GraphData, NodeInfo
from project.utils.path_util import PathUtil
import json

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
        sim_name_map[qualified_name] = qualified_name
        sim_name_map[simple_name] = qualified_name
    json_str = json.dumps(sim_name_map, indent=4)
    with open('../output/simple_qualified_name_map.json', 'w') as f:
        f.write(json_str)