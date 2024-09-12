import inspect
import ast
import tokenize
import io
from pprint import pprint
import plantuml.plantuml_types as pt
import inspect
from collections.abc import Container

"""
@startuml
skinparam roundCorner 10
skinparam class {
BorderColor #7A694B
backGroundColor #FCFDF8/EBE5D7
}
sprite foo1 <svg viewBox="0 0 16 16">
<path fill="#801714" d="M 2 2 H 13 V 15 H 1Z"/>
<path fill="#EEDCDA" d="M 3 3 H 12 V 8 H 3Z M 3 9 H 12 V 11 H 3Z M 3 12 H 12 V 14 H 3Z"/>
</svg>
class C1 <<$foo1 >>
class C2 <<$foo1 >> #red-green
@enduml
"""

EXCLUDE_LIST = ['_abc_impl', "object", "ABC"]

def print_with_indent(text, indent):
    print('    ' * indent + text)

def get_classes(class_object):

    classes_set = set()
    
    if not isinstance(class_object, (int, float, str, bool, type(None), Container)):
        # classes_set.add(type(class_object))
        for value in inspect.getmro(type(class_object)):
            if value.__name__ in EXCLUDE_LIST:
                continue
            classes_set.add(value)
            # print(f' value: {value.__name__}')

    return classes_set

def get_inheritance(class_type):

    inheritance_set = set()
    def recurrent(obj_type):
        # print(f'          {obj_type}')

        # classes_set.add(type(obj))
        for value in obj_type.__bases__:
            if value.__name__ in EXCLUDE_LIST:
                continue
            # print(f'  {value.__name__} <|-up- {obj_type.__name__}')
            inheritance_set.add(f'  {obj_type.__name__} -up-|> {value.__name__}')
            recurrent(value)
    
    # print(f'        class_type = {class_type}')
    # print(f'        class_type.__name__ = {class_type.__name__}')
    recurrent(class_type)
    
    return inheritance_set


def print_class(class_item):
    """
    Print a single class definition
    """
    print(f'  class {class_item} <<$deco>>') 

def print_interface(interface_item):
    """
    Print a single interface definition
    """
    print(f'  interface {interface_item} <<($deco) interface>>') 

def print_attrs_with_class(class_type):
    """
    return a dictionary of class.attribue and if this is an interface
    """
    attr_dict = {}
    # print (f'\'print_attrs_with_class {class_type.__name__}, {class_type}')
    if not isinstance(class_type, (int, float, str, bool, type(None), Container)):

        # Get all instance methods (exclude static methods)
        for name, member in inspect.getmembers(class_type):
            if not name.endswith('__') and not name in EXCLUDE_LIST:
                # print(f'\' class {name}')
                key=f'{class_type.__name__}.{name}'
                
                vis_name = name # Visibility name
                prefix = f'_{class_type.__name__}__' # name mangling
                if name.startswith(prefix):
                    vis_name = '-' + name.removeprefix(prefix) # de-mangling
                elif name.startswith('_'):
                    vis_name = '#' + name.removeprefix('_')

                if inspect.isfunction(member):
                    abs = ""
                    if getattr(member, "__isabstractmethod__", False):
                        abs = " {abstract}"
                    attr_dict[key] = f' {class_type.__name__} : {{static}}{abs} {vis_name}()'

                else:
                    attr_dict[key] = f' {class_type.__name__} : {{static}}  {vis_name}: {type(member).__name__}'
    is_interface = True
    for key, attr in attr_dict.items():
        if not "{abstract}" in attr: # If one not abstract
            is_interface = False
            break
    return attr_dict, is_interface

def print_attrs_with_instance(class_name, class_object):
    """
    The main diff between class and object here is that class has no values
    """
    attr_dict = {}
    # print (f'\'print_attrs_with_instance {class_name}, {class_object}, {type(class_object).__name__}')
    if not isinstance(class_object, (int, float, str, bool, type(None), Container)):

        # Get all instance methods (exclude static methods)
        for name, member in inspect.getmembers(class_object):
            if not name.endswith('__') and not name in EXCLUDE_LIST:
                key=f'{class_object.__class__.__name__}.{name}'

                vis_name = name # Visibility name
                prefix = f'_{type(class_object).__name__}__' # name mangling
                if name.startswith(prefix):
                    vis_name = '-' + name.removeprefix(prefix) # de-mangling
                elif name.startswith('_'):
                    vis_name = '#' + name.removeprefix('_')

                if inspect.ismethod(member):
                    abs = ""
                    if getattr(member, "__isabstractmethod__", False):
                        abs = " {abstract}"
                    attr_dict[key] = f' {type(class_object).__name__} :{abs} {vis_name}()'
                elif inspect.isfunction(member):
                    abs = ""
                    if getattr(member, "__isabstractmethod__", False):
                        abs = " {abstract}"
                    attr_dict[key] = f' {type(class_object).__name__} : {{static}}{abs} {vis_name}()'
                elif not inspect.isroutine(member) and not name in class_object.__dict__:
                    attr_dict[key] = f' {type(class_object).__name__} : {{static}}  {vis_name}: {type(member).__name__}'
                else:
                    attr_dict[key] = f' {type(class_object).__name__} : {vis_name}: {type(member).__name__}'
    return attr_dict

def get_associated_classes(class_object, association_classes_set):
    # Get all instance methods (exclude static methods)
    for name, member in inspect.getmembers(class_object):
        if not isinstance(member, (int, float, str, bool, type(None), Container)) and not name.endswith('__') and not name in EXCLUDE_LIST and not inspect.isroutine(member):
            association_classes_set.add(type(member))
            get_associated_classes(member, association_classes_set)
        
def get_associations(class_object, association_classes_set):

    for name, member in inspect.getmembers(class_object):
        if not isinstance(member, (int, float, str, bool, type(None), Container)) and not name.endswith('__') and not name in EXCLUDE_LIST and not inspect.isroutine(member):
        
            vis_name = name # Visibility name
            prefix = f'_{class_object.__class__.__name__}__' # name mangling
            if name.startswith(prefix):
                vis_name = name.removeprefix(prefix) # de-mangling
            elif name.startswith('_'):
                vis_name = name.removeprefix('_')
        
            association_classes_set.add(f'{class_object.__class__.__name__} -right-> {member.__class__.__name__} : {vis_name}')
            get_associations(member, association_classes_set)
        
        
def print_object_values(obj_name, object):
    """
    The main diff between class and object here is that class has no values
    """
    attr_dict = {}
    for name, value in inspect.getmembers(object):
        if not name.endswith('__') and not name in EXCLUDE_LIST:
            key=f'{obj_name}.{name}'
            if not inspect.isroutine(value):
                vis_name = name # Visibility name
                prefix = f'_{type(object).__name__}__' # name mangling
                if name.startswith(prefix):
                    vis_name = '-' + name.removeprefix(prefix) # de-mangling
                elif name.startswith('_'):
                    vis_name = '#' + name.removeprefix('_')
                attr_dict[key] = f'  {obj_name} : {vis_name} = {value}'
    return attr_dict

def do_plantuml_class_diagram(plantuml_data: pt.PlantumlDataType, **kwargs):
    """
    This function creates a simple plantuml output representation of the data class diagram.
    This function will only add PlantumlDataNote notes referring to classes, not to instances. 
    This function will replace the Python visibility prefixes '__' and '_' of the elements names by plantuml visibility simbols ('-' and '#').
    Argumnets:
        plantuml_data -- A class of a PlantumlDataType type.
        kwargs -- Optional key/value arguments.
    """

    connections = {} # Use dictionary to avoid duplications
    print("@startuml")

    if "arrow_dir" in plantuml_data.metadata_dict:
        print(plantuml_data.metadata_dict["arrow_dir"])
    if "skinparam" in plantuml_data.metadata_dict:
        print(plantuml_data.metadata_dict["skinparam"])

    # Get the set of all classes, including inheritance and interfaces
    classes_set = set()
    notes = []
    note_idx = 1
    for name, value in inspect.getmembers(plantuml_data):
        if not name.endswith('__'):
            if isinstance(value, pt.PlantumlDataNote):
                if isinstance(value.ref, type): # Only notes for types
                    notes.append(f'note "{value.note}" as N{note_idx}')
                    notes.append(f'N{note_idx} .. {value.name}')
                    note_idx += 1
                else:
                    pass # Ignores notes for instances
            else:
                classes_set |= get_classes(value)
                # print_class(name, value)

    # Get the set of classes associated with the objects, only the classes
    association_classes_set = set()
    for name, value in inspect.getmembers(plantuml_data):
        if not name.endswith('__') and not isinstance(value, pt.PlantumlDataNote):
            get_associated_classes(value, association_classes_set)

    # Get the set of associations
    association_set = set()
    for name, value in inspect.getmembers(plantuml_data):
        if not name.endswith('__') and not isinstance(value, pt.PlantumlDataNote):
            get_associations(value, association_set)

    # Get the dictionary of all class.attributes
    interfaces_set = set()
    class_dict = {}
    for class_item in classes_set | association_classes_set:
        attr_dict, is_interface = print_attrs_with_class(class_item)
        class_dict.update(attr_dict)
        if is_interface:
            interfaces_set.add(class_item)

    # Get the inheritances
    inheritance_set = set()
    for class_item in classes_set:
        inheritance_set |= get_inheritance(class_item)
        
    # Print interfaces definition
    for interface_item in interfaces_set:
        print_interface(interface_item.__name__)
        classes_set.discard(interface_item)

    # Print classes definition
    for class_item in classes_set | association_classes_set:
        print_class(class_item.__name__)

    # Print of the class inheritances
    for inheritance in inheritance_set:
        print(inheritance)

    for name, value in inspect.getmembers(plantuml_data):
        if not name.endswith('__') and not name in EXCLUDE_LIST and not name == "metadata_dict" and not isinstance(value, pt.PlantumlDataNote):
            # print (f'\'print_class_attrs_with_instance {name}')
            class_dict.update(print_attrs_with_instance(name, value))

    # Final print of the classes attributes
    for key, value in class_dict.items():
        # print(f'\' {key} = {value}')
        print(value)
        
    for association in association_set:
        print(association)

    for note in notes:
        print(note)

    print("@enduml")

def do_plantuml_object_diagram(plantuml_data: pt.PlantumlDataType, **kwargs):
    """
    This function creates a simple plantuml output representation of the data object diagram.
    This function will only add PlantumlDataNote notes referring to objects, not to classes.
    This function will replace the Python visibility prefixes '__' and '_' of the elements names by plantuml visibility simbols ('-' and '#').
    Argumnets:
        plantuml_data -- A class of a PlantumlDataType type.
        kwargs -- Optional key/value arguments.
    """

    connections = {} # Use dictionary to avoid duplications
    print("@startuml")

    if "arrow_dir" in plantuml_data.metadata_dict:
        print(plantuml_data.metadata_dict["arrow_dir"])
    if "skinparam" in plantuml_data.metadata_dict:
        print(plantuml_data.metadata_dict["skinparam"])

    cobj_dict = {}
    notes = []
    note_idx = 1
    for name, value in inspect.getmembers(plantuml_data):
        if not name.endswith('__') and not name == "metadata_dict":
            if isinstance(value, pt.PlantumlDataNote):
                if not isinstance(value.ref, type): # Only notes for instances
                    notes.append(f'note "{value.note}" as N{note_idx}')
                    notes.append(f'N{note_idx} .. {value.name}')
                    note_idx += 1
                else:
                    pass # Ignores notes for types
            else:
                print(f'object "{name}: {value.__class__.__name__}" as {name}')
                cobj_dict.update(print_object_values(name, value))

    # Final print of the objects values
    for key, value in cobj_dict.items():
        # print(f'\' {key} = {value}')
        print(value)
        
    for note in notes:
        print(note)

    print("@enduml")
