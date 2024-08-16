from dataclasses import dataclass, field

def get_variable_names(obj, namespace):
    return [name for name in namespace if namespace[name] is obj]

@dataclass
class PlantumlType:
    """
    Base class for all PlantUML architectural types
    Valid to all derived classes.
    name: The name of this component.
    options:
        note: Add a not to the component, e.g.: note=r"This is a note\nfor a component"
        remove: Remove completely a component of drawing, e.g.: remove=True
        hide: Make a component invisible, but still occupining the place, e.g.: hide=True
        color: Define the colors of the component as plantuml syntax, e.g.: color="pink;line:red;line.bold;text:red"
    """
    
    # Class variable to count instances, used for auto name generation
    _instance_count: int = field(default=0, init=False, repr=False)
    
    # metadata_dict = {}
    def __init__(self, name="", **options):
        self.name = name
        self.type = "Type"
        self.path = name
        self.metadata_dict = {"hide": False, "remove": False}
        # print("---->", get_variable_names(self, globals()))

    def __post_init__(self):
        PlantumlType._instance_count += 1  # Increment the counter
        # if self.name == "":
            # # print("-------------------------------------------", self.name)
            # self.name = f"{self.type}_{type(self)._instance_count}"
            # # print("-----------------------------------------------", self.name)

@dataclass
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

@dataclass
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

@dataclass
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

@dataclass
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

@dataclass
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

@dataclass
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
  roundCorner 0
  BackgroundColor #C5FFA6
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
}"""
        super().__post_init__()

@dataclass
class PlantumlArchView(PlantumlArchitecture):
    """
    This class defines a PlantUML Architecture view.
    See base class PlantumlType for more.
    """
    def __init__(self, name=""):
        super().__init__(name)
        self.type = "ArchView"
        super().__post_init__()
        
@dataclass
class PlantumlConnection(PlantumlType):
    """
    This class defines a PlantUML architectural Connection between two components.
    Usually connecting actors, components or activities, but also interfaces and ports.
    See base class PlantumlType for more.
    """
    def __init__(self, name, comp1, comp2, **options):
        super().__init__(name="")
        self.type = "ArchView"
        self.comp1 = comp1
        self.comp2 = comp2

        self.metadata_dict.update(options)
        super().__post_init__()

