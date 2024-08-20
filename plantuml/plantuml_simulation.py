import plantuml.plantuml_types as pt
import re
import asyncio

def sanitize_name(name):
    return re.sub(r'\W|^(?=\d)', '_', name.lower())

class PlantumlSimulation():
    """
    This class defines a PlantUML Simulation, which can generate sequence diagrams
    """
    def __init__(self, architecture, name=""):
        self.name = name
        self.architecture = architecture
        self.participants = {}
        self.part_seq = [] # Store seq of participants during a simulation simulation.
        self.sequence = [] # Store sequence of activities during a simulation simulation
        self.queues = {}
        
    def gather_participants(self, activities):
        owners = set()
        participants = {}
        
        # Create a set of owners, because sequences are shown per component, not per activity
        for activity in activities:
            # res = self.architecture.get_activity_owner(activity)
            owners.add(activity.owner.ref)
            
        # Create a dictionary of Owners (i.e. components owning the activities)
        for owner in owners:
            if owner != None:
                color = "#96B1DA"
                
                if isinstance(owner, pt.PlantumlActor):
                    color = "#C6E6FF"
                #owner_path = owner.path # sanitize_name(owner.name)
                participants[owner.path] = f'  participant "{owner.name}" as {owner.path} {color}'
        self.participants = participants

    def set_simulation_decorator(self, deco_text):
        self.sequence.append(deco_text)

    def set_simulation_activate(self, component):
        if isinstance(component, pt.PlantumlActivity):
            component = component.owner.ref # self.architecture.get_activity_owner(component)
        self.sequence.append(f"  activate {component.path}")

    def set_simulation_deactivate(self, component):
        if isinstance(component, pt.PlantumlActivity):
            component = component.owner.ref # self.architecture.get_activity_owner(component)
        self.sequence.append(f"  deactivate {component.path}")

    def set_simulation_activity_decorator(self, component):
        if not isinstance(component, pt.PlantumlActivity):
            return
        owner = self.architecture.get_activity_owner(component)
        owner2 = self.architecture.get_owner(component)
        
        #print(f"  Owner = {component.name} {component.owner} {component.owner.ref} {owner.path} {owner2.path}")
        self.sequence.append(f"  rnote over {component.owner.ref.path} #C5FFA6\n{component.name}\n  endrnote")

    async def run(self, activities):
        # Run the list of coroutines concurrently
        await asyncio.gather(*(coro.run(self) for coro in activities))

    def simulate(self):
        activities = self.architecture.get_all_activities()
        self.part_seq = [] # clear part_seq from previous simulation
        self.sequence = [] # clear sequence
        self.queues = {}   # clear queues
        
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

        self.gather_participants(activities)
        asyncio.run(self.run(list(activities)))
        
        new_list_of_participants = []
        
        # Only shows participants that where really used in the simulation
        # Use list instead of set to preserve order
        for item in self.part_seq:
            if not item in new_list_of_participants:
                new_list_of_participants.append(item)
        
        print("")            
        # Show participants
        for item in new_list_of_participants:
            print(self.participants[item])
        print("")            
        
        # Show sequences
        for item in self.sequence :
            print(item)
            print("")            
        
        print("@enduml")            

    def get_queue(self, connection):
        # print(f"   -----> get_queue connection = {connection}")
    
        if isinstance(connection, pt.ObjectRef):
            connection = connection.ref
        # print(f"   -----> get_queue connection name = {connection}")
            
        if not connection.name in self.queues:
            self.queues[connection.name] = asyncio.Queue()
        return self.queues[connection.name]

    def print_transmission(self, connection, sender, text):
        send_path = sender.path 
        if isinstance(sender, pt.PlantumlActivity):
            send_path = sender.owner.ref.path 
            
        if isinstance(connection, pt.ObjectRef):
            connection = connection.ref

        other = connection.comp1.ref
        if other == sender:
            other = connection.comp2.ref
        other_path = other.path 
        if isinstance(other, pt.PlantumlActivity):
            other_path = other.owner.ref.path 
        # send_path = sanitize_name(send_name)
        # other_path = sanitize_name(other_name)
        self.part_seq.append(send_path)
        self.part_seq.append(other_path)
        self.sequence.append(f"{send_path} -> {other_path}: {text}")
        
    async def send_message(self, connection, sender, lable, data=""):
        """
        Sends a message in the queue.
        This method also yields the control to the event loop after sending.
        """
        if connection == None:
            return
        if sender == None:
            return
        if lable == None:
            return
        self.print_transmission(connection, sender, lable)
        await self.get_queue(connection).put({"label":lable, "data":data})

    async def send_message_and_wait(self, connection, sender, lable, data=""):
        """
        Sends a message and waits for an answer in the queue.
        """
        if connection == None:
            return
        if sender == None:
            return
        if lable == None:
            return
        self.print_transmission(connection, sender, lable)
        self.get_queue(connection).put_nowait({"label":lable, "data":data})
        item = await self.get_queue(connection).get()
        return item

    async def wait_message(self, connection):
        """
        Waits for a message in the queue.
        """
        if connection == None:
            return
        item = await self.get_queue(connection).get()
        return item
