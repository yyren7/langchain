import json
import networkx as nx
import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader
from pyvis.network import Network


def build_dependency_graph(ast_features):
    """构建跨文件依赖图。"""
    graph = nx.DiGraph()

    for feature in ast_features:
        file_path = feature["file_path"]
        graph.add_node(file_path)

        for import_data in feature["imports"]:
            import_name = import_data["import_name"]
            from_name = import_data["from_name"]

            # 构建依赖边的名称，优先使用from_name
            dependency_name = from_name if from_name else import_name

            if dependency_name:  # 避免None值导致错误
                graph.add_edge(file_path, dependency_name)

    return graph


# ... (find_related_files, selective_retrieval_with_imports, print_dependency_graph 函数可以根据需要保留或删除，本次修改不涉及)

def draw_dependency_graph(graph, output_file="dependency_graph.png"):
    """绘制依赖图并保存为图像文件。"""
    plt.figure(figsize=(12, 8))
    nx.draw(graph, with_labels=True, node_size=2000, node_color="lightblue", font_size=10, font_weight="bold",
            arrowsize=20)
    plt.title("Cross-File Dependency Graph")
    plt.savefig(output_file)
    print(f"依赖图已保存为 {output_file}")
    plt.show()


def generate_interactive_graph(graph, output_file="dependency_graph.html"):
    net = Network(notebook=False, directed=True)

    for node in graph.nodes:
        net.add_node(node, label=node)

    for edge in graph.edges:
        net.add_edge(edge[0], edge[1])

    # 指定模板路径 (根据你的实际路径修改)
    template_path = "C:/Users/J100052060/PycharmProjects/pythonProject1/venv/lib/site-packages/pyvis/templates"  # 请修改此路径
    env = Environment(loader=FileSystemLoader(template_path))
    net.template = env.get_template("template.html")

    net.show(output_file)
    print(f"交互式依赖图已保存为 {output_file}")


if __name__ == "__main__":
    with open("ast_features.json", 'r', encoding="utf-8") as ast:  # 添加encoding
        ast_data = json.load(ast)
    ast_graph = build_dependency_graph(ast_data)

    draw_dependency_graph(ast_graph)
    generate_interactive_graph(ast_graph)