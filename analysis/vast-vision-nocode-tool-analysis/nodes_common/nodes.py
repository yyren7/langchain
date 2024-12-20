from ryven.node_env import *
import sys
import os
sys.path.append(os.path.dirname(__file__))
import node_from_db
import create_dummy
import tempfile
import atexit

script_path = os.path.abspath(__file__)
parent_dir = os.path.dirname(os.path.dirname(script_path))
sys.path.insert(0, parent_dir)
from database_lib import redis_lib_client
from vastlib.utils import read_json

def remove_temp(path):
    if os.path.exists(path):  # if file is existing then delete it
        os.remove(path)

# TODO: db configuration is read by config file (not hard cording)
# config = read_json("config/config.json")
# DATABASE_URL = config["db_url"]
# controller = db_lib.db_controller(DATABASE_URL)
controller = redis_lib_client.db_controller()

dummy_path = create_dummy.create_dummy(controller)
# delete dummy file when program ends
atexit.register(remove_temp, path=dummy_path)

# source code for dynamic class from metadata
with open(node_from_db.__file__, 'r') as f:
    node_from_db_code = f.read()

# dummy code for dynamic class
with open(dummy_path, 'r') as f:
    dummy_code = f.read()

# dummy file path (debug)
#path = os.path.dirname(os.path.abspath(__file__)) + "\\temp.py"

# merge dynamic class file and dummy class file
#with open(path, 'w+') as fw:
with tempfile.NamedTemporaryFile(dir=os.path.dirname(__file__), suffix=".py", delete=False) as temp_file:
    temp_file_path = temp_file.name
    with open(temp_file_path, 'a+') as fw:
        fw.write(node_from_db_code)
        fw.write(dummy_code)
        fw.seek(0)

atexit.register(remove_temp, path=temp_file_path)

file_path = os.path.dirname(temp_file_path)
sys.path.append(file_path)

# import merged file
mdl = __import__(os.path.basename(temp_file_path[:-3]), fromlist=['*'])

# export custom nodes
export_nodes([
    *mdl.get_nodes()
])

