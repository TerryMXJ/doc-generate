#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
-----------------------------------------
@Author: lvxiaoxiang
@Email: 1547554745@qq.com
@Created: 2020/09/15
------------------------------------------
@Modify: 2020/09/15
------------------------------------------
@Description:
"""
import json
from pathlib import Path

from sekg.graph.exporter.graph_data import GraphData
from sekg.ir.doc.wrapper import MultiFieldDocumentCollection, MultiFieldDocument

from definitions import DATA_DIR
from project.utils.path_util import PathUtil

'''
添加概念节点
'''

class Concept2Graph:

    def __init__(self, graph_data_path, dc_file_location, concepts_path, relations_path):
        self.graph: GraphData = GraphData.load(graph_data_path)
        self.doc_collection: MultiFieldDocumentCollection = MultiFieldDocumentCollection.load(dc_file_location)
        with open(concepts_path) as f:
            self.concepts_list = json.load(f)
        with open(relations_path) as f:
            self.relations_list = json.load(f)
        self.concept_2_node_id = {}

    def add_concept_2_graph(self):
        for item in self.concepts_list:
            node_labels = {"concept", "entity"}
            node_properties = {
                "qualified_name": item[0],
                "api_type": 0,
                "alias": item
            }
            node_id = self.graph.add_node(node_labels, node_properties, primary_property_name="qualified_name")
            self.concept_2_node_id[item[0]] = node_id
        print("concepts导入完成")

    def add_relation_2_graph(self):
        # 概念关系的添加
        for item in self.relations_list:
            if item["start"] in self.concepts_list and item["end"] in self.concepts_list:
                start_id = -1
                end_id = -1
                for start_concept in item["start"]:
                    if start_concept in self.concept_2_node_id:
                        start_id = self.concept_2_node_id[start_concept]
                        break
                    # start_node = self.graph.find_one_node_by_property("qualified_name", start_concept)
                    # if start_node:
                    #     start_id = start_node["id"]
                    #     break
                for end_concept in item["end"]:
                    if end_concept in self.concept_2_node_id:
                        end_id = self.concept_2_node_id[end_concept]
                        break
                    # end_node = self.graph.find_one_node_by_property("qualified_name", end_concept)
                    # if end_node:
                    #     end_id = end_node["id"]
                    #     break
                if start_id == -1 or end_id == -1:
                    print("-" * 50)
                    print("找不到node")
                    print("start id" + str(start_id))
                    print(item["start"])
                    print("end id" + str(end_id))
                    print(item["end"])
                    continue
                self.graph.add_relation(start_id, item["relation"], end_id)
        # 概念链接到graph的node上
        node_ids_list = self.graph.get_node_ids()
        for node_id in node_ids_list:
            node_doc: MultiFieldDocument = self.doc_collection.get_by_id(node_id)
            if node_doc:
                full_description = node_doc.get_doc_text_by_field('full_description')
                for concept_list_item in self.concepts_list:
                    concept_node_id = -1
                    for concept in concept_list_item:
                        if concept in self.concept_2_node_id:
                            concept_node_id = self.concept_2_node_id[concept]
                            break
                    if concept_node_id >= 0:
                        for concept in concept_list_item:
                            if concept in full_description:
                                self.graph.add_relation(node_id, "has concept", concept_node_id)
                                break
        print("relation添加完毕")


if __name__ == "__main__":
    concept_and_relation_path = Path(DATA_DIR) / "concept_and_relation"
    concept_2_graph = Concept2Graph(PathUtil.graph_data("jabref", "v1.8"),
                                    PathUtil.doc(pro_name="jabref", version='v1.2'),
                                    str(concept_and_relation_path / "concepts.json"),
                                    str(concept_and_relation_path / "relations.json"))
    concept_2_graph.add_concept_2_graph()
    concept_2_graph.add_relation_2_graph()
    concept_2_graph.graph.save(PathUtil.graph_data("jabref", "v1.9"))
    print("图导入完成")
