import tempfile
import os

def create_dummy(controller):
    nodenames = controller.get_table_names()
    inputs_list = [item for item in nodenames if "inputs" in item.lower()]

    with tempfile.NamedTemporaryFile(dir=os.path.dirname(__file__), suffix=".py", delete=False) as temp_file:
        temp_file_path = temp_file.name
    # tempファイルに記述
        for i_name in inputs_list:
            source_code = f"""
class {i_name}(NodeBase):
    pass
                """
            with open(temp_file_path, 'a+') as f:
                f.write(source_code)
                f.seek(0)

    return temp_file_path