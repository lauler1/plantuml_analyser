import copy
import types
import asyncio
# from dataclasses import dataclass, field
from plantuml.plantuml_activity import do_plantuml_activity
from plantuml.plantuml_sequence import do_plantuml_sequence
from plantuml.plantuml_architecture import do_plantuml_architecture, introspect_object
from plantuml.redirect_output_to_file import redirect_output_to_file
from plantuml.generate_plantuml_html import redirect_output_to_html
from plantuml.plantuml_types import PlantumlActor, PlantumlComponent, PlantumlInterface, PlantumlPort, PlantumlActivity, PlantumlArchitecture, PlantumlConnection

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

class MyActivity(PlantumlActivity):
    def __init__(self, name, **options):
        super().__init__(name, **options)

class MySubComponent1(PlantumlComponent):
    activity1 = PlantumlActivity("Mysubactivity 1", note=r"This is a note\nfor an activity")
    activity2 = PlantumlActivity("Mysubactivity 2")
    def __init__(self, name, **options):
        super().__init__(name, **options)

class MyComponent1(PlantumlComponent):

    class MyActivity1(PlantumlActivity):
        def __init__(self, name, **options):
            super().__init__(name, **options)
        async def run(self, arch_inst):
            # conn = arch_inst.get_sub_obj_by_name("Conn 1")
            # print(f"New run: Starting async call for {self.name}...")
            arch_inst.set_simulation_activity_decorator(self)
            result = await self.conn_1.wait_message(arch_inst)
            
            arch_inst.set_simulation_decorator("alt #F2F2F2 sucess")
            await self.conn_1.send_message(arch_inst, self, "message 2")
            arch_inst.set_simulation_activate(self)
            arch_inst.set_simulation_decorator("else error")
            await self.conn_1.send_message(arch_inst, self, "message 3")
            arch_inst.set_simulation_decorator("end")
            # print(f"New run: Async call completed for {self.name}!, result message = {result}")   
            arch_inst.set_simulation_deactivate(self)
            await self.conn_2.send_message(arch_inst, self, "message 4")
            
    activity1 = MyActivity1("Myactivity 1")
    activity2 = MyActivity("Myactivity 2")# , hide=True)
    subcomp = MySubComponent1("SubComponent 1", note=r"This is a note\nfor a component")# , remove=True)
    def __init__(self, name, **options):
        super().__init__(name, **options)

class MyComponent2(PlantumlComponent):
    activity1 = PlantumlActivity("Myactivity")
    def __init__(self, name, **options):
        super().__init__(name, **options)

class MyActor(PlantumlActor):

    class MyActorActivity(PlantumlActivity):
        def __init__(self, name, **options):
            super().__init__(name, **options)
        async def run(self, arch_inst):
            #conn = arch_inst.get_sub_obj_by_name("Conn 1")
            # print(f"New run: Starting async call for {self.name}...")
            arch_inst.set_simulation_activity_decorator(self)
            await self.conn_1.send_message(arch_inst, self, "message 1")
            # print(f"New run: Async call completed for {self.name}!")   

    actor_activity = MyActorActivity("Actor activity")
    
    def __init__(self, name, **options):
        super().__init__(name, **options)


class MyArchitecture(PlantumlArchitecture):
    actor1 = MyActor("Myactor 1")
    # actor1.actor_activity.run = types.MethodType(new_call_method, actor1.actor_activity)
    
    component1 = MyComponent1("Mycomponent 1")
    component2 = MyComponent2("Mycomponent 2", color="pink;line:red;line.bold;text:red")

    component3 = PlantumlComponent("Mycomponent 3")
    component4 = PlantumlComponent()
    component5 = PlantumlComponent()
    class_activity = PlantumlActivity("Class Activity")
    
    conn1 = PlantumlConnection("Conn 1", actor1.actor_activity, component1.activity1) # , hide=True)
    conn2 = PlantumlConnection("Conn 2", component1.activity1, component2.activity1)
    conn3 = PlantumlConnection("Conn 3", actor1, component1.subcomp)
    
    description="""
This is an example of architecture that can be shown as diagram using PlantUML.<br>
It can also be simulated.
    """

    def __init__(self, name):
        super().__init__(name)  # Call the __init__ method of PlantumlArchitecture
        
        self.component6 = PlantumlComponent("asdfasdfasfasdfasf")
        self.activity = PlantumlActivity("Self Activity")

myarch = MyArchitecture("my arch name")

@redirect_output_to_html('output/myarch.html', "Architecture test", myarch.description)
def case3(myarch):
    # Example with do_plantuml_architecture
    do_plantuml_architecture(myarch)

@redirect_output_to_html('output/myarcview.html', "ArchitectureView test")
def case4(myarch):
    # Example with do_plantuml_architecture
    do_plantuml_architecture(myarch)

@redirect_output_to_html('output/mysimul.html', "Architecture Simulation test")
def case5(myarch):
    # Example with PlantumlArchitecture simulate
    myarch.simulate()

# introspect_object(myarch)

case3(myarch)
print("simulate arch:")
case5(myarch)
# myarch.simulate()

# myarch.add(PlantumlComponent("Added to the clone"))
# myarch.component4.set_options(hide=True)
# myarch.get_sub_obj_by_name("Myactor 1")
# myarch.get_sub_obj_by_name("Actor activity")
# myarch.get_sub_obj_by_name("Conn 1")
# myarch.get_sub_obj_by_name("Added to the clone")

# print("simulate 2:")
#myarch.simulate()

# case4(myarch)



