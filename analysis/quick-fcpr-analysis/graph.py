import json

import networkx as nx


def build_dependency_graph(ast_features):
    """
    构建跨文件依赖图。
    :param ast_features: 所有文件的AST特征列表
    :return: 依赖图（NetworkX图）
    """
    graph = nx.DiGraph()

    for feature in ast_features:
        file_path = feature["file_path"]
        graph.add_node(file_path)

        for import_path in feature["imports"]:
            if import_path:
                graph.add_edge(file_path, import_path)

    return graph


def find_related_files(graph, file_path):
    """
    查找与给定文件相关的所有依赖文件。
    :param graph: 依赖图
    :param file_path: 文件路径
    :return: 相关文件列表
    """
    return list(nx.dfs_postorder_nodes(graph, file_path))


def selective_retrieval_with_imports(file_path, graph, retriever, top_k=5):
    """
    基于import依赖关系的选择性检索策略。
    :param file_path: 当前文件路径
    :param graph: 依赖图
    :param retriever: 检索器
    :param top_k: 检索的文件数量
    :return: 检索到的相关上下文
    """
    related_files = find_related_files(graph, file_path)

    # 检索相关文件的代码内容
    context = []
    for related_file in related_files[:top_k]:
        with open(related_file, 'r', encoding='utf-8') as f:
            context.append(f.read())

    return "\n".join(context)

def print_dependency_graph(graph):
    """
    打印依赖图的文本格式。
    :param graph: NetworkX DiGraph
    """
    for node in graph.nodes:
        dependencies = list(graph.successors(node))
        if dependencies:
            print(f"{node} 导入了:")
            for dep in dependencies:
                print(f"  - {dep}")
        else:
            print(f"{node} 没有导入其他文件。")

import matplotlib.pyplot as plt
def draw_dependency_graph(graph, output_file="dependency_graph.png"):
    """
    绘制依赖图并保存为图像文件。
    :param graph: NetworkX DiGraph
    :param output_file: 输出图像文件路径
    """
    plt.figure(figsize=(12, 8))
    nx.draw(graph, with_labels=True, node_size=2000, node_color="lightblue", font_size=10, font_weight="bold", arrowsize=20)
    plt.title("Cross-File Dependency Graph")
    plt.savefig(output_file)
    print(f"依赖图已保存为 {output_file}")
    plt.show()


from jinja2 import Environment, FileSystemLoader
from pyvis.network import Network

# 手动设置模板路径
def generate_interactive_graph(graph, output_file="dependency_graph.html"):
    net = Network(notebook=False, directed=True)

    for node in graph.nodes:
        net.add_node(node, label=node)

    for edge in graph.edges:
        net.add_edge(edge[0], edge[1])

    # 指定模板路径
    template_path = "C:/Users/J100052060/PycharmProjects/pythonProject1/venv/lib/site-packages/pyvis/templates"
    env = Environment(loader=FileSystemLoader(template_path))
    net.template = env.get_template("template.html")

    net.show(output_file)
    print(f"交互式依赖图已保存为 {output_file}")

with open("ast_features.json", 'r') as ast:
    ast_data=json.load(ast)
ast_graph=build_dependency_graph(ast_data)

print(draw_dependency_graph(ast_graph))

print(generate_interactive_graph(ast_graph))