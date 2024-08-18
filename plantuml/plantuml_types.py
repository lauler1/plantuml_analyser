from copy import deepcopy
import re
import types
import asyncio
from dataclasses import dataclass, field

def get_variable_names(obj, namespace):
    return [name for name in namespace if namespace[name] is obj]

def sanitize_name(name):
    return re.sub(r'\W|^(?=\d)', '_', name.lower())

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
        self.path = name
        self.metadata_dict = {"hide": False, "remove": False}
        # print("---->", get_variable_names(self, globals()))

    def __post_init__(self):
        PlantumlType._instance_count += 1  # Increment the counter
        self.instance_count = PlantumlType._instance_count

    def add(self, value):
        print(f"Adding {value.name}")

        # Sanitize the variable name: replace invalid characters with '_'
        sanitized_name = sanitize_name(value.name)#re.sub(r'\W|^(?=\d)', '_', value.name.lower())
        
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

        # print(f"   self: {self}")
        result = None
        for key, value in vars(self.__class__).items():
            # print(f"   Class: {key}:{value}")
            if object == value:
                result = self
                # print(f"   Found owner of {object.name}, it is {result}, {key}")
                return result
            elif isinstance(value, PlantumlType) and not isinstance(value, PlantumlConnection):
                result = value.get_owner(object)
                if result != None and isinstance(value, PlantumlType):
                    return result
        for key, value in self.__dict__.items():
            # print(f"   Object: {key}:{value}")
            if object == value:
                result = self
                # print(f"   Found owner of {object.name}, it is {result}, {key}")
                return result
            elif isinstance(value, PlantumlType) and not isinstance(value, PlantumlConnection):
                result = value.get_owner(object)
                if result != None and isinstance(value, PlantumlType):
                    return result
        return result
        
    def get_owner_tree(self, object):
        owner_tree = []
        current_owner = self.get_owner(object)
        
        # print("   self =", self.name)

        while current_owner is not None:
            # print("     current_owner =", current_owner.name)
            owner_tree.append(current_owner.name)
            current_owner = self.get_owner(current_owner)

        return owner_tree

    def set_options(self, **options):
        """
        Update the options, refer to the main constructor for more details.
        """
        # Update the metadata_dict with the provided options
        self.metadata_dict.update(options)

    def replace_call_method(new_call_method):
        self.__call__ = types.MethodType(new_call_method, self)

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
        await asyncio.sleep(2)  # Simulating an asynchronous operation
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
        super().__post_init__()

    def gather_participants(self, activities):
        owners = set()
        participants = {}
        for activity in activities:
            # print(f"  gather_participants {activity.name}")
            res = self.get_activity_owner(activity)
            # print(f"    gather_participants res={res}")
            owners.add(res)
        # print("  Owners:", owners)
        for owner in owners:
            if owner != None:
                color = "#96B1DA"
                
                if isinstance(owner, PlantumlActor):
                    color = "#C6E6FF"
                # print("  Owner:", owner.name)
                sanitized_name = sanitize_name(owner.name)#re.sub(r'\W|^(?=\d)', '_', owner.name.lower())
                # print(f'participant "{owner}" as {sanitized_name}')
                participants[sanitized_name] = f'participant "{owner.name}" as {sanitized_name} {color}'
        self.metadata_dict['participants'] = participants

    def set_simulation_decorator(self, deco_text):
        self.metadata_dict['sequence'].append(deco_text)

    def set_simulation_activate(self, component):
        if isinstance(component, PlantumlActivity):
            component = self.get_activity_owner(component)
        self.metadata_dict['sequence'].append(f"activate {sanitize_name(component.name)}")

    def set_simulation_deactivate(self, component):
        if isinstance(component, PlantumlActivity):
            component = self.get_activity_owner(component)
        self.metadata_dict['sequence'].append(f"deactivate {sanitize_name(component.name)}")

    def set_simulation_activity_decorator(self, component):
        if not isinstance(component, PlantumlActivity):
            return
        owner = self.get_activity_owner(component)
        self.metadata_dict['sequence'].append(f"rnote over {sanitize_name(owner.name)} #C5FFA6\n{component.name}\nendrnote")


    async def run(self, activities):
        # Run the list of coroutines concurrently
        # print ("Running coroutines:", activities)
        await asyncio.gather(*(coro.run(self) for coro in activities))

    def simulate(self):
        activities = self.get_all_activities()
        self.metadata_dict['part_seq'] = []
        self.metadata_dict['sequence'] = []
        
        # for item in activities:
            # print("       Activities: =", item)
        print("@startuml")
        
        skinparam = """hide footbox
skinparam roundcorner 0
skinparam sequence {
LifeLineBackgroundColor #C5FFA6
LifeLineBorderColor #095C2E
ParticipantFontColor #4A4A97
ParticipantBorderColor #4A4A97
ParticipantBackgroundColor #96B1DA
}"""

        print(skinparam)
        # if "skinparam" in self.metadata_dict:
            # print(self.metadata_dict["skinparam"])

        self.gather_participants(activities)
        asyncio.run(self.run(list(activities)))
        
        new_list_of_participants = []
        for item in self.metadata_dict['part_seq']:
            if not item in new_list_of_participants:
                new_list_of_participants.append(item)
        
        for item in new_list_of_participants:
            print(self.metadata_dict['participants'][item])
        
        
        for item in self.metadata_dict['sequence'] :
            print(item)
        
        print("@enduml")            


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
        self.comp1 = comp1
        self.comp2 = comp2
        
        self.metadata_dict["direction"] = "inout"
        
        assert isinstance(comp1, PlantumlActivity) or isinstance(comp1, PlantumlActor) or isinstance(comp1, PlantumlComponent), "comp1 must be of type PlantumlActivity, PlantumlActor or PlantumlComponent"
        
        if isinstance(comp1, PlantumlActivity):
            assert isinstance(comp2, PlantumlActivity), "PlantumlActivity can only be connected to other PlantumlActivity"

        if not isinstance(comp1, PlantumlActivity):
            assert not isinstance(comp2, PlantumlActivity), "PlantumlActivity can only be connected to other PlantumlActivity"

        self.metadata_dict.update(options)
        self.queue = asyncio.Queue()
        
    # def __post_init__(self):       
        # super().__post_init__()

        # Also creates the connection inside the componets
        self.comp1.add(self)
        self.comp2.add(self)

        
    def print_transmission(self, architecture, sender, text):
        send_name = sender.name 
        if isinstance(sender, PlantumlActivity):
            send_name = architecture.get_activity_owner(sender).name

        other = self.comp1
        if other == sender:
            other = self.comp2
        other_name = other.name 
        if isinstance(sender, PlantumlActivity):
            other_name = architecture.get_activity_owner(other).name
        sanitized_send_name = sanitize_name(send_name)
        sanitized_other_name = sanitize_name(other_name)
        architecture.metadata_dict['part_seq'].append(sanitized_send_name)#re.sub(r'\W|^(?=\d)', '_', send_name.lower()))
        architecture.metadata_dict['part_seq'].append(sanitized_other_name)#re.sub(r'\W|^(?=\d)', '_', other_name.lower()))

        # print(f"{re.sub(r'\W|^(?=\d)', '_', send_name.lower())} -> {re.sub(r'\W|^(?=\d)', '_', other_name.lower())}")
        architecture.metadata_dict['sequence'].append(f"{sanitized_send_name} -> {sanitized_other_name}: {text}")
        
    async def send_message(self, architecture, sender, lable, data=""):
        """
        Sends a message in the queue.
        This method also yields the control to the event loop after sending.
        """
        self.print_transmission(architecture, sender, lable)
        await self.queue.put({"label":lable, "data":data})

    async def send_message_and_wait(self, architecture, sender, lable, data=""):
        """
        Sends a message and waits for an answer in the queue.
        """
        self.print_transmission(architecture, sender, lable)
        self.queue.put_nowait({"label":lable, "data":data})
        item = await self.queue.get()
        return item

    async def wait_message(self, architecture):
        """
        Waits for a message in the queue.
        """
        item = await self.queue.get()
        return item
