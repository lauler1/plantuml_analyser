import copy
import types
import asyncio
# from dataclasses import dataclass, field
from plantuml.plantuml_activity import do_plantuml_activity
from plantuml.plantuml_sequence import do_plantuml_sequence
from plantuml.plantuml_architecture import do_plantuml_architecture, introspect_object
from plantuml.redirect_output_to_file import redirect_output_to_file
from plantuml.generate_plantuml_html import redirect_plantuml_output_to_html
from plantuml.generate_svg_html import redirect_svg_output_to_html
from plantuml.plantuml_types import PlantumlActor, PlantumlComponent, PlantumlInterface, PlantumlActivity, PlantumlArchitecture, PlantumlConnection, clone_architecture, PlantumlFrame, PlantumlGroup, ArchBreakLine, PlantumlDataType
from plantuml.plantuml_simulation import PlantumlSimulation
from plantuml.plantuml_class import do_plantuml_class_diagram, do_plantuml_object_diagram

from plantuml.svg_architecture import do_svg_architecture, Orientation
import plantuml.connection_routing as cr

# Exemplo 1 -------------------------------------------------------------------
def example_function(x, a=1, *args, **kwargs):
    y = x + 10
    z = 2 * y
    # This is a comment before a
    a: Int = 0
    print1('text1') # Comment print 1
    print('text2')
    
    squares = [x**2 for x in range(10)]
    print(squares)
    
    # Comment before if
    if x >= 100 and x < 1000: # Comment on if
        y = x + 1
    elif x < y: # Comment on elif
        y = x + 2
        return x, y
    else: # Comment on else
        print1('text3')
        print('text4')
        y = x - 1
        if z > 20 and z <= 30:
            print(x)
    for i in range(y):
        print2(i)
    count = 0
    while count < 5:# Comment on while
        print(f"Count is: {count}")# Comment on print
        count += 1
    else:
        print(f"Count is: {count}")
    count = 0
    while True:
        print(f"Count is: {count}")
        count += 1
        if count >= 5:
            break
    return 10
    
# Exemplo 2 -------------------------------------------------------------------
def example_sequence_1():
    example_sequence_2(10)
    for i in range(10):
        example_sequence_2(10)

def example_sequence_2(a, **kwargs):
    if a > b:
        example_sequence_3(10, b=30, c=30)
    else:
        example_sequence_4()

    if a < b:
        print("")
    else:
        print("")

    return "OK"

def example_sequence_3(b, c):
    while b > 0:
        example_sequence_4()

def example_sequence_4():
    return "OK", "Bye"

@redirect_output_to_file('output/log1.puml')
def case1():
    # Example with do_plantuml_activity
    do_plantuml_activity(example_function, filter_call=['func1', 'printd1'], args=True, assign=True, augassign=True, ret=True, comment=True)

@redirect_output_to_file('output/log2.puml')
def case2():
    # Example with do_plantuml_sequence
    do_plantuml_sequence((example_sequence_1, "Actor 1", "actor"), (example_sequence_2, "Participant 2", "participant"), (example_sequence_3, "DB 1", "database"), (example_sequence_4, "Last", "participant"), max_rec=10, title="This is a title")


case1()
case2()

async def state_machine_run(self, simulation):
    if self.smconn == None:
        # To ensure that this simulation ca run.
        # As the connections are fulfilled by reflection at architecture,
        # not all instances of this class may be connected
        return
        
    simulation.set_simulation_state_decorator(self, "State 1")
    result = await simulation.wait_message(self.smconn)
    simulation.set_simulation_state_decorator(self, f"State 2 {result}")
    result = await simulation.wait_message(self.smconn)
    simulation.set_simulation_state_decorator(self, f"State 3 {result}")

async def subactivity_2_run(self, simulation):
    if self.multipleconn == None:
        # To ensure that this simulation ca run.
        # As the connections are fulfilled by reflection at architecture,
        # not all instances of this class may be connected
        return
    result = await simulation.send_message(self.multipleconn, self, "subactivity_2 message")

async def sm_send_run(self, simulation):
    if self.smconn == None:
        # To ensure that this simulation ca run.
        # As the connections are fulfilled by reflection at architecture,
        # not all instances of this class may be connected
        return
    await asyncio.sleep(0)
    # await simulation.wait_message(self.sm_conn)
    result = await simulation.send_message(self.smconn, self, "SM message", self.name)

class MyActivity(PlantumlActivity):
    def __init__(self, name, **options):
        super().__init__(name, **options)

class MySubComponent1(PlantumlComponent):
    def __init__(self, name, **options):
        self.activity1 = PlantumlActivity("Mysubactivity 1", note=r"This is a note\nfor an activity")
        self.activity2 = PlantumlActivity("Mysubactivity 2")
        super().__init__(name, **options)

class MyActivity1(PlantumlActivity):
    def __init__(self, name, **options):
        self.conn1 = None # This connection ref shall bewfulfilled by Reflection
        self.conn2 = None # This connection ref shall bewfulfilled by Reflection
        super().__init__(name, **options)
        
    async def run(self, simulation):
        
        if self.conn1 == None or self.conn2 == None:
            # To ensure that this simulation ca run.
            # As the connections are fulfilled by reflection at architecture,
            # not all instances of this class may be connected
            return
        
        # conn = simulation.get_sub_obj_by_name("Conn 1")
        # print(f"New run: Starting async call for {self.name}...")
        simulation.set_simulation_activity_decorator(self)
        
        result = await simulation.wait_message(self.conn1)
        
        simulation.set_simulation_decorator("alt #F2F2F2 sucess")
        await simulation.send_message(self.conn1, self, "message 2")
        simulation.set_simulation_activate(self)
        simulation.set_simulation_decorator("else error")
        await simulation.send_message(self.conn1, self, "message 3")
        simulation.set_simulation_decorator("end")
        # print(f"New run: Async call completed for {self.name}!, result message = {result}")   
        simulation.set_simulation_deactivate(self)
        await simulation.send_message(self.conn2, self, "message 4")
            
class MyComponent1(PlantumlComponent):
  
    def __init__(self, name, **options):
        self.activity1 = MyActivity1("Myactivity 1")
        self.activity2 = MyActivity("Myactivity 2")# , hide=True)
        self.subcomp = MySubComponent1("SubComponent 1", note=r"This is a note\nfor a component")# , remove=True)
        super().__init__(name, **options)

class MyComponent2(PlantumlComponent):
    def __init__(self, name, **options):
        self.activity1 = PlantumlActivity("Myactivity")
        super().__init__(name, **options)

class MyActor(PlantumlActor):

    class MyActorActivity(PlantumlActivity):
        def __init__(self, name, **options):
            self.conn1 = None # This connection ref shall bewfulfilled by Reflection
            super().__init__(name, **options)
        async def run(self, simulation):
            #conn = simulation.get_sub_obj_by_name("Conn 1")
            # print(f"New run: Starting async call for {self.name}...")
            simulation.set_simulation_activity_decorator(self)
            await simulation.send_message(self.conn1, self, "message 1")
            # print(f"New run: Async call completed for {self.name}!")   
    
    def __init__(self, name, **options):
        self.actor_activity = self.MyActorActivity("Actor activity")
        super().__init__(name, **options)

class MyArchitecture(PlantumlArchitecture):
    
    description="""
This is an example of architecture that can be shown as diagram using PlantUML.<br>
It can also be simulated.
    """

    def __init__(self, name):
        self.actor1 = MyActor("Myactor 1")
        # actor1.actor_activity.run = types.MethodType(new_call_method, actor1.actor_activity)
        
        self.component1 = MyComponent1("Mycomponent 1")
        self.component2 = MyComponent2("Mycomponent 2", color="pink;line:red;line.bold;text:red")

        self.brk1 = ArchBreakLine()

        self.group1 = PlantumlGroup()
        self.group1.component3 = PlantumlComponent("Mycomponent 3")
        self.group1.component4 = PlantumlComponent()
        self.group1.component5 = PlantumlComponent()
        self.class_activity = PlantumlActivity("Class Activity")
        
        self.component6 = PlantumlComponent("PlantumlComponent 6")
        self.component6.state_activity = PlantumlActivity("State Machine")
        self.component6.state_activity.state_conn_1 = None
        self.component6.state_activity2 = PlantumlActivity("This is a very long name to fit inside a component", note=r"This is a note\nfor an ver long activity")
        self.component6.state_activity.replace_run_method(state_machine_run)

        self.brk2 = ArchBreakLine()
        self.component7 = PlantumlComponent()
        self.component7.activity = PlantumlActivity()
        self.component8 = PlantumlComponent()
        self.component9 = PlantumlComponent()

        
        # # Create some invisible plantuml connections to try to fix components in relative positions
        # self.layout_combine_vertical = [(self.component2, self.component6)]
        
        self.component1.subcomp.activity2.replace_run_method(subactivity_2_run)
        self.class_activity.replace_run_method(sm_send_run)
        self.component1.activity2.replace_run_method(sm_send_run)
        
        self.conn1 = PlantumlConnection("Conn 1", self.actor1.actor_activity, self.component1.activity1) # , hide=True)
        self.conn2 = PlantumlConnection("Conn 2", self.component1.activity1, self.component2.activity1)
        self.conn3 = PlantumlConnection("Conn 3", self.actor1, self.component1.subcomp)

        self.conn3b = PlantumlConnection("Conn 3B", self.class_activity, self.component6.state_activity2)

        self.smconn = PlantumlConnection("SM Conn", [self.class_activity, self.component1.activity2], self.component6.state_activity)
        self.mltconn = PlantumlConnection("Multiple Conn", self.component1.subcomp.activity2, [self.class_activity, self.component1.activity1])

        super().__init__(name)  # Call the __init__ method of PlantumlArchitecture

class MySuperArchitecture(PlantumlArchitecture):  
    description="""
This is an example of architecture that can be shown as diagram using PlantUML.<br>
It can also be simulated.
    """

    def __init__(self, name):
        self.frame = PlantumlFrame("My Frame")
        self.frame.sub_architecture = MyArchitecture("my architecture")

        self.brk1 = ArchBreakLine()
        
        # self.group1 = PlantumlGroup()
        self.frame2 = PlantumlFrame("My Frame 2")
        self.frame2.component_super_arch2 = MyComponent2("Mycomponent_super_arch 2", color="pink;line:red;line.bold;text:red")
        self.frame2.component_super_arch1 = MyComponent1("Mycomponent_super_arch 1")
        self.frame2.component_super_arch3 = PlantumlComponent("Mycomponent_super_arch 3", svg_orientation=Orientation.TOP_DOWN)
        self.frame2.component_super_arch3.add(PlantumlActivity("vertical activity 1"))
        self.frame2.component_super_arch3.add(PlantumlActivity("vertical activity 2"))
        self.frame2.component_super_arch3.add(PlantumlActivity("vertical activity 3"))
        self.conn4 = PlantumlConnection("Conn 4", self.frame2.component_super_arch1, self.frame2.component_super_arch2)

        self.conn5 = PlantumlConnection("Conn 5", self.frame2.component_super_arch1.activity1, self.frame.sub_architecture.component2.activity1, color="red")
        self.conn6 = PlantumlConnection("Conn 6", self.frame.sub_architecture.component7.activity, self.frame.sub_architecture.component2.activity1)

        # # Create some invisible plantuml connections to try to fix components in relative positions
        # self.layout_combine_vertical = [(self.group1.component_super_arch1, self.frame), (self.frame, self.group1.component_super_arch2)]
        
        super().__init__(name)  # Call the __init__ method of PlantumlArchitecture

myarch = MySuperArchitecture("my super architecture")
myarch.set_options(svg_orientation=Orientation.TOP_DOWN) # TOP_DOWN, LEFT_RIGHT

# myarch.arch_post_init()


@redirect_plantuml_output_to_html('output/myarch.html', "Architecture test", myarch.description)
def case3(myarch):
    # Example with do_plantuml_architecture
    do_plantuml_architecture(myarch)

@redirect_plantuml_output_to_html('output/myarcview.html', "ArchitectureView test")
def case4(myarch):
    # Example with do_plantuml_architecture
    do_plantuml_architecture(myarch)

@redirect_plantuml_output_to_html('output/mysimul.html', "Architecture Simulation test", "First simulation attempt")
def case5(mysim):
    # Example with PlantumlArchitecture simulate
    mysim.simulate()

@redirect_plantuml_output_to_html('output/mysimul2.html', "Architecture Simulation test 2", "Second simulation, to test repetition")
def case6(mysim):
    # Example with PlantumlArchitecture simulate
    mysim.simulate()

@redirect_svg_output_to_html('output/svg_arch.html', "Architecture Simulation with SVG", "This is the description of this SVG simulation<br> It may contain multiple lines")
def case7(myarch):
    # Example with PlantumlArchitecture simulate
    do_svg_architecture(myarch, print_roads=False)

# myarch.frame.set_options(hide=True) 

case7(myarch) 
# introspect_object(myarch)


# owner_tree = myarch.get_owner_tree(myarch.sub_architecture.component1.subcomp.activity1)
# print("owner_tree of ", myarch.sub_architecture.component1.subcomp.activity1.name, " is ", owner_tree)
# print ("owner_path is ", myarch.get_complete_path_name(myarch.sub_architecture.component1.subcomp.activity1))

new_arch = clone_architecture(myarch, "Nome da nova classe")
new_arch.add(PlantumlComponent("Added to the clone"))
new_arch.frame.sub_architecture.group1.component4.set_options(hide=True)
# # new_arch.get_sub_obj_by_name("Myactor 1")
# # new_arch.get_sub_obj_by_name("Actor activity")
# # new_arch.get_sub_obj_by_name("Conn 1")
# # new_arch.get_sub_obj_by_name("Added to the clone")

case3(myarch)
case4(new_arch)

print("simulate arch:")
mysim = PlantumlSimulation(myarch, comp_order=[\
            myarch.frame.sub_architecture.actor1.path,\
            myarch.frame.sub_architecture.component1.path,\
            myarch.frame.sub_architecture.component1.subcomp.path,\
            myarch.frame.sub_architecture.path])
case5(mysim)
# print("simulate arch 2:")
mysim.set_options(comp_order=[\
            myarch.frame.sub_architecture.actor1.path,\
            myarch.frame.sub_architecture.component1.path,\
            myarch.frame.sub_architecture.path,\
            myarch.frame.sub_architecture.component1.subcomp.path,\
            myarch.frame.sub_architecture.component2.path])
case6(mysim)


from abc import ABC, abstractmethod
class Base(ABC):
    @abstractmethod
    def my_abstract_method(self):
        pass
    
    @staticmethod
    @abstractmethod
    def my_abstract_func():
        pass

class A1(Base):
    static_val: int = None

class A2():
    static_val: int = 10

class Compos1():
    var1 = 0

class Compos2():
    def __init__(self):
        self.comp1 = Compos1()

class B(A1, A2):
    def __init__(self):
        self.value = "my value B"
        self.a = 10
        self.b = [1,2,3]
        self.comp1 = Compos1()
        self.comp2 = Compos2()

    def my_abstract_method(self):
        pass
    
    @staticmethod
    def my_abstract_func():
        pass

class C(A1):
    st = 10
    def __init__(self):
        self.value = "my value C"
        
    def my_func(self):
        pass

    @staticmethod
    def my_static_func():
        pass

    def my_abstract_method(self):
        pass
    
    @staticmethod
    def my_abstract_func():
        pass

class ClassDiagram(PlantumlDataType):

    def __init__(self):
        super().__init__()
        self.b = B()
        self.c = C()
        self.a: int = 0

@redirect_plantuml_output_to_html('output/class_diagram.html', "Data Class Diagram", "This is a simple class diagram using plantuml.")
def case7(class_diagram=ClassDiagram()):
    do_plantuml_class_diagram(class_diagram)
case7()

@redirect_plantuml_output_to_html('output/object_diagram.html', "Object Diagram", "This is a simple object diagram using plantuml.")
def case8(class_diagram=ClassDiagram()):
    do_plantuml_object_diagram(class_diagram)
case8()

cr.test(myarch, [myarch.frame2.component_super_arch1.activity1, myarch.frame2.component_super_arch1.activity2, myarch.frame.sub_architecture.component1.activity1, myarch.frame.sub_architecture.component2.activity1])

# print("\n Old----------------------------------------------------------------------------------------")
# introspect_object(myarch)

# print("\n New----------------------------------------------------------------------------------------")
# introspect_object(new_arch)



# A version of PlantumlConnection used only to align components on the screen: https://crashedmind.github.io/PlantUMLHitchhikersGuide/layout/layout.html

# TODO: Add processes in the architecture diagrams.
# TODO: Add class diagrams, also include other containes like dictionaries and json.

