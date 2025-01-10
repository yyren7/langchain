import os
import ast
import json
import sys
import importlib
import importlib.metadata

def extract_ast_features_from_file(file_path, project_root):
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None

    features = {
        "file_path": file_path,
        "imports": [],
        "functions": []
    }

    imported_modules = {}

    # 提取全局的 import 信息
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules[alias.name] = alias.asname or alias.name
                features["imports"].append({
                    "import_name": alias.name,
                    "as_name": alias.asname or alias.name,
                    "source": classify_import_source(alias.name, project_root)
                })
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                full_import_name = f"{node.module}.{alias.name}"
                imported_modules[full_import_name] = alias.asname or alias.name
                features["imports"].append({
                    "import_name": full_import_name,
                    "as_name": alias.asname or alias.name,
                    "source": classify_import_source(node.module, project_root)
                })

    # 遍历每个函数定义
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            function_features = {
                "function_name": node.name,
                "used_functions": []
            }

            # 遍历函数体内的节点
            for func_node in ast.walk(node):
                if isinstance(func_node, ast.Call):
                    func_name = extract_function_name_from_node(func_node.func, imported_modules)
                    if func_name:
                        function_features["used_functions"].append(func_name)

            features["functions"].append(function_features)

    return features

def extract_function_name_from_node(node, imported_modules):
    func_name = ""
    if isinstance(node, ast.Name):
        func_name = node.id
    elif isinstance(node, ast.Attribute):
        if isinstance(node.value, ast.Name):
            module_name = node.value.id
            if module_name in imported_modules:
                func_name = f"{imported_modules[module_name]}.{node.attr}"
            else:
                func_name = f"{module_name}.{node.attr}"
        elif isinstance(node.value, ast.Call):
            func_name_prefix = extract_function_name_from_node(node.value, imported_modules)
            if func_name_prefix:
                func_name = f"{func_name_prefix}.{node.attr}"
    return func_name

def classify_import_source(module_name, project_root):
    if module_name in sys.builtin_module_names:
        return "内置模块"

    try:
        installed_packages = {pkg.metadata['Name'].lower() for pkg in importlib.metadata.distributions()}
        if module_name.lower() in installed_packages:
            return "第三方库"
    except Exception as e:
        print(f"Error checking installed packages: {e}")
        return "未知模块"

    local_path = os.path.join(project_root, module_name.replace('.', os.sep) + '.py')
    if os.path.exists(local_path):
        return f"本地文件: {local_path}"

    return "未知模块"

def traverse_directory_and_extract_features(directory):
    ast_features = []

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                features = extract_ast_features_from_file(file_path, directory)
                if features:
                    ast_features.append(features)

    return ast_features

def save_features_to_json(features, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(features, f, indent=4, ensure_ascii=False)


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
    project_directory = "../MvImport/"  # 替换为你的项目路径
    output_file = "ast_features.json"

    print(f"正在解析项目目录：{project_directory}")
    features = traverse_directory_and_extract_features(project_directory)
    print(f"解析完成，共提取 {len(features)} 个文件的AST特征。")

    save_features_to_json(features, output_file)
    print(f"AST特征已保存至：{output_file}")
    with open("ast_features.json", 'r', encoding="utf-8") as ast:  # 添加encoding
        ast_data = json.load(ast)
    ast_graph = build_dependency_graph(ast_data)

    draw_dependency_graph(ast_graph)
    generate_interactive_graph(ast_graph)
