from project.utils.path_util import PathUtil
from pathlib import Path
from sekg.graph.exporter.graph_data import GraphData, NodeInfo
from sekg.ir.doc.wrapper import MultiFieldDocument, MultiFieldDocumentCollection
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.cluster import KMeans
import definitions
import json


pro_name = "jabref"
graph_data_path = PathUtil.graph_data(pro_name=pro_name, version="v1.8")
doc_collection_path = PathUtil.doc(pro_name=pro_name, version="v1.2")
doc_collection_save_path = PathUtil.doc(pro_name=pro_name, version="v1.3")
api_to_example_json_path = Path(definitions.ROOT_DIR) / "output" / "json" / "api_2_example_sorted.json"
mid_to_method_info_json_path = Path(definitions.ROOT_DIR) / "output" / "json" / "mid_2_method_info_without_comment.json"

graph_data: GraphData = GraphData.load(graph_data_path)
doc_collection: MultiFieldDocumentCollection = MultiFieldDocumentCollection.load(doc_collection_path)

# 读取sample code文件. api_to_mid: 每个api对应的sample code的mid. methods_info: 每个mid对应的代码
with open(api_to_example_json_path, 'r') as f:
    api_to_mid = json.load(f)
f.close()
methods_info = list()
methods = open(mid_to_method_info_json_path, 'r').readlines()
for method in methods:
    methods_info.append(json.loads(method)['method'])


# 根据qualified name查找得到doc文件
def find_doc(qualified_name):
    node: NodeInfo = graph_data.find_one_node_by_property(property_name='qualified_name', property_value=qualified_name)
    if node is None:
        node: NodeInfo = graph_data.find_one_node_by_property_value_starts_with(property_name='qualified_name',
                                                                                property_value_starter=qualified_name)
    api_id = node['id']
    doc: MultiFieldDocument = doc_collection.get_by_id(api_id)
    return doc


# 返回api对应的语料
def get_corpus(qualified_name):
    corpus = list()
    nums = api_to_mid[qualified_name]
    for num in nums:
        method: str = methods_info[num-1]
        if method.count("\n") >= 8:
            corpus.append(method)
    if len(nums) <= 5 or len(corpus) <= 5:
        return None
    return corpus


# 将语料转化为词向量
def corpus_to_vector(corpus):
    # 转化为词频矩阵
    vectorizer = CountVectorizer()
    X = vectorizer.fit_transform(corpus)
    word = vectorizer.get_feature_names()
    # 转化为TF-IDF矩阵
    transformer = TfidfTransformer()
    tfidf = transformer.fit_transform(X)
    return tfidf


# 返回相应cluster的样例代码
def find_one_cluster_example(corpus, result, index):
    for i in range(len(result)):
        if result[i] == index:
            return corpus[i]
    return ""


# k-means得到5个cluster
def get_cluster_result(X, corpus):
    km = KMeans(5, init="k-means++", max_iter=300, n_init=1, verbose=False)
    km.fit(X)
    result = list(km.predict(X))
    sample_code = list()
    for i in range(5):
        sample_code.append(find_one_cluster_example(corpus, result, i))
    return sample_code


if __name__ == '__main__':
    for qualified_name in iter(api_to_mid):
        print("process {}".format(qualified_name))
        doc = find_doc(qualified_name)
        corpus = get_corpus(qualified_name)
        if corpus is not None:
            vector = corpus_to_vector(corpus)
            result = get_cluster_result(vector, corpus)
            print("clustering...")
            doc.add_field(field_name="sample_code_cluster", field_document=result)
        else:
            print("None...")
            doc.add_field(field_name="sample_code_cluster", field_document=None)
        doc_collection.save(doc_collection_save_path)

