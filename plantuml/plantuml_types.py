from copy import deepcopy
import re
import types
import asyncio

import inspect

def get_variable_names(obj, namespace):
    return [name for name in namespace if namespace[name] is obj]

def sanitize_name(name):
    return re.sub(r'\W|^(?=\d)', '_', name.lower())

class ObjectRef:
    """
    Stores a simple obj reference, it is used to store PlantumlType avoiding recursive searches.
    """
    def __init__(self, ref):
        self.ref = ref

class PlantumlType:
    """
    Base class for all PlantUML architectural types
    Valid to all derived classes.
    """
    
    # Class variable to count instances, used for auto name generation
    _instance_count = 0 #: int = field(default=0, init=False, repr=False)
    description=""
 
    # metadata_dict = {}
    def __init__(self, name="", **options):
        """
        Main constructor.
        name: The name of this component.
        options:
            note: Add a not to the component, e.g.: note=r"This is a note\nfor a component"
            remove: Remove completely a component of drawing, e.g.: remove=True
            hide: Make a component invisible, but still occupining the place, e.g.: hide=True
            color: Define the colors of the component as plantuml syntax, e.g.: color="pink;line:red;line.bold;text:red"
        """
        self.name = name
        self.type = "Type"
        # self.path = name
        self.metadata_dict = {"hide": False, "remove": False}
        # print("---->", get_variable_names(self, globals()))

    def __post_init__(self):
        PlantumlType._instance_count += 1  # Increment the counter
        self.instance_count = PlantumlType._instance_count

    def add(self, value):
        """
        Add a new attribute to the class. The attribute must be instance of PlantumlType or ObjectRef of an instance of PlantumlType.
        """
        if isinstance(value, ObjectRef):
            print(f"Adding {value.ref.name}")
            sanitized_name = sanitize_name(value.ref.name)
        elif isinstance(value, PlantumlType):
            print(f"Adding {value.name}")
            sanitized_name = sanitize_name(value.name)
        else:
            return
        
        # Set the attribute on the class instance using reflection
        setattr(self, sanitized_name, value)
        
        print(f"Added attribute: {sanitized_name} = {value} to {self.name}")

    def has_sub_objs(self) -> bool:
        # Iterate over all attributes of the object
        for attr_name, attr_value in vars(self).items():
            # Check if any attribute is an instance of the specified base class
            if isinstance(attr_value, PlantumlType):
                return True
        # Check static (class) variables
        for attr_name, attr_value in vars(self.__class__).items():
            if isinstance(attr_value, PlantumlType):
                return True
        return False
        
    def get_activity_owner(self, activity):
        result = None
        for key, value in vars(self.__class__).items():
            if isinstance(value, PlantumlActivity) and activity == value:
                result = self
                # print(f"   Found owner of {activity.name}, it is {result}, {key}")
                return result
            elif isinstance(value, PlantumlType) and not isinstance(value, PlantumlConnection):
                result = value.get_activity_owner(activity)
                if result != None and  isinstance(value, PlantumlType):
                    return result
        for key, value in self.__dict__.items():
            if isinstance(value, PlantumlActivity) and activity == value:
                result = self
                # print(f"   Found owner of {activity.name}, it is {result}, {key}")
                return result
            elif isinstance(value, PlantumlType) and not isinstance(value, PlantumlConnection):
                result = value.get_activity_owner(activity)
                if result != None and  isinstance(value, PlantumlType):
                    return result
        return result

    def get_owner(self, object):
        result = None
        for key, value in vars(self.__class__).items():
            if object == value:
                result = self
                return result
            elif isinstance(value, PlantumlType) and not isinstance(value, PlantumlConnection):
                result = value.get_owner(object)
                if result != None and isinstance(value, PlantumlType):
                    return result
        for key, value in self.__dict__.items():
            if object == value:
                result = self
                return result
            elif isinstance(value, PlantumlType) and not isinstance(value, PlantumlConnection):
                result = value.get_owner(object)
                if result != None and isinstance(value, PlantumlType):
                    return result
        return result
        
    def find_sub_obj_by_name_recursive(self, name):
        result = None
        for key, value in self.__dict__.items():
            if isinstance(value, PlantumlType) and value.name == name:
                print (f"  Found obj '{name}' at instance level")
                return value
            elif isinstance(value, PlantumlType) and not isinstance(value, PlantumlConnection):
                result = value.find_sub_obj_by_name_recursive(name)
                if result != None and isinstance(value, PlantumlType):
                    return result
        for key, value in vars(self.__class__).items():
            if isinstance(value, PlantumlType) and value.name == name:
                print (f"  Found obj '{name}' at class level")
                return value
            elif isinstance(value, PlantumlType) and not isinstance(value, PlantumlConnection):
                result = value.find_sub_obj_by_name_recursive(name)
                if result != None and isinstance(value, PlantumlType):
                    return result
        # print (f"Obj '{name}' not found")
        return None

    def get_sub_obj_by_name(self, name):
        for key, value in self.__dict__.items():
            if isinstance(value, PlantumlType) and value.name == name:
                print (f"  Found obj '{name}' at instance level")
                return value
        for key, value in vars(self.__class__).items():
            if isinstance(value, PlantumlType) and value.name == name:
                print (f"  Found obj '{name}' at class level")
                return value
        print (f"Obj '{name}' not found")
        return None

    def get_owner_tree(self, object):
        owner_tree = []
        current_owner = self.get_owner(object)

        while current_owner is not None:
            owner_tree.insert(0, current_owner)
            current_owner = self.get_owner(current_owner)

        return owner_tree

    def get_complete_path_name(self, object):
        owner_tree = self.get_owner_tree(object)
        name_tree = [sanitize_name(item.name) for item in owner_tree]
        name_tree.append(sanitize_name(object.name))
        return "_".join(name_tree)

    def set_options(self, **options):
        """
        Update the options, refer to the main constructor for more details.
        """
        # Update the metadata_dict with the provided options
        self.metadata_dict.update(options)

    def replace_call_method(new_call_method):
        self.__call__ = types.MethodType(new_call_method, self)

    def get_all_activities(self, level = 1):
        activities_list = set()
        
        for key, value in vars(self.__class__).items():
            if isinstance(value, PlantumlActivity):
                activities_list.add(value)
            elif isinstance(value, PlantumlType) and not isinstance(value, PlantumlConnection):
                activities_list.update(value.get_all_activities(level+1))

        for key, value in self.__dict__.items():
            if isinstance(value, PlantumlActivity):
                activities_list.add(value)
            elif isinstance(value, PlantumlType) and not isinstance(value, PlantumlConnection):
                activities_list.update(value.get_all_activities(level+1))

        return activities_list

class PlantumlActor(PlantumlType):
    """
    This class defines a PlantUML architectural Actor.
    See base class PlantumlType for more.
    """
    def __init__(self, name="", **options):
        super().__init__(name)
        self.type = "Actor"
        self.metadata_dict.update(options)
        super().__post_init__()

class PlantumlComponent(PlantumlType):
    """
    This class defines a PlantUML architectural Component.
    See base class PlantumlType for more.
    """
    def __init__(self, name="", **options):
        super().__init__(name)
        self.type = "Component"
        self.metadata_dict.update(options)
        super().__post_init__()

class PlantumlInterface(PlantumlType):
    """
    This class defines a PlantUML architectural Interface.
    See base class PlantumlType for more.
    """
    def __init__(self, name="", **options):
        super().__init__(name)
        self.type = "Interface"
        self.metadata_dict.update(options)
        super().__post_init__()

class PlantumlPort(PlantumlType):
    """
    This class defines a PlantUML architectural Port.
    See base class PlantumlType for more.
    """
    def __init__(self, name="", **options):
        super().__init__(name)
        self.type = "Port"
        self.metadata_dict.update(options)
        super().__post_init__()

class PlantumlActivity(PlantumlType):
    """
    This class defines a PlantUML architectural Activity.
    See base class PlantumlType for more.
    """
    def __init__(self, name="", **options):
        super().__init__(name)
        self.type = "Activity"
        self.metadata_dict.update(options)
        super().__post_init__()
        
    async def run(self, arch_inst):
        """
        The default __call__ for an activity does not do any particular action, you shall replace it by another call (you can use replace_call_method);
        Note, it must be async.
        """
        # print(f"Starting async call for {self.name}...")
        await asyncio.sleep(0)  # Simulating an asynchronous operation
        # print(f"Async call completed for {self.name}!")    

class PlantumlArchitecture(PlantumlType):
    """
    This class defines a PlantUML Architecture.
    This class defines the 'skinparam' attribute for all components (plantuml syntax). It can be replaced using parma skinparam="..."
    See base class PlantumlType for more.
    options:
        skinparam="..."
    """
    def __init__(self, name="", **options):
        super().__init__(name)
        self.type = "Architecture"
        self.metadata_dict["skinparam"] = """skinparam note{
  BackgroundColor #FFFFCB
  BorderColor #FFCC66
}
skinparam agent {
  roundCorne 0
  BackgroundColor #C5FFA6
  BorderColor #145B17
  FontColor #085D24
}
skinparam rectangle {
  roundCorne 0
  BackgroundColor #D9FCFF-C6E6FF
  BorderColor #145B17
  FontColor #085D24
}
skinparam interface {
  backgroundColor RosyBrown
  borderColor orange
}
skinparam component {
  roundCorner 0
  FontSize 13
  FontName Courier
  BorderColor #4E4E97
  BackgroundColor #C2E5FE-96B1DA
  ArrowFontName Impact
  ArrowColor #5C5C66
  ArrowFontColor #4D4D4D
}
"""

class PlantumlConnection(PlantumlType):
    """
    This class defines a PlantUML architectural Connection between two components.
    Usually connecting actors, components or activities, but also interfaces and ports.
    See base class PlantumlType for more.
    """
    def __init__(self, name, comp1, comp2, **options):
        """
        Main constructor.
        See base class PlantumlType for more.
        options:
            direction: Can be "in", "out" or "inout". Default = "inout".
            line: plantuml connection line/arrow, e.g. "--", "->", "<-",... Default line used is "--"
        """
        super().__init__(name)
        self.type = "ArchView"
        
        self.metadata_dict["direction"] = "inout"

        self.metadata_dict.update(options)
        
        self.set_refs(comp1, comp2)

    def set_refs(self, comp1, comp2):
        assert isinstance(comp1, PlantumlActivity) or isinstance(comp1, PlantumlActor) or isinstance(comp1, PlantumlComponent), "comp1 must be of type PlantumlActivity, PlantumlActor or PlantumlComponent"
        
        if isinstance(comp1, PlantumlActivity):
            assert isinstance(comp2, PlantumlActivity), "PlantumlActivity can only be connected to other PlantumlActivity"

        if not isinstance(comp1, PlantumlActivity):
            assert not isinstance(comp2, PlantumlActivity), "PlantumlActivity can only be connected to other PlantumlActivity"

        self.comp1 = ObjectRef(comp1)
        self.comp2 = ObjectRef(comp2)

        # Also creates the connection inside the componets
        self.comp1.ref.add(ObjectRef(self))
        self.comp2.ref.add(ObjectRef(self))

def print_with_indent(text, indent=1):
    print('    ' * indent + text)

def clone_plant_uml_object(object):
    # for key, value in object.__dict__.items():
        # if isinstance(value, PlantumlType):
            # setattr(new_instance, key, clone_plant_uml_object(value))
        # else:
            # setattr(new_instance, key, deepcopy(value))
            
    return deepcopy(object)
    
    
def go_through_connections(object, architecture):
    for key, value in vars(object.__class__).items():
        if isinstance(value, PlantumlConnection):
            owner = architecture.get_owner(value)
            owner_name = ""
            if isinstance(owner, PlantumlType):
                owner_name = owner.name
            # print(f"  Class connection: {key}, owner={owner_name}, comp1={value.comp1.ref.name}, comp2={value.comp2.ref.name}")
            # print(f"      insta={value}")
            # print(f"      owner={owner}")
            # print(f"      comp1={value.comp1.ref}")
            # print(f"      comp2={value.comp2.ref}")
            
            comp1 = architecture.find_sub_obj_by_name_recursive(value.comp1.ref.name)
            comp2 = architecture.find_sub_obj_by_name_recursive(value.comp2.ref.name)
            # print(f"       New comp1={comp1}")
            # print(f"       New comp2={comp2}")
            value.set_refs(comp1, comp2)
            
        elif isinstance(value, PlantumlType) and not isinstance(value, PlantumlConnection):
            result = value.get_owner(object)
            go_through_connections(value, architecture)
    for key, value in object.__dict__.items():
        if isinstance(value, PlantumlConnection):
            owner = architecture.get_owner(value)
            owner_name = ""
            if isinstance(owner, PlantumlType):
                owner_name = owner.name
            # print(f"  Objct connection: {key}, owner={owner_name}, comp1={value.comp1.ref.name}, comp2={value.comp2.ref.name}")
            # print(f"      insta={value}")
            # print(f"      owner={owner}")
            # print(f"      comp1={value.comp1.ref}")
            # print(f"      comp2={value.comp2.ref}")
            
            comp1 = architecture.find_sub_obj_by_name_recursive(value.comp1.ref.name)
            comp2 = architecture.find_sub_obj_by_name_recursive(value.comp2.ref.name)
            # print(f"       New comp1={comp1}")
            # print(f"       New comp2={comp2}")
            value.set_refs(comp1, comp2)
            
        elif isinstance(value, PlantumlType) and not isinstance(value, PlantumlConnection):
            go_through_connections(value, architecture)

    
def clone_architecture(architecture, new_name, base_class=PlantumlArchitecture):

    print("\n----------------------------------------------------------------------------------\nclone_architecture")
    # print("original class items")
    # for key, value in vars(architecture.__class__).items():
        # print_with_indent(f"{key}: {value}")
    # print("original object items")
    # for key, value in architecture.__dict__.items():
        # print_with_indent(f"{key}: {value}")
    
    # # Step 1: Get the original class and create a new class with the specified base class
    OriginalClass = architecture.__class__

    # # Create a new class dynamically that inherits from the given base class
    NewClass = types.new_class(OriginalClass.__name__, (base_class,), {})

    # Step 2: Copy the class attributes and methods from the original class
    for key, value in OriginalClass.__dict__.items():
        if not key.startswith('__'):
            # Ensure that functions are correctly bound to the new class
            if isinstance(value, types.FunctionType):
                value = types.FunctionType(
                    value.__code__,
                    value.__globals__,
                    name=value.__name__,
                    argdefs=value.__defaults__,
                    closure=value.__closure__
                )
                setattr(NewClass, key, value)
            # elif isinstance(value, PlantumlType):
                # setattr(NewClass, key, clone_plant_uml_object(value))
            else:
                setattr(NewClass, key, deepcopy(value))

    # Step 3: Create a new instance of this new class
    new_instance = NewClass(new_name)

    # Step 4: Copy the instance attributes from the original instance
    for key, value in architecture.__dict__.items():
        setattr(new_instance, key, deepcopy(value))

    # print("new class items")
    # for key, value in vars(new_instance.__class__).items():
        # print_with_indent(f"{key}: {value}")
    # print("new object items")
    # for key, value in new_instance.__dict__.items():
        # print_with_indent(f"{key}: {value}")

    # print("go_through_connections Original")
    # go_through_connections(new_instance, architecture)
    # print("go_through_connections new")
    go_through_connections(new_instance, new_instance)
    return new_instance