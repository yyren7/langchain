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
        "used_functions": [],
        "imports": []
    }

    imported_modules = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules[alias.name] = alias.asname or alias.name
                features["imports"].append({
                    "import_name": alias.name,
                    "from_name": None,
                    "as_name": alias.asname,
                    "source": classify_import_source(alias.name, project_root)
                })
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported_modules[f"{node.module}.{alias.name}"] = alias.asname or alias.name
                features["imports"].append({
                    "import_name": alias.name,
                    "from_name": node.module,
                    "as_name": alias.asname,
                    "source": classify_import_source(node.module, project_root)
                })
        elif isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    module_name = node.func.value.id
                    if module_name in imported_modules:
                        func_name = f"{imported_modules[module_name]}.{node.func.attr}"
                    else:
                        func_name = f"{module_name}.{node.func.attr}"
                elif isinstance(node.func.value,ast.Call):
                    #处理a().b()的情况，递归调用
                    func_name_prefix=extract_function_name_from_node(node.func.value,imported_modules)
                    if func_name_prefix:
                        func_name = f"{func_name_prefix}.{node.func.attr}"
                else:
                    pass
            elif isinstance(node.func, ast.Subscript):
                #处理a[0]()的情况
                pass
            if func_name:
                features["used_functions"].append(func_name)

    return features
def extract_function_name_from_node(node,imported_modules):
    func_name = ""
    if isinstance(node, ast.Name):
        func_name = node.id
    elif isinstance(node, ast.Attribute):
        if isinstance(node.func.value, ast.Name):
            module_name = node.func.value.id
            if module_name in imported_modules:
                func_name = f"{imported_modules[module_name]}.{node.func.attr}"
            else:
                func_name = f"{module_name}.{node.func.attr}"
        elif isinstance(node.func.value,ast.Call):
            func_name_prefix=extract_function_name_from_node(node.func.value,imported_modules)
            if func_name_prefix:
                func_name = f"{func_name_prefix}.{node.func.attr}"
        else:
            pass
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

if __name__ == "__main__":
    project_directory = "Python"  # 替换为你的项目路径
    output_file = "ast_features.json"

    print(f"正在解析项目目录：{project_directory}")
    features = traverse_directory_and_extract_features(project_directory)
    print(f"解析完成，共提取 {len(features)} 个文件的AST特征。")

    save_features_to_json(features, output_file)
    print(f"AST特征已保存至：{output_file}")