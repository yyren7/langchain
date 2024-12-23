
# vast-vision-nocode-tool-analysis

## nodes_common

### create_dummy.py

### content

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

### analysis

This Python code defines a function `create_dummy` that generates a temporary Python file containing class definitions. Let's break down its functionality step by step:

**1. Imports:**

   - `import tempfile`: This line imports the `tempfile` module, which is used for creating temporary files and directories.
   - `import os`: This line imports the `os` module, which provides functions for interacting with the operating system, such as getting the directory of a file.

**2. Function Definition:**

   - `def create_dummy(controller):`: This defines a function named `create_dummy` that takes one argument, `controller`. It's assumed that `controller` is an object that has a method called `get_table_names()`.

**3. Get Table Names and Filter Inputs:**

   - `nodenames = controller.get_table_names()`: This line calls the `get_table_names()` method of the `controller` object and stores the returned value (presumably a list of strings) in the `nodenames` variable.
   - `inputs_list = [item for item in nodenames if "inputs" in item.lower()]`: This line uses a list comprehension to create a new list called `inputs_list`. It iterates through each `item` in `nodenames` and includes it in `inputs_list` only if the lowercase version of the `item` contains the substring "inputs". This effectively filters the table names to keep only those that seem to be related to inputs.

**4. Create Temporary File:**

   - `with tempfile.NamedTemporaryFile(dir=os.path.dirname(__file__), suffix=".py", delete=False) as temp_file:`: This line creates a temporary file using `tempfile.NamedTemporaryFile`.
     - `dir=os.path.dirname(__file__)`: This specifies that the temporary file should be created in the same directory as the current Python file.
     - `suffix=".py"`: This sets the file extension of the temporary file to ".py", indicating that it's a Python file.
     - `delete=False`: This prevents the temporary file from being automatically deleted when the `with` block exits.
     - `as temp_file`: This assigns the file object to the variable `temp_file`.
   - `temp_file_path = temp_file.name`: This line gets the full path of the temporary file and stores it in the `temp_file_path` variable.

**5. Write Class Definitions to Temporary File:**

   - `for i_name in inputs_list:`: This loop iterates through each item in the `inputs_list`.
   - `source_code = f""" class {i_name}(NodeBase): pass """`: This line creates a string containing the source code for a Python class definition. The class name is dynamically generated using the current `i_name` from the loop. It's assumed that `NodeBase` is a base class that is available in the environment where this code is executed.
   - `with open(temp_file_path, 'a+') as f:`: This opens the temporary file in append mode (`'a+'`). This means that new content will be added to the end of the file, and the file will be created if it doesn't exist.
   - `f.write(source_code)`: This line writes the generated `source_code` to the temporary file.
   - `f.seek(0)`: This line moves the file pointer to the beginning of the file. This is not strictly necessary in this case, as the file is not read after writing.

**6. Return Temporary File Path:**

   - `return temp_file_path`: This line returns the path of the temporary file.

**In summary, the `create_dummy` function:**

1.  Takes a `controller` object as input.
2.  Extracts table names from the controller.
3.  Filters the table names to keep only those containing "inputs".
4.  Creates a temporary Python file.
5.  Writes class definitions (inheriting from `NodeBase`) into the temporary file, using the filtered table names as class names.
6.  Returns the path to the temporary file.

**Potential Use Case:**

This function seems designed to dynamically generate Python code based on some input data (table names from a controller). This could be used in a system where you need to create classes on the fly, perhaps for data processing or node-based programming. The generated classes are simple placeholders, inheriting from `NodeBase`, and likely intended to be further customized or extended in a later stage.

**Further Analysis:**

- The code assumes the existence of a `NodeBase` class. Without knowing more about this class, it's hard to fully understand the purpose of the generated classes.
- The `f.seek(0)` after writing to the file is not necessary in this context.
- The code does not handle potential errors, such as if `controller.get_table_names()` raises an exception.
- The temporary file is not deleted after use, which might lead to accumulation of temporary files if the function is called repeatedly.

In conclusion, this code provides a mechanism for dynamically generating Python class definitions based on input data. It's a useful tool for systems that require dynamic code generation, but it could be improved by adding error handling and temporary file cleanup.


### gui.py

### content

import re
from ryven.gui_env import *
#from special_nodes import *

from qtpy.QtGui import QFont
from qtpy.QtCore import Qt, Signal, QEvent
from qtpy.QtWidgets import QPushButton, QComboBox, QSlider, QTextEdit, QPlainTextEdit, QWidget, QVBoxLayout, QLineEdit, \
    QDialog, QMessageBox

# QLineEditのシンプルな入力GUI
class BasicInputWidget(NodeInputWidget, QLineEdit):
    def __init__(self, params):
        NodeInputWidget.__init__(self, params)
        QLineEdit.__init__(self)

        self.setMinimumWidth(60)
        self.setMaximumWidth(100)
        self.setStyleSheet("background-color:black;")

        ## loadしたとき毎回発火してしまう->silent=Trueで解決
        self.textChanged.connect(lambda: self.text_changed())
        self.init_value()

    def text_changed(self):
        self.update_node_input(Data(self.text()), silent=True)

    def get_state(self) -> dict:
        return {'value': self.text()}

    def set_state(self, data: dict):
        try:
            self.setText(data['value'])
        except:
            pass

    def val_update_event(self, val: Data):
        try:
            super().val_update_event(val)
            # 値を取得（画像のパス）
            data = val.payload
            self.setText(str(data))
        except:
            pass

    def init_value(self):
        # input the default value
        self.set_state({"value": self.input.default})
"""
    generic base classes
"""

# 入力部にQLineEditが付いたGUI
class BasicNodeGui(NodeGUI):
    input_widget_classes = {'input': BasicInputWidget}

    def add_input(self, name):
        self.init_input_widgets[len(self.init_input_widgets)] = {'name':'input', 'pos':'below'}

    def __init__(self, params):
        super().__init__(params)

        for inp in self.node.inputs:
            self.input_widgets[inp] = {'name': 'input', 'pos': 'besides'}


"""
    operator nodes
"""
## 以下はryvenにもともと載っていたサンプルコード（参考）
class GuiBase(NodeGUI):
    pass

class OperatorNodeBaseGui(GuiBase):
    input_widget_classes = {
        'in': inp_widgets.Builder.evaled_line_edit(size='s', resizing=True),
    }
    # init_input_widgets = {
    #     0: {'name': 'in', 'pos': 'besides'},
    #     1: {'name': 'in', 'pos': 'besides'},
    # }
    style = 'small'

    def __init__(self, params):
        super().__init__(params)
        self.actions['add input'] = {'method': self.add_operand_input}
        self.actions['remove input'] = {}

        for inp in self.node.inputs:
            self.input_widgets[inp] = {'name': 'in', 'pos': 'besides'}

    def initialized(self):
        super().initialized()
        self.rebuild_remove_actions()

    def add_operand_input(self):
        self.register_new_operand_input(self.node.num_inputs + 1)
        self.node.add_op_input()

    def register_new_operand_input(self, index):
        self.actions[f'remove input'][f'{index}'] = {
            'method': self.remove_operand_input,
            'data': index
        }

    def remove_operand_input(self, index):
        self.node.remove_op_input(index)
        self.rebuild_remove_actions()

    def rebuild_remove_actions(self):
        try:
            self.actions['remove input'] = {}
            for i in range(self.node.num_inputs):
                self.actions[f'remove input'][f'{i}'] = \
                    {'method': self.remove_operand_input, 'data': i}
        except Exception as e:
            print(e)



export_guis([
    # DualNodeBaseGui,
    #
    # CheckpointNodeGui,
    # OperatorNodeBaseGui,
    BasicNodeGui
    # LogicNodeBaseGui,
    # ArithNodeBaseGui,
    # CompNodeBaseGui,
    #
    # CSNodeBaseGui,
    # ForLoopGui,
    # ForEachLoopGui,
    #
    # SpecialNodeGuiBase,
    # ButtonNodeGui,
    # ClockNodeGui,
    # LogNodeGui,
    # SliderNodeGui,
    # DynamicPortsGui,
    # ExecNodeGui,
    # EvalNodeGui,
    # InterpreterConsoleGui,
    # StorageNodeGui,
    # LinkIN_NodeGui,
    # LinkOUT_NodeGui,
])



### analysis

Okay, let's break down this Python code. It appears to be defining custom GUI elements for a node-based visual programming environment, likely Ryven. Here's a structured analysis:

**Core Concepts**

*   **Ryven Integration:** The code heavily relies on Ryven's API (`ryven.gui_env.*`, `NodeInputWidget`, `NodeGUI`, `Data`). This indicates it's designed to extend Ryven's functionality with custom node appearances and behaviors.
*   **Qt for GUI:** It uses `qtpy` which is a compatibility layer for Qt bindings (PyQt or PySide). This means the GUI elements are built using Qt's framework.
*   **Node-Based Programming:** The code is creating visual representations (GUIs) for nodes in a node-based system. These nodes likely perform operations and pass data between each other.
*   **Custom Input Widgets:** The code defines custom input widgets (`BasicInputWidget`) that allow users to interact with node inputs.
*   **Node GUI Classes:** The code defines base classes for node GUIs (`BasicNodeGui`, `OperatorNodeBaseGui`) that can be extended for specific node types.

**Detailed Breakdown**

1.  **Imports:**
    *   `re`: Regular expression library (not used in the provided code).
    *   `ryven.gui_env`: Imports necessary classes from Ryven's GUI environment.
    *   `qtpy.QtGui`, `qtpy.QtCore`, `qtpy.QtWidgets`: Imports Qt classes for GUI elements.

2.  **`BasicInputWidget` Class:**
    *   **Inheritance:** Inherits from both `NodeInputWidget` (Ryven) and `QLineEdit` (Qt). This makes it a Ryven input widget that is also a Qt line edit box.
    *   **Initialization (`__init__`)**:
        *   Sets minimum and maximum width.
        *   Sets background color to black.
        *   Connects the `textChanged` signal to the `text_changed` method.
        *   Calls `init_value` to set the initial value.
    *   **`text_changed` Method:**
        *   Updates the node's input value using `update_node_input` when the text in the line edit changes. `silent=True` prevents infinite loops.
    *   **`get_state` Method:**
        *   Returns a dictionary containing the current text value, used for saving the state of the widget.
    *   **`set_state` Method:**
        *   Sets the text of the line edit from a dictionary, used for loading the state of the widget.
    *   **`val_update_event` Method:**
        *   Updates the text of the line edit when the node's input value is updated.
    *   **`init_value` Method:**
        *   Sets the initial value of the line edit from the node's default input value.

3.  **`BasicNodeGui` Class:**
    *   **Inheritance:** Inherits from `NodeGUI` (Ryven).
    *   **`input_widget_classes`:** Defines that the input widget for this node will be `BasicInputWidget`.
    *   **`add_input` Method:**
        *   Adds a new input to the node.
    *   **Initialization (`__init__`)**:
        *   Sets the input widgets to be displayed beside the node.

4.  **`GuiBase` Class:**
    *   A base class for other node GUIs.

5.  **`OperatorNodeBaseGui` Class:**
    *   **Inheritance:** Inherits from `GuiBase`.
    *   **`input_widget_classes`:** Defines that the input widget for this node will be an evaled line edit.
    *   **`style`:** Sets the style to 'small'.
    *   **Initialization (`__init__`)**:
        *   Adds actions for adding and removing inputs.
        *   Sets the input widgets to be displayed beside the node.
    *   **`initialized` Method:**
        *   Calls the parent's `initialized` method and rebuilds the remove actions.
    *   **`add_operand_input` Method:**
        *   Registers a new input and adds it to the node.
    *   **`register_new_operand_input` Method:**
        *   Registers a new remove action for the input.
    *   **`remove_operand_input` Method:**
        *   Removes an input from the node and rebuilds the remove actions.
    *   **`rebuild_remove_actions` Method:**
        *   Rebuilds the remove actions for the inputs.

6.  **`export_guis` Function:**
    *   Exports the defined GUI classes to Ryven, making them available for use with nodes.

**Key Insights**

*   **Customizable Node Inputs:** The code provides a way to create nodes with simple text input fields, which can be useful for various purposes (e.g., entering file paths, numbers, or strings).
*   **Dynamic Inputs:** The `OperatorNodeBaseGui` class demonstrates how to create nodes with a variable number of inputs, which is useful for operations that can take multiple operands.
*   **State Management:** The `get_state` and `set_state` methods in `BasicInputWidget` allow the GUI to save and load the state of the input widgets, which is important for saving and loading node graphs.
*   **Extensibility:** The code is designed to be extensible, allowing developers to create new node GUI classes with different input widgets and behaviors.
*   **Ryven Integration:** The code is tightly integrated with Ryven, using its API to create custom nodes and interact with the node graph.

**Potential Use Cases**

*   **Data Input Nodes:** Nodes that allow users to input data (e.g., numbers, strings, file paths).
*   **Parameter Nodes:** Nodes that allow users to configure parameters for other nodes.
*   **Operator Nodes:** Nodes that perform operations on multiple inputs.
*   **Custom Node Libraries:** The code can be used as a basis for creating custom node libraries with specific functionalities.

**Further Analysis**

To provide a more in-depth analysis, it would be helpful to know:

*   **The specific purpose of the Ryven project:** What kind of visual programming is being done?
*   **The types of nodes that will use these GUIs:** What kind of data will be passed through the nodes?
*   **The overall architecture of the Ryven project:** How do these nodes fit into the larger system?

**In summary, this code provides a foundation for creating custom node GUIs in Ryven, with a focus on simple text input and dynamic input management. It demonstrates good practices for integrating with Ryven and using Qt for GUI development.**


### nodes.py

### content

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



### analysis

Okay, I'll analyze this Python script. Here's a breakdown of what it does and some insights:

**Overall Purpose:**

The script dynamically generates and loads custom nodes for a visual programming environment (likely Ryven, based on `ryven.node_env`). It does this by:

1.  **Reading Node Definitions:** It fetches node definitions from a database (using `redis_lib_client`) and a dummy file.
2.  **Dynamically Creating Python Code:** It combines the code for a base node class (`node_from_db.py`) with the node definitions from the database and dummy file.
3.  **Creating a Temporary Python File:** It writes the combined code into a temporary Python file.
4.  **Importing the Temporary File:** It imports the temporary file as a module.
5.  **Exporting Nodes:** It extracts the node classes from the imported module and exports them using `export_nodes`.

**Detailed Breakdown:**

*   **Imports:**
    *   `ryven.node_env`: Likely provides the necessary functions for defining and exporting nodes in the Ryven environment.
    *   `sys`, `os`: Standard modules for system-level operations (path manipulation, etc.).
    *   `node_from_db`: A custom module that likely contains the base class for the dynamically generated nodes.
    *   `create_dummy`: A custom module that creates a dummy node definition file.
    *   `tempfile`: Used for creating temporary files.
    *   `atexit`: Used to register functions to be executed when the script exits (for cleanup).
    *   `database_lib.redis_lib_client`: A custom module for interacting with a Redis database.
    *   `vastlib.utils.read_json`: A custom function to read json files (commented out).

*   **Path Setup:**
    *   The script dynamically adds directories to the Python path to ensure that it can import the necessary modules.

*   **Database Interaction:**
    *   It initializes a database controller using `redis_lib_client.db_controller()`.
    *   It uses `create_dummy.create_dummy(controller)` to create a dummy node definition file, likely based on data from the database.

*   **Reading Code:**
    *   It reads the source code of `node_from_db.py` and the dummy node definition file.

*   **Temporary File Creation:**
    *   It creates a temporary Python file using `tempfile.NamedTemporaryFile`. This file will hold the combined code.
    *   It registers a cleanup function (`remove_temp`) to delete the temporary file when the script exits.

*   **Code Merging:**
    *   It writes the code from `node_from_db.py` and the dummy code into the temporary file.

*   **Importing the Temporary Module:**
    *   It adds the directory containing the temporary file to the Python path.
    *   It imports the temporary file as a module using `__import__`.

*   **Exporting Nodes:**
    *   It calls `mdl.get_nodes()` to get a list of node classes from the imported module.
    *   It exports these nodes using `export_nodes`.

**Insights and Potential Issues:**

*   **Dynamic Node Generation:** The core idea of dynamically generating nodes based on database content is powerful. It allows for a flexible and extensible node-based system.
*   **Temporary Files:** Using temporary files is a good practice for this kind of dynamic code generation. The `atexit` cleanup ensures that these files don't clutter the system.
*   **Dependency on Custom Modules:** The script relies heavily on custom modules (`node_from_db`, `create_dummy`, `database_lib`, `vastlib`). Understanding these modules is crucial for understanding the entire process.
*   **Hardcoded Database Configuration:** The commented-out code suggests that the database configuration was intended to be read from a JSON file. It's better to avoid hardcoding database URLs.
*   **Error Handling:** The script lacks explicit error handling. It would be beneficial to add `try...except` blocks to handle potential issues like file reading errors, database connection problems, or import errors.
*   **Security:** If the database content is user-provided, there might be security concerns. The script should sanitize or validate the data before using it to generate code.
*   **Debugging:** Debugging dynamically generated code can be challenging. It would be helpful to add logging or debugging statements to track the code generation process.
*   **Code Readability:** The script could be improved by adding more comments and using more descriptive variable names.

**Recommendations:**

*   **Implement Database Configuration from File:** Use the commented-out code to read the database configuration from a JSON file.
*   **Add Error Handling:** Implement `try...except` blocks to handle potential errors.
*   **Sanitize Database Input:** If the database content is user-provided, sanitize or validate it before using it to generate code.
*   **Add Logging:** Add logging statements to track the code generation process.
*   **Improve Code Readability:** Add more comments and use more descriptive variable names.

Let me know if you have any specific questions about the script or if you'd like me to elaborate on any of these points.


### node_from_db.py

### content

from ryven.node_env import *
import sys
import os
import time
from time import sleep
from copy import copy, deepcopy
from PySide2.QtCore import Signal, QObject, QThread
from database_lib import redis_lib_client
from functools import partial

script_path = os.path.abspath(__file__)
parent_dir = os.path.dirname(os.path.dirname(script_path))
sys.path.insert(0, parent_dir)

guis = import_guis(__file__)
globalcount = 0
class NodeBase(Node):
    color = '#00a6ff'

class BasicNode(NodeBase):
    version = 'v0.1'
    title = 'base'
    name = 'base'
    counter = 0
    message = {}
    _FUNC = None

    INSTANCES = []
    controller = None

    def __init__(self, params):
        super().__init__(params)
        self.activate = True
        global comm
        self.comm = comm
        self.message_recv_slot = partial(self.get_message, self)
        self.connect = False

    def __start(self):
        if not self.connect:
            self.comm.recv_signal.connect(self.message_recv_slot)
            self.connect = True

    def __stop(self):
        if self.connect:
            self.comm.recv_signal.disconnect(self.message_recv_slot)
            self.connect = False

    def have_gui(self):
        return hasattr(self, 'gui')

    def get_message(self, _self, _recv_message):
        recv_message = _recv_message

        try:
            obj_name, id_num = recv_message.split(":")
        except Exception as e:
            # if message format is not correct, continue recv
            return

        if "Errors" in obj_name:
            # check error message
            ret = self.check_err(obj_name, id_num, self.message)
            # if "module" and "id" in error message are matched, stop recv
            try:
                if ret:
                    self.gui.set_display_title(self.title + "(err)")
                    self.__stop()
                    # display log on headless gui
                    if self._FUNC is not None:
                        self._FUNC(self.name[:-6], "Error")
                    return
                else:
                    return
            except:
                pass


        # check name and id
        if (obj_name[:-7] == self.name[:-6] and int(id_num) == int(self.message["id"])):
            # if name and id is correct, stop recv
            self.__stop()
            pass
        else:
            return

        # get result record
        record_dict = self.controller.get_record_client(obj_name, id_num)
        # write recode to output ports
        for i, outp in enumerate(self.outputs):
            if outp.type_ == "exec":
                continue
            self.set_output_val(i, Data(record_dict[outp.label_str]))

        # exec flow
        try:
            self.gui.set_display_title(self.title)
        except:
            pass
        # display log on headless gui
        if self._FUNC is not None:
            self._FUNC(self.name[:-6], "Done")
        self.exec_output(0)



    # main function of nodes
    def update_event(self, inp_num=-1):
        # update only for exec flow
        if inp_num == 0:
            # reset input port color
            self.reset_color()
            # check id
            self.counter = self.controller.check_key(self.title + "Inputs", self.counter)
            # create message
            message = {"id": copy(self.counter)}
            self.counter += 1
            for i, inp in enumerate(self.inputs):
                if inp.type_ == "exec":
                    continue
                try:
                    if self.input(i).payload != "None":
                        message[inp.label_str] = self.input(i).payload
                except:
                    pass

            self.message = deepcopy(message)

            self.__stop()
            self.__start()

            res = self.controller.set_record_and_notify_client(self.title + "Inputs",
                                                               message,
                                                               "input",
                                                               message["id"]
            )
            try:
                self.gui.set_display_title(self.title + "<<<")
            except:
                pass

            if self._FUNC is not None:
                self._FUNC(self.name[:-6], "start")

    def check_err(self, obj_name, id_num, send_message):
        # get result record
        try:
            record_dict = self.controller.get_record_client(obj_name, id_num)
            if record_dict["input_id"] == send_message["id"] and self.title in record_dict["module"]:
                if obj_name == "FlowErrors":
                    for name in record_dict["message"]:
                        for num, input in enumerate(self.inputs):
                            if num == 0:
                                continue
                            if name == input.label_str:
                                self.gui.input_widget(num).setStyleSheet("background-color:red;")
                return True
            else:
                return False
        except:
            return False

    def reset_color(self):
        try:
            for i in range(len(self.gui.input_widgets)):
                if i == 0:
                    continue
                self.gui.input_widget(i).setStyleSheet("background-color:black;")
        except:
            pass


# matching xxinputs and xxoutputs
def extract_nodenames(names):
    inputs_list = [item for item in names if "inputs" in item.lower()]
    results_list = [item for item in names if "outputs" in item.lower()]

    mapping = {}
    for item in inputs_list:
        prefix = item[:-6]
        matching_result = [result for result in results_list if result.startswith(prefix)]
        if matching_result:
            mapping[item] = matching_result[0]

    return mapping

def get_nodes():
    controller = redis_lib_client.db_controller()
    nodenames = controller.get_table_names()
    io_pairs = extract_nodenames(nodenames)
    _nodes = []

    # create node class
    for i, (i_name, r_name) in enumerate(io_pairs.items()):
        i_columns = controller.get_columns(i_name)
        r_columns = controller.get_columns(r_name)

        cls = type(i_name, (BasicNode,), {})

        init_record = controller.get_record_client(table_name=i_name, record_id=0)

        cls.name = i_name
        cls.title = i_name[:-6]

        node_inputs = [NodeInputType(type_='exec')]
        node_outputs = [NodeOutputType(type_='exec')]

        for i, i_column in enumerate(i_columns):
            if i_column["name"] != "id" and i_column["name"] != "date":
                if type(init_record) == dict:
                        try:
                            node_inputs.append(NodeInputType(i_column["name"], default=str(init_record[i_column["name"]])))
                        except:
                            node_inputs.append(NodeInputType(i_column["name"]))
                else:
                    node_inputs.append(NodeInputType(i_column["name"]))
        for i, r_column in enumerate(r_columns):
            if r_column["name"] != "id" and r_column["name"] != "date":
                node_outputs.append(NodeOutputType(r_column["name"]))
        cls.init_inputs = node_inputs
        cls.init_outputs = node_outputs

        cls.num_inputs = len(i_columns)
        # cls.GUI = guis.OperatorNodeBaseGui
        cls.GUI = guis.BasicNodeGui

        # TODO:this inplementation may be bad.
        cls.controller = controller

        _nodes.append(cls)

    return _nodes

class Communicate(QObject):
    # カスタムシグナルの定義
    recv_signal = Signal(str)
    def __init__(self, controller):
        super().__init__()
        self.thread = listen_thread(controller)
        self.thread.message_signal.connect(lambda v: self._notification(v))

    def _start(self):
        self.thread.running = True
        self.thread.start()
        while not self.thread.isRunning():
            time.sleep(0.001)

    def _stop(self):
        self.thread.stop()
        self.thread.wait()

    def _notification(self, message):
        self.recv_signal.emit(message)

    def __del__(self):
        self._stop()

class listen_thread(QThread):
    message_signal = Signal(str)
    def __init__(self, controller):
        super().__init__()
        self.running = True
        self.controller = controller

    def run(self):
        while self.running:
            try:
                sleep(0.001)
                recv_message = self.controller._listen_message(channels=["output", "error"],
                                                              timeout=0
                                                              )
                if recv_message is not None:
                    self.message_signal.emit(recv_message)
                    continue
                else:
                    continue
            except:
                continue

        return

    def set_controller(self, controller):
        self.controller = controller

    def stop(self):
        self.running = False

controller = redis_lib_client.db_controller()
comm = Communicate(controller)
comm._start()

### analysis

Okay, I've analyzed the provided Python code. Here's a breakdown of its functionality and key aspects:

**Overall Purpose:**

The code defines a system for creating and managing nodes within a visual programming environment (likely Ryven, based on the import `from ryven.node_env import *`). These nodes interact with a Redis database to store and retrieve data, and they communicate with each other using a custom signal/slot mechanism. The system appears to be designed for data processing or workflow automation.

**Key Components:**

1.  **NodeBase and BasicNode:**
    *   `NodeBase`: A base class for all nodes, setting a default color.
    *   `BasicNode`: A core node class that inherits from `NodeBase`. It includes:
        *   `version`, `title`, `name`: Basic node properties.
        *   `counter`: A counter for generating unique IDs for messages.
        *   `message`: A dictionary to store data associated with the node's current operation.
        *   `INSTANCES`: A list to keep track of all instances of the node.
        *   `controller`: An instance of `redis_lib_client.db_controller` for database interaction.
        *   `__init__`: Initializes the node, sets up communication, and connects to the message receiving slot.
        *   `__start` and `__stop`: Methods to connect and disconnect the message receiving slot.
        *   `have_gui`: Checks if the node has a GUI.
        *   `get_message`: A slot that receives messages from the communication system, processes them, and updates the node's outputs.
        *   `update_event`: The main function that is triggered when an input is received. It prepares a message, sends it to the database, and triggers the output flow.
        *   `check_err`: Checks for error messages related to the node.
        *   `reset_color`: Resets the background color of the input widgets.

2.  **`extract_nodenames`:**
    *   A function that takes a list of names and extracts pairs of input and output table names based on the naming convention (e.g., "SomeNodeInputs" and "SomeNodeOutputs").

3.  **`get_nodes`:**
    *   A function that retrieves table names from the Redis database, extracts input/output pairs, and dynamically creates node classes based on the database schema.
    *   It uses `redis_lib_client.db_controller` to interact with the database.
    *   It dynamically creates node classes using `type()`.
    *   It sets up input and output ports based on the columns in the database tables.
    *   It assigns a GUI class (`guis.BasicNodeGui`) to each node.

4.  **`Communicate` and `listen_thread`:**
    *   `Communicate`: A class that manages communication between nodes using Qt signals and slots.
    *   `listen_thread`: A QThread that listens for messages from the Redis database and emits a signal when a message is received.
    *   This implements a separate thread for listening to messages from Redis, preventing the main thread from blocking.

5.  **Global Variables:**
    *   `controller`: An instance of `redis_lib_client.db_controller`.
    *   `comm`: An instance of `Communicate` for handling inter-node communication.

**Key Insights:**

*   **Dynamic Node Creation:** The system dynamically creates node classes based on the schema of the Redis database. This allows for a flexible and extensible system where new nodes can be added by simply creating new tables in the database.
*   **Redis as a Central Hub:** Redis is used as a central hub for storing data and facilitating communication between nodes. This allows for a decoupled architecture where nodes don't need to know about each other directly.
*   **Signal/Slot Communication:** The system uses Qt's signal/slot mechanism for inter-node communication. This is a robust and efficient way to handle asynchronous events.
*   **Error Handling:** The system includes basic error handling by checking for error messages in the Redis database and highlighting the corresponding input ports in the GUI.
*   **GUI Integration:** The code integrates with a GUI framework (likely Ryven) to provide a visual representation of the nodes and their connections.
*   **Asynchronous Operations:** The use of a separate thread for listening to Redis messages allows for asynchronous operations, preventing the main thread from blocking.

**Potential Improvements:**

*   **Error Handling:** The error handling could be improved by providing more detailed error messages and logging.
*   **Data Validation:** The system could benefit from data validation to ensure that the data being passed between nodes is in the correct format.
*   **Node Configuration:** The system could be made more configurable by allowing users to specify node properties and behavior through a configuration file or GUI.
*   **Scalability:** The system could be made more scalable by using a more efficient communication mechanism or by distributing the workload across multiple machines.
*   **Modularity:** The code could be made more modular by separating the node logic from the communication logic.

**In summary,** the code implements a dynamic node-based system for data processing or workflow automation, leveraging Redis for data storage and communication, and Qt's signal/slot mechanism for inter-node interaction. It's a well-structured system with potential for further development and improvement.


## nodes_common\calculation_nodes
