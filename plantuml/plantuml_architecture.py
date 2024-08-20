import inspect
import ast
import tokenize
import io
from pprint import pprint
import plantuml.plantuml_types as pt
import inspect

def print_with_indent(text, indent):
    print('    ' * indent + text)
    
def print_call_stack():
    # Get the current stack frames
    stack = inspect.stack()
    print("Call stack:")
    for frame in stack:
        print(f"File '{frame.filename}', line {frame.lineno}, in {frame.function}")

def print_plant_component(name, plantuml_obj, indent=0):
    path = plantuml_obj.path
    color = ""
    if "color" in plantuml_obj.metadata_dict:
        color = "#"+plantuml_obj.metadata_dict["color"]
    extra = ""
    if isinstance(plantuml_obj, pt.PlantumlActor):
        if plantuml_obj.has_sub_objs():
            print_with_indent(f"rectangle  \"{name}\" <<actor>> as {path} $comp_{path} {color} {{", indent)
            indent += 1
        else:
            print_with_indent(f"actor \"{name}\" as {path} ${path} {color}", indent)
    elif isinstance(plantuml_obj, pt.PlantumlGroup):
        if plantuml_obj.has_sub_objs():
            print_with_indent(f"{plantuml_obj.type} {{", indent)
    elif isinstance(plantuml_obj, pt.PlantumlComponent) or \
            isinstance(plantuml_obj, pt.PlantumlFrame) or \
            isinstance(plantuml_obj, pt.PlantumlFolder) or \
            isinstance(plantuml_obj, pt.PlantumlDatabase) or \
            isinstance(plantuml_obj, pt.PlantumlPackage):
        if plantuml_obj.has_sub_objs():
            extra = "{"
        print_with_indent(f"{plantuml_obj.type} \"{name}\" as {path} ${path} {color}{extra}", indent)
    elif isinstance(plantuml_obj, pt.PlantumlInterface):
        print_with_indent(f"interface \"{name}\" as {path} ${path} {color}", indent)
    elif isinstance(plantuml_obj, pt.PlantumlPort):
        print_with_indent(f"port \"{name}\" as {path} ${path} {color}", indent)
    elif isinstance(plantuml_obj, pt.PlantumlActivity):
        print_with_indent(f"agent \"{name}\" as {path} ${path} {color}", indent)


def create_plant_comonnection(name, plantuml_obj, indent=0):
    color = ""
    if "color" in plantuml_obj.metadata_dict:
        color = "#"+plantuml_obj.metadata_dict["color"]
    
    line = "-[norank]-"
    if "line" in plantuml_obj.metadata_dict:
        line = plantuml_obj.metadata_dict["line"]
    elif plantuml_obj.metadata_dict["direction"] == "out":
        line = "-[norank]->"
    elif plantuml_obj.metadata_dict["direction"] == "in":
        line = "<-[norank]-"

    conn_str = ""
    if isinstance(plantuml_obj.comp1, list):
        path2 = plantuml_obj.comp2.ref.path
        for item in plantuml_obj.comp1:
            path1 = item.ref.path
            conn_str += f"{path1} {line} {path2} {color} : {name}\n"
        
    elif isinstance(plantuml_obj.comp2, list):
        path1 = plantuml_obj.comp1.ref.path
        for item in plantuml_obj.comp2:
            path2 = item.ref.path
            conn_str += f"{path1} {line} {path2} {color} : {name}\n"
        # path2 = plantuml_obj.comp2.ref.path
        # return {name:f"{path1} {line} {path2} {color} : {name}"}
    else:
        path1 = plantuml_obj.comp1.ref.path
        path2 = plantuml_obj.comp2.ref.path
        conn_str = f"{path1} {line} {path2} {color} : {name}"
    return {name:conn_str}


# Function to recursively pretty-print the AST
def pretty_print_ast(node, level=2):
    indent="  "
        
    if isinstance(node, list):
        for item in node:
            pretty_print_ast(item, level)
    elif isinstance(node, ast.AST):
        print(f"1) {indent * level}{node.__class__.__name__}(")
       
        for field, value in ast.iter_fields(node):
            print(f"2) {indent * (level + 1)}{field}=")
            pretty_print_ast(value, level+1)
        print(f"{indent * level})")
    else:
        print(f"3) {indent * level}{repr(node)},")

def is_primitive(value):
    return isinstance(value, (int, float, str, bool))

def is_container(obj):
    """Check if the object is a container type."""
    return isinstance(obj, (dict, list, tuple, set)) or hasattr(obj, '__dict__')

def introspect_object(obj, depth=1):
    def introspect(obj, indent):
        for name, value in inspect.getmembers(obj):
            if not inspect.isroutine(value) and not name.startswith('__'):
                print_with_indent(f"{name}: {value}", indent)
                if is_container(value) and not isinstance(value, pt.PlantumlConnection):
                    introspect(value, indent+1)

    print_with_indent(f"Object of type: {type(obj).__name__}", depth)
    introspect(obj, depth)

def join_path(path, name):
    if path == "":
        return name
    else:
        return path+"_"+name

def do_plantuml_architecture(plantuml_arch, **kwargs):
    """
    This function creates a simple plantuml output representation of the architecture.
    if an element has no name, then the variable name will be automaticaly applied as name.
    Argumnets:
        plantuml_arch -- A class of a PlantumlType type.
        kwargs -- Optional key/value arguments.
    """
    def introspect(obj, connections, indent):
        path = ""
        
        # First add the layout_connectors to the connections dictionary
        if isinstance(obj, pt.PlantumlArchitecture) and "layout_connectors" in obj.metadata_dict:
            for value in obj.metadata_dict["layout_connectors"]:
                str = f"{value[0].ref.path} {value[1]} {value[2].ref.path}"
                connections.update({str:str})
        for name, value in inspect.getmembers(obj):
            if not inspect.isroutine(value) and not name.startswith('__'):
                if isinstance(value, pt.PlantumlType):
                    path = value.path
                    if isinstance(value, pt.PlantumlConnection):
                        if value.metadata_dict['hide'] == False and value.metadata_dict['remove'] == False:
                            # Add this connection to the connections dictionary
                            connections.update(create_plant_comonnection(value.name, value, indent))
                    else:
                        print_plant_component(value.name, value, indent)

                if isinstance(value, pt.PlantumlType) and not isinstance(value, pt.PlantumlConnection):# and is_container(value):
                    introspect(value, connections, indent+1)
                if isinstance(value, pt.PlantumlComponent) or\
                    isinstance(value, pt.PlantumlGroup) or \
                    isinstance(value, pt.PlantumlActor) or \
                    isinstance(value, pt.PlantumlFrame) or \
                    isinstance(value, pt.PlantumlFolder) or \
                    isinstance(value, pt.PlantumlDatabase) or \
                    isinstance(value, pt.PlantumlPackage):
                    if value.has_sub_objs():
                        print_with_indent("}", indent)
                if isinstance(value, pt.PlantumlType) and not isinstance(value, pt.PlantumlConnection) and value.metadata_dict['hide'] == True:
                    print_with_indent(f"hide ${path}", indent)
                if isinstance(value, pt.PlantumlType) and not isinstance(value, pt.PlantumlConnection) and value.metadata_dict['remove'] == True:
                    print_with_indent(f"remove ${path}", indent)
                if isinstance(value, pt.PlantumlType) and "note" in value.metadata_dict:
                    
                    note_path = path+"_note"
                    # Add this note with its connection to the connections dictionary
                    connections.update({note_path: f"note \"{value.metadata_dict['note']}\" as {note_path}\n{note_path} ~ {path}"})


    connections = {} # Use dictionary to avoid duplications
    print("@startuml")
    if "orientation" in plantuml_arch.metadata_dict:
        print(plantuml_arch.metadata_dict["orientation"])
    if "skinparam" in plantuml_arch.metadata_dict:
        print(plantuml_arch.metadata_dict["skinparam"])
    introspect(plantuml_arch, connections, 0)
    
    # print all connections only in the end.
    for value in connections.values():
        print(value)

    
    print("@enduml")
