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
        graph.add_node(file_path, label=file_path, group="file")

        # 添加全局的 import 信息
        for import_data in feature["imports"]:
            import_name = import_data["import_name"]
            graph.add_node(import_name, label=import_name, group="import")
            graph.add_edge(file_path, import_name)

        # 添加函数信息
        for func in feature["functions"]:
            func_name = f"{file_path}:{func['function_name']}"
            graph.add_node(func_name, label=func['function_name'], group="function")
            graph.add_edge(file_path, func_name)

            # 添加函数调用的其他函数
            for used_func in func["used_functions"]:
                graph.add_node(used_func, label=used_func, group="function_call")
                graph.add_edge(func_name, used_func)

    return graph

def draw_dependency_graph(graph, output_file="dependency_graph.png"):
    """绘制依赖图并保存为图像文件。"""
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(graph)
    nx.draw(graph, pos, with_labels=True, node_size=2000, node_color="lightblue", font_size=10, font_weight="bold", arrowsize=20)
    plt.title("Cross-File Dependency Graph")
    plt.savefig(output_file)
    print(f"依赖图已保存为 {output_file}")
    plt.show()

def generate_interactive_graph(graph, output_file="dependency_graph.html"):
    """生成交互式依赖图并保存为 HTML 文件。"""
    net = Network(notebook=False, directed=True, height="750px", width="100%", bgcolor="#222222", font_color="white")

    # 添加节点和边
    for node in graph.nodes:
        group = graph.nodes[node].get("group", "default")
        label = graph.nodes[node].get("label", node)
        net.add_node(node, label=label, group=group)

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