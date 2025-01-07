import os
import ast
import json

# 功能：解析整个项目目录中的代码文件，并提取AST特征
def extract_ast_features_from_file(file_path):
    """
    解析单个Python文件的AST并提取特征。
    :param file_path: Python文件路径
    :return: 文件的AST特征字典
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None  # 跳过语法错误文件

    features = {
        "file_path": file_path,
        "classes": {},
        "functions": [],
        "imports": []
    }

    for node in ast.walk(tree):
        # 类定义
        if isinstance(node, ast.ClassDef):
            features["classes"][node.name] = {
                "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
            }
        # 函数定义
        elif isinstance(node, ast.FunctionDef):
            features["functions"].append(node.name)
        # 导入语句
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                features["imports"].append(alias.name)

    return features


def traverse_directory_and_extract_features(directory):
    """
    遍历项目目录并提取所有代码文件的AST特征。
    :param directory: 项目目录路径
    :return: 所有文件的AST特征列表
    """
    ast_features = []

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                features = extract_ast_features_from_file(file_path)
                if features:
                    ast_features.append(features)

    return ast_features


def save_features_to_json(features, output_path):
    """
    将提取的AST特征保存为JSON文件。
    :param features: AST特征列表
    :param output_path: JSON文件路径
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(features, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    # 设置项目路径和输出路径
    project_directory = "app\\lib"  # 替换为你的项目路径
    output_file = "ast_features.json"

    # 提取AST特征
    print(f"正在解析项目目录：{project_directory}")
    features = traverse_directory_and_extract_features(project_directory)
    print(f"解析完成，共提取 {len(features)} 个文件的AST特征。")

    # 保存特征到JSON文件
    save_features_to_json(features, output_file)
    print(f"AST特征已保存至：{output_file}")
