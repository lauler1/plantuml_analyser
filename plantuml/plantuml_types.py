from copy import deepcopy
import re
import types
import asyncio

import inspect

def get_variable_names(obj, namespace):
    return [name for name in namespace if namespace[name] is obj]

def sanitize_name(name):
    # print(f"sanitize_name {name} -> {re.sub(r'\W|^(?=\d)', '', name.lower())}")
    return re.sub(r'\W|^(?=\d)', '', name.lower())

class ObjectRef:
    """
    Stores a simple obj reference, it is used to store PlantumlType avoiding recursive searches.
    """
    def __init__(self, ref):
        self.ref = ref

class ArchBreakLine():
    """
    This class defines a PlantUML architectural breakline in the architecture layout.
    This function has no other function.
    """
    def __init__(self, name="", id="", **options):
        self.type = "BreakLine"
        self.name = name
        self.id = id

def post_init_decorator(init_func):
    def wrapper(self, *args, **kwargs):
        # Call the original __init__ method
        # print("     wrapper:", args)
        init_func(self, *args, **kwargs)
        # Call the post_init method after the original __init__ method
        self.post_init()
    return wrapper

def plantuml_architecture_decorator(init_func):
    def wrapper(self, *args, **kwargs):
        # Call the original __init__ method
        # print("   plantuml_architecture_decorator wrapper:", args)
        init_func(self, *args, **kwargs)
        # Call the post_init method after the original __init__ method
        self.arch_post_init()
    return wrapper

class PlantumlDataType:
    """
    Base class for all PlantUML data types. The objects inside this class will be showed in the class/object diagram.
    Valid to all derived classes.
    options:
        skinparam: plantUML skin parameters, it is a multi-line text.
    """
    def __init__(self, name="", id="", **options):
    
        self.metadata_dict = {}
        self.metadata_dict["skinparam"] = """
skinparam roundCorner 10
skinparam class {
BorderColor #7A694B
backGroundColor #FCFDF8/EBE5D7
}
skinparam roundCorner 10
skinparam object {
BorderColor #7A694B
backGroundColor #FCFDF8/EBE5D7
}
sprite deco <svg viewBox="0 0 16 16">
<path fill="#801714" d="M 2 2 H 13 V 15 H 1Z"/>
<path fill="#EEDCDA" d="M 3 3 H 12 V 8 H 3Z M 3 9 H 12 V 11 H 3Z M 3 12 H 12 V 14 H 3Z"/>
</svg>
skinparam linetype ortho
"""
        # self.metadata_dict["arrow_dir"] = "left to right direction"
        self.metadata_dict.update(options)
        
class PlantumlDataNote:
    """
    Class to define comment notes for data objects and types inside a PlantumlDataType. The objects or types referred in the initialization will have a text note shown when using do_plantuml_class_diagram or do_plantuml_object_diagram
    
    owner: The PlantumlDataType owner of this note instance (use 'self').
    ref: The object or type of object to add a note to.
    note: Text note.
    name: Optional name of a class or object to manually associate this note. It shall be used to replace ref (ref shall be None).
    """
    def __init__(self, owner: PlantumlDataType, ref=None, note: str ="Default note.", name = ""):
        self.ref = ref
        self.note = note
        self.name = name
        
        if isinstance(owner, PlantumlDataType) and ref != None and not isinstance(ref, type):
            for v_name, val in vars(owner).items():
                if val is ref:
                    self.name = v_name
                    break
        elif isinstance(ref, type):
            self.name = ref.__name__

class PlantumlType:
    """
    Class to define data types to be displayed as class diagrams
    """
    
    # Class variable to count instances, used for auto name generation
    _instance_count = 0 #: int = field(default=0, init=False, repr=False)
    description=""
 
    # metadata_dict = {}
    @post_init_decorator
    def __init__(self, name="", id="", **options):
        """
        Main constructor.
        name: The name of this component.
        id: An identification for this component, without spaces and special characters (like in a variable name). Any space and special character will be removed.
        options:
            note: Add a not to the component, e.g.: note=r"This is a note\nfor a component"
            remove: Remove completely a component of drawing, e.g.: remove=True
            hide: Make a component invisible, but still occupining the place, e.g.: hide=True
            color: Define the colors of the component as plantuml syntax, e.g.: color="pink;line:red;line.bold;text:red"
            svg_orientation: Used by SVG architecture to define the orientation of inner items, can be Orientation.TOP_DOWN or LEFT_RIGHT.

            title_height: SVG title height. Default 15.
            title_font_family: Title font family. Default 'Consolas'.
            title_font_size: Title font size. Default 25.

        """
        self.name = name
        self.type = "Type"
        self.id = sanitize_name(id)
        if self.id == "":
            self.id = sanitize_name(name)
        self.path = self.id # Initial path, will be replaced by architecture post init via set_architecture.
        self.metadata_dict = {"hide": False, "remove": False}

        #self.architecture = None
        self.owner = "NONE"
        # print("---->", get_variable_names(self, globals()))
        self.metadata_dict.update({"rect_min_x_len": 200, "rect_min_y_len": 50, "rect_x_pos":None, "rect_y_pos":None, "rect_x_len":None, "rect_y_len":None})

    def __str__(self):
        return f"'{self.path}'"

    def __repr__(self):
        return f"'{self.path}'"

    def is_visible(self):
        if self.metadata_dict['hide'] == True or self.metadata_dict['remove'] == True:
            return False
        return True

    def is_visible_recursive(self, arch):
        if self.metadata_dict['hide'] == True or self.metadata_dict['remove'] == True:
            return False

        owner_tree = arch.get_owner_tree(self)
        # print("is_visible_recursive ", owner_tree)
        for item in owner_tree:
            if item.is_visible() == False:
                return False

        return True
    
    def post_init(self):
        PlantumlType._instance_count += 1  # Increment the counter
        self.instance_count = PlantumlType._instance_count

        # print("      __post_init__(self):", self.name)

    def set_architecture(self, architecture):
        # setattr(self, "architecture", ObjectRef(architecture))
        #self.architecture = architecture_ref
        self.path = architecture.get_complete_path_name(self)
        self.owner = ObjectRef(architecture.get_owner(self))
        # print(f"set_architecture: {self.name} {self.owner} {architecture.get_owner(self)}")

    def add(self, value):
        """
        Add a new attribute to the class. The attribute must be instance of PlantumlType or ObjectRef of an instance of PlantumlType.
        """
        if isinstance(value, ObjectRef):
            # print(f"Adding ref {value.ref.name}")
            sanitized_name = sanitize_name(value.ref.id)
        elif isinstance(value, PlantumlType):
            # print(f"Adding obj {value.name}")
            sanitized_name = sanitize_name(value.id)
        else:
            return
        
        # Set the attribute on the class instance using reflection
        setattr(self, sanitized_name, value)
        
        # print(f"Added attribute: {sanitized_name} = {value} to {self.name}")

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
        """
        This is a recursive method that looks for the owner for an object from the current tree position.
        Idealy it can be called from a base architecture to look inside the entire architecture tree of components.
        """
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
        
    def find_sub_obj_by_path_recursive(self, path):
        # Goes recursive to find object
        result = None
        for key, value in self.__dict__.items():
            if isinstance(value, PlantumlType) and value.path == path:
                # print (f"  Found obj '{path}' at instance level")
                return value
            elif isinstance(value, PlantumlType) and not isinstance(value, PlantumlConnection):
                result = value.find_sub_obj_by_path_recursive(path)
                if result != None and isinstance(value, PlantumlType):
                    return result
        for key, value in vars(self.__class__).items():
            if isinstance(value, PlantumlType) and value.path == path:
                # print (f"  Found obj '{path}' at class level")
                return value
            elif isinstance(value, PlantumlType) and not isinstance(value, PlantumlConnection):
                result = value.find_sub_obj_by_path_recursive(path)
                if result != None and isinstance(value, PlantumlType):
                    return result
        # print (f"Obj '{path}' not found")
        return None

    def find_sub_obj_by_name_recursive(self, name):
        # Goes recursive to find object
        result = None
        for key, value in self.__dict__.items():
            if isinstance(value, PlantumlType) and value.name == name:
                # print (f"  Found obj '{name}' at instance level")
                return value
            elif isinstance(value, PlantumlType) and not isinstance(value, PlantumlConnection):
                result = value.find_sub_obj_by_name_recursive(name)
                if result != None and isinstance(value, PlantumlType):
                    return result
        for key, value in vars(self.__class__).items():
            if isinstance(value, PlantumlType) and value.name == name:
                # print (f"  Found obj '{name}' at class level")
                return value
            elif isinstance(value, PlantumlType) and not isinstance(value, PlantumlConnection):
                result = value.find_sub_obj_by_name_recursive(name)
                if result != None and isinstance(value, PlantumlType):
                    return result
        # print (f"Obj '{name}' not found")
        return None

    def find_sub_obj_by_id_recursive(self, id):
        # Goes recursive to find object
        result = None
        for key, value in self.__dict__.items():
            if isinstance(value, PlantumlType) and value.id == id:
                # print (f"  Found obj '{id}' at instance level")
                return value
            elif isinstance(value, PlantumlType) and not isinstance(value, PlantumlConnection):
                result = value.find_sub_obj_by_name_recursive(id)
                if result != None and isinstance(value, PlantumlType):
                    return result
        for key, value in vars(self.__class__).items():
            if isinstance(value, PlantumlType) and value.id == id:
                # print (f"  Found obj '{id}' at class level")
                return value
            elif isinstance(value, PlantumlType) and not isinstance(value, PlantumlConnection):
                result = value.find_sub_obj_by_name_recursive(id)
                if result != None and isinstance(value, PlantumlType):
                    return result
        # print (f"Obj '{id}' not found")
        return None

    def set_options(self, **options):
        """
        Update the options, refer to the main constructor for more details.
        """
        # Update the metadata_dict with the provided options
        self.metadata_dict.update(options)

    def replace_call_method(new_call_method):
        self.__call__ = types.MethodType(new_call_method, self)

    def get_all_activities(self, level = 1):
        """
        Returns a set of references to activities objects.
        """
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

class PlantumlContainer(PlantumlType):
    """
    Parent class for all class that may contain other PlantumlType inside, a container.
    See base class PlantumlType for more.
    """
    def __init__(self, name="", id="", **options):
        super().__init__(name, id)
        self.type = "container"
        self.metadata_dict.update(options)
        # super().__post_init__()

class PlantumlGroup(PlantumlContainer):
    """
    This class defines a PlantUML architectural 'together' to group components without any visible box.
    See base class PlantumlType for more.
    """
    def __init__(self, name="", id="", **options):
        super().__init__(name, id)
        self.type = "together"
        self.metadata_dict.update(options)
        # super().__post_init__()

class PlantumlActor(PlantumlContainer):
    """
    This class defines a PlantUML architectural Actor.
    See base class PlantumlType for more.
    """
    def __init__(self, name="", id="", **options):
        super().__init__(name, id)
        self.type = "Actor"
        self.metadata_dict.update(options)
        # super().__post_init__()

class PlantumlComponent(PlantumlContainer):
    """
    This class defines a PlantUML architectural Component.
    See base class PlantumlType for more.
    """
    def __init__(self, name="", id="", **options):
        super().__init__(name, id)
        self.type = "Component"
        self.metadata_dict.update(options)

class PlantumlFrame(PlantumlContainer):
    """
    This class defines a PlantUML architectural Frame.
    See base class PlantumlType for more.
    """
    def __init__(self, name="", id="", **options):
        super().__init__(name, id)
        self.type = "Frame"
        self.metadata_dict.update(options)

class PlantumlFolder(PlantumlContainer):
    """
    This class defines a PlantUML architectural Folder.
    See base class PlantumlType for more.
    """
    def __init__(self, name="", id="", **options):
        super().__init__(name, id)
        self.type = "Folder"
        self.metadata_dict.update(options)

class PlantumlDatabase(PlantumlContainer):
    """
    This class defines a PlantUML architectural Database.
    See base class PlantumlType for more.
    """
    def __init__(self, name="", id="", **options):
        super().__init__(name, id)
        self.type = "Database"
        self.metadata_dict.update(options)

class PlantumlPackage(PlantumlContainer):
    """
    This class defines a PlantUML architectural Package.
    See base class PlantumlType for more.
    """
    def __init__(self, name="", id="", **options):
        super().__init__(name, id)
        self.type = "Package"
        self.metadata_dict.update(options)

class PlantumlInterface(PlantumlType):
    """
    This class defines a PlantUML architectural Interface.
    See base class PlantumlType for more.
    """
    def __init__(self, name="", id="", **options):
        super().__init__(name, id)
        self.type = "Interface"
        self.metadata_dict.update(options)

# class PlantumlPort(PlantumlType):
    # """
    # This class defines a PlantUML architectural Port.
    # See base class PlantumlType for more.
    # """
    # def __init__(self, name="", id="", **options):
        # super().__init__(name, id)
        # self.type = "Port"
        # self.metadata_dict.update(options)

class PlantumlActivity(PlantumlType):
    """
    This class defines a PlantUML architectural Activity.
    See base class PlantumlType for more.
    """
    def __init__(self, name="", id="", **options):
        super().__init__(name, id)
        self.type = "Activity"
        self.metadata_dict.update(options)
        # super().__post_init__()

    def replace_run_method(self, new_call_method):
        self.run = types.MethodType(new_call_method, self)
        
    async def run(self, arch_inst):
        """
        The default __call__ for an activity does not do any particular action, you shall replace it by another call (you can use replace_call_method);
        Note, it must be async.
        """
        # print(f"Starting async call for {self.name}...")
        await asyncio.sleep(0)  # Simulating an asynchronous operation
        # print(f"Async call completed for {self.name}!")    

class PlantumlArchitecture(PlantumlContainer):
    """
    This class defines a PlantUML Architecture.
    This class defines the 'skinparam' attribute for all components (plantuml syntax). It can be replaced using parma skinparam="..."
    
    You can define the variables layout_combine_vertical and layout_combine_horizontal inside the class as list of tuples to define invisible connections between two componnents to force some layout pattern. e.g. = [(self.comp1, self.comp2), (self.comp3, self.comp4)] will connect comp1 with comp2 and comp3 with comp4.
    
    See base class PlantumlType for more.
    options:
        arrow_dir: default orientation of the arrows for plantUML, it can be "left to right direction" or "top to bottom direction". For SVG, architecture, svg_orientation has precedence.
        skinparam: plantUML skin parameters, it is a multi-line text.
        show_connections: Can be used to turn off the visibility of connection in the architecture diagrams (show_connections=False).
    """

    @plantuml_architecture_decorator
    def __init__(self, name="", id="", **options):
        super().__init__(name, id)
        self.type = "Architecture"
        self.metadata_dict["layout_connectors"] = [] # Connections used to force placing components next other
        self.metadata_dict["arrow_dir"] = "left to right direction"
        self.metadata_dict["arrow_dir"] = "top to bottom direction" # this is the orientation of plantuml arrows
        self.metadata_dict["skinparam"] = """
skinparam note{
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
skinparam linetype ortho
"""

    def _recursive_post_init(self, curr_obj):
        #Add this architecture as attribute of each element instance of PlantumlType
        for key, value in vars(curr_obj.__class__).items():
            if isinstance(value, PlantumlType):
                if value.name == "":
                    value.name = key
                if value.id == "":
                    value.id = key
                value.set_architecture(self)
                self._recursive_post_init(value)
        for key, value in curr_obj.__dict__.items():
            if isinstance(value, PlantumlType):
                if value.name == "":
                    value.name = key
                if value.id == "":
                    value.id = key
                value.set_architecture(self)
                self._recursive_post_init(value)
    
    def arch_post_init(self):
        # print("    arch_post_init(self):", self.name)
        self._recursive_post_init(self)
        self._connect_arch_items()
        self.do_layout_combinations()

    def _connect_arch_items(self):
        # Connects all compones to the previous one horizontally, till a ArchBreakLine is found
        # Initialize the previous key-value pair
        self.layout_combine_horizontal = []
        self.layout_combine_vertical = []
        prev_value = None
        first_row_value = None
        previous_first_row_value = None
        for value in self.__dict__.values():
            if isinstance(value, PlantumlType) and not isinstance(value, PlantumlConnection) and not isinstance(value, PlantumlGroup):
                if first_row_value is None:
                    first_row_value = value 
                    if previous_first_row_value is not None:
                        self.layout_combine_vertical.append((previous_first_row_value, first_row_value))
                        previous_first_row_value = None
                if prev_value is not None:
                    self.layout_combine_horizontal.append((prev_value, value))
                    # Update previous value pair
                prev_value = value
            elif isinstance(value, ArchBreakLine):
                # Starts again new line
                prev_value = None
                previous_first_row_value = first_row_value
                first_row_value = None
    
    def do_layout_combinations(self):
        # Create some invisible plantuml connections to try to fix components in relative positions
        self.metadata_dict["layout_connectors"] = []
        if hasattr(self, 'layout_combine_vertical'):
            for item in self.layout_combine_vertical:
                # Store a tuple
                self.metadata_dict["layout_connectors"].append((ObjectRef(item[0]), f"-[hidden]d-", ObjectRef(item[1])))
                # self.metadata_dict["layout_connectors"].append(f"{item[0].path} -[hidden]d- {item[1].path}")
        if hasattr(self, 'layout_combine_horizontal'):
            for item in self.layout_combine_horizontal:
                # Store a tuple
                self.metadata_dict["layout_connectors"].append((ObjectRef(item[0]), f"-[hidden]r-", ObjectRef(item[1])))
                # self.metadata_dict["layout_connectors"].append(f"{item[0].path} -[hidden]r- {item[1].path}")

    def get_sub_obj_by_name(self, name):
        # Does not go recursive
        for key, value in self.__dict__.items():
            if isinstance(value, PlantumlType) and value.name == name:
                # print (f"  Found obj '{name}' at instance level")
                return value
        for key, value in vars(self.__class__).items():
            if isinstance(value, PlantumlType) and value.name == name:
                # print (f"  Found obj '{name}' at class level")
                return value
        print (f"Obj '{name}' not found")
        return None

    def get_sub_obj_by_id(self, id):
        # Does not go recursive
        for key, value in self.__dict__.items():
            if isinstance(value, PlantumlType) and value.id == id:
                # print (f"  Found obj '{id}' at instance level")
                return value
        for key, value in vars(self.__class__).items():
            if isinstance(value, PlantumlType) and value.id == id:
                # print (f"  Found obj '{id}' at class level")
                return value
        print (f"Obj '{id}' not found")
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
        name_tree = [item.id for item in owner_tree]
        name_tree.append(object.id)
        return "_".join(name_tree)

class PlantumlConnection(PlantumlType):
    """
    This class defines a PlantUML architectural Connection between two components.
    Usually connecting actors, components or activities, but also interfaces and ports.
    See base class PlantumlType for more.
    """
    def __init__(self, name, comp1, comp2, id="", **options):
        """
        Main constructor.
        
        More details of lines rules for plantuml, see:
        - https://crashedmind.github.io/PlantUMLHitchhikersGuide/layout/layout.html
        - https://crashedmind.github.io/PlantUMLHitchhikersGuide/index.html
        - https://isgb.otago.ac.nz/infosci/mark.george/Wiki/wiki/PlantUML%20GraphViz%20Layout
        
        A copnnection can connect components and activities. Only activities can be simulated. Multiple components to single and single to multiple are allowed, but they are unidiretional. Multiple to multiple are not allowed. Multiple activities to single activity will be simulated using single shared queue, and the direction of communication must be from multiple to the single. Single activity to multiple activities will use separate queues for each destination, and the direction of communication must be from the single to multiple.
        
        See base class PlantumlType for more.
        comp1: First end component of the connection. It can be a single component, activity or a list of components.
        comp2: Second end component of the connection. It can be a single component, activity or a list of components.
        options:
            direction: Can be "in", "out" or "inout". Default = "inout".
            line: plantuml connection line/arrow, e.g. "--", "->", "<-",... Default line used is "--"
            
        """
        super().__init__(name, id)
        self.type = "Connection"
        
        self.metadata_dict["direction"] = "inout"
        # self.metadata_dict["line"] = "--"

        self.metadata_dict.update(options)
        
        self.set_refs(comp1, comp2)

    def set_refs(self, comp1, comp2):
        assert isinstance(comp1, PlantumlActivity) or isinstance(comp1, PlantumlActor) or isinstance(comp1, PlantumlComponent) or isinstance(comp1, list), "comp1 must be of type PlantumlActivity, PlantumlActor or PlantumlComponent"
        
        if isinstance(comp1, PlantumlActivity):
            assert isinstance(comp2, PlantumlActivity) or isinstance(comp2, list), "PlantumlActivity can only be connected to other PlantumlActivity"
        if not isinstance(comp1, PlantumlActivity) and not isinstance(comp1, list):
            assert not isinstance(comp2, PlantumlActivity), "PlantumlActivity can only be connected to other PlantumlActivity"
        if isinstance(comp1, list):
            assert not isinstance(comp2, list), "Multiple to multiple connection is not allowed."

        if isinstance(comp1, list):
            self.metadata_dict["direction"] = "out"
            self.comp1 = []
            for item in comp1:
                self.comp1.append(ObjectRef(item))
                item.add(ObjectRef(self))
        else:
            self.comp1 = ObjectRef(comp1)
            # Also creates the connection inside the componets
            self.comp1.ref.add(ObjectRef(self)) # Also creates the connection inside the componets

        if isinstance(comp2, list):
            self.metadata_dict["direction"] = "out"
            self.comp2 = []
            for item in comp2:
                self.comp2.append(ObjectRef(item))
                item.add(ObjectRef(self)) # Also creates the connection inside the componets
        else:
            self.comp2 = ObjectRef(comp2)
            # Also creates the connection inside the componets
            self.comp2.ref.add(ObjectRef(self))

def print_with_indent(text, indent=1):
    print('    ' * indent + text)
    
def go_through_connections(object, architecture):
    def proc_value(value):
        owner = architecture.get_owner(value)
        owner_name = ""
        # if isinstance(owner, PlantumlType):
            # owner_name = owner.name
        # Reconstruct comp1 with the new references
        if isinstance(value.comp1, list):
            comp1 = []
            for item in value.comp1:
                comp1.append(architecture.find_sub_obj_by_name_recursive(item.ref.name))
        else:
            comp1 = architecture.find_sub_obj_by_name_recursive(value.comp1.ref.name)
        # Reconstruct comp2 with the new references
        if isinstance(value.comp2, list):
            comp2 = []
            for item in value.comp2:
                comp2.append(architecture.find_sub_obj_by_name_recursive(item.ref.name))
        else:
            comp2 = architecture.find_sub_obj_by_name_recursive(value.comp2.ref.name)
        value.set_refs(comp1, comp2)

    for key, value in vars(object.__class__).items():
        if isinstance(value, PlantumlConnection):
            proc_value(value)
        elif isinstance(value, PlantumlType) and not isinstance(value, PlantumlConnection):
            go_through_connections(value, architecture)
    for key, value in object.__dict__.items():
        if isinstance(value, PlantumlConnection):
            proc_value(value)
        elif isinstance(value, PlantumlType) and not isinstance(value, PlantumlConnection):
            go_through_connections(value, architecture)

    
def clone_architecture(architecture, new_name, base_class=PlantumlArchitecture):

    print("\n----------------------------------------------------------------------------------\nclone_architecture")
    # Step 1: Get the original class and create a new class with the specified base class
    OriginalClass = architecture.__class__

    # Create a new class dynamically that inherits from the given base class
    NewClass = types.new_class(OriginalClass.__name__, (base_class,), {})

    # Step 2: Copy the class attributes and methods from the original class
    for key, value in OriginalClass.__dict__.items():
        if not key.startswith('__'):
            pass
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
            else:
                pass
                setattr(NewClass, key, deepcopy(value))

    # Step 3: Create a new instance of this new class
    new_instance = NewClass(new_name)

    # Step 4: Copy the instance attributes from the original instance
    for key, value in architecture.__dict__.items():
        setattr(new_instance, key, deepcopy(value))

    # Step 5: Correct all connection references
    go_through_connections(new_instance, new_instance)
    return new_instance
