import functools

from sekg.constant.code import CodeEntityRelationCategory
from sekg.constant.constant import WikiDataConstance
from sekg.graph.exporter.graph_data import GraphData, NodeInfo
from sekg.ir.doc.wrapper import MultiFieldDocumentCollection, MultiFieldDocument
from script.classify_sentence import FastTextClassifier

from project.extractor_module.constant.constant import RelationNameConstant, FeatureConstant, DomainConstant, \
    FunctionalityConstant, SentenceConstant, CodeConstant
from project.utils.path_util import PathUtil
import re
import networkx as nx


class KnowledgeService:
    def __init__(self, doc_collection, graph_data_path=PathUtil.graph_data(pro_name="jabref", version="v3.10")):
        if isinstance(graph_data_path, GraphData):
            self.graph_data: GraphData = graph_data_path
        else:
            self.graph_data: GraphData = GraphData.load(graph_data_path)
        self.doc_collection = doc_collection
        self.functionClassifier = FastTextClassifier()
        self.G = nx.Graph(self.graph_data.graph)

    def get_api_characteristic(self, api_id):
        res_list = []
        res_list.extend(self.api_relation_search(api_id, RelationNameConstant.has_Feature_Relation))
        res_list.extend(self.api_relation_search(api_id, RelationNameConstant.has_Constraint_Relation))
        return self.parse_res_list(res_list)

    def get_api_category(self, api_id):
        res_list = []
        res_list.extend(self.api_relation_search(api_id, RelationNameConstant.Ontology_IS_A_Relation))
        res_list.extend(self.api_relation_search(api_id, RelationNameConstant.Ontology_Derive_Relation))
        res_list.extend(self.api_relation_search(api_id, RelationNameConstant.Ontology_Consist_Of_Relation))
        res_list.extend(self.api_relation_search(api_id, RelationNameConstant.Ontology_Parallel_Relation))
        return self.parse_res_list(res_list)

    @staticmethod
    def split_and_sort_directive(directive_list: list):
        new_directive_set = set()
        for item in directive_list:
            for sentence_item in item.split(". "):
                for atomic_directive in sentence_item.split(" || "):
                    new_directive_set.add(atomic_directive)
        new_directive_list = list(new_directive_set)
        new_directive_list.sort(key=lambda directive: len(directive))
        return new_directive_list

    def get_return_value_directive(self, api_id):
        out_relations = self.graph_data.get_all_out_relations(api_id)
        in_relations = self.graph_data.get_all_in_relations(api_id)
        all_relations = out_relations.union(in_relations)
        return_value_directive_id_set = set()
        for start, relation, end in all_relations:
            if relation == "has return code directive":
                return_value_directive_id_set.add(end if start == api_id else start)
        return_value_directive_list = [self.graph_data.get_node_info_dict(item)["properties"]["description"] for item in return_value_directive_id_set]
        return self.split_and_sort_directive(return_value_directive_list)

    def get_throws_directive(self, api_id):
        out_relations = self.graph_data.get_all_out_relations(api_id)
        in_relations = self.graph_data.get_all_in_relations(api_id)
        all_relations = out_relations.union(in_relations)
        throws_directive_id_set = set()
        for start, relation, end in all_relations:
            if relation == "has exception code directive":
                throws_directive_id_set.add(end if start == api_id else start)
        throws_directive_list = [self.graph_data.get_node_info_dict(item)["properties"]["short_description"] for item in throws_directive_id_set]
        return self.split_and_sort_directive(throws_directive_list)

    def get_api_methods(self, api_id, if_class=True):
        res_list = []
        if if_class:
            res_list.extend(self.api_by_relation_search(api_id, CodeEntityRelationCategory.category_code_to_str_map[
               CodeEntityRelationCategory.RELATION_CATEGORY_BELONG_TO]))
            method_list = self.parse_res_list(res_list)
        else:
            method_node = self.graph_data.get_node_info_dict(api_id)
            t = {
                "id": method_node["id"],
                "name": self.get_name_of_node_by_different_label(method_node)
            }
            if "properties" in method_node and 'full_description' in method_node["properties"]:
                t["full_description"] = method_node["properties"]["full_description"]
            method_list = [t]
        for m in method_list:
            m["declare"] = self.get_declare_from_method_name(m["name"])
            m["parameters"] = self.method_parameter(m["id"])
            m["return_value"] = self.method_return_value(m["id"])
            m["doc_info"] = self.get_method_doc_info(m["id"])
            m["exception_info"] = self.get_exception_info(m["id"])
            m["label"] = self.get_label_info(m["id"], "method")
            m["sample_code"] = self.get_one_sample_code(m["id"])
            m["concepts"] = self.get_concept(m["id"])
            m["return_value_directive"] = self.get_return_value_directive(m["id"])
            m["throws_directive"] = self.get_throws_directive(m["id"])
            fun_dir = self.classify_directive_and_functionality(m["id"])
            m["functionality"] = fun_dir["functionality_str"]
            m["directive"] = fun_dir["directive_str"]
            m["functionality_list"] = fun_dir["functionality_list"]
            m["directive_list"] = fun_dir["directive_list"]
        method_list.sort(key=lambda x: x['declare'])
        # 排除构造方法
        count = 0
        for m in method_list:
            if m['declare'][0] < 'a':
                count += 1
            else:
                break
        method_list = method_list[count:]
        return method_list

    def classify_directive_and_functionality(self, api_id):
        # directive 返回2， functionality 返回1
        directive_str = ""
        functionality_str = ""
        directive_str = []
        functionality_list = []
        comment = self.get_method_doc_info(api_id)["comment"]
        if comment.startswith("Generated by DeepLearning:"):
            comment = comment[comment.find(":")+1:]
        if comment is not "" or comment is not None:
            # 分句
            sentence_list = comment.split(". ")
            for i in range(len(sentence_list)):
                if sentence_list[i].find(".") == -1:
                    sentence_list[i] = sentence_list[i] + ". "
            # 句子分类
            directive_list = list()
            functionality_list = list()
            for i in sentence_list:
                if self.functionClassifier.predict(i) == 1:
                    functionality_list.append(i)
                else:
                    directive_list.append(i)
            # 构建functionality和directive句子
            functionality_str = ""
            directive_str = ""
            for i in directive_list:
                directive_str += i
            for i in functionality_list:
                functionality_str += i
        result = dict()
        result["directive_str"] = directive_str
        result["functionality_str"] = functionality_str
        result["directive_list"] = directive_list
        result["functionality_list"] = functionality_list
        return result

    def get_desc_from_api_id(self, api_id):
        doc: MultiFieldDocument = self.doc_collection.get_by_id(api_id)
        if doc is None:
            return ""
        full_description = doc.get_doc_text_by_field('full_description')
        if full_description == "":
            short_description = doc.get_doc_text_by_field('short_description')
            return short_description
        return full_description

    def get_method_doc_info(self, method_id):
        res = dict()
        doc: MultiFieldDocument = self.doc_collection.get_by_id(method_id)
        full_description = doc.get_doc_text_by_field('full_description')
        dp_comment = doc.get_doc_text_by_field('dp_comment')
        # 正则处理去掉多余字符
        dp_comment = re.sub(r"</?(.+?)>", "", dp_comment)
        dp_comment = dp_comment.lstrip().rstrip()
        if full_description != "" and full_description is not None:
            res['comment'] = full_description
        elif dp_comment != "" and dp_comment is not None:
            res['comment'] = 'Generated by DeepLearning: ' + dp_comment
        else:
            res['comment'] = ''
        return res

    def method_parameter(self, method_id):
        res_list = []
        res_list.extend(self.api_relation_search(method_id, CodeEntityRelationCategory.category_code_to_str_map[
            CodeEntityRelationCategory.RELATION_CATEGORY_HAS_PARAMETER]))
        for r in res_list:
            if r[1]['properties']['short_description'] == "":
                r[1]['properties']['short_description'] = self.get_desc_from_api_id(r[1]["id"])
            r[1]['properties']['description'] = r[1]['properties']['short_description']
            r[1]['labels'] = list(r[1]['labels'])
        return res_list

    def method_return_value(self, method_id):
        res_list = []
        res_list.extend(self.api_relation_search(method_id, CodeEntityRelationCategory.category_code_to_str_map[
            CodeEntityRelationCategory.RELATION_CATEGORY_HAS_RETURN_VALUE]))
        if len(res_list) > 0:
            r = res_list[0]
            if r[1]['properties']['description'] == "":
                r[1]['properties']['description'] = self.get_desc_from_api_id(r[1]["id"])
            r[1]["labels"] = list(r[1]["labels"])
            return res_list[0]
        return dict()

    def get_api_father_class(self, api_id):
        # API 的父类是什么
        res_list = []
        res_list.extend(self.api_relation_search(api_id, CodeEntityRelationCategory.category_code_to_str_map[
            CodeEntityRelationCategory.RELATION_CATEGORY_EXTENDS]))
        return self.parse_res_list(res_list)

    def get_api_implement_class(self, api_id):
        # API implements了哪些
        res_list = []
        res_list.extend(self.api_relation_search(api_id, CodeEntityRelationCategory.category_code_to_str_map[
            CodeEntityRelationCategory.RELATION_CATEGORY_IMPLEMENTS]))
        return self.parse_res_list(res_list)

    def get_api_terminologies(self, api_name):
        """
        API的术语
        :return []:
        """
        api_id = self.get_api_id_by_name(api_name)
        if api_id == -1:
            return []
        candidates = self.graph_data.get_relations(start_id=api_id, relation_type="has terminology",
                                                   end_id=None)
        node_list = []
        for (s, r, e) in candidates:
            end_node = self.graph_data.get_node_info_dict(e)
            node_list.append((end_node['properties']['terminology_name'], end_node['properties']["score"]))
        sorted(node_list, key=lambda x: x[1], reverse=True)
        return node_list

    def parse_res_list(self, res_list):
        parse_res = []
        for relation_type, node in res_list:
            t = {"id": node["id"], "relation": relation_type, "name": self.get_name_of_node_by_different_label(node)}
            if "properties" in node and 'full_description' in node["properties"]:
                t["full_description"] = node["properties"]["full_description"]
            parse_res.append(t)
        return parse_res

    def get_declare_from_method_name(self, method_name: str):
        if method_name is None or method_name == "":
            return ""
        font = method_name[0:method_name.find("(")]
        font = font.split(".")[-1]
        font += method_name[method_name.find("("):]
        return font

    def get_name_of_node_by_different_label(self, node):
        """
        根据node的label类型，返回它的名称
        :param node:
        :return:
        """
        labels = node["labels"]
        if FeatureConstant.LABEL in labels:
            return node["properties"][FeatureConstant.PRIMARY_PROPERTY_NAME]
        if DomainConstant.LABEL in labels:
            return node["properties"][DomainConstant.PRIMARY_PROPERTY_NAME]
        if FunctionalityConstant.LABEL in labels:
            return node["properties"][FunctionalityConstant.PRIMARY_PROPERTY_NAME]
        if WikiDataConstance.LABEL_WIKIDATA in labels:
            if 'labels_en' in node["properties"]:
                return node["properties"]['labels_en']
            return node["properties"][WikiDataConstance.NAME]
        if SentenceConstant.LABEL in labels:
            return node["properties"][SentenceConstant.PRIMARY_PROPERTY_NAME]
        else:
            if CodeConstant.QUALIFIED_NAME in node["properties"]:
                return node["properties"][CodeConstant.QUALIFIED_NAME]
            else:
                return ""

    def api_relation_search(self, api_id, relation_type):
        node_list = []
        candidates = self.graph_data.get_relations(start_id=api_id, relation_type=relation_type,
                                                   end_id=None)
        for (s, r, e) in candidates:
            end_node = self.graph_data.get_node_info_dict(e)
            node_list.append((r, end_node))
        return node_list

    def api_by_relation_search(self, api_id, relation_type):
        node_list = []
        candidates = self.graph_data.get_relations(start_id=None, relation_type=relation_type,
                                                   end_id=api_id)
        for (s, r, e) in candidates:
            start_node = self.graph_data.get_node_info_dict(s)
            node_list.append((r, start_node))
        return node_list

    def get_api_id_by_name(self, name):
        node = self.graph_data.find_one_node_by_property(property_name=GraphData.DEFAULT_KEY_PROPERTY_QUALIFIED_NAME,
                                                         property_value=name)
        if node is not None:
            api_id = node["id"]
        else:
            api_id = -1
        return api_id

    def get_knowledge(self, name):
        knowledge = dict()
        knowledge["message"] = ""
        api_id = self.get_api_id_by_name(name)
        if api_id == -1:
            knowledge["message"] = "can't find api by name"
            return knowledge
        # characteristic假接口
        if api_id == 1207:
            res = list()

            knowledge["characteristic"] = [{
                "name": "cloneable",
                "relation": ""
            }]
        else:
            knowledge["characteristic"] = self.get_api_characteristic(api_id)
        knowledge["category"] = self.get_api_category(api_id)
        return knowledge

    def api_contains_method(self, api_name):
        api_id = self.get_api_id_by_name(api_name)
        return self.get_api_methods(api_id)

    def api_father_class(self, api_id):
        res = dict()
        father_class_list = self.get_api_father_class(api_id)
        if len(father_class_list) > 0:
            return father_class_list[0]
        else:
            res = {"relation": CodeEntityRelationCategory.category_code_to_str_map[
                CodeEntityRelationCategory.RELATION_CATEGORY_EXTENDS], "name": "java.lang.Object"}
            return res

    def api_implement_class(self, api_id):
        get_api_implement_class_list = self.get_api_implement_class(api_id)

        return get_api_implement_class_list

    def api_field(self, api_id):
        res_list = []
        res_list.extend(self.api_relation_search(api_id, CodeEntityRelationCategory.category_code_to_str_map[
            CodeEntityRelationCategory.RELATION_CATEGORY_HAS_FIELD]))
        for r in res_list:
            r[1]['labels'] = list(r[1]['labels'])

        return res_list

    def get_concept(self, api_id):
        out_relations = self.graph_data.get_all_out_relations(api_id)
        concepts_list = []
        for item in out_relations:
            if item[1] == "has concept":
                concepts_list.append(self.graph_data.get_node_info_dict(item[2])["properties"]["qualified_name"])
        return concepts_list

    def api_base_structure(self, api_name):
        # 继承树
        api_id = self.get_api_id_by_name(api_name)
        print("searching class name: " + api_name)
        print("api id is " + str(api_id))
        res = dict()
        res["methods"] = self.get_api_methods(api_id)
        res["extends"] = self.api_father_class(api_id)
        res["implements"] = self.api_implement_class(api_id)
        res["fields"] = self.api_field(api_id)
        res["label"] = self.get_label_info(api_id, "class")
        res["concepts"] = self.get_concept(api_id)
        fun_dir = self.classify_directive_and_functionality(api_id)
        res["functionality"] = fun_dir["functionality_str"]
        res["directive"] = fun_dir["directive_str"]
        res["functionality_list"] = fun_dir["functionality_list"]
        res["directive_list"] = fun_dir["directive_list"]

        return res

    def get_api_methods_id(self, api_name):
        api_id = self.get_api_id_by_name(api_name)
        methods_list = []
        for i in self.graph_data.get_all_in_relations(api_id):
            if "belong to" == i[1]:
                methods_list.append(i[0])
        return methods_list

    # 返回类下面5个最关键方法
    def get_key_methods(self, api_name):
        method_id_list = self.get_api_methods_id(api_name)
        res_list = list()
        unsorted_list = list()
        for i in method_id_list:
            node: NodeInfo = self.graph_data.find_nodes_by_ids(i)[0]
            unsorted_list.append((node['properties']['qualified_name'], node['properties']['pr_value']))
        unsorted_list.sort(key=lambda x: x[1], reverse=True)
        count = 0
        for i in unsorted_list:
            if count > 4:
                break;
            temp = dict()
            temp['qualified_name'] = i[0]
            temp['sample_code'] = self.get_one_sample_code(api_id=self.get_api_id_by_name(i[0]))
            count += 1
            res_list.append(temp)
        return res_list


    # 返回该类的构造方法信息
    def get_constructor(self, api_name):
        api_id: int = self.get_api_id_by_name(name=api_name)
        res = dict()
        res_list = []
        res_list.extend(self.api_by_relation_search(api_id, CodeEntityRelationCategory.category_code_to_str_map[
            CodeEntityRelationCategory.RELATION_CATEGORY_BELONG_TO]))
        method_list = self.parse_res_list(res_list)
        for m in method_list:
            m["declare"] = self.get_declare_from_method_name(m["name"])
            m["parameters"] = self.method_parameter(m["id"])
            m["return_value"] = self.method_return_value(m["id"])
            m["doc_info"] = self.get_method_doc_info(m["id"])
        method_list.sort(key=lambda x: x['declare'])
        # 选取构造方法
        count = 0
        for m in method_list:
            if m['declare'][0] < 'a':
                count += 1
            else:
                break;
        constructor_list = method_list[:count]
        res['number_of_constructor'] = count
        res['constructor_detail'] = constructor_list
        return res

    # 返回该方法的exception信息
    def get_exception_info(self, api_id):
        exception_info = list()
        res_list: list = self.api_relation_search(api_id, "has exception condition")
        for res in res_list:
            info = dict()
            full_name: str = res[1]['properties']['qualified_name']
            exception_name = full_name[full_name.rfind(")")+2:]
            info['exception_name'] = exception_name
            info['description'] = res[1]['properties']['short_description']
            exception_info.append(info)
        return exception_info

    # 返回分类标签信息
    def get_label_info(self, api_id, class_or_method):
        node: NodeInfo = self.graph_data.find_nodes_by_ids(api_id)[0]
        method_label_list = ["accessor method", "mutator method", "creational method", "constructor", "undefined method"]
        class_label_list = ["entity class", "factory class", "util class", "pool class", "undefined class"]
        if class_or_method == "class" :
            label_list = class_label_list
        else:
            label_list = method_label_list
        for i in label_list:
            if i in node["labels"]:
                return i
        return "missing label"

    # 返回方法对应的单个sample_code
    def get_one_sample_code(self, api_id):
        doc: MultiFieldDocument = self.doc_collection.get_by_id(api_id)
        if doc is None:
            return "No sample code available."
        sample_code = doc.get_doc_text_by_field('sample_code')
        if len(sample_code) == 0 or sample_code is None:
            return "No sample code available."
        else:
            return sample_code[0][2:]

    # 返回相关api
    def get_related_api(self, qualified_name):
        result = dict()
        api_id = self.get_api_id_by_name(qualified_name)
        node: NodeInfo = self.graph_data.find_nodes_by_ids(api_id)[0]
        related_api = list()
        related_api_simplified = list()
        related_api = node['properties']['simrank']
        for i in related_api:
            related_api_simplified.append(i[i.rfind('.')+1:])
        result['related_api'] = related_api
        result['related_api_simplified'] = related_api_simplified
        return result


if __name__ == '__main__':
    pro_name = "jabref"
    data_dir = PathUtil.doc(pro_name=pro_name, version="v3.3")
    doc_collection: MultiFieldDocumentCollection = MultiFieldDocumentCollection.load(data_dir)

    knowledge_service = KnowledgeService(doc_collection)
    print(knowledge_service.get_related_api("org.jabref.model.entry.BibEntry"))
